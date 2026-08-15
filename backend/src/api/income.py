import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.income_entry import (
    IncomeEntryCreate,
    IncomeEntryListResponse,
    IncomeEntryRead,
    IncomeEntryUpdate,
)
from src.services import income_entry_service as service

router = APIRouter(prefix="/api/income", tags=["income"])


@router.post("", response_model=IncomeEntryRead, status_code=201)
async def create_income(
    payload: IncomeEntryCreate, session: AsyncSession = Depends(get_session)
) -> IncomeEntryRead:
    try:
        entry = await service.create_entry(
            session,
            amount=payload.amount,
            date=payload.date,
            source_id=payload.source_id,
            description=payload.description,
        )
    except service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IncomeEntryRead.model_validate(entry)


@router.get("", response_model=IncomeEntryListResponse)
async def list_income(
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    source_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> IncomeEntryListResponse:
    try:
        entries = await service.list_entries(
            session, date_from=date_from, date_to=date_to, source_id=source_id
        )
    except service.InvalidDateRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    items = [IncomeEntryRead.model_validate(e) for e in entries]
    return IncomeEntryListResponse(items=items, total=len(items))


@router.get("/{entry_id}", response_model=IncomeEntryRead)
async def get_income(
    entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> IncomeEntryRead:
    try:
        entry = await service.get_entry(session, entry_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return IncomeEntryRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=IncomeEntryRead)
async def update_income(
    entry_id: uuid.UUID,
    payload: IncomeEntryUpdate,
    session: AsyncSession = Depends(get_session),
) -> IncomeEntryRead:
    try:
        entry = await service.update_entry(
            session,
            entry_id,
            amount=payload.amount,
            date=payload.date,
            source_id=payload.source_id,
            description=payload.description,
        )
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IncomeEntryRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
async def delete_income(
    entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    try:
        await service.delete_entry(session, entry_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
