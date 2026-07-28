import json
import re

from src.config import AGENT_MODEL, OPENAI_API_KEY

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    # gpt-4o-mini sometimes wraps a JSON reply in a markdown code fence
    # despite being told "no prose" — strip it so json.loads still succeeds
    # rather than falling back unnecessarily.
    match = _CODE_FENCE_RE.search(text)
    return match.group(1) if match else text

_REASON_CATEGORY_TEMPLATES = {
    "unusual_amount": "its amount is unusual compared to similar postings",
    "round_number": "its amount is a suspiciously round number",
    "duplicate_looking": "it looks like a duplicate of another entry",
    "unusual_account_pairing": "this combination of accounts is rarely used",
    "unusual_timing": "it was posted at an unusual time",
}


def _fallback_explanation(flag_summary: dict) -> str:
    reasons = [
        _REASON_CATEGORY_TEMPLATES.get(category, category)
        for category in flag_summary["reason_categories"]
    ]
    return (
        f"Flagged: {flag_summary['debit_account']} / {flag_summary['credit_account']}, "
        f"{flag_summary['amount']} on {flag_summary['date']} — " + "; ".join(reasons) + "."
    )


async def explain_flags(flag_summaries: list[dict]) -> list[str]:
    """Explain a batch of already-flagged entries in plain language.

    One call per audit run (not one per flag — research.md), so it sees
    only each flag's already-computed score/reason categories and entry
    data — never raw unflagged ledger rows, and never asked to decide
    which entries are anomalous itself (constitution Principle II). Falls
    back to a deterministic per-category template when no
    OPENAI_API_KEY is configured, the same fail-safe shape as
    reporting_tools.py/reconciliation_tools.py.
    """
    if not flag_summaries:
        return []

    if not OPENAI_API_KEY:
        return [_fallback_explanation(summary) for summary in flag_summaries]

    from agents import Agent, Runner

    agent = Agent(
        name="AnomalyExplainer",
        model=AGENT_MODEL,
        instructions=(
            "For each flagged journal entry below, write one short, plain-language "
            "sentence explaining why it was flagged, using only the reason categories "
            "and data given for that entry — never invent a reason or a number not "
            "present in the data. Reply with ONLY a JSON array of strings, no prose, "
            "in the same order as the entries given: "
            '["explanation for entry 0", "explanation for entry 1", ...]'
        ),
    )
    lines = [
        f"{i}. amount={summary['amount']}, date={summary['date']}, "
        f"debit_account={summary['debit_account']}, credit_account={summary['credit_account']}, "
        f"reason_categories={summary['reason_categories']}"
        for i, summary in enumerate(flag_summaries)
    ]
    result = await Runner.run(agent, "\n".join(lines))
    try:
        parsed = json.loads(_strip_code_fence(result.final_output))
        if not isinstance(parsed, list) or len(parsed) != len(flag_summaries):
            raise ValueError("Unexpected explanation count")
        return [str(explanation) for explanation in parsed]
    except (json.JSONDecodeError, TypeError, ValueError):
        return [_fallback_explanation(summary) for summary in flag_summaries]
