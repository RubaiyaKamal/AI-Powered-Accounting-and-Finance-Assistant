import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.journal_entry import JournalEntry

MIN_ENTRIES_FOR_DETECTION = 20


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


async def _evaluate_entries(
    session: AsyncSession,
    start: datetime.date | None,
    end: datetime.date | None,
) -> tuple[datetime.date, datetime.date, list[JournalEntry]]:
    """Resolve the audit range and load the active posted entries within it.

    Active postings only — `status = 'posted' AND reverses_journal_entry_id
    IS NULL` — the same filter `002`/`005` established, so a reversed
    entry and its reversal never seed the detector or generate a spurious
    flag (research.md, FR-010). Defaults to the whole ledger to date when
    no range is given, since an audit is naturally a look-back over
    whatever history exists rather than a "current period" the way
    reporting's P&L/cash flow default.
    """
    if start is not None and end is not None and end < start:
        raise ValidationError("end must not be before start")

    filters = [
        JournalEntry.status == "posted",
        JournalEntry.reverses_journal_entry_id.is_(None),
    ]
    if start is not None:
        filters.append(JournalEntry.date >= start)
    if end is not None:
        filters.append(JournalEntry.date <= end)

    stmt = (
        select(JournalEntry)
        .where(*filters)
        .options(
            selectinload(JournalEntry.debit_account), selectinload(JournalEntry.credit_account)
        )
        .order_by(JournalEntry.date)
    )
    entries = list((await session.execute(stmt)).scalars().all())

    resolved_start = start if start is not None else min(
        (entry.date for entry in entries), default=datetime.date.today()
    )
    resolved_end = end if end is not None else datetime.date.today()

    return resolved_start, resolved_end, entries
