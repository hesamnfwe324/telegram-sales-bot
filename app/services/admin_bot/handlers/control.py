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
    """Send a free RDP/server post immediately to ALL active channels.

    Manual admin override — bypasses cooldown, channel locks, and opt-out
    flags.  Handles Telegram FloodWait with automatic wait + one retry.
    """
    status_msg = await callback.message.answer(
      "🖥 *در حال اسکن برای سرور رایگان...*\n\n"
      "⏳ اسکنر در حال جستجوی IP با پورت 3389 باز است. چند ثانیه صبر کنید...",
      parse_mode="Markdown",
    )
    await callback.answer()

    if not _userbot_manager:
      await status_msg.edit_text("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
      return

    # ── Step 1: RDP scanner ──────────────────────────────────────────────────
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
          f"❌ *خطا در اسکن:*\n`{str(e)[:200]}`\n\nاسکنر نتوانست IP پیدا کند.",
          parse_mode="Markdown", reply_markup=back_kb(),
      )
      return

    if not rdp_result:
      await status_msg.edit_text(
          "⚠️ *هیچ سرور بازی پیدا نشد.*\n\n"
          "اسکنر همه کشورها را بررسی کرد ولی پورت 3389 باز پیدا نکرد.\n"
          "دوباره امتحان کنید.",
          parse_mode="Markdown", reply_markup=back_kb(),
      )
      return

    # ── Step 2: Show result ──────────────────────────────────────────────────
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

    # ── Step 3: Client map ───────────────────────────────────────────────────
    accounts = _userbot_manager.list_accounts()
    connected_accounts = [a for a in accounts if a["is_connected"]]
    if not connected_accounts:
      await status_msg.edit_text(
          "❌ *هیچ یوزربات متصلی وجود ندارد.*\n\nلطفاً ابتدا UserBot را Start کنید.",
          parse_mode="Markdown", reply_markup=back_kb(),
      )
      return
    client_map = {str(a["account_id"]): _userbot_manager.get_client(a["account_id"]) for a in connected_accounts}
    fallback_client = _userbot_manager.get_client(connected_accounts[0]["account_id"])

    # ── Step 4: ALL active channels — no cooldown filter, no lock check ──────
    from app.services.channel.auto_poster import _get_active_channels, mark_channel_posted, _toggle_post_mode
    all_channels = await _get_active_channels()
    if not all_channels:
      await status_msg.edit_text("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
      return

    # ── Step 5: Banner image ─────────────────────────────────────────────────
    from app.services.content.rdp_post_builder import build_rdp_post
    from app.services.channel.publisher import (
      _parse_image_urls, _download_with_fallbacks, _build_post_text,
      _read_local_file, _FILE_MARKER, _BANNER_REL_PATH,
    )
    _tmp, rdp_image_urls = build_rdp_post(
      ip=ip, port=port, username=username, password=password,
      country_name=country_name, country_flag=country_flag,
      seed=random.randint(100_000, 99_999_999), channel_username=None,
    )
    image_bytes = _read_local_file(_BANNER_REL_PATH)
    if image_bytes is None and rdp_image_urls:
      try:
          if rdp_image_urls.startswith(_FILE_MARKER):
              image_bytes = _read_local_file(rdp_image_urls[len(_FILE_MARKER):])
          else:
              urls = _parse_image_urls(rdp_image_urls)
              image_bytes = await asyncio.wait_for(_download_with_fallbacks(urls), timeout=20.0)
      except Exception as img_err:
          logger.warning("rdp_image_download_failed", error=str(img_err)[:80])

    # ── Step 6: Send to every channel — FloodWait-aware ──────────────────────
    import io
    from telethon.errors import FloodWaitError
    success = 0
    failed = 0
    failed_reasons = []

    for ch in all_channels:
      ch_id = str(ch.id)
      ch_client = client_map.get(str(ch.account_id), fallback_client)
      try:
          seed = random.randint(100_000, 99_999_999)
          ch_content, _ = build_rdp_post(
              ip=ip, port=port, username=username, password=password,
              country_name=country_name, country_flag=country_flag,
              seed=seed, channel_username=ch.username,
          )

          async def _do_send(client=ch_client, target=ch.telegram_channel_id,
                             content=ch_content, uname=ch.username, img=image_bytes):
              if img:
                  f = io.BytesIO(img)
                  f.name = "banner.jpg"
                  await client.send_file(target, f, caption=_build_post_text(content, uname, 1024), parse_mode="md")
              else:
                  await client.send_message(target, content, parse_mode="md")

          try:
              await _do_send()
          except FloodWaitError as fw:
              w = fw.seconds + 3
              logger.warning("rdp_flood_wait", channel=ch.telegram_channel_id, wait_sec=w)
              await asyncio.sleep(w)
              await _do_send()

          success += 1
          await mark_channel_posted(ch_id)
          _toggle_post_mode(ch_id)
          logger.info("rdp_sent_to_channel", channel=ch.telegram_channel_id)
          await asyncio.sleep(3)

      except Exception as ch_err:
          failed += 1
          err_msg = str(ch_err)[:80]
          failed_reasons.append(f"{ch.telegram_channel_id}: {err_msg}")
          logger.error("rdp_channel_send_failed", channel=ch.telegram_channel_id, error=err_msg)
          await asyncio.sleep(1)

    has_img = "✅" if image_bytes else "❌ (text only)"
    result_text = (
      f"{'✅' if success > 0 else '⚠️'} *پست سرور رایگان {'ارسال شد' if success > 0 else 'ارسال نشد'}!*\n\n"
      f"🌍 کشور: {country_flag} {country_name}\n"
      f"🔗 IP: `{ip}`\n"
      f"📡 موفق: `{success}` / `{len(all_channels)}` کانال\n"
      f"🖼 تصویر: {has_img}"
    )
    if failed_reasons:
      result_text += "\n\n❌ خطاها:\n" + "\n".join(f"`{r}`" for r in failed_reasons[:5])
    await status_msg.edit_text(result_text, parse_mode="Markdown", reply_markup=back_kb())
    logger.info("admin_rdp_post_done", success=success, failed=failed, ip=ip, country=country_name)

@router.callback_query(F.data == "ctrl_rdp_plans_post")
async def ctrl_rdp_plans_post(callback: CallbackQuery):
    """Send RDP pricing-plans post to ALL active channels.

    Manual admin override — no cooldown, no lock, FloodWait-aware with retry.
    Buttons attached via Telethon (Bot API cannot edit userbot messages).
    """
    status_msg = await callback.message.answer(
      "📋 *در حال ارسال پست پلن‌های RDP...*\n\n⏳ لطفاً صبر کنید...",
      parse_mode="Markdown",
    )
    await callback.answer()

    if not _userbot_manager:
      await status_msg.edit_text("❌ UserBot در دسترس نیست.", reply_markup=back_kb())
      return

    accounts = _userbot_manager.list_accounts()
    connected_accounts = [a for a in accounts if a["is_connected"]]
    if not connected_accounts:
      await status_msg.edit_text(
          "❌ *هیچ یوزربات متصلی وجود ندارد.*\n\nلطفاً ابتدا UserBot را Start کنید.",
          parse_mode="Markdown", reply_markup=back_kb(),
      )
      return
    client_map = {str(a["account_id"]): _userbot_manager.get_client(a["account_id"]) for a in connected_accounts}
    fallback_client = _userbot_manager.get_client(connected_accounts[0]["account_id"])

    from app.services.channel.auto_poster import _get_active_channels
    all_channels = await _get_active_channels()
    if not all_channels:
      await status_msg.edit_text("❌ هیچ کانال فعالی وجود ندارد.", reply_markup=back_kb())
      return

    from app.services.channel.publisher import _read_local_file, _BANNER_REL_PATH
    from app.services.content.rdp_plans_builder import build_rdp_plans_post
    import io
    from telethon.errors import FloodWaitError
    from telethon.tl.custom import Button as TelethonButton

    plans_buttons = [
      [TelethonButton.url("🛒  سفارش RDP", "https://t.me/vps24h")],
      [TelethonButton.url("💬  تماس با ادمین", "https://t.me/vps24h")],
    ]
    image_bytes = _read_local_file(_BANNER_REL_PATH)

    success = 0
    failed = 0
    failed_reasons = []

    for ch in all_channels:
      ch_client = client_map.get(str(ch.account_id), fallback_client)
      seed = random.randint(0, 9_999_999)
      post_text, _ = build_rdp_plans_post(channel_username=ch.username, seed=seed)

      async def _do_send_plans(client=ch_client, target=ch.telegram_channel_id,
                                text=post_text, img=image_bytes, btns=plans_buttons):
          if img:
              f = io.BytesIO(img)
              f.name = "banner.jpg"
              await client.send_file(target, f, caption=text, parse_mode="md", buttons=btns)
          else:
              await client.send_message(target, text, parse_mode="md", buttons=btns)

      try:
          try:
              await _do_send_plans()
          except FloodWaitError as fw:
              w = fw.seconds + 3
              logger.warning("rdp_plans_flood_wait", channel=ch.telegram_channel_id, wait_sec=w)
              await asyncio.sleep(w)
              await _do_send_plans()

          success += 1
          logger.info("rdp_plans_sent_to_channel", channel=ch.telegram_channel_id)
          await asyncio.sleep(3)

      except Exception as ch_err:
          failed += 1
          err_msg = str(ch_err)[:80]
          failed_reasons.append(f"{ch.telegram_channel_id}: {err_msg}")
          logger.error("rdp_plans_send_failed", channel=ch.telegram_channel_id, error=err_msg)
          await asyncio.sleep(1)

    has_img = "✅" if image_bytes else "❌ (text only)"
    result_text = (
      f"{'✅' if success > 0 else '⚠️'} *پست پلن‌های RDP {'ارسال شد' if success > 0 else 'ارسال نشد'}!*\n\n"
      f"📡 موفق: `{success}` / `{len(all_channels)}` کانال\n"
      f"🖼 تصویر: {has_img}"
    )
    if failed_reasons:
      result_text += "\n\n❌ خطاها:\n" + "\n".join(f"`{r}`" for r in failed_reasons[:5])
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
