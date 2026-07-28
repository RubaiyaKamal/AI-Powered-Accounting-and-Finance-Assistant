# Implementation Plan: Analysis & Advisory / Natural-Language Q&A

**Branch**: `009-analysis-advisory` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-analysis-advisory/spec.md`

## Summary

Let an admin ask natural-language spending questions ("how much did we
spend on utilities in March?"), view spending breakdowns and
period-over-period comparisons directly, and request a spending forecast
— all backed entirely by deterministic computation. Technical approach:
a single narrow LLM call classifies a question into one of four fixed
request kinds (amount, breakdown, comparison, forecast) plus its
parameters (an account name drawn only from the real chart of accounts,
and one or two date periods) — this is *not* free-form LLM-authored SQL;
the classification result is handed to plain Python functions that reuse
`ReportingService.profit_and_loss` for every actual figure, exactly the
way `005-reporting` already computes them. Forecasting fits a simple
linear trend (`scikit-learn`'s `LinearRegression`, already a dependency
since `007`) over recent months' actual `profit_and_loss` totals — no new
dependency. A second narrow LLM call narrates the already-computed result
in prose, always labeling a forecast as an estimate. This is the fourth
application of the "deterministic computation, LLM classifies and
narrates only" split this project has now established (`005`, `007`,
`008`), and deliberately rejects the literal "LLM writes SQL" reading of
this feature's named method, since that would reintroduce exactly the
class of bug (a subtly wrong or incomplete filter) this codebase has
worked to keep out by reusing one shared, carefully-written
active-postings filter everywhere.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as prior features
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — all already in use. **No new
dependency**: forecasting reuses `scikit-learn` (`LinearRegression`),
already present since `007`'s anomaly detector; no embeddings or vector
work is needed here.
**Storage**: PostgreSQL — no new tables. Every answer, breakdown,
comparison, and forecast is computed fresh from the existing `accounts`
and `journal_entries` tables (`002`), the same way `005-reporting`
operates — nothing here is persisted (spec's Key Entities section states
this explicitly; no review/sign-off lifecycle applies, since Analysis &
Advisory is not one of Principle III's named regulated-action examples).
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses
the existing `backend`/`frontend`/`db` services)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: Every direct computation (breakdown, comparison,
one or two `profit_and_loss` calls) is a single fast SQL aggregation,
sub-second at this project's realistic scale. A forecast fits a linear
regression over at most a handful of monthly `profit_and_loss` calls
(~6), still comfortably sub-second. The dominant cost is the LLM
classification + narration round-trip (~2-4s p95, same order as every
other agent call in this codebase), well within spec's 15-second target
(SC-002).
**Constraints**: Every numeric figure MUST come from
`ReportingService.profit_and_loss` — the AI layer (`analysis_tools.py`)
MUST NOT receive raw journal-entry rows and MUST NOT be the source of any
figure, including a forecasted one. Account-name resolution MUST be
bounded to the real chart of accounts (the LLM picks from a given list or
returns none — mirrors `suggest_account_coding`'s established pattern —
never invents an account). A forecast MUST always be labeled an estimate
in the response, never presented as a certain figure.
**Scale/Scope**: Single business, single admin user, single currency —
same scope as prior features. Four fixed, bounded request kinds — not
open-ended analytical Q&A.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and its quality checklist passed before this plan |
| II. Deterministic Financial Computation | ✅ PASS | Every figure (amount, breakdown line, comparison delta, forecast value) is produced by `reporting_service.profit_and_loss` or a deterministic linear-regression fit over its own past outputs — never the LLM; `resolve_spending_request` only classifies intent/parameters (never sees ledger data), `narrate_spending_result` only narrates an already-computed result object (never raw rows) — mirrors `narrate_report`/`narrate_audit_run`/`draft_summary_narrative`'s exact pattern |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | N/A | Analysis & Advisory is not named among Principle III's regulated/high-risk examples (audit anomaly flags, fraud detection, tax/compliance summaries) — this feature is read-only informational Q&A with no posting, matching, or filing action to gate |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `009-analysis-advisory`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI flow (`resolve_spending_request`/`narrate_spending_result`) and a new deterministic forecaster — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | No new dependency — reuses `scikit-learn` (already present) for a simple linear-trend forecast rather than a heavier time-series library (`statsmodels`, `prophet`), which this project's realistic data volume (a handful to dozens of months) doesn't justify; reuses `reporting_service.profit_and_loss` for every figure rather than duplicating aggregation logic; explicitly rejected literal free-form LLM-authored SQL (the Input's literal "text-to-SQL" phrasing) in favor of a bounded classify-then-compute split, reusing this codebase's one existing, carefully-scoped active-postings computation rather than letting the LLM construct new queries per question |

**Gate result**: PASS with one tracked action item (V — diagram update),
not a violation requiring justification — no entry needed in Complexity
Tracking.

📋 **Architectural decision detected**: rejecting the literal "resolve
questions into free-form LLM-authored SQL" reading of this feature's
named method, in favor of a bounded classify-then-compute split that
reuses `reporting_service.profit_and_loss` for every figure, plus
adopting a simple linear-regression forecaster (`scikit-learn`, no new
dependency) over a fixed recent-months window. This has long-term
consequences (sets the pattern for how "ask anything about the ledger"
requests are safely bounded in this codebase going forward), real
alternatives were considered and rejected (free-form SQL generation, a
heavier time-series library), and it's cross-cutting to how every one of
this feature's four request kinds gets its numbers. **Document reasoning
and tradeoffs?** Run `/sp.adr spending-qa-query-approach`. (Consent
required before creation — not created automatically.)

## Project Structure

### Documentation (this feature)

```text
specs/009-analysis-advisory/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── analysis-api.md  # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── schemas/
│   │   └── analysis.py               # NEW: Pydantic response models (breakdown, comparison, forecast, query)
│   ├── services/
│   │   └── analysis_service.py       # NEW: breakdown/comparison/forecast computation, all via reporting_service.profit_and_loss
│   ├── agent/
│   │   └── analysis_tools.py         # NEW: resolve_spending_request (NL → intent + params, bounded to real accounts), narrate_spending_result
│   └── api/
│       ├── analysis.py               # NEW: GET /api/analysis/{breakdown,comparison,forecast}
│       └── agent.py                  # MODIFIED: add POST /api/agent/analysis/query (handles all four request kinds, including single-amount, which has no direct REST equivalent per spec's US1 wording)
└── tests/
    ├── contract/                     # one test file per contracts/analysis-api.md endpoint
    ├── integration/                  # per-user-story flows (US1-US4)
    └── unit/                         # forecast regression logic, deterministic given fixed fixtures

frontend/
├── src/
│   ├── components/
│   │   ├── SpendingQuery.tsx         # NEW: free-text question box + narrated answer (US1, US4)
│   │   ├── SpendingBreakdown.tsx     # NEW: period picker + ranked breakdown + period-comparison view (US2)
│   │   └── SpendingForecast.tsx      # NEW: future-period picker + forecast + method explanation (US3)
│   ├── app/
│   │   └── analysis/                 # NEW: page wiring the above components
│   └── services/
│       └── analysisApi.ts            # NEW: typed client for contracts/analysis-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories, following the pattern established by `002`–`008` — additive
on top of the same stack and reusing `reporting_service.profit_and_loss`
rather than introducing parallel aggregation logic. One new frontend
route (`/analysis`) and nav link, matching how `/reports`, `/audit`, and
`/tax` were each added. `api/agent.py` is extended in place for the one
agent-mediated endpoint, per the established "all agent-mediated
endpoints live in api/agent.py" rule — unlike prior features, this
endpoint is the *sole* delivery mechanism for the single-amount request
kind (US1), since spec.md describes that capability only via natural
language, with no separate direct-form equivalent requested.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram
update) is tracked as a task, not a constitutional exception. The
query-approach and forecasting-method decisions are tracked as a
suggested ADR above, not Complexity Tracking violations, since both
directly satisfy explicit functional requirements (FR-002, FR-008)
without adding a new dependency.*
