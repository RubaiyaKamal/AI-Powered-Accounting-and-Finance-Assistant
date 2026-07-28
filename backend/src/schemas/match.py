import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MatchCreate(BaseModel):
    expense_entry_id: uuid.UUID


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bank_transaction_id: uuid.UUID
    expense_entry_id: uuid.UUID | None
    source: Literal["auto", "manual"]
    status: Literal["confirmed", "dismissed"]
    ai_reasoning: str | None
