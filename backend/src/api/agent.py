import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.analysis_tools import narrate_spending_result, resolve_spending_request
from src.agent.audit_tools import narrate_audit_run, resolve_audit_request
from src.agent.expense_tools import parse_expense_draft, parse_receipt_image
from src.agent.reporting_tools import narrate_report, resolve_report_request
from src.agent.tax_tools import resolve_summary_request
from src.config import RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES, RECEIPT_IMAGE_MAX_SIZE_BYTES
from src.db import get_session
from src.schemas.analysis import SpendingQueryRequest, SpendingQueryResponse
from src.schemas.audit import AuditQueryRequest, AuditQueryResponse, AuditRunResponse
from src.schemas.reports import ReportQueryRequest, ReportQueryResponse
from src.schemas.tax import TaxQueryRequest, TaxQueryResponse, TaxSummaryResponse
from src.services import (
    account_service,
    analysis_service,
    audit_service,
    reporting_service,
    tax_summary_service,
)

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


@router.post("/audit/query", response_model=AuditQueryResponse)
async def query_audit(
    payload: AuditQueryRequest, session: AsyncSession = Depends(get_session)
) -> AuditQueryResponse | JSONResponse:
    """Ask for an audit in natural language (US4's chat path).

    Resolves a date range via `resolve_audit_request`, calls the *exact
    same* deterministic `AuditService.run_audit` a direct request would
    use, then narrates via `narrate_audit_run` — the AI never decides
    which entries are anomalous itself (FR-002).
    """
    resolution = await resolve_audit_request(payload.question, datetime.date.today())
    if not resolution["resolvable"]:
        clarification = AuditQueryResponse(
            data=None,
            narrative=(
                "I couldn't tell what period you'd like audited. Could you say a "
                "date range, like 'this month' or 'last quarter'?"
            ),
        )
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    try:
        run = await audit_service.run_audit(session, resolution["start"], resolution["end"])
    except audit_service.ValidationError as exc:
        clarification = AuditQueryResponse(data=None, narrative=str(exc))
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    data = AuditRunResponse.model_validate(run).model_dump(mode="json")
    narrative = await narrate_audit_run(data)
    return AuditQueryResponse(data=data, narrative=narrative)


@router.post("/tax/query", response_model=TaxQueryResponse)
async def query_tax_summary(
    payload: TaxQueryRequest, session: AsyncSession = Depends(get_session)
) -> TaxQueryResponse | JSONResponse:
    """Ask for a tax/compliance summary in natural language (US4's chat path).

    Resolves a date range via `resolve_summary_request`, calls the *exact
    same* deterministic `TaxSummaryService.generate` a direct request
    would use, and returns the generated summary's own `narrative` — no
    separate narration call, since `generate` already produces one overall
    narrative per summary (unlike audit's per-flag explanations).
    """
    resolution = await resolve_summary_request(payload.question, datetime.date.today())
    if not resolution["resolvable"]:
        clarification = TaxQueryResponse(
            data=None,
            narrative=(
                "I couldn't tell what period you'd like a tax summary for. Could you "
                "say a date range, like 'this month' or 'last quarter'?"
            ),
        )
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    try:
        summary = await tax_summary_service.generate(
            session, resolution["start"], resolution["end"]
        )
    except tax_summary_service.ValidationError as exc:
        clarification = TaxQueryResponse(data=None, narrative=str(exc))
        return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))

    data = TaxSummaryResponse.model_validate(summary).model_dump(mode="json")
    return TaxQueryResponse(data=data, narrative=summary.narrative)


def _analysis_clarification(narrative: str) -> JSONResponse:
    clarification = SpendingQueryResponse(request_kind=None, data=None, narrative=narrative)
    return JSONResponse(status_code=422, content=clarification.model_dump(mode="json"))


@router.post("/analysis/query", response_model=SpendingQueryResponse)
async def query_analysis(
    payload: SpendingQueryRequest, session: AsyncSession = Depends(get_session)
) -> SpendingQueryResponse | JSONResponse:
    """Ask a spending question in natural language.

    This is the *sole* delivery mechanism for the single-amount request
    kind (US1 — spec.md describes it only via natural language, with no
    direct REST equivalent) and the chat path for the rest (US4). Resolves
    the question via `resolve_spending_request` (bounded to the real
    expense account list), calls the *exact same* deterministic
    `AnalysisService` function the matching direct endpoint (where one
    exists) uses, then narrates via `narrate_spending_result` — the AI
    never computes or states a figure itself (FR-002).
    """
    accounts = await account_service.list_accounts(session)
    account_names = [account.name for account in accounts if account.type == "expense"]

    resolution = await resolve_spending_request(
        payload.question, datetime.date.today(), account_names
    )
    request_kind = resolution["request_kind"]

    if request_kind is None:
        return _analysis_clarification(
            "I couldn't tell what kind of spending question that is. Could you ask "
            "for a specific account's total, a spending breakdown, a comparison "
            "between two periods, or a forecast?"
        )

    try:
        if request_kind == "amount":
            if resolution["account_name"] is None:
                return _analysis_clarification(
                    "I couldn't find an account matching what you asked about in "
                    "your chart of accounts."
                )
            result = await analysis_service.spending_amount(
                session, resolution["account_name"], resolution["start"], resolution["end"]
            )
        elif request_kind == "breakdown":
            result = await analysis_service.breakdown(
                session, resolution["start"], resolution["end"]
            )
        elif request_kind == "comparison":
            periods = (
                resolution["period_a_start"],
                resolution["period_a_end"],
                resolution["period_b_start"],
                resolution["period_b_end"],
            )
            if not all(periods):
                return _analysis_clarification(
                    "I couldn't tell which two periods you'd like to compare. Could "
                    "you name both periods?"
                )
            result = await analysis_service.comparison(session, *periods)
        else:  # forecast
            if not resolution["target_start"] or not resolution["target_end"]:
                return _analysis_clarification(
                    "I couldn't tell which future period you'd like a forecast for. "
                    "Could you name it, like 'next month'?"
                )
            result = await analysis_service.forecast(
                session, resolution["target_start"], resolution["target_end"]
            )
    except (analysis_service.ValidationError, analysis_service.NotFoundError) as exc:
        return _analysis_clarification(str(exc))

    data = result.model_dump(mode="json")
    narrative = await narrate_spending_result(request_kind, data)
    return SpendingQueryResponse(request_kind=request_kind, data=data, narrative=narrative)
