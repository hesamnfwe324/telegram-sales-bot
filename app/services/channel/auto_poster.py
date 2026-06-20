"""
  Smart auto-poster — unique content per channel, per post, always.

  Two-part posting system:
    - Post 1 (media): image or video + text as caption in ONE message
    - Post 2 (text):  text only — no media
    - Alternates per channel automatically

  Uniqueness guarantees:
    1. Redis tracks every topic+type combo used globally (7-day TTL)
    2. DB query pulls last 25 post first-lines and injects them as
       "forbidden angles" into every AI prompt
    3. Each prompt gets a random style modifier + unique seed
    4. In-memory hash dedup catches any accidental near-duplicates
  """
  import asyncio
  import hashlib
  import random
  import uuid
  from collections import deque
  from datetime import datetime, timezone
  from zoneinfo import ZoneInfo

  from sqlalchemy import select, desc
  from app.db.session import AsyncSessionLocal
  from app.models.channel import TelegramChannel
  from app.models.post import Post
  from app.services.content.generator import generate_post
  from app.services.content.templates import get_all_content_types
  from app.services.channel.publisher import publish_post
  from app.core.logging import get_logger

  logger = get_logger(__name__)

  TEHRAN = ZoneInfo("Asia/Tehran")

  PEAK_WINDOWS = [
      (8,  10, 1),
      (12, 14, 1),
      (20, 23, 2),
  ]

  MIN_INTERVAL_SECONDS = 2 * 3600  # exactly 2 hours between posts per channel

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
      "CI/CD pipeline on a $5 VPS",
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
      "Use a 'myth vs reality' frame — bust a common misconception.",
      "Use a 'most people don't know this' hook to drive curiosity.",
      "Use a numbered list format — '5 reasons why...' or '3 things that...'",
      "Use a conversational friendly tone, like talking to a colleague.",
      "Use urgency and scarcity signals throughout.",
      "Use a beginner-friendly angle — assume zero technical knowledge.",
      "Use a pro/expert angle — talk directly to experienced sysadmins.",
      "Use a cost-saving / ROI angle — focus on money saved or earned.",
      "Use a security-first angle — emphasize risks and how to avoid them.",
      "Use a comparison/versus angle even if not explicitly a comparison post.",
      "Use an aspirational tone — paint a picture of what success looks like.",
      "Use a problem-first structure — lead with the pain, then the solution.",
      "Use a controversial or contrarian opinion to spark discussion.",
      "Use a 'quick wins' frame — what can someone do in the next 10 minutes?",
      "Use a 'case study' frame — write as if describing a real customer success.",
      "Use a 'behind the scenes' angle — insider knowledge others don't share.",
      "Use a 'warning' or 'danger' framing — something people are doing wrong.",
      "Use a minimalist style — fewer words, more impact per sentence.",
  ]

  # ── Professional tech/server image pool (Pexels — permanent direct URLs) ──────
  # Categorized by topic keyword for smarter selection
  _TECH_IMAGES_BY_CATEGORY = {
      "server": [
          "https://images.pexels.com/photos/1148820/pexels-photo-1148820.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1714208/pexels-photo-1714208.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/60504/security-protection-anti-virus-software-60504.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/3861972/pexels-photo-3861972.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
      "security": [
          "https://images.pexels.com/photos/60504/security-protection-anti-virus-software-60504.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/5380642/pexels-photo-5380642.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/60504/security-protection-anti-virus-software-60504.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/2882552/pexels-photo-2882552.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
      "code": [
          "https://images.pexels.com/photos/1181354/pexels-photo-1181354.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1181467/pexels-photo-1181467.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/4164418/pexels-photo-4164418.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1181244/pexels-photo-1181244.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
      "network": [
          "https://images.pexels.com/photos/374793/pexels-photo-374793.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/270360/pexels-photo-270360.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1089438/pexels-photo-1089438.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/573573/pexels-photo-573573.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
      "cloud": [
          "https://images.pexels.com/photos/4974914/pexels-photo-4974914.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/6804085/pexels-photo-6804085.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/2881232/pexels-photo-2881232.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1629016/pexels-photo-1629016.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
      "general": [
          "https://images.pexels.com/photos/1148820/pexels-photo-1148820.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/325229/pexels-photo-325229.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1181354/pexels-photo-1181354.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/270360/pexels-photo-270360.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/4974914/pexels-photo-4974914.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/1714208/pexels-photo-1714208.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
          "https://images.pexels.com/photos/3861972/pexels-photo-3861972.jpeg?auto=compress&cs=tinysrgb&w=1280&h=720&fit=crop",
      ],
  }

  _TOPIC_IMAGE_KEYWORDS = {
      "security": "security", "firewall": "security", "ssh": "security",
      "fail2ban": "security", "ssl": "security", "ddos": "security",
      "docker": "code", "python": "code", "github": "code", "ci/cd": "code",
      "deploy": "code", "bash": "code", "script": "code",
      "network": "network", "nginx": "network", "proxy": "network",
      "cloudflare": "network", "dns": "network", "ipv6": "network",
      "cloud": "cloud", "aws": "cloud", "vps": "server",
      "server": "server", "datacenter": "server", "rdp": "server",
      "windows": "server", "ubuntu": "server", "linux": "server",
      "backup": "server", "monitoring": "server",
  }


  def _get_topic_image_url(topic: str) -> str:
      """Select a professional image URL based on the post topic."""
      topic_lower = topic.lower()
      category = "general"
      for keyword, cat in _TOPIC_IMAGE_KEYWORDS.items():
          if keyword in topic_lower:
              category = cat
              break
      pool = _TECH_IMAGES_BY_CATEGORY.get(category, _TECH_IMAGES_BY_CATEGORY["general"])
      return random.choice(pool)


  # ── Per-channel two-part posting mode ──────────────────────────────────────
  # "media" = next post is image/video + text caption
  # "text"  = next post is text only
  _channel_post_mode: dict[str, str] = {}


  def _get_post_mode(channel_id: str) -> str:
      """Return the current post mode for a channel. Defaults to 'media' on first post."""
      return _channel_post_mode.get(channel_id, "media")


  def _toggle_post_mode(channel_id: str) -> None:
      """Alternate between media and text modes after each successful post."""
      current = _channel_post_mode.get(channel_id, "media")
      _channel_post_mode[channel_id] = "text" if current == "media" else "media"


  # In-memory hash dedup (last 300 posts)
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


  def _is_peak_hour() -> bool:
      h = _now_tehran().hour
      return any(start <= h < end for start, end, _ in PEAK_WINDOWS)


  def _seconds_to_next_peak() -> int:
      now = _now_tehran()
      h, m = now.hour, now.minute
      for start, end, _ in PEAK_WINDOWS:
          if h < start:
              return (start - h) * 3600 - m * 60
      first_start = PEAK_WINDOWS[0][0]
      return (24 - h + first_start) * 3600 - m * 60


  def _pick_content_type() -> str:
      types = list(CONTENT_TYPE_WEIGHTS.keys())
      weights = [CONTENT_TYPE_WEIGHTS[t] for t in types]
      return random.choices(types, weights=weights, k=1)[0]


  # ── Redis-backed uniqueness tracking ───────────────────────────────────────

  async def _is_combo_used(topic: str, content_type: str) -> bool:
      from app.cache.redis_client import cache_get
      key = _combo_key(topic, content_type)
      return bool(await cache_get(key))


  async def _mark_combo_used(topic: str, content_type: str) -> None:
      from app.cache.redis_client import cache_set
      key = _combo_key(topic, content_type)
      await cache_set(key, "1", ttl=7 * 24 * 3600)


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


  # ── DB-backed forbidden angles ──────────────────────────────────────────────

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


  # ── Main channel post function ──────────────────────────────────────────────

  async def _post_to_channel(userbot_manager, channel: TelegramChannel) -> bool:
      lang = channel.language or "en"
      if lang == "fa":
          lang = "en"

      # Determine post mode: media (image+caption) or text-only
      channel_id_str = str(channel.id)
      post_mode = _get_post_mode(channel_id_str)

      # Pick a topic+type combo not used in 7 days
      topic, content_type = await _pick_fresh_combo()

      # Get recent post first-lines to inject as "forbidden angles"
      forbidden_angles = await _get_recent_post_angles(limit=25)

      style_hint = random.choice(STYLE_MODIFIERS)
      unique_seed = random.randint(100000, 999999)

      # Try up to 4 times — each retry picks a completely different combo
      for attempt in range(4):
          if attempt > 0:
              topic, content_type = await _pick_fresh_combo()
              style_hint = random.choice(STYLE_MODIFIERS)
              unique_seed = random.randint(100000, 999999)

          try:
              logger.info(
                  "auto_post_generating",
                  channel=channel.display_name,
                  type=content_type,
                  topic=topic,
                  mode=post_mode,
                  attempt=attempt + 1,
              )
              content = await generate_post(
                  content_type, topic, lang,
                  include_hashtags=True,
                  style_hint=style_hint,
                  forbidden_angles=forbidden_angles,
                  unique_seed=unique_seed,
              )
          except Exception as e:
              logger.error("auto_post_generate_failed",
                           channel=channel.display_name, error=str(e))
              return False

          if not _is_duplicate(content):
              break

          logger.warning("auto_post_duplicate_detected",
                         channel=channel.display_name, attempt=attempt + 1)
          if attempt == 3:
              logger.error("auto_post_all_duplicates_skipping",
                           channel=channel.display_name)
              return False

      # Select image URL for media posts
      image_url: str | None = None
      if post_mode == "media":
          image_url = _get_topic_image_url(topic)

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
              # Toggle mode: next post for this channel will alternate
              _toggle_post_mode(channel_id_str)
              logger.info(
                  "auto_post_sent",
                  channel=channel.display_name,
                  type=content_type,
                  topic=topic,
                  mode=post_mode,
                  has_media=image_url is not None,
              )
              return True
          except Exception as e:
              post.status = "failed"
              await session.commit()
              logger.error("auto_post_send_failed",
                           channel=channel.display_name, error=str(e))
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
                                  channel=channel.display_name,
                                  remaining_minutes=remaining)
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
  