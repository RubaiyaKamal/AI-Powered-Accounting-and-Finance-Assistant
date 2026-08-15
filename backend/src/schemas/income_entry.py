import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.income_source import IncomeSourceRead


class IncomeEntryCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    date: datetime.date
    source_id: uuid.UUID
    description: str | None = Field(default=None, max_length=500)


class IncomeEntryUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    date: datetime.date | None = None
    source_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=500)


class IncomeEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    date: datetime.date
    source: IncomeSourceRead
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class IncomeEntryListResponse(BaseModel):
    items: list[IncomeEntryRead]
    total: int
