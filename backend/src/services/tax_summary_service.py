import datetime
import re
import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.tax_tools import draft_summary_narrative, embed_text
from src.models.tax_rules_document_chunk import TaxRulesDocumentChunk
from src.models.tax_summary import TaxSummary
from src.services import reporting_service

TOP_K_PASSAGES = 3
COSINE_SIMILARITY_FLOOR = 0.2  # a loose relevance bar for OpenAI embeddings
KEYWORD_MIN_OVERLAP = 1  # at least one shared word, for the no-API-key fallback

_STOPWORDS = {
    "a", "an", "the", "is", "are", "of", "to", "in", "for", "and", "or", "this", "that",
    "with", "on", "at", "by", "be", "as", "it", "its",
}


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


async def _retrieve_passages(session: AsyncSession, query_text: str) -> list[dict]:
    """Rank every stored chunk against the query and return the top matches.

    Chunks with a stored embedding are scored by cosine similarity against
    the query's own embedding; chunks without one (added while no
    OPENAI_API_KEY was configured) are scored by keyword overlap instead
    (research.md). Returns `[]` when nothing clears a minimal relevance
    bar — `generate` surfaces that as "no relevant material found" rather
    than including a weak or irrelevant passage (FR-005).
    """
    stmt = select(TaxRulesDocumentChunk).options(selectinload(TaxRulesDocumentChunk.document))
    chunks = list((await session.execute(stmt)).scalars().all())
    if not chunks:
        return []

    query_embedding = await embed_text(query_text)
    query_words = _keywords(query_text)

    scored: list[tuple[float, TaxRulesDocumentChunk]] = []
    for chunk in chunks:
        if query_embedding is not None and chunk.embedding is not None:
            score = _cosine_similarity(query_embedding, chunk.embedding)
            if score > COSINE_SIMILARITY_FLOOR:
                scored.append((score, chunk))
        else:
            overlap = len(query_words & _keywords(chunk.chunk_text))
            if overlap >= KEYWORD_MIN_OVERLAP:
                scored.append((float(overlap), chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {"document_title": chunk.document.title, "chunk_text": chunk.chunk_text}
        for _, chunk in scored[:TOP_K_PASSAGES]
    ]


async def generate(
    session: AsyncSession,
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> TaxSummary:
    try:
        report = await reporting_service.profit_and_loss(session, start, end)
    except reporting_service.ValidationError as exc:
        raise ValidationError(str(exc)) from exc

    query_text = (
        f"Tax and compliance summary for {report.start} to {report.end}. "
        f"Total revenue {report.total_revenue}, total expenses {report.total_expenses}, "
        f"net profit {report.net_profit}."
    )
    cited_passages = await _retrieve_passages(session, query_text)
    figures = {
        "start": report.start.isoformat(),
        "end": report.end.isoformat(),
        "total_revenue": str(report.total_revenue),
        "total_expenses": str(report.total_expenses),
        "net_profit": str(report.net_profit),
    }
    narrative = await draft_summary_narrative(figures, cited_passages)

    summary = TaxSummary(
        start=report.start,
        end=report.end,
        status="draft",
        total_revenue=report.total_revenue,
        total_expenses=report.total_expenses,
        net_profit=report.net_profit,
        cited_passages=cited_passages,
        narrative=narrative,
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)
    return summary


async def get_summary(session: AsyncSession, summary_id: uuid.UUID) -> TaxSummary:
    summary = await session.get(TaxSummary, summary_id)
    if summary is None:
        raise NotFoundError(f"No tax summary with id {summary_id}")
    return summary


async def list_summaries(session: AsyncSession) -> list[TaxSummary]:
    stmt = select(TaxSummary).order_by(TaxSummary.generated_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def sign_off(session: AsyncSession, summary_id: uuid.UUID) -> TaxSummary:
    summary = await get_summary(session, summary_id)
    if summary.status == "signed_off":
        raise ConflictError("This summary is already signed off")

    # Staleness check (FR-009, research.md): recompute the period's actual
    # figures and refuse sign-off if they've drifted from what this draft
    # was generated with — the draft must be regenerated against current
    # data first, not signed off as if it still reflected reality.
    current = await reporting_service.profit_and_loss(session, summary.start, summary.end)
    if (
        current.total_revenue != summary.total_revenue
        or current.total_expenses != summary.total_expenses
    ):
        raise ValidationError(
            "This draft's figures are out of date — regenerate the summary before "
            "signing off"
        )

    summary.status = "signed_off"
    summary.signed_off_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    return summary


async def discard(session: AsyncSession, summary_id: uuid.UUID) -> None:
    summary = await get_summary(session, summary_id)
    if summary.status == "signed_off":
        raise ConflictError("A signed-off summary cannot be discarded")
    await session.delete(summary)
    await session.commit()
