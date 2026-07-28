from src.config import EMBEDDING_MODEL, OPENAI_API_KEY


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
