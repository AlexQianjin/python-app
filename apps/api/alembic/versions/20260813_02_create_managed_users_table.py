"""Create the managed users table.

Revision ID: 20260813_02
Revises: 20260813_01
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260813_02"
down_revision: str | None = "20260813_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "managed_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_managed_users_email", "managed_users", ["email"], unique=True)
    op.create_index("ix_managed_users_name", "managed_users", ["name"])
    op.create_index("ix_managed_users_role", "managed_users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_managed_users_role", table_name="managed_users")
    op.drop_index("ix_managed_users_name", table_name="managed_users")
    op.drop_index("ix_managed_users_email", table_name="managed_users")
    op.drop_table("managed_users")
