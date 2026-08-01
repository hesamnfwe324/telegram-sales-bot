"""add safe RDP educational challenges

Revision ID: c5d6e7f8a9b0
Revises: e4f1a2b3c9d0
Create Date: 2026-08-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "e4f1a2b3c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rdp_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("challenge_type", sa.String(length=40), nullable=False, server_default="configuration_quiz"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("translations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("channel_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("publish_log", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="ai"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rdp_challenges_status", "rdp_challenges", ["status"], unique=False)

    op.create_table(
        "rdp_challenge_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("channel_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("selected_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("explanation_language", sa.String(length=5), nullable=False, server_default="en"),
        sa.Column("feedback_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["rdp_challenges.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("challenge_id", "telegram_user_id", name="uq_rdp_challenge_response_user"),
    )
    op.create_index(
        "ix_rdp_challenge_responses_challenge_id",
        "rdp_challenge_responses",
        ["challenge_id"],
        unique=False,
    )
    op.create_index(
        "ix_rdp_challenge_responses_telegram_user_id",
        "rdp_challenge_responses",
        ["telegram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rdp_challenge_responses_telegram_user_id", table_name="rdp_challenge_responses")
    op.drop_index("ix_rdp_challenge_responses_challenge_id", table_name="rdp_challenge_responses")
    op.drop_table("rdp_challenge_responses")
    op.drop_index("ix_rdp_challenges_status", table_name="rdp_challenges")
    op.drop_table("rdp_challenges")