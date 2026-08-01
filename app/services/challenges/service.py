import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.cache.redis_client import cache_get, cache_set, get_redis
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.channel import TelegramChannel
from app.models.challenge import ChallengeResponse, RDPChallenge
from app.models.post import Post
from app.services.challenges.builder import build_challenge_translations, render_translation
from app.services.channel.publisher import publish_post, set_challenge_buttons

logger = get_logger(__name__)

CAMPAIGN_COOLDOWN_KEY = "rdp_challenge:campaign_cooldown"
CAMPAIGN_LOCK_KEY = "rdp_challenge:campaign_lock"


async def _acquire_campaign_lock(ttl: int = 900) -> bool:
    try:
        redis = await get_redis()
        return bool(await redis.set(CAMPAIGN_LOCK_KEY, str(time.time()), nx=True, ex=ttl))
    except Exception as exc:
        logger.warning("rdp_challenge_lock_failed", error=str(exc)[:120])
        return True


async def _release_campaign_lock() -> None:
    try:
        redis = await get_redis()
        await redis.delete(CAMPAIGN_LOCK_KEY)
    except Exception:
        pass


async def create_and_publish_campaign() -> dict:
    if not await _acquire_campaign_lock():
        return {"status": "locked"}

    try:
        async with AsyncSessionLocal() as session:
            channels = (
                await session.execute(
                    select(TelegramChannel)
                    .where(TelegramChannel.is_active == True)
                    .order_by(TelegramChannel.created_at.asc())
                )
            ).scalars().all()

            if not channels:
                return {"status": "no_channels", "published": 0}

            languages = [channel.language for channel in channels]
            translations, source = await build_challenge_translations(languages)
            challenge = RDPChallenge(
                challenge_type="configuration_quiz",
                status="publishing",
                translations=translations,
                channel_ids=[str(channel.id) for channel in channels],
                source=source,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
            session.add(challenge)
            await session.flush()

            primary_account_id = channels[0].account_id
            post = Post(
                account_id=primary_account_id,
                content=render_translation(translations["en"]),
                content_type="rdp_challenge",
                languages={
                    language: render_translation(translation)
                    for language, translation in translations.items()
                },
                channel_ids=[str(channel.id) for channel in channels],
                status="publishing",
            )
            session.add(post)
            await session.flush()

            results = await publish_post(session, post)
            published = 0
            for channel in channels:
                result = results.get(str(channel.id), {})
                if result.get("status") != "published":
                    continue
                published += 1
                message_id = result.get("message_id")
                translation = translations.get(channel.language) or translations["en"]
                if message_id:
                    await set_challenge_buttons(
                        channel.telegram_channel_id,
                        message_id,
                        str(challenge.id),
                        translation["options"],
                    )

            challenge.status = "published" if published else "failed"
            challenge.published_at = datetime.now(timezone.utc) if published else None
            challenge.publish_log = results
            await session.commit()

        if published:
            await cache_set(
                CAMPAIGN_COOLDOWN_KEY,
                str(time.time()),
                ttl=max(3600, settings.RDP_CHALLENGE_INTERVAL_HOURS * 3600),
            )
        logger.info("rdp_challenge_campaign_complete", source=source, published=published, total=len(channels))
        return {"status": "ok", "source": source, "published": published, "total": len(channels)}
    except Exception:
        logger.exception("rdp_challenge_campaign_failed")
        return {"status": "error", "published": 0}
    finally:
        await _release_campaign_lock()


async def record_answer(challenge_id: str, user_id: int, username: str | None, selected_index: int, channel_id: int | None, language: str) -> dict:
    if selected_index not in range(4):
        return {"status": "invalid_answer"}

    async with AsyncSessionLocal() as session:
        challenge = await session.get(RDPChallenge, uuid.UUID(challenge_id))
        if not challenge or challenge.status != "published":
            return {"status": "expired"}
        if challenge.expires_at and challenge.expires_at <= datetime.now(timezone.utc):
            return {"status": "expired"}

        translation = challenge.translations.get(language) or challenge.translations.get("en")
        if not translation:
            return {"status": "expired"}
        correct_index = int(translation.get("correct_index", -1))
        is_correct = selected_index == correct_index
        response = ChallengeResponse(
            challenge_id=challenge.id,
            telegram_user_id=user_id,
            username=username,
            channel_telegram_id=channel_id,
            selected_index=selected_index,
            is_correct=is_correct,
            explanation_language=language if language in challenge.translations else "en",
        )
        session.add(response)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return {"status": "already_answered", "is_correct": is_correct, "explanation": translation["explanation"]}
        return {
            "status": "recorded",
            "is_correct": is_correct,
            "explanation": translation["explanation"],
        }


async def get_campaign_stats(challenge_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(
                select(func.count(ChallengeResponse.id)).where(
                    ChallengeResponse.challenge_id == uuid.UUID(challenge_id)
                )
            )
        ).scalar() or 0
        correct = (
            await session.execute(
                select(func.count(ChallengeResponse.id)).where(
                    ChallengeResponse.challenge_id == uuid.UUID(challenge_id),
                    ChallengeResponse.is_correct == True,
                )
            )
        ).scalar() or 0
    return {"total": total, "correct": correct}


async def run_challenge_campaign_loop() -> None:
    """Publish a safe educational campaign to all active channels on a cooldown."""
    logger.info("rdp_challenge_loop_started", interval_hours=settings.RDP_CHALLENGE_INTERVAL_HOURS)
    await asyncio.sleep(45)
    while True:
        try:
            if settings.RDP_CHALLENGE_AUTO_ENABLED and not await cache_get(CAMPAIGN_COOLDOWN_KEY):
                await create_and_publish_campaign()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("rdp_challenge_loop_error", error=str(exc)[:180])
        await asyncio.sleep(300)