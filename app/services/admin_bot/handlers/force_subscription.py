"""Force-subscription management handler.

Allows the admin to:
  • toggle per-channel عضویت اجباری (require_join) on the challenge public bot
  • add brand-new public channels by @username without a userbot scan
  • remove manually-added channels (account_id IS NULL)

Only channels with require_join=True are checked by the public challenge bot
when a user sends /start.  Channels added here do NOT enter the posting
pipeline — they are solely for the membership gate.
"""

import uuid
import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.services.admin_bot.keyboards import back_kb, force_sub_menu_kb

logger = get_logger(__name__)
router = Router()


# ── FSM ────────────────────────────────────────────────────────────────────

class AddChannelFSM(StatesGroup):
    waiting_for_input = State()


# ── helpers ────────────────────────────────────────────────────────────────

def _parse_username(text: str) -> str | None:
    """Extract a bare username from @username, t.me/username, or a plain word."""
    text = text.strip()
    # strip t.me prefix
    text = re.sub(r"^https?://t\.me/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^t\.me/", "", text, flags=re.IGNORECASE)
    # strip leading @
    text = text.lstrip("@")
    # drop query-string / path tails
    text = re.split(r"[/?]", text)[0].strip()
    # basic sanity: only alphanumeric + underscores, 5+ chars
    if re.fullmatch(r"[a-zA-Z0-9_]{3,}", text):
        return text
    return None


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="fsub_cancel_add")]
        ]
    )


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
        return (
            "⚠️ هیچ کانال فعالی در سیستم ثبت نشده است.\n\n"
            "با دکمه «اضافه کردن کانال» یک کانال عمومی اضافه کنید.",
            [],
        )

    lines = ["🔐 *عضویت اجباری — مدیریت کانال‌ها*\n"]
    lines.append(
        "کانال‌هایی که کاربر باید قبل از ورود به چالش عضو آن‌ها باشد را انتخاب کنید:\n"
    )
    for ch in channels:
        name = ch.display_name or ch.username or str(ch.telegram_channel_id)
        status = "✅ فعال" if ch.require_join else "❌ غیرفعال"
        tag = " _(دستی)_" if ch.account_id is None else ""
        lines.append(f"• {name}{tag} — {status}")

    lines.append("\nبرای تغییر وضعیت هر کانال روی دکمه آن کلیک کنید.")
    return "\n".join(lines), channels


# ── show menu ──────────────────────────────────────────────────────────────

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


# ── toggle require_join ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fsub_toggle_"))
async def toggle_channel(callback: CallbackQuery) -> None:
    channel_id_str = callback.data[len("fsub_toggle_"):]

    try:
        channel_uuid = uuid.UUID(channel_id_str)
    except ValueError:
        await callback.answer("❌ شناسه کانال نامعتبر است.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        channel = await session.get(TelegramChannel, channel_uuid)
        if channel is None:
            await callback.answer("❌ کانال پیدا نشد.", show_alert=True)
            return

        channel.require_join = not channel.require_join
        new_status = channel.require_join
        name = channel.display_name or channel.username or str(channel.telegram_channel_id)
        await session.commit()

    status_text = "✅ فعال شد" if new_status else "❌ غیرفعال شد"
    await callback.answer(f"{name}: {status_text}", show_alert=False)

    text, channels = await _build_fsub_text()
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=force_sub_menu_kb(channels),
        )
    except Exception:
        pass


# ── add channel (FSM) ──────────────────────────────────────────────────────

@router.callback_query(F.data == "fsub_add")
async def start_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddChannelFSM.waiting_for_input)
    await callback.message.edit_text(
        "🔗 <b>اضافه کردن کانال جدید</b>\n\n"
        "یوزرنیم یا لینک کانال <b>عمومی</b> را ارسال کنید:\n\n"
        "نمونه: <code>@mychannel</code>\n"
        "نمونه: <code>https://t.me/mychannel</code>\n\n"
        "⚠️ فقط کانال‌های عمومی (با @username) پشتیبانی می‌شوند.\n"
        "برای کانال خصوصی باید ربات چالش را ادمین کانال کنید.",
        parse_mode="HTML",
        reply_markup=_cancel_kb(),
    )
    await callback.answer()


@router.message(AddChannelFSM.waiting_for_input)
async def process_add_channel(message: Message, state: FSMContext) -> None:
    from aiogram.exceptions import TelegramAPIError
    from app.services.admin_bot.bot import get_bot

    text_in = (message.text or "").strip()
    username = _parse_username(text_in)

    if not username:
        await message.answer(
            "❌ یوزرنیم نامعتبر است.\n"
            "مثال درست: <code>@mychannel</code>",
            parse_mode="HTML",
            reply_markup=_cancel_kb(),
        )
        return

    # Verify the channel is reachable via the admin bot
    bot = get_bot()
    if bot is None:
        await message.answer("❌ ربات ادمین در دسترس نیست.", parse_mode="HTML")
        await state.clear()
        return

    try:
        chat = await bot.get_chat(f"@{username}")
    except TelegramAPIError as exc:
        await message.answer(
            f"❌ کانال <code>@{username}</code> پیدا نشد یا قابل دسترسی نیست:\n"
            f"<code>{exc}</code>",
            parse_mode="HTML",
            reply_markup=_cancel_kb(),
        )
        return

    # Normalise the Telegram channel ID to the -100XXXXXXXXX format
    raw_id = chat.id
    tg_id = int(f"-100{raw_id}") if raw_id > 0 else raw_id

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(TelegramChannel).where(
                TelegramChannel.telegram_channel_id == tg_id
            )
        )

        if existing is not None:
            if not existing.require_join:
                existing.require_join = True
                existing.is_active = True
                await session.commit()
                await message.answer(
                    f"✅ کانال <b>{chat.title}</b> فعال‌سازی شد.",
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    f"ℹ️ کانال <b>{chat.title}</b> قبلاً در لیست عضویت اجباری وجود دارد.",
                    parse_mode="HTML",
                )
        else:
            new_ch = TelegramChannel(
                account_id=None,          # manually added — no userbot
                telegram_channel_id=tg_id,
                username=username,
                display_name=chat.title,
                language="en",
                is_active=True,
                require_join=True,
                metadata_={"join_link": f"https://t.me/{username}"},
            )
            session.add(new_ch)
            await session.commit()
            logger.info("fsub_channel_added_manually", username=username, title=chat.title)
            await message.answer(
                f"✅ کانال <b>{chat.title}</b> (@{username}) با موفقیت اضافه شد.\n\n"
                f"از این به بعد کاربران باید عضو این کانال باشند تا بتوانند از ربات چالش استفاده کنند.",
                parse_mode="HTML",
            )

    await state.clear()

    # Refresh the force-sub menu
    menu_text, channels = await _build_fsub_text()
    await message.answer(
        menu_text,
        parse_mode="Markdown",
        reply_markup=force_sub_menu_kb(channels),
    )


@router.callback_query(F.data == "fsub_cancel_add")
async def cancel_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
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


# ── remove manually-added channel ─────────────────────────────────────────

@router.callback_query(F.data.startswith("fsub_remove_"))
async def remove_channel(callback: CallbackQuery) -> None:
    """Remove a manually-added channel (account_id IS NULL) from the gate."""
    channel_id_str = callback.data[len("fsub_remove_"):]

    try:
        channel_uuid = uuid.UUID(channel_id_str)
    except ValueError:
        await callback.answer("❌ شناسه کانال نامعتبر است.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        channel = await session.get(TelegramChannel, channel_uuid)
        if channel is None:
            await callback.answer("❌ کانال پیدا نشد.", show_alert=True)
            return

        if channel.account_id is not None:
            await callback.answer(
                "⚠️ این کانال از طریق اسکن اضافه شده و قابل حذف نیست. فقط غیرفعالش کنید.",
                show_alert=True,
            )
            return

        name = channel.display_name or channel.username or str(channel.telegram_channel_id)
        await session.delete(channel)
        await session.commit()
        logger.info("fsub_channel_removed_manually", name=name)

    await callback.answer(f"🗑 {name} حذف شد.", show_alert=False)

    text, channels = await _build_fsub_text()
    try:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=force_sub_menu_kb(channels),
        )
    except Exception:
        pass
