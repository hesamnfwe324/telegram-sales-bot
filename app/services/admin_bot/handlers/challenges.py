from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.challenge import RDPChallenge
from app.services.challenges.service import (
    create_and_publish_campaign,
    get_campaign_stats,
    record_answer,
)

logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data == "rdp_challenge")
async def start_challenge_campaign(callback: CallbackQuery):
    await callback.answer()
    status = await callback.message.edit_text("🧠 Building a safe AI RDP challenge for all active channels...")
    result = await create_and_publish_campaign()
    if result.get("status") == "no_channels":
        await status.edit_text("⚠️ No active channels are configured.")
    elif result.get("status") == "locked":
        await status.edit_text("⏳ Another challenge campaign is already being published.")
    else:
        await status.edit_text(
            "🧠 RDP Challenge campaign complete.\n\n"
            f"📡 Published: {result.get('published', 0)}/{result.get('total', 0)}\n"
            f"✍️ Content source: {result.get('source', 'fallback')}"
        )


@router.message(Command("rdp_challenge"))
async def start_challenge_command(message: Message):
    status = await message.answer("🧠 Building a safe AI RDP challenge for all active channels...")
    result = await create_and_publish_campaign()
    if result.get("status") == "no_channels":
        await status.edit_text("⚠️ No active channels are configured.")
    elif result.get("status") == "locked":
        await status.edit_text("⏳ Another challenge campaign is already being published.")
    else:
        await status.edit_text(
            "🧠 RDP Challenge campaign complete.\n\n"
            f"📡 Published: {result.get('published', 0)}/{result.get('total', 0)}\n"
            f"✍️ Content source: {result.get('source', 'fallback')}"
        )


@router.callback_query(F.data.startswith("rdp_ch:"))
async def answer_challenge(callback: CallbackQuery):
    try:
        _, challenge_id, selected = callback.data.split(":", 2)
        selected_index = int(selected)
    except (AttributeError, ValueError):
        await callback.answer("This challenge button is invalid.", show_alert=True)
        return

    language = "en"
    if callback.from_user and callback.from_user.language_code:
        language = callback.from_user.language_code[:2].lower()
    result = await record_answer(
        challenge_id=challenge_id,
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        selected_index=selected_index,
        channel_id=callback.message.chat.id if callback.message and callback.message.chat else None,
        language=language,
    )
    if result["status"] == "expired":
        await callback.answer("This challenge has expired.", show_alert=True)
    elif result["status"] == "invalid_answer":
        await callback.answer("This answer is invalid.", show_alert=True)
    elif result["status"] == "already_answered":
        await callback.answer("You already answered this challenge.", show_alert=True)
    else:
        verdict = "✅ Correct!" if result["is_correct"] else "❌ Not quite."
        feedback = f"{verdict}\n\n{result['explanation']}"
        await callback.answer(feedback[:190], show_alert=True)


@router.message(Command("challenge_stats"))
async def challenge_stats(message: Message):
    async with AsyncSessionLocal() as session:
        challenge = (
            await session.execute(
                select(RDPChallenge).order_by(RDPChallenge.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
    if not challenge:
        await message.answer("No RDP challenge campaign has been created yet.")
        return
    stats = await get_campaign_stats(str(challenge.id))
    await message.answer(
        f"🧠 Latest RDP Challenge\n\n"
        f"📊 Answers: {stats['total']}\n"
        f"✅ Correct: {stats['correct']}\n"
        f"📡 Status: {challenge.status}"
    )