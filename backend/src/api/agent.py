from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.agent.expense_tools import parse_expense_draft, parse_receipt_image
from src.config import RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES, RECEIPT_IMAGE_MAX_SIZE_BYTES

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
