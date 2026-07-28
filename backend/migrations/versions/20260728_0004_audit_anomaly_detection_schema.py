"""audit anomaly detection schema

Revision ID: 20260728_0004
Revises: 20260728_0003
Create Date: 2026-07-28

Creates audit_runs and anomaly_flags (data-model.md). anomaly_flags uses
real, enforced FKs with ON DELETE CASCADE for both audit_run_id and
journal_entry_id — an AnomalyFlag is an operational annotation on a run
and an entry, not itself a financial posting (research.md, mirroring
004-bank-reconciliation's Match precedent).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260728_0004"
down_revision = "20260728_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("start", sa.Date(), nullable=False),
        sa.Column("end", sa.Date(), nullable=False),
        sa.Column("entries_evaluated", sa.Integer(), nullable=False),
        sa.Column("entries_flagged", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "anomaly_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "audit_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audit_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "journal_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("journal_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Numeric(6, 4), nullable=False),
        sa.Column("reason_categories", postgresql.ARRAY(sa.String(length=30)), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("resolution", sa.String(length=20), nullable=False, server_default="unreviewed"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("anomaly_flags")
    op.drop_table("audit_runs")
