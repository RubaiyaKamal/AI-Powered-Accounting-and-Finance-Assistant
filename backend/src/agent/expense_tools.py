import datetime
import json
import re
from decimal import Decimal, InvalidOperation

from src.config import AGENT_MODEL, OPENAI_API_KEY
from src.models.category import Category

REQUIRED_DRAFT_FIELDS = ("amount", "date")

_AMOUNT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)")
_MONTH_NAMES = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


def _fallback_parse(text: str) -> dict:
    """Deterministic, offline fallback used when no OPENAI_API_KEY is configured.

    This intentionally does not attempt to match LLM-quality understanding —
    it exists so the app runs and is testable without a live API key. Real
    parsing quality (SC-002's 90% target) is expected from the Agents SDK
    path below, once a key is configured.
    """
    lowered = text.lower()

    amount_match = _AMOUNT_RE.search(text)
    amount = None
    if amount_match:
        try:
            amount = Decimal(amount_match.group(1).replace(",", ""))
        except InvalidOperation:
            amount = None

    date_value = None
    today = datetime.date.today()
    for i, month in enumerate(_MONTH_NAMES, start=1):
        if month in lowered:
            year = today.year
            # "for <month>" with no day given -> last day of that month, a
            # reasonable default for a monthly bill like the assignment's own example.
            if i == 12:
                next_month_first = datetime.date(year + 1, 1, 1)
            else:
                next_month_first = datetime.date(year, i + 1, 1)
            date_value = next_month_first - datetime.timedelta(days=1)
            break
    if date_value is None and ("today" in lowered or amount is not None):
        date_value = today

    description = text.strip()

    missing = []
    if amount is None:
        missing.append("amount")
    if date_value is None:
        missing.append("date")

    if missing:
        field = missing[0]
        question = "What was the amount?" if field == "amount" else "What date was this for?"
        return {
            "status": "needs_clarification",
            "missing_field": field,
            "follow_up_question": question,
        }

    return {
        "status": "ready_for_confirmation",
        "draft": {
            "amount": str(amount),
            "date": date_value.isoformat(),
            "category_name_hint": description,
            "description": description,
        },
    }


async def parse_expense_draft(text: str) -> dict:
    """Parse free text into a draft expense entry, or ask a follow-up question.

    Never writes to the database (constitution Principle II) — the caller
    is responsible for showing the draft for confirmation (FR-008) before
    calling create_entry.
    """
    if not OPENAI_API_KEY:
        return _fallback_parse(text)

    from agents import Agent, Runner  # imported lazily so the fallback path has no SDK dependency

    agent = Agent(
        name="ExpenseDraftParser",
        model=AGENT_MODEL,
        instructions=(
            "Extract an expense entry draft from the user's message. "
            "Respond with ONLY a JSON object, no prose, in one of these two shapes:\n"
            '{"status": "ready_for_confirmation", "draft": '
            '{"amount": "<decimal string>", "date": "<YYYY-MM-DD>", '
            '"category_name_hint": "<short text>", "description": "<original text>"}}\n'
            'or, if the amount or date cannot be determined:\n'
            '{"status": "needs_clarification", "missing_field": "amount"|"date", '
            '"follow_up_question": "<a specific question for the missing field>"}\n'
            f"Today's date is {datetime.date.today().isoformat()}, use it to resolve "
            'relative dates like "for July" (assume the most recent occurrence of that month).'
        ),
    )
    result = await Runner.run(agent, text)
    try:
        return json.loads(result.final_output)
    except (json.JSONDecodeError, TypeError):
        return _fallback_parse(text)


async def suggest_category(description: str, categories: list[Category]) -> str:
    """Suggest the best-matching category name for a description.

    Falls back to a simple keyword match (or the first category) when no
    OPENAI_API_KEY is configured, so callers always get a usable answer.
    """
    names = [c.name for c in categories]
    if not names:
        return "Miscellaneous"

    if not OPENAI_API_KEY:
        lowered = description.lower()
        for name in names:
            if name.lower() in lowered:
                return name
        return names[0]

    from agents import Agent, Runner

    agent = Agent(
        name="CategorySuggester",
        model=AGENT_MODEL,
        instructions=(
            "Given a short expense description and a list of category names, "
            "reply with ONLY the single best-matching category name from the list, "
            "exactly as written, with no other text."
        ),
    )
    prompt = f"Description: {description}\nCategories: {', '.join(names)}"
    result = await Runner.run(agent, prompt)
    suggestion = result.final_output.strip()
    return suggestion if suggestion in names else names[0]
