import os

from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url: str) -> str:
    """Rewrite postgres://... or postgresql://... to the asyncpg driver scheme
    SQLAlchemy's async engine requires. Railway's Postgres plugin (and most
    managed Postgres hosts) exposes DATABASE_URL without a driver suffix.
    Leaves the URL untouched if a driver is already specified.
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalize_database_url(
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/accounting",
    )
)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
AGENT_MODEL = os.environ.get("AGENT_MODEL", "gpt-4o-mini")
FRONTEND_ORIGINS = list(
    dict.fromkeys(
        ["http://localhost:3000"]
        + [
            origin.strip()
            for origin in os.environ.get("FRONTEND_ORIGIN", "").split(",")
            if origin.strip()
        ]
    )
)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
ACCOUNT_CODING_CONFIDENCE_THRESHOLD = float(
    os.environ.get("ACCOUNT_CODING_CONFIDENCE_THRESHOLD", "0.8")
)

RECEIPT_IMAGE_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
RECEIPT_IMAGE_MAX_SIZE_BYTES = 5 * 1024 * 1024
