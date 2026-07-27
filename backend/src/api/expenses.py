import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.expense_entry import (
    ExpenseEntryCreate,
    ExpenseEntryDetailRead,
    ExpenseEntryListResponse,
    ExpenseEntryRead,
    ExpenseEntryUpdate,
)
from src.services import expense_entry_service as service

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseEntryRead, status_code=201)
async def create_expense(
    payload: ExpenseEntryCreate, session: AsyncSession = Depends(get_session)
) -> ExpenseEntryRead:
    try:
        entry = await service.create_entry(
            session,
            amount=payload.amount,
            date=payload.date,
            category_id=payload.category_id,
            category_name_hint=payload.category_name_hint,
            description=payload.description,
            source=payload.source,
        )
    except service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExpenseEntryRead.model_validate(entry)


@router.get("", response_model=ExpenseEntryListResponse)
async def list_expenses(
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    category_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> ExpenseEntryListResponse:
    try:
        entries = await service.list_entries(
            session, date_from=date_from, date_to=date_to, category_id=category_id
        )
    except service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    items = [ExpenseEntryRead.model_validate(e) for e in entries]
    return ExpenseEntryListResponse(items=items, total=len(items))


@router.get("/{entry_id}", response_model=ExpenseEntryDetailRead)
async def get_expense(
    entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ExpenseEntryDetailRead:
    try:
        entry = await service.get_entry(session, entry_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExpenseEntryDetailRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=ExpenseEntryRead)
async def update_expense(
    entry_id: uuid.UUID,
    payload: ExpenseEntryUpdate,
    session: AsyncSession = Depends(get_session),
) -> ExpenseEntryRead:
    try:
        entry = await service.update_entry(
            session,
            entry_id,
            amount=payload.amount,
            date=payload.date,
            category_id=payload.category_id,
            description=payload.description,
        )
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExpenseEntryRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
async def delete_expense(
    entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    try:
        await service.delete_entry(session, entry_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
