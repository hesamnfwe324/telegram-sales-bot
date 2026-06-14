"""
Smart auto-poster — knows Iran peak hours, generates viral AI content,
and posts to admin channels with duplicate-prevention.
"""
import asyncio
import hashlib
import random
import uuid
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.content.generator import generate_post
from app.services.content.templates import get_viral_content_types
from app.services.channel.publisher import publish_post
from app.core.logging import get_logger

logger = get_logger(__name__)

TEHRAN = ZoneInfo("Asia/Tehran")

# Peak hours (Tehran time): (start, end, weight)
PEAK_WINDOWS = [
    (8,  10, 1),   # morning
    (12, 14, 1),   # noon
    (20, 23, 2),   # evening — highest activity
]

# Minimum interval between two posts to the same channel (4 hours)
MIN_INTERVAL_SECONDS = 4 * 3600

# Topics in English only
TOPICS_POOL = [
    "Free VPS trial for beginners",
    "Ubuntu Linux server setup guide",
    "Free Windows RDP access",
    "Server performance optimization tricks",
    "Installing Docker on a VPS",
    "How to cut your server costs in half",
    "VPS security hardening checklist",
    "Boost your VPS speed: top 5 tweaks",
    "Nginx vs Apache: which should you use?",
    "Best data centers for low-latency hosting",
    "SSH productivity tips every sysadmin needs",
    "Firewall configuration best practices",
    "Running a Telegram bot on a VPS",
    "VPS for private proxy setup",
    "Crypto node hosting on VPS",
    "SSD vs NVMe VPS: what's the difference?",
    "Cloudflare + VPS: the perfect combo",
    "Backup strategy for your VPS",
    "IPv6 setup on Linux VPS",
    "Monitoring your VPS uptime for free",
]

# Duplicate prevention: keep hashes of the last 200 generated posts in memory
_recent_hashes: deque = deque(maxlen=200)
# Per-channel last post timestamp
_last_post_time: dict[str, float] = {}


def _content_hash(text: str) -> str:
    """Short hash of post content for dedup detection."""
    return hashlib.sha1(text.strip().lower().encode()).hexdigest()[:16]


def _is_duplicate(content: str) -> bool:
    """Return True if this content (or near-identical) was recently posted."""
    h = _content_hash(content)
    return h in _recent_hashes


def _record_hash(content: str) -> None:
    _recent_hashes.append(_content_hash(content))


def _now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def _is_peak_hour() -> bool:
    h = _now_tehran().hour
    for start, end, _ in PEAK_WINDOWS:
        if start <= h < end:
            return True
    return False


def _seconds_to_next_peak() -> int:
    now = _now_tehran()
    h = now.hour
    m = now.minute

    for start, end, _ in PEAK_WINDOWS:
        if h < start:
            diff_minutes = (start - h) * 60 - m
            return diff_minutes * 60

    # Past the last window → first window tomorrow
    first_start = PEAK_WINDOWS[0][0]
    diff_minutes = (24 - h + first_start) * 60 - m
    return diff_minutes * 60


def _pick_content_type() -> str:
    weights = {
        "viral_giveaway":        25,
        "viral_free_resource":   25,
        "viral_tip_secret":      20,
        "viral_poll_engagement": 20,
        "viral_news_hook":       10,
    }
    types = list(weights.keys())
    probs = [weights[t] for t in types]
    return random.choices(types, weights=probs, k=1)[0]


async def _get_active_channels(account_id=None):
    async with AsyncSessionLocal() as session:
        q = select(TelegramChannel).where(TelegramChannel.is_active == True)
        if account_id:
            q = q.where(TelegramChannel.account_id == uuid.UUID(str(account_id)))
        result = await session.execute(q)
        return result.scalars().all()


async def _post_to_channel(userbot_manager, channel: TelegramChannel) -> bool:
    """Generate an AI post and send it, with duplicate prevention and retries."""
    # Force English; respect channel override only if explicitly set to a non-Persian lang
    lang = channel.language or "en"
    if lang == "fa":
        lang = "en"

    content_type = _pick_content_type()

    # Try up to 3 times to get a non-duplicate
    for attempt in range(3):
        topic = random.choice(TOPICS_POOL)
        try:
            logger.info("auto_post_generating",
                        channel=channel.display_name,
                        type=content_type,
                        topic=topic,
                        attempt=attempt + 1)
            content = await generate_post(content_type, topic, lang, include_hashtags=True)
        except Exception as e:
            logger.error("auto_post_generate_failed",
                         channel=channel.display_name, error=str(e))
            return False

        if not _is_duplicate(content):
            break
        logger.warning("auto_post_duplicate_detected",
                       channel=channel.display_name, attempt=attempt + 1)
        if attempt == 2:
            logger.error("auto_post_all_duplicates_skipping",
                         channel=channel.display_name)
            return False

    # Save post and send
    async with AsyncSessionLocal() as session:
        post = Post(
            account_id=channel.account_id,
            channel_ids=[str(channel.id)],
            content=content,
            languages={lang: content},
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(post)
        await session.flush()

        try:
            await publish_post(session, post)
            await session.commit()
            _record_hash(content)
            logger.info("auto_post_sent",
                        channel=channel.display_name, type=content_type)
            return True
        except Exception as e:
            post.status = "failed"
            await session.commit()
            logger.error("auto_post_send_failed",
                         channel=channel.display_name, error=str(e))
            return False


async def run_auto_poster(userbot_manager):
    """
    Main scheduler loop — runs forever.
    Posts during Tehran peak hours, enforces per-channel cooldowns.
    """
    logger.info("auto_poster_started")

    # Wait 30s for all services to come up
    await asyncio.sleep(30)

    while True:
        try:
            from app.cache.redis_client import cache_get
            if await cache_get("system:posting_paused"):
                logger.info("auto_poster_paused_sleeping_60s")
                await asyncio.sleep(60)
                continue

            if not _is_peak_hour():
                wait = _seconds_to_next_peak()
                wait += random.randint(0, 600)
                logger.info("auto_poster_waiting_for_peak",
                            minutes=round(wait / 60))
                await asyncio.sleep(wait)
                continue

            channels = await _get_active_channels()
            if not channels:
                logger.info("auto_poster_no_active_channels")
                await asyncio.sleep(300)
                continue

            now_ts = asyncio.get_running_loop().time()
            posted = 0

            for channel in channels:
                ch_key = str(channel.id)
                last = _last_post_time.get(ch_key, 0)

                if now_ts - last < MIN_INTERVAL_SECONDS:
                    remaining = int((MIN_INTERVAL_SECONDS - (now_ts - last)) / 60)
                    logger.info("auto_poster_channel_cooldown",
                                channel=channel.display_name,
                                remaining_minutes=remaining)
                    continue

                success = await _post_to_channel(userbot_manager, channel)
                if success:
                    _last_post_time[ch_key] = asyncio.get_running_loop().time()
                    posted += 1
                    # Anti-spam jitter between channels
                    await asyncio.sleep(random.randint(15, 45))

            if posted == 0:
                await asyncio.sleep(900)
            else:
                logger.info("auto_poster_cycle_done", posted=posted)
                await asyncio.sleep(1800)

        except asyncio.CancelledError:
            logger.info("auto_poster_cancelled")
            break
        except Exception as e:
            logger.error("auto_poster_error", error=str(e))
            await asyncio.sleep(120)
