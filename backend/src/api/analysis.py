import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.analysis import (
    SpendingBreakdownResponse,
    SpendingComparisonResponse,
    SpendingForecastResponse,
)
from src.services import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/breakdown", response_model=SpendingBreakdownResponse)
async def get_breakdown(
    start: datetime.date | None = None,
    end: datetime.date | None = None,
    session: AsyncSession = Depends(get_session),
) -> SpendingBreakdownResponse:
    return await analysis_service.breakdown(session, start, end)


@router.get("/comparison", response_model=SpendingComparisonResponse)
async def get_comparison(
    period_a_start: datetime.date,
    period_a_end: datetime.date,
    period_b_start: datetime.date,
    period_b_end: datetime.date,
    session: AsyncSession = Depends(get_session),
) -> SpendingComparisonResponse:
    try:
        return await analysis_service.comparison(
            session, period_a_start, period_a_end, period_b_start, period_b_end
        )
    except analysis_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/forecast", response_model=SpendingForecastResponse)
async def get_forecast(
    target_start: datetime.date,
    target_end: datetime.date,
    session: AsyncSession = Depends(get_session),
) -> SpendingForecastResponse:
    try:
        return await analysis_service.forecast(session, target_start, target_end)
    except analysis_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
