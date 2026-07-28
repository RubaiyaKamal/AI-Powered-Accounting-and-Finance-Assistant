from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.audit import AuditRunResponse, AuditRunTriggerRequest
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
