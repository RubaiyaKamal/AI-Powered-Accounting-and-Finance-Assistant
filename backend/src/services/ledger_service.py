import datetime
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.ledger_tools import suggest_account_coding
from src.config import ACCOUNT_CODING_CONFIDENCE_THRESHOLD
from src.models.account import Account
from src.models.account_coding import AccountCoding
from src.models.expense_entry import ExpenseEntry
from src.models.journal_entry import JournalEntry

OFFSET_ACCOUNT_NAME = "Cash"


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    pass


def _coding_load_options():
    return (
        selectinload(AccountCoding.account),
        selectinload(AccountCoding.journal_entries).selectinload(JournalEntry.debit_account),
        selectinload(AccountCoding.journal_entries).selectinload(JournalEntry.credit_account),
    )


async def _get_offset_account(session: AsyncSession) -> Account:
    result = await session.execute(select(Account).where(Account.name == OFFSET_ACCOUNT_NAME))
    account = result.scalar_one_or_none()
    if account is None:
        raise ValidationError(f"Offset account '{OFFSET_ACCOUNT_NAME}' is not configured")
    return account


def active_journal_entry(coding: AccountCoding) -> JournalEntry | None:
    # A reversal entry is itself status="posted" (it's a real, completed
    # transaction) — only an original, un-reversed posting (no
    # reverses_journal_entry_id) represents the coding's current active
    # entry. Without this, a second correction could mistakenly reverse the
    # prior correction's reversal entry instead of the real active posting.
    return next(
        (
            je
            for je in coding.journal_entries
            if je.status == "posted" and je.reverses_journal_entry_id is None
        ),
        None,
    )


async def get_coding(session: AsyncSession, expense_entry_id: uuid.UUID) -> AccountCoding:
    # populate_existing=True: callers that mutate a coding's account_id or its
    # journal entries earlier in the same session must see those changes here
    # too — selectinload alone skips relationships that are already loaded in
    # the identity map, which would otherwise return stale account/journal
    # data after suggest_coding/approve_coding/correct_coding's own writes.
    stmt = (
        select(AccountCoding)
        .where(AccountCoding.expense_entry_id == expense_entry_id)
        .options(*_coding_load_options())
        .execution_options(populate_existing=True)
    )
    result = await session.execute(stmt)
    coding = result.scalar_one_or_none()
    if coding is None:
        raise NotFoundError(f"No account coding exists yet for expense entry {expense_entry_id}")
    return coding


async def post_journal_entry(
    session: AsyncSession, coding: AccountCoding, expense_entry: ExpenseEntry
) -> JournalEntry:
    offset_account = await _get_offset_account(session)
    if coding.account_id == offset_account.id:
        raise ValidationError(
            "Cannot post a journal entry where the debit and credit accounts are the same"
        )

    entry = JournalEntry(
        expense_entry_id=expense_entry.id,
        account_coding_id=coding.id,
        debit_account_id=coding.account_id,
        credit_account_id=offset_account.id,
        amount=expense_entry.amount,
        date=expense_entry.date,
        status="posted",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry, attribute_names=["debit_account", "credit_account"])
    return entry


async def reverse_journal_entry(session: AsyncSession, entry: JournalEntry) -> JournalEntry:
    reversal = JournalEntry(
        expense_entry_id=entry.expense_entry_id,
        account_coding_id=entry.account_coding_id,
        debit_account_id=entry.credit_account_id,
        credit_account_id=entry.debit_account_id,
        amount=entry.amount,
        date=entry.date,
        status="posted",
        reverses_journal_entry_id=entry.id,
    )
    entry.status = "reversed"
    session.add(reversal)
    await session.commit()
    await session.refresh(reversal, attribute_names=["debit_account", "credit_account"])
    return reversal


async def suggest_coding(session: AsyncSession, expense_entry_id: uuid.UUID) -> AccountCoding:
    expense_entry = await session.get(ExpenseEntry, expense_entry_id)
    if expense_entry is None:
        raise NotFoundError(f"No expense entry with id {expense_entry_id}")

    existing = await session.execute(
        select(AccountCoding).where(AccountCoding.expense_entry_id == expense_entry_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            "This expense entry already has a coding; use PATCH .../coding to change it"
        )

    accounts = list((await session.execute(select(Account))).scalars().all())
    account_name, confidence = await suggest_account_coding(
        expense_entry.description or "", accounts
    )
    account = next((a for a in accounts if a.name == account_name), None)
    if account is None:
        raise ValidationError("No matching account could be resolved for this expense entry")

    status = (
        "approved"
        if confidence >= Decimal(str(ACCOUNT_CODING_CONFIDENCE_THRESHOLD))
        else "pending_review"
    )
    coding = AccountCoding(
        expense_entry_id=expense_entry.id,
        account_id=account.id,
        confidence_score=confidence,
        source="ai_suggested",
        status=status,
    )
    session.add(coding)
    await session.commit()

    if status == "approved":
        await post_journal_entry(session, coding, expense_entry)

    return await get_coding(session, expense_entry_id)


async def approve_coding(session: AsyncSession, expense_entry_id: uuid.UUID) -> AccountCoding:
    coding = await get_coding(session, expense_entry_id)
    if coding.status == "approved":
        raise ConflictError("This coding is already approved")

    expense_entry = await session.get(ExpenseEntry, expense_entry_id)
    if expense_entry is None:
        raise NotFoundError(f"No expense entry with id {expense_entry_id}")

    coding.status = "approved"
    await session.commit()

    await post_journal_entry(session, coding, expense_entry)
    return await get_coding(session, expense_entry_id)


async def correct_coding(
    session: AsyncSession, expense_entry_id: uuid.UUID, account_id: uuid.UUID
) -> AccountCoding:
    coding = await get_coding(session, expense_entry_id)
    account = await session.get(Account, account_id)
    if account is None:
        raise ValidationError("account_id does not reference an existing account")

    expense_entry = await session.get(ExpenseEntry, expense_entry_id)
    if expense_entry is None:
        raise NotFoundError(f"No expense entry with id {expense_entry_id}")

    entry_to_reverse = active_journal_entry(coding)

    coding.account_id = account.id
    coding.source = "user"
    coding.status = "approved"
    coding.confidence_score = None
    await session.commit()

    if entry_to_reverse is not None:
        await reverse_journal_entry(session, entry_to_reverse)
    await post_journal_entry(session, coding, expense_entry)
    return await get_coding(session, expense_entry_id)


async def reverse_journal_entry_for_expense(
    session: AsyncSession, expense_entry_id: uuid.UUID
) -> None:
    """Reverse the posted journal entry (if any) for an expense entry about to be deleted.

    See FR-012.
    """
    stmt = (
        select(AccountCoding)
        .where(AccountCoding.expense_entry_id == expense_entry_id)
        .options(selectinload(AccountCoding.journal_entries))
    )
    coding = (await session.execute(stmt)).scalar_one_or_none()
    if coding is None:
        return
    active_entry = active_journal_entry(coding)
    if active_entry is not None:
        await reverse_journal_entry(session, active_entry)


async def get_journal_entry(session: AsyncSession, journal_entry_id: uuid.UUID) -> JournalEntry:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.id == journal_entry_id)
        .options(
            selectinload(JournalEntry.debit_account), selectinload(JournalEntry.credit_account)
        )
    )
    entry = (await session.execute(stmt)).scalar_one_or_none()
    if entry is None:
        raise NotFoundError(f"No journal entry with id {journal_entry_id}")
    return entry


async def list_journal_entries(
    session: AsyncSession,
    *,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    account_id: uuid.UUID | None = None,
) -> list[JournalEntry]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValidationError("date_from must not be after date_to")

    stmt = select(JournalEntry).options(
        selectinload(JournalEntry.debit_account), selectinload(JournalEntry.credit_account)
    )
    if date_from is not None:
        stmt = stmt.where(JournalEntry.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(JournalEntry.date <= date_to)
    if account_id is not None:
        stmt = stmt.where(
            (JournalEntry.debit_account_id == account_id)
            | (JournalEntry.credit_account_id == account_id)
        )
    stmt = stmt.order_by(JournalEntry.date.desc(), JournalEntry.created_at.desc())

    result = await session.execute(stmt)
    return list(result.scalars().all())
