import json
from decimal import Decimal, InvalidOperation

from src.config import AGENT_MODEL, OPENAI_API_KEY
from src.models.account import Account


async def suggest_account_coding(description: str, accounts: list[Account]) -> tuple[str, Decimal]:
    """Suggest the best-matching expense account and a confidence score for a description.

    Never writes to the database (constitution Principle II) — the caller
    (LedgerService) decides, from the returned confidence score, whether to
    auto-post or route to review. Falls back to a simple keyword match when
    no OPENAI_API_KEY is configured, so callers always get a usable answer.
    """
    expense_accounts = [a for a in accounts if a.type == "expense"]
    names = [a.name for a in expense_accounts]
    if not names:
        return "Miscellaneous Expense", Decimal("0.00")

    if not OPENAI_API_KEY:
        lowered = description.lower()
        for name in names:
            key = name.lower().replace(" expense", "").strip()
            if key and key in lowered:
                return name, Decimal("0.95")
        return names[0], Decimal("0.40")

    from agents import Agent, Runner

    agent = Agent(
        name="AccountCodingSuggester",
        model=AGENT_MODEL,
        instructions=(
            "Given a short expense description and a list of expense account names, "
            "reply with ONLY a JSON object, no prose: "
            '{"account_name": "<one of the given names, exactly as written>", '
            '"confidence": <number between 0 and 1>}. '
            "confidence should reflect how certain you are that account is the correct match "
            "for the description."
        ),
    )
    prompt = f"Description: {description}\nAccounts: {', '.join(names)}"
    result = await Runner.run(agent, prompt)
    try:
        parsed = json.loads(result.final_output)
        account_name = parsed.get("account_name")
        confidence = Decimal(str(parsed.get("confidence", 0)))
    except (json.JSONDecodeError, TypeError, InvalidOperation):
        account_name = None
        confidence = Decimal("0.00")

    if account_name not in names:
        account_name = names[0]
        confidence = min(confidence, Decimal("0.50"))

    confidence = max(Decimal("0.00"), min(Decimal("1.00"), confidence))
    return account_name, confidence
