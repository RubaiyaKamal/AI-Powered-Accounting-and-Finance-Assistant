---
description: "Task list for expense-entry feature implementation"
---

# Tasks: Expense Entry

**Input**: Design documents from `/specs/001-expense-entry/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/expense-entries-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification. If TDD is wanted later, add contract tests per `contracts/expense-entries-api.md` and integration tests per the acceptance scenarios in `spec.md` before their corresponding implementation tasks.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root, per `plan.md`'s Project Structure

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create the `backend/` and `frontend/` directory skeleton per plan.md's Project Structure (`backend/src/{models,schemas,services,agent,api}`, `backend/migrations`, `backend/tests/{contract,integration,unit}`, `frontend/src/{components,services}`, `frontend/src/app/expenses`, `frontend/tests/components`)
- [x] T002 Initialize the backend Python project with `uv` in `backend/pyproject.toml`, adding FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, and the OpenAI Agents SDK as dependencies
- [x] T003 [P] Initialize the frontend Next.js (TypeScript, App Router) project with `npm` in `frontend/package.json`
- [x] T004 [P] Configure linting/formatting: `ruff` for the backend (`backend/pyproject.toml`), ESLint + Prettier for the frontend (`frontend/.eslintrc.json`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Configure the PostgreSQL async engine and session factory in `backend/src/db.py`
- [x] T006 Set up the Alembic migrations framework, pointed at the engine from T005, in `backend/migrations/env.py`
- [x] T007 [P] Create the `Category` SQLAlchemy model (`id`, `name` unique, `is_custom`) in `backend/src/models/category.py`, per `data-model.md`
- [x] T008 [P] Create the `ExpenseEntry` SQLAlchemy model (`id`, `amount`, `date`, `category_id`, `category_source`, `description`, `source`, `created_at`, `updated_at`) in `backend/src/models/expense_entry.py`, per `data-model.md`
- [x] T009 [P] Create the `ExpenseEntryEditHistory` SQLAlchemy model (`id`, `expense_entry_id` FK cascade-delete, `field_name`, `old_value`, `new_value`, `changed_at`) in `backend/src/models/expense_entry_edit_history.py`
- [x] T010 Write the Alembic migration creating the three tables from T007–T009 and seeding the starter category set (Utilities, Rent, Salaries, Supplies, `is_custom=false`) in `backend/migrations/versions/`
- [x] T011 [P] Create `Category` Pydantic request/response schemas in `backend/src/schemas/category.py`, per `contracts/expense-entries-api.md`
- [x] T012 [P] Create `ExpenseEntry` Pydantic request/response schemas (including the `edit_history` nested list) in `backend/src/schemas/expense_entry.py`, per `contracts/expense-entries-api.md`
- [x] T013 Configure the FastAPI app instance and router registration in `backend/src/main.py`
- [x] T014 Configure the OpenAI Agents SDK client (model: GPT-4o mini) bootstrap in `backend/src/agent/__init__.py`
- [x] T015 [P] Scaffold the typed frontend API client (base fetch wrapper) in `frontend/src/services/expensesApi.ts`
- [x] T016 Configure environment variable handling for the DB connection string and OpenAI API key via `.env` / `backend/.env.example` — never hardcoded, per the constitution

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Record an expense manually (Priority: P1) 🎯 MVP

**Goal**: An admin can create a valid expense entry via a form; invalid entries (zero/negative amount, missing required field) are rejected with a clear reason.

**Independent Test**: Submit an entry with amount/date/category via the form and confirm it appears in the list with exactly those values; submit a zero/negative amount or a missing field and confirm rejection.

- [x] T017 [US1] Implement `CategoryService.list_categories` and `CategoryService.create_category` (rejects case-insensitive duplicate names, FR-014) in `backend/src/services/category_service.py`
- [x] T018 [US1] Implement `ExpenseEntryService.create_entry` (validates amount > 0, required fields present, requires a resolved `category_id`) in `backend/src/services/expense_entry_service.py`, per FR-001–FR-003. AI-suggestion of an omitted category is added later in US4 (T038) — until then, `category_id` is required input.
- [x] T019 [US1] Implement `POST /api/expenses`, `GET /api/categories`, and `POST /api/categories` (add custom category, FR-014) in `backend/src/api/expenses.py` and `backend/src/api/categories.py`, per `contracts/expense-entries-api.md`
- [x] T019a [US1] Add an "add category" control (name input + submit) wired to `POST /api/categories` in `frontend/src/components/ExpenseForm.tsx`, per FR-014
- [x] T020 [US1] Register the expenses and categories routers in `backend/src/main.py`
- [x] T021 [US1] Build the `ExpenseForm` component (amount/date/category/description fields) in `frontend/src/components/ExpenseForm.tsx`
- [x] T022 [US1] Build the expenses page wiring `ExpenseForm` to `POST /api/expenses` in `frontend/src/app/expenses/page.tsx`
- [x] T023 [US1] Add error display for rejected submissions (invalid amount, missing field) in `frontend/src/components/ExpenseForm.tsx`, per FR-002–FR-003

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - View, edit, and delete existing expenses (Priority: P2)

**Goal**: An admin can filter/view entries, correct any field (with the change recorded in edit history), delete an entry, and view an entry's edit history.

**Independent Test**: Create an entry, edit one field and confirm the change and its history row are saved, then delete it and confirm it's gone from the list.

- [x] T024 [US2] Implement `ExpenseEntryService.list_entries` with `date_from`/`date_to`/`category_id` filters in `backend/src/services/expense_entry_service.py`, per FR-004
- [x] T025 [US2] Implement `ExpenseEntryService.update_entry`, writing one `ExpenseEntryEditHistory` row per changed field, in `backend/src/services/expense_entry_service.py`, per FR-005 and FR-015
- [x] T026 [US2] Implement `ExpenseEntryService.delete_entry` (relies on DB cascade for history) in `backend/src/services/expense_entry_service.py`, per FR-006
- [x] T027 [US2] Implement `GET /api/expenses`, `GET /api/expenses/{id}` (with `edit_history`), `PATCH /api/expenses/{id}`, and `DELETE /api/expenses/{id}` in `backend/src/api/expenses.py`, per `contracts/expense-entries-api.md`
- [x] T028 [US2] Validate `date_from <= date_to` in the list endpoint, returning `422` otherwise, in `backend/src/api/expenses.py`
- [x] T029 [US2] Build the `ExpenseList` component with date-range/category filters in `frontend/src/components/ExpenseList.tsx`
- [x] T030 [US2] Build the `ExpenseHistory` component displaying field/old value/new value/changed-at in `frontend/src/components/ExpenseHistory.tsx`, per FR-015a
- [x] T031 [US2] Wire edit and delete actions from `ExpenseList` to the `PATCH`/`DELETE` endpoints in `frontend/src/components/ExpenseList.tsx`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Record an expense using natural language (Priority: P3)

**Goal**: An admin can create an expense entry by typing a plain-language sentence, with parsed fields confirmed before saving and a follow-up question asked when a required field is missing.

**Independent Test**: Send a natural-language sentence with amount, date, and description; confirm the assistant shows parsed values and the entry saves correctly on confirmation. Send one missing the amount and confirm a specific follow-up question is asked.

- [x] T032 [US3] Implement the `parse_expense_draft` agent tool (extracts amount/date/category hint/description; identifies missing required fields) in `backend/src/agent/expense_tools.py`, per FR-007–FR-009
- [x] T033 [US3] Implement `POST /api/agent/expenses/parse` returning `ready_for_confirmation` or `needs_clarification`, per `contracts/expense-entries-api.md`, in `backend/src/api/agent.py`
- [x] T034 [US3] Extend `ExpenseEntryService.create_entry` and its Pydantic schema to accept `source=natural_language` in `backend/src/services/expense_entry_service.py` and `backend/src/schemas/expense_entry.py`
- [x] T035 [US3] Build the `AssistantChat` component (send text, show parsed draft, confirm or correct, submit) in `frontend/src/components/AssistantChat.tsx`
- [x] T036 [US3] Wire the follow-up-question flow for `needs_clarification` responses in `frontend/src/components/AssistantChat.tsx`, per FR-009

**Checkpoint**: User Stories 1–3 are all independently functional.

---

## Phase 6: User Story 4 - Get an AI-suggested category for an entry (Priority: P4)

**Goal**: An entry submitted without an explicit category receives an AI-suggested one, visibly marked, and overridable in one action.

**Independent Test**: Submit an entry with a description but no category; confirm a marked AI-suggested category appears and can be overridden in a single action.

- [x] T037 [US4] Implement the `suggest_category` agent tool (description + existing category list → suggested name) in `backend/src/agent/expense_tools.py`, per FR-010
- [x] T038 [US4] Wire `suggest_category` into `ExpenseEntryService.create_entry` when `category_id` is omitted, setting `category_source=ai_suggested`, in `backend/src/services/expense_entry_service.py`
- [x] T039 [US4] Surface the AI-suggested marker and a one-action override control in `frontend/src/components/ExpenseForm.tsx` and `frontend/src/components/ExpenseList.tsx`, flipping `category_source` to `user` on override, per FR-011

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T040 [P] Create the Lucidchart or draw.io workflow diagram (UI → API → agent → tools → database flow) and record its shareable URL in `.specify/memory/constitution.md` (Principle V) and `README.md` — required before this feature's PR merges, per the Constitution Check in `plan.md`
- [x] T041 [P] Write `README.md` with setup and run instructions (clone, install, environment variables, `docker-compose up`)
- [x] T042 [P] Add Docker setup: `backend/Dockerfile`, `frontend/Dockerfile`, and a root `docker-compose.yml` wiring both plus PostgreSQL
- [ ] T043 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [x] T044 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories.
  - US2 (P2) depends on US1's `ExpenseEntryService.create_entry` and endpoint existing (it edits/deletes entries US1 creates) but its own list/edit/delete logic is independently testable once seeded data exists.
  - US3 (P3) depends on US1's `create_entry`/`POST /api/expenses` (it commits through the same endpoint, per `research.md`).
  - US4 (P4) depends on US1's `create_entry` (it extends the same creation path).
  - Recommended order given these dependencies: US1 → US2 → US3 → US4 (matches priority order already).
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### Within Each User Story

- Services before endpoints; endpoints before frontend components that call them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- All Setup tasks marked `[P]` (T003, T004) can run in parallel with each other (not with T001/T002, which they depend on existing).
- Foundational model tasks T007, T008, T009 can run in parallel (different files); T010 (migration) depends on all three.
- Foundational schema tasks T011, T012 can run in parallel; T015 (frontend client scaffold) can run in parallel with any backend foundational task.
- Within each user story phase, backend service/endpoint tasks are sequential (same files depend on prior steps), but frontend component tasks for a story can often start once that story's endpoint contracts are stable.
- Polish tasks T040–T042 and T044 can all run in parallel with each other.

---

## Parallel Example: Foundational Phase

```bash
# Launch model creation together (different files, no cross-dependencies):
Task: "Create Category SQLAlchemy model in backend/src/models/category.py"
Task: "Create ExpenseEntry SQLAlchemy model in backend/src/models/expense_entry.py"
Task: "Create ExpenseEntryEditHistory SQLAlchemy model in backend/src/models/expense_entry_edit_history.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (critical — blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently.
5. Demo if ready — this alone is a usable bookkeeping tool.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (MVP).
3. Add US2 → validate → demo (data can now be corrected/reviewed).
4. Add US3 → validate → demo (AI differentiator live).
5. Add US4 → validate → demo (category suggestion polish).
6. Polish phase → diagram, README, Docker, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T040 (workflow diagram) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `001-expense-entry` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
- T043 remains open: Docker Desktop's daemon would not come up in the dev environment during implementation (API returned 500 for several minutes after launch), so the full stack (`docker-compose up`) could not be started to run `quickstart.md` end-to-end. Backend was instead verified via `uv run python -c "import src.main"` (clean) and `ruff check` (clean); frontend via `npx tsc --noEmit` (clean). Run `docker-compose up` and walk through `quickstart.md` once Docker is healthy.
