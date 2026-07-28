import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

RequestKind = Literal["amount", "breakdown", "comparison", "forecast"]
ForecastStatus = Literal["completed", "insufficient_data"]


class SpendingAmountResponse(BaseModel):
    account_code: str
    account_name: str
    start: datetime.date
    end: datetime.date
    amount: Decimal


class BreakdownLine(BaseModel):
    account_code: str
    account_name: str
    amount: Decimal
    share: Decimal


class SpendingBreakdownResponse(BaseModel):
    start: datetime.date
    end: datetime.date
    lines: list[BreakdownLine]
    total: Decimal


class PeriodRange(BaseModel):
    start: datetime.date
    end: datetime.date


class ComparisonLine(BaseModel):
    account_code: str
    account_name: str
    period_a_amount: Decimal
    period_b_amount: Decimal
    change: Decimal


class SpendingComparisonResponse(BaseModel):
    period_a: PeriodRange
    period_b: PeriodRange
    lines: list[ComparisonLine]
    total_period_a: Decimal
    total_period_b: Decimal
    total_change: Decimal


class HistoricalPoint(BaseModel):
    start: datetime.date
    end: datetime.date
    amount: Decimal


class SpendingForecastResponse(BaseModel):
    status: ForecastStatus
    target_start: datetime.date
    target_end: datetime.date
    forecast_amount: Decimal | None
    is_estimate: bool = True
    method: str | None
    historical_points: list[HistoricalPoint]


class SpendingQueryRequest(BaseModel):
    question: str


class SpendingQueryResponse(BaseModel):
    request_kind: RequestKind | None
    data: dict | None
    narrative: str
