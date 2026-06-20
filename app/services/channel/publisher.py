import io
  import httpx
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

  MAX_CAPTION_LENGTH = 1020
  MAX_TEXT_LENGTH = 4090

  _CHANNEL_EMOJIS = [
      "🌐", "🚀", "💡", "⚡", "🔥", "🛡️", "💎", "🎯",
      "🔮", "🌟", "💫", "🏆", "⚙️", "🖥️", "🔐", "📡",
      "🧠", "🌊", "🎪", "🦅", "🦁", "🐉", "🌙", "☄️",
      "🏔️", "🔱", "⚜️", "🌈", "🎖️", "🛰️",
  ]

  _VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}


  def set_userbot_manager(manager) -> None:
      global _userbot_manager
      _userbot_manager = manager


  def _is_video_url(url: str) -> bool:
      lower = url.lower().split("?")[0]
      return any(lower.endswith(ext) for ext in _VIDEO_EXTENSIONS)


  def _truncate_caption(text: str, limit: int = MAX_CAPTION_LENGTH) -> str:
      if len(text) <= limit:
          return text
      truncated = text[:limit - 3]
      last_newline = truncated.rfind("\n")
      if last_newline > limit // 2:
          truncated = truncated[:last_newline]
      return truncated + "…"


  def _assign_channel_emoji(channel_id: str) -> str:
      hash_int = int(hashlib.md5(str(channel_id).encode()).hexdigest(), 16)
      return _CHANNEL_EMOJIS[hash_int % len(_CHANNEL_EMOJIS)]


  def _build_channel_signature(channel: TelegramChannel) -> str:
      emoji = _assign_channel_emoji(str(channel.id))
      if channel.username:
          handle = f"@{channel.username.lstrip('@')}"
      else:
          handle = f"ID: `{channel.telegram_channel_id}`"
      name_part = f" | {channel.display_name}" if channel.display_name else ""
      return f"\n\n━━━━━━━━━━━━━━━━━━━━━\n{emoji} {handle}{name_part}"


  async def _refresh_channel_info(client, channel: TelegramChannel) -> None:
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


  async def _download_media_bytes(url: str, timeout: int = 90) -> bytes | None:
      """
      Download image/video from a URL and return raw bytes.
      Uses httpx with a generous timeout since AI image generation can be slow.
      Returns None if download fails so caller can fall back to text-only.
      """
      try:
          async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
              logger.info("media_download_start", url=url[:80])
              response = await client.get(url)
              response.raise_for_status()
              data = response.content
              content_type = response.headers.get("content-type", "")
              logger.info(
                  "media_download_done",
                  size_kb=len(data) // 1024,
                  content_type=content_type,
              )
              return data
      except Exception as e:
          logger.warning("media_download_failed", url=url[:80], error=str(e))
          return None


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
          result = await session.execute(
              select(TelegramChannel).where(TelegramChannel.id == channel_id)
          )
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

              if not channel.username or not channel.display_name:
                  await _refresh_channel_info(client, channel)

              signature = _build_channel_signature(channel)
              final_content = content + signature

              media_sent = False

              if post.image_url:
                  # Pre-download the media bytes (handles AI-generated images, slow URLs, redirects)
                  media_bytes = await _download_media_bytes(post.image_url)

                  if media_bytes:
                      caption = _truncate_caption(final_content, MAX_CAPTION_LENGTH)
                      is_video = _is_video_url(post.image_url)
                      file_obj = io.BytesIO(media_bytes)

                      if is_video:
                          # Give the BytesIO a filename hint so Telethon knows it's a video
                          file_obj.name = "video.mp4"
                          msg = await client.send_file(
                              channel.telegram_channel_id,
                              file_obj,
                              caption=caption,
                              parse_mode="md",
                              supports_streaming=True,
                          )
                          media_type = "video"
                      else:
                          file_obj.name = "image.jpg"
                          msg = await client.send_file(
                              channel.telegram_channel_id,
                              file_obj,
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
                      media_sent = True
                      logger.info(
                          "post_published_with_media",
                          channel_id=str(channel_id),
                          msg_id=msg.id,
                          media_type=media_type,
                          size_kb=len(media_bytes) // 1024,
                      )
                  else:
                      # Download failed — fall back to text-only
                      logger.warning(
                          "media_download_failed_sending_text_only",
                          channel_id=str(channel_id),
                      )

              if not media_sent:
                  # Text-only post (either no image_url or download failed)
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
                  logger.info(
                      "post_published_text_only",
                      channel_id=str(channel_id),
                      msg_id=msg.id,
                  )

              channel.post_count = (channel.post_count or 0) + 1
              await increment_daily_stat("posts_published")
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
  