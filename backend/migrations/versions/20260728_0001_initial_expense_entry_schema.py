"""initial expense entry schema

Revision ID: 20260728_0001
Revises:
Create Date: 2026-07-28

Creates categories, expense_entries, and expense_entry_edit_history
(data-model.md), and seeds the starter category set (FR-014).
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260728_0001"
down_revision = None
branch_labels = None
depends_on = None

STARTER_CATEGORIES = ["Utilities", "Rent", "Salaries", "Supplies"]


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "expense_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id"),
            nullable=False,
        ),
        sa.Column("category_source", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_expense_entries_amount_positive"),
    )

    op.create_table(
        "expense_entry_edit_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "expense_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expense_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.String(length=500), nullable=True),
        sa.Column("new_value", sa.String(length=500), nullable=True),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.bulk_insert(
        categories,
        [{"id": uuid.uuid4(), "name": name, "is_custom": False} for name in STARTER_CATEGORIES],
    )


def downgrade() -> None:
    op.drop_table("expense_entry_edit_history")
    op.drop_table("expense_entries")
    op.drop_table("categories")
