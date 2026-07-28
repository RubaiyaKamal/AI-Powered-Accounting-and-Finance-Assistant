"""ledger and journal entries schema

Revision ID: 20260728_0002
Revises: 20260728_0001
Create Date: 2026-07-28

Creates accounts, account_codings, and journal_entries (data-model.md), and
seeds the starter chart of accounts: one Expense-type account per existing
seeded category, plus a single Cash asset account used as the fixed
credit-side offset for expense-derived postings (research.md).
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260728_0002"
down_revision = "20260728_0001"
branch_labels = None
depends_on = None

STARTER_EXPENSE_ACCOUNTS = [
    ("5000", "Utilities Expense", "Utilities"),
    ("5010", "Rent Expense", "Rent"),
    ("5020", "Salaries Expense", "Salaries"),
    ("5030", "Supplies Expense", "Supplies"),
]


def upgrade() -> None:
    accounts = op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "account_codings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Not a DB-enforced FK: coding history must survive the source
        # expense entry's deletion (FR-012) — see the model's docstring.
        sa.Column("expense_entry_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Not a DB-enforced FK — same audit-survival reasoning as above.
        sa.Column("expense_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_coding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("account_codings.id"),
            nullable=False,
        ),
        sa.Column(
            "debit_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "credit_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "reverses_journal_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("journal_entries.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount > 0", name="ck_journal_entries_amount_positive"),
        sa.CheckConstraint(
            "debit_account_id != credit_account_id", name="ck_journal_entries_distinct_accounts"
        ),
    )

    connection = op.get_bind()
    categories_table = sa.table(
        "categories", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String)
    )

    cash_account_id = uuid.uuid4()
    op.bulk_insert(
        accounts,
        [
            {
                "id": cash_account_id,
                "code": "1000",
                "name": "Cash",
                "type": "asset",
                "is_custom": False,
            }
        ],
    )

    for code, account_name, category_name in STARTER_EXPENSE_ACCOUNTS:
        category_row = connection.execute(
            sa.select(categories_table.c.id).where(categories_table.c.name == category_name)
        ).first()
        if category_row is None:
            continue
        op.bulk_insert(
            accounts,
            [
                {
                    "id": uuid.uuid4(),
                    "code": code,
                    "name": account_name,
                    "type": "expense",
                    "is_custom": False,
                }
            ],
        )


def downgrade() -> None:
    op.drop_table("journal_entries")
    op.drop_table("account_codings")
    op.drop_table("accounts")
