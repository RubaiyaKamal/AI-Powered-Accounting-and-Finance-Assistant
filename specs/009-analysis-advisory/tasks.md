---
description: "Task list for analysis and advisory NL Q&A feature implementation"
---

# Tasks: Analysis & Advisory / Natural-Language Q&A

**Input**: Design documents from `/specs/009-analysis-advisory/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/analysis-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching prior features' precedent.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root, per `plan.md`'s Project Structure.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create this feature's new file skeleton: `backend/src/schemas/analysis.py`, `backend/src/services/analysis_service.py`, `backend/src/agent/analysis_tools.py`, `backend/src/api/analysis.py`; `frontend/src/app/analysis/`, `frontend/src/components/{SpendingQuery.tsx,SpendingBreakdown.tsx,SpendingForecast.tsx}`, `frontend/src/services/analysisApi.ts` — per `plan.md`'s Project Structure (no new dependency — `research.md`'s decisions reuse `scikit-learn`, already present)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create the Pydantic schemas (`SpendingAmountResponse`; `BreakdownLine` + `SpendingBreakdownResponse`; `ComparisonLine` + `SpendingComparisonResponse`; `HistoricalPoint` + `SpendingForecastResponse` with `status`; `SpendingQueryRequest`, `SpendingQueryResponse`) in `backend/src/schemas/analysis.py`, per `data-model.md` and `contracts/analysis-api.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Ask a Natural-Language Spending Question (Priority: P1) 🎯 MVP

**Goal**: An admin asks a plain-language spending question and gets a direct, accurate answer grounded in the ledger.

**Independent Test**: Post expense activity to a known account in a known period, ask a natural-language question about that account and period, and confirm the answer states the correct figure.

- [X] T003 [US1] Implement `AnalysisService.spending_amount(session, account_name, start, end)` — matches `account_name` case-insensitively against the chart of accounts, raising `NotFoundError` if no match (FR-005); otherwise calls `reporting_service.profit_and_loss(session, start, end)` and returns the matching `expense_lines` entry, or a zero-amount result if the account exists but had no activity that period — in `backend/src/services/analysis_service.py`, per FR-001, FR-005, `data-model.md`
- [X] T004 [US1] Implement `resolve_spending_request(question, today, account_names)` in `backend/src/agent/analysis_tools.py` — classifies a question into one of the four request kinds (`amount`, `breakdown`, `comparison`, `forecast`) or `null`, plus parameters (`account_name` bound to the given real account list for `amount`; `start`/`end` for `amount`/`breakdown`/forecast target; `period_a`/`period_b` for `comparison`); mirrors `suggest_account_coding`'s bounded-choice account matching and `007`/`008`'s "unresolvable, don't guess" shape — per `research.md`
- [X] T005 [US1] Implement `narrate_spending_result(request_kind, computed_result)` in `backend/src/agent/analysis_tools.py` — narrates an already-computed result into prose per `request_kind`, explicitly framing a forecast as an estimate (FR-008); deterministic per-kind fallback template when no `OPENAI_API_KEY` is configured — per `research.md`
- [X] T006 [US1] Implement `POST /api/agent/analysis/query` in `backend/src/api/agent.py` — fetches the real expense account names, resolves the question via `resolve_spending_request`, handles the `amount` branch by calling `AnalysisService.spending_amount`, narrates via `narrate_spending_result`; returns `422` with a clarifying question when `request_kind` is `null`, no account could be matched, or the resolved kind isn't wired up yet (`breakdown`/`comparison`/`forecast`, added in later phases) — per `contracts/analysis-api.md` (depends on T003, T004, T005)
- [X] T007 [US1] Build the `SpendingQuery` component (free-text question box, narrated answer, underlying data rendered) in `frontend/src/components/SpendingQuery.tsx`
- [X] T008 [US1] Add `queryAnalysis(question)` to `frontend/src/services/analysisApi.ts`, build the analysis page wiring `SpendingQuery` in `frontend/src/app/analysis/page.tsx`, and add an "Analysis" link to `frontend/src/components/Sidebar.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - View Spending Pattern Analysis (Priority: P2)

**Goal**: An admin views a ranked spending breakdown for a period, and a comparison of spending between two periods, directly.

**Independent Test**: Post expense activity across several accounts in a period, request a breakdown for that period, and confirm every account with activity appears with its correct total, ranked highest to lowest; separately, request a comparison between two periods and confirm the reported change matches the actual difference in posted activity.

- [X] T009 [US2] Implement `AnalysisService.breakdown(session, start, end)` — defaults both to the current calendar month when omitted; calls `reporting_service.profit_and_loss`, sorts `expense_lines` by balance descending, computes each line's share of the total — in `backend/src/services/analysis_service.py`, per FR-003(b), FR-006, `data-model.md`
- [X] T010 [US2] Implement `AnalysisService.comparison(session, period_a_start, period_a_end, period_b_start, period_b_end)` — calls `profit_and_loss` twice and merges the results by account (an account absent from one period contributes `0.00` for it), computing the change per account and overall — in `backend/src/services/analysis_service.py`, per FR-003(c), FR-006, `data-model.md`
- [X] T011 [US2] Implement `GET /api/analysis/breakdown` and `GET /api/analysis/comparison` in `backend/src/api/analysis.py`, per `contracts/analysis-api.md` (depends on T009, T010)
- [X] T012 [US2] Register the analysis router in `backend/src/main.py`
- [X] T013 [US2] Wire the `breakdown` and `comparison` branches into `POST /api/agent/analysis/query` in `backend/src/api/agent.py`, calling the same `AnalysisService` functions T011's endpoints use (depends on T009, T010, T006)
- [X] T014 [US2] Build the `SpendingBreakdown` component (period picker + ranked breakdown table; a two-period picker + comparison table) in `frontend/src/components/SpendingBreakdown.tsx`
- [X] T015 [US2] Add `getBreakdown`/`getComparison` to `frontend/src/services/analysisApi.ts` and wire `SpendingBreakdown` into `frontend/src/app/analysis/page.tsx`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Get a Spending Forecast (Priority: P3)

**Goal**: An admin requests a spending forecast for a future period and receives an estimate, clearly labeled as such, with a plain-language explanation.

**Independent Test**: Post a consistent trend of expense activity across several past periods, request a forecast for the next period, and confirm the forecast is clearly labeled an estimate, is reasonably consistent with the trend, and comes with a plain-language explanation of its method and data.

- [X] T016 [US3] Implement `AnalysisService.forecast(session, target_start, target_end)` — gathers up to the past 6 complete calendar months' `profit_and_loss` `total_expenses` (`research.md`'s lookback window); if fewer than 3 of those months have any posted activity, returns `status="insufficient_data"` (FR-009); otherwise fits `scikit-learn`'s `LinearRegression` on month-index → `total_expenses`, predicts the target period, and returns `is_estimate=true` with the method description and the historical points used — in `backend/src/services/analysis_service.py`, per FR-007, FR-008, FR-009, `data-model.md`
- [X] T017 [US3] Implement `GET /api/analysis/forecast` in `backend/src/api/analysis.py`, per `contracts/analysis-api.md` (depends on T016)
- [X] T018 [US3] Wire the `forecast` branch into `POST /api/agent/analysis/query` in `backend/src/api/agent.py`, calling the same `AnalysisService.forecast` function T017's endpoint uses (depends on T016, T006)
- [X] T019 [US3] Build the `SpendingForecast` component (future-period picker, forecast figure clearly labeled an estimate, method and historical-points explanation) in `frontend/src/components/SpendingForecast.tsx`
- [X] T020 [US3] Add `getForecast` to `frontend/src/services/analysisApi.ts` and wire `SpendingForecast` into `frontend/src/app/analysis/page.tsx`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently.

---

## Phase 6: User Story 4 - Ask for Patterns or a Forecast in Natural Language (Priority: P4)

**Goal**: An admin asks the chat interface for a breakdown, comparison, or forecast and gets the same result the equivalent direct request would produce.

**Independent Test**: Ask the chat interface a pattern or forecast question with a clearly implied period, and confirm it returns the same result a direct breakdown or forecast request for that period would.

> **Note**: `resolve_spending_request` (T004) and the query endpoint's routing (T006, extended by T013 and T018) already cover all four request kinds by the time User Story 3 completes — the resolver's classification vocabulary was written once, upfront, in Phase 3, since correctly discriminating "amount" from the other three kinds requires knowing about all of them from the start. This phase is about confirming the natural-language path for `breakdown`/`comparison`/`forecast` questions actually behaves per FR-010, not building new backend machinery — the groundwork was laid incrementally across User Stories 1–3 rather than deferred to its own late cross-cutting phase the way `005-reporting`'s NL layer was.

- [X] T021 [US4] Verify and, if needed, adjust `resolve_spending_request`'s prompt so breakdown-, comparison-, and forecast-shaped natural-language questions reliably classify into the correct `request_kind` with correctly extracted periods, in `backend/src/agent/analysis_tools.py`, per FR-010, spec Edge Cases
- [X] T022 [US4] Confirm `frontend/src/components/SpendingQuery.tsx` correctly renders `breakdown`/`comparison`/`forecast` result shapes returned via the chat path (not just `amount`), reusing `SpendingBreakdown`/`SpendingForecast`'s rendering where practical

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T023 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the spending-analysis flow, the deterministic forecaster, and the `resolve_spending_request`/`narrate_spending_result` tools — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [X] T024 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [X] T025 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories — it's the only story with no direct-REST counterpart, delivered entirely through the natural-language endpoint.
  - US2 (P2) depends on US1's query endpoint (T006) existing to extend with new branches; its own direct endpoints are independent.
  - US3 (P3) depends on the same query endpoint, for the same reason.
  - US4 (P4) depends on US1–US3's resolver and branches all being in place — see the note in Phase 6.
  - Recommended order given these dependencies: US1 → US2 → US3 → US4 (matches priority order already).
- **Polish (Phase 7)**: Depends on all desired phases being complete.

### Within Each User Story

- Service function(s) before endpoint(s); direct endpoint and NL-branch wiring before the frontend piece that calls them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- T002 (schemas) has no dependencies within Phase 2.
- T009 and T010 (breakdown, comparison service functions) touch the same file but are logically independent — safe to implement sequentially in one file or split across parallel work if care is taken to avoid merge conflicts.
- Frontend component tasks for a story can start once that story's endpoint contract is stable.
- Polish tasks T023 and T025 can run in parallel with each other.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently (a natural-language amount question, the no-activity and unknown-account edge cases).
5. Demo if ready — an admin can already ask spending questions in plain language, even without breakdowns, comparisons, or forecasts yet.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (ask a spending question in natural language — the MVP).
3. Add US2 → validate → demo (spending breakdowns and period comparisons).
4. Add US3 → validate → demo (spending forecasts).
5. Add US4 → validate → demo (patterns and forecasts via chat too).
6. Polish phase → diagram update, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T023 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- This feature introduces no new backend dependency and no new database tables (`research.md`, `data-model.md`) — `scikit-learn` is already present from `007`.
- Commit after each task or logical group, on the `009-analysis-advisory` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
