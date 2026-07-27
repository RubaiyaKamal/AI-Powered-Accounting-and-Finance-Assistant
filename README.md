# AI-Powered Accounting Assistant

An accounting/bookkeeping web app with an AI agent layer: manage expenses,
income, and ledgers through a modern UI, and let an AI assistant automate
accounting tasks via natural language (entry creation, reports, audits,
spending Q&A). Built spec-first — see `/specs` and `/history/prompts` for
the full spec → clarify → plan → tasks → implement trail behind every
feature, and `.specify/memory/constitution.md` for the project's governing
principles.

## Stack

- **Frontend**: Next.js (App Router) + TypeScript — `frontend/`
- **Backend**: FastAPI + Pydantic v2 + SQLAlchemy (async) + Alembic, managed with `uv` — `backend/`
- **Database**: PostgreSQL
- **AI layer**: OpenAI Agents SDK (GPT-4o mini) — the agent only ever drafts/suggests; every write goes through the same validated backend endpoint a human confirms (see the constitution's Principle II)

## Workflow diagram

`docs/workflow-diagram.drawio` — open it free at
[app.diagrams.net](https://app.diagrams.net) (File → Open From → Device) to
view/edit, and use its Share button to get a shareable link.

## Running with Docker (recommended)

```bash
cp backend/.env.example backend/.env      # add your OPENAI_API_KEY (optional — falls back to a local heuristic if empty)
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Postgres: localhost:5432 (user/pass: `postgres`/`postgres`, db: `accounting`)

The backend container needs the database migrated on first run:

```bash
docker-compose exec backend uv run alembic upgrade head
```

## Running locally without Docker

**Backend**

```bash
cd backend
uv sync
cp .env.example .env   # point DATABASE_URL at a local Postgres instance
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Tests / linting

```bash
cd backend && uv run ruff check src migrations && uv run pytest
cd frontend && npx tsc --noEmit && npm run lint
```

## Project structure

```
specs/<feature>/       spec.md → plan.md → tasks.md per feature (SDD artifacts)
history/prompts/       Prompt History Records for every /sp.* command
history/adr/           Architecture Decision Records
.specify/memory/       Project constitution
research/              Phase 1 research paper content
backend/               FastAPI app
frontend/              Next.js app
docs/                  Workflow diagram
```
