import datetime
import uuid
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class TaxSummary(Base):
    __tablename__ = "tax_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    start: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # A fixed snapshot ({"document_title", "chunk_text"} per element) taken
    # at generation time — never a live reference to a
    # TaxRulesDocumentChunk row, so a signed-off summary can't be altered
    # by a later document edit/removal (research.md, FR-007).
    cited_passages: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    signed_off_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
