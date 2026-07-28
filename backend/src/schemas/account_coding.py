import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.schemas.account import AccountRead
from src.schemas.journal_entry import JournalEntryRead


class AccountCodingCorrect(BaseModel):
    account_id: uuid.UUID


class AccountCodingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    expense_entry_id: uuid.UUID
    account: AccountRead
    confidence_score: Decimal | None
    source: Literal["ai_suggested", "user"]
    status: Literal["approved", "pending_review"]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AccountCodingWithJournalEntry(BaseModel):
    coding: AccountCodingRead
    journal_entry: JournalEntryRead | None = None
