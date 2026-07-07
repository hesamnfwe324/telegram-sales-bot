"""
Auto-poster — only posts free RDP/VPS scan results.

One post type only:
  - RDP scanner finds a live free server → posts its credentials
  - Scan fails or finds nothing → skips this cycle (no fallback AI posts)

KEY DESIGN:
  Scan ONCE per cycle, then post the same IP to ALL channels that are
  ready (not on cooldown). This way a scan timeout never blocks some
  channels because of another channel's failed scan.
"""
import asyncio
import hashlib
import io
import random
import time as _time
import uuid
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.channel.publisher import publish_post
from app.cache.redis_client import get_redis
from app.core.logging import get_logger

logger = get_logger(__name__)

TEHRAN = ZoneInfo("Asia/Tehran")

MIN_INTERVAL_SECONDS = 3 * 3600
COOLDOWN_SECONDS = MIN_INTERVAL_SECONDS


def _cooldown_key(channel_id: str) -> str:
    return f"autoposter:cooldown:{channel_id}"


async def get_cooldown_remaining(channel_id: str) -> int:
    from app.cache.redis_client import cache_get
    val = await cache_get(_cooldown_key(channel_id))
    if not val:
        return 0
    try:
        posted_at = float(val)
        elapsed = _time.time() - posted_at
        return max(0, int(COOLDOWN_SECONDS - elapsed))
    except Exception:
        return 0


def _lock_key(channel_id: str) -> str:
    return f"autoposter:lock:{channel_id}"


async def acquire_channel_lock(channel_id: str, ttl: int = 60) -> bool:
    """
    Try to acquire a short-lived distributed lock for a channel post.
    Returns True if the lock was acquired (caller may post).
    Returns False if another process is already posting to this channel.
    Uses Redis SET NX (atomic) to prevent duplicate concurrent posts.
    """
    try:
        r = await get_redis()
        acquired = await r.set(_lock_key(channel_id), "1", nx=True, ex=ttl)
        return bool(acquired)
    except Exception as e:
        logger.warning("channel_lock_acquire_failed", channel_id=channel_id, error=str(e)[:60])
        # If Redis fails, allow posting (better than silent drop)
        return True


async def release_channel_lock(channel_id: str) -> None:
    try:
        r = await get_redis()
        await r.delete(_lock_key(channel_id))
    except Exception:
        pass


async def mark_channel_posted(channel_id: str) -> None:
    from app.cache.redis_client import cache_set
    await cache_set(_cooldown_key(channel_id), str(_time.time()), ttl=COOLDOWN_SECONDS + 300)
    _last_post_time[channel_id] = asyncio.get_running_loop().time()


_recent_hashes: deque = deque(maxlen=300)
_last_post_time: dict[str, float] = {}
_post_mode: dict[str, str] = {}


def _toggle_post_mode(channel_id: str) -> None:
    """Toggle next post mode between 'text' and 'media' for a channel."""
    current = _post_mode.get(channel_id, "text")
    _post_mode[channel_id] = "media" if current == "text" else "text"


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode()).hexdigest()[:16]


def _is_duplicate(content: str) -> bool:
    return _content_hash(content) in _recent_hashes


def _record_hash(content: str) -> None:
    _recent_hashes.append(_content_hash(content))


async def _post_to_channel(userbot_manager, channel: TelegramChannel) -> bool:
    """
    Scan for a live RDP server and post it to a single channel.
    Used by the admin 'post_now' button which posts one channel at a time.
    For the auto-poster loop use _post_rdp_result_to_channel() instead
    so the scan is shared across all channels in one cycle.
    """
    try:
        from app.services.scanner.rdp_scanner import scan_for_rdp
        rdp_result = await asyncio.wait_for(scan_for_rdp(), timeout=45.0)
    except asyncio.TimeoutError:
        logger.warning("rdp_scan_timeout_skipping_channel", channel=channel.display_name)
        return False
    except Exception as e:
        logger.warning("rdp_scan_error_skipping_channel", channel=channel.display_name, error=str(e))
        return False

    if not rdp_result:
        logger.info("rdp_scan_no_result_skipping", channel=channel.display_name)
        return False

    return await _post_rdp_result_to_channel(rdp_result, channel)


async def _post_rdp_result_to_channel(rdp_result: dict, channel: TelegramChannel) -> bool:
    """
    Post an already-scanned RDP result to a single channel.
    Accepts a pre-scanned rdp_result so one scan can serve all channels
    in the same cycle — no redundant scans, no blocked channels.

    Uses a short-lived Redis lock to prevent duplicate posts when the
    auto-poster loop and an admin button run at the same time.
    """
    ch_id = str(channel.id)

    # Acquire lock — if another process is already posting to this channel, skip
    if not await acquire_channel_lock(ch_id, ttl=90):
        logger.info("rdp_post_skipped_locked", channel=channel.display_name)
        return False

    try:
        from app.services.content.rdp_post_builder import build_rdp_post

        lang = channel.language or "en"
        if lang == "fa":
            lang = "en"

        unique_seed = random.randint(100_000, 99_999_999)
        rdp_content, rdp_image_url = build_rdp_post(
            ip=rdp_result["ip"],
            port=rdp_result["port"],
            username=rdp_result["username"],
            password=rdp_result["password"],
            country_name=rdp_result["country_name"],
            country_flag=rdp_result["country_flag"],
            seed=unique_seed,
            channel_username=channel.username,
        )

        if _is_duplicate(rdp_content):
            logger.warning("rdp_post_duplicate_skipping", channel=channel.display_name)
            return False

        async with AsyncSessionLocal() as session:
            post = Post(
                account_id=channel.account_id,
                channel_ids=[ch_id],
                content=rdp_content,
                languages={lang: rdp_content},
                image_url=rdp_image_url,
                status="scheduled",
                scheduled_at=datetime.now(timezone.utc),
            )
            session.add(post)
            await session.flush()
            try:
                await publish_post(session, post)
                await session.commit()
                _record_hash(rdp_content)
                logger.info(
                    "rdp_post_sent",
                    channel=channel.display_name,
                    country=rdp_result["country_name"],
                    ip=rdp_result["ip"],
                )
                return True
            except Exception as e:
                post.status = "failed"
                await session.commit()
                logger.error("rdp_post_send_failed", channel=channel.display_name, error=str(e))
                return False
    finally:
        # Always release the lock — even on exception — so next cycle isn't blocked
        await release_channel_lock(ch_id)


async def _get_active_channels(account_id=None):
    async with AsyncSessionLocal() as session:
        q = select(TelegramChannel).where(TelegramChannel.is_active == True)
        if account_id:
            q = q.where(TelegramChannel.account_id == uuid.UUID(str(account_id)))
        result = await session.execute(q)
        return result.scalars().all()


async def run_auto_poster(userbot_manager):
    """
    Main auto-poster loop.

    FIX: Previously called _post_to_channel() per channel, which ran a
    separate scan for EACH channel. A scan timeout on channel N blocked
    channels N+1, N+2, ... and caused some channels to never post.

    Now: scan ONCE per cycle, post the result to ALL ready channels.
    Each channel still gets its own per-channel cooldown and its own
    post text (different seed → different channel tag line).
    """
    logger.info("auto_poster_started — rdp_only_mode")
    await asyncio.sleep(30)

    while True:
        try:
            from app.cache.redis_client import cache_get
            if await cache_get("system:posting_paused"):
                logger.info("auto_poster_paused_sleeping_60s")
                await asyncio.sleep(60)
                continue

            channels = await _get_active_channels()
            if not channels:
                await asyncio.sleep(300)
                continue

            # ── Step 1: Find channels ready to post ──────────────────────────
            ready_channels = []
            for ch in channels:
                cooldown = await get_cooldown_remaining(str(ch.id))
                if cooldown > 0:
                    logger.info(
                        "auto_poster_channel_cooldown",
                        channel=ch.display_name,
                        remaining_minutes=cooldown // 60,
                    )
                else:
                    ready_channels.append(ch)

            if not ready_channels:
                # All channels are on cooldown — check back in 10 min
                logger.info("auto_poster_all_channels_on_cooldown", count=len(channels))
                await asyncio.sleep(600)
                continue

            # ── Step 2: Scan ONCE for a live server ──────────────────────────
            # One scan serves all ready channels — no redundant scans.
            from app.services.scanner.rdp_scanner import scan_for_rdp
            try:
                rdp_result = await asyncio.wait_for(scan_for_rdp(), timeout=45.0)
            except asyncio.TimeoutError:
                logger.warning("auto_poster_rdp_scan_timeout")
                await asyncio.sleep(300)
                continue
            except Exception as scan_err:
                logger.error("auto_poster_rdp_scan_error", error=str(scan_err))
                await asyncio.sleep(300)
                continue

            if not rdp_result:
                logger.info("auto_poster_rdp_no_result_sleeping_5min")
                await asyncio.sleep(300)
                continue

            logger.info(
                "auto_poster_rdp_found",
                ip=rdp_result["ip"],
                country=rdp_result["country_name"],
                ready_channels=len(ready_channels),
            )

            # ── Step 3: Post to every ready channel ───────────────────────────
            posted = 0
            for ch in ready_channels:
                success = await _post_rdp_result_to_channel(rdp_result, ch)
                if success:
                    await mark_channel_posted(str(ch.id))
                    posted += 1
                    # Short pause between channels to avoid flood
                    await asyncio.sleep(random.randint(3, 8))

            logger.info("auto_poster_cycle_done", posted=posted, total_ready=len(ready_channels))

            # ── Step 4: Sleep before next cycle ──────────────────────────────
            # 15 min if we posted something, 10 min if all failed
            await asyncio.sleep(900 if posted > 0 else 600)

        except asyncio.CancelledError:
            logger.info("auto_poster_cancelled")
            break
        except Exception as e:
            logger.error("auto_poster_error", error=str(e))
            await asyncio.sleep(120)
