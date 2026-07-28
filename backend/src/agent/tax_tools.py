import datetime
import json
import re

from src.config import AGENT_MODEL, EMBEDDING_MODEL, OPENAI_API_KEY

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    # gpt-4o-mini sometimes wraps a JSON reply in a markdown code fence
    # despite being told "no prose" — strip it so json.loads still
    # succeeds rather than falling back unnecessarily.
    match = _CODE_FENCE_RE.search(text)
    return match.group(1) if match else text


def _parse_date(value: object) -> datetime.date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


async def embed_text(text: str) -> list[float] | None:
    """Embed a passage of text for similarity-based retrieval.

    Returns `None` when no OPENAI_API_KEY is configured — retrieval falls
    back to deterministic keyword-overlap scoring for anything without an
    embedding (research.md). This is a plain embeddings-API lookup, not a
    generative call: given the same text and model, it deterministically
    returns (approximately) the same vector, so it carries none of
    Principle II's "never let the LLM compute a figure" risk — it never
    produces a number that appears in a report.
    """
    if not OPENAI_API_KEY:
        return None

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    result = await client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return result.data[0].embedding


def _fallback_narrative(figures: dict, cited_passages: list[dict]) -> str:
    parts = [
        f"For {figures['start']} to {figures['end']}: total revenue "
        f"{figures['total_revenue']}, total expenses {figures['total_expenses']}, "
        f"net profit {figures['net_profit']}."
    ]
    if cited_passages:
        quoted = " ".join(f'"{passage["chunk_text"]}"' for passage in cited_passages)
        parts.append(f"Relevant reference material: {quoted}")
    else:
        parts.append(
            "No relevant reference material was found in the tax rules library for "
            "this period."
        )
    parts.append("This is an unreviewed draft — sign off before treating it as final.")
    return " ".join(parts)


async def draft_summary_narrative(figures: dict, cited_passages: list[dict]) -> str:
    """Draft a plain-language tax/compliance summary from already-computed data.

    Sees only the already-computed figures and already-retrieved passages
    — never raw ledger rows or the full reference library (constitution
    Principle II). Explicitly instructed to say so, not invent guidance,
    when `cited_passages` is empty (FR-005). Falls back to a deterministic
    template when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return _fallback_narrative(figures, cited_passages)

    from agents import Agent, Runner

    agent = Agent(
        name="TaxSummaryNarrator",
        model=AGENT_MODEL,
        instructions=(
            "Draft a short, plain-language tax/compliance summary for a small "
            "business owner, using only the period figures and reference passages "
            "given below — never invent a number or a piece of tax guidance not "
            "present in the data. If no reference passages are given, explicitly say "
            "that no relevant reference material was found rather than offering tax "
            "guidance from your own general knowledge. End by noting this is an "
            "unreviewed draft that needs sign-off before being treated as final."
        ),
    )
    prompt = (
        f"Period figures: {json.dumps(figures, default=str)}\n"
        f"Cited reference passages: {json.dumps(cited_passages, default=str)}"
    )
    result = await Runner.run(agent, prompt)
    return result.final_output.strip()


async def resolve_summary_request(question: str, today: datetime.date) -> dict:
    """Resolve a natural-language summary request into a date range.

    Sees only the question text and today's date — never ledger data or
    the reference library (constitution Principle II). Mirrors
    `resolve_audit_request`'s "unresolvable, ask rather than guess" shape
    (research.md) — guessing a tax period is exactly what this feature's
    regulatory-risk framing argues against. Falls back to "resolvable,
    current calendar month" when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return {"resolvable": True, "start": None, "end": None}

    from agents import Agent, Runner

    agent = Agent(
        name="TaxSummaryRequestResolver",
        model=AGENT_MODEL,
        instructions=(
            "Determine whether a business owner's question clearly implies a date "
            "range for a tax/compliance summary (e.g., 'this month', 'last quarter'). "
            "If a specific period is implied, return its start and end date. If the "
            "question gives you no way to tell what period is meant, set resolvable "
            "to false rather than guessing. Reply with ONLY a JSON object, no prose: "
            '{"resolvable": true|false, "start": "YYYY-MM-DD"|null, '
            '"end": "YYYY-MM-DD"|null}'
        ),
    )
    prompt = f"Today's date: {today.isoformat()}\nQuestion: {question}"
    result = await Runner.run(agent, prompt)
    try:
        parsed = json.loads(_strip_code_fence(result.final_output))
    except (json.JSONDecodeError, TypeError):
        return {"resolvable": False, "start": None, "end": None}

    if not isinstance(parsed, dict) or not parsed.get("resolvable"):
        return {"resolvable": False, "start": None, "end": None}

    return {
        "resolvable": True,
        "start": _parse_date(parsed.get("start")),
        "end": _parse_date(parsed.get("end")),
    }
