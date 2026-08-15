import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.account import AccountRead


class IncomeSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: Literal["revenue", "equity"]


class IncomeSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account: AccountRead
    is_custom: bool


class IncomeSourceListResponse(BaseModel):
    items: list[IncomeSourceRead]
