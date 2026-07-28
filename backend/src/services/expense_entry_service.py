import datetime
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.category import Category
from src.models.expense_entry import ExpenseEntry
from src.models.expense_entry_edit_history import ExpenseEntryEditHistory


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidDateRangeError(Exception):
    pass


async def _resolve_category(
    session: AsyncSession,
    category_id: uuid.UUID | None,
    category_name_hint: str | None,
) -> tuple[Category, str]:
    """Resolve the category for a new entry.

    Returns (category, category_source). If category_id is given, the entry
    is user-categorized. Otherwise this falls back to an AI suggestion
    (FR-010), added in US4's suggest_category tool; until then an explicit
    category_id is required (see tasks.md T018 note).
    """
    if category_id is not None:
        category = await session.get(Category, category_id)
        if category is None:
            raise ValidationError("category_id does not reference an existing category")
        return category, "user"

    from src.agent.expense_tools import suggest_category  # local import avoids agent/db cycle

    categories = (await session.execute(select(Category))).scalars().all()
    suggested_name = await suggest_category(category_name_hint or "", categories)
    category = next((c for c in categories if c.name == suggested_name), None)
    if category is None:
        raise ValidationError(
            "No category specified and none could be suggested; provide category_id"
        )
    return category, "ai_suggested"


async def create_entry(
    session: AsyncSession,
    *,
    amount: Decimal,
    date: datetime.date,
    category_id: uuid.UUID | None,
    category_name_hint: str | None,
    description: str | None,
    source: str,
) -> ExpenseEntry:
    if amount <= 0:
        raise ValidationError("amount must be greater than zero")

    category, category_source = await _resolve_category(session, category_id, category_name_hint)

    entry = ExpenseEntry(
        amount=amount,
        date=date,
        category_id=category.id,
        category_source=category_source,
        description=description,
        source=source,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry, attribute_names=["category"])
    return entry


async def list_entries(
    session: AsyncSession,
    *,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    category_id: uuid.UUID | None = None,
) -> list[ExpenseEntry]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidDateRangeError("date_from must not be after date_to")

    stmt = select(ExpenseEntry).options(selectinload(ExpenseEntry.category))
    if date_from is not None:
        stmt = stmt.where(ExpenseEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(ExpenseEntry.date <= date_to)
    if category_id is not None:
        stmt = stmt.where(ExpenseEntry.category_id == category_id)
    stmt = stmt.order_by(ExpenseEntry.date.desc(), ExpenseEntry.created_at.desc())

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_entry(session: AsyncSession, entry_id: uuid.UUID) -> ExpenseEntry:
    stmt = (
        select(ExpenseEntry)
        .where(ExpenseEntry.id == entry_id)
        .options(selectinload(ExpenseEntry.category), selectinload(ExpenseEntry.edit_history))
    )
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError(f"No expense entry with id {entry_id}")
    return entry


_EDITABLE_FIELDS = ("amount", "date", "category_id", "description")


async def update_entry(
    session: AsyncSession,
    entry_id: uuid.UUID,
    *,
    amount: Decimal | None = None,
    date: datetime.date | None = None,
    category_id: uuid.UUID | None = None,
    description: str | None = None,
) -> ExpenseEntry:
    entry = await get_entry(session, entry_id)

    updates = {
        "amount": amount,
        "date": date,
        "category_id": category_id,
        "description": description,
    }
    for field in _EDITABLE_FIELDS:
        new_value = updates[field]
        if new_value is None:
            continue
        old_value = getattr(entry, field)
        if old_value == new_value:
            continue
        if field == "amount" and new_value <= 0:
            raise ValidationError("amount must be greater than zero")
        if field == "category_id":
            category = await session.get(Category, new_value)
            if category is None:
                raise ValidationError("category_id does not reference an existing category")
            entry.category_source = "user"

        session.add(
            ExpenseEntryEditHistory(
                expense_entry_id=entry.id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
            )
        )
        setattr(entry, field, new_value)

    await session.commit()
    await session.refresh(entry)
    await session.refresh(entry, attribute_names=["category", "edit_history"])
    return entry


async def delete_entry(session: AsyncSession, entry_id: uuid.UUID) -> None:
    entry = await get_entry(session, entry_id)
    await session.delete(entry)
    await session.commit()
