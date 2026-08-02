"""Force-subscription management handler.

Allows the admin to toggle per-channel عضویت اجباری (require_join) on the
challenge public bot without affecting the posting pipeline.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.services.admin_bot.keyboards import back_kb, force_sub_menu_kb

logger = get_logger(__name__)
router = Router()


async def _build_fsub_text() -> tuple[str, list[TelegramChannel]]:
    """Return (message_text, channels) for the force-sub menu."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TelegramChannel)
            .where(TelegramChannel.is_active.is_(True))
            .order_by(TelegramChannel.created_at)
        )
        channels = list(result.scalars().all())

    if not channels:
        return "⚠️ هیچ کانال فعالی در سیستم ثبت نشده است.", []

    lines = ["🔐 *عضویت اجباری — مدیریت کانال‌ها*\n"]
    lines.append("کانال‌هایی که کاربر باید قبل از ورود به چالش عضو آن‌ها باشد را انتخاب کنید:\n")
    for ch in channels:
        name = ch.display_name or ch.username or str(ch.telegram_channel_id)
        status = "✅ فعال" if ch.require_join else "❌ غیرفعال"
        lines.append(f"• {name} — {status}")

    lines.append("\nبرای تغییر وضعیت هر کانال روی دکمه آن کلیک کنید.")
    return "\n".join(lines), channels


@router.callback_query(F.data == "fsub_menu")
async def show_fsub_menu(callback: CallbackQuery) -> None:
    text, channels = await _build_fsub_text()
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=force_sub_menu_kb(channels),
        )
    except Exception:
        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=force_sub_menu_kb(channels),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("fsub_toggle_"))
async def toggle_channel(callback: CallbackQuery) -> None:
    channel_id_str = callback.data.removeprefix("fsub_toggle_")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TelegramChannel).where(TelegramChannel.id.cast(str) == channel_id_str)
        )
        channel = result.scalar_one_or_none()
        if not channel:
            await callback.answer("❌ کانال پیدا نشد.", show_alert=True)
            return
        channel.require_join = not channel.require_join
        new_status = channel.require_join
        name = channel.display_name or channel.username or str(channel.telegram_channel_id)
        await session.commit()

    status_text = "✅ فعال شد" if new_status else "❌ غیرفعال شد"
    await callback.answer(f"{name}: {status_text}", show_alert=False)

    # Refresh the menu in place
    text, channels = await _build_fsub_text()
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=force_sub_menu_kb(channels),
        )
    except Exception:
        pass
