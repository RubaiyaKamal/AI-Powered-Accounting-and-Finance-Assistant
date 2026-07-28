import datetime
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


def _parse_date(value: object) -> datetime.date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


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


async def resolve_audit_request(question: str, today: datetime.date) -> dict:
    """Resolve a natural-language audit request into a date range.

    Sees only the question text and today's date — never ledger data
    (constitution Principle II; mirrors `005-reporting`'s
    resolve_report_request/narrate_report split). Unlike reporting's
    silent "default to current period" behavior, an audit request with no
    determinable period is marked unresolvable rather than guessed — the
    caller then asks a clarifying question instead of running an
    unintended full-ledger audit (spec Edge Cases). Falls back to
    "resolvable, whole ledger" when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return {"resolvable": True, "start": None, "end": None}

    from agents import Agent, Runner

    agent = Agent(
        name="AuditRequestResolver",
        model=AGENT_MODEL,
        instructions=(
            "Determine whether a business owner's question clearly implies a date "
            "range to audit (e.g., 'this month', 'last quarter', 'the whole ledger', "
            "'everything so far'). If a specific period is implied, return its start "
            "and end date. If the question implies checking the whole ledger with no "
            "specific period, return null for both dates but still mark it resolvable. "
            "If the question gives you no way to tell what period is meant at all, set "
            "resolvable to false. Reply with ONLY a JSON object, no prose: "
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


def _fallback_run_narrative(run_result: dict) -> str:
    if run_result["status"] == "insufficient_data":
        return (
            f"I checked {run_result['start']} to {run_result['end']}, but there wasn't "
            f"enough posted activity yet ({run_result['entries_evaluated']} entries) for "
            "a meaningful audit."
        )
    if run_result["entries_flagged"] == 0:
        return (
            f"I checked {run_result['start']} to {run_result['end']} "
            f"({run_result['entries_evaluated']} entries) and found nothing unusual."
        )
    return (
        f"I checked {run_result['start']} to {run_result['end']} and found "
        f"{run_result['entries_flagged']} entries worth a look."
    )


async def narrate_audit_run(run_result: dict) -> str:
    """Summarize an already-computed audit run result in one or two sentences.

    Sees only the final run result (the same shape the direct endpoint
    returns, including each flag's already-generated explanation) — never
    raw ledger rows, and never asked to decide or calculate anything
    itself (constitution Principle II). Falls back to a plain templated
    summary when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return _fallback_run_narrative(run_result)

    from agents import Agent, Runner

    agent = Agent(
        name="AuditRunNarrator",
        model=AGENT_MODEL,
        instructions=(
            "Summarize the given already-computed audit run result in one or two "
            "plain-language sentences for a small business owner. Use only the data "
            "given — never introduce a number, entry, or reason not present in it."
        ),
    )
    result = await Runner.run(agent, json.dumps(run_result, default=str))
    return result.final_output.strip()
