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


@router.callback_query(F.data == "ctrl_reset_cooldowns")
async def ctrl_reset_cooldowns(callback: CallbackQuery):
    """
    Reset all auto-poster cooldowns so every channel can post immediately
    in the next cycle.  Use this when channels are stuck because cooldowns
    were set erroneously (e.g. after the old bug that marked channels as
    posted even when nothing was actually sent).
    """
    await callback.answer()
    msg = await callback.message.answer("🔁 در حال پاک کردن cooldown‌ها...")
    try:
        from app.services.channel.auto_poster import reset_all_cooldowns
        deleted = await reset_all_cooldowns()
        await msg.edit_text(
            f"✅ *Cooldowns reset!*\n\n"
            f"🗑 {deleted} cooldown key(s) deleted from Redis.\n\n"
            "کانال‌ها در چرخه بعدی auto-poster (حداکثر چند دقیقه دیگر) پست می‌فرستند.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ خطا: `{str(e)[:200]}`",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )


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

    # ── Step 2: Show scan result & prepare ──────────────────────────────────
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

    # ── Step 3: Build per-account client map ────────────────────────────────
    # BUGFIX: previously used a single client (accounts[0]) for ALL channels.
    # Channels that belong to a different account were sent with the wrong
    # userbot, causing them to silently fail every cycle.
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
    # Map account_id (str) → its client; fall back to first connected account
    client_map = {
        str(a["account_id"]): _userbot_manager.get_client(a["account_id"])
        for a in connected_accounts
    }
    fallback_client = _userbot_manager.get_client(connected_accounts[0]["account_id"])

    # ── Step 4: Get active channels — filter per-channel cooldown ────────────
    # BUG FIX: previously checked only channels[0] cooldown and blocked ALL
    # channels. Now each channel is checked independently; only ready ones post.
    from app.services.channel.auto_poster import (
        _get_active_channels, _last_post_time,
        get_cooldown_remaining, mark_channel_posted, _toggle_post_mode,
        acquire_channel_lock, release_channel_lock,
    )
    all_channels = await _get_active_channels()
    if not all_channels:
        await status_msg.edit_text("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
        return

    # FIX: Manual admin trigger bypasses cooldown — admin button must reach
      # ALL active channels, not just those outside the auto-poster window.
      channels = all_channels

    # ── Step 5: Load banner image once (shared across channels) ─────────────
    from app.services.content.rdp_post_builder import build_rdp_post
    from app.services.channel.publisher import (
        _parse_image_urls, _download_with_fallbacks, _build_post_text,
        _read_local_file, _FILE_MARKER, _BANNER_REL_PATH,
    )

    # Build a temporary post to get the image URL
    _tmp_content, rdp_image_urls = build_rdp_post(
        ip=ip, port=port, username=username, password=password,
        country_name=country_name, country_flag=country_flag,
        seed=random.randint(100_000, 99_999_999),
        channel_username=None,
    )

    # Priority 1: always try the UPGRADE TEAM brand banner first (local file)
    image_bytes = _read_local_file(_BANNER_REL_PATH)

    # Priority 2: fall back to the post's own image_url (handles FILE: prefix)
    if image_bytes is None and rdp_image_urls:
        try:
            if rdp_image_urls.startswith(_FILE_MARKER):
                rel_path = rdp_image_urls[len(_FILE_MARKER):]
                image_bytes = _read_local_file(rel_path)
            else:
                urls = _parse_image_urls(rdp_image_urls)
                image_bytes = await asyncio.wait_for(
                    _download_with_fallbacks(urls), timeout=20.0
                )
        except (asyncio.TimeoutError, Exception) as img_err:
            logger.warning("rdp_image_download_failed", error=str(img_err)[:80])
            image_bytes = None

    # ── Step 6: Send to each channel with its own tag ────────────────────────
    import io
    success = 0
    failed = 0
    failed_reasons = []

    for ch in channels:
        if ch.metadata_ and ch.metadata_.get("rdp_enabled") is False:
            logger.info("rdp_channel_skipped_opt_out", channel=ch.telegram_channel_id)
            continue

        ch_id = str(ch.id)

        # Acquire per-channel lock — prevents duplicate posts if auto_poster runs simultaneously
        if not await acquire_channel_lock(ch_id, ttl=90):
            logger.info("rdp_admin_channel_locked_skip", channel=ch.telegram_channel_id)
            failed += 1
            failed_reasons.append(f"{ch.telegram_channel_id}: locked by another process")
            continue

        try:
            # Build post content specifically for this channel's username
            seed = random.randint(100_000, 99_999_999)
            ch_content, _ = build_rdp_post(
                ip=ip,
                port=port,
                username=username,
                password=password,
                country_name=country_name,
                country_flag=country_flag,
                seed=seed,
                channel_username=ch.username,
            )

            # Use the client that belongs to this channel's account
            ch_client = client_map.get(str(ch.account_id), fallback_client)

            if image_bytes:
                file_obj = io.BytesIO(image_bytes)
                file_obj.name = "banner.jpg"
                caption = _build_post_text(ch_content, ch.username, 1024)
                await ch_client.send_file(
                    ch.telegram_channel_id, file_obj,
                    caption=caption, parse_mode="md",
                )
            else:
                await ch_client.send_message(
                    ch.telegram_channel_id, ch_content, parse_mode="md",
                )

            success += 1
            await mark_channel_posted(ch_id)
            _toggle_post_mode(ch_id)
            logger.info("rdp_sent_to_channel", channel=ch.telegram_channel_id)
            await asyncio.sleep(2)

        except Exception as ch_err:
            failed += 1
            failed_reasons.append(f"{ch.telegram_channel_id}: {str(ch_err)[:60]}")
            logger.error("rdp_channel_send_failed", channel=ch.telegram_channel_id, error=str(ch_err))
        finally:
            await release_channel_lock(ch_id)

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


@router.callback_query(F.data == "ctrl_rdp_plans_post")
async def ctrl_rdp_plans_post(callback: CallbackQuery):
    """Send a beautiful RDP pricing-plans post immediately to all active channels."""
    status_msg = await callback.message.answer(
        "📋 *در حال ارسال پست پلن‌های RDP...*\n\n"
        "⏳ لطفاً صبر کنید...",
        parse_mode="Markdown",
    )
    await callback.answer()

    if not _userbot_manager:
        await status_msg.edit_text("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
        return

    # ── Build account_id → client map for all connected accounts ─────────────
    accounts = _userbot_manager.list_accounts()
    connected_accounts = [a for a in accounts if a["is_connected"]]
    if not connected_accounts:
        await status_msg.edit_text(
            "❌ *هیچ یوزربات متصلی وجود ندارد.*\n\nلطفاً ابتدا UserBot را Start کنید.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return
    # Map each account_id (str) → its Telethon client
    client_map = {
        str(a["account_id"]): _userbot_manager.get_client(a["account_id"])
        for a in connected_accounts
    }
    # Fallback client — used only if a channel's account is not in client_map
    fallback_client = _userbot_manager.get_client(connected_accounts[0]["account_id"])

    # ── Get active channels ───────────────────────────────────────────────────
    from app.services.channel.auto_poster import _get_active_channels
    all_channels = await _get_active_channels()
    if not all_channels:
        await status_msg.edit_text("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
        return

    # ── Load banner image once ────────────────────────────────────────────────
    from app.services.channel.publisher import _read_local_file, _BANNER_REL_PATH
    from app.services.content.rdp_plans_builder import build_rdp_plans_post
    from app.core.config import settings
    import httpx
    import io

    async def _add_plans_buttons(channel_id, message_id):
        """Edit the plans post to add glass inline URL buttons via admin bot."""
        bot_token = settings.ADMIN_BOT_TOKEN
        if not bot_token:
            return
        try:
            async with httpx.AsyncClient(timeout=8) as http:
                resp = await http.post(
                    f"https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup",
                    json={
                        "chat_id": channel_id,
                        "message_id": message_id,
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "🛒  سفارش RDP", "url": "https://t.me/vps24h"}],
                                [{"text": "💬  تماس با ادمین", "url": "https://t.me/vps24h"}],
                            ]
                        },
                    },
                )
                data = resp.json()
                if not data.get("ok"):
                    logger.warning("add_plans_buttons_failed", channel=str(channel_id), reason=data.get("description"))
        except Exception as exc:
            logger.warning("add_plans_buttons_exception", error=str(exc))

    image_bytes = _read_local_file(_BANNER_REL_PATH)

    # ── Send to each channel ─────────────────────────────────────────────────
    success = 0
    failed = 0
    failed_reasons = []

    for ch in all_channels:
        ch_id = str(ch.id)
        try:
            # Pick the client that owns this channel; fall back to any connected one
            ch_client = client_map.get(str(ch.account_id), fallback_client)
            seed = random.randint(0, 9_999_999)
            post_text, _ = build_rdp_plans_post(
                channel_username=ch.username,
                seed=seed,
            )

            if image_bytes:
                file_obj = io.BytesIO(image_bytes)
                file_obj.name = "banner.jpg"
                msg = await ch_client.send_file(
                    ch.telegram_channel_id, file_obj,
                    caption=post_text, parse_mode="md",
                )
            else:
                msg = await ch_client.send_message(
                    ch.telegram_channel_id, post_text, parse_mode="md",
                )
            await _add_plans_buttons(ch.telegram_channel_id, msg.id)

            success += 1
            logger.info("rdp_plans_sent_to_channel", channel=ch.telegram_channel_id)
            await asyncio.sleep(2)

        except Exception as ch_err:
            failed += 1
            failed_reasons.append(f"{ch.telegram_channel_id}: {str(ch_err)[:60]}")
            logger.error("rdp_plans_send_failed", channel=ch.telegram_channel_id, error=str(ch_err))

    has_img = "✅" if image_bytes else "❌ (text only)"
    result_text = (
        f"{'✅' if success > 0 else '⚠️'} *پست پلن‌های RDP {'ارسال شد' if success > 0 else 'ارسال نشد'}!*\n\n"
        f"📡 موفق: `{success}` / `{len(all_channels)}` کانال\n"
        f"🖼 تصویر: {has_img}"
    )
    if failed_reasons:
        result_text += "\n\n❌ خطاها:\n" + "\n".join(f"`{r}`" for r in failed_reasons[:3])

    await status_msg.edit_text(result_text, parse_mode="Markdown", reply_markup=back_kb())
    logger.info("admin_rdp_plans_post_done", success=success, failed=failed)


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


@router.message(Command("channel_diag"))
@router.callback_query(F.data == "ctrl_channel_diag")
async def channel_diag(event: Message | CallbackQuery):
    """
    Show per-channel diagnostic: account connectivity, cooldown status,
    and last publish result. Helps identify which channels never receive
    posts and exactly why (wrong account, disconnected, cooldown, etc.).
    """
    msg = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()

    status_msg = await msg.answer("🔍 در حال بررسی وضعیت کانال‌ها...")

    if not _userbot_manager:
        await status_msg.edit_text("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
        return

    from app.services.channel.auto_poster import _get_active_channels, get_cooldown_remaining
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select, desc
    from app.models.post import Post

    # Build set of connected account_ids
    connected_ids = {
        str(a["account_id"])
        for a in _userbot_manager.list_accounts()
        if a["is_connected"]
    }

    channels = await _get_active_channels()
    if not channels:
        await status_msg.edit_text("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
        return

    # Fetch last publish log for each channel from recent posts
    channel_last_result: dict[str, str] = {}
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Post)
                .where(Post.status.in_(["published", "failed"]))
                .order_by(desc(Post.published_at))
                .limit(50)
            )
            recent_posts = result.scalars().all()
            for post in recent_posts:
                log = post.publish_log or {}
                for ch_id_str, ch_result in log.items():
                    if ch_id_str not in channel_last_result:
                        channel_last_result[ch_id_str] = ch_result.get("status", "?")
    except Exception:
        pass

    lines = []
    problem_channels = []

    for ch in channels:
        ch_id = str(ch.id)
        name = ch.display_name or ch.username or str(ch.telegram_channel_id)
        acc_id = str(ch.account_id)
        acc_connected = acc_id in connected_ids
        cooldown = await get_cooldown_remaining(ch_id)
        last = channel_last_result.get(ch_id, "—")

        if not acc_connected:
            icon = "🔴"
            reason = "اکانت disconnect"
            problem_channels.append(f"  ❌ {name} → {reason}")
        elif cooldown > 0:
            h, m = divmod(cooldown, 3600)
            m = m // 60
            icon = "⏳"
            reason = f"cooldown {h}h{m:02d}m"
        elif last in ("error", "skipped"):
            icon = "⚠️"
            reason = f"آخرین نتیجه: {last}"
            problem_channels.append(f"  ⚠️ {name} → {reason}")
        else:
            icon = "✅"
            reason = f"آخرین: {last}" if last != "—" else "ready"

        lines.append(f"{icon} *{name[:30]}*\n    └ {reason}")

    body = "\n".join(lines)
    problems = ("\n\n🔎 *مشکل‌دار:*\n" + "\n".join(problem_channels)) if problem_channels else ""

    # Split into pages if too long
    MAX_CHARS = 3800
    if len(body) > MAX_CHARS:
        body = body[:MAX_CHARS] + "\n…(بقیه کانال‌ها حذف شد)"

    text = (
        f"📊 *وضعیت کانال‌ها* ({len(channels)} کانال)\n\n"
        f"{body}"
        f"{problems}"
    )
    await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=back_kb())
