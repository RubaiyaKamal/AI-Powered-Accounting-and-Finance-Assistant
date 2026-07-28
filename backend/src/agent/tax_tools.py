import json

from src.config import AGENT_MODEL, EMBEDDING_MODEL, OPENAI_API_KEY


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
