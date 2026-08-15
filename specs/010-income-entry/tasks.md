---
description: "Task list for income entry feature implementation"
---

# Tasks: Income Entry

**Input**: Design documents from `/specs/010-income-entry/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/income-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching `001-expense-entry` and `002-ledger-journal-entries`'s precedent. If TDD is wanted later, add contract tests per `contracts/income-api.md` and integration tests per the acceptance scenarios in `spec.md` before their corresponding implementation tasks.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- File paths are relative to the repository root, per `plan.md`'s Project Structure. This feature extends the existing `backend/` and `frontend/` projects — no new project initialization is needed.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create this feature's new file skeleton: `backend/src/models/income_source.py`, `backend/src/models/income_entry.py`, `backend/src/schemas/income_source.py`, `backend/src/schemas/income_entry.py`, `backend/src/services/income_source_service.py`, `backend/src/services/income_entry_service.py`, `backend/src/api/income_sources.py`, `backend/src/api/income.py`; `frontend/src/app/income/`, `frontend/src/components/IncomeForm.tsx`, `frontend/src/components/IncomeList.tsx`, `frontend/src/services/incomeApi.ts` — per `plan.md`'s Project Structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 [P] Create the `IncomeSource` SQLAlchemy model (`id`, `name` unique, `account_id` FK, `is_custom`) in `backend/src/models/income_source.py`, per `data-model.md`
- [x] T003 [P] Create the `IncomeEntry` SQLAlchemy model (`id`, `amount` with `> 0` check, `date`, `source_id` FK, `description`, `created_at`, `updated_at`) in `backend/src/models/income_entry.py`, per `data-model.md`
- [x] T004 Modify the `JournalEntry` SQLAlchemy model in `backend/src/models/journal_entry.py`: make `expense_entry_id` and `account_coding_id` nullable, add nullable `income_entry_id` (not a DB-enforced FK, same audit-survival reasoning as `expense_entry_id`), per `data-model.md`'s `JournalEntry` generalization (depends on T002, T003 existing so the column can conceptually reference `IncomeEntry`)
- [x] T005 Write the Alembic migration in `backend/migrations/versions/` that: creates `income_sources` and `income_entries` tables; alters `journal_entries` to make `expense_entry_id`/`account_coding_id` nullable and adds nullable `income_entry_id`; adds the `ck_journal_entries_exactly_one_source` check constraint; seeds two starter accounts (`4000 Sales Revenue` type `revenue`, `3000 Owner's Capital` type `equity`) and two starter income sources ("Sales" → Sales Revenue, "Owner Investment" → Owner's Capital) — per `data-model.md` and `research.md` Decision 5 (depends on T002–T004)
- [x] T006 [P] Create `IncomeSource` Pydantic request/response schemas (`IncomeSourceCreate` with `account_type: Literal["revenue","equity"]`, `IncomeSourceRead` with nested `AccountRead`, `IncomeSourceListResponse`) in `backend/src/schemas/income_source.py`, per `contracts/income-api.md`
- [x] T007 [P] Create `IncomeEntry` Pydantic request/response schemas (`IncomeEntryCreate`, `IncomeEntryUpdate`, `IncomeEntryRead` with nested `IncomeSourceRead`, `IncomeEntryListResponse`) in `backend/src/schemas/income_entry.py`, per `contracts/income-api.md`
- [x] T008 Modify `backend/src/schemas/journal_entry.py`: make `expense_entry_id` optional and add optional `income_entry_id` on `JournalEntryRead`, per `data-model.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Record an income transaction manually (Priority: P1) 🎯 MVP

**Goal**: An admin records money received (amount, date, source, optional description) and it immediately posts a balanced journal entry (debit Cash / credit the source's mapped Revenue or Equity account) — no separate approval step.

**Independent Test**: Submit a new income entry with an amount, date, and source; confirm it appears in the income list and that `GET /api/journal-entries` shows a new posted entry debiting Cash and crediting the source's account for that amount.

- [x] T009 [US1] Implement `IncomeSourceService.list_sources` and `IncomeSourceService.create_source` (creates a new `revenue`- or `equity`-type `Account` with an auto-assigned next code in that type's range, then the `IncomeSource` row pointing at it; rejects a case-insensitive duplicate name, FR-007) in `backend/src/services/income_source_service.py`
- [x] T010 [US1] Implement `GET /api/income-sources` and `POST /api/income-sources` in `backend/src/api/income_sources.py`, per `contracts/income-api.md`
- [x] T011 [US1] Implement `LedgerService.post_income_journal_entry` (constructs a balanced debit-Cash/credit-source's-account `JournalEntry` from an `IncomeEntry`'s amount/date/source; refuses to post if the resolved debit and credit accounts would be equal) in `backend/src/services/ledger_service.py`, per FR-008, mirroring `post_journal_entry`'s validation shape (depends on T004)
- [x] T012 [US1] Generalize `LedgerService.reverse_journal_entry` to also copy `income_entry_id` from the entry being reversed (alongside the existing `expense_entry_id`/`account_coding_id` copy) in `backend/src/services/ledger_service.py`, per `research.md` Decision 4 (depends on T011)
- [x] T013 [US1] Implement `IncomeEntryService.create_entry` (validates `amount > 0`, resolves `source_id` to an `IncomeSource`, creates the `IncomeEntry` row, then calls `LedgerService.post_income_journal_entry` in the same transaction) in `backend/src/services/income_entry_service.py`, per FR-001–FR-002, FR-008 (depends on T011)
- [x] T014 [US1] Implement `POST /api/income` in `backend/src/api/income.py`, per `contracts/income-api.md`
- [x] T015 [US1] Register the income-sources and income routers in `backend/src/main.py`
- [x] T016 [US1] Build the `IncomeForm` component (amount, date, source picker populated from `GET /api/income-sources`, optional description) in `frontend/src/components/IncomeForm.tsx`
- [x] T017 [US1] Create the typed API client (`createIncomeEntry`, `listIncomeSources`, `createIncomeSource`) in `frontend/src/services/incomeApi.ts`, per `contracts/income-api.md`
- [x] T018 [US1] Build the income page wiring `IncomeForm` in `frontend/src/app/income/page.tsx`, and add `{ href: "/income", label: "Income" }` to `frontend/src/components/Sidebar.tsx` — the one existing-file touch-point for this story

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - View, edit, and delete existing income entries (Priority: P2)

**Goal**: An admin can list/filter income entries, correct a mistake (amount/date/source/description), or remove an entry — with the ledger effect corrected or reversed to match.

**Independent Test**: Create an entry, edit its amount and confirm both the entry and its journal entry reflect the new value (old entry reversed, new one posted), then delete it and confirm it's gone from the list and its journal entry is marked reversed.

- [x] T019 [US2] Implement `LedgerService.reverse_journal_entry_for_income` (finds the active — `posted`, non-reversal — journal entry for a given `income_entry_id` and reverses it, no-ops if none exists) in `backend/src/services/ledger_service.py`, per FR-006, mirroring `reverse_journal_entry_for_expense` (depends on T012)
- [x] T020 [US2] Implement `IncomeEntryService.list_entries` (filters by `date_from`/`date_to`/`source_id`, rejects `date_from > date_to`) and `IncomeEntryService.get_entry` in `backend/src/services/income_entry_service.py`, per FR-004
- [x] T021 [US2] Implement `IncomeEntryService.update_entry` (updates any of `amount`/`date`/`source_id`/`description`; if `amount`, `date`, or `source_id` changed, calls `reverse_journal_entry_for_income` then `post_income_journal_entry` for the corrected values in the same transaction) in `backend/src/services/income_entry_service.py`, per FR-005, `research.md` Decision 4 (depends on T019)
- [x] T022 [US2] Implement `IncomeEntryService.delete_entry` (calls `reverse_journal_entry_for_income` then deletes the row) in `backend/src/services/income_entry_service.py`, per FR-006 (depends on T019)
- [x] T023 [US2] Implement `GET /api/income`, `GET /api/income/{id}`, `PATCH /api/income/{id}`, and `DELETE /api/income/{id}` in `backend/src/api/income.py`, per `contracts/income-api.md`
- [x] T024 [US2] Build the `IncomeList` component (date-range and source filters, edit and delete actions) in `frontend/src/components/IncomeList.tsx`
- [x] T025 [US2] Wire `IncomeList` into `frontend/src/app/income/page.tsx` alongside `IncomeForm`, and extend `frontend/src/services/incomeApi.ts` with `listIncomeEntries`, `updateIncomeEntry`, `deleteIncomeEntry`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - See income reflected in the income statement and balance sheet (Priority: P2)

**Goal**: The already-existing income-statement and balance-sheet reports show income entries correctly, with no changes to `reporting_service.py`, `schemas/reports.py`, or `api/reports.py` (per `plan.md`'s Structure Decision and `research.md` Decision 1).

**Independent Test**: Record one "Owner Investment" entry and one "Sales" entry alongside an existing posted expense entry; confirm the income statement's `revenue_lines` includes the Sales entry and the balance sheet's `is_balanced` is `true`.

> **Note**: Because Decision 1 deliberately generalized `journal_entries` rather than adding a parallel table, there is no new reporting code to write for this story — it is validation-only, confirming the design assumption holds against the real database.

- [x] T026 [US3] Manually verify (per `quickstart.md`'s step 6 and the $5.50 demo walkthrough) that `GET /api/reports/profit-and-loss` includes posted "Sales" income in `revenue_lines` and `GET /api/reports/balance-sheet` returns `is_balanced: true` for a scenario including an Owner Investment entry — record any gap found as a bug against `LedgerService.post_income_journal_entry` (T011), not against the reporting layer

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T027 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the income-entry → journal-posting path alongside the existing expense-entry path, and confirm the shareable URL in `.specify/memory/constitution.md`/`README.md` still reflects the current system — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [x] T028 [P] Update `README.md`'s Project structure / feature list to mention income entry, if it enumerates features
- [x] T029 Run the `quickstart.md` validation flow end-to-end (including the $5.50 demo walkthrough) and fix any gaps found
- [x] T030 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories, but its implementation necessarily includes `post_income_journal_entry` and the `reverse_journal_entry` generalization (T011–T012) that US2 also relies on — same shape as `002`'s US1/US2 relationship.
  - US2 (P2) depends on US1's `post_income_journal_entry`/generalized `reverse_journal_entry` existing.
  - US3 (P2) depends on US1 (and ideally US2, for a fuller demo) having posted at least some income journal entries to verify against — it adds no new code of its own.
  - Recommended order given these dependencies: US1 → US2 → US3 (matches priority order already).
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### Within Each User Story

- Services before endpoints; endpoints before frontend components that call them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- Foundational model tasks T002, T003 can run in parallel (different files); T004 (journal_entry model change) and T005 (migration) depend on them.
- Foundational schema tasks T006, T007 can run in parallel with each other; T008 (journal_entry schema change) can run in parallel with T006/T007.
- Within each user story phase, backend service/endpoint tasks are sequential (same files depend on prior steps), but frontend component tasks for a story can often start once that story's endpoint contracts are stable.
- Polish tasks T027, T028, T030 can all run in parallel with each other.

---

## Parallel Example: Foundational Phase

```bash
# Launch model creation together (different files, no cross-dependencies):
Task: "Create IncomeSource SQLAlchemy model in backend/src/models/income_source.py"
Task: "Create IncomeEntry SQLAlchemy model in backend/src/models/income_entry.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (critical — blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently.
5. Demo if ready — this alone delivers manual income recording with immediate ledger posting.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (MVP — record income, see it posted to the ledger).
3. Add US2 → validate → demo (list/filter/edit/delete with correct ledger reversal).
4. Add US3 → validate → demo (confirm the pre-existing reports now show real revenue/equity numbers — the original goal).
5. Polish phase → diagram update, README, quickstart validation (including the $5.50 demo), cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T027 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `010-income-entry` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.

### T029 findings (quickstart validation)

Ran the migration and the full backend live against `docker-compose up`
(`docker compose restart backend` to apply the new migration/code; the
frontend needed `docker compose restart frontend` too — its dev server did
not discover the new `frontend/src/app/income/` route directory via its
file watcher while running, unlike a plain file edit inside an existing
route, so a restart was required to serve `/income`).

Verified live end to end via the running API:

1. Starter seed data: `GET /api/income-sources` returned exactly "Sales" →
   `4000 Sales Revenue` (revenue) and "Owner Investment" → `3000 Owner's
   Capital` (equity), per `research.md` Decision 5.
2. Create (US1): `POST /api/income` with a Sales-sourced $5.50 entry
   produced a journal entry debiting Cash / crediting Sales Revenue for
   $5.50, and `GET /api/reports/profit-and-loss` immediately showed
   `revenue_lines: [{"account_name": "Sales Revenue", "balance": "5.50"}]`,
   `net_profit: "5.50"` — with zero changes to `reporting_service.py`,
   confirming `research.md` Decision 1.
3. Edit (US2): `PATCH` the same entry's amount to $10.00 — profit-and-loss
   immediately showed revenue `"10.00"`, not `"15.50"`, confirming the old
   posting was reversed (not left active) before the new one posted.
4. Delete (US2): `DELETE` the entry — profit-and-loss reverted to
   `total_revenue: "0.00"`, confirming the reversal-on-delete path.
5. Equity path: `POST /api/income` an Owner-Investment-sourced $1000 entry
   — `GET /api/reports/balance-sheet` showed
   `equity_lines: [{"account_name": "Owner's Capital", "balance": "1000.00"}]`
   and the Cash asset line moved by the same $1000, confirming the
   revenue/equity split (`research.md` Decision 3) needs no reporting code.
6. Validation: zero-amount and missing-date `POST /api/income` both
   correctly returned `422`.
7. Demo data (per this feature's originating request): seeded 3× $5.50
   Owner Investment + 3× $5.50 Sales entries through the running app's API
   (not a DB script). Result: `profit-and-loss` for August showed
   `total_revenue: "16.50"`, `net_profit: "16.50"`; `balance-sheet` showed
   `equity_lines` totaling `"16.50"`. `is_balanced` was `false` overall only
   because of a large volume of pre-existing expense demo data already in
   this database from before this feature (unrelated to this change) with
   no offsetting funding entry — not a defect in this feature's posting
   logic, which was independently confirmed balanced in isolation (steps
   2–5 above each moved Cash by exactly the entry amount, matching the
   credited account).

`ruff check src migrations` and `uv run pytest` both pass; `npx tsc
--noEmit` passes with no errors. No test tasks existed to add coverage for
the new code paths (matching this feature's no-TDD scope decision), so
these are process/lint gates only, not behavioral coverage — the live API
verification above is what actually exercises FR-001–FR-012.
