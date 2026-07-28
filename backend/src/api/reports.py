import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.reports import TrialBalanceResponse
from src.services import reporting_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    as_of: datetime.date | None = None, session: AsyncSession = Depends(get_session)
) -> TrialBalanceResponse:
    return await reporting_service.trial_balance(session, as_of)
