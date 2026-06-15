from telethon import events
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.customer import Customer
from app.models.conversation import Conversation, Message
from app.services.ai.engine import generate_reply, extract_facts_from_conversation
from app.services.ai.language import detect_language
from app.services.ai.prompts import get_system_prompt, get_objection_handler
from app.services.ai.memory import (
    get_recent_messages,
    build_context_prompt,
    upsert_memory,
    upsert_memory_bulk,
)
from app.services.ai.classifier import classify_message
from app.services.anti_spam.detector import should_block
from app.services.sales.lead_manager import get_or_create_lead
from app.services.sales.recommender import recommend_plans, format_plan_recommendation
from app.services.monitoring.metrics_collector import increment_daily_stat
from app.cache.redis_client import cache_get, cache_set
from app.cache.keys import CacheKeys
from app.core.config import settings
from app.core.logging import get_logger
from datetime import datetime, timezone
import asyncio
import uuid
import random

logger = get_logger(__name__)

TYPING_DELAYS = {
    "short": (0.5, 1.5),
    "medium": (1.5, 3.0),
    "long": (2.5, 4.5),
}

GREETING_TRIGGERS = {
    "hi", "hello", "hey", "سلام", "درود", "مرحبا", "مرحباً",
    "merhaba", "привет", "bonjour", "hola", "hallo",
}

GREETING_REPLIES = {
    "fa": "سلام! 👋 چطور می‌تونم کمکتون کنم؟ می‌تونیم در مورد VPS، سرور اختصاصی یا هر سرویسی که نیاز دارید صحبت کنیم.",
    "ar": "مرحباً! 👋 كيف يمكنني مساعدتك؟ يمكنني مساعدتك في VPS والخوادم المخصصة وغيرها.",
    "tr": "Merhaba! 👋 Size nasıl yardımcı olabilirim? VPS, özel sunucu veya başka hizmetler hakkında konuşabiliriz.",
    "ru": "Привет! 👋 Чем могу помочь? Я расскажу вам о VPS, выделенных серверах и других услугах.",
    "en": "Hi there! 👋 How can I help you today? We can chat about VPS, dedicated servers, or any hosting service you need.",
}

FALLBACK_MESSAGES = {
    "fa": "ممنون از پیامتون 🙏 همکارم به زودی پاسخ می‌ده.",
    "ar": "شكراً لرسالتك 🙏 سيرد عليك أحد زملائي قريباً.",
    "tr": "Mesajınız için teşekkürler 🙏 Ekibimizden biri kısa sürede size dönecek.",
    "ru": "Спасибо за ваше сообщение 🙏 Один из наших сотрудников свяжется с вами в ближайшее время.",
    "de": "Danke für Ihre Nachricht 🙏 Ein Teammitglied wird sich bald bei Ihnen melden.",
    "fr": "Merci pour votre message 🙏 Un membre de notre équipe vous répondra bientôt.",
    "es": "Gracias por su mensaje 🙏 Un miembro de nuestro equipo le responderá pronto.",
    "en": "Thanks for your message 🙏 One of our team will get back to you shortly.",
}


async def handle_private_message(event, account_id: str):
    sender = await event.get_sender()
    if not sender or sender.bot:
        return

    user_id = sender.id
    text = event.message.text or ""

    if not text.strip():
        return

    blocked, reason = await should_block(user_id, text)
    if blocked:
        logger.warning("message_blocked", user_id=user_id, reason=reason)
        return

    await increment_daily_stat("messages_received")

    text_lower = text.lower().strip()
    reply_length = "short" if len(text) < 50 else ("medium" if len(text) < 200 else "long")

    async with AsyncSessionLocal() as session:
        customer = await get_or_create_customer(session, sender, account_id)
        await session.flush()

        # ── Language detection ─────────────────────────────────────────────
        # Detect language only from messages long enough to be reliable (>=5 chars).
        # For very short messages (emoji, one-word greetings like «سلام» which is
        # only 4 chars) detect_language falls back to DEFAULT_LANGUAGE ("en"), which
        # would wrongly overwrite a previously confirmed language. Skip the update
        # in that case and keep the customer's stored language.
        previous_lang = customer.language_code or "en"

        # Always attempt detection — language.py handles short texts via
        # Unicode script detection (Persian/Arabic/Cyrillic work even for 1 char).
        detected_lang = await detect_language(text)
        if detected_lang and detected_lang != previous_lang:
            customer.language_code = detected_lang
            logger.info(
                "language_switched",
                user_id=user_id,
                from_lang=previous_lang,
                to_lang=detected_lang,
            )

        language = customer.language_code or "en"
        # ──────────────────────────────────────────────────────────────────

        conv = await get_or_create_conversation(session, customer, account_id, language)
        await session.flush()

        # Update conversation language if it changed
        if conv.language != language:
            conv.language = language

        await save_message(session, conv.id, event.message.id, "inbound", text)
        await session.flush()

        # ── Greeting fast-path ─────────────────────────────────────────────
        # Pure greeting (single word/phrase): skip AI to save tokens and reply
        # instantly. We only do this when the conversation is brand new (≤1 msg).
        if text_lower.strip() in GREETING_TRIGGERS:
            msg_count_check = int(await cache_get(f"conv_msg_count:{conv.id}") or 0)
            if msg_count_check == 0:
                greeting_reply = GREETING_REPLIES.get(language, GREETING_REPLIES["en"])
                await save_message(session, conv.id, None, "outbound", greeting_reply, ai_generated=False)
                await session.commit()
                try:
                    await event.reply(greeting_reply, parse_mode="md")
                    await increment_daily_stat("messages_sent")
                    logger.info("greeting_fast_reply", user_id=user_id, language=language)
                except Exception as e:
                    logger.error("send_greeting_failed", user_id=user_id, error=str(e))
                return
        # ──────────────────────────────────────────────────────────────────

        classification = await classify_message(text, language)

        if classification.get("intent") in ("sales", "inquiry", "negotiation", "comparison"):
            await get_or_create_lead(session, customer, uuid.UUID(account_id), classification)

        if classification.get("urgency") == "critical":
            await upsert_memory(session, customer.id, "urgency_flag", "critical", confidence=1.0)

        if classification.get("use_case"):
            await upsert_memory(session, customer.id, "use_case", classification["use_case"], confidence=0.95)

        if classification.get("tech_level") and classification["tech_level"] != "unknown":
            await upsert_memory(session, customer.id, "tech_level", classification["tech_level"], confidence=0.9)

        if classification.get("competitor_mentioned"):
            await upsert_memory(session, customer.id, "competitor", classification["competitor_mentioned"], confidence=1.0)

        context_prompt = await build_context_prompt(session, customer, conv.id)

        # get_system_prompt now includes a hard language directive at the top
        system_prompt = get_system_prompt(language)

        objection_hint = ""
        if classification.get("objection_type") and classification["objection_type"] != "none":
            handler = get_objection_handler(classification["objection_type"], language)
            if handler:
                objection_hint = f"\n\nOBJECTION GUIDANCE: {handler}"

        full_system = f"{system_prompt}\n\n{context_prompt}{objection_hint}"

        history = await get_recent_messages(session, conv.id, limit=20)
        current_msg = {"role": "user", "content": text}
        messages = history[:-1] + [current_msg] if history else [current_msg]

        delay_range = TYPING_DELAYS[reply_length]
        typing_delay = random.uniform(*delay_range)

        tokens = 0
        try:
            async with event.client.action(event.chat_id, "typing"):
                await asyncio.sleep(typing_delay)
                reply, tokens = await generate_reply(messages, full_system)
        except Exception as ai_err:
            logger.error("ai_failed_using_fallback", user_id=user_id, error=str(ai_err))
            reply = FALLBACK_MESSAGES.get(language, FALLBACK_MESSAGES["en"])

        if tokens > 0 and (
            classification.get("purchase_readiness") in ("ready_to_buy", "considering")
            and classification.get("service_interest") not in ("none", "general")
            and len(messages) >= 3
        ):
            plans = recommend_plans(
                classification.get("service_interest", "vps"),
                classification.get("budget_max"),
                {
                    "use_case": classification.get("use_case"),
                    "tech_level": classification.get("tech_level"),
                },
            )
            if plans:
                plan_text = format_plan_recommendation(plans, language)
                reply = f"{reply}\n\n{plan_text}"

        await save_message(
            session, conv.id, None, "outbound", reply,
            ai_generated=tokens > 0, tokens=tokens,
        )

        msg_count_key = f"conv_msg_count:{conv.id}"
        msg_count = int(await cache_get(msg_count_key) or 0) + 1
        await cache_set(msg_count_key, msg_count, ttl=86400)

        if tokens > 0 and msg_count % 10 == 0 and msg_count >= 10:
            asyncio.create_task(
                _extract_and_store_facts(
                    customer.id,
                    messages + [{"role": "assistant", "content": reply}],
                )
            )

        await session.commit()

    try:
        await event.reply(reply, parse_mode="md")
        await increment_daily_stat("messages_sent")
        logger.info(
            "reply_sent",
            user_id=user_id,
            language=language,
            tokens=tokens,
            intent=classification.get("intent"),
        )
    except Exception as e:
        logger.error("send_reply_failed", user_id=user_id, error=str(e))


async def _extract_and_store_facts(customer_id: uuid.UUID, messages: list[dict]):
    try:
        async with AsyncSessionLocal() as new_session:
            facts = await extract_facts_from_conversation(messages)
            if facts:
                filterable = {
                    k: v for k, v in facts.items()
                    if v and v not in ("null", "unknown", [])
                }
                await upsert_memory_bulk(new_session, customer_id, filterable)
                await new_session.commit()
                logger.info(
                    "facts_extracted_and_stored",
                    customer_id=str(customer_id),
                    count=len(filterable),
                )
    except Exception as e:
        logger.warning("fact_extraction_bg_failed", error=str(e))


async def get_or_create_customer(session, sender, account_id: str) -> Customer:
    result = await session.execute(
        select(Customer).where(Customer.telegram_id == sender.id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        customer = Customer(
            telegram_id=sender.id,
            username=getattr(sender, "username", None),
            display_name=(
                f"{getattr(sender, 'first_name', '') or ''} "
                f"{getattr(sender, 'last_name', '') or ''}"
            ).strip() or None,
            language_code="en",
        )
        session.add(customer)
        await increment_daily_stat("new_customers")
        logger.info("customer_created", telegram_id=sender.id)
    else:
        if getattr(sender, "username", None):
            customer.username = sender.username
        if getattr(sender, "first_name", None) or getattr(sender, "last_name", None):
            new_name = (
                f"{getattr(sender, 'first_name', '') or ''} "
                f"{getattr(sender, 'last_name', '') or ''}"
            ).strip()
            if new_name:
                customer.display_name = new_name

    return customer


async def get_or_create_conversation(
    session, customer: Customer, account_id: str, language: str = "en"
) -> Conversation:
    cache_key = CacheKeys.conversation_active(account_id, customer.telegram_id)
    cached_id = await cache_get(cache_key)

    if cached_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == uuid.UUID(cached_id))
        )
        conv = result.scalar_one_or_none()
        if conv and conv.status == "active":
            return conv

    conv = Conversation(
        customer_id=customer.id,
        account_id=uuid.UUID(account_id),
        status="active",
        language=language,
        started_at=datetime.now(timezone.utc),
    )
    session.add(conv)
    await session.flush()
    await cache_set(cache_key, str(conv.id), ttl=86400)
    return conv


async def save_message(
    session,
    conv_id,
    tg_msg_id,
    direction: str,
    content: str,
    ai_generated: bool = False,
    tokens: int = 0,
):
    session.add(Message(
        conversation_id=conv_id,
        telegram_msg_id=tg_msg_id,
        direction=direction,
        content=content,
        ai_generated=ai_generated,
        tokens_used=tokens,
        sent_at=datetime.now(timezone.utc),
    ))
