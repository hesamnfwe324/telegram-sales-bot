"""
Auto-poster — only posts free RDP/VPS scan results.

One post type only:
  - RDP scanner finds a live free server → posts its credentials
  - Scan fails or finds nothing → skips this cycle (no fallback AI posts)
"""
import asyncio
import hashlib
import random
import time as _time
import uuid
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, desc
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.channel.publisher import publish_post
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


async def mark_channel_posted(channel_id: str) -> None:
    from app.cache.redis_client import cache_set
    await cache_set(_cooldown_key(channel_id), str(_time.time()), ttl=COOLDOWN_SECONDS + 300)
    _last_post_time[channel_id] = asyncio.get_running_loop().time()


_recent_hashes: deque = deque(maxlen=300)
_last_post_time: dict[str, float] = {}


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode()).hexdigest()[:16]


def _is_duplicate(content: str) -> bool:
    return _content_hash(content) in _recent_hashes


def _record_hash(content: str) -> None:
    _recent_hashes.append(_content_hash(content))


async def _post_to_channel(userbot_manager, channel: TelegramChannel) -> bool:
    """Post ONLY if a live free RDP/VPS server is found by the scanner.
    Returns True on success, False if scan found nothing or posting failed.
    No AI-generated fallback — either a real server is posted or nothing is.
    """
    lang = channel.language or "en"
    if lang == "fa":
        lang = "en"

    try:
        from app.services.scanner.rdp_scanner import scan_for_rdp
        from app.services.content.rdp_post_builder import build_rdp_post

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
            channel_ids=[str(channel.id)],
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


async def _get_active_channels(account_id=None):
    async with AsyncSessionLocal() as session:
        q = select(TelegramChannel).where(TelegramChannel.is_active == True)
        if account_id:
            q = q.where(TelegramChannel.account_id == uuid.UUID(str(account_id)))
        result = await session.execute(q)
        return result.scalars().all()


async def run_auto_poster(userbot_manager):
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

            posted = 0

            for channel in channels:
                ch_key = str(channel.id)
                cooldown = await get_cooldown_remaining(ch_key)
                if cooldown > 0:
                    logger.info("auto_poster_channel_cooldown",
                                channel=channel.display_name,
                                remaining_minutes=cooldown // 60)
                    continue

                success = await _post_to_channel(userbot_manager, channel)
                if success:
                    await mark_channel_posted(ch_key)
                    posted += 1
                    await asyncio.sleep(random.randint(10, 30))

            await asyncio.sleep(900 if posted > 0 else 600)
            if posted > 0:
                logger.info("auto_poster_cycle_done", posted=posted)

        except asyncio.CancelledError:
            logger.info("auto_poster_cancelled")
            break
        except Exception as e:
            logger.error("auto_poster_error", error=str(e))
            await asyncio.sleep(120)
