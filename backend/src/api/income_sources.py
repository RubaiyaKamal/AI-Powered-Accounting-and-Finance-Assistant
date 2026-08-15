from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.income_source import IncomeSourceCreate, IncomeSourceListResponse, IncomeSourceRead
from src.services import income_source_service

router = APIRouter(prefix="/api/income-sources", tags=["income"])


@router.get("", response_model=IncomeSourceListResponse)
async def list_income_sources(
    session: AsyncSession = Depends(get_session),
) -> IncomeSourceListResponse:
    sources = await income_source_service.list_sources(session)
    return IncomeSourceListResponse(items=[IncomeSourceRead.model_validate(s) for s in sources])


@router.post("", response_model=IncomeSourceRead, status_code=201)
async def create_income_source(
    payload: IncomeSourceCreate, session: AsyncSession = Depends(get_session)
) -> IncomeSourceRead:
    try:
        source = await income_source_service.create_source(
            session, payload.name, payload.account_type
        )
    except income_source_service.DuplicateSourceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return IncomeSourceRead.model_validate(source)
