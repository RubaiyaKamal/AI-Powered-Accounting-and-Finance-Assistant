from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.account import AccountCreate, AccountListResponse, AccountRead
from src.services import account_service

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=AccountListResponse)
async def list_accounts(session: AsyncSession = Depends(get_session)) -> AccountListResponse:
    accounts = await account_service.list_accounts(session)
    return AccountListResponse(items=[AccountRead.model_validate(a) for a in accounts])


@router.post("", response_model=AccountRead, status_code=201)
async def create_account(
    payload: AccountCreate, session: AsyncSession = Depends(get_session)
) -> AccountRead:
    try:
        account = await account_service.create_account(
            session, payload.code, payload.name, payload.type
        )
    except account_service.DuplicateAccountError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AccountRead.model_validate(account)
