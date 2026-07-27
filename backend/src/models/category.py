import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    expense_entries: Mapped[list["ExpenseEntry"]] = relationship(  # noqa: F821
        back_populates="category"
    )
