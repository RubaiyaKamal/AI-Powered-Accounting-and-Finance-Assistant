import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.models.tax_rules_document import TaxRulesDocument
from src.schemas.tax import (
    TaxRulesDocumentCreate,
    TaxRulesDocumentListResponse,
    TaxRulesDocumentResponse,
    TaxRulesDocumentSummary,
    TaxSummaryResponse,
    TaxSummaryTriggerRequest,
)
from src.services import tax_document_service, tax_summary_service

router = APIRouter(prefix="/api/tax", tags=["tax"])


def _document_response(document: TaxRulesDocument) -> TaxRulesDocumentResponse:
    return TaxRulesDocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        chunk_count=len(document.chunks),
        created_at=document.created_at,
    )


def _document_summary(document: TaxRulesDocument) -> TaxRulesDocumentSummary:
    return TaxRulesDocumentSummary(
        id=document.id,
        title=document.title,
        chunk_count=len(document.chunks),
        created_at=document.created_at,
    )


@router.post("/documents", response_model=TaxRulesDocumentResponse, status_code=201)
async def add_document(
    payload: TaxRulesDocumentCreate, session: AsyncSession = Depends(get_session)
) -> TaxRulesDocumentResponse:
    document = await tax_document_service.add_document(session, payload.title, payload.content)
    return _document_response(document)


@router.get("/documents", response_model=TaxRulesDocumentListResponse)
async def list_documents(
    session: AsyncSession = Depends(get_session),
) -> TaxRulesDocumentListResponse:
    documents = await tax_document_service.list_documents(session)
    items = [_document_summary(d) for d in documents]
    return TaxRulesDocumentListResponse(items=items, total=len(items))


@router.get("/documents/{document_id}", response_model=TaxRulesDocumentResponse)
async def get_document(
    document_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> TaxRulesDocumentResponse:
    try:
        document = await tax_document_service.get_document(session, document_id)
    except tax_document_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _document_response(document)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    try:
        await tax_document_service.delete_document(session, document_id)
    except tax_document_service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/summaries", response_model=TaxSummaryResponse, status_code=201)
async def generate_summary(
    payload: TaxSummaryTriggerRequest = TaxSummaryTriggerRequest(),
    session: AsyncSession = Depends(get_session),
) -> TaxSummaryResponse:
    try:
        summary = await tax_summary_service.generate(session, payload.start, payload.end)
    except tax_summary_service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TaxSummaryResponse.model_validate(summary)
