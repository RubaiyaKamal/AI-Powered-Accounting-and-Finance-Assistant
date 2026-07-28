import datetime
import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_journal_entries_amount_positive"),
        CheckConstraint(
            "debit_account_id != credit_account_id", name="ck_journal_entries_distinct_accounts"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Not a DB-enforced FK, same reasoning as AccountCoding.expense_entry_id:
    # a journal entry must survive its source expense entry's deletion
    # (FR-012) rather than block it or cascade away.
    expense_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    account_coding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account_codings.id"), nullable=False
    )
    debit_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    credit_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="posted")
    reverses_journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account_coding: Mapped["AccountCoding"] = relationship(  # noqa: F821
        back_populates="journal_entries"
    )
    debit_account: Mapped["Account"] = relationship(foreign_keys=[debit_account_id])  # noqa: F821
    credit_account: Mapped["Account"] = relationship(  # noqa: F821
        foreign_keys=[credit_account_id]
    )
    reverses: Mapped["JournalEntry | None"] = relationship(
        remote_side=[id], foreign_keys=[reverses_journal_entry_id]
    )
