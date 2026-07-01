from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from app.services.admin_bot.keyboards import control_kb, back_kb
from app.cache.redis_client import cache_set, cache_get
from app.core.logging import get_logger
import asyncio
import random

router = Router()
logger = get_logger(__name__)

_userbot_manager = None


def set_userbot_manager(manager) -> None:
    global _userbot_manager
    _userbot_manager = manager


@router.message(Command("control"))
@router.callback_query(F.data == "control")
async def show_control(event: Message | CallbackQuery):
    msg = event if isinstance(event, Message) else event.message
    posting_paused = await cache_get("system:posting_paused")
    status = "⏸ PAUSED" if posting_paused else "▶️ ACTIVE"
    text = (
        f"⚙️ *System Control*\n\n"
        f"📢 Posting status: *{status}*\n\n"
        "Select an action:"
    )
    await msg.answer(text, parse_mode="Markdown", reply_markup=control_kb())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data == "ctrl_start")
async def ctrl_start(callback: CallbackQuery):
    if not _userbot_manager:
        await callback.message.answer("❌ UserBot manager not available.", reply_markup=back_kb())
        await callback.answer()
        return

    if _userbot_manager.is_running():
        # Check if accounts are actually connected — not just the flag
        accounts = _userbot_manager.list_accounts()
        connected = [a for a in accounts if a.get("is_connected")]
        if connected:
            await callback.message.answer(
                f"ℹ️ UserBot is already running. {len(connected)} account(s) connected.",
                reply_markup=back_kb(),
            )
            await callback.answer()
            return
        # Running flag is True but no accounts connected — restart automatically
        logger.warning("ctrl_start_no_accounts_restarting")
        await _userbot_manager.stop()

    await _userbot_manager.start()
    accounts = _userbot_manager.list_accounts()
    connected = [a for a in accounts if a.get("is_connected")]
    if connected:
        await callback.message.answer(
            f"✅ UserBot started. {len(connected)} account(s) connected.",
            reply_markup=back_kb(),
        )
    else:
        await callback.message.answer(
            "⚠️ UserBot started but *no accounts connected*.\n\n"
            "Make sure at least one Telegram account has been added with a valid session string.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
    await callback.answer()


@router.callback_query(F.data == "ctrl_stop")
async def ctrl_stop(callback: CallbackQuery):
    if _userbot_manager:
        await _userbot_manager.stop()
        await callback.message.answer("⏹️ UserBot stopped.", reply_markup=back_kb())
    else:
        await callback.message.answer("❌ UserBot manager not available.", reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == "ctrl_restart")
async def ctrl_restart(callback: CallbackQuery):
    if not _userbot_manager:
        await callback.message.answer("❌ UserBot manager not available.", reply_markup=back_kb())
        await callback.answer()
        return
    await _userbot_manager.stop()
    await _userbot_manager.start()
    accounts = _userbot_manager.list_accounts()
    connected = [a for a in accounts if a.get("is_connected")]
    if connected:
        await callback.message.answer(
            f"🔄 UserBot restarted. {len(connected)} account(s) connected.",
            reply_markup=back_kb(),
        )
    else:
        await callback.message.answer(
            "🔄 UserBot restarted but *no accounts connected*.\n\n"
            "Add a Telegram account session to get started.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
    await callback.answer()


@router.callback_query(F.data == "ctrl_pause_posting")
async def ctrl_pause_posting(callback: CallbackQuery):
    await cache_set("system:posting_paused", True, ttl=86400 * 7)
    await callback.message.answer("⏸️ Posting paused.", reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == "ctrl_resume_posting")
async def ctrl_resume_posting(callback: CallbackQuery):
    from app.cache.redis_client import cache_delete
    await cache_delete("system:posting_paused")
    await callback.message.answer("▶️ Posting resumed.", reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == "ctrl_scan_channels")
async def ctrl_scan_channels(callback: CallbackQuery):
    await callback.message.answer("📡 در حال اسکن کانال‌ها... لطفاً صبر کنید.")
    await callback.answer()

    if not _userbot_manager:
        await callback.message.answer("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
        return

    accounts = _userbot_manager.list_accounts()
    if not accounts:
        await callback.message.answer("❌ هیچ اکانتی متصل نیست.", reply_markup=back_kb())
        return

    total_added = 0
    total_found = 0
    report_lines = []

    from app.services.channel.auto_discover import discover_and_register_channels

    for acc in accounts:
        if not acc["is_connected"]:
            continue
        result = await discover_and_register_channels(_userbot_manager, acc["account_id"])
        found = result.get("found", 0)
        added = result.get("added", 0)
        total_found += found
        total_added += added
        report_lines.append(f"📱 {acc['phone']}: {found} found, {added} new")

    report = "\n".join(report_lines) if report_lines else "No connected accounts to scan."
    await callback.message.answer(
        f"✅ *Scan complete*\n\n{report}\n\n"
        f"Total: {total_found} found, {total_added} added to DB.",
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )
