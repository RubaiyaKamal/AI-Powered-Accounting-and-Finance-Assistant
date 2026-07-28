# Implementation Plan: Bank/Vendor Reconciliation

**Branch**: `004-bank-reconciliation` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-bank-reconciliation/spec.md`

## Summary

Let an admin upload a bank statement CSV, have each transaction line
automatically matched to the expense entry it corresponds to (or flagged
for review), and resolve anything ambiguous or unmatched through a review
queue. Technical approach: a new `bank_transactions` and `matches` table;
deterministic matching (exact amount, date-proximity window, and
description fuzzy-string similarity via `rapidfuzz`) decides confident
auto-matches without any AI involvement; a new `adjudicate_match` agent
tool is invoked only when multiple candidates are plausible but no single
one clears the auto-match bar, returning a chosen candidate (or none) plus
its reasoning for the admin to review — never silently deciding on its
own. This is the same "deterministic first, AI only for genuine ambiguity"
split the ledger-coding feature (`002`) already established.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as prior features
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — backend; Next.js (App Router),
React — frontend; **new**: `rapidfuzz` (lightweight, pure-Python/C
string-similarity library) for description matching — CSV parsing uses
Python's built-in `csv` module, no new dependency needed for that.
**Storage**: PostgreSQL — two new tables, `bank_transactions` and
`matches` (see `data-model.md`), referencing the existing `expense_entries`
table from `001-expense-entry`.
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services — no new services needed)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: CSV import + matching pass for a typical month's
statement (tens to low hundreds of lines) completes well under a few
seconds — matching itself is a deterministic in-process computation, not
LLM-latency-bound; only the (comparatively rare) ambiguous-adjudication
path is LLM-latency-bound, same order as other agent calls (~3s p95 once
warm).
**Constraints**: The match-scoring computation (amount/date/description
comparison, confident-vs-ambiguous-vs-none classification) MUST be
deterministic application code — the AI is invoked only to adjudicate
between already-identified plausible candidates when the deterministic
score can't confidently pick one, and even then it only *chooses among*
candidates the deterministic pass already found plausible; it never
invents a match on its own (constitution Principle II — no financial
linkage decided by unmediated LLM output).
**Scale/Scope**: Single business, single admin user, low volume (a
month's bank statement is realistically tens to low hundreds of lines) —
same scope as prior features.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and clarified via `/sp.specify`'s interactive Q&A before this plan |
| II. Deterministic Financial Computation | ✅ PASS | Match scoring (amount/date/description) is deterministic Python; `adjudicate_match` only *chooses among* deterministically-identified candidates and explains its choice — it never computes a match from scratch or writes a match directly, matching the exact pattern `suggest_account_coding` already established in `002` |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS | Ambiguous adjudications and fully-unmatched transactions both route to the review queue rather than auto-resolving (FR-006, FR-007) — the constitution's explicit example of what this principle requires |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `004-bank-reconciliation`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI tool (`adjudicate_match`) and a new CSV-import flow — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | Reuses the existing `Expense Entry` entity rather than reconciling against ledger/Cash movements (spec Assumptions); one-to-one matching only, no split/bulk-matching complexity; `Match` rows are hard-deleted on undo or on cascade when their expense entry is deleted — no reversal-entry audit trail, since (unlike `002`'s journal entries) a reconciliation match isn't itself a financial posting, just an operational link |

**Gate result**: PASS with one tracked action item (V — diagram update), not
a violation requiring justification — no entry needed in Complexity
Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/004-bank-reconciliation/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── reconciliation-api.md   # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── bank_transaction.py     # NEW: SQLAlchemy model
│   │   └── match.py                 # NEW: SQLAlchemy model
│   ├── schemas/
│   │   ├── bank_transaction.py     # NEW: Pydantic request/response models
│   │   └── match.py                 # NEW
│   ├── services/
│   │   └── reconciliation_service.py # NEW: CSV parsing, matching algorithm, review-queue resolution
│   ├── agent/
│   │   └── reconciliation_tools.py  # NEW: adjudicate_match tool def
│   └── api/
│       └── reconciliation.py        # NEW: /api/reconciliation/* routes
├── migrations/                       # Alembic migration adding bank_transactions/matches
└── tests/
    ├── contract/                     # one test file per contracts/reconciliation-api.md endpoint
    ├── integration/                  # per-user-story flows (US1-US3)
    └── unit/                         # match-scoring algorithm tests (deterministic, easy to unit test)

frontend/
├── src/
│   ├── components/
│   │   ├── BankStatementImport.tsx   # NEW: CSV upload control + import result summary (US1)
│   │   └── ReconciliationQueue.tsx   # NEW: matched list + review queue with AI reasoning (US2, US3)
│   ├── app/
│   │   └── reconciliation/           # NEW: page wiring the above components
│   └── services/
│       └── reconciliationApi.ts      # NEW: typed client for contracts/reconciliation-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories rather than creating new top-level projects, following the
pattern established by `002` and `003` — this feature is additive on top
of the same stack and the existing `expense_entries` table. One new
top-level frontend route (`/reconciliation`) and nav link, matching how
`/ledger` was added in `002`.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception.*
