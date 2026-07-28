import csv
import datetime
import io
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

from rapidfuzz import fuzz
from rapidfuzz import utils as fuzz_utils
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.reconciliation_tools import adjudicate_match
from src.models.bank_transaction import BankTransaction
from src.models.expense_entry import ExpenseEntry
from src.models.match import Match

DATE_WINDOW_DAYS = 5
AUTO_MATCH_THRESHOLD = 90.0
AMBIGUOUS_THRESHOLD = 60.0
AUTO_MATCH_MARGIN = 15.0
MAX_AMBIGUOUS_CANDIDATES = 5


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ValidationError(Exception):
    pass


@dataclass
class ParsedRow:
    date: datetime.date
    amount: Decimal
    description: str


@dataclass
class InvalidRow:
    row: int
    reason: str


@dataclass
class ParseResult:
    valid: list[ParsedRow]
    invalid: list[InvalidRow]


def parse_csv(content: bytes) -> ParseResult:
    """Parse a bank statement CSV (date/amount/description columns, case-insensitive).

    Raises ValidationError if the file isn't a usable CSV at all (no
    header row, or missing a required column). A malformed individual row
    is skipped and reported, not a file-level failure (spec Edge Cases).
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValidationError("The uploaded file has no header row")

    field_map = {name.strip().lower(): name for name in reader.fieldnames}
    required = ["date", "amount", "description"]
    missing = [f for f in required if f not in field_map]
    if missing:
        raise ValidationError(f"Missing required column(s): {', '.join(missing)}")

    valid: list[ParsedRow] = []
    invalid: list[InvalidRow] = []
    for i, row in enumerate(reader, start=2):  # header is row 1
        raw_date = (row.get(field_map["date"]) or "").strip()
        raw_amount = (row.get(field_map["amount"]) or "").strip()
        raw_description = (row.get(field_map["description"]) or "").strip()

        try:
            parsed_date = datetime.date.fromisoformat(raw_date)
        except ValueError:
            invalid.append(InvalidRow(row=i, reason="unparseable date"))
            continue
        try:
            parsed_amount = Decimal(raw_amount.replace(",", ""))
        except InvalidOperation:
            invalid.append(InvalidRow(row=i, reason="unparseable amount"))
            continue
        if not raw_description:
            invalid.append(InvalidRow(row=i, reason="missing description"))
            continue

        valid.append(
            ParsedRow(date=parsed_date, amount=parsed_amount, description=raw_description)
        )

    return ParseResult(valid=valid, invalid=invalid)


async def import_transactions(
    session: AsyncSession, rows: list[ParsedRow]
) -> tuple[list[BankTransaction], int]:
    """Insert parsed rows as BankTransaction rows, skipping exact duplicates (FR-003)."""
    inserted: list[BankTransaction] = []
    duplicates = 0
    for row in rows:
        existing = await session.execute(
            select(BankTransaction).where(
                BankTransaction.date == row.date,
                BankTransaction.amount == row.amount,
                BankTransaction.description == row.description,
            )
        )
        if existing.scalar_one_or_none() is not None:
            duplicates += 1
            continue
        txn = BankTransaction(date=row.date, amount=row.amount, description=row.description)
        session.add(txn)
        inserted.append(txn)

    await session.commit()
    for txn in inserted:
        await session.refresh(txn)
    return inserted, duplicates


@dataclass
class Candidate:
    expense_entry: ExpenseEntry
    score: float


async def score_candidates(
    session: AsyncSession, transaction: BankTransaction
) -> list[Candidate]:
    """Amount-exact, date-windowed candidates, scored by description similarity."""
    window_start = transaction.date - datetime.timedelta(days=DATE_WINDOW_DAYS)
    window_end = transaction.date + datetime.timedelta(days=DATE_WINDOW_DAYS)
    result = await session.execute(
        select(ExpenseEntry).where(
            ExpenseEntry.amount == transaction.amount,
            ExpenseEntry.date >= window_start,
            ExpenseEntry.date <= window_end,
        )
    )
    entries = list(result.scalars().all())
    if not entries:
        return []

    already_matched = await session.execute(
        select(Match.expense_entry_id).where(
            Match.expense_entry_id.in_([e.id for e in entries])
        )
    )
    matched_ids = {row[0] for row in already_matched.all()}
    entries = [e for e in entries if e.id not in matched_ids]

    candidates: list[Candidate] = []
    for entry in entries:
        # token_set_ratio (not token_sort_ratio): bank statement descriptions
        # are typically terser/abbreviated versions of the fuller expense
        # description (e.g. "WIFI CHARGES JULY" vs "Wi-fi charges for the
        # month July") — token_set_ratio scores a token-subset relationship
        # highly, where token_sort_ratio penalizes the extra words as if
        # they were a mismatch (found via live testing).
        description_score = fuzz.token_set_ratio(
            transaction.description, entry.description or "", processor=fuzz_utils.default_process
        )
        date_diff = abs((entry.date - transaction.date).days)
        date_score = max(0.0, 100.0 - date_diff * (100.0 / (DATE_WINDOW_DAYS + 1)))
        composite = description_score * 0.7 + date_score * 0.3
        candidates.append(Candidate(expense_entry=entry, score=composite))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


class MatchClassification(Enum):
    AUTO = "auto"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


def classify_match(candidates: list[Candidate]) -> MatchClassification:
    """Auto/ambiguous/none per research.md's Matching Thresholds decision."""
    if not candidates:
        return MatchClassification.NONE

    top = candidates[0]
    if top.score < AMBIGUOUS_THRESHOLD:
        return MatchClassification.NONE

    if top.score >= AUTO_MATCH_THRESHOLD:
        runner_up = candidates[1].score if len(candidates) > 1 else 0.0
        if top.score - runner_up >= AUTO_MATCH_MARGIN:
            return MatchClassification.AUTO

    return MatchClassification.AMBIGUOUS


async def run_matching_for_transaction(session: AsyncSession, transaction: BankTransaction) -> str:
    """Classify and resolve (or flag) one bank transaction.

    Returns "auto_matched" or "needs_review".
    """
    candidates = await score_candidates(session, transaction)
    classification = classify_match(candidates)

    if classification == MatchClassification.AUTO:
        match = Match(
            bank_transaction_id=transaction.id,
            expense_entry_id=candidates[0].expense_entry.id,
            source="auto",
            status="confirmed",
            ai_reasoning=None,
        )
        session.add(match)
        await session.commit()
        return "auto_matched"

    if classification == MatchClassification.AMBIGUOUS:
        ambiguous = [c for c in candidates if c.score >= AMBIGUOUS_THRESHOLD]
        ambiguous = ambiguous[:MAX_AMBIGUOUS_CANDIDATES]
        chosen_id, reasoning = await adjudicate_match(
            transaction, [c.expense_entry for c in ambiguous]
        )
        transaction.suggested_expense_entry_id = chosen_id
        transaction.ai_reasoning = reasoning
        await session.commit()
        return "needs_review"

    return "needs_review"


async def list_bank_transactions(
    session: AsyncSession, status: str | None = None
) -> list[BankTransaction]:
    stmt = (
        select(BankTransaction)
        .options(selectinload(BankTransaction.match))
        .order_by(BankTransaction.date.desc(), BankTransaction.created_at.desc())
    )
    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    if status == "matched":
        return [t for t in transactions if t.match is not None and t.match.status == "confirmed"]
    if status == "unmatched":
        return [t for t in transactions if t.match is None]
    if status == "dismissed":
        return [t for t in transactions if t.match is not None and t.match.status == "dismissed"]
    return transactions


@dataclass
class ReviewQueueItem:
    bank_transaction: BankTransaction
    suggested_expense_entry: ExpenseEntry | None
    ai_reasoning: str | None
    candidates_considered: list[ExpenseEntry] | None


async def list_review_queue(session: AsyncSession) -> list[ReviewQueueItem]:
    """Unmatched bank transactions (no Match row yet) — ambiguous ones show their AI suggestion."""
    stmt = (
        select(BankTransaction)
        .outerjoin(Match, Match.bank_transaction_id == BankTransaction.id)
        .where(Match.id.is_(None))
        .order_by(BankTransaction.date.desc())
    )
    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    items: list[ReviewQueueItem] = []
    for txn in transactions:
        suggested = None
        if txn.suggested_expense_entry_id is not None:
            suggested = await session.get(ExpenseEntry, txn.suggested_expense_entry_id)
        candidates = await score_candidates(session, txn)
        candidate_entries = [c.expense_entry for c in candidates] if candidates else None
        items.append(
            ReviewQueueItem(
                bank_transaction=txn,
                suggested_expense_entry=suggested,
                ai_reasoning=txn.ai_reasoning,
                candidates_considered=candidate_entries,
            )
        )
    return items


async def _get_transaction(session: AsyncSession, transaction_id: uuid.UUID) -> BankTransaction:
    txn = await session.get(BankTransaction, transaction_id)
    if txn is None:
        raise NotFoundError(f"No bank transaction with id {transaction_id}")
    return txn


async def _existing_match(session: AsyncSession, transaction_id: uuid.UUID) -> Match | None:
    result = await session.execute(
        select(Match).where(Match.bank_transaction_id == transaction_id)
    )
    return result.scalar_one_or_none()


async def confirm_match(
    session: AsyncSession, transaction_id: uuid.UUID, expense_entry_id: uuid.UUID
) -> Match:
    txn = await _get_transaction(session, transaction_id)
    if await _existing_match(session, transaction_id) is not None:
        raise ConflictError("This bank transaction is already resolved")

    expense_entry = await session.get(ExpenseEntry, expense_entry_id)
    if expense_entry is None:
        raise NotFoundError(f"No expense entry with id {expense_entry_id}")

    already_matched = await session.execute(
        select(Match).where(Match.expense_entry_id == expense_entry_id)
    )
    if already_matched.scalar_one_or_none() is not None:
        raise ConflictError("This expense entry is already matched to a different bank transaction")

    match = Match(
        bank_transaction_id=txn.id,
        expense_entry_id=expense_entry_id,
        source="manual",
        status="confirmed",
        ai_reasoning=None,
    )
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def dismiss_transaction(session: AsyncSession, transaction_id: uuid.UUID) -> Match:
    txn = await _get_transaction(session, transaction_id)
    if await _existing_match(session, transaction_id) is not None:
        raise ConflictError("This bank transaction is already resolved")

    match = Match(
        bank_transaction_id=txn.id,
        expense_entry_id=None,
        source="manual",
        status="dismissed",
        ai_reasoning=None,
    )
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


async def undo_match(session: AsyncSession, match_id: uuid.UUID) -> None:
    match = await session.get(Match, match_id)
    if match is None or match.status != "confirmed":
        raise NotFoundError(f"No confirmed match with id {match_id}")
    await session.delete(match)
    await session.commit()
