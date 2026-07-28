import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/accounting",
)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
AGENT_MODEL = os.environ.get("AGENT_MODEL", "gpt-4o-mini")
ACCOUNT_CODING_CONFIDENCE_THRESHOLD = float(
    os.environ.get("ACCOUNT_CODING_CONFIDENCE_THRESHOLD", "0.8")
)

RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
RECEIPT_IMAGE_MAX_SIZE_BYTES = 5 * 1024 * 1024
