# Implementation Plan: Tax & Compliance Summaries

**Branch**: `008-tax-compliance-summaries` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-tax-compliance-summaries/spec.md`

## Summary

Let an admin maintain a small library of their own tax-rule reference
documents, then request a draft tax/compliance summary for a chosen
period. Technical approach: each reference document is chunked into
paragraph-sized passages and embedded once at add-time (OpenAI embeddings,
via the `openai` client already present as a transitive dependency of
`openai-agents` — no new package); a summary request embeds the query,
ranks passages by in-process cosine similarity (`numpy`, already present
via `007`'s `scikit-learn`), and reuses `ReportingService.profit_and_loss`
verbatim for the period's figures — no new financial computation. A
single narrow LLM call drafts the narrative from the already-computed
figures and already-retrieved passages only. Every draft is persisted
with its figures and cited passages frozen onto the row (not live
references), stays labeled a draft until the admin explicitly signs off,
and sign-off is blocked if the period's figures have since changed. This
is the same "deterministic computation + AI narrates only" split `005`
and `007` established, now paired with a retrieval step ahead of
generation, and the same "review before final" gate `007` established —
applied here to Principle III's other explicitly named example.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as prior features
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini) — all already in use. **No new
dependency**: the OpenAI embeddings API is called via the `openai` Python
client already installed transitively through `openai-agents`; cosine
similarity is computed with `numpy`, already present since `007`'s
`scikit-learn` dependency.
**Storage**: PostgreSQL — three new tables: `tax_rules_documents`,
`tax_rules_document_chunks` (one row per paragraph-sized passage, with a
nullable embedding column), and `tax_summaries` (see `data-model.md`).
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses
the existing `backend`/`frontend`/`db` services)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: Retrieval over a realistic reference library (a
single admin's own documents — realistically tens of documents, at most a
few hundred chunks) via brute-force in-process cosine similarity is
sub-second; draft generation is dominated by one LLM narration call
(~2-4s p95, same order as other single-shot agent calls in this codebase),
comfortably under spec's 30-second target (SC-004).
**Constraints**: Every financial figure in a summary MUST come from
`ReportingService.profit_and_loss` (reused, not reimplemented) — the AI
layer (`tax_tools.py`) MUST NOT receive raw journal-entry rows and MUST
NOT be the source of any figure. Every cited passage MUST be an actual
retrieved chunk — the narration call receives only already-retrieved
passages, never the full document library. A draft MUST NOT be signed off
if the period's figures have changed since it was generated (FR-009),
checked by recomputing and comparing at sign-off time. A signed-off
summary's figures and cited passages MUST be frozen onto its own row, not
live references to documents/chunks that could later change or be removed
(FR-007, spec Edge Cases).
**Scale/Scope**: Single business, single admin user, single currency —
same scope as prior features. One retrieval pass + one narration call per
summary request; summaries persist for review and history.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and its quality checklist passed before this plan |
| II. Deterministic Financial Computation | ✅ PASS (extended) | Figures are `ReportingService.profit_and_loss`'s own output, reused verbatim; passage retrieval (embedding similarity or keyword-overlap fallback) is deterministic non-LLM scoring; the one LLM call (`draft_summary_narrative`) receives only already-computed figures and already-retrieved passages, never ledger rows or the full library — mirrors `narrate_report`/`narrate_audit_run`'s exact pattern |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS | This constitution explicitly names "tax/compliance summaries" as requiring human review and prohibiting auto-finalization — FR-006/007/008's draft-until-signed-off gate, plus FR-009's stale-draft sign-off block, are exactly this requirement |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `008-tax-compliance-summaries`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a retrieval step and new AI tools (`draft_summary_narrative`, `resolve_summary_request`) — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | No new dependency — reuses the `openai` client already present and `numpy` already present; chose in-process brute-force cosine similarity over `pgvector` or a dedicated vector store, since this project's realistic scale (one admin's own reference library) doesn't need indexed approximate search; reuses `profit_and_loss` rather than duplicating financial computation |

**Gate result**: PASS with one tracked action item (V — diagram update),
not a violation requiring justification — no entry needed in Complexity
Tracking.

📋 **Architectural decision detected**: adopting in-process
embedding-based retrieval (OpenAI embeddings + brute-force cosine
similarity via `numpy`) as this project's first retrieval/RAG pattern,
with a deterministic keyword-overlap fallback when no `OPENAI_API_KEY` is
configured, rather than a dedicated vector database or extension. This
has long-term consequences (establishes how any future retrieval-based
feature in this codebase would likely work), multiple viable alternatives
were considered (`pgvector`, a dedicated vector service, keyword-only
retrieval), and it's a new architectural pattern even though it
introduces no new dependency. **Document reasoning and tradeoffs?** Run
`/sp.adr tax-summary-retrieval-approach`. (Consent required before
creation — not created automatically.)

## Project Structure

### Documentation (this feature)

```text
specs/008-tax-compliance-summaries/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md         # Phase 1 output (/sp.plan command)
├── quickstart.md         # Phase 1 output (/sp.plan command)
├── contracts/
│   └── tax-api.md       # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── tax_rules_document.py         # NEW: SQLAlchemy model
│   │   ├── tax_rules_document_chunk.py   # NEW: SQLAlchemy model (with embedding column)
│   │   └── tax_summary.py                # NEW: SQLAlchemy model
│   ├── schemas/
│   │   └── tax.py                        # NEW: Pydantic request/response models
│   ├── services/
│   │   ├── tax_document_service.py       # NEW: document CRUD, chunking, embedding at add-time
│   │   └── tax_summary_service.py        # NEW: retrieval, figure computation (calls reporting_service), draft/sign-off/discard lifecycle
│   ├── agent/
│   │   └── tax_tools.py                  # NEW: embed_text, draft_summary_narrative, resolve_summary_request
│   └── api/
│       ├── tax.py                        # NEW: document-library + summary routes
│       └── agent.py                      # MODIFIED: add POST /api/agent/tax/query (natural-language summary request)
├── migrations/                            # Alembic migration adding the three new tables
└── tests/
    ├── contract/                          # one test file per contracts/tax-api.md endpoint
    ├── integration/                       # per-user-story flows (US1-US4)
    └── unit/                              # retrieval scoring + staleness-check logic (deterministic, easy to unit test)

frontend/
├── src/
│   ├── components/
│   │   ├── TaxDocumentLibrary.tsx        # NEW: add/view/remove reference documents (US1)
│   │   ├── TaxSummaryGenerator.tsx       # NEW: period picker, generate a draft, sign-off/discard controls on the fresh draft (US2, US3)
│   │   └── TaxSummaryHistory.tsx         # NEW: past summaries list, reopen any (draft or signed-off) to view (US3)
│   ├── app/
│   │   └── tax/                          # NEW: page wiring the above components
│   └── services/
│       └── taxApi.ts                     # NEW: typed client for contracts/tax-api.md
└── tests/
    └── components/
```

**Structure Decision**: Extends the existing `backend/` + `frontend/`
directories, following the pattern established by `002`–`007` — additive
on top of the same stack and reusing `reporting_service.profit_and_loss`
rather than introducing parallel computation. One new frontend route
(`/tax`) and nav link, matching how `/reports` (`005`) and `/audit` (`007`)
were added. `api/agent.py` is extended in place for the one
agent-mediated endpoint, per the established "all agent-mediated
endpoints live in api/agent.py" rule.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram
update) is tracked as a task, not a constitutional exception. The
retrieval-architecture decision is tracked as a suggested ADR above, not
a Complexity Tracking violation, since it introduces no new dependency
and directly satisfies an explicit functional requirement (FR-003).*
