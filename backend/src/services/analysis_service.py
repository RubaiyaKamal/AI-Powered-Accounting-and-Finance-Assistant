import calendar
import datetime
from decimal import Decimal

import numpy as np
from sklearn.linear_model import LinearRegression
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import Account
from src.schemas.analysis import (
    BreakdownLine,
    ComparisonLine,
    HistoricalPoint,
    PeriodRange,
    SpendingAmountResponse,
    SpendingBreakdownResponse,
    SpendingComparisonResponse,
    SpendingForecastResponse,
)
from src.services import reporting_service

# research.md's forecast window: up to 6 preceding calendar months, at
# least 3 of which must have posted activity for a meaningful trend.
FORECAST_LOOKBACK_MONTHS = 6
FORECAST_MIN_MONTHS_WITH_ACTIVITY = 3

SHARE_PRECISION = Decimal("0.001")


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


async def spending_amount(
    session: AsyncSession,
    account_name: str,
    start: datetime.date | None,
    end: datetime.date | None,
) -> SpendingAmountResponse:
    """Total spending for one expense account over a period (US1, FR-001).

    Reuses reporting_service.profit_and_loss for the actual figure — never
    a new aggregation query (research.md). Distinguishes "account exists,
    no activity this period" (a valid zero) from "no such account at all"
    (NotFoundError, FR-005) by falling back to a direct chart-of-accounts
    lookup only when profit_and_loss's expense_lines has no matching line.
    """
    pl = await reporting_service.profit_and_loss(session, start, end)
    lowered = account_name.strip().lower()
    line = next(
        (each for each in pl.expense_lines if each.account_name.lower() == lowered), None
    )
    if line is not None:
        return SpendingAmountResponse(
            account_code=line.account_code,
            account_name=line.account_name,
            start=pl.start,
            end=pl.end,
            amount=line.balance,
        )

    stmt = select(Account).where(
        Account.type == "expense", func.lower(Account.name) == lowered
    )
    account = (await session.execute(stmt)).scalar_one_or_none()
    if account is None:
        raise NotFoundError(f"No expense account named '{account_name}' found")

    return SpendingAmountResponse(
        account_code=account.code,
        account_name=account.name,
        start=pl.start,
        end=pl.end,
        amount=Decimal("0.00"),
    )


async def breakdown(
    session: AsyncSession, start: datetime.date | None, end: datetime.date | None
) -> SpendingBreakdownResponse:
    """Ranked spending across accounts for a period (US2, FR-003(b)).

    Directly reshapes profit_and_loss's own expense_lines — sorted highest
    to lowest, each line's share of the period's total added.
    """
    pl = await reporting_service.profit_and_loss(session, start, end)
    total = pl.total_expenses
    sorted_lines = sorted(pl.expense_lines, key=lambda line: line.balance, reverse=True)
    lines = [
        BreakdownLine(
            account_code=line.account_code,
            account_name=line.account_name,
            amount=line.balance,
            share=(line.balance / total).quantize(SHARE_PRECISION) if total else Decimal("0.000"),
        )
        for line in sorted_lines
    ]
    return SpendingBreakdownResponse(start=pl.start, end=pl.end, lines=lines, total=total)


async def comparison(
    session: AsyncSession,
    period_a_start: datetime.date,
    period_a_end: datetime.date,
    period_b_start: datetime.date,
    period_b_end: datetime.date,
) -> SpendingComparisonResponse:
    """Change in spending between two periods, overall and by account (US2, FR-003(c)).

    Two profit_and_loss calls merged by account code — an account with
    activity in only one period contributes 0.00 for the other, rather
    than being dropped (data-model.md).
    """
    if period_a_end < period_a_start:
        raise ValidationError("period_a end must not be before period_a start")
    if period_b_end < period_b_start:
        raise ValidationError("period_b end must not be before period_b start")

    pl_a = await reporting_service.profit_and_loss(session, period_a_start, period_a_end)
    pl_b = await reporting_service.profit_and_loss(session, period_b_start, period_b_end)

    by_code: dict[str, dict] = {}
    for line in pl_a.expense_lines:
        by_code[line.account_code] = {
            "account_name": line.account_name,
            "period_a_amount": line.balance,
            "period_b_amount": Decimal("0.00"),
        }
    for line in pl_b.expense_lines:
        entry = by_code.setdefault(
            line.account_code,
            {
                "account_name": line.account_name,
                "period_a_amount": Decimal("0.00"),
                "period_b_amount": Decimal("0.00"),
            },
        )
        entry["period_b_amount"] = line.balance
        entry["account_name"] = line.account_name

    lines = [
        ComparisonLine(
            account_code=code,
            account_name=data["account_name"],
            period_a_amount=data["period_a_amount"],
            period_b_amount=data["period_b_amount"],
            change=data["period_b_amount"] - data["period_a_amount"],
        )
        for code, data in sorted(by_code.items())
    ]

    return SpendingComparisonResponse(
        period_a=PeriodRange(start=period_a_start, end=period_a_end),
        period_b=PeriodRange(start=period_b_start, end=period_b_end),
        lines=lines,
        total_period_a=pl_a.total_expenses,
        total_period_b=pl_b.total_expenses,
        total_change=pl_b.total_expenses - pl_a.total_expenses,
    )


def _preceding_month_ranges(
    target_start: datetime.date, count: int
) -> list[tuple[datetime.date, datetime.date]]:
    ranges = []
    year, month = target_start.year, target_start.month
    for _ in range(count):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        last_day = calendar.monthrange(year, month)[1]
        ranges.append((datetime.date(year, month, 1), datetime.date(year, month, last_day)))
    ranges.reverse()
    return ranges


async def forecast(
    session: AsyncSession, target_start: datetime.date, target_end: datetime.date
) -> SpendingForecastResponse:
    """An estimate of future spending via a linear trend (US3, FR-007, FR-008).

    Fits scikit-learn's LinearRegression over up to the past 6 complete
    calendar months' profit_and_loss totals (research.md) — never the LLM.
    Returns status="insufficient_data" (FR-009) rather than a low-confidence
    guess when fewer than 3 of those months have any posted activity.
    """
    if target_end < target_start:
        raise ValidationError("target_end must not be before target_start")

    month_ranges = _preceding_month_ranges(target_start, FORECAST_LOOKBACK_MONTHS)
    points: list[HistoricalPoint] = []
    for start, end in month_ranges:
        pl = await reporting_service.profit_and_loss(session, start, end)
        points.append(HistoricalPoint(start=start, end=end, amount=pl.total_expenses))

    months_with_activity = sum(1 for point in points if point.amount > 0)
    if months_with_activity < FORECAST_MIN_MONTHS_WITH_ACTIVITY:
        return SpendingForecastResponse(
            status="insufficient_data",
            target_start=target_start,
            target_end=target_end,
            forecast_amount=None,
            is_estimate=True,
            method=None,
            historical_points=[],
        )

    x = np.array([[i] for i in range(len(points))])
    y = np.array([float(point.amount) for point in points])
    model = LinearRegression()
    model.fit(x, y)
    predicted = float(model.predict(np.array([[len(points)]]))[0])
    forecast_amount = Decimal(str(round(max(predicted, 0.0), 2)))

    return SpendingForecastResponse(
        status="completed",
        target_start=target_start,
        target_end=target_end,
        forecast_amount=forecast_amount,
        is_estimate=True,
        method=f"linear trend over the last {len(points)} months",
        historical_points=points,
    )
