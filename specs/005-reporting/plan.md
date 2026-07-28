# Implementation Plan: Financial Reporting (Trial Balance, P&L, Balance Sheet, Cash Flow)

**Branch**: `005-reporting` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-reporting/spec.md`

## Summary

Four read-only financial statements (Trial Balance, Profit & Loss, Balance
Sheet, Cash Flow), each computed on demand from the existing `accounts` and
`journal_entries` tables the Ledger feature (`002`) already maintains — no
new persisted entities. Technical approach: a single `reporting_service.py`
module does all aggregation as plain SQLAlchemy `SUM`/`GROUP BY` queries
(deterministic, auditable SQL — no pandas needed for sums this simple, see
`research.md`); each report is exposed as a direct REST endpoint; a second,
narrow AI path lets an admin ask for a report in natural language
("how did we do last quarter") — a small LLM call resolves *only* which
report and which date/period is meant, the backend calls the exact same
deterministic function the direct endpoint uses, and a second LLM call
narrates the already-computed numbers in prose. The AI never sees raw
ledger rows and never touches a number before or after it is computed —
this is Constitution Principle II applied for the first time to a
reporting surface rather than a posting/matching one.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as prior features
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async),
OpenAI Agents SDK (GPT-4o mini) — all already in use, **no new backend
dependency required**; Next.js (App Router), React — frontend.
**Storage**: PostgreSQL — reads only, no schema change. Every report is
computed from the existing `accounts` and `journal_entries` tables (`002`);
no new tables, no migration.
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: Each report is a single aggregate SQL query over a
single business's full journal-entry history (realistically low thousands
of rows for the lifetime of a small business) — sub-second, not a
performance-sensitive path. The narrate/resolve LLM calls are
latency-bound the same as other single-shot agent calls in this codebase
(~2-3s p95 once warm).
**Constraints**: Every number in every report response MUST originate from
a SQL aggregation in `reporting_service.py` — the AI layer (`reporting_tools.py`)
MUST NOT receive raw journal-entry rows to sum itself, and MUST NOT be the
source of any digit that appears in a response (constitution Principle II).
The natural-language path's resolve step and narrate step are two separate,
narrowly-scoped LLM calls — neither is given write access or a broader task
than its single job.
**Scale/Scope**: Single business, single admin user, single currency — same
scope as prior features. Four report types, each a single deterministic
calculation function plus one shared "which entries count" filter.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and its quality checklist passed before this plan |
| II. Deterministic Financial Computation | ✅ PASS | All four reports are pure SQL aggregation in `reporting_service.py`; the AI's `resolve_report_request` only classifies report-type/date-range from free text (never sees ledger data), and `narrate_report` only receives the already-computed result object to describe in prose (never raw rows) — mirrors `adjudicate_match`'s "never sees the full table" precedent from `004` |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | N/A | This feature has no posting, matching, or auto-finalizing action to gate — it is read-only reporting; nothing here writes to the ledger or requires sign-off |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `005-reporting`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI flow (`resolve_report_request` / `narrate_report`) and new report endpoints — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | No new tables; reuses `Account`/`JournalEntry` as-is. Chose plain SQL `SUM`/`GROUP BY` over adding `pandas` — the aggregations needed (per-account debit/credit sums, optionally date-filtered) are exactly what SQL `GROUP BY` already does, so a new dependency would add complexity without adding capability (see `research.md`). Reused the existing single-shot-JSON LLM-call pattern (`suggest_account_coding`, `adjudicate_match`) rather than introducing OpenAI Agents SDK function-tool-calling machinery not used anywhere else in this codebase |

**Gate result**: PASS with one tracked action item (V — diagram update), not
a violation requiring justification — no entry needed in Complexity
Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/005-reporting/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── reports-api.md   # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── schemas/
│   │   └── reports.py               # NEW: Pydantic response models for all 4 reports + shared line-item schema
│   ├── services/
│   │   └── reporting_service.py     # NEW: trial_balance / profit_and_loss / balance_sheet / cash_flow — pure SQL aggregation
│   ├── agent/
│   │   └── reporting_tools.py       # NEW: resolve_report_request (NL → report type + date/range) and narrate_report (result → prose)
│   └── api/
│       ├── reports.py               # NEW: GET /api/reports/{trial-balance,profit-and-loss,balance-sheet,cash-flow}
│       └── agent.py                 # MODIFIED: add POST /api/agent/reports/query (natural-language report request)
└── tests/
    ├── contract/                    # one test file per contracts/reports-api.md endpoint
    ├── integration/                 # per-user-story flows (US1-US4), including the reversed-entry edge case
    └── unit/                        # reporting_service aggregation logic (deterministic, easy to unit test with fixed fixtures)

frontend/
├── src/
│   ├── components/
│   │   ├── ReportViewer.tsx         # NEW: report-type selector + date/range picker + rendered statement table (US1-US4)
│   │   └── ReportQuery.tsx          # NEW: free-text "ask for a report" box + narrated answer (FR-007's chat path)
│   ├── app/
│   │   └── reports/                 # NEW: page wiring the above components
│   └── services/
│       └── reportsApi.ts            # NEW: typed client for contracts/reports-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories, following the pattern established by `002`–`004` — additive on
top of the same stack and the existing `accounts`/`journal_entries` tables,
with no new top-level project. One new frontend route (`/reports`) and nav
link, matching how `/ledger` (`002`) and `/reconciliation` (`004`) were
added. `api/agent.py` is extended in place (rather than adding a new agent
router) since it is already this codebase's single home for every
agent-mediated endpoint.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception.*
