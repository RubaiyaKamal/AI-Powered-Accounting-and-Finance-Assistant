---
description: "Task list for ledger and journal entries feature implementation"
---

# Tasks: Ledger & Journal Entries

**Input**: Design documents from `/specs/002-ledger-journal-entries/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ledger-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching `001-expense-entry`'s precedent. If TDD is wanted later, add contract tests per `contracts/ledger-api.md` and integration tests per the acceptance scenarios in `spec.md` before their corresponding implementation tasks.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- File paths are relative to the repository root, per `plan.md`'s Project Structure. This feature extends the existing `backend/` and `frontend/` projects from `001-expense-entry` — no new project initialization is needed.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create this feature's new file skeleton: `backend/src/agent/ledger_tools.py`, `backend/src/api/accounts.py`, `backend/src/api/ledger.py`, `backend/src/services/account_service.py`, `backend/src/services/ledger_service.py`; `frontend/src/app/ledger/`, `frontend/src/components/AccountCoding.tsx`, `frontend/src/components/JournalEntryList.tsx`, `frontend/src/services/ledgerApi.ts` — per `plan.md`'s Project Structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Add `ACCOUNT_CODING_CONFIDENCE_THRESHOLD` env var handling (default `0.8`) in `backend/src/config.py` and `backend/.env.example`, per `research.md`'s Confidence Threshold Configuration decision
- [x] T003 [P] Create the `Account` SQLAlchemy model (`id`, `code` unique, `name` unique, `type` enum, `is_custom`) in `backend/src/models/account.py`, per `data-model.md`
- [x] T004 [P] Create the `AccountCoding` SQLAlchemy model (`id`, `expense_entry_id` FK unique, `account_id` FK, `confidence_score`, `source`, `status`) in `backend/src/models/account_coding.py`, per `data-model.md`
- [x] T005 [P] Create the `JournalEntry` SQLAlchemy model (`id`, `expense_entry_id` FK, `account_coding_id` FK, `debit_account_id` FK, `credit_account_id` FK, `amount`, `date`, `status`, `reverses_journal_entry_id` self-referencing FK) in `backend/src/models/journal_entry.py`, per `data-model.md`
- [x] T006 Write the Alembic migration creating the three tables from T003–T005 and seeding the starter chart of accounts (one `Cash` asset account, plus one expense account per existing seeded category: Utilities, Rent, Salaries, Supplies) in `backend/migrations/versions/`
- [x] T007 [P] Create `Account` Pydantic request/response schemas in `backend/src/schemas/account.py`, per `contracts/ledger-api.md`
- [x] T008 [P] Create `AccountCoding` Pydantic response schemas (including a nested `account` and, when posted, a nested `journal_entry`) in `backend/src/schemas/account_coding.py`, per `contracts/ledger-api.md`
- [x] T009 [P] Create `JournalEntry` Pydantic response schemas in `backend/src/schemas/journal_entry.py`, per `contracts/ledger-api.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Get an AI-suggested account coding for an expense (Priority: P1) 🎯 MVP

**Goal**: An admin gets an AI-suggested chart-of-accounts coding with a confidence score for an expense entry, and can approve it as-is or correct it to a different account.

**Independent Test**: Take an existing expense entry, confirm the system shows a suggested account and a confidence score, then either accept it or pick a different account, and confirm the entry's coding reflects that choice.

- [x] T010 [US1] Implement `AccountService.list_accounts` and `AccountService.create_account` (rejects a case-insensitive duplicate code or name, FR-002) in `backend/src/services/account_service.py`
- [x] T011 [US1] Implement `GET /api/accounts` and `POST /api/accounts` in `backend/src/api/accounts.py`, per `contracts/ledger-api.md`
- [x] T012 [US1] Implement the `suggest_account_coding` agent tool (description + existing accounts → suggested account name + confidence score) in `backend/src/agent/ledger_tools.py`, per FR-003, mirroring `expense_tools.py`'s `suggest_category`
- [x] T013 [US1] Implement `LedgerService.post_journal_entry` (constructs a balanced debit/credit pair from an `AccountCoding` and its `ExpenseEntry`'s amount/date; refuses to post if the debit and credit accounts would be equal or either account no longer exists) in `backend/src/services/ledger_service.py`, per FR-007–FR-008, FR-015
- [x] T014 [US1] Implement `LedgerService.reverse_journal_entry` (creates a new `JournalEntry` with debit/credit accounts swapped, same amount, `reverses_journal_entry_id` set; marks the original `status=reversed`) in `backend/src/services/ledger_service.py`, per `research.md`'s Reversal Mechanics decision (depends on T013)
- [x] T015 [US1] Implement `LedgerService.suggest_coding` (calls `suggest_account_coding`, resolves the suggested name to an `Account`, creates an `AccountCoding` row; auto-approves and calls `post_journal_entry` when confidence is at/above the configured threshold, else leaves `status=pending_review`) in `backend/src/services/ledger_service.py`, per FR-003–FR-005 (depends on T012, T013)
- [x] T016 [US1] Implement `LedgerService.approve_coding` (`pending_review` → `approved`, calls `post_journal_entry`) in `backend/src/services/ledger_service.py`, per US1 acceptance scenario 2 (depends on T013)
- [x] T017 [US1] Implement `LedgerService.correct_coding` (sets `account_id` + `source=user` + `status=approved`; if a `posted` `JournalEntry` already exists for this coding, calls `reverse_journal_entry` then `post_journal_entry` for the corrected account) in `backend/src/services/ledger_service.py`, per FR-006, FR-011 (depends on T013, T014)
- [x] T018 [US1] Implement `POST /api/expenses/{expense_id}/coding/suggest`, `GET /api/expenses/{expense_id}/coding`, `POST /api/expenses/{expense_id}/coding/approve`, and `PATCH /api/expenses/{expense_id}/coding` in `backend/src/api/ledger.py`, per `contracts/ledger-api.md`
- [x] T019 [US1] Register the accounts and ledger routers in `backend/src/main.py`
- [x] T020 [US1] Build the `AccountCoding` component (shows the suggested account + confidence score or a pending-review state, an approve control, and an account picker to correct) in `frontend/src/components/AccountCoding.tsx`
- [x] T021 [US1] Wire `AccountCoding` into the expense list/detail view — calling `suggest` the first time an entry's coding is opened, and `approve`/`correct` on user action — in `frontend/src/services/ledgerApi.ts` and `frontend/src/components/ExpenseList.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - Post a balanced double-entry journal entry (Priority: P2)

**Goal**: Every approved account coding is reflected in the ledger as a proper, balanced double-entry journal entry, and deleting an already-posted expense entry reverses its journal entry rather than orphaning it.

**Independent Test**: Approve the coding on an expense entry and confirm a journal entry is created whose debit and credit lines are for the same amount and sum to zero, referencing the coded account and the source expense entry.

> **Note**: The core posting/reversal mechanics (`post_journal_entry`, `reverse_journal_entry`) were necessarily implemented in User Story 1 (T013–T014), since FR-004 ties auto-posting directly to coding approval — this mirrors how `001-expense-entry`'s AI-suggestion mechanics were split across stories. This phase's distinctly-testable increment is the deletion-triggered reversal integration and the dedicated single-entry detail view.

- [x] T022 [US2] Implement `GET /api/journal-entries/{id}` (single entry detail, including `reverses_journal_entry_id` linkage) in `backend/src/api/ledger.py`, per `contracts/ledger-api.md`
- [x] T023 [US2] Implement `LedgerService.reverse_journal_entry_for_expense` and wire it into the existing `DELETE /api/expenses/{id}` handler in `backend/src/api/expenses.py`, per FR-012 — the one integration touch-point into already-shipped `001-expense-entry` code called out in `plan.md`
- [x] T024 [US2] Add a defensive check in `LedgerService.post_journal_entry` that the constructed debit and credit amounts are always equal and that neither account has been deleted, rather than relying solely on DB foreign-key constraints, in `backend/src/services/ledger_service.py`, per FR-008, FR-015

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - View the ledger (Priority: P3)

**Goal**: An admin can browse posted journal entries, filtered by account and/or date range, and trace each one back to its source expense entry.

**Independent Test**: Post a few journal entries and confirm they can be listed and filtered by account and by date range, and that each one links back to its source expense entry.

- [x] T025 [US3] Implement `LedgerService.list_journal_entries` with `date_from`/`date_to`/`account_id` filters (matching either the debit or credit account) in `backend/src/services/ledger_service.py`, per FR-009
- [x] T026 [US3] Implement `GET /api/journal-entries` (list + filters) in `backend/src/api/ledger.py`, per `contracts/ledger-api.md`
- [x] T027 [US3] Validate `date_from <= date_to` in the list endpoint, returning `422` otherwise, in `backend/src/api/ledger.py` — mirrors `001-expense-entry`'s expense-list validation
- [x] T028 [US3] Build the `JournalEntryList` component with account/date-range filters and a link back to each entry's source expense entry in `frontend/src/components/JournalEntryList.tsx`
- [x] T029 [US3] Build the ledger page wiring `JournalEntryList` in `frontend/src/app/ledger/page.tsx`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T030 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the `suggest_account_coding` tool and the auto-posting flow, and confirm the shareable URL in `.specify/memory/constitution.md`/`README.md` still reflects the current system — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [x] T031 [P] Update `README.md` to document the new `ACCOUNT_CODING_CONFIDENCE_THRESHOLD` environment variable
- [x] T032 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [x] T033 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories, but its implementation necessarily includes the core posting/reversal mechanics (T013–T014) that US2 also relies on — see the note in Phase 4.
  - US2 (P2) depends on US1's `post_journal_entry`/`reverse_journal_entry` existing (same reasoning `001-expense-entry`'s US4 depended on US1's `create_entry`).
  - US3 (P3) depends on US1/US2 having posted at least some journal entries to list, but its own list/filter logic is independently testable once seeded data exists.
  - Recommended order given these dependencies: US1 → US2 → US3 (matches priority order already).
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### Within Each User Story

- Services before endpoints; endpoints before frontend components that call them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- Foundational model tasks T003, T004, T005 can run in parallel (different files); T006 (migration) depends on all three.
- Foundational schema tasks T007, T008, T009 can run in parallel with each other and with T002.
- Within each user story phase, backend service/endpoint tasks are sequential (same files depend on prior steps), but frontend component tasks for a story can often start once that story's endpoint contracts are stable.
- Polish tasks T030, T031, T033 can all run in parallel with each other.

---

## Parallel Example: Foundational Phase

```bash
# Launch model creation together (different files, no cross-dependencies):
Task: "Create Account SQLAlchemy model in backend/src/models/account.py"
Task: "Create AccountCoding SQLAlchemy model in backend/src/models/account_coding.py"
Task: "Create JournalEntry SQLAlchemy model in backend/src/models/journal_entry.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (critical — blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently.
5. Demo if ready — this alone delivers AI-suggested coding with review/approve/correct.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (MVP — coding + implicit posting for high-confidence entries).
3. Add US2 → validate → demo (deletion-triggered reversal, dedicated journal-entry detail view).
4. Add US3 → validate → demo (full ledger browsing).
5. Polish phase → diagram update, README, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T030 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `002-ledger-journal-entries` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.

### T032 findings (quickstart validation)

Ran the full `quickstart.md` flow live against `docker-compose up`. Found and
fixed three real bugs during implementation/verification, beyond the two
design corrections already noted in `data-model.md`:

1. **PATCH .../coding 500 (MissingGreenlet)**: identical class of bug to the
   one found in `001-expense-entry`'s T043 — partial `session.refresh`
   calls left relationship data expired, triggering an async lazy-load
   inside Pydantic's synchronous validation. Fixed by having every mutating
   `ledger_service` function finish with a re-fetch through `get_coding()`.
2. **Stale relationship data after a direct FK mutation**: setting
   `coding.account_id` directly doesn't refresh the already-loaded
   `.account`/`.journal_entries` relationships in the session's identity
   map — `selectinload` skips relationships that are already populated.
   Fixed by adding `execution_options(populate_existing=True)` to
   `get_coding()`'s query.
3. **`active_journal_entry()` could pick a reversal entry as "active"**: a
   reversal entry is itself `status="posted"` (a real, completed
   transaction) — a second correction could therefore reverse the *previous
   correction's reversal* instead of the real active posting, corrupting
   the audit trail. Fixed by only considering entries with
   `reverses_journal_entry_id IS NULL` as "active."

All fixes verified live: auto-post above threshold, pending-review below
threshold + manual approve, single and double correction (with a correct,
clean reversal chain each time), deletion-triggered reversal preserving
history (FR-012), and filtered ledger listing all confirmed working end to
end via the running `docker-compose` stack.
