"""
Smart auto-poster — unique content per channel, per post, always.

Two-part posting system:
  - Post 1 (media): AI-generated unique image + text as caption in ONE message
  - Post 2 (text):  text only — no media
  - Alternates per channel automatically

Image generation (Pollinations.ai / Flux — free, no API key):
  - 3 different URLs generated per post (different seeds + prompt styles)
  - publisher.py tries them in order — first success wins
  - Zero repetition guaranteed by unique seeds
"""
import asyncio
import hashlib
import random
import uuid
import urllib.parse
from collections import deque
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, desc
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.content.generator import generate_post
from app.services.content.templates import get_all_content_types
from app.services.channel.publisher import publish_post, _URL_SEPARATOR
from app.core.logging import get_logger

logger = get_logger(__name__)

TEHRAN = ZoneInfo("Asia/Tehran")

PEAK_WINDOWS = [
    (8,  10, 1),
    (12, 14, 1),
    (20, 23, 2),
]

MIN_INTERVAL_SECONDS = 2 * 3600

TOPICS_POOL = [
    "Free VPS trial for beginners",
    "Ubuntu Linux server setup guide",
    "Free Windows RDP access",
    "How to set up a VPS in 5 minutes",
    "Choosing the right OS for your VPS",
    "First things to do after buying a VPS",
    "How to connect to VPS via SSH",
    "VPS vs shared hosting — full comparison",
    "Server performance optimization tricks",
    "Boost your VPS speed: top 5 tweaks",
    "How to double your server RAM efficiency",
    "Swap memory optimization on Linux",
    "CPU pinning tricks for better VPS performance",
    "Reduce server latency in 10 minutes",
    "Installing Docker on a VPS",
    "Running Docker Compose on a cheap VPS",
    "Deploy a web app with Docker in 3 steps",
    "Kubernetes vs Docker Swarm for small teams",
    "CI/CD pipeline on a budget VPS",
    "GitHub Actions + VPS auto-deploy setup",
    "VPS security hardening checklist",
    "Firewall configuration best practices",
    "Stop brute-force attacks on your VPS",
    "How to set up fail2ban in 5 minutes",
    "SSH key authentication — why and how",
    "Free SSL certificate setup on VPS",
    "DDoS protection on a budget VPS",
    "Nginx vs Apache: which should you use?",
    "Best data centers for low-latency hosting",
    "Cloudflare + VPS: the perfect combo",
    "Setting up a reverse proxy with Nginx",
    "IPv6 setup on Linux VPS",
    "Custom domain + VPS in under 15 minutes",
    "Load balancing across two cheap VPS nodes",
    "How to cut your server costs in half",
    "Best budget VPS plans in 2025",
    "NVMe vs SSD VPS — is it worth paying more?",
    "When to upgrade from VPS to dedicated server",
    "Hidden costs of cloud hosting nobody tells you",
    "Backup strategy for your VPS",
    "Automated daily backups on Linux",
    "rsync backup to remote server — full guide",
    "SSD vs NVMe VPS: what's the difference?",
    "Monitoring your VPS uptime for free",
    "Set up server alerts in Telegram",
    "Top 5 free server monitoring tools",
    "How to auto-restart a crashed service",
    "SSH productivity tips every sysadmin needs",
    "Running a Telegram bot on a VPS",
    "VPS for private proxy setup",
    "Crypto node hosting on VPS",
    "Hosting a game server on a VPS",
    "Running a personal VPN on VPS",
    "Self-hosted email server on VPS",
    "WordPress on VPS vs managed hosting",
    "Deploy a Discord bot 24/7 on VPS",
    "Host your own Nextcloud on VPS",
    "Database server hosting — tips and tricks",
    "Running Python scripts 24/7 on a VPS",
    "cPanel vs Hestia: lightweight control panels",
    "Headless Chrome on VPS for scraping",
    "VPS for Forex trading bots",
]

CONTENT_TYPE_WEIGHTS = {
    "viral_giveaway":        15,
    "viral_free_resource":   15,
    "viral_tip_secret":      15,
    "viral_poll_engagement": 12,
    "viral_news_hook":       10,
    "educational":           12,
    "technical":             10,
    "marketing":              8,
    "comparison":             8,
    "promotion":              5,
    "announcement":           5,
}

STYLE_MODIFIERS = [
    "Use a confident, bold tone. Short punchy sentences.",
    "Use a storytelling angle — open with a mini real-world scenario.",
    "Use a myth vs reality frame — bust a common misconception.",
    "Use a numbered list format — 5 reasons why or 3 things that.",
    "Use a conversational friendly tone, like talking to a colleague.",
    "Use urgency and scarcity signals throughout.",
    "Use a beginner-friendly angle — assume zero technical knowledge.",
    "Use a pro/expert angle — talk directly to experienced sysadmins.",
    "Use a cost-saving / ROI angle — focus on money saved or earned.",
    "Use a security-first angle — emphasize risks and how to avoid them.",
    "Use an aspirational tone — paint a picture of what success looks like.",
    "Use a problem-first structure — lead with the pain, then the solution.",
    "Use a quick wins frame — what can someone do in the next 10 minutes?",
    "Use a case study frame — write as if describing a real customer success.",
    "Use a warning framing — something people are doing wrong.",
    "Use a minimalist style — fewer words, more impact per sentence.",
]

_TOPIC_IMAGE_PROMPTS = {
    "docker": "Docker containers visualization, microservices architecture, interconnected nodes, technology",
    "kubernetes": "Kubernetes orchestration diagram, pod clusters, cloud-native technology, abstract",
    "ssh": "secure shell terminal, green text on black screen, encryption visualization, cybersecurity",
    "security": "cybersecurity shield, digital lock, firewall protection, network security visualization",
    "firewall": "network firewall packet filtering, secure gateway, digital protection concept",
    "ssl": "SSL certificate HTTPS padlock, secure connection, encryption data flow, green lock",
    "nginx": "Nginx web server reverse proxy, load balancing, high-traffic architecture diagram",
    "vpn": "VPN tunnel visualization, encrypted connection, privacy shield, global network map",
    "backup": "data backup system, cloud storage disaster recovery, digital archive, safe storage",
    "monitoring": "server monitoring dashboard, real-time metrics, uptime graphs, alert notification",
    "linux": "Linux terminal command line, Tux penguin logo, code on dark screen, open source",
    "ubuntu": "Ubuntu Linux server terminal, orange purple branding, open source datacenter",
    "windows": "Windows Server interface, datacenter racks, cloud infrastructure, blue theme",
    "rdp": "Remote Desktop connection, Windows remote access, screen sharing technology",
    "cloud": "cloud computing infrastructure, floating servers, scalable architecture, sky data",
    "vps": "Virtual Private Server visualization, virtualization layers, isolated containers, rack",
    "database": "database server SQL tables, structured data storage, PostgreSQL visualization",
    "python": "Python programming snake logo, automation scripts, code on dark background",
    "telegram": "Telegram bot automation, messaging API, blue chat interface, code integration",
    "crypto": "cryptocurrency node server, blockchain network, mining rig, digital ledger nodes",
    "game": "game server infrastructure, low-latency network, gaming datacenter, performance",
    "wordpress": "WordPress hosting CMS dashboard, PHP server, web publishing platform",
    "network": "global network infrastructure, fiber optic cables, internet exchange point",
    "latency": "low latency network, speed visualization, fiber optic data transfer, fast",
    "free": "free VPS server gift concept, promotional offer, cloud hosting open access",
    "speed": "server performance speed, NVMe SSD, ultra-fast data processing visualization",
    "cost": "cost savings hosting, budget optimization, money and technology, ROI concept",
    "default": "premium VPS cloud server infrastructure, professional datacenter, advanced technology",
}

_FALLBACK_STYLES = [
    "ultra-realistic 8K professional photography, cinematic lighting, dark tech aesthetic",
    "futuristic 3D render, glowing neon circuits, hyper-detailed, dark background, dramatic",
    "clean corporate illustration, vibrant gradient colors, modern professional design",
]


def _get_base_prompt(topic: str) -> str:
    topic_lower = topic.lower()
    for keyword, prompt in _TOPIC_IMAGE_PROMPTS.items():
        if keyword in topic_lower:
            return prompt
    return _TOPIC_IMAGE_PROMPTS["default"]


def _build_pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1280&height=720&model=flux&seed={seed}&nologo=true&enhance=true"
    )


def _generate_image_urls(topic: str, base_seed: int) -> str:
    """
    Generate 3 AI image URLs with different seeds and visual styles.
    Packed into one string separated by _URL_SEPARATOR.
    Publisher tries them in order — first successful download wins.
    """
    base_prompt = _get_base_prompt(topic)
    urls = []
    for i, style in enumerate(_FALLBACK_STYLES):
        seed = base_seed + (i * 7919)
        full_prompt = f"{base_prompt}, {style}"
        urls.append(_build_pollinations_url(full_prompt, seed))
    return _URL_SEPARATOR.join(urls)


_channel_post_mode: dict[str, str] = {}


def _get_post_mode(channel_id: str) -> str:
    return _channel_post_mode.get(channel_id, "media")


def _toggle_post_mode(channel_id: str) -> None:
    current = _channel_post_mode.get(channel_id, "media")
    _channel_post_mode[channel_id] = "text" if current == "media" else "media"


_recent_hashes: deque = deque(maxlen=300)
_last_post_time: dict[str, float] = {}


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode()).hexdigest()[:16]


def _is_duplicate(content: str) -> bool:
    return _content_hash(content) in _recent_hashes


def _record_hash(content: str) -> None:
    _recent_hashes.append(_content_hash(content))


def _now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def _pick_content_type() -> str:
    types = list(CONTENT_TYPE_WEIGHTS.keys())
    weights = [CONTENT_TYPE_WEIGHTS[t] for t in types]
    return random.choices(types, weights=weights, k=1)[0]


async def _is_combo_used(topic: str, content_type: str) -> bool:
    from app.cache.redis_client import cache_get
    return bool(await cache_get(_combo_key(topic, content_type)))


async def _mark_combo_used(topic: str, content_type: str) -> None:
    from app.cache.redis_client import cache_set
    await cache_set(_combo_key(topic, content_type), "1", ttl=7 * 24 * 3600)


def _combo_key(topic: str, content_type: str) -> str:
    slug = hashlib.md5(f"{topic}:{content_type}".encode()).hexdigest()[:12]
    return f"post_combo:{slug}"


async def _pick_fresh_combo() -> tuple[str, str]:
    all_types = list(CONTENT_TYPE_WEIGHTS.keys())
    candidates = [(t, ct) for t in TOPICS_POOL for ct in all_types]
    random.shuffle(candidates)
    for topic, content_type in candidates:
        if not await _is_combo_used(topic, content_type):
            return topic, content_type
    logger.warning("all_post_combos_used_picking_random")
    return random.choice(TOPICS_POOL), _pick_content_type()


async def _get_recent_post_angles(limit: int = 25) -> list[str]:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Post.content)
                .where(Post.status == "published")
                .order_by(desc(Post.published_at))
                .limit(limit)
            )
            rows = result.scalars().all()
            angles = []
            for content in rows:
                if content:
                    first_line = content.strip().split("\n")[0][:120]
                    if first_line:
                        angles.append(first_line)
            return angles
    except Exception as e:
        logger.warning("get_recent_post_angles_failed", error=str(e))
        return []


async def _post_to_channel(userbot_manager, channel: TelegramChannel) -> bool:
    lang = channel.language or "en"
    if lang == "fa":
        lang = "en"

    channel_id_str = str(channel.id)
    post_mode = _get_post_mode(channel_id_str)

      # ── RDP Scanner post (replaces text-only post) ─────────────────────────
      if post_mode == "text":
          try:
              from app.services.scanner.rdp_scanner import scan_for_rdp
              from app.services.content.rdp_post_builder import build_rdp_post
              rdp_result = await scan_for_rdp()
              if rdp_result:
                  unique_seed = random.randint(100_000, 99_999_999)
                  rdp_content, rdp_image_url = build_rdp_post(
                      ip=rdp_result["ip"],
                      port=rdp_result["port"],
                      username=rdp_result["username"],
                      password=rdp_result["password"],
                      country_name=rdp_result["country_name"],
                      country_flag=rdp_result["country_flag"],
                      seed=unique_seed,
                  )
                  async with AsyncSessionLocal() as session:
                      rdp_post = Post(
                          account_id=channel.account_id,
                          channel_ids=[str(channel.id)],
                          content=rdp_content,
                          languages={lang: rdp_content},
                          image_url=rdp_image_url,
                          status="scheduled",
                          scheduled_at=datetime.now(timezone.utc),
                      )
                      session.add(rdp_post)
                      await session.flush()
                      try:
                          await publish_post(session, rdp_post)
                          await session.commit()
                          _record_hash(rdp_content)
                          _toggle_post_mode(channel_id_str)
                          logger.info("rdp_post_sent",
                                      channel=channel.display_name,
                                      country=rdp_result["country_name"],
                                      ip=rdp_result["ip"])
                          return True
                      except Exception as e:
                          rdp_post.status = "failed"
                          await session.commit()
                          logger.error("rdp_post_send_failed",
                                       channel=channel.display_name, error=str(e))
          except Exception as e:
              logger.warning("rdp_scan_fallback_to_regular",
                             channel=channel.display_name, error=str(e))
      # ── End RDP scanner block ──────────────────────────────────────────────

      topic, content_type = await _pick_fresh_combo()
    forbidden_angles = await _get_recent_post_angles(limit=25)
    style_hint = random.choice(STYLE_MODIFIERS)
    unique_seed = random.randint(100_000, 99_999_999)

    for attempt in range(4):
        if attempt > 0:
            topic, content_type = await _pick_fresh_combo()
            style_hint = random.choice(STYLE_MODIFIERS)
            unique_seed = random.randint(100_000, 99_999_999)

        try:
            logger.info("auto_post_generating", channel=channel.display_name,
                        type=content_type, topic=topic, mode=post_mode, attempt=attempt + 1)
            content = await generate_post(
                content_type, topic, lang,
                include_hashtags=True,
                style_hint=style_hint,
                forbidden_angles=forbidden_angles,
                unique_seed=unique_seed,
            )
        except Exception as e:
            logger.error("auto_post_generate_failed", channel=channel.display_name, error=str(e))
            return False

        if not _is_duplicate(content):
            break

        logger.warning("auto_post_duplicate_detected", channel=channel.display_name, attempt=attempt + 1)
        if attempt == 3:
            logger.error("auto_post_all_duplicates_skipping", channel=channel.display_name)
            return False

    image_url: str | None = None
    if post_mode == "media":
        image_url = _generate_image_urls(topic, unique_seed)
        logger.info("image_urls_generated", topic=topic, base_seed=unique_seed)

    async with AsyncSessionLocal() as session:
        post = Post(
            account_id=channel.account_id,
            channel_ids=[str(channel.id)],
            content=content,
            languages={lang: content},
            image_url=image_url,
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(post)
        await session.flush()

        try:
            await publish_post(session, post)
            await session.commit()
            _record_hash(content)
            await _mark_combo_used(topic, content_type)
            _toggle_post_mode(channel_id_str)
            logger.info("auto_post_sent", channel=channel.display_name,
                        type=content_type, topic=topic, mode=post_mode,
                        has_media=image_url is not None)
            return True
        except Exception as e:
            post.status = "failed"
            await session.commit()
            logger.error("auto_post_send_failed", channel=channel.display_name, error=str(e))
            return False


async def _get_active_channels(account_id=None):
    async with AsyncSessionLocal() as session:
        q = select(TelegramChannel).where(TelegramChannel.is_active == True)
        if account_id:
            q = q.where(TelegramChannel.account_id == uuid.UUID(str(account_id)))
        result = await session.execute(q)
        return result.scalars().all()


async def run_auto_poster(userbot_manager):
    logger.info("auto_poster_started")
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

            now_ts = asyncio.get_running_loop().time()
            posted = 0

            for channel in channels:
                ch_key = str(channel.id)
                last = _last_post_time.get(ch_key, 0)

                if now_ts - last < MIN_INTERVAL_SECONDS:
                    remaining = int((MIN_INTERVAL_SECONDS - (now_ts - last)) / 60)
                    logger.info("auto_poster_channel_cooldown",
                                channel=channel.display_name, remaining_minutes=remaining)
                    continue

                success = await _post_to_channel(userbot_manager, channel)
                if success:
                    _last_post_time[ch_key] = asyncio.get_running_loop().time()
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
