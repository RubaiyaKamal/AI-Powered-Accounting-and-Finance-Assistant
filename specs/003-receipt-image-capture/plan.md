# Implementation Plan: Receipt/Invoice Image Capture

**Branch**: `003-receipt-image-capture` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-receipt-image-capture/spec.md`

## Summary

Let an admin upload a receipt/invoice photo and get a parsed draft
(amount, date, vendor/description) for confirmation, exactly mirroring
`001-expense-entry`'s natural-language flow but with an image instead of
free text. Technical approach: a new `parse_receipt_image` agent function
(added to the existing `backend/src/agent/expense_tools.py`, alongside
`parse_expense_draft`) sends the uploaded image directly to GPT-4o mini's
multimodal input — no separate OCR library — and returns the same
`ready_for_confirmation` / `needs_clarification` shape `parse_expense_draft`
already returns. A new `POST /api/agent/expenses/parse-receipt` endpoint
accepts the upload, processes it in memory, and never writes it to disk.
The existing `AssistantChat` component gains a file-upload control that
reuses its already-built confirm/correct/save UI — no new frontend
component. Commit still happens through the same `POST /api/expenses`
endpoint, now accepting `source=receipt_image`.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Node 20 (frontend)
— same stack as `001-expense-entry`/`002-ledger-journal-entries`, no new
languages
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) +
Alembic, OpenAI Agents SDK (GPT-4o mini, multimodal input) — backend;
Next.js (App Router), React — frontend. No new dependency needed for file
upload: FastAPI's `UploadFile`/`File` (already a transitive dependency via
`python-multipart`, confirmed present in the existing lockfile) handles
multipart uploads natively.
**Storage**: No new tables. Extends `expense_entries.source`'s existing
enum (`manual`, `natural_language`) with a third value, `receipt_image`
(see `research.md`) — the uploaded image itself is never persisted (FR-008).
**Testing**: pytest + httpx async client (backend), Vitest + React Testing
Library (frontend) — same tooling as prior features.
**Target Platform**: Web application, containerized via Docker (reuses the
existing `backend`/`frontend`/`db` services — no new services needed)
**Project Type**: web (frontend + backend split, same repo layout)
**Performance Goals**: Upload → parsed draft round trip is LLM-latency- and
image-size-bound; target under 5s p95 for a typical receipt photo once the
agent is warm (same cold-start caveat already observed and documented for
`parse_expense_draft` in `001-expense-entry`'s T043 findings — the very
first agent call after a backend restart is materially slower).
**Constraints**: The uploaded image MUST NOT be written to disk, object
storage, or any database column at any point (FR-008) — it is read into
memory, sent to the vision model, and discarded once the request completes.
No financial figure (amount) may be written to the database as LLM-generated
free text — every write still goes through the same validated
`POST /api/expenses` endpoint regardless of source (constitution Principle
II, same guarantee `001-expense-entry` already established for the
natural-language path).
**Scale/Scope**: Single business, single admin user, low volume — same
scope as prior features. No batch upload, no multi-image receipts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | `spec.md` written and passed its quality checklist before this plan |
| II. Deterministic Financial Computation | ✅ PASS | `parse_receipt_image` only ever returns a draft for confirmation (mirrors `parse_expense_draft`'s existing guarantee, FR-002); the actual database write always goes through the same validated `POST /api/expenses` endpoint as every other creation path |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | ✅ PASS (by extension) | Not itself an audit/tax action, but preserves the same "AI drafts, human confirms" pattern the higher-stakes features depend on |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Work is on `003-receipt-image-capture`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ⚠️ ACTION REQUIRED | This feature adds a new AI tool (`parse_receipt_image`) and a new upload flow — `docs/workflow-diagram.drawio` must be updated before this feature's PR merges, per Principle V |
| VI. Simplicity & Traceability | ✅ PASS | No new component (extends `AssistantChat`, not a parallel upload UI); no new tables (extends the existing `source` enum); no persistent image storage infrastructure introduced |

**Gate result**: PASS with one tracked action item (V — diagram update), not
a violation requiring justification — no entry needed in Complexity
Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-receipt-image-capture/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/
│   └── receipt-capture-api.md   # Phase 1 output (/sp.plan command)
└── tasks.md              # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── agent/
│   │   └── expense_tools.py       # MODIFIED: add parse_receipt_image, alongside parse_expense_draft
│   ├── api/
│   │   └── agent.py               # MODIFIED: add POST /api/agent/expenses/parse-receipt
│   └── schemas/
│       └── expense_entry.py       # MODIFIED: source Literal gains "receipt_image"
└── tests/
    ├── contract/                   # one test file per contracts/receipt-capture-api.md endpoint
    └── integration/                # US1's four acceptance scenarios

frontend/
├── src/
│   ├── components/
│   │   └── AssistantChat.tsx       # MODIFIED: add a file-upload control, reusing its existing draft/confirm UI
│   └── services/
│       └── expensesApi.ts          # MODIFIED: add parseReceiptImage(file) client function
```

**Structure Decision**: No new top-level directories or components — this
feature is a small, additive extension of `001-expense-entry`'s existing
natural-language-entry code paths (`expense_tools.py`, `api/agent.py`,
`AssistantChat.tsx`, `expensesApi.ts`), per Principle VI. The only schema
touch is widening `ExpenseEntryCreate.source`'s `Literal` type by one value
— not a restructuring of the already-shipped `expense_entries` table.

## Complexity Tracking

*No entries — Constitution Check passed without violations requiring
justification. The one pending item (Principle V, workflow diagram update)
is tracked as a task, not a constitutional exception.*
