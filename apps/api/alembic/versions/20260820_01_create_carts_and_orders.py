"""Create shopping carts and orders.

Revision ID: 20260820_01
Revises: 20260813_02
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260820_01"
down_revision: str | None = "20260813_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id"),
    )
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"])
    op.create_index("ix_cart_items_user_id", "cart_items", ["user_id"])
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("sku", sa.String(length=32), nullable=False),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_cart_items_user_id", table_name="cart_items")
    op.drop_index("ix_cart_items_product_id", table_name="cart_items")
    op.drop_table("cart_items")
