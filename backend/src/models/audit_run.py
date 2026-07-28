import datetime
import uuid

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    start: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    entries_evaluated: Mapped[int] = mapped_column(Integer, nullable=False)
    entries_flagged: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    flags: Mapped[list["AnomalyFlag"]] = relationship(  # noqa: F821
        back_populates="audit_run", order_by="AnomalyFlag.score.desc()"
    )
