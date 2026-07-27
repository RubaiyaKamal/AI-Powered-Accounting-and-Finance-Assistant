from fastapi import APIRouter
from pydantic import BaseModel

from src.agent.expense_tools import parse_expense_draft

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
