"""tax compliance summaries schema

Revision ID: 20260728_0005
Revises: 20260728_0004
Create Date: 2026-07-28

Creates tax_rules_documents, tax_rules_document_chunks, and tax_summaries
(data-model.md). tax_summaries stores its figures and cited_passages as
fixed values/snapshots rather than live references to documents/chunks,
so a signed-off summary can't be altered by a later document edit or
removal (research.md's immutability decision).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260728_0005"
down_revision = "20260728_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_rules_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "tax_rules_document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tax_rules_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "tax_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("start", sa.Date(), nullable=False),
        sa.Column("end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("total_revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_expenses", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_profit", sa.Numeric(12, 2), nullable=False),
        sa.Column("cited_passages", postgresql.JSON(), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("tax_summaries")
    op.drop_table("tax_rules_document_chunks")
    op.drop_table("tax_rules_documents")
