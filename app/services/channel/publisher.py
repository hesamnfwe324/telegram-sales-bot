from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.monitoring.metrics_collector import increment_daily_stat
from app.core.logging import get_logger
from datetime import datetime, timezone
import asyncio
import uuid

logger = get_logger(__name__)

_userbot_manager = None
MAX_CAPTION_LENGTH = 1020


def set_userbot_manager(manager) -> None:
    global _userbot_manager
    _userbot_manager = manager


def _truncate_caption(text: str) -> str:
    if len(text) <= MAX_CAPTION_LENGTH:
        return text
    return text[:MAX_CAPTION_LENGTH] + "…"


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
            if client and client.is_connected:
                if post.image_url:
                    caption = _truncate_caption(content)
                    msg = await client.send_file(
                        channel.telegram_channel_id,
                        post.image_url,
                        caption=caption,
                        parse_mode="md",
                    )
                else:
                    msg = await client.send_message(
                        channel.telegram_channel_id,
                        content,
                        parse_mode="md",
                    )

                results[str(channel_id)] = {
                    "status": "published",
                    "message_id": msg.id,
                    "has_image": bool(post.image_url),
                }
                channel.post_count = (channel.post_count or 0) + 1
                await increment_daily_stat("posts_published")
                logger.info("post_published", channel_id=str(channel_id), msg_id=msg.id, has_image=bool(post.image_url))
                await asyncio.sleep(1)
            else:
                results[str(channel_id)] = {"status": "error", "reason": "no_connected_client"}
        except Exception as e:
            logger.error("publish_failed", channel_id=str(channel_id), error=str(e))
            results[str(channel_id)] = {"status": "error", "reason": str(e)[:200]}

    published_count = sum(1 for r in results.values() if r.get("status") == "published")
    post.publish_log = results
    post.status = "published" if published_count > 0 else "failed"
    post.published_at = datetime.now(timezone.utc)

    logger.info("post_publish_complete", post_id=str(post.id), published=published_count, total=len(channel_ids))
    return results
