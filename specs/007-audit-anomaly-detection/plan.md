# Implementation Plan: Audit & Anomaly Detection (Fraud/Anomaly Flags)

**Branch**: `007-audit-anomaly-detection` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-audit-anomaly-detection/spec.md`

## Summary

Let an admin trigger an audit over a chosen date range and see the posted
journal entries that stand out as statistically unusual, each with a
plain-language reason. Technical approach: a hybrid detector —
`scikit-learn`'s `IsolationForest` (unsupervised outlier scoring over
amount/account/timing features) combined with two deterministic rule
checks (exact-duplicate detection, round-number detection) — computes every
flag and its ranking in `audit_service.py`; a single batched LLM call per
audit run narrates the already-computed flags in plain language (never
decides which entries are anomalous). Flags and audit runs persist
(`audit_runs`, `anomaly_flags` tables) so an admin can record a resolution
per flag and revisit past runs. This is the same "deterministic
computation, LLM narrates only" split `005-reporting` established, and the
same "review queue, no auto-action" pattern `004-bank-reconciliation`
established — applied here to Principle III's explicit "audit anomaly
flags... MUST be presented for human review" requirement.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as prior features
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — all already in use; **new**:
`scikit-learn` (`IsolationForest`) for unsupervised outlier scoring — this
project's first ML dependency (pulls in `numpy` transitively; no other new
ML library is introduced — see `research.md`).
**Storage**: PostgreSQL — two new tables, `audit_runs` and `anomaly_flags`
(see `data-model.md`), referencing the existing `journal_entries` table
from `002-ledger-journal-entries`.
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: An audit run over a typical small business's full
ledger history (realistically low thousands of rows) fits and scores an
`IsolationForest` in well under a second — the dominant cost is the single
batched LLM narration call per run (~2-4s p95), keeping every run
comfortably under spec's 30-second target (SC-001) regardless of how many
entries it flags, since narration is one call per run, not one per flag.
**Constraints**: Every anomaly flag and its ranking MUST originate from the
deterministic detector (`audit_service.py`) — the AI layer
(`audit_tools.py`) MUST NOT receive the full unflagged ledger to score
itself, MUST NOT decide which entries are anomalous, and MUST NOT be the
source of any flag that isn't traceable to the detector's own output
(constitution Principle II, extended from financial figures to anomaly
judgments). Audit anomaly flags MUST be presented for human review and
MUST NOT be auto-finalized or trigger any automatic action (constitution
Principle III, which names this exact feature).
**Scale/Scope**: Single business, single admin user, single currency —
same scope as prior features. One hybrid detection pass (ML outlier score
+ two rule-based checks) per audit run; audit runs and their flags persist
for later review.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and its quality checklist passed before this plan |
| II. Deterministic Financial Computation | ✅ PASS (extended) | Anomaly flags aren't financial figures, but the same discipline applies: every flag/score comes from `audit_service.py`'s `IsolationForest` + rule checks; the LLM (`explain_flags`) receives only the already-computed flag list to narrate, never raw unflagged ledger rows, and never assigns or alters a score — mirrors `narrate_report`'s exact pattern from `005` |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS | This constitution explicitly names "audit anomaly flags, fraud-pattern detection" as requiring human review and prohibiting auto-finalization — FR-006's resolution workflow (confirmed issue / false positive / no action needed) is exactly that gate; flags never block, reverse, or auto-correct a journal entry (spec Assumptions) |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `007-audit-anomaly-detection`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI flow (`resolve_audit_request` / `explain_flags`) and new audit endpoints — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | `scikit-learn` is a new dependency, but it directly satisfies FR-001's explicit requirement for unsupervised ML-based detection (named by the feature request itself) rather than being spec-independent abstraction; the model is fit fresh per audit run (no persisted/versioned model, no retraining pipeline) — the simplest approach that still satisfies the spec, avoiding model-lifecycle complexity this project's scale doesn't need (see `research.md`) |

**Gate result**: PASS with one tracked action item (V — diagram update),
not a violation requiring justification — no entry needed in Complexity
Tracking. The `scikit-learn` dependency addition is a genuine first for
this codebase (new dependency *category*, not just a new package) and is
flagged below as a suggested Architecture Decision Record.

📋 **Architectural decision detected**: adopting `scikit-learn`'s
`IsolationForest` (this project's first ML/statistics dependency) as the
anomaly-scoring engine, combined with deterministic rule-based checks, and
fitting the model fresh per audit run rather than persisting a trained
model. This has long-term consequences (dependency footprint, a new
"detector" pattern future audit features may extend), multiple viable
alternatives were considered (pure rule-based statistics, clustering/DBSCAN,
a persisted/retrained model), and it's cross-cutting to how this feature's
core detection works. **Document reasoning and tradeoffs?** Run
`/sp.adr anomaly-detection-approach`. (Consent required before creation —
not created automatically.)

## Project Structure

### Documentation (this feature)

```text
specs/007-audit-anomaly-detection/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── audit-api.md     # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── audit_run.py             # NEW: SQLAlchemy model
│   │   └── anomaly_flag.py          # NEW: SQLAlchemy model
│   ├── schemas/
│   │   └── audit.py                 # NEW: Pydantic request/response models for audit runs + flags
│   ├── services/
│   │   └── audit_service.py         # NEW: feature extraction, IsolationForest + rule-based detection, persistence, resolution
│   ├── agent/
│   │   └── audit_tools.py           # NEW: resolve_audit_request (NL → date range) and explain_flags (flag list → prose, batched per run)
│   └── api/
│       ├── audit.py                 # NEW: GET/POST /api/audit/* routes (run audit, list history, get run, resolve flag)
│       └── agent.py                 # MODIFIED: add POST /api/agent/audit/query (natural-language audit request)
├── migrations/                       # Alembic migration adding audit_runs/anomaly_flags
└── tests/
    ├── contract/                     # one test file per contracts/audit-api.md endpoint
    ├── integration/                  # per-user-story flows (US1-US4), including the reversed-entry and low-data edge cases
    └── unit/                         # detector logic (deterministic given a fixed random seed, easy to unit test with fixed fixtures)

frontend/
├── src/
│   ├── components/
│   │   ├── AuditRunner.tsx          # NEW: date-range picker + run button + ranked flagged-entry list with resolution controls (US1, US2)
│   │   └── AuditHistory.tsx         # NEW: past audit runs list, reopen a run's results (US3)
│   ├── app/
│   │   └── audit/                   # NEW: page wiring the above components
│   └── services/
│       └── auditApi.ts              # NEW: typed client for contracts/audit-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories, following the pattern established by `002`–`005` — additive
on top of the same stack and the existing `journal_entries` table, with
two new persisted tables (this feature needs state across runs, unlike
`005`'s fully-computed-on-demand reports). One new frontend route
(`/audit`) and nav link, matching how `/reports` (`005`) and
`/reconciliation` (`004`) were added. `api/agent.py` is extended in place
(rather than a new agent router) since it remains this codebase's single
home for every agent-mediated endpoint (established in `005`'s
research.md).

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception. The new
`scikit-learn` dependency is tracked as a suggested ADR above, not a
Complexity Tracking violation, since it directly satisfies an explicit
functional requirement rather than being discretionary complexity.*
