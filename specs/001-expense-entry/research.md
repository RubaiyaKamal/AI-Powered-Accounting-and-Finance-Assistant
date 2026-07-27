# Phase 0 Research: Expense Entry

All technology choices below are either fixed by the ratified project
constitution (`.specify/memory/constitution.md`, Technology & Architecture
Constraints) or are feature-scoped decisions with no remaining
`NEEDS CLARIFICATION` markers — this feature's Technical Context has no open
unknowns, so this document records decisions rather than resolving questions.

## Decision: Backend framework & validation

**Decision**: FastAPI + Pydantic v2, dependencies managed with `uv`.
**Rationale**: Fixed by the constitution's Technology & Architecture
Constraints; also directly requested by the user during clarification
("all API request/response models must use Pydantic"). FastAPI's native
Pydantic integration means request/response validation for financial fields
(amount, date, category) is enforced at the API boundary with no extra
glue code.
**Alternatives considered**: Flask + Marshmallow (rejected — constitution
already fixes the stack; switching frameworks is a governance-level decision,
not a feature-level one).

## Decision: Database & ORM

**Decision**: PostgreSQL, accessed via SQLAlchemy 2.0 (async engine) with
Alembic for migrations.
**Rationale**: Constitution fixes PostgreSQL. SQLAlchemy's async support
pairs naturally with FastAPI's async request handlers; Alembic gives the
project a real migration history, which matters once `Category` and
`ExpenseEntryEditHistory` tables need schema evolution across features.
**Alternatives considered**: Raw `asyncpg` queries (rejected — more
boilerplate, weaker type safety than SQLAlchemy models mirrored by Pydantic
schemas, which the constitution calls for explicitly).

## Decision: Frontend framework

**Decision**: Next.js (App Router) + TypeScript.
**Rationale**: Fixed by the constitution.
**Alternatives considered**: none evaluated at feature level — this is a
project-wide constraint.

## Decision: AI integration shape for this feature

**Decision**: The OpenAI Agents SDK agent is given two scoped tools relevant
to this feature: `parse_expense_draft` (takes free text, returns structured
draft fields — amount, date, category guess, description — without writing
to the database) and `suggest_category` (takes a description and the current
category list, returns a suggested category name). Both tools return data
for the frontend/API to show the admin for confirmation; neither tool
commits an entry directly. Committing happens through the same
`POST /api/expenses` endpoint the manual form uses, tagged with
`source=natural_language` once the admin confirms.
**Rationale**: This is the concrete, feature-level application of the
constitution's Principle II (LLM orchestrates/narrates, never writes
financial data unmediated) and directly implements FR-008/FR-009 (show
parsed fields for confirmation; ask a follow-up question in the same turn
when a required field is missing — which the Agents SDK's conversational
tool-calling loop supports natively, since the agent can simply respond with
a clarifying question instead of calling the tool when required arguments
are absent).
**Alternatives considered**: Having the LLM call a `create_expense_entry`
tool directly (rejected — skips the human-confirmation step FR-008
requires); parsing NL input with a separate regex/rules layer instead of the
LLM (rejected — brittle against real phrasing variance like "for July" as a
date, which is exactly the kind of input the assignment's example uses).

## Decision: Edit history storage

**Decision**: A dedicated `expense_entry_edit_history` table, one row per
field change (`field_name`, `old_value`, `new_value`, `changed_at`), foreign
keyed to the expense entry, cascade-deleted with its parent entry.
**Rationale**: Matches the `Edit History Entry` key entity from the spec
directly; keeps the hot `expense_entries` row small and makes it possible to
later query "what changed in March" for the audit feature without parsing a
JSON blob. Cascade delete on the parent is intentional — per the spec's
Assumptions, entry deletion doesn't retroactively alter already-generated
reports, and history for a deleted entry is meaningless in isolation.
**Alternatives considered**: Storing a JSON diff array on the entry row
itself (rejected — harder to query/index for the later audit feature, and
grows unboundedly on a row that's read far more often than its history is).

## Decision: Category storage

**Decision**: A dedicated `categories` table (`id`, `name` unique, `is_custom`
boolean), referenced by `category_id` foreign key from `expense_entries`,
seeded with the starter set (Utilities, Rent, Salaries, Supplies) at
migration time with `is_custom=false`.
**Rationale**: Directly implements FR-014 (starter set + admin-extensible).
A foreign key (not a free-text string column) keeps category names
consistent for filtering (FR-004) and future reporting, and makes "is this
category one of the starter defaults or admin-added" a queryable fact
rather than an inferred one.
**Alternatives considered**: Free-text category string on the entry
(rejected — allows silent typos/duplicates like "Utilities" vs "utilties"
that would fragment reporting).

## Decision: Testing approach

**Decision**: Backend — pytest + httpx (async test client) for contract and
integration tests. Frontend — Vitest + React Testing Library for component
tests.
**Rationale**: Standard, well-supported pairings for FastAPI and Next.js
respectively; nothing about this feature's scope calls for anything more
specialized (e.g., no need for a dedicated LLM-eval framework yet, since the
NL-parsing tool's correctness is checked via SC-002's 90%-first-attempt
target using recorded example phrases, not a formal eval harness at this
stage).
**Alternatives considered**: Deferred — end-to-end browser testing
(Playwright) is not decided here since it's a project-wide tooling choice
better made once more than one feature exists; not blocking for this plan.

## Outstanding item carried to Complexity Tracking / tasks

The constitution's Principle V (Documented Architecture & Workflow) requires
a Lucidchart/draw.io diagram of the UI → API → agent → tools → database flow,
updated in the same PR as any change that alters that flow. This feature is
the first real implementation of that flow (natural-language entry creation
through the agent). No diagram exists yet project-wide. This is carried
forward as an explicit task in `tasks.md` rather than silently skipped.
