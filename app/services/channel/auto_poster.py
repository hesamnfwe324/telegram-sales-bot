"""
Auto-poster — only posts free RDP/VPS scan results.

One post type only:
  - RDP scanner finds a live free server → posts its credentials
  - Scan fails or finds nothing → skips this cycle (no fallback AI posts)

KEY DESIGN:
  Each ready channel gets its OWN unique RDP server (different IP + country).
  scan_for_rdp() pops randomly from the Redis pool so every call returns a
  distinct IP. Results are pre-fetched for all channels before posting begins,
  so a scan timeout on one channel never blocks the others.

SYNC FIX (Jul 2026):
  Some channels drift out of phase — their cooldown expires minutes before
  other channels, so they get posted in isolation and fall permanently behind.
  Solution: if any channel will be ready within SYNC_WINDOW_SECONDS, wait
  for it before scanning so all channels post together in the same batch.
"""
import asyncio
import os
import hashlib
import io
import random
import time as _time
import uuid
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
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

# If any channel's cooldown expires within this window, wait for it so all
# channels post in a single synchronised batch instead of drifting apart.
SYNC_WINDOW_SECONDS = 300    # 5 minutes — reduced from 20 min to prevent post bunching


def _cooldown_key(channel_id: str) -> str:
    return f"autoposter:cooldown:{channel_id}"


async def _get_db_auto_post_remaining(channel_id: str) -> int:
    """Read the authoritative last VPS post time from PostgreSQL.

    This deliberately does not depend on Redis, which may be fakeredis on Render."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Post.published_at, Post.channel_ids, Post.content_type, Post.image_url,
                )
                .where(
                    Post.status == "published",
                    Post.published_at.is_not(None),
                )
                .order_by(Post.published_at.desc())
                .limit(1000)
            )
            now = _time.time()
            for published_at, channel_ids, content_type, image_url in result.all():
                ids = {str(value) for value in (channel_ids or [])}
                image_marker = str(image_url or "").lower()
                is_auto_post = content_type == "rdp" or "rdp" in image_marker
                if not is_auto_post or channel_id not in ids:
                    continue
                remaining = max(0, int(COOLDOWN_SECONDS - (now - published_at.timestamp())))
                if remaining > 0:
                    return remaining
                return 0
    except Exception as exc:
        logger.warning("autoposter_db_cooldown_read_failed", channel_id=channel_id, error=str(exc)[:160])
    return 0


async def get_cooldown_remaining(channel_id: str) -> int:
    # PostgreSQL is authoritative. Redis can only add a conservative delay,
    # never make a channel eligible earlier than its database timestamp.
    db_remaining = await _get_db_auto_post_remaining(channel_id)
    if db_remaining > 0:
        return db_remaining
    try:
        from app.cache.redis_client import cache_get
        val = await cache_get(_cooldown_key(channel_id))
        if val:
            posted_at = float(val)
            return max(0, int(COOLDOWN_SECONDS - (_time.time() - posted_at)))
    except Exception as exc:
        logger.warning("autoposter_cache_cooldown_read_failed", channel_id=channel_id, error=str(exc)[:120])
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
                content_type="rdp",
                status="scheduled",
                scheduled_at=datetime.now(timezone.utc),
            )
            session.add(post)
            await session.flush()
            try:
                pub_results = await publish_post(session, post)
                published_count = sum(
                    1 for r in pub_results.values() if r.get("status") == "published"
                )
                await session.commit()

                if not published_count:
                    # publish_post returned without actually sending (manager not
                    # ready, posting paused, or all channels errored).  Do NOT call
                    # mark_channel_posted — the channel must stay ready so it is
                    # retried next cycle instead of sitting on a 3-hour cooldown
                    # with no post delivered.
                    logger.warning(
                        "rdp_post_publish_no_success_not_marking_cooldown",
                        channel=channel.display_name,
                        results=pub_results,
                    )
                    return False

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


async def reset_all_cooldowns() -> int:
    """
    Delete every autoposter:cooldown:* key from Redis.
    Call this when channels are stuck because cooldowns were set erroneously
    (e.g. by the old bug that marked channels as posted even when nothing was sent).
    Returns the number of keys deleted.
    """
    try:
        r = await get_redis()
        pattern = "autoposter:cooldown:*"
        keys = []
        async for key in r.scan_iter(pattern):
            keys.append(key)
        if keys:
            await r.delete(*keys)
        logger.info("all_cooldowns_reset", deleted=len(keys))
        return len(keys)
    except Exception as e:
        logger.error("reset_all_cooldowns_failed", error=str(e))
        return 0


async def _get_active_channels(account_id=None):
    """
    Return all active channels in randomised order.

    ORDER BY RANDOM() ensures that no channel is consistently at the end of
    the posting queue across cycles. Without this, the last channels in heap
    order always absorb flood-wait errors and drift out of phase over time.
    """
    async with AsyncSessionLocal() as session:
        q = (
            select(TelegramChannel)
            .where(TelegramChannel.is_active == True)
            .order_by(func.random())
        )
        if account_id:
            q = q.where(TelegramChannel.account_id == uuid.UUID(str(account_id)))
        result = await session.execute(q)
        return result.scalars().all()


async def _compute_cooldowns(channels) -> dict[str, int]:
    """Return {channel_id: seconds_remaining} for every channel."""
    cooldowns = {}
    for ch in channels:
        cooldowns[str(ch.id)] = await get_cooldown_remaining(str(ch.id))
    return cooldowns


async def run_auto_poster(userbot_manager):
    """
    Main auto-poster loop.

    FIX (original): scan ONCE per cycle, post to ALL ready channels so a
    scan timeout on channel N never blocks channels N+1, N+2, ...

    FIX (Jul 2026 — sync): if some channels are ready NOW and others will be
    ready within SYNC_WINDOW_SECONDS (20 min), wait for the laggards before
    scanning. This keeps all channels in a single synchronised batch and
    prevents permanent phase drift where a subset always posts alone.
    """
    # Safety stop remains active until the verified cooldown implementation is deployed.
    if os.getenv("AUTO_POSTER_ENABLED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        logger.warning("auto_poster_disabled_by_config")
        return
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

            # ── Step 1: Compute cooldowns for every channel ───────────────────
            cooldowns = await _compute_cooldowns(channels)

            ready_channels = [ch for ch in channels if cooldowns[str(ch.id)] == 0]
            waiting_channels = [
                (ch, cooldowns[str(ch.id)])
                for ch in channels
                if cooldowns[str(ch.id)] > 0
            ]

            for ch, rem in waiting_channels:
                logger.info(
                    "auto_poster_channel_cooldown",
                    channel=ch.display_name,
                    remaining_minutes=rem // 60,
                )

            # ── Step 2: Synchronisation gate ─────────────────────────────────
            # If some channels are ready but others will be ready soon, wait
            # for the stragglers so all channels post in one coherent batch.
            # This prevents permanent phase-drift (e.g. 3 channels always
            # posting 15–20 min before the other 11, and then being skipped).
            if ready_channels and waiting_channels:
                min_wait = min(rem for _, rem in waiting_channels)
                if min_wait <= SYNC_WINDOW_SECONDS:
                    logger.info(
                        "auto_poster_sync_waiting",
                        ready=len(ready_channels),
                        waiting=len(waiting_channels),
                        wait_seconds=min_wait,
                        wait_minutes=round(min_wait / 60, 1),
                    )
                    await asyncio.sleep(min_wait + 5)   # +5s safety margin
                    # Re-evaluate from the top with fresh cooldown data
                    continue

            if not ready_channels:
                # All channels are on cooldown — check back in 10 min
                logger.info("auto_poster_all_channels_on_cooldown", count=len(channels))
                await asyncio.sleep(600)
                continue

            # ── Step 3: Fetch one unique RDP result per ready channel ────────
            # Each channel gets a DIFFERENT server (different IP + country).
            # scan_for_rdp() pops randomly from the Redis pool, so every call
            # returns a distinct IP. We pre-fetch all results before posting
            # so a timeout on one channel never blocks the others.
            #
            # FALLBACK: when the pool runs dry and inline scan also fails,
            # reuse the last successfully fetched result from this cycle so
            # every ready channel still gets a post instead of being skipped.
            from app.services.scanner.rdp_scanner import scan_for_rdp

            channel_results: list[tuple] = []   # (channel, rdp_result)
            _last_good_rdp: dict | None = None   # fallback when pool is dry

            for ch in ready_channels:
                try:
                    rdp_result = await asyncio.wait_for(scan_for_rdp(), timeout=45.0)
                    if rdp_result:
                        _last_good_rdp = rdp_result
                        channel_results.append((ch, rdp_result))
                        logger.info(
                            "auto_poster_rdp_fetched",
                            channel=ch.display_name,
                            ip=rdp_result["ip"],
                            country=rdp_result["country_name"],
                        )
                    elif _last_good_rdp:
                        # Pool empty for this channel — reuse earlier result
                        channel_results.append((ch, _last_good_rdp))
                        logger.info(
                            "auto_poster_rdp_pool_dry_using_fallback",
                            channel=ch.display_name,
                            ip=_last_good_rdp["ip"],
                        )
                    else:
                        logger.info(
                            "auto_poster_rdp_no_result_skipping_channel",
                            channel=ch.display_name,
                        )
                except asyncio.TimeoutError:
                    if _last_good_rdp:
                        channel_results.append((ch, _last_good_rdp))
                        logger.info(
                            "auto_poster_rdp_timeout_using_fallback",
                            channel=ch.display_name,
                            ip=_last_good_rdp["ip"],
                        )
                    else:
                        logger.warning(
                            "auto_poster_rdp_scan_timeout_skipping_channel",
                            channel=ch.display_name,
                        )
                except Exception as scan_err:
                    logger.error(
                        "auto_poster_rdp_scan_error_skipping_channel",
                        channel=ch.display_name,
                        error=str(scan_err),
                    )

            if not channel_results:
                logger.info("auto_poster_rdp_no_results_sleeping_5min")
                await asyncio.sleep(300)
                continue

            logger.info(
                "auto_poster_rdp_fetch_done",
                fetched=len(channel_results),
                ready_channels=len(ready_channels),
            )

            # ── Step 4: Post each channel's unique server ─────────────────────
            posted = 0
            for ch, rdp_result in channel_results:
                success = await _post_rdp_result_to_channel(rdp_result, ch)
                if success:
                    await mark_channel_posted(str(ch.id))
                    posted += 1
                    # Randomised pause between channels — long enough to avoid
                    # Telegram flood limits when posting to many channels.
                    await asyncio.sleep(random.randint(8, 15))

            logger.info("auto_poster_cycle_done", posted=posted, total_ready=len(ready_channels))

            # ── Step 5: Sleep before next cycle ──────────────────────────────
            # 15 min if we posted something, 10 min if all failed
            await asyncio.sleep(900 if posted > 0 else 600)

        except asyncio.CancelledError:
            logger.info("auto_poster_cancelled")
            break
        except Exception as e:
            logger.error("auto_poster_error", error=str(e))
            await asyncio.sleep(120)
