---
description: "Task list for bank reconciliation feature implementation"
---

# Tasks: Bank/Vendor Reconciliation

**Input**: Design documents from `/specs/004-bank-reconciliation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/reconciliation-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching prior features' precedent.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- File paths are relative to the repository root, per `plan.md`'s Project Structure.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Add `rapidfuzz` as a dependency in `backend/pyproject.toml`, per `research.md`'s fuzzy-matching decision
- [ ] T002 Create this feature's new file skeleton: `backend/src/models/{bank_transaction,match}.py`, `backend/src/schemas/{bank_transaction,match}.py`, `backend/src/services/reconciliation_service.py`, `backend/src/agent/reconciliation_tools.py`, `backend/src/api/reconciliation.py`; `frontend/src/app/reconciliation/`, `frontend/src/components/{BankStatementImport.tsx,ReconciliationQueue.tsx}`, `frontend/src/services/reconciliationApi.ts` — per `plan.md`'s Project Structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 [P] Create the `BankTransaction` SQLAlchemy model (`id`, `date`, `amount`, `description`, `suggested_expense_entry_id` FK `ON DELETE SET NULL`, `ai_reasoning`, `created_at`; unique constraint on `(date, amount, description)`) in `backend/src/models/bank_transaction.py`, per `data-model.md`
- [ ] T004 [P] Create the `Match` SQLAlchemy model (`id`, `bank_transaction_id` FK unique, `expense_entry_id` FK `ON DELETE CASCADE` nullable with a partial unique index where not null, `source`, `status`, `ai_reasoning`, `created_at`) in `backend/src/models/match.py`, per `data-model.md`
- [ ] T005 Write the Alembic migration creating both tables from T003–T004, including the `(date, amount, description)` unique constraint and the partial unique index on `matches.expense_entry_id`, in `backend/migrations/versions/`
- [ ] T006 [P] Create `BankTransaction` Pydantic response schemas in `backend/src/schemas/bank_transaction.py`, per `contracts/reconciliation-api.md`
- [ ] T007 [P] Create `Match` Pydantic response schemas in `backend/src/schemas/match.py`, per `contracts/reconciliation-api.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Import bank statement transactions (Priority: P1) 🎯 MVP

**Goal**: An admin uploads a bank statement CSV and its transaction lines are recorded, with exact duplicates detected and skipped.

**Independent Test**: Import a set of bank transaction lines and confirm they appear in the system, unmatched, ready for reconciliation; re-import the same file and confirm no duplicates are created.

- [ ] T008 [US1] Implement `ReconciliationService.parse_csv` (case-insensitive `date`/`amount`/`description` column matching; returns valid rows plus a list of skipped invalid rows with reasons) in `backend/src/services/reconciliation_service.py`, per FR-001, Edge Cases
- [ ] T009 [US1] Implement `ReconciliationService.import_transactions` (inserts parsed rows as `BankTransaction`s, skipping exact `(date, amount, description)` duplicates via T003's unique constraint) in `backend/src/services/reconciliation_service.py`, per FR-003 (depends on T008)
- [ ] T010 [US1] Implement `POST /api/reconciliation/import` (multipart CSV upload; calls `parse_csv` + `import_transactions`; returns the import summary shape from `contracts/reconciliation-api.md`) in `backend/src/api/reconciliation.py`
- [ ] T011 [US1] Register the reconciliation router in `backend/src/main.py`
- [ ] T012 [US1] Build the `BankStatementImport` component (file upload control, shows the import summary response) in `frontend/src/components/BankStatementImport.tsx`
- [ ] T013 [US1] Add `importBankStatement(file)` to `frontend/src/services/reconciliationApi.ts`, build the reconciliation page wiring `BankStatementImport` in `frontend/src/app/reconciliation/page.tsx`, and add a nav link in `frontend/src/app/layout.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP (import + dedupe, no matching yet).

---

## Phase 4: User Story 2 - Automatic matching of confident pairs (Priority: P2)

**Goal**: Imported bank transactions are automatically paired with the expense entries they clearly correspond to, without requiring per-item admin review.

**Independent Test**: Import a bank transaction that clearly corresponds to an existing expense entry and confirm the system marks them as matched to each other automatically, without any manual action.

> **Note**: `adjudicate_match` (T016) is developed in this phase, not User Story 3, because matching's three-way classification (auto/ambiguous/none) can't complete without it — the ambiguous branch needs the AI's choice and reasoning at import time, not lazily when the queue is later viewed (`research.md`). This mirrors how `002-ledger-journal-entries`'s core posting logic ended up living in its own User Story 1 for the same structural reason. User Story 3's own scope is the queue-viewing/resolution endpoints and UI that consume what this phase produces.

- [ ] T014 [US2] Implement `ReconciliationService.score_candidates` (for a `BankTransaction`, finds `ExpenseEntry` rows with an exact amount match and a date within the configured window, and computes a `rapidfuzz` description-similarity score for each) in `backend/src/services/reconciliation_service.py`, per `research.md`'s Matching Thresholds decision
- [ ] T015 [US2] Implement `ReconciliationService.classify_match` (applies the auto/ambiguous/none thresholds from `research.md` to `score_candidates`'s output) in `backend/src/services/reconciliation_service.py` (depends on T014)
- [ ] T016 [US2] Implement the `adjudicate_match` agent tool (bank transaction + a bounded list of ambiguous candidates → a chosen `expense_entry_id` or `null`, plus reasoning; never sees the full expense-entry table) in `backend/src/agent/reconciliation_tools.py`, per `research.md`'s AI Adjudication Tool decision
- [ ] T017 [US2] Implement `ReconciliationService.run_matching_for_transaction` (auto → creates a `Match` row with `source=auto`, `status=confirmed`; ambiguous → calls `adjudicate_match`, stores `suggested_expense_entry_id`/`ai_reasoning` on the `BankTransaction`; none → leaves it unmatched with no suggestion) in `backend/src/services/reconciliation_service.py`, per FR-004–FR-007 (depends on T015, T016)
- [ ] T018 [US2] Wire `run_matching_for_transaction` into `POST /api/reconciliation/import` so every newly imported (non-duplicate) transaction is matched immediately in `backend/src/api/reconciliation.py` (depends on T010, T017)
- [ ] T019 [US2] Implement `GET /api/reconciliation/bank-transactions` (list with optional `status` filter) in `backend/src/api/reconciliation.py`, per `contracts/reconciliation-api.md`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Review ambiguous and unmatched transactions (Priority: P3)

**Goal**: An admin reviews a queue of transactions the system couldn't confidently auto-match, sees the AI's reasoning for any ambiguous candidates, and resolves each one (confirm, correct, or dismiss) — with resolved items never resurfacing and confirmed matches undoable.

**Independent Test**: Trigger a reconciliation pass that produces one ambiguous and one fully-unmatched transaction, confirm both appear in the review queue (the ambiguous one showing AI reasoning), and confirm resolving each removes it from the queue.

- [ ] T020 [US3] Implement `ReconciliationService.list_review_queue` (unmatched `BankTransaction`s — no `Match` row — with `candidates_considered` recomputed live via T014 for display, alongside any already-persisted `suggested_expense_entry_id`/`ai_reasoning`) in `backend/src/services/reconciliation_service.py`, per FR-006, FR-007
- [ ] T021 [US3] Implement `GET /api/reconciliation/review-queue` in `backend/src/api/reconciliation.py`, per `contracts/reconciliation-api.md`
- [ ] T022 [US3] Implement `ReconciliationService.confirm_match`, `ReconciliationService.dismiss_transaction`, and `ReconciliationService.undo_match` (enforcing FR-010's one-to-one constraint via T004's unique indexes, and FR-009's no-resurface guarantee via `Match` row existence) in `backend/src/services/reconciliation_service.py`, per FR-008, FR-009, FR-011
- [ ] T023 [US3] Implement `POST /api/reconciliation/bank-transactions/{id}/match`, `POST /api/reconciliation/bank-transactions/{id}/dismiss`, and `DELETE /api/reconciliation/matches/{id}` in `backend/src/api/reconciliation.py`, per `contracts/reconciliation-api.md`
- [ ] T024 [US3] Build the `ReconciliationQueue` component (matched-transactions list plus the review queue with AI reasoning display, confirm/correct/dismiss controls, and an undo control on confirmed matches) in `frontend/src/components/ReconciliationQueue.tsx`
- [ ] T025 [US3] Wire `ReconciliationQueue` into the reconciliation page in `frontend/src/app/reconciliation/page.tsx`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T026 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the `adjudicate_match` tool and the CSV-import/matching flow — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [ ] T027 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [ ] T028 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories.
  - US2 (P2) depends on US1's import path existing (it matches transactions US1 creates), and its own implementation necessarily includes the `adjudicate_match` tool that US3 also relies on — see the note in Phase 4.
  - US3 (P3) depends on US2's matching/classification logic having run and persisted suggestions to display and resolve.
  - Recommended order given these dependencies: US1 → US2 → US3 (matches priority order already).
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### Within Each User Story

- Services before endpoints; endpoints before frontend components that call them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- T001 can run in parallel with T002 (different files).
- Foundational model tasks T003, T004 can run in parallel (different files); T005 (migration) depends on both. T006, T007 can run in parallel with each other and with T003–T005.
- Within each user story phase, backend service/endpoint tasks are sequential (same files depend on prior steps), but frontend component tasks for a story can often start once that story's endpoint contracts are stable.
- Polish tasks T026 and T028 can run in parallel with each other.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently (import + duplicate detection).
5. Demo if ready — bank data is now in the system, even without matching yet.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (import + dedupe).
3. Add US2 → validate → demo (automatic matching, the core time-saving value).
4. Add US3 → validate → demo (full reconciliation workflow, including ambiguous review).
5. Polish phase → diagram update, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T026 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `004-bank-reconciliation` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
