import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.expense_tools import parse_expense_draft, parse_receipt_image
from src.agent.reporting_tools import narrate_report, resolve_report_request
from src.config import RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES, RECEIPT_IMAGE_MAX_SIZE_BYTES
from src.db import get_session
from src.schemas.reports import ReportQueryRequest, ReportQueryResponse
from src.services import reporting_service

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ParseRequest(BaseModel):
    text: str


@router.post("/expenses/parse")
async def parse_expense(payload: ParseRequest) -> dict:
    """Draft-only parsing (constitution Principle II) — never writes to the DB.

    Returns either a ready-for-confirmation draft or a needs_clarification
    follow-up question, per FR-008/FR-009.
    """
    return await parse_expense_draft(payload.text)


@router.post("/expenses/parse-receipt")
async def parse_receipt(file: UploadFile = File(...)) -> dict:
    """Draft-only parsing from an uploaded receipt/invoice image.

    Never persists the uploaded image (FR-008) — read into memory, sent to
    the vision model, and discarded once this request completes.
    """
    if file.content_type not in RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Unsupported image type: {file.content_type}"
        )
    image_bytes = await file.read()
    if len(image_bytes) > RECEIPT_IMAGE_MAX_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="Image exceeds the 5MB size limit")
    return await parse_receipt_image(image_bytes, file.content_type)


@router.post("/reports/query", response_model=ReportQueryResponse)
async def query_report(
    payload: ReportQueryRequest, session: AsyncSession = Depends(get_session)
) -> ReportQueryResponse | JSONResponse:
    """Ask for a report in natural language (FR-007's chat path).

    Resolves report type and date/period via `resolve_report_request`,
    calls the *exact same* deterministic `ReportingService` function the
    matching direct endpoint uses, then narrates via `narrate_report` — the
    AI never computes or states a figure itself (FR-001).
    """
    resolution = await resolve_report_request(payload.question, datetime.date.today())
    report_type = resolution["report_type"]
    if report_type is None:
        clarification = ReportQueryResponse(
            report_type=None,
            data=None,
            narrative=(
                "I couldn't tell which report you're asking for. Could you say "
                "whether you want a trial balance, profit & loss, balance "
                "sheet, or cash flow, and for what date or period?"
            ),
        )
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    try:
        if report_type == "trial_balance":
            result = await reporting_service.trial_balance(session, resolution["as_of"])
        elif report_type == "profit_and_loss":
            result = await reporting_service.profit_and_loss(
                session, resolution["start"], resolution["end"]
            )
        elif report_type == "balance_sheet":
            result = await reporting_service.balance_sheet(session, resolution["as_of"])
        else:
            result = await reporting_service.cash_flow(
                session, resolution["start"], resolution["end"]
            )
    except reporting_service.ValidationError as exc:
        clarification = ReportQueryResponse(report_type=None, data=None, narrative=str(exc))
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    data = result.model_dump(mode="json")
    narrative = await narrate_report(report_type, data)
    return ReportQueryResponse(report_type=report_type, data=data, narrative=narrative)
