# Implementation Plan: Expense Entry

**Branch**: `001-expense-entry` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-expense-entry/spec.md`

## Summary

Let an office admin record, view, edit, and delete daily expense entries —
either through a structured form or a natural-language request to the AI
agent — with AI-suggested categories and full field-level edit history.
Technical approach: FastAPI + Pydantic backend over PostgreSQL (via
SQLAlchemy) stores entries, categories, and edit-history rows; the OpenAI
Agents SDK agent only ever *drafts* a parsed entry (via a `parse_expense_draft`
tool) or *suggests* a category (via `suggest_category`) — it never writes to
the database directly, and every entry (manual or natural-language) is
committed through the same confirmed `POST /api/expenses` call, keeping
financial writes deterministic and human-confirmed per the constitution.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — backend; Next.js (App Router),
React — frontend; dependency management via `uv` (backend) and `npm`
(frontend)
**Storage**: PostgreSQL — `expense_entries`, `categories`,
`expense_entry_edit_history` tables (see `data-model.md`)
**Testing**: pytest + httpx async client (backend contract/integration
tests); Vitest + React Testing Library (frontend component tests)
**Target Platform**: Web application, containerized via Docker
(frontend/backend/PostgreSQL each their own container, wired by
`docker-compose`), per the constitution
**Project Type**: web (frontend + backend split)
**Performance Goals**: Manual entry create/edit/delete round-trips fast
enough to satisfy SC-001 (under 30s including user think-time — the API
call itself should be well under 1s p95); natural-language parsing is
LLM-latency-bound, target under 3s p95 for `POST /api/agent/expenses/parse`
**Constraints**: No financial figure (amount) may be written to the database
as LLM-generated free text — every write goes through the same validated
`POST /api/expenses` / `PATCH /api/expenses/{id}` endpoints regardless of
which UI path produced it (constitution Principle II)
**Scale/Scope**: Single business, single admin user, low volume (hundreds to
low thousands of entries per year) — no high-concurrency or multi-tenant
requirements (spec Assumptions)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and clarified (`/sp.specify`, `/sp.clarify`) before this plan |
| II. Deterministic Financial Computation | ✅ PASS | The agent's tools (`parse_expense_draft`, `suggest_category`) only ever return draft data for confirmation (FR-008, FR-011); the actual database write always goes through the same validated endpoint as the manual form, regardless of source |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS (by extension) | This feature isn't itself an audit/tax action, but it establishes the same pattern (AI drafts, human confirms) that Principle III requires for the higher-stakes features built on top of it |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `001-expense-entry`; will merge to `main` via PR, not direct push |
| V. Documented Architecture & Workflow | ⚠️ PENDING | No Lucidchart/draw.io workflow diagram exists yet project-wide. This feature is the first real implementation of the UI → API → agent → tools → database flow the diagram must show. **Action**: a diagram-creation task is included in `tasks.md`'s Polish phase; this feature's PR should not merge without it, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | No speculative abstractions (no multi-currency, no period-locking — see spec Assumptions); traceable via this plan, `research.md` decisions, and PHRs |

**Gate result**: PASS with one tracked action item (V), not a violation
requiring justification — no entry needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-entry/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── expense-entries-api.md   # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── expense_entry.py       # SQLAlchemy model
│   │   ├── category.py            # SQLAlchemy model
│   │   └── expense_entry_edit_history.py
│   ├── schemas/
│   │   ├── expense_entry.py       # Pydantic request/response models
│   │   └── category.py
│   ├── services/
│   │   ├── expense_entry_service.py   # create/edit/delete + history recording
│   │   └── category_service.py
│   ├── agent/
│   │   └── expense_tools.py       # parse_expense_draft, suggest_category tool defs
│   └── api/
│       ├── expenses.py            # /api/expenses routes
│       ├── categories.py          # /api/categories routes
│       └── agent.py               # /api/agent/expenses/parse route
├── migrations/                    # Alembic migrations (categories seed data included)
└── tests/
    ├── contract/                  # one test file per contracts/expense-entries-api.md endpoint
    ├── integration/                # per-user-story flows (US1-US4)
    └── unit/                       # service-level validation logic

frontend/
├── src/
│   ├── components/
│   │   ├── ExpenseForm.tsx         # manual create/edit (US1, US2)
│   │   ├── ExpenseList.tsx         # list + filters (US2)
│   │   ├── ExpenseHistory.tsx      # edit history view (FR-015a)
│   │   └── AssistantChat.tsx       # NL entry creation UI (US3)
│   ├── pages/ (or app/ under App Router)
│   │   └── expenses/
│   └── services/
│       └── expensesApi.ts          # typed client for contracts/expense-entries-api.md
└── tests/
    └── components/
```

**Structure Decision**: Web application split (`backend/` + `frontend/`),
per the constitution's fixed stack and this being the project's first
feature — these directories are created now and reused by all subsequent
features, not re-decided per feature.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram) is
tracked as a task, not a constitutional exception.*
