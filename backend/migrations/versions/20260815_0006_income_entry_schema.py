"""income entry schema

Revision ID: 20260815_0006
Revises: 20260728_0005
Create Date: 2026-08-15

Creates income_sources and income_entries (data-model.md), generalizes
journal_entries to allow a posting to originate from either an expense
entry or an income entry (expense_entry_id/account_coding_id become
nullable, income_entry_id is added, and an exactly-one-source check
constraint is added), and seeds two starter income sources: "Sales"
(mapped to a new Revenue account) and "Owner Investment" (mapped to a new
Equity account) — research.md Decision 5.
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260815_0006"
down_revision = "20260728_0005"
branch_labels = None
depends_on = None

STARTER_SOURCES = [
    # (source_name, account_code, account_name, account_type)
    ("Sales", "4000", "Sales Revenue", "revenue"),
    ("Owner Investment", "3000", "Owner's Capital", "equity"),
]


def upgrade() -> None:
    accounts = sa.table(
        "accounts",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("type", sa.String),
        sa.column("is_custom", sa.Boolean),
    )

    income_sources = op.create_table(
        "income_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "income_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("income_sources.id"),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount > 0", name="ck_income_entries_amount_positive"),
    )

    op.alter_column("journal_entries", "expense_entry_id", nullable=True)
    op.alter_column("journal_entries", "account_coding_id", nullable=True)
    op.add_column(
        "journal_entries",
        sa.Column("income_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_journal_entries_exactly_one_source",
        "journal_entries",
        "(expense_entry_id IS NOT NULL) != (income_entry_id IS NOT NULL)",
    )

    for source_name, code, account_name, account_type in STARTER_SOURCES:
        account_id = uuid.uuid4()
        op.bulk_insert(
            accounts,
            [
                {
                    "id": account_id,
                    "code": code,
                    "name": account_name,
                    "type": account_type,
                    "is_custom": False,
                }
            ],
        )
        op.bulk_insert(
            income_sources,
            [
                {
                    "id": uuid.uuid4(),
                    "name": source_name,
                    "account_id": account_id,
                    "is_custom": False,
                }
            ],
        )


def downgrade() -> None:
    op.drop_constraint(
        "ck_journal_entries_exactly_one_source", "journal_entries", type_="check"
    )
    op.drop_column("journal_entries", "income_entry_id")
    op.alter_column("journal_entries", "account_coding_id", nullable=False)
    op.alter_column("journal_entries", "expense_entry_id", nullable=False)
    op.drop_table("income_entries")
    op.drop_table("income_sources")
