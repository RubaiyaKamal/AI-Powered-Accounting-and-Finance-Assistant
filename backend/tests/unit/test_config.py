from src.config import _normalize_database_url


def test_normalizes_bare_postgres_scheme():
    assert (
        _normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql+asyncpg://user:pass@host:5432/db"
    )


def test_normalizes_bare_postgresql_scheme():
    assert (
        _normalize_database_url("postgresql://user:pass@host:5432/db")
        == "postgresql+asyncpg://user:pass@host:5432/db"
    )


def test_leaves_asyncpg_scheme_untouched():
    url = "postgresql+asyncpg://user:pass@host:5432/db"
    assert _normalize_database_url(url) == url


def test_leaves_other_driver_scheme_untouched():
    url = "postgresql+psycopg2://user:pass@host:5432/db"
    assert _normalize_database_url(url) == url
