---
description: "Task list for financial reporting feature implementation"
---

# Tasks: Financial Reporting (Trial Balance, P&L, Balance Sheet, Cash Flow)

**Input**: Design documents from `/specs/005-reporting/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/reports-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching prior features' precedent.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root, per `plan.md`'s Project Structure.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create this feature's new file skeleton: `backend/src/schemas/reports.py`, `backend/src/services/reporting_service.py`, `backend/src/agent/reporting_tools.py`, `backend/src/api/reports.py`; `frontend/src/app/reports/`, `frontend/src/components/{ReportViewer.tsx,ReportQuery.tsx}`, `frontend/src/services/reportsApi.ts` — per `plan.md`'s Project Structure (no new dependency to add — `research.md`'s SQL-over-pandas decision)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create the shared `AccountBalance` schema and the four per-report response schemas (`TrialBalanceResponse`, `ProfitAndLossResponse`, `BalanceSheetResponse`, `CashFlowResponse`) in `backend/src/schemas/reports.py`, per `data-model.md`
- [X] T003 Implement `ReportingService._account_balances(session, as_of=None, start=None, end=None)` — the shared per-account debit/credit aggregation query, filtered to `status = 'posted' AND reverses_journal_entry_id IS NULL` (the active-postings-only rule) and, when given, to a date window — in `backend/src/services/reporting_service.py`, per `research.md`'s "which entries count" and "SQL aggregation, not pandas" decisions (depends on T002)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Generate a Trial Balance (Priority: P1) 🎯 MVP

**Goal**: An admin requests a trial balance as of a chosen date and sees every account's balance, with total debits proven equal to total credits.

**Independent Test**: Post a handful of journal entries, request a trial balance as of today, and confirm every account with activity appears with the correct balance and that total debits equal total credits.

- [X] T004 [US1] Implement `ReportingService.trial_balance(session, as_of)` (defaults `as_of` to today; builds `lines`, `total_debits`, `total_credits`, `is_balanced` from `_account_balances`) in `backend/src/services/reporting_service.py`, per `data-model.md`, FR-002, FR-009 (depends on T003)
- [X] T005 [US1] Implement `GET /api/reports/trial-balance` in `backend/src/api/reports.py`, per `contracts/reports-api.md` (depends on T004)
- [X] T006 [US1] Register the reports router in `backend/src/main.py`
- [X] T007 [US1] Build the `ReportViewer` component (report-type selector defaulting to Trial Balance, an `as_of` date picker, and a rendered statement table showing `is_balanced`) in `frontend/src/components/ReportViewer.tsx`
- [X] T008 [US1] Add `getTrialBalance(asOf?)` to `frontend/src/services/reportsApi.ts`, build the reports page wiring `ReportViewer` in `frontend/src/app/reports/page.tsx`, and add a nav link in `frontend/src/app/layout.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - Generate a Profit & Loss Statement (Priority: P2)

**Goal**: An admin requests a P&L for a chosen period and sees total revenue, total expenses by account, and net profit/loss for that period.

**Independent Test**: Post expense journal entries dated within a chosen period, request a P&L for that period, and confirm the expense total matches the sum of those entries and nets out to the correct profit/loss figure.

- [X] T009 [US2] Implement `ReportingService.profit_and_loss(session, start, end)` (defaults both to the current calendar month when omitted; builds `revenue_lines`/`total_revenue`, `expense_lines`/`total_expenses`, `net_profit` from `_account_balances`) in `backend/src/services/reporting_service.py`, per `data-model.md`, FR-003 (depends on T003)
- [X] T010 [US2] Implement `GET /api/reports/profit-and-loss` in `backend/src/api/reports.py`, per `contracts/reports-api.md` (depends on T009)
- [X] T011 [US2] Extend `ReportViewer` with the Profit & Loss report type (start/end range inputs, revenue/expense line rendering, net profit/loss) in `frontend/src/components/ReportViewer.tsx` (depends on T007)
- [X] T012 [US2] Add `getProfitAndLoss(start?, end?)` to `frontend/src/services/reportsApi.ts`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Generate a Balance Sheet (Priority: P3)

**Goal**: An admin requests a balance sheet as of a chosen date and sees total assets, liabilities, and equity, with assets proven equal to liabilities plus equity.

**Independent Test**: Post journal entries across asset, liability, and equity accounts, request a balance sheet as of a chosen date, and confirm total assets equal total liabilities plus total equity.

- [ ] T013 [US3] Implement `ReportingService.balance_sheet(session, as_of)` (defaults `as_of` to today; builds `asset_lines`/`total_assets`, `liability_lines`/`total_liabilities`, `equity_lines`/`total_equity`, `is_balanced` from `_account_balances`) in `backend/src/services/reporting_service.py`, per `data-model.md`, FR-004, FR-009 (depends on T003)
- [ ] T014 [US3] Implement `GET /api/reports/balance-sheet` in `backend/src/api/reports.py`, per `contracts/reports-api.md` (depends on T013)
- [ ] T015 [US3] Extend `ReportViewer` with the Balance Sheet report type (asset/liability/equity sections, `is_balanced` flag surfaced visibly) in `frontend/src/components/ReportViewer.tsx` (depends on T007)
- [ ] T016 [US3] Add `getBalanceSheet(asOf?)` to `frontend/src/services/reportsApi.ts`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently.

---

## Phase 6: User Story 4 - Generate a Cash Flow Statement (Priority: P4)

**Goal**: An admin requests a cash flow statement for a chosen period and sees the net change in cash, reconciling to the cash account's balance change over that period.

**Independent Test**: Post journal entries affecting the cash account within a chosen period, request a cash flow statement for that period, and confirm the reported net change in cash matches the sum of those entries and reconciles to the cash account's balance change between the period's start and end.

- [ ] T017 [US4] Implement `ReportingService.cash_flow(session, start, end)` (defaults both to the current calendar month when omitted; `opening_balance` from the Cash account's trial-balance-style balance as of `start - 1 day`, `closing_balance` as of `end`, `net_change = closing_balance - opening_balance`) in `backend/src/services/reporting_service.py`, per `data-model.md`, FR-005 (depends on T003)
- [ ] T018 [US4] Implement `GET /api/reports/cash-flow` in `backend/src/api/reports.py`, per `contracts/reports-api.md` (depends on T017)
- [ ] T019 [US4] Extend `ReportViewer` with the Cash Flow report type (start/end range inputs, opening/closing/net-change display) in `frontend/src/components/ReportViewer.tsx` (depends on T007)
- [ ] T020 [US4] Add `getCashFlow(start?, end?)` to `frontend/src/services/reportsApi.ts`

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Cross-Cutting - Natural-Language Report Queries (FR-007)

> **Note**: This phase is not part of any single user story because FR-007 (the chat path) applies to *all four* reports at once — `resolve_report_request` must classify among all four report types, so it can't meaningfully exist until US1–US4's report functions all exist to be classified into and called. This mirrors `004-bank-reconciliation`'s note about why its cross-cutting AI tool was developed in its own phase rather than a single user story.

- [ ] T021 [P] Implement `resolve_report_request(question, today)` and `narrate_report(report_type, computed_result)` in `backend/src/agent/reporting_tools.py`, per `research.md`'s two-narrow-LLM-calls decision — `resolve_report_request` sees only the question text and today's date (never ledger data); `narrate_report` sees only the already-computed result object (never raw journal-entry rows) (depends on T004, T009, T013, T017 existing to classify among)
- [ ] T022 Implement `POST /api/agent/reports/query` in `backend/src/api/agent.py` — resolves the request via `resolve_report_request`, calls the matching `ReportingService` function for the exact same data a direct request would get, then narrates via `narrate_report`; returns `422` with a clarifying question in `narrative` when the report/period can't be confidently resolved — per `contracts/reports-api.md` (depends on T021)
- [ ] T023 [P] Add `queryReport(question)` to `frontend/src/services/reportsApi.ts`, build the `ReportQuery` component (free-text question box, narrated answer, and the underlying data table reusing `ReportViewer`'s rendering) in `frontend/src/components/ReportQuery.tsx`, and wire it into `frontend/src/app/reports/page.tsx` alongside `ReportViewer` (depends on T022)

**Checkpoint**: All four reports are requestable both directly and via natural language, with numerically identical figures either way (FR-007).

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T024 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the `resolve_report_request`/`narrate_report` tools and the reporting flow — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [ ] T025 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [ ] T026 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - US1 (P1), US2 (P2), US3 (P3), and US4 (P4) each depend only on the shared `_account_balances` helper (T003) — none depend on each other, since each report type is an independent aggregation over the same data.
  - Recommended order given priority: US1 → US2 → US3 → US4.
- **Cross-Cutting NL Queries (Phase 7)**: Depends on all of US1–US4 being complete (see the note in Phase 7).
- **Polish (Phase 8)**: Depends on all desired phases being complete.

### Within Each User Story

- Service function before endpoint; endpoint before the frontend extension that calls it.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- T002 (schemas) has no dependencies within Phase 2 other than being needed by T003.
- Once Foundational (T002–T003) is complete, US1–US4's service-layer tasks (T004, T009, T013, T017) touch the same file (`reporting_service.py`) but are logically independent — safe to implement sequentially in one file or split across parallel work if care is taken to avoid merge conflicts.
- Frontend `reportsApi.ts` additions (T008, T012, T016, T020) are additive to the same file per story but don't depend on each other's code, only on their own story's endpoint being ready.
- Polish tasks T024 and T026 can run in parallel with each other.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the Trial Balance portion of `quickstart.md` independently.
5. Demo if ready — the ledger's balance is now visible and provably consistent, even without the other three statements yet.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (Trial Balance).
3. Add US2 → validate → demo (Profit & Loss).
4. Add US3 → validate → demo (Balance Sheet).
5. Add US4 → validate → demo (Cash Flow).
6. Add the natural-language query phase → validate → demo (chat-driven reporting).
7. Polish phase → diagram update, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T024 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `005-reporting` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
