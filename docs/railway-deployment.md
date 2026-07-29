# Deploying the backend to Railway

This covers deploying the FastAPI backend and its PostgreSQL database to
Railway. The frontend is deployed separately (e.g. Vercel) and is out of
scope here — see the root `README.md` for local dev with all three services
via `docker-compose`.

## Prerequisites

- A Railway account with the GitHub repo connected/authorized.
- Your `OPENAI_API_KEY` (optional — the agent falls back to a local
  heuristic if empty, same as local dev).

## Step 1: Create the Railway project

New Project → Deploy from GitHub repo → select this repository.

## Step 2: Add the Postgres plugin

Add a "Postgres" database plugin to the project. Railway auto-generates its
own `DATABASE_URL` variable scoped to the plugin, in plain `postgresql://`
form (no driver suffix) — this is expected. The backend normalizes the
scheme itself (see `backend/src/config.py`), so you don't need to edit it.

## Step 3: Configure the backend service

- **Root Directory**: set to `backend/`. This is a monorepo (`backend/`,
  `frontend/`, plus a root `docker-compose.yml` for local dev only); Railway
  won't find the Dockerfile or `pyproject.toml` from the repo root.
- **Builder**: should auto-detect as Dockerfile once `backend/railway.toml`
  is present. Verify under Settings → Build if unsure.

## Step 4: Set environment variables on the backend service

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference variable — keeps it in sync if credentials rotate) |
| `OPENAI_API_KEY` | your key |
| `AGENT_MODEL` | optional, defaults to `gpt-4o-mini` |
| `FRONTEND_ORIGIN` | your deployed frontend's origin, e.g. `https://your-app.vercel.app` (no trailing slash; comma-separate if multiple) |
| `ACCOUNT_CODING_CONFIDENCE_THRESHOLD` | optional, defaults to `0.8` |
| `EMBEDDING_MODEL` | optional, defaults to `text-embedding-3-small` |

Do **not** manually set `PORT` — Railway injects it automatically and the
Dockerfile now binds to it.

## Step 5: Deploy and verify logs

Trigger a deploy and watch:
1. Build logs — `uv sync` completing successfully.
2. Deploy logs — `alembic upgrade head` printing applied migration
   revisions (not just "already up to date" on a fresh database, which
   would mean migrations silently didn't run).
3. uvicorn logs — bound to `0.0.0.0:$PORT` (the actual injected port, not
   necessarily `8000`).

## Step 6: Verify the health check

`GET https://<service>.up.railway.app/health` should return
`{"status": "ok"}`. Railway's dashboard should show the deployment as
"Healthy" (wired via `healthcheckPath` in `backend/railway.toml`).

## Step 7: Verify migrations against the database

Via Railway's Postgres plugin "Data" tab, or `railway connect postgres`,
confirm the expected tables exist: `expense_entries`, `categories`,
`expense_entry_edit_history`, `accounts`, `journal_entries`, etc.

## Troubleshooting

**"No open port detected" / app deploys but is unreachable**
The Dockerfile CMD must read `--port ${PORT:-8000}`, not a hardcoded port.
Also check there's no custom Start Command set in the Railway dashboard
that overrides the Dockerfile's `CMD` with a hardcoded port.

**`sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.` during the `alembic upgrade head` step**
This was hit in an actual deploy attempt. Cause: `DATABASE_URL` reached the
app without a `+asyncpg` driver suffix. `backend/src/db.py` creates its
async engine at import time using the raw `DATABASE_URL`, and this import
happens as a side effect of Alembic loading the model metadata — so it
fails before Alembic even gets to use its own sync-driver override. Fixed
by `_normalize_database_url()` in `backend/src/config.py`, which rewrites
`postgres://`/`postgresql://` to `postgresql+asyncpg://` at read time. If
you see this error, confirm the deployed image actually includes that fix
(rebuild/redeploy if it's from before this change).

**Build fails with "Dockerfile not found" or "pyproject.toml not found"**
Root Directory on the backend service isn't set to `backend/`.

**CORS errors in the browser console from the deployed frontend**
`FRONTEND_ORIGIN` isn't set (or is wrong — check protocol, trailing slash)
on the backend service. Restart the service after changing it.

**Migrations never ran / tables missing, but the app "boots fine"**
A custom Start Command was set in the Railway dashboard that only runs
uvicorn, skipping `alembic upgrade head`. Clear the custom Start Command so
the Dockerfile's `CMD` (which chains migrate-then-serve) is used, or
explicitly replicate the full chain in the custom command.

**`DATABASE_URL` silently pointing at `localhost`**
The `${{Postgres.DATABASE_URL}}` reference variable wasn't actually
attached to the backend service — check it's not blank/unset in the
service's Variables tab.

**`backend/railway.toml` doesn't seem to be applied**
Check Settings → Config as Code — the path should resolve relative to the
Root Directory (`backend/`). Set it explicitly if Railway didn't
auto-detect it.

## Rollback

Railway keeps prior deployments — use "Redeploy" on a previous successful
deployment from the Deployments tab if a new one breaks production.
Alembic migrations here are forward-only (no generated `downgrade`
scripts), so check migration content before relying on
`alembic downgrade` in an emergency.
