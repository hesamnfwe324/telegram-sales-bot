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
        accounts = _userbot_manager.list_accounts()
        connected = [a for a in accounts if a.get("is_connected")]
        if connected:
            await callback.message.answer("ℹ️ UserBot is already running.", reply_markup=back_kb())
            await callback.answer()
            return
        logger.warning("ctrl_start_no_accounts_restarting")
        await _userbot_manager.stop()
    await _userbot_manager.start()
    accounts = _userbot_manager.list_accounts()
    connected = [a for a in accounts if a.get("is_connected")]
    if connected:
        await callback.message.answer(f"✅ UserBot started. {len(connected)} account(s) connected.", reply_markup=back_kb())
    else:
        await callback.message.answer(
            "⚠️ UserBot started but no accounts connected.\n\nMake sure at least one Telegram account has been added with a valid session string.",
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
    if _userbot_manager:
        await _userbot_manager.stop()
        await _userbot_manager.start()
        await callback.message.answer("🔄 UserBot restarted.", reply_markup=back_kb())
    else:
        await callback.message.answer("❌ UserBot manager not available.", reply_markup=back_kb())
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
        total_found += result.get("found", 0)
        total_added += result.get("added", 0)
        for ch in result.get("channels", []):
            name = ch.get("title") or ch.get("username") or "بدون نام"
            report_lines.append(f"  • {name}")

    channels_list = "\n".join(report_lines[:20]) if report_lines else "  (هیچ کانالی پیدا نشد)"

    text = (
        "📡 *نتیجه اسکن کانال‌ها*\n\n"
        f"🔍 پیدا شده: `{total_found}` کانال\n"
        f"✅ ثبت جدید: `{total_added}` کانال\n\n"
        f"*کانال‌های یافت‌شده:*\n{channels_list}"
    )
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_kb())


@router.callback_query(F.data == "ctrl_post_now")
async def ctrl_post_now(callback: CallbackQuery):
    await callback.message.answer("🚀 در حال ارسال پست فوری به همه کانال‌ها...")
    await callback.answer()

    if not _userbot_manager:
        await callback.message.answer("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
        return

    from app.services.channel.auto_poster import _post_to_channel, _get_active_channels, _last_post_time

    channels = await _get_active_channels()
    if not channels:
        await callback.message.answer("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
        return

    success = 0
    failed = 0
    now_ts = asyncio.get_event_loop().time()
    for ch in channels:
        ok = await _post_to_channel(_userbot_manager, ch)
        if ok:
            success += 1
            # Reset cooldown so auto_poster waits full interval before posting again
            _last_post_time[str(ch.id)] = now_ts
        else:
            failed += 1
        await asyncio.sleep(10)

    text = (
        "✅ پست فوری انجام شد\n\n"
        f"📤 موفق: `{success}` کانال\n"
        f"❌ ناموفق: `{failed}` کانال"
    )
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_kb())


@router.callback_query(F.data == "ctrl_rdp_post_now")
async def ctrl_rdp_post_now(callback: CallbackQuery):
    """Send a free RDP/server post immediately to all active channels."""
    status_msg = await callback.message.answer(
        "🖥 *در حال اسکن برای سرور رایگان...*\n\n"
        "⏳ اسکنر در حال جستجوی IP با پورت 3389 باز است. چند ثانیه صبر کنید...",
        parse_mode="Markdown",
    )
    await callback.answer()

    if not _userbot_manager:
        await status_msg.edit_text("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
        return

    # ── Step 1: Run RDP scanner ──────────────────────────────────────────────
    try:
        from app.services.scanner.rdp_scanner import scan_for_rdp
        try:
            rdp_result = await asyncio.wait_for(scan_for_rdp(), timeout=45.0)
        except asyncio.TimeoutError:
            rdp_result = None
            logger.warning("admin_rdp_scan_timeout")
    except Exception as e:
        logger.error("admin_rdp_scan_failed", error=str(e))
        await status_msg.edit_text(
            f"❌ *خطا در اسکن:*\n`{str(e)[:200]}`\n\n"
            "اسکنر نتوانست IP پیدا کند.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return

    if not rdp_result:
        await status_msg.edit_text(
            "⚠️ *هیچ سرور بازی پیدا نشد.*\n\n"
            "اسکنر همه کشورها را بررسی کرد ولی پورت 3389 باز پیدا نکرد.\n"
            "دوباره امتحان کنید.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return

    # ── Step 2: Build the post content ──────────────────────────────────────
    try:
        from app.services.content.rdp_post_builder import build_rdp_post
        seed = random.randint(100_000, 99_999_999)
        rdp_content, rdp_image_urls = build_rdp_post(
            ip=rdp_result["ip"],
            port=rdp_result["port"],
            username=rdp_result["username"],
            password=rdp_result["password"],
            country_name=rdp_result["country_name"],
            country_flag=rdp_result["country_flag"],
            seed=seed,
        )

        country_flag = rdp_result["country_flag"]
        country_name = rdp_result["country_name"]
        ip = rdp_result["ip"]
        port = rdp_result["port"]
        username = rdp_result["username"]
        password = rdp_result["password"]

        await status_msg.edit_text(
            f"✅ *سرور پیدا شد!* {country_flag} {country_name}\n\n"
            f"🔗 IP: `{ip}`\n"
            f"🔌 Port: `{port}`\n"
            f"👤 User: `{username}`\n"
            f"🔑 Pass: `{password}`\n\n"
            "📤 *در حال ارسال به همه کانال‌ها...*",
            parse_mode="Markdown",
        )

        # ── Step 3: Find a connected userbot client ───────────────────────────
        accounts = _userbot_manager.list_accounts()
        connected_accounts = [a for a in accounts if a["is_connected"]]
        if not connected_accounts:
            await status_msg.edit_text(
                "❌ *هیچ یوزربات متصلی وجود ندارد.*\n\n"
                "لطفاً ابتدا UserBot را Start کنید.",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
            return
        client = _userbot_manager.get_client(connected_accounts[0]["account_id"])

        # ── Step 4: Get active channels + cooldown check ──────────────────────
        from app.services.channel.auto_poster import (
            _get_active_channels, _last_post_time,
            get_cooldown_remaining, mark_channel_posted, _toggle_post_mode,
        )
        channels = await _get_active_channels()
        if not channels:
            await status_msg.edit_text(
                "❌ هیچ کانال فعالی وجود ندارد.",
                reply_markup=back_kb(),
            )
            return

        # Block manual post if still in 3-hour cooldown
        if channels:
            cooldown = await get_cooldown_remaining(str(channels[0].id))
            if cooldown > 0:
                h = cooldown // 3600
                m = (cooldown % 3600) // 60
                await status_msg.edit_text(
                    f"⏳ *هنوز باید صبر کنید!*\n\n"
                    f"آخرین پست کمتر از ۳ ساعت پیش ارسال شد.\n"
                    f"⏱ تا پست بعدی: *{h}h {m:02d}m* دیگر",
                    parse_mode="Markdown",
                    reply_markup=back_kb(),
                )
                return

        # ── Step 5: Download image (with short timeout, fall back to text) ────
        from app.services.channel.publisher import _parse_image_urls, _download_with_fallbacks, _build_post_text
        image_bytes = None
        if rdp_image_urls:
            try:
                urls = _parse_image_urls(rdp_image_urls)
                image_bytes = await asyncio.wait_for(
                    _download_with_fallbacks(urls), timeout=20.0
                )
            except (asyncio.TimeoutError, Exception) as img_err:
                logger.warning("rdp_image_download_failed", error=str(img_err)[:80])
                image_bytes = None

        # ── Step 6: Send to each channel ──────────────────────────────────────
        import io
        success = 0
        failed = 0
        failed_reasons = []
        for ch in channels:
            # Skip channels that explicitly opted out of RDP posts
            if ch.metadata_ and ch.metadata_.get("rdp_enabled") is False:
                logger.info("rdp_channel_skipped_opt_out", channel=ch.telegram_channel_id)
                continue
            try:
                caption = _build_post_text(rdp_content, ch.username, 1024)
                if image_bytes:
                    file_obj = io.BytesIO(image_bytes)
                    file_obj.name = "rdp.jpg"
                    await client.send_file(ch.telegram_channel_id, file_obj, caption=caption, parse_mode="md")
                else:
                    await client.send_message(ch.telegram_channel_id, rdp_content, parse_mode="md")
                success += 1
                # Mark 3-hour cooldown in Redis + toggle next post mode to media
                await mark_channel_posted(str(ch.id))
                _toggle_post_mode(str(ch.id))
                logger.info("rdp_sent_to_channel", channel=ch.telegram_channel_id)
                await asyncio.sleep(2)
            except Exception as ch_err:
                failed += 1
                failed_reasons.append(f"{ch.telegram_channel_id}: {str(ch_err)[:60]}")
                logger.error("rdp_channel_send_failed", channel=ch.telegram_channel_id, error=str(ch_err))

        has_img = "✅" if image_bytes else "❌ (text only)"
        result_text = (
            f"{'✅' if success > 0 else '⚠️'} *پست سرور رایگان {'ارسال شد' if success > 0 else 'ارسال نشد'}!*\n\n"
            f"🌍 کشور: {country_flag} {country_name}\n"
            f"🔗 IP: `{ip}`\n"
            f"📡 موفق: `{success}` / `{len(channels)}` کانال\n"
            f"🖼 تصویر: {has_img}"
        )
        if failed_reasons:
            result_text += f"\n\n❌ خطاها:\n" + "\n".join(f"`{r}`" for r in failed_reasons[:3])

        await status_msg.edit_text(result_text, parse_mode="Markdown", reply_markup=back_kb())
        logger.info("admin_rdp_post_done", success=success, failed=failed, ip=ip, country=country_name)

    except Exception as outer_err:
        logger.error("ctrl_rdp_post_now_unhandled", error=str(outer_err))
        try:
            await status_msg.edit_text(
                f"❌ *خطای غیرمنتظره:*\n`{str(outer_err)[:400]}`\n\n"
                "لطفاً دوباره امتحان کنید.",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
        except Exception:
            pass


@router.message(Command("post_now"))
async def cmd_post_now(message: Message):
    await message.answer("🚀 در حال ارسال پست فوری...")

    if not _userbot_manager:
        await message.answer("❌ UserBot در دسترس نیست.")
        return

    from app.services.channel.auto_poster import _post_to_channel, _get_active_channels, _last_post_time

    channels = await _get_active_channels()
    if not channels:
        await message.answer("❌ هیچ کانال فعالی وجود ندارد.")
        return

    success = 0
    failed = 0
    for ch in channels:
        _last_post_time[str(ch.id)] = 0
        ok = await _post_to_channel(_userbot_manager, ch)
        if ok:
            success += 1
        else:
            failed += 1
        await asyncio.sleep(10)

    await message.answer(
        f"✅ موفق: `{success}` | ❌ ناموفق: `{failed}`",
        parse_mode="Markdown",
        reply_markup=back_kb()
    )


@router.message(Command("scan_channels"))
async def cmd_scan_channels(message: Message):
    await message.answer("📡 در حال اسکن کانال‌ها...")

    if not _userbot_manager:
        await message.answer("❌ UserBot در دسترس نیست.")
        return

    accounts = _userbot_manager.list_accounts()
    if not accounts:
        await message.answer("❌ هیچ اکانتی متصل نیست.")
        return

    from app.services.channel.auto_discover import discover_and_register_channels

    total_added = 0
    total_found = 0
    report_lines = []

    for acc in accounts:
        if not acc["is_connected"]:
            continue
        result = await discover_and_register_channels(_userbot_manager, acc["account_id"])
        total_found += result.get("found", 0)
        total_added += result.get("added", 0)
        for ch in result.get("channels", []):
            name = ch.get("title") or ch.get("username") or "بدون نام"
            report_lines.append(f"  • {name}")

    channels_list = "\n".join(report_lines[:20]) if report_lines else "  (هیچ کانالی پیدا نشد)"
    text = (
        "📡 *نتیجه اسکن*\n\n"
        f"🔍 پیدا شده: `{total_found}`\n"
        f"✅ ثبت جدید: `{total_added}`\n\n"
        f"{channels_list}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=back_kb())
