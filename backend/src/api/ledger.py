import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.account_coding import AccountCodingCorrect, AccountCodingWithJournalEntry
from src.schemas.journal_entry import JournalEntryListResponse, JournalEntryRead
from src.services import ledger_service

router = APIRouter(tags=["ledger"])


def _coding_response(coding) -> AccountCodingWithJournalEntry:
    journal_entry = ledger_service.active_journal_entry(coding)
    return AccountCodingWithJournalEntry(
        coding=coding,
        journal_entry=journal_entry,
    )


@router.post(
    "/api/expenses/{expense_id}/coding/suggest", response_model=AccountCodingWithJournalEntry
)
async def suggest_coding(
    expense_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AccountCodingWithJournalEntry:
    try:
        coding = await ledger_service.suggest_coding(session, expense_id)
    except ledger_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ledger_service.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ledger_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _coding_response(coding)


@router.get("/api/expenses/{expense_id}/coding", response_model=AccountCodingWithJournalEntry)
async def get_coding(
    expense_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AccountCodingWithJournalEntry:
    try:
        coding = await ledger_service.get_coding(session, expense_id)
    except ledger_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _coding_response(coding)


@router.post(
    "/api/expenses/{expense_id}/coding/approve", response_model=AccountCodingWithJournalEntry
)
async def approve_coding(
    expense_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AccountCodingWithJournalEntry:
    try:
        coding = await ledger_service.approve_coding(session, expense_id)
    except ledger_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ledger_service.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _coding_response(coding)


@router.patch("/api/expenses/{expense_id}/coding", response_model=AccountCodingWithJournalEntry)
async def correct_coding(
    expense_id: uuid.UUID,
    payload: AccountCodingCorrect,
    session: AsyncSession = Depends(get_session),
) -> AccountCodingWithJournalEntry:
    try:
        coding = await ledger_service.correct_coding(session, expense_id, payload.account_id)
    except ledger_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ledger_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _coding_response(coding)


@router.get("/api/journal-entries", response_model=JournalEntryListResponse)
async def list_journal_entries(
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    account_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> JournalEntryListResponse:
    try:
        entries = await ledger_service.list_journal_entries(
            session, date_from=date_from, date_to=date_to, account_id=account_id
        )
    except ledger_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    items = [JournalEntryRead.model_validate(e) for e in entries]
    return JournalEntryListResponse(items=items, total=len(items))


@router.get("/api/journal-entries/{entry_id}", response_model=JournalEntryRead)
async def get_journal_entry(
    entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> JournalEntryRead:
    try:
        entry = await ledger_service.get_journal_entry(session, entry_id)
    except ledger_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JournalEntryRead.model_validate(entry)
