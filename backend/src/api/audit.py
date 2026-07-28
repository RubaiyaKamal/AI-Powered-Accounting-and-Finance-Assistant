import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.audit import (
    AnomalyFlagResponse,
    AuditRunListResponse,
    AuditRunResponse,
    AuditRunSummary,
    AuditRunTriggerRequest,
    ResolveFlagRequest,
)
from src.services import audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.post("/runs", response_model=AuditRunResponse, status_code=201)
async def trigger_audit_run(
    payload: AuditRunTriggerRequest = AuditRunTriggerRequest(),
    session: AsyncSession = Depends(get_session),
) -> AuditRunResponse:
    try:
        run = await audit_service.run_audit(session, payload.start, payload.end)
    except audit_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AuditRunResponse.model_validate(run)


@router.get("/runs", response_model=AuditRunListResponse)
async def list_audit_runs(session: AsyncSession = Depends(get_session)) -> AuditRunListResponse:
    runs = await audit_service.list_audit_runs(session)
    items = [AuditRunSummary.model_validate(run) for run in runs]
    return AuditRunListResponse(items=items, total=len(items))


@router.get("/runs/{run_id}", response_model=AuditRunResponse)
async def get_audit_run(
    run_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> AuditRunResponse:
    try:
        run = await audit_service.get_audit_run(session, run_id)
    except audit_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuditRunResponse.model_validate(run)


@router.patch("/flags/{flag_id}", response_model=AnomalyFlagResponse)
async def resolve_flag(
    flag_id: uuid.UUID,
    payload: ResolveFlagRequest,
    session: AsyncSession = Depends(get_session),
) -> AnomalyFlagResponse:
    try:
        flag = await audit_service.resolve_flag(session, flag_id, payload.resolution)
    except audit_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnomalyFlagResponse.model_validate(flag)
