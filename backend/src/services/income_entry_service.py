import datetime
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.income_entry import IncomeEntry
from src.models.income_source import IncomeSource
from src.services import ledger_service


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidDateRangeError(Exception):
    pass


def _load_options():
    return (selectinload(IncomeEntry.source).selectinload(IncomeSource.account),)


_EDITABLE_FIELDS = ("amount", "date", "source_id", "description")
_LEDGER_AFFECTING_FIELDS = ("amount", "date", "source_id")


async def create_entry(
    session: AsyncSession,
    *,
    amount: Decimal,
    date: datetime.date,
    source_id: uuid.UUID,
    description: str | None,
) -> IncomeEntry:
    if amount <= 0:
        raise ValidationError("amount must be greater than zero")

    source = await session.get(IncomeSource, source_id)
    if source is None:
        raise ValidationError("source_id does not reference an existing income source")

    entry = IncomeEntry(amount=amount, date=date, source_id=source.id, description=description)
    session.add(entry)
    await session.commit()
    await session.refresh(entry, attribute_names=["source"])

    await ledger_service.post_income_journal_entry(session, entry)

    return await get_entry(session, entry.id)


async def list_entries(
    session: AsyncSession,
    *,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    source_id: uuid.UUID | None = None,
) -> list[IncomeEntry]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidDateRangeError("date_from must not be after date_to")

    stmt = select(IncomeEntry).options(*_load_options())
    if date_from is not None:
        stmt = stmt.where(IncomeEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(IncomeEntry.date <= date_to)
    if source_id is not None:
        stmt = stmt.where(IncomeEntry.source_id == source_id)
    stmt = stmt.order_by(IncomeEntry.date.desc(), IncomeEntry.created_at.desc())

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_entry(session: AsyncSession, entry_id: uuid.UUID) -> IncomeEntry:
    stmt = (
        select(IncomeEntry)
        .where(IncomeEntry.id == entry_id)
        .options(*_load_options())
        .execution_options(populate_existing=True)
    )
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError(f"No income entry with id {entry_id}")
    return entry


async def update_entry(
    session: AsyncSession,
    entry_id: uuid.UUID,
    *,
    amount: Decimal | None = None,
    date: datetime.date | None = None,
    source_id: uuid.UUID | None = None,
    description: str | None = None,
) -> IncomeEntry:
    entry = await get_entry(session, entry_id)

    updates = {
        "amount": amount,
        "date": date,
        "source_id": source_id,
        "description": description,
    }
    changed_ledger_fields = False
    for field in _EDITABLE_FIELDS:
        new_value = updates[field]
        if new_value is None:
            continue
        old_value = getattr(entry, field)
        if old_value == new_value:
            continue
        if field == "amount" and new_value <= 0:
            raise ValidationError("amount must be greater than zero")
        if field == "source_id":
            source = await session.get(IncomeSource, new_value)
            if source is None:
                raise ValidationError("source_id does not reference an existing income source")

        setattr(entry, field, new_value)
        if field in _LEDGER_AFFECTING_FIELDS:
            changed_ledger_fields = True

    await session.commit()

    if changed_ledger_fields:
        await ledger_service.reverse_journal_entry_for_income(session, entry.id)
        await session.refresh(entry, attribute_names=["source"])
        await ledger_service.post_income_journal_entry(session, entry)

    return await get_entry(session, entry_id)


async def delete_entry(session: AsyncSession, entry_id: uuid.UUID) -> None:
    entry = await get_entry(session, entry_id)
    await ledger_service.reverse_journal_entry_for_income(session, entry_id)
    await session.delete(entry)
    await session.commit()
