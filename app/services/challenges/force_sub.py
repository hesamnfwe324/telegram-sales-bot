"""
Force-subscription gate for the public challenge bot.

How it works
------------
1. On every protected handler (including /start) call:
       allowed, statuses = await check_membership(bot, user_id)
2. If allowed -> proceed normally.
3. If not allowed -> call send_gate(message, statuses) to show the join screen.
4. When the user clicks the verify button call:
       invalidate_cache(user_id)
       allowed, statuses = await check_membership(bot, user_id, force=True)

Channel discovery
-----------------
Required channels come from the `channels` DB table where:
  - is_active   = True
  - require_join = True
Channels are populated via the admin-bot "Scan channels" feature (auto_discover.py).

getChatMember notes
-------------------
- Public channels (@username known): works WITHOUT bot being admin. Use @username.
- Private channels (no username, only numeric ID): bot MUST be admin of that channel.
We always try @username first, then fall back to the numeric ID.
Any exception is logged and treated as "unverified" (gate stays closed).
"""

from __future__ import annotations

import asyncio
import time

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel

logger = get_logger(__name__)

# per-user result cache: {user_id: (monotonic_ts, allowed, statuses)}
_cache: dict[int, tuple[float, bool, list[dict]]] = {}
_CACHE_TTL: float = 60.0  # seconds


def invalidate_cache(user_id: int) -> None:
    """Remove the cached result for a user.

    Call this before re-checking so the bot contacts Telegram fresh instead
    of returning the old cached answer.
    """
    _cache.pop(user_id, None)


# ── internal helpers ───────────────────────────────────────────────────────

def _join_url(channel: TelegramChannel) -> str | None:
    """Return the best available join URL for a channel."""
    meta = channel.metadata_ or {}
    invite = meta.get("invite_link") or meta.get("join_link")
    if invite:
        return str(invite)
    if channel.username:
        return "https://t.me/" + channel.username.lstrip("@")
    return None


async def _load_required_channels() -> list[TelegramChannel]:
    """Return active channels that require membership."""
    try:
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                select(TelegramChannel)
                .where(
                    TelegramChannel.is_active.is_(True),
                    TelegramChannel.require_join.is_(True),
                )
                .order_by(TelegramChannel.created_at)
            )
            return list(rows.scalars().all())
    except Exception as exc:
        logger.error("force_sub_db_load_failed", error=str(exc))
        return []


async def _check_one(
    bot: Bot, user_id: int, channel: TelegramChannel
) -> dict[str, str | None]:
    """Check one channel. Returns {"name", "status", "link"}.

    status values:
      "joined"     - user is member / admin / creator
      "not_joined" - user is not a member (left / kicked / never joined)
      "unverified" - all Telegram API calls failed (bot not admin, network, etc.)
    """
    name = channel.display_name or channel.username or str(channel.telegram_channel_id)
    link = _join_url(channel)

    # Build list of chat_id values to try.
    # @username works for public channels without the bot being an admin.
    # Numeric ID works when the bot IS an admin (also covers private channels).
    chat_ids: list[str | int] = []
    if channel.username:
        chat_ids.append("@" + channel.username.lstrip("@"))
    chat_ids.append(channel.telegram_channel_id)

    last_error: str = ""
    for chat_id in chat_ids:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            raw = getattr(member.status, "value", str(member.status))
            joined = raw in {"creator", "administrator", "member"}
            if raw == "restricted":
                joined = bool(getattr(member, "is_member", False))
            status = "joined" if joined else "not_joined"
            logger.info(
                "force_sub_ok",
                user_id=user_id,
                channel=name,
                chat_id=str(chat_id),
                tg_status=raw,
                result=status,
            )
            return {"name": name, "status": status, "link": link}
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "force_sub_attempt_failed",
                user_id=user_id,
                channel=name,
                chat_id=str(chat_id),
                error=last_error,
            )

    # All attempts failed
    logger.error(
        "force_sub_all_failed",
        user_id=user_id,
        channel=name,
        error=last_error,
    )
    return {"name": name, "status": "unverified", "link": link}


# ── public API ─────────────────────────────────────────────────────────────

async def check_membership(
    bot: Bot,
    user_id: int,
    *,
    force: bool = False,
) -> tuple[bool, list[dict[str, str | None]]]:
    """Check that user_id is a member of every required channel.

    Parameters
    ----------
    bot:     The aiogram Bot instance of the public bot.
    user_id: Telegram user ID to check.
    force:   If True, bypass the cache and contact Telegram directly.

    Returns
    -------
    (allowed, statuses)
      allowed  - True only when every required channel returned "joined".
      statuses - list of {"name", "status", "link"} for each required channel.
    """
    now = time.monotonic()

    if not force and user_id in _cache:
        ts, cached_allowed, cached_statuses = _cache[user_id]
        if now - ts < _CACHE_TTL:
            logger.debug("force_sub_cache_hit", user_id=user_id, allowed=cached_allowed)
            return cached_allowed, cached_statuses

    channels = await _load_required_channels()

    if not channels:
        logger.warning("force_sub_no_channels_configured", user_id=user_id)
        fallback: list[dict[str, str | None]] = [
            {
                "name": "کانال‌های رسمی Upgrade Team",
                "status": "unverified",
                "link": getattr(settings, "REQUIRED_CHANNEL_FOLDER_LINK", None) or None,
            }
        ]
        _cache[user_id] = (now, False, fallback)
        return False, fallback

    statuses = list(
        await asyncio.gather(*(_check_one(bot, user_id, ch) for ch in channels))
    )
    allowed = all(s["status"] == "joined" for s in statuses)

    _cache[user_id] = (now, allowed, statuses)
    logger.info(
        "force_sub_result",
        user_id=user_id,
        channels=len(statuses),
        allowed=allowed,
        not_joined=sum(1 for s in statuses if s["status"] == "not_joined"),
        unverified=sum(1 for s in statuses if s["status"] == "unverified"),
    )
    return allowed, statuses


def build_gate_message(
    statuses: list[dict[str, str | None]],
) -> tuple[str, InlineKeyboardMarkup]:
    """Build gate message text + keyboard from channel statuses."""
    lines = [
        "<b>⛔ عضویت اجباری</b>",
        "",
        "برای استفاده از ربات باید در <b>تمام</b> کانال‌های زیر عضو باشید.",
        "",
    ]
    buttons: list[list[InlineKeyboardButton]] = []

    for s in statuses:
        name = s.get("name") or "Channel"
        link = s.get("link")
        icon = "✅" if s.get("status") == "joined" else "❌"
        label = f"{icon}  {name}"
        if link:
            buttons.append([InlineKeyboardButton(text=label, url=link)])
        else:
            lines.append(f"{icon} {name}")

    folder_link = getattr(settings, "REQUIRED_CHANNEL_FOLDER_LINK", None)
    if folder_link and not all(s.get("link") for s in statuses):
        buttons.append(
            [InlineKeyboardButton(text="📂 مشاهده همه کانال‌ها", url=folder_link)]
        )

    lines += ["", "پس از عضویت در همه کانال‌ها روی دکمه زیر بزنید:"]
    buttons.append(
        [InlineKeyboardButton(text="✅ بررسی عضویت", callback_data="fsub_verify")]
    )

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_gate(
    message: Message, statuses: list[dict[str, str | None]]
) -> None:
    """Send the force-subscription gate to the user."""
    text, kb = build_gate_message(statuses)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
