import calendar
import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import Account
from src.models.journal_entry import JournalEntry
from src.schemas.reports import (
    AccountBalance,
    BalanceSheetResponse,
    CashFlowResponse,
    ProfitAndLossResponse,
    TrialBalanceResponse,
)
from src.services.ledger_service import OFFSET_ACCOUNT_NAME

DEBIT_NORMAL_TYPES = {"asset", "expense"}


class ValidationError(Exception):
    pass


def _active_posting_filters(date_column, as_of, start, end):
    # The same "currently active, non-reversal, non-reversed posting"
    # definition ledger_service.active_journal_entry() uses for a single
    # coding, applied globally across all codings for aggregation
    # (research.md) — this is what makes a reversed entry and its reversal
    # cancel out to zero instead of double-counting the correction.
    filters = [
        JournalEntry.status == "posted",
        JournalEntry.reverses_journal_entry_id.is_(None),
    ]
    if as_of is not None:
        filters.append(date_column <= as_of)
    if start is not None:
        filters.append(date_column >= start)
    if end is not None:
        filters.append(date_column <= end)
    return filters


async def _account_balances(
    session: AsyncSession,
    *,
    as_of: datetime.date | None = None,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> list[AccountBalance]:
    """Per-account debit/credit totals over active postings, optionally date-windowed.

    `as_of` bounds the window to entries dated on or before `as_of` (a
    point-in-time snapshot, cumulative from inception). `start`/`end` bound
    it to entries dated within `[start, end]` (a period summary). Only
    accounts with a non-zero resulting balance are returned.
    """
    filters = _active_posting_filters(JournalEntry.date, as_of, start, end)

    debit_stmt = (
        select(JournalEntry.debit_account_id, func.sum(JournalEntry.amount))
        .where(*filters)
        .group_by(JournalEntry.debit_account_id)
    )
    credit_stmt = (
        select(JournalEntry.credit_account_id, func.sum(JournalEntry.amount))
        .where(*filters)
        .group_by(JournalEntry.credit_account_id)
    )

    debit_totals = dict((await session.execute(debit_stmt)).all())
    credit_totals = dict((await session.execute(credit_stmt)).all())

    account_ids = set(debit_totals) | set(credit_totals)
    if not account_ids:
        return []

    accounts = (
        (await session.execute(select(Account).where(Account.id.in_(account_ids))))
        .scalars()
        .all()
    )

    balances = []
    for account in accounts:
        debit_total = debit_totals.get(account.id, Decimal("0.00"))
        credit_total = credit_totals.get(account.id, Decimal("0.00"))
        balance = (
            debit_total - credit_total
            if account.type in DEBIT_NORMAL_TYPES
            else credit_total - debit_total
        )
        if balance == 0:
            continue
        balances.append(
            AccountBalance(
                account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                account_type=account.type,
                debit_total=debit_total,
                credit_total=credit_total,
                balance=balance,
            )
        )
    return balances


async def trial_balance(
    session: AsyncSession, as_of: datetime.date | None = None
) -> TrialBalanceResponse:
    as_of = as_of or datetime.date.today()
    lines = await _account_balances(session, as_of=as_of)
    total_debits = sum((line.debit_total for line in lines), Decimal("0.00"))
    total_credits = sum((line.credit_total for line in lines), Decimal("0.00"))
    return TrialBalanceResponse(
        as_of=as_of,
        lines=lines,
        total_debits=total_debits,
        total_credits=total_credits,
        is_balanced=total_debits == total_credits,
    )


def _current_month_range(today: datetime.date) -> tuple[datetime.date, datetime.date]:
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.replace(day=1), today.replace(day=last_day)


async def profit_and_loss(
    session: AsyncSession,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> ProfitAndLossResponse:
    # Per contracts/reports-api.md: if either bound is omitted, both default
    # together to the current calendar month, rather than mixing one
    # explicit bound with an inferred other.
    if start is None or end is None:
        start, end = _current_month_range(datetime.date.today())
    if end < start:
        raise ValidationError("end must not be before start")

    lines = await _account_balances(session, start=start, end=end)
    revenue_lines = [line for line in lines if line.account_type == "revenue"]
    expense_lines = [line for line in lines if line.account_type == "expense"]
    total_revenue = sum((line.balance for line in revenue_lines), Decimal("0.00"))
    total_expenses = sum((line.balance for line in expense_lines), Decimal("0.00"))
    return ProfitAndLossResponse(
        start=start,
        end=end,
        revenue_lines=revenue_lines,
        total_revenue=total_revenue,
        expense_lines=expense_lines,
        total_expenses=total_expenses,
        net_profit=total_revenue - total_expenses,
    )


async def balance_sheet(
    session: AsyncSession, as_of: datetime.date | None = None
) -> BalanceSheetResponse:
    as_of = as_of or datetime.date.today()
    lines = await _account_balances(session, as_of=as_of)
    asset_lines = [line for line in lines if line.account_type == "asset"]
    liability_lines = [line for line in lines if line.account_type == "liability"]
    equity_lines = [line for line in lines if line.account_type == "equity"]
    total_assets = sum((line.balance for line in asset_lines), Decimal("0.00"))
    total_liabilities = sum((line.balance for line in liability_lines), Decimal("0.00"))
    total_equity = sum((line.balance for line in equity_lines), Decimal("0.00"))
    return BalanceSheetResponse(
        as_of=as_of,
        asset_lines=asset_lines,
        total_assets=total_assets,
        liability_lines=liability_lines,
        total_liabilities=total_liabilities,
        equity_lines=equity_lines,
        total_equity=total_equity,
        is_balanced=total_assets == total_liabilities + total_equity,
    )


async def _cash_balance(session: AsyncSession, as_of: datetime.date) -> Decimal:
    lines = await _account_balances(session, as_of=as_of)
    # research.md's single-account assumption: OFFSET_ACCOUNT_NAME ("Cash")
    # is the one designated cash/offset account this system currently has.
    line = next((line for line in lines if line.account_name == OFFSET_ACCOUNT_NAME), None)
    return line.balance if line is not None else Decimal("0.00")


async def cash_flow(
    session: AsyncSession,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> CashFlowResponse:
    if start is None or end is None:
        start, end = _current_month_range(datetime.date.today())
    if end < start:
        raise ValidationError("end must not be before start")

    opening_balance = await _cash_balance(session, start - datetime.timedelta(days=1))
    closing_balance = await _cash_balance(session, end)
    return CashFlowResponse(
        start=start,
        end=end,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        net_change=closing_balance - opening_balance,
    )
