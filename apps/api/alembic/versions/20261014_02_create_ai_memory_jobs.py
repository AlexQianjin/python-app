"""Create durable Mem0 work queue.

Revision ID: 20261014_02
Revises: 20261014_01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261014_02"
down_revision: str | None = "20261014_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_memory_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_memory_jobs_user_id", "ai_memory_jobs", ["user_id"])
    op.create_index("ix_ai_memory_jobs_status", "ai_memory_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ai_memory_jobs_status", table_name="ai_memory_jobs")
    op.drop_index("ix_ai_memory_jobs_user_id", table_name="ai_memory_jobs")
    op.drop_table("ai_memory_jobs")
