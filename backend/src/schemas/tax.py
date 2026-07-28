import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

TaxSummaryStatus = Literal["draft", "signed_off"]


class TaxRulesDocumentCreate(BaseModel):
    title: str
    content: str


class TaxRulesDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content: str
    chunk_count: int
    created_at: datetime.datetime


class TaxRulesDocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    chunk_count: int
    created_at: datetime.datetime


class TaxRulesDocumentListResponse(BaseModel):
    items: list[TaxRulesDocumentSummary]
    total: int


class CitedPassage(BaseModel):
    document_title: str
    chunk_text: str


class TaxSummaryTriggerRequest(BaseModel):
    start: datetime.date | None = None
    end: datetime.date | None = None


class TaxSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start: datetime.date
    end: datetime.date
    status: TaxSummaryStatus
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    cited_passages: list[CitedPassage]
    narrative: str
    generated_at: datetime.datetime
    signed_off_at: datetime.datetime | None = None


class TaxSummarySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start: datetime.date
    end: datetime.date
    status: TaxSummaryStatus
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    generated_at: datetime.datetime
    signed_off_at: datetime.datetime | None = None


class TaxSummaryListResponse(BaseModel):
    items: list[TaxSummarySummary]
    total: int
