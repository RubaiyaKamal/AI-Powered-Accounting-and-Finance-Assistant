import datetime
import json

from src.config import AGENT_MODEL, OPENAI_API_KEY

REPORT_TYPES = ("trial_balance", "profit_and_loss", "balance_sheet", "cash_flow")


def _parse_date(value: object) -> datetime.date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


async def resolve_report_request(question: str, today: datetime.date) -> dict:
    """Classify a natural-language question into a report type and date/period.

    Sees only the question text and today's date — never ledger data
    (constitution Principle II; research.md's two-narrow-LLM-calls
    decision). Falls back to keyword matching when no OPENAI_API_KEY is
    configured; unresolved dates are left `None` so the caller's
    ReportingService function applies its own default (today / current
    calendar month) rather than this tool guessing one.
    """
    if not OPENAI_API_KEY:
        lowered = question.lower()
        if "trial balance" in lowered:
            report_type = "trial_balance"
        elif "balance sheet" in lowered:
            report_type = "balance_sheet"
        elif "cash flow" in lowered or "cash" in lowered:
            report_type = "cash_flow"
        elif any(word in lowered for word in ("profit", "loss", "p&l", "p and l", "income")):
            report_type = "profit_and_loss"
        else:
            report_type = None
        return {"report_type": report_type, "as_of": None, "start": None, "end": None}

    from agents import Agent, Runner

    agent = Agent(
        name="ReportRequestResolver",
        model=AGENT_MODEL,
        instructions=(
            "Classify a business owner's question into one of four financial "
            "report types, and a date or date range if one is clearly implied. "
            "Report types: 'trial_balance' (every account's balance as of a "
            "date), 'profit_and_loss' (revenue and expenses over a period), "
            "'balance_sheet' (assets/liabilities/equity as of a date), "
            "'cash_flow' (change in cash over a period). trial_balance and "
            "balance_sheet take an 'as_of' date; profit_and_loss and cash_flow "
            "take a 'start' and 'end' date. If the question does not clearly "
            "imply one of these four report types, set report_type to null. "
            "Only set a date field you can confidently infer from the "
            "question and today's date; leave the rest null rather than "
            "guessing. Reply with ONLY a JSON object, no prose: "
            '{"report_type": "trial_balance"|"profit_and_loss"|"balance_sheet"'
            '|"cash_flow"|null, "as_of": "YYYY-MM-DD"|null, '
            '"start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null}'
        ),
    )
    prompt = f"Today's date: {today.isoformat()}\nQuestion: {question}"
    result = await Runner.run(agent, prompt)
    try:
        parsed = json.loads(result.final_output)
    except (json.JSONDecodeError, TypeError):
        return {"report_type": None, "as_of": None, "start": None, "end": None}

    report_type = parsed.get("report_type")
    if report_type not in REPORT_TYPES:
        report_type = None

    return {
        "report_type": report_type,
        "as_of": _parse_date(parsed.get("as_of")),
        "start": _parse_date(parsed.get("start")),
        "end": _parse_date(parsed.get("end")),
    }


def _fallback_narrative(report_type: str, data: dict) -> str:
    if report_type == "trial_balance":
        return (
            f"Trial balance as of {data['as_of']}: total debits "
            f"{data['total_debits']}, total credits {data['total_credits']} "
            f"({'balanced' if data['is_balanced'] else 'not balanced'})."
        )
    if report_type == "profit_and_loss":
        return (
            f"For {data['start']} to {data['end']}: total revenue "
            f"{data['total_revenue']}, total expenses {data['total_expenses']}, "
            f"net profit {data['net_profit']}."
        )
    if report_type == "balance_sheet":
        return (
            f"Balance sheet as of {data['as_of']}: total assets "
            f"{data['total_assets']}, total liabilities {data['total_liabilities']}, "
            f"total equity {data['total_equity']} "
            f"({'balanced' if data['is_balanced'] else 'not balanced'})."
        )
    return (
        f"Cash flow for {data['start']} to {data['end']}: opening balance "
        f"{data['opening_balance']}, closing balance {data['closing_balance']}, "
        f"net change {data['net_change']}."
    )


async def narrate_report(report_type: str, computed_result: dict) -> str:
    """Describe already-computed report figures in prose.

    Sees only the final computed result object (the same shape the direct
    REST endpoint returns) — never raw journal-entry rows, and never asked
    to calculate anything itself (constitution Principle II). Falls back to
    a plain templated summary when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return _fallback_narrative(report_type, computed_result)

    from agents import Agent, Runner

    agent = Agent(
        name="ReportNarrator",
        model=AGENT_MODEL,
        instructions=(
            "Describe the given already-computed financial report figures in "
            "one or two plain-language sentences for a small business owner. "
            "Use only the numbers provided — never calculate, estimate, or "
            "introduce any figure not present in the given data."
        ),
    )
    prompt = f"Report type: {report_type}\nData: {json.dumps(computed_result, default=str)}"
    result = await Runner.run(agent, prompt)
    return result.final_output.strip()
