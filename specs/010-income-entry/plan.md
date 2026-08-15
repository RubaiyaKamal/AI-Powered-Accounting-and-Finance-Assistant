# Implementation Plan: Income Entry

**Branch**: `010-income-entry` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-income-entry/spec.md`

## Summary

Let an admin record income (a sale, a service payment, or an owner capital
contribution) via a manual structured form — amount, date, source,
optional description — and have it immediately post a deterministic,
balanced journal entry (debit Cash / credit the source's mapped Revenue or
Equity account). Technical approach: add `income_sources` and
`income_entries` tables, generalize the existing `journal_entries` table
(from `002-ledger-journal-entries`) to allow a posting to originate from
either an expense entry or an income entry, and reuse the existing
`reporting_service.py` unmodified — it already aggregates purely from
`journal_entries` + `accounts`, so once income posts correctly the existing
income-statement and balance-sheet reports pick it up with zero reporting
code changes.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as `001-expense-entry` / `002-ledger-journal-entries`, no new
languages
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic — backend; Next.js (App Router), React — frontend; `uv` (backend) /
`npm` (frontend). No AI/OpenAI Agents SDK dependency for this feature — it
is explicitly manual-entry-only (spec Assumptions).
**Storage**: PostgreSQL — new tables `income_sources`, `income_entries`; one
generalizing migration on the existing `journal_entries` table (see
`data-model.md`)
**Testing**: pytest + httpx async client (backend contract/integration
tests); Vitest + React Testing Library (frontend component tests) — same
tooling as `001-expense-entry` / `002-ledger-journal-entries`
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services in `docker-compose.yml` — no new
services needed)
**Project Type**: web (frontend + backend split, same repo layout as prior
features)
**Performance Goals**: All operations are direct DB reads/writes with no
LLM call on the request path — target well under 1s p95, same as the
non-AI parts of `001`/`002`.
**Constraints**: No debit/credit amount may ever be produced by anything
other than a direct copy of the income entry's own `amount` field by
application code (constitution Principle II) — there is no AI-derived
figure anywhere in this feature. Every posting must remain a balanced
double-entry (one debit, one credit, equal amounts), matching the invariant
`journal_entries` already enforces via its `amount > 0` and
`debit_account_id != credit_account_id` check constraints.
**Scale/Scope**: Same single-business, single-admin, low-volume scope as
prior features — one income entry has at most one active journal entry at
a time (mirrors the expense-entry/journal-entry cardinality).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written via `/sp.specify`, spec-quality checklist passed, before this plan |
| II. Deterministic Financial Computation | ✅ PASS | No AI involvement at all in this feature (explicit scope exclusion); every journal-entry amount is a direct copy of `IncomeEntry.amount` by deterministic service code; `reporting_service.py` is untouched, so its existing determinism guarantee extends automatically to income data |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS (N/A) | This principle targets AI-derived/high-risk actions (audit flags, fraud detection, tax summaries, below-threshold codings); a manually-entered income record is already a direct human statement of fact with no AI suggestion step, so no review-queue gate applies — documented explicitly in spec.md's Assumptions |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `010-income-entry`, branched from `origin/main`; will merge only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new UI → API → DB path (income entry → journal posting) alongside the existing expense path; the workflow diagram (`docs/workflow-diagram.drawio`) must be updated to show it before this feature's PR merges |
| VI. Simplicity & Traceability | ✅ PASS | Reuses the existing `journal_entries` table via a minimal nullable-column generalization instead of building a parallel ledger table; no AI tool, no new services beyond what's needed for CRUD + posting; traceable via this plan, `research.md`, and PHRs |

**Gate result**: PASS with one tracked action item (V — diagram update), not
a violation requiring justification — no entry needed in Complexity
Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/010-income-entry/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── income-api.md     # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── income_source.py         # NEW: SQLAlchemy model (source -> account mapping)
│   │   ├── income_entry.py          # NEW: SQLAlchemy model
│   │   └── journal_entry.py         # MODIFIED: expense_entry_id/account_coding_id become
│   │                                 #   nullable, income_entry_id added (see data-model.md)
│   ├── schemas/
│   │   ├── income_source.py         # NEW: Pydantic request/response models
│   │   ├── income_entry.py          # NEW
│   │   └── journal_entry.py         # MODIFIED: expense_entry_id optional, income_entry_id added
│   ├── services/
│   │   ├── income_source_service.py # NEW: list/create income sources (+ their mapped account)
│   │   ├── income_entry_service.py  # NEW: create/list/get/update/delete income entries
│   │   └── ledger_service.py        # MODIFIED: generalize reverse_journal_entry to carry
│   │                                 #   income_entry_id; add post_income_journal_entry,
│   │                                 #   reverse_journal_entry_for_income
│   └── api/
│       ├── income_sources.py        # NEW: /api/income-sources routes
│       ├── income.py                # NEW: /api/income routes
│       └── expenses.py              # UNCHANGED
├── migrations/                       # NEW: generalize journal_entries; add income_sources,
│                                     #   income_entries; seed starter income sources + accounts
└── tests/
    ├── contract/                     # one test file per contracts/income-api.md endpoint
    ├── integration/                  # per-user-story flows (US1-US3), including a
    │                                 #   report-reflects-income integration test
    └── unit/                         # income_entry_service + ledger_service posting/reversal

frontend/
├── src/
│   ├── components/
│   │   ├── IncomeForm.tsx            # NEW: mirrors ExpenseForm.tsx (US1)
│   │   └── IncomeList.tsx            # NEW: mirrors ExpenseList.tsx, filterable (US2)
│   ├── app/
│   │   └── income/                   # NEW: page wiring the above components
│   └── services/
│       └── incomeApi.ts              # NEW: typed client for contracts/income-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories rather than creating new top-level projects — additive on top
of the same stack, reusing the established layout (`models/`, `schemas/`,
`services/`, `api/`). The one integration point touching already-shipped
code is `journal_entries` (model, schema, and `ledger_service.py`'s
`reverse_journal_entry`) gaining an `income_entry_id` alongside the
existing `expense_entry_id` — the same kind of small, explicit touch
`002-ledger-journal-entries` made to `expenses.py`'s DELETE handler.
`reporting_service.py`, `schemas/reports.py`, and `api/reports.py` require
**no changes** — they already aggregate generically over
`journal_entries` + `accounts`.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception.*
