import datetime
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.schemas.match import MatchRead


class BankTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: datetime.date
    amount: Decimal
    description: str


class BankTransactionWithMatch(BankTransactionRead):
    match: MatchRead | None = None


class BankTransactionListResponse(BaseModel):
    items: list[BankTransactionWithMatch]
    total: int


class ExpenseEntrySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    date: datetime.date
    description: str | None


class ImportInvalidRow(BaseModel):
    row: int
    reason: str


class ImportSummary(BaseModel):
    imported: int
    duplicates_skipped: int
    invalid_rows_skipped: list[ImportInvalidRow]
    auto_matched: int
    needs_review: int


class ReviewQueueItem(BaseModel):
    bank_transaction: BankTransactionRead
    suggested_expense_entry: ExpenseEntrySummary | None = None
    ai_reasoning: str | None = None
    candidates_considered: list[ExpenseEntrySummary] | None = None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int
