import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.reports import BalanceSheetResponse, ProfitAndLossResponse, TrialBalanceResponse
from src.services import reporting_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    as_of: datetime.date | None = None, session: AsyncSession = Depends(get_session)
) -> TrialBalanceResponse:
    return await reporting_service.trial_balance(session, as_of)


@router.get("/profit-and-loss", response_model=ProfitAndLossResponse)
async def get_profit_and_loss(
    start: datetime.date | None = None,
    end: datetime.date | None = None,
    session: AsyncSession = Depends(get_session),
) -> ProfitAndLossResponse:
    try:
        return await reporting_service.profit_and_loss(session, start, end)
    except reporting_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/balance-sheet", response_model=BalanceSheetResponse)
async def get_balance_sheet(
    as_of: datetime.date | None = None, session: AsyncSession = Depends(get_session)
) -> BalanceSheetResponse:
    return await reporting_service.balance_sheet(session, as_of)
