import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.bank_transaction import (
    BankTransactionListResponse,
    BankTransactionWithMatch,
    ExpenseEntrySummary,
    ImportInvalidRow,
    ImportSummary,
    ReviewQueueItem,
    ReviewQueueResponse,
)
from src.schemas.match import MatchCreate, MatchRead
from src.services import reconciliation_service as service

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


@router.post("/import", response_model=ImportSummary)
async def import_bank_statement(
    file: UploadFile = File(...), session: AsyncSession = Depends(get_session)
) -> ImportSummary:
    content = await file.read()
    try:
        parsed = service.parse_csv(content)
    except service.ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    inserted, duplicates = await service.import_transactions(session, parsed.valid)

    auto_matched = 0
    needs_review = 0
    for txn in inserted:
        outcome = await service.run_matching_for_transaction(session, txn)
        if outcome == "auto_matched":
            auto_matched += 1
        else:
            needs_review += 1

    return ImportSummary(
        imported=len(inserted),
        duplicates_skipped=duplicates,
        invalid_rows_skipped=[
            ImportInvalidRow(row=r.row, reason=r.reason) for r in parsed.invalid
        ],
        auto_matched=auto_matched,
        needs_review=needs_review,
    )


@router.get("/bank-transactions", response_model=BankTransactionListResponse)
async def list_bank_transactions(
    status: str | None = None, session: AsyncSession = Depends(get_session)
) -> BankTransactionListResponse:
    transactions = await service.list_bank_transactions(session, status=status)
    items = [BankTransactionWithMatch.model_validate(t) for t in transactions]
    return BankTransactionListResponse(items=items, total=len(items))


@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(session: AsyncSession = Depends(get_session)) -> ReviewQueueResponse:
    queue = await service.list_review_queue(session)
    items = [
        ReviewQueueItem(
            bank_transaction=item.bank_transaction,
            suggested_expense_entry=(
                ExpenseEntrySummary.model_validate(item.suggested_expense_entry)
                if item.suggested_expense_entry
                else None
            ),
            ai_reasoning=item.ai_reasoning,
            candidates_considered=(
                [ExpenseEntrySummary.model_validate(c) for c in item.candidates_considered]
                if item.candidates_considered
                else None
            ),
        )
        for item in queue
    ]
    return ReviewQueueResponse(items=items, total=len(items))


@router.post("/bank-transactions/{transaction_id}/match", response_model=MatchRead, status_code=201)
async def confirm_match(
    transaction_id: uuid.UUID,
    payload: MatchCreate,
    session: AsyncSession = Depends(get_session),
) -> MatchRead:
    try:
        match = await service.confirm_match(session, transaction_id, payload.expense_entry_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchRead.model_validate(match)


@router.post(
    "/bank-transactions/{transaction_id}/dismiss", response_model=MatchRead, status_code=201
)
async def dismiss_transaction(
    transaction_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> MatchRead:
    try:
        match = await service.dismiss_transaction(session, transaction_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchRead.model_validate(match)


@router.delete("/matches/{match_id}", status_code=204)
async def undo_match(match_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    try:
        await service.undo_match(session, match_id)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
