import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.category import CategoryRead


class ExpenseEntryCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    date: datetime.date
    category_id: uuid.UUID | None = None
    category_name_hint: str | None = Field(
        default=None,
        description="Used only when category_id is omitted, to drive AI category suggestion.",
    )
    description: str | None = Field(default=None, max_length=500)
    source: Literal["manual", "natural_language", "receipt_image"] = "manual"


class ExpenseEntryUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    date: datetime.date | None = None
    category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=500)


class EditHistoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime.datetime


class ExpenseEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    date: datetime.date
    category: CategoryRead
    category_source: Literal["user", "ai_suggested"]
    description: str | None
    source: Literal["manual", "natural_language", "receipt_image"]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ExpenseEntryDetailRead(ExpenseEntryRead):
    edit_history: list[EditHistoryEntryRead] = []


class ExpenseEntryListResponse(BaseModel):
    items: list[ExpenseEntryRead]
    total: int
