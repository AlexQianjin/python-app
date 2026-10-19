"""Queue existing documents for indexing with BM25.

Revision ID: 20261014_03
Revises: 20261014_02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261014_03"
down_revision: str | None = "20261014_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE ai_documents "
            "SET status = 'queued', attempts = 0, started_at = NULL, error = NULL "
            "WHERE status = 'ready'"
        )
    )


def downgrade() -> None:
    # Reindexing cannot be reversed once the worker has processed the queue.
    pass
