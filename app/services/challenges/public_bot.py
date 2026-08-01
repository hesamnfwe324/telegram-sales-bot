import asyncio
from html import escape
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.challenge import Challenge
from app.services.challenges.service import (
    challenge_summary,
    get_active_challenge,
    leaderboard,
    register_participant,
    submit_answer,
)

logger = get_logger(__name__)
router = Router()
_bot: Bot | None = None
_dispatcher: Dispatcher | None = None
_username: str | None = None
_polling_task: asyncio.Task | None = None


def get_public_bot_username() -> str | None:
    return _username or settings.PUBLIC_BOT_USERNAME or None


def _answer_keyboard(slug: str, answers: list[str]) -> InlineKeyboardMarkup:
    labels = ("A", "B", "C", "D")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{labels[index]}  •  {answer}", callback_data=f"challenge:{slug}:{index}")]
            for index, answer in enumerate(answers)
        ]
    )


def _challenge_text(challenge: Challenge) -> str:
    return (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "      <b>UPGRADE TEAM</b>\n"
        "      <b>RDP SECURITY CHALLENGE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{escape(challenge.title)}</b>\n\n"
        f"🎯 <b>Challenge Brief</b>\n{escape(challenge.question)}\n\n"
        f"🎁 <b>Reward:</b> {escape(challenge.reward)}\n"
        f"⏱ <b>Deadline:</b> {challenge.ends_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "<i>Select the best answer below.</i>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


@router.message(CommandStart())
async def start(message: Message):
    args = (message.text or "").split(maxsplit=1)
    slug = args[1].removeprefix("challenge_") if len(args) > 1 else ""
    async with AsyncSessionLocal() as session:
        challenge = (
            await session.scalar(select(Challenge).where(Challenge.slug == slug))
            if slug
            else await get_active_challenge(session)
        )
        if not challenge or challenge.status != "active":
            await message.answer(
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<b>UPGRADE TEAM</b>\n"
                "<b>RDP SECURITY CHALLENGE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "There is no active challenge right now.\n"
                "Please check back soon.",
                parse_mode=ParseMode.HTML,
            )
            return
        if challenge.language != "en":
            await message.answer(
                "<b>UPGRADE TEAM</b>\n\n"
                "This challenge has expired. Please use the latest challenge link.",
                parse_mode=ParseMode.HTML,
            )
            return
        user = message.from_user
        participant = await register_participant(
            session,
            challenge,
            user.id,
            user.username,
            user.full_name,
        )
        await message.answer(
            _challenge_text(challenge),
            parse_mode=ParseMode.HTML,
            reply_markup=_answer_keyboard(challenge.slug, challenge.answers)
            if not participant.answer_submitted
            else None,
        )


@router.callback_query(F.data.startswith("challenge:"))
async def answer(callback: CallbackQuery):
    try:
        _, slug, raw_index = callback.data.split(":", 2)
        answer_index = int(raw_index)
    except (AttributeError, ValueError):
        await callback.answer("Invalid answer. Please try again.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        challenge = await session.scalar(select(Challenge).where(Challenge.slug == slug))
        if not challenge or challenge.status != "active":
            await callback.answer("This challenge has ended.", show_alert=True)
            return
        if challenge.language != "en":
            await callback.answer("This challenge is no longer available.", show_alert=True)
            return
        participant = await register_participant(
            session,
            challenge,
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name,
        )
        if participant.answer_submitted:
            await callback.answer("You have already answered this challenge.", show_alert=True)
            return
        correct = await submit_answer(session, challenge, participant, answer_index)
        await callback.answer(
            "Correct answer — 10 points earned!" if correct else "Not quite. Keep learning and try the next challenge!",
            show_alert=True,
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "✅ <b>Answer recorded.</b> View the current leaderboard with /leaderboard."
            if correct
            else "✅ <b>Answer recorded.</b> Watch for the next Upgrade Team challenge.",
            parse_mode=ParseMode.HTML,
        )


@router.message(Command("leaderboard"))
async def show_leaderboard(message: Message):
    async with AsyncSessionLocal() as session:
        challenge = await get_active_challenge(session)
        if not challenge:
            await message.answer("There is no active challenge right now.")
            return
        rows = await leaderboard(session, challenge.id)
    lines = ["🏆 <b>UPGRADE TEAM LEADERBOARD</b>", ""]
    for index, row in enumerate(rows, 1):
        name = row.username and f"@{row.username}" or row.display_name or "Participant"
        lines.append(f"<b>{index}.</b> {escape(name)}  ·  {row.points} points")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("challenges"))
async def challenge_help(message: Message):
    await message.answer(
        "<b>UPGRADE TEAM CHALLENGES</b>\n\n"
        "Open the latest challenge link from our channel and select one answer.\n"
        "Each participant gets one attempt. Results are based on correctness and response time.\n\n"
        "View the leaderboard: /leaderboard",
        parse_mode=ParseMode.HTML,
    )


def get_public_bot() -> Bot | None:
    return _bot


async def _run_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    while True:
        try:
            await dispatcher.start_polling(bot, allowed_updates=["message", "callback_query"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("public_bot_polling_failed", error=str(exc))
            await asyncio.sleep(5)


async def setup_public_bot() -> None:
    global _bot, _dispatcher, _username, _polling_task
    if not settings.public_bot_token:
        logger.warning("public_bot_token_not_set")
        return
    _bot = Bot(
        token=settings.public_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    _dispatcher = Dispatcher(storage=MemoryStorage())
    _dispatcher.include_router(router)
    try:
        me = await _bot.get_me()
        _username = me.username
    except Exception as exc:
        logger.error("public_bot_identity_failed", error=str(exc))
    webhook_url = (
        os.environ.get("WEBHOOK_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    )
    if webhook_url:
        url = webhook_url.rstrip("/") + "/tg-api/public-bot/webhook"
        try:
            await _bot.set_webhook(url=url, drop_pending_updates=True, allowed_updates=["message", "callback_query"])
            logger.info("public_bot_webhook_set", url=url)
            return
        except Exception as exc:
            logger.error("public_bot_webhook_failed_falling_back_polling", error=str(exc))
    # Telegram refuses getUpdates while any webhook is configured. Always clear
    # stale webhooks before polling so /start keeps working after a redeploy.
    try:
        await _bot.delete_webhook(drop_pending_updates=False)
        logger.info("public_bot_webhook_cleared_for_polling")
    except Exception as exc:
        logger.warning("public_bot_webhook_clear_failed", error=str(exc))
    _polling_task = asyncio.create_task(_run_polling(_bot, _dispatcher))
    logger.info("public_bot_polling_started")


async def process_update(update_data: dict) -> None:
    if not _bot or not _dispatcher:
        return
    try:
        from aiogram.types import Update

        update = Update.model_validate(update_data)
        await _dispatcher.feed_update(_bot, update)
    except Exception as exc:
        logger.error("public_bot_update_processing_failed", error=str(exc))


async def shutdown_public_bot() -> None:
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        _polling_task = None
    if _bot:
        try:
            await _bot.session.close()
        except Exception as exc:
            logger.error("public_bot_shutdown_failed", error=str(exc))