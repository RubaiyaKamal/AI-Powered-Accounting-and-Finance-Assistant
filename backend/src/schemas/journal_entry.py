import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.schemas.account import AccountRead


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    expense_entry_id: uuid.UUID
    debit_account: AccountRead
    credit_account: AccountRead
    amount: Decimal
    date: datetime.date
    status: Literal["posted", "reversed"]
    reverses_journal_entry_id: uuid.UUID | None = None


class JournalEntryListResponse(BaseModel):
    items: list[JournalEntryRead]
    total: int
