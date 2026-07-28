import datetime
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.journal_entry import JournalEntryRead

AuditRunStatus = Literal["completed", "insufficient_data"]
FlagResolution = Literal["unreviewed", "confirmed_issue", "false_positive", "no_action_needed"]


class AuditRunTriggerRequest(BaseModel):
    start: datetime.date | None = None
    end: datetime.date | None = None


class AnomalyFlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    journal_entry: JournalEntryRead
    score: Decimal
    reason_categories: list[str]
    explanation: str
    resolution: FlagResolution
    resolved_at: datetime.datetime | None = None


class AuditRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start: datetime.date
    end: datetime.date
    status: AuditRunStatus
    entries_evaluated: int
    entries_flagged: int
    created_at: datetime.datetime
    flags: list[AnomalyFlagResponse]


class AuditRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start: datetime.date
    end: datetime.date
    status: AuditRunStatus
    entries_evaluated: int
    entries_flagged: int
    created_at: datetime.datetime


class AuditRunListResponse(BaseModel):
    items: list[AuditRunSummary]
    total: int


class ResolveFlagRequest(BaseModel):
    resolution: Literal["confirmed_issue", "false_positive", "no_action_needed"] = Field(
        description="The admin's recorded outcome for this flag"
    )
