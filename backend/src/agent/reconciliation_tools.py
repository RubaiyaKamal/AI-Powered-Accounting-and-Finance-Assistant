import json
import uuid

from src.config import AGENT_MODEL, OPENAI_API_KEY
from src.models.bank_transaction import BankTransaction
from src.models.expense_entry import ExpenseEntry


async def adjudicate_match(
    transaction: BankTransaction, candidates: list[ExpenseEntry]
) -> tuple[uuid.UUID | None, str | None]:
    """Choose among deterministically-bounded ambiguous candidates, or none.

    Never sees the full expense-entry table — only candidates the
    deterministic scoring pass in reconciliation_service.py already found
    plausible (constitution Principle II: the AI narrows among
    already-identified options, it never invents a match itself). Falls
    back to "no confident pick" when no OPENAI_API_KEY is configured, the
    same fail-safe shape as expense_tools.py/ledger_tools.py.
    """
    if not candidates:
        return None, None

    if not OPENAI_API_KEY:
        return None, "No OpenAI API key configured — routed for manual review."

    from agents import Agent, Runner  # imported lazily, same as other agent tools

    candidate_lines = "\n".join(
        f"- id={c.id}, amount={c.amount}, date={c.date}, description={c.description or ''}"
        for c in candidates
    )
    agent = Agent(
        name="ReconciliationAdjudicator",
        model=AGENT_MODEL,
        instructions=(
            "A bank transaction needs to be matched to one of the candidate expense "
            "entries below, or to none of them if no single one is a confident match. "
            "Respond with ONLY a JSON object, no prose: "
            '{"chosen_id": "<one of the given ids>" or null, "reasoning": "<brief explanation>"}'
        ),
    )
    prompt = (
        f"Bank transaction: amount={transaction.amount}, date={transaction.date}, "
        f"description={transaction.description}\n"
        f"Candidates:\n{candidate_lines}"
    )
    result = await Runner.run(agent, prompt)
    try:
        parsed = json.loads(result.final_output)
        chosen_id_raw = parsed.get("chosen_id")
        reasoning = parsed.get("reasoning")
    except (json.JSONDecodeError, TypeError):
        return None, "Could not confidently determine a match among the candidates."

    valid_ids = {str(c.id) for c in candidates}
    if chosen_id_raw not in valid_ids:
        return None, reasoning or "No candidate was confidently chosen."

    return uuid.UUID(chosen_id_raw), reasoning
