import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RDPChallenge(Base, TimestampMixin):
    """A safe, educational RDP challenge campaign."""

    __tablename__ = "rdp_challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_type: Mapped[str] = mapped_column(String(40), default="configuration_quiz")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    translations: Mapped[dict] = mapped_column(JSONB, default=dict)
    channel_ids: Mapped[list] = mapped_column(JSONB, default=list)
    publish_log: Mapped[dict] = mapped_column(JSONB, default=dict)
    source: Mapped[str] = mapped_column(String(20), default="ai")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChallengeResponse(Base, TimestampMixin):
    """One participant's answer to a challenge campaign."""

    __tablename__ = "rdp_challenge_responses"
    __table_args__ = (
        UniqueConstraint(
            "challenge_id",
            "telegram_user_id",
            name="uq_rdp_challenge_response_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rdp_challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    selected_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    explanation_language: Mapped[str] = mapped_column(String(5), default="en")
    feedback_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)