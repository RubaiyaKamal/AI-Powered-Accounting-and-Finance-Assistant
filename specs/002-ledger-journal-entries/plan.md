# Implementation Plan: Ledger & Journal Entries

**Branch**: `002-ledger-journal-entries` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-ledger-journal-entries/spec.md`

## Summary

Let an admin get an AI-suggested chart-of-accounts coding (with a confidence
score) for each expense entry, review/approve/correct it, and have the
system post a balanced double-entry (debit/credit) journal entry against the
chart of accounts — automatically for high-confidence suggestions, gated by
mandatory review below the confidence threshold. Technical approach: extend
the existing FastAPI + SQLAlchemy (async) + PostgreSQL backend with
`accounts`, `account_codings`, and `journal_entries` tables; a new
`suggest_account_coding` OpenAI Agents SDK tool returns a suggested account
name and confidence score (never a number to post — see Principle II); the
actual debit/credit posting, balance check, and reversal-on-correction logic
are deterministic Python service code, never LLM output.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as `001-expense-entry`, no new languages
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — backend; Next.js (App Router),
React — frontend; `uv` (backend) / `npm` (frontend)
**Storage**: PostgreSQL — new tables `accounts`, `account_codings`,
`journal_entries` (see `data-model.md`), referencing the existing
`expense_entries` table from `001-expense-entry`
**Testing**: pytest + httpx async client (backend contract/integration
tests); Vitest + React Testing Library (frontend component tests) — same
tooling as `001-expense-entry`
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services in `docker-compose.yml` — no new
services needed)
**Project Type**: web (frontend + backend split, same repo layout as
`001-expense-entry`)
**Performance Goals**: Coding-suggestion + auto-post round trip is
LLM-latency-bound, target under 3s p95 (same order as
`POST /api/agent/expenses/parse` in the expense-entry feature); journal
listing/filtering queries well under 1s p95 (deterministic DB query, no LLM
involved)
**Constraints**: No debit/credit amount may ever be produced by the LLM as
free text — the AI tool returns only a suggested account name + confidence
score; the actual journal-entry amounts are always copied deterministically
from the source expense entry's amount by application code (constitution
Principle II). Below-threshold codings and any journal-affecting correction
MUST NOT auto-finalize without being representable as a reviewable state
(constitution Principle III).
**Scale/Scope**: Same single-business, single-admin, low-volume scope as
`001-expense-entry` — one coding and at most one active journal entry per
expense entry at a time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and clarified via `/sp.specify`'s interactive Q&A before this plan |
| II. Deterministic Financial Computation | ✅ PASS | `suggest_account_coding` (the only new AI tool) returns an account name + confidence score, never an amount; journal-entry amounts are always copied from `ExpenseEntry.amount` by service code (FR-007); balance (debit == credit) is asserted in code, not trusted from the LLM |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS | Below-threshold codings route to mandatory review before posting (FR-005), matching the constitution's explicit example ("journal postings... below a configured confidence threshold MUST route to a review queue"); above-threshold auto-posting was an explicit, informed user choice during `/sp.specify` clarification, not a silent default |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `002-ledger-journal-entries`; will merge to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI tool (`suggest_account_coding`) and a new automatic-posting flow — the existing workflow diagram (`docs/workflow-diagram.drawio`) must be updated to reflect it before this feature's PR merges, per Principle V's "any change that alters how a request moves between frontend, backend, agent, and database MUST update the diagram in the same pull request" |
| VI. Simplicity & Traceability | ✅ PASS | No speculative abstractions (single fixed offset account for the credit side — see `research.md`; no multi-currency, no multi-line journal entries beyond one debit/one credit pair); traceable via this plan, `research.md`, and PHRs |

**Gate result**: PASS with one tracked action item (V — diagram update), not
a violation requiring justification — no entry needed in Complexity
Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-ledger-journal-entries/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── ledger-api.md     # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── account.py               # NEW: SQLAlchemy model (chart of accounts)
│   │   ├── account_coding.py        # NEW: SQLAlchemy model (expense entry -> account link)
│   │   └── journal_entry.py         # NEW: SQLAlchemy model (posted double-entry record)
│   ├── schemas/
│   │   ├── account.py               # NEW: Pydantic request/response models
│   │   ├── account_coding.py        # NEW
│   │   └── journal_entry.py         # NEW
│   ├── services/
│   │   ├── account_service.py       # NEW: list/create accounts
│   │   └── ledger_service.py        # NEW: suggest/approve/correct coding, post/reverse journal entries
│   ├── agent/
│   │   └── ledger_tools.py          # NEW: suggest_account_coding tool def (mirrors expense_tools.py's suggest_category)
│   └── api/
│       ├── accounts.py              # NEW: /api/accounts routes
│       └── ledger.py                # NEW: /api/expenses/{id}/coding, /api/journal-entries routes
├── migrations/                       # Alembic migration adding accounts/account_codings/journal_entries + seed chart of accounts
└── tests/
    ├── contract/                     # one test file per contracts/ledger-api.md endpoint
    ├── integration/                  # per-user-story flows (US1-US3)
    └── unit/                         # ledger_service balance/reversal logic

frontend/
├── src/
│   ├── components/
│   │   ├── AccountCoding.tsx         # NEW: shows suggestion+confidence, approve/correct controls (US1)
│   │   └── JournalEntryList.tsx      # NEW: filterable ledger view (US3)
│   ├── app/
│   │   └── ledger/                   # NEW: page wiring the above components
│   └── services/
│       └── ledgerApi.ts              # NEW: typed client for contracts/ledger-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories from `001-expense-entry` rather than creating new top-level
projects — this feature is additive on top of the same stack and the same
`expense_entries` table, so it reuses the established layout (`models/`,
`schemas/`, `services/`, `agent/`, `api/`) instead of inventing a new one.
One existing file requires a small, explicit touch: `backend/src/api/expenses.py`'s
`DELETE /api/expenses/{id}` handler gains a call into the new
`ledger_service.reverse_journal_entry_for_expense(...)` (FR-012) — this is
the one integration point where this feature must modify already-shipped
code, and it is a single function call, not a restructuring.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception.*
