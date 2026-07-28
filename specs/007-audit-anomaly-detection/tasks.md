---
description: "Task list for audit and anomaly detection feature implementation"
---

# Tasks: Audit & Anomaly Detection (Fraud/Anomaly Flags)

**Input**: Design documents from `/specs/007-audit-anomaly-detection/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/audit-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching prior features' precedent.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root, per `plan.md`'s Project Structure.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 [P] Add `scikit-learn` as a dependency in `backend/pyproject.toml`, per `research.md`'s hybrid-detector decision
- [X] T002 Create this feature's new file skeleton: `backend/src/models/{audit_run,anomaly_flag}.py`, `backend/src/schemas/audit.py`, `backend/src/services/audit_service.py`, `backend/src/agent/audit_tools.py`, `backend/src/api/audit.py`; `frontend/src/app/audit/`, `frontend/src/components/{AuditRunner.tsx,AuditHistory.tsx}`, `frontend/src/services/auditApi.ts` — per `plan.md`'s Project Structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Create the `AuditRun` SQLAlchemy model (`id`, `start`, `end`, `entries_evaluated`, `entries_flagged`, `status` enum(`completed`, `insufficient_data`), `created_at`) in `backend/src/models/audit_run.py`, per `data-model.md`
- [X] T004 [P] Create the `AnomalyFlag` SQLAlchemy model (`id`, `audit_run_id` FK `ON DELETE CASCADE`, `journal_entry_id` FK `ON DELETE CASCADE`, `score`, `reason_categories` (array of text), `explanation`, `resolution` enum(`unreviewed`, `confirmed_issue`, `false_positive`, `no_action_needed`) default `unreviewed`, `resolved_at`, `created_at`) in `backend/src/models/anomaly_flag.py`, per `data-model.md`
- [X] T005 Write the Alembic migration creating both tables from T003–T004 in `backend/migrations/versions/` (depends on T003, T004)
- [X] T006 [P] Create `AuditRun`/`AnomalyFlag` Pydantic schemas (`AuditRunResponse` with a nested `flags` list, `AnomalyFlagResponse`, `AuditRunSummary` for the history list, `ResolveFlagRequest`) in `backend/src/schemas/audit.py`, per `contracts/audit-api.md`
- [X] T007 [P] Implement `AuditService._evaluate_entries(session, start, end)` (queries active posted journal entries — `status='posted' AND reverses_journal_entry_id IS NULL`, reused from `002`/`005` — within `[start, end]`, defaulting to the whole ledger to date when omitted) in `backend/src/services/audit_service.py`, per `research.md`'s active-postings decision, FR-010

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Run an Audit and See Flagged Entries (Priority: P1) 🎯 MVP

**Goal**: An admin triggers an audit over a chosen date range and sees a ranked list of the most anomalous posted journal entries, each with a plain-language explanation.

**Independent Test**: Post a mix of typical and deliberately unusual journal entries, run an audit over that period, and confirm the unusual entries are flagged with explanations that correctly describe what made each one stand out, while typical entries are not flagged.

- [ ] T008 [US1] Implement `AuditService._detect(entries)` — fits a `scikit-learn` `IsolationForest` (fixed random seed) on each evaluated entry's feature vector (amount, one-hot debit/credit account pair, day-of-week, day-of-month), plus the exact-duplicate and round-number rule checks; merges both into one ranked list of raw flags, each with a `score` and `reason_categories` — in `backend/src/services/audit_service.py`, per `research.md`'s hybrid-detector decision, FR-001, FR-004, FR-005 (depends on T007)
- [ ] T009 [US1] Implement the `explain_flags` agent tool (one batched LLM call: a run's list of raw flags → a plain-language explanation per flag, grounded in each flag's actual `reason_categories` and entry data; deterministic per-category fallback text when no `OPENAI_API_KEY` is configured) in `backend/src/agent/audit_tools.py`, per `research.md`'s batched-narration decision, FR-002, FR-004
- [ ] T010 [US1] Implement `AuditService.run_audit(session, start, end)` — applies `research.md`'s 20-entry minimum threshold (returns an `AuditRun` with `status=insufficient_data` and no flags when unmet); otherwise calls `_detect` then `explain_flags` and persists the `AuditRun` plus its `AnomalyFlag` rows — in `backend/src/services/audit_service.py`, per `data-model.md`'s state transitions, FR-003, FR-008 (depends on T008, T009)
- [ ] T011 [US1] Implement `POST /api/audit/runs` in `backend/src/api/audit.py`, per `contracts/audit-api.md` (depends on T010)
- [ ] T012 [US1] Register the audit router in `backend/src/main.py`
- [ ] T013 [US1] Build the `AuditRunner` component (date-range picker, run button, ranked flagged-entry list showing each entry's score, reason categories, and explanation) in `frontend/src/components/AuditRunner.tsx`
- [ ] T014 [US1] Add `runAudit(start?, end?)` to `frontend/src/services/auditApi.ts`, build the audit page wiring `AuditRunner` in `frontend/src/app/audit/page.tsx`, and add an "Audit" link to `frontend/src/components/Sidebar.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the MVP.

---

## Phase 4: User Story 2 - Review and Resolve a Flagged Entry (Priority: P2)

**Goal**: An admin records a resolution (confirmed issue / false positive / no action needed) for a flagged entry, and that resolution stays visible whenever the flag is viewed again.

**Independent Test**: Flag an entry via an audit run, record a resolution for it, and confirm that resolution is still shown the next time that flag is viewed.

- [ ] T015 [US2] Implement `AuditService.resolve_flag(session, flag_id, resolution)` (validates `resolution` is one of the allowed values; sets `resolved_at`) in `backend/src/services/audit_service.py`, per FR-006 (depends on T004)
- [ ] T016 [US2] Implement `PATCH /api/audit/flags/{id}` in `backend/src/api/audit.py`, per `contracts/audit-api.md` (depends on T015)
- [ ] T017 [US2] Add resolution controls (confirmed issue / false positive / no action needed) to each flagged entry in `frontend/src/components/AuditRunner.tsx`, calling `resolveFlag` (depends on T013)
- [ ] T018 [US2] Add `resolveFlag(flagId, resolution)` to `frontend/src/services/auditApi.ts`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Review Past Audit History (Priority: P3)

**Goal**: An admin views a list of past audit runs and reopens any of them to see its original flagged entries, explanations, and recorded resolutions.

**Independent Test**: Run two or more audits over different periods and confirm both appear in a history view with their date range and flag counts, and each can be reopened to see its original results.

- [ ] T019 [US3] Implement `AuditService.list_audit_runs(session)` and `AuditService.get_audit_run(session, run_id)` in `backend/src/services/audit_service.py`, per FR-007 (depends on T010)
- [ ] T020 [US3] Implement `GET /api/audit/runs` and `GET /api/audit/runs/{id}` in `backend/src/api/audit.py`, per `contracts/audit-api.md` (depends on T019)
- [ ] T021 [US3] Build the `AuditHistory` component (past runs list with date range and flag count; reopens a run to show its full flagged-entry results, reusing `AuditRunner`'s rendering) in `frontend/src/components/AuditHistory.tsx`
- [ ] T022 [US3] Add `listAuditRuns()` and `getAuditRun(id)` to `frontend/src/services/auditApi.ts`, and wire `AuditHistory` into `frontend/src/app/audit/page.tsx` alongside `AuditRunner`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently.

---

## Phase 6: User Story 4 - Ask About Anomalies in Natural Language (Priority: P4)

**Goal**: An admin asks the AI chat interface something like "check this month for anything unusual" and gets the same audit result a direct request for that period would produce, narrated in prose.

**Independent Test**: Ask the chat interface an audit-style question with an implied period, and confirm it triggers the same detection process and returns the same flagged entries and explanations a direct audit run over that period would.

- [ ] T023 [US4] Implement `resolve_audit_request(question, today)` and `narrate_audit_run(run_result)` in `backend/src/agent/audit_tools.py`, per `research.md`'s two-narrow-LLM-calls pattern (mirrors `resolve_report_request`/`narrate_report` from `005`) — `resolve_audit_request` sees only the question text and today's date (never ledger data), returning a `start`/`end` range or `null` if unresolvable; `narrate_audit_run` sees only the already-computed, already-explained run result to produce one short overall summary
- [ ] T024 [US4] Implement `POST /api/agent/audit/query` in `backend/src/api/agent.py` — resolves the date range via `resolve_audit_request`, calls the same `AuditService.run_audit` a direct request would use for that range, then narrates via `narrate_audit_run`; returns `422` with a clarifying question in `narrative` when the period can't be confidently resolved — per `contracts/audit-api.md` (depends on T023, T010)
- [ ] T025 [US4] Add `queryAudit(question)` to `frontend/src/services/auditApi.ts`, add a free-text question box to `frontend/src/app/audit/page.tsx` wired to `POST /api/agent/audit/query`, reusing `AuditRunner`'s rendering for the returned data (depends on T024)

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T026 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the `audit_service` detector, the `resolve_audit_request`/`narrate_audit_run`/`explain_flags` tools, and the audit flow — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [ ] T027 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [ ] T028 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories.
  - US2 (P2) depends on US1's persisted `AnomalyFlag` rows existing to resolve.
  - US3 (P3) depends on US1's persisted `AuditRun`/`AnomalyFlag` rows existing to list and reopen.
  - US4 (P4) depends on US1's `run_audit` existing to call from the natural-language path.
  - Recommended order given these dependencies: US1 → US2 → US3 → US4 (matches priority order already).
- **Polish (Phase 7)**: Depends on all desired phases being complete.

### Within Each User Story

- Service function(s) before endpoint(s); endpoint(s) before the frontend piece that calls them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- T001 can run in parallel with T002 (different files).
- Foundational model tasks T003, T004 can run in parallel (different files); T005 (migration) depends on both. T006, T007 can run in parallel with each other and with T003–T005.
- Within each user story phase, backend service/endpoint tasks are sequential (each depends on the prior step in the same or a related file), but frontend tasks for a story can start once that story's endpoint contract is stable.
- Polish tasks T026 and T028 can run in parallel with each other.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1 independently (insufficient-data, deliberate-anomalies, and clean-period scenarios).
5. Demo if ready — the ledger can now be checked for statistically unusual entries, even without resolution or history yet.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate → demo (run an audit, see flagged entries with explanations).
3. Add US2 → validate → demo (resolve a flag, see it stay resolved).
4. Add US3 → validate → demo (browse past audit history).
5. Add US4 → validate → demo (chat-driven audit requests).
6. Polish phase → diagram update, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T026 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- `scikit-learn` (T001) is this project's first ML/statistics dependency — see `plan.md`'s suggested ADR (`anomaly-detection-approach`) for the reasoning, not yet created pending user consent.
- Commit after each task or logical group, on the `007-audit-anomaly-detection` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
