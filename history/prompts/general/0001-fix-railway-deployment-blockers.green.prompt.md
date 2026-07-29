---
id: 0001
title: Fix Railway deployment blockers and add deployment runbook
stage: green
date: 2026-07-29
surface: agent
model: claude-sonnet-5
feature: none
branch: main
user: Rubaiya-Kamal
command: /plan
labels: ["deployment", "railway", "backend", "docker", "database"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/Dockerfile
 - backend/src/config.py
 - backend/.env.example
 - backend/railway.toml
 - docs/railway-deployment.md
 - README.md
 - backend/tests/unit/test_config.py
tests:
 - backend/tests/unit/test_config.py (new: 4 unit tests for _normalize_database_url)
 - uv run ruff check src migrations tests (PASS)
 - uv run pytest (4 passed)
 - docker compose up --build db backend (verified: alembic upgrade head ran, health check 200, uvicorn bound to fallback port 8000 with no PORT set)
 - docker run with PORT=5555 env override against the built image (verified: uvicorn bound to 0.0.0.0:5555, health check 200)
---

## Prompt

tell me the full process how to deploy backend FASTAPI and DATABASE on Railway I tried many times but again and again issues come

[Follow-up, pasted mid-planning as further context — an actual Railway deploy log]:
File "/app/.venv/lib/python3.12/site-packages/alembic/script/base.py", line 556, in run_env
    util.load_python_file(self.dir, "env.py")
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/alembic/util/pyfiles.py", line 116, in load_python_file
  File "/app/.venv/bin/alembic", line 10, in <module>
    module = load_module_py(module_id, path)
    sys.exit(main())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/alembic/util/pyfiles.py", line 136, in load_module_py
             ^^^^^^
    spec.loader.exec_module(module)  # type: ignore
  File "/app/.venv/lib/python3.12/site-packages/alembic/config.py", line 1047, in main
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
    CommandLine(prog=prog).main(argv=argv)
  File "/app/.venv/lib/python3.12/site-packages/alembic/config.py", line 1037, in main
    self.run_cmd(cfg, options)
  File "/app/.venv/lib/python3.12/site-packages/alembic/config.py", line 971, in run_cmd
    fn(
  File "/app/src/models/account.py", line 7, in <module>
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
    from src.db import Base
  File "/app/migrations/env.py", line 6, in <module>
  File "/app/src/db.py", line 8, in <module>
    from src import models  # noqa: F401  (registers all models on Base.metadata)
    engine = create_async_engine(DATABASE_URL, echo=False)
    ^^^^^^^^^^^^^^^^^^^^^^
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/src/models/__init__.py", line 1, in <module>
  File "/app/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/engine.py", line 121, in create_async_engine
    from src.models.account import Account
    return AsyncEngine(sync_engine)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/sqlalchemy/ext/asyncio/engine.py", line 1035, in __init__
    raise exc.InvalidRequestError(
sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.

## Response snapshot

Explored the repo's actual deployment surface (Dockerfile, `src/config.py`, `src/db.py`, `migrations/env.py`, `.env.example`, `docker-compose.yml`) instead of giving generic Railway advice, and found the deploy had never been fully wired: (1) `backend/Dockerfile`'s CMD hardcoded `--port 8000`, ignoring Railway's injected `$PORT`; (2) `create_async_engine(DATABASE_URL, ...)` in `src/db.py` requires the `postgresql+asyncpg://` scheme but nothing normalized Railway's plain `postgresql://` Postgres-plugin URL — confirmed by the pasted traceback, whose root cause is `migrations/env.py` importing `src.models` → `src.db`, which creates the async engine at module-import time using the raw `DATABASE_URL` before Alembic's own sync-driver `.replace()` ever runs; (3) no `railway.toml` existed to pin the Dockerfile builder/health check/restart policy; (4) `.env.example` didn't document `FRONTEND_ORIGIN`/`EMBEDDING_MODEL`. Implemented: `${PORT:-8000}` in the Dockerfile CMD; a `_normalize_database_url()` helper in `src/config.py` that idempotently rewrites `postgres://`/`postgresql://` to `postgresql+asyncpg://`; added the two missing vars to `.env.example`; added `backend/railway.toml` pinning the Dockerfile builder and `/health` health check; wrote `docs/railway-deployment.md` as a full step-by-step runbook with a troubleshooting section mapped to each failure mode found (including the exact pasted error); linked it from `README.md`; added `backend/tests/unit/test_config.py` covering the new normalization helper (the repo's test suite was previously empty). Verified end-to-end with `docker compose up --build` (migrations ran, health check 200, default port fallback worked) and a standalone `docker run -e PORT=5555` against the built image (confirmed dynamic port binding actually works, simulating Railway).

## Outcome

- ✅ Impact: Backend is now Railway-deployable — the two concrete crash/unreachability causes behind repeated failed deploys are fixed in code, plus config-as-code and a runbook exist so the next deploy is procedural instead of trial-and-error.
- 🧪 Tests: `uv run ruff check` + `uv run pytest` both pass (4/4, all new); verified live via `docker compose up --build` and a `PORT` env-override `docker run` against the built image.
- 📁 Files: backend/Dockerfile, backend/src/config.py, backend/.env.example, backend/railway.toml (new), docs/railway-deployment.md (new), README.md, backend/tests/unit/test_config.py (new).
- 🔁 Next prompts: Walk the actual Railway dashboard through `docs/railway-deployment.md` end-to-end to confirm each step against the real service; commit and push once the user has reviewed.
- 🧠 Reflection: The real deploy traceback the user pasted mid-planning was decisive — it let the plan cite the exact root cause chain (`migrations/env.py` → `src.models` → `src.db`'s module-level `create_async_engine`) rather than reasoning abstractly about scheme mismatches, and confirmed the chosen fix (normalize in `config.py`, the single import source) resolves it everywhere at once.

## Evaluation notes (flywheel)

- Failure modes observed: Repo had zero prior Railway documentation or config-as-code; two silent-failure-prone code paths (hardcoded port, unnormalized DB URL scheme) had persisted through at least one prior partial fix (the CORS-only fix in PR #16) without being caught, because nothing exercised a Railway-like environment locally until this session's `docker run -e PORT=...` check.
- Graders run and results (PASS/FAIL): ruff PASS; pytest PASS (4/4); live docker-compose boot PASS; live PORT-override boot PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Consider adding a lightweight CI step that builds the backend Docker image and boots it once with a `PORT` env override, so a future regression in the port/DB-scheme handling fails CI instead of surfacing only on a live Railway deploy.
