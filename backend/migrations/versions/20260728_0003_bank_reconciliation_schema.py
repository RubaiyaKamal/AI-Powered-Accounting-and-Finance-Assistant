"""bank reconciliation schema

Revision ID: 20260728_0003
Revises: 20260728_0002
Create Date: 2026-07-28

Creates bank_transactions and matches (data-model.md). matches.expense_entry_id
uses a real, enforced FK with ON DELETE CASCADE (unlike 002's deliberately
non-enforced FKs) — a Match is an operational link, not a financial
posting requiring an audit trail (research.md).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260728_0003"
down_revision = "20260728_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column(
            "suggested_expense_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expense_entries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "date", "amount", "description", name="uq_bank_transactions_date_amount_description"
        ),
    )

    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "bank_transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bank_transactions.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "expense_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expense_entries.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "uq_matches_expense_entry_id",
        "matches",
        ["expense_entry_id"],
        unique=True,
        postgresql_where=sa.text("expense_entry_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_matches_expense_entry_id", table_name="matches")
    op.drop_table("matches")
    op.drop_table("bank_transactions")
