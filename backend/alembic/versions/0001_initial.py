"""initial schema — users, products, cart_items, orders, order_items

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-19

This is the EXPAND-friendly baseline. Note users.display_name is nullable from
the start (see Module 07's expand/contract story).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="general"),
        sa.Column("image_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_category", "products", ["category"])

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )
    op.create_index("ix_cart_items_user_id", "cart_items", ["user_id"])
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    # These drops reverse the baseline create. check_migrations.py flags any
    # drop_table (it can't tell upgrade from downgrade), so we acknowledge them:
    # a downgrade never runs in a forward rolling deploy, so it's not the
    # backward-incompatibility the gate guards against.
    op.drop_table("order_items")  # migration-safety: ack baseline downgrade (reverses create)
    op.drop_table("orders")  # migration-safety: ack baseline downgrade (reverses create)
    op.drop_table("cart_items")  # migration-safety: ack baseline downgrade (reverses create)
    op.drop_table("products")  # migration-safety: ack baseline downgrade (reverses create)
    op.drop_table("users")  # migration-safety: ack baseline downgrade (reverses create)
