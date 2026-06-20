from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.models.channel import TelegramChannel
  from app.models.post import Post
  from app.services.monitoring.metrics_collector import increment_daily_stat
  from app.core.logging import get_logger
  from datetime import datetime, timezone
  import asyncio
  import uuid
  import hashlib

  logger = get_logger(__name__)

  _userbot_manager = None

  # Telegram caption limit for media posts (images/videos): 1024 chars
  # Telegram message limit for text-only posts: 4096 chars
  MAX_CAPTION_LENGTH = 1020
  MAX_TEXT_LENGTH = 4090

  # Pool of professional emojis — one is assigned permanently per channel
  _CHANNEL_EMOJIS = [
      "🌐", "🚀", "💡", "⚡", "🔥", "🛡️", "💎", "🎯",
      "🔮", "🌟", "💫", "🏆", "⚙️", "🖥️", "🔐", "📡",
      "🧠", "🌊", "🎪", "🦅", "🦁", "🐉", "🌙", "☄️",
      "🏔️", "🔱", "⚜️", "🌈", "🎖️", "🛰️",
  ]

  # Video file extensions — used to detect if media_url is a video
  _VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}


  def set_userbot_manager(manager) -> None:
      global _userbot_manager
      _userbot_manager = manager


  def _is_video_url(url: str) -> bool:
      """Detect if the media URL is a video based on its extension."""
      lower = url.lower().split("?")[0]
      return any(lower.endswith(ext) for ext in _VIDEO_EXTENSIONS)


  def _truncate_caption(text: str, limit: int = MAX_CAPTION_LENGTH) -> str:
      if len(text) <= limit:
          return text
      # Truncate at last complete word/line before limit
      truncated = text[:limit - 3]
      last_newline = truncated.rfind("\n")
      if last_newline > limit // 2:
          truncated = truncated[:last_newline]
      return truncated + "…"


  def _assign_channel_emoji(channel_id: str) -> str:
      """Deterministically assign a unique emoji to a channel based on its ID."""
      hash_int = int(hashlib.md5(str(channel_id).encode()).hexdigest(), 16)
      return _CHANNEL_EMOJIS[hash_int % len(_CHANNEL_EMOJIS)]


  def _build_channel_signature(channel: TelegramChannel) -> str:
      """
      Build the signature line appended to every post.
      Format:  <emoji> @username | Channel Name
      """
      emoji = _assign_channel_emoji(str(channel.id))

      if channel.username:
          handle = f"@{channel.username.lstrip('@')}"
      else:
          handle = f"ID: `{channel.telegram_channel_id}`"

      name_part = f" | {channel.display_name}" if channel.display_name else ""
      return f"\n\n━━━━━━━━━━━━━━━━━━━━━\n{emoji} {handle}{name_part}"


  async def _refresh_channel_info(client, channel: TelegramChannel) -> None:
      """
      Fetch channel entity from Telegram and update username / display_name
      if they are missing or stale. Silently skips on any error.
      """
      try:
          entity = await client.get_entity(channel.telegram_channel_id)
          changed = False

          username = getattr(entity, "username", None)
          if username and channel.username != username:
              channel.username = username
              changed = True

          title = getattr(entity, "title", None)
          if title and channel.display_name != title:
              channel.display_name = title
              changed = True

          if changed:
              logger.info(
                  "channel_info_refreshed",
                  channel_id=str(channel.id),
                  username=channel.username,
                  display_name=channel.display_name,
              )
      except Exception as e:
          logger.warning("channel_info_refresh_failed",
                         channel_id=str(channel.id), error=str(e))


  async def publish_post(session: AsyncSession, post: Post) -> dict:
      if not _userbot_manager:
          logger.error("publisher_no_userbot_manager")
          return {}

      from app.cache.redis_client import cache_get
      posting_paused = await cache_get("system:posting_paused")
      if posting_paused:
          logger.info("publishing_paused_skipping")
          return {}

      results = {}
      channel_ids = post.channel_ids or []

      for channel_id_str in channel_ids:
          channel_id = uuid.UUID(channel_id_str) if isinstance(channel_id_str, str) else channel_id_str
          result = await session.execute(select(TelegramChannel).where(TelegramChannel.id == channel_id))
          channel = result.scalar_one_or_none()

          if not channel or not channel.is_active:
              results[str(channel_id)] = {"status": "skipped", "reason": "channel_not_found_or_inactive"}
              continue

          content = post.languages.get(channel.language) or post.content
          if not content:
              results[str(channel_id)] = {"status": "skipped", "reason": "no_content_for_language"}
              continue

          try:
              client = _userbot_manager.get_client(str(post.account_id))
              if not (client and client.is_connected):
                  results[str(channel_id)] = {"status": "error", "reason": "no_connected_client"}
                  continue

              # Auto-detect and cache username/display_name if missing
              if not channel.username or not channel.display_name:
                  await _refresh_channel_info(client, channel)

              # Build the channel signature and append to content
              signature = _build_channel_signature(channel)
              final_content = content + signature

              if post.image_url:
                  # Send as media post: text becomes the caption (all in one message)
                  caption = _truncate_caption(final_content, MAX_CAPTION_LENGTH)
                  is_video = _is_video_url(post.image_url)

                  if is_video:
                      msg = await client.send_file(
                          channel.telegram_channel_id,
                          post.image_url,
                          caption=caption,
                          parse_mode="md",
                          supports_streaming=True,
                      )
                      media_type = "video"
                  else:
                      msg = await client.send_file(
                          channel.telegram_channel_id,
                          post.image_url,
                          caption=caption,
                          parse_mode="md",
                      )
                      media_type = "image"

                  results[str(channel_id)] = {
                      "status": "published",
                      "message_id": msg.id,
                      "has_media": True,
                      "media_type": media_type,
                      "signature": signature.strip(),
                  }
              else:
                  # Text-only post
                  text = _truncate_caption(final_content, MAX_TEXT_LENGTH)
                  msg = await client.send_message(
                      channel.telegram_channel_id,
                      text,
                      parse_mode="md",
                  )
                  results[str(channel_id)] = {
                      "status": "published",
                      "message_id": msg.id,
                      "has_media": False,
                      "media_type": None,
                      "signature": signature.strip(),
                  }

              channel.post_count = (channel.post_count or 0) + 1
              await increment_daily_stat("posts_published")
              logger.info(
                  "post_published",
                  channel_id=str(channel_id),
                  msg_id=msg.id,
                  username=channel.username,
                  has_media=bool(post.image_url),
                  media_type=results[str(channel_id)].get("media_type"),
              )
              await asyncio.sleep(1)

          except Exception as e:
              logger.error("publish_failed", channel_id=str(channel_id), error=str(e))
              results[str(channel_id)] = {"status": "error", "reason": str(e)[:200]}

      published_count = sum(1 for r in results.values() if r.get("status") == "published")
      post.publish_log = results
      post.status = "published" if published_count > 0 else "failed"
      post.published_at = datetime.now(timezone.utc)

      logger.info("post_publish_complete", post_id=str(post.id),
                  published=published_count, total=len(channel_ids))
      return results
  