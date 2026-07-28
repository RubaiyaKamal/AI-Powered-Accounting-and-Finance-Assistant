import datetime
import json
import re

from src.config import AGENT_MODEL, OPENAI_API_KEY

REQUEST_KINDS = ("amount", "breakdown", "comparison", "forecast")

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)

_EMPTY_PARAMS = {
    "account_name": None,
    "start": None,
    "end": None,
    "period_a_start": None,
    "period_a_end": None,
    "period_b_start": None,
    "period_b_end": None,
    "target_start": None,
    "target_end": None,
}


def _strip_code_fence(text: str) -> str:
    # gpt-4o-mini sometimes wraps a JSON reply in a markdown code fence
    # despite being told "no prose" — strip it so json.loads still succeeds
    # rather than falling back unnecessarily (mirrors audit_tools.py).
    match = _CODE_FENCE_RE.search(text)
    return match.group(1) if match else text


def _parse_date(value: object) -> datetime.date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _fallback_resolution(question: str, account_names: list[str]) -> dict:
    lowered = question.lower()
    if any(
        word in lowered
        for word in ("forecast", "predict", "expect", "likely", "next month", "next quarter")
    ):
        return {"request_kind": "forecast", **_EMPTY_PARAMS}
    if any(
        word in lowered
        for word in ("compare", "comparison", "versus", " vs ", "difference between")
    ):
        return {"request_kind": "comparison", **_EMPTY_PARAMS}
    if any(
        word in lowered
        for word in ("breakdown", "most on", "biggest", "categories", "where did")
    ):
        return {"request_kind": "breakdown", **_EMPTY_PARAMS}

    matched_account = next(
        (name for name in account_names if name.lower().replace(" expense", "").strip() in lowered),
        None,
    )
    if matched_account or any(word in lowered for word in ("spend", "spent", "cost", "how much")):
        return {"request_kind": "amount", **_EMPTY_PARAMS, "account_name": matched_account}

    return {"request_kind": None, **_EMPTY_PARAMS}


async def resolve_spending_request(
    question: str, today: datetime.date, account_names: list[str]
) -> dict:
    """Classify a natural-language spending question into a request kind and its parameters.

    Sees only the question text, today's date, and the real expense account
    name list — never ledger data (constitution Principle II). account_name
    is bound to the given list exactly, mirroring `suggest_account_coding`'s
    established pattern — the model picks one of the given names or leaves
    it null, never invents an account (FR-005). Every one of the four
    request kinds is described here from the start (research.md), so the
    classifier can correctly discriminate between them even before every
    kind's underlying computation exists. request_kind is left as
    "amount" (not forced to null) when the kind is clear but no account
    matched, so the caller can distinguish "couldn't tell what you meant"
    (FR-004) from "that account doesn't exist" (FR-005, spec US1 AC4).
    Falls back to keyword matching when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return _fallback_resolution(question, account_names)

    from agents import Agent, Runner

    accounts_list = ", ".join(account_names) if account_names else "(none)"
    agent = Agent(
        name="SpendingRequestResolver",
        model=AGENT_MODEL,
        instructions=(
            "Classify a business owner's spending question into exactly one of four "
            "kinds, and extract its parameters. Kinds:\n"
            "- 'amount': total spending for ONE specific account/category over a "
            "period. Requires account_name (must be exactly one of the given real "
            "account names below, written exactly as given — if none matches, leave "
            "account_name null but still set request_kind to 'amount' if the "
            "question is clearly asking about one account/category) and optionally "
            "start/end (a period).\n"
            "- 'breakdown': a ranked view of spending across ALL accounts for a "
            "period. Takes optional start/end.\n"
            "- 'comparison': spending compared between TWO periods. Takes "
            "period_a_start/period_a_end and period_b_start/period_b_end.\n"
            "- 'forecast': an estimate of FUTURE spending. Takes "
            "target_start/target_end (the future period being asked about).\n"
            "If the question doesn't clearly match one of these four kinds, set "
            "request_kind to null. Only set a date field you can confidently infer "
            "from the question and today's date; leave the rest null rather than "
            "guessing — a missing period for amount/breakdown/forecast is fine (the "
            "caller defaults it to the current month), but comparison always needs "
            "both periods to make sense.\n"
            f"Real expense account names: {accounts_list}\n"
            "Reply with ONLY a JSON object, no prose: "
            '{"request_kind": "amount"|"breakdown"|"comparison"|"forecast"|null, '
            '"account_name": "<one of the given names, exactly as written>"|null, '
            '"start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null, '
            '"period_a_start": "YYYY-MM-DD"|null, "period_a_end": "YYYY-MM-DD"|null, '
            '"period_b_start": "YYYY-MM-DD"|null, "period_b_end": "YYYY-MM-DD"|null, '
            '"target_start": "YYYY-MM-DD"|null, "target_end": "YYYY-MM-DD"|null}'
        ),
    )
    prompt = f"Today's date: {today.isoformat()}\nQuestion: {question}"
    result = await Runner.run(agent, prompt)
    try:
        parsed = json.loads(_strip_code_fence(result.final_output))
    except (json.JSONDecodeError, TypeError):
        return {"request_kind": None, **_EMPTY_PARAMS}

    if not isinstance(parsed, dict):
        return {"request_kind": None, **_EMPTY_PARAMS}

    request_kind = parsed.get("request_kind")
    if request_kind not in REQUEST_KINDS:
        request_kind = None

    account_name = parsed.get("account_name")
    if not (isinstance(account_name, str) and account_name in account_names):
        account_name = None

    return {
        "request_kind": request_kind,
        "account_name": account_name,
        "start": _parse_date(parsed.get("start")),
        "end": _parse_date(parsed.get("end")),
        "period_a_start": _parse_date(parsed.get("period_a_start")),
        "period_a_end": _parse_date(parsed.get("period_a_end")),
        "period_b_start": _parse_date(parsed.get("period_b_start")),
        "period_b_end": _parse_date(parsed.get("period_b_end")),
        "target_start": _parse_date(parsed.get("target_start")),
        "target_end": _parse_date(parsed.get("target_end")),
    }


def _fallback_narrative(request_kind: str, data: dict) -> str:
    if request_kind == "amount":
        return (
            f"From {data['start']} to {data['end']}, you spent {data['amount']} on "
            f"{data['account_name']}."
        )
    if request_kind == "breakdown":
        if not data["lines"]:
            return f"No expense activity from {data['start']} to {data['end']}."
        top = data["lines"][0]
        return (
            f"From {data['start']} to {data['end']}, total spending was {data['total']}. "
            f"The largest category was {top['account_name']} at {top['amount']}."
        )
    if request_kind == "comparison":
        changed_up = data["total_change"] and float(data["total_change"]) > 0
        direction = "up" if changed_up else "down"
        return (
            f"Spending went from {data['total_period_a']} "
            f"({data['period_a']['start']} to {data['period_a']['end']}) to "
            f"{data['total_period_b']} ({data['period_b']['start']} to "
            f"{data['period_b']['end']}), {direction} by {abs(float(data['total_change']))}."
        )
    # forecast
    if data.get("status") == "insufficient_data":
        return (
            f"There isn't enough spending history yet to forecast "
            f"{data['target_start']} to {data['target_end']}."
        )
    return (
        f"Estimated spending for {data['target_start']} to {data['target_end']} is "
        f"{data['forecast_amount']}, based on a {data['method']}. This is an estimate, "
        "not a certainty."
    )


async def narrate_spending_result(request_kind: str, computed_result: dict) -> str:
    """Narrate an already-computed spending result in prose.

    Sees only the final computed result object (the same shape the direct
    endpoint returns) — never raw ledger rows, and never asked to calculate
    anything itself (constitution Principle II). A forecast result is
    always explicitly framed as an estimate (FR-008), even in the LLM path
    — the instructions require it. Falls back to a plain templated summary
    when no OPENAI_API_KEY is configured.
    """
    if not OPENAI_API_KEY:
        return _fallback_narrative(request_kind, computed_result)

    from agents import Agent, Runner

    agent = Agent(
        name="SpendingResultNarrator",
        model=AGENT_MODEL,
        instructions=(
            "Describe the given already-computed spending result in one or two "
            "plain-language sentences for a small business owner. Use only the "
            "numbers provided — never calculate, estimate, or introduce any figure "
            "not present in the given data. If the result is a forecast, explicitly "
            "say it's an estimate, not a certainty — and if its status is "
            "'insufficient_data', clearly say there isn't enough history yet rather "
            "than inventing a figure."
        ),
    )
    prompt = f"Request kind: {request_kind}\nData: {json.dumps(computed_result, default=str)}"
    result = await Runner.run(agent, prompt)
    return result.final_output.strip()
