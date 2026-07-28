import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index(
            "uq_matches_expense_entry_id",
            "expense_entry_id",
            unique=True,
            postgresql_where="expense_entry_id IS NOT NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bank_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_transactions.id"), unique=True, nullable=False
    )
    # Real, enforced FK with cascade — unlike 002-ledger-journal-entries's
    # deliberately non-enforced FKs, a Match isn't a financial posting that
    # needs to survive its source's deletion (research.md).
    expense_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_entries.id", ondelete="CASCADE"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    bank_transaction: Mapped["BankTransaction"] = relationship(  # noqa: F821
        back_populates="match"
    )
