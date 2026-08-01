import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.account import TelegramAccount
from app.models.challenge import Challenge, ChallengeParticipant
from app.models.channel import TelegramChannel
from app.models.post import Post
from app.services.challenges.generator import generate_challenge_content

logger = get_logger(__name__)


def _slugify(value: str) -> str:
    # Telegram deep-link payloads are ASCII-only in practice and capped at 64
    # bytes. Keep the identifier short regardless of the topic language.
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    prefix = (normalized[:24] or "rdp-challenge").strip("-")
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _public_start_link(slug: str, username: str | None) -> str:
    if username:
        return f"https://t.me/{username.lstrip('@')}?start=challenge_{slug}"
    return f"/start challenge_{slug}"


def build_announcement(content: dict[str, Any], slug: str, username: str | None, ends_at: datetime) -> str:
    end_text = ends_at.strftime("%Y-%m-%d %H:%M UTC")
    hashtags = " ".join(content.get("hashtags", []))
    link = _public_start_link(slug, username)
    return (
        f"⚡️ {content['title']}\n\n"
        f"{content['question']}\n\n"
        "برای شرکت، روی لینک زیر بزن و پاسخ را در ربات ثبت کن:\n"
        f"👉 {link}\n\n"
        f"🎁 جایزه: {content['reward']}\n"
        f"⏳ مهلت شرکت: {end_text}\n"
        "✅ فقط یک پاسخ برای هر نفر ثبت می‌شود؛ نتیجه بر اساس پاسخ درست و زمان ثبت اعلام می‌شود.\n\n"
        f"{hashtags}"
    )


async def create_challenge(
    session: AsyncSession,
    topic: str = "امنیت و سرعت RDP",
    language: str = "fa",
    public_bot_username: str | None = None,
) -> Challenge:
    channel_result = await session.execute(
        select(TelegramChannel).where(TelegramChannel.is_active.is_(True)).order_by(TelegramChannel.created_at)
    )
    channels = list(channel_result.scalars().all())
    if not channels:
        raise RuntimeError("No active Telegram channels are available for a challenge")

    account_result = await session.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == channels[0].account_id,
            TelegramAccount.is_active.is_(True),
        )
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise RuntimeError("No active Telegram account owns the configured channels")

    content = await generate_challenge_content(topic, language)
    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(hours=settings.CHALLENGE_DURATION_HOURS)
    slug = _slugify(topic)
    challenge = Challenge(
        slug=slug,
        title=content["title"],
        topic=topic,
        announcement="",
        question=content["question"],
        answers=content["answers"],
        correct_answer=content["correct_answer"],
        hashtags=content["hashtags"],
        seo_keywords=content["seo_keywords"],
        reward=content["reward"],
        channel_ids=[str(channel.id) for channel in channels],
        language=language,
        status="active",
        starts_at=now,
        ends_at=ends_at,
        winner_count=3,
        metadata_={"account_id": str(account.id), "generated_by": "xai"},
    )
    challenge.announcement = build_announcement(content, slug, public_bot_username, ends_at)
    session.add(challenge)
    await session.flush()
    return challenge


async def publish_challenge(session: AsyncSession, challenge: Challenge) -> dict:
    from app.services.channel.publisher import publish_post

    channel_ids = challenge.channel_ids or []
    if not channel_ids:
        raise RuntimeError("Challenge has no target channels")
    account_id = (challenge.metadata_ or {}).get("account_id")
    if not account_id:
        raise RuntimeError("Challenge has no publishing account")

    post = Post(
        account_id=uuid.UUID(account_id),
        content=challenge.announcement,
        content_type="challenge",
        languages={challenge.language: challenge.announcement},
        channel_ids=channel_ids,
        status="publishing",
        publish_log={"challenge_id": str(challenge.id)},
    )
    session.add(post)
    await session.flush()
    results = await publish_post(session, post)
    published = sum(1 for result in results.values() if result.get("status") == "published")
    challenge.published_at = datetime.now(timezone.utc)
    challenge.metadata_ = {**(challenge.metadata_ or {}), "post_id": str(post.id), "published_channels": published}
    if published == 0:
        challenge.status = "publish_failed"
    await session.commit()
    logger.info("challenge_published", challenge_id=str(challenge.id), published_channels=published)
    return results


async def create_and_publish_challenge(
    session: AsyncSession,
    topic: str = "امنیت و سرعت RDP",
    language: str = "fa",
    public_bot_username: str | None = None,
) -> tuple[Challenge, dict]:
    challenge = await create_challenge(session, topic, language, public_bot_username)
    results = await publish_challenge(session, challenge)
    return challenge, results


async def get_active_challenge(session: AsyncSession) -> Challenge | None:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Challenge)
        .where(Challenge.status == "active", Challenge.starts_at <= now, Challenge.ends_at > now)
        .order_by(desc(Challenge.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def register_participant(
    session: AsyncSession,
    challenge: Challenge,
    telegram_id: int,
    username: str | None,
    display_name: str | None,
) -> ChallengeParticipant:
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge.id,
            ChallengeParticipant.telegram_id == telegram_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant is None:
        participant = ChallengeParticipant(
            challenge_id=challenge.id,
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
            joined_at=datetime.now(timezone.utc),
        )
        session.add(participant)
        await session.commit()
        await session.refresh(participant)
    return participant


async def submit_answer(
    session: AsyncSession,
    challenge: Challenge,
    participant: ChallengeParticipant,
    answer_index: int,
) -> bool:
    if participant.answer_submitted:
        return participant.answer_correct
    participant.answer_submitted = True
    participant.answer_correct = answer_index == challenge.correct_answer
    participant.points = 10 if participant.answer_correct else 0
    participant.metadata_ = {
        **(participant.metadata_ or {}),
        "answer_index": answer_index,
        "answered_at": datetime.now(timezone.utc).isoformat(),
    }
    await session.commit()
    return participant.answer_correct


async def leaderboard(session: AsyncSession, challenge_id: uuid.UUID, limit: int = 10) -> list[ChallengeParticipant]:
    result = await session.execute(
        select(ChallengeParticipant)
        .where(ChallengeParticipant.challenge_id == challenge_id)
        .order_by(desc(ChallengeParticipant.points), ChallengeParticipant.created_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def challenge_summary(session: AsyncSession, challenge: Challenge) -> dict[str, Any]:
    participants = await session.scalar(
        select(func.count(ChallengeParticipant.id)).where(ChallengeParticipant.challenge_id == challenge.id)
    )
    correct = await session.scalar(
        select(func.count(ChallengeParticipant.id)).where(
            ChallengeParticipant.challenge_id == challenge.id,
            ChallengeParticipant.answer_correct.is_(True),
        )
    )
    return {
        "slug": challenge.slug,
        "title": challenge.title,
        "status": challenge.status,
        "participants": participants or 0,
        "correct_answers": correct or 0,
        "channels": len(challenge.channel_ids or []),
        "ends_at": challenge.ends_at.isoformat(),
    }


async def run_challenge_scheduler() -> None:
    import asyncio
    from app.db.session import AsyncSessionLocal
    from app.services.challenges.public_bot import get_public_bot_username

    while True:
        try:
            if settings.CHALLENGE_AUTO_ENABLED:
                async with AsyncSessionLocal() as session:
                    active = await get_active_challenge(session)
                    if not active:
                        latest = await session.scalar(select(Challenge).order_by(desc(Challenge.created_at)).limit(1))
                        due = latest is None or latest.created_at < datetime.now(timezone.utc) - timedelta(
                            hours=settings.CHALLENGE_INTERVAL_HOURS
                        )
                        if due:
                            challenge, _ = await create_and_publish_challenge(
                                session,
                                topic="ترفندهای جذاب RDP و امنیت سرور",
                                language="fa",
                                public_bot_username=get_public_bot_username(),
                            )
                            logger.info("automatic_challenge_created", challenge_id=str(challenge.id))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("challenge_scheduler_failed", error=str(exc))
        await asyncio.sleep(600)