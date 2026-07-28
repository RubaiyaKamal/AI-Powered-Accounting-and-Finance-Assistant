import datetime
import statistics
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import TypedDict

import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.audit_tools import explain_flags
from src.models.anomaly_flag import AnomalyFlag
from src.models.audit_run import AuditRun
from src.models.journal_entry import JournalEntry

MIN_ENTRIES_FOR_DETECTION = 20
ML_CONTAMINATION = 0.1  # caps the model's own share of flags at 10% (FR-005, SC-003)
RANDOM_SEED = 42  # fixed seed — detection is reproducible given the same data (research.md)

ROUND_NUMBER_UNIT = 100


class RawFlag(TypedDict):
    entry: JournalEntry
    score: float
    reason_categories: list[str]


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
    flag (research.md, FR-010). Defaults to the whole ledger to date
    (earliest active posting through today — `contracts/audit-api.md`)
    when no range is given.
    """
    if start is not None and end is not None and end < start:
        raise ValidationError("end must not be before start")

    active_filters = [
        JournalEntry.status == "posted",
        JournalEntry.reverses_journal_entry_id.is_(None),
    ]

    resolved_start = start
    if resolved_start is None:
        earliest_stmt = select(func.min(JournalEntry.date)).where(*active_filters)
        earliest = (await session.execute(earliest_stmt)).scalar_one_or_none()
        resolved_start = earliest or datetime.date.today()
    resolved_end = end if end is not None else datetime.date.today()

    stmt = (
        select(JournalEntry)
        .where(
            *active_filters,
            JournalEntry.date >= resolved_start,
            JournalEntry.date <= resolved_end,
        )
        .options(
            selectinload(JournalEntry.debit_account), selectinload(JournalEntry.credit_account)
        )
        .order_by(JournalEntry.date)
    )
    entries = list((await session.execute(stmt)).scalars().all())

    return resolved_start, resolved_end, entries


def _build_features(entries: list[JournalEntry]) -> np.ndarray:
    """Numeric feature vector per entry: amount, day-of-week, day-of-month,
    and a one-hot encoded debit/credit account pair (research.md)."""
    pairs = [f"{e.debit_account_id}:{e.credit_account_id}" for e in entries]
    unique_pairs = sorted(set(pairs))
    pair_index = {pair: i for i, pair in enumerate(unique_pairs)}

    rows = []
    for entry, pair in zip(entries, pairs, strict=True):
        one_hot = [0.0] * len(unique_pairs)
        one_hot[pair_index[pair]] = 1.0
        rows.append(
            [float(entry.amount), float(entry.date.weekday()), float(entry.date.day), *one_hot]
        )
    return np.array(rows)


def _reason_categories_for_ml_flag(
    entry: JournalEntry, entries: list[JournalEntry], pair_counts: dict[tuple, int]
) -> list[str]:
    """Best-effort decomposition of *why* the model flagged this entry, so
    the explanation isn't just "the model said so" (FR-004)."""
    categories = []

    same_account_amounts = [
        float(e.amount) for e in entries if e.debit_account_id == entry.debit_account_id
    ]
    mean = statistics.fmean(same_account_amounts)
    stdev = statistics.pstdev(same_account_amounts) if len(same_account_amounts) > 1 else 0.0
    if (stdev > 0 and abs(float(entry.amount) - mean) > 2 * stdev) or (
        stdev == 0 and float(entry.amount) != mean
    ):
        categories.append("unusual_amount")

    pair_key = (entry.debit_account_id, entry.credit_account_id)
    if pair_counts[pair_key] <= 1:
        categories.append("unusual_account_pairing")

    if entry.date.weekday() >= 5:
        weekend_ratio = sum(1 for e in entries if e.date.weekday() >= 5) / len(entries)
        if weekend_ratio < 0.1:
            categories.append("unusual_timing")

    return categories or ["unusual_amount"]


def _detect(entries: list[JournalEntry]) -> list[RawFlag]:
    """Hybrid detection: IsolationForest outlier scoring plus deterministic
    duplicate/round-number rule checks, merged into one ranked flag list.

    Every flag, its score, and its reason categories come entirely from
    this function — nothing here is decided or altered by the AI layer
    (constitution Principle II, extended — research.md).
    """
    features = _build_features(entries)
    model = IsolationForest(random_state=RANDOM_SEED, contamination=ML_CONTAMINATION)
    model.fit(features)
    predictions = model.predict(features)  # 1 = inlier, -1 = outlier
    raw_scores = model.decision_function(features)  # higher = more normal
    scores = [round(-s, 4) for s in raw_scores]  # negate: higher = more anomalous

    duplicate_groups: dict[tuple, list[int]] = defaultdict(list)
    pair_counts: dict[tuple, int] = defaultdict(int)
    for i, entry in enumerate(entries):
        dup_key = (entry.amount, entry.date, entry.debit_account_id, entry.credit_account_id)
        duplicate_groups[dup_key].append(i)
        pair_counts[(entry.debit_account_id, entry.credit_account_id)] += 1

    flags: list[RawFlag] = []
    for i, entry in enumerate(entries):
        categories: list[str] = []
        if predictions[i] == -1:
            categories.extend(_reason_categories_for_ml_flag(entry, entries, pair_counts))

        dup_key = (entry.amount, entry.date, entry.debit_account_id, entry.credit_account_id)
        if len(duplicate_groups[dup_key]) > 1:
            categories.append("duplicate_looking")

        if entry.amount >= ROUND_NUMBER_UNIT and entry.amount % ROUND_NUMBER_UNIT == 0:
            categories.append("round_number")

        if not categories:
            continue

        deduped = list(dict.fromkeys(categories))
        flags.append(RawFlag(entry=entry, score=scores[i], reason_categories=deduped))

    flags.sort(key=lambda f: f["score"], reverse=True)
    return flags


def _run_load_options():
    return (
        selectinload(AuditRun.flags)
        .selectinload(AnomalyFlag.journal_entry)
        .selectinload(JournalEntry.debit_account),
        selectinload(AuditRun.flags)
        .selectinload(AnomalyFlag.journal_entry)
        .selectinload(JournalEntry.credit_account),
    )


async def _get_run(session: AsyncSession, run_id: uuid.UUID) -> AuditRun:
    stmt = select(AuditRun).where(AuditRun.id == run_id).options(*_run_load_options())
    run = (await session.execute(stmt)).scalar_one_or_none()
    if run is None:
        raise NotFoundError(f"No audit run with id {run_id}")
    return run


async def run_audit(
    session: AsyncSession, start: datetime.date | None, end: datetime.date | None
) -> AuditRun:
    resolved_start, resolved_end, entries = await _evaluate_entries(session, start, end)

    if len(entries) < MIN_ENTRIES_FOR_DETECTION:
        run = AuditRun(
            start=resolved_start,
            end=resolved_end,
            entries_evaluated=len(entries),
            entries_flagged=0,
            status="insufficient_data",
        )
        session.add(run)
        await session.commit()
        return await _get_run(session, run.id)

    raw_flags = _detect(entries)

    flag_summaries = [
        {
            "amount": str(flag["entry"].amount),
            "date": flag["entry"].date.isoformat(),
            "debit_account": flag["entry"].debit_account.name,
            "credit_account": flag["entry"].credit_account.name,
            "reason_categories": flag["reason_categories"],
        }
        for flag in raw_flags
    ]
    explanations = await explain_flags(flag_summaries)

    run = AuditRun(
        start=resolved_start,
        end=resolved_end,
        entries_evaluated=len(entries),
        entries_flagged=len(raw_flags),
        status="completed",
    )
    session.add(run)
    await session.flush()

    for raw_flag, explanation in zip(raw_flags, explanations, strict=True):
        session.add(
            AnomalyFlag(
                audit_run_id=run.id,
                journal_entry_id=raw_flag["entry"].id,
                score=Decimal(str(raw_flag["score"])),
                reason_categories=raw_flag["reason_categories"],
                explanation=explanation,
            )
        )
    await session.commit()
    return await _get_run(session, run.id)


async def list_audit_runs(session: AsyncSession) -> list[AuditRun]:
    stmt = select(AuditRun).order_by(AuditRun.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_audit_run(session: AsyncSession, run_id: uuid.UUID) -> AuditRun:
    return await _get_run(session, run_id)


async def resolve_flag(session: AsyncSession, flag_id: uuid.UUID, resolution: str) -> AnomalyFlag:
    stmt = (
        select(AnomalyFlag)
        .where(AnomalyFlag.id == flag_id)
        .options(
            selectinload(AnomalyFlag.journal_entry).selectinload(JournalEntry.debit_account),
            selectinload(AnomalyFlag.journal_entry).selectinload(JournalEntry.credit_account),
        )
    )
    flag = (await session.execute(stmt)).scalar_one_or_none()
    if flag is None:
        raise NotFoundError(f"No anomaly flag with id {flag_id}")

    flag.resolution = resolution
    flag.resolved_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    return flag
