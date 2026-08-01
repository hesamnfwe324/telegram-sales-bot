from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import desc, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.challenge import Challenge
from app.services.challenges.public_bot import get_public_bot_username
from app.services.challenges.service import challenge_summary, create_and_publish_challenge

logger = get_logger(__name__)
router = Router()


@router.message(Command("challenge"))
async def create_challenge_command(message: Message):
    topic = (message.text or "").partition(" ")[2].strip() or "ترفندهای جذاب RDP و امنیت سرور"
    status_message = await message.answer("در حال ساخت و انتشار چالش در همه کانال‌های فعال...")
    try:
        async with AsyncSessionLocal() as session:
            challenge, results = await create_and_publish_challenge(
                session,
                topic=topic[:500],
                language="fa",
                public_bot_username=get_public_bot_username(),
            )
        published = sum(1 for result in results.values() if result.get("status") == "published")
        await status_message.edit_text(
            f"✅ چالش ساخته و منتشر شد.\n\n"
            f"عنوان: {challenge.title}\n"
            f"کانال‌های موفق: {published}/{len(results)}\n"
            f"لینک داخلی: `/start challenge_{challenge.slug}`\n\n"
            "برای دیدن گزارش: /challenge_stats",
        )
    except Exception as exc:
        logger.error("manual_challenge_failed", error=str(exc))
        await status_message.edit_text(
            "❌ ساخت چالش انجام نشد. مطمئن شوید حداقل یک کانال فعال و یک اکانت متصل وجود دارد."
        )


@router.message(Command("challenge_stats"))
async def challenge_stats_command(message: Message):
    async with AsyncSessionLocal() as session:
        challenge = await session.scalar(select(Challenge).order_by(desc(Challenge.created_at)).limit(1))
        if not challenge:
            await message.answer("هنوز چالشی ساخته نشده است.")
            return
        summary = await challenge_summary(session, challenge)
    await message.answer(
        f"📊 گزارش آخرین چالش\n\n"
        f"عنوان: {summary['title']}\n"
        f"وضعیت: {summary['status']}\n"
        f"شرکت‌کننده: {summary['participants']}\n"
        f"پاسخ درست: {summary['correct_answers']}\n"
        f"کانال‌ها: {summary['channels']}\n"
        f"پایان: {summary['ends_at']}"
    )