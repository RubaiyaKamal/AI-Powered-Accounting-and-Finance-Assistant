---
description: "Task list for tax and compliance summaries feature implementation"
---

# Tasks: Tax & Compliance Summaries

**Input**: Design documents from `/specs/008-tax-compliance-summaries/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tax-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching prior features' precedent.

**Organization**: Tasks are grouped by user story (from `spec.md`) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root, per `plan.md`'s Project Structure.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create this feature's new file skeleton: `backend/src/models/{tax_rules_document,tax_rules_document_chunk,tax_summary}.py`, `backend/src/schemas/tax.py`, `backend/src/services/{tax_document_service,tax_summary_service}.py`, `backend/src/agent/tax_tools.py`, `backend/src/api/tax.py`; `frontend/src/app/tax/`, `frontend/src/components/{TaxDocumentLibrary.tsx,TaxSummaryGenerator.tsx,TaxSummaryHistory.tsx}`, `frontend/src/services/taxApi.ts` — per `plan.md`'s Project Structure (no new dependency to add — `research.md`'s retrieval decision reuses `openai` and `numpy`, both already present)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create the `TaxRulesDocument` SQLAlchemy model (`id`, `title`, `content`, `created_at`) in `backend/src/models/tax_rules_document.py`, per `data-model.md`
- [X] T003 [P] Create the `TaxRulesDocumentChunk` SQLAlchemy model (`id`, `document_id` FK `ON DELETE CASCADE`, `chunk_index`, `chunk_text`, `embedding` nullable array of float, `created_at`) in `backend/src/models/tax_rules_document_chunk.py`, per `data-model.md`
- [X] T004 [P] Create the `TaxSummary` SQLAlchemy model (`id`, `start`, `end`, `status` enum(`draft`, `signed_off`) default `draft`, `total_revenue`, `total_expenses`, `net_profit`, `cited_passages` JSON, `narrative`, `generated_at`, `signed_off_at` nullable) in `backend/src/models/tax_summary.py`, per `data-model.md`
- [X] T005 Write the Alembic migration creating all three tables from T002–T004 in `backend/migrations/versions/` (depends on T002, T003, T004)
- [X] T006 [P] Create the Pydantic schemas (`TaxRulesDocumentResponse`, `TaxRulesDocumentSummary`, `TaxRulesDocumentListResponse`, `TaxSummaryResponse` with a `cited_passages` list, `TaxSummarySummary` for the history list, `TaxSummaryListResponse`, `TaxSummaryTriggerRequest`) in `backend/src/schemas/tax.py`, per `contracts/tax-api.md`
- [X] T007 [P] Implement `embed_text(text)` in `backend/src/agent/tax_tools.py` — calls the OpenAI embeddings API via the `openai` client already available through `openai-agents`; returns `None` when no `OPENAI_API_KEY` is configured, per `research.md`'s retrieval decision

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Build a Tax Rules Reference Library (Priority: P1)

**Goal**: An admin adds, views, and removes tax rules reference documents in a library that future summaries retrieve from.

**Independent Test**: Add a reference document, confirm it appears in the library with its content viewable, and confirm removing it makes it disappear from the library.

- [X] T008 [US1] Implement `TaxDocumentService.add_document(session, title, content)` — splits `content` into paragraph-sized chunks (`research.md`'s chunking decision), calls `embed_text` for each chunk, persists the `TaxRulesDocument` and its `TaxRulesDocumentChunk` rows — in `backend/src/services/tax_document_service.py`, per FR-001 (depends on T002, T003, T007)
- [X] T009 [US1] Implement `TaxDocumentService.list_documents`, `get_document`, and `delete_document` in `backend/src/services/tax_document_service.py`, per FR-001
- [X] T010 [US1] Implement `POST /api/tax/documents`, `GET /api/tax/documents`, `GET /api/tax/documents/{id}`, `DELETE /api/tax/documents/{id}` in `backend/src/api/tax.py`, per `contracts/tax-api.md` (depends on T008, T009)
- [X] T011 [US1] Register the tax router in `backend/src/main.py`
- [X] T012 [US1] Build the `TaxDocumentLibrary` component (add-document form with title/content fields, list of existing documents with view and remove controls) in `frontend/src/components/TaxDocumentLibrary.tsx`
- [X] T013 [US1] Add `addDocument`/`listDocuments`/`getDocument`/`deleteDocument` to `frontend/src/services/taxApi.ts`, build the tax page wiring `TaxDocumentLibrary` in `frontend/src/app/tax/page.tsx`, and add a "Tax" link to `frontend/src/components/Sidebar.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Generate a Draft Tax/Compliance Summary (Priority: P2)

**Goal**: An admin requests a summary for a chosen period and receives a draft grounded in the period's actual computed figures and the most relevant reference passages, clearly labeled unreviewed.

**Independent Test**: Post journal entries in a period, add a reference document relevant to that activity, request a summary for that period, and confirm the draft shows the correct figures, cites the relevant passage, and is labeled a draft.

- [ ] T014 [US2] Implement `TaxSummaryService._retrieve_passages(session, query_text, top_k)` — embeds `query_text` via `embed_text`; ranks chunks with an embedding by cosine similarity (`numpy`) and chunks without one (no API key at add-time) by keyword overlap; returns the top matches as `{document_title, chunk_text}` — in `backend/src/services/tax_summary_service.py`, per `research.md`'s retrieval decision
- [ ] T015 [US2] Implement the `draft_summary_narrative` agent tool (figures + cited passages → prose; explicitly states when `cited_passages` is empty rather than inventing guidance; deterministic fallback when no `OPENAI_API_KEY` is configured) in `backend/src/agent/tax_tools.py`, per `research.md`, FR-004, FR-005
- [ ] T016 [US2] Implement `TaxSummaryService.generate(session, start, end)` (defaults both to the current calendar month when omitted; calls `reporting_service.profit_and_loss` for the period's figures; builds a retrieval query from the period and figures; calls `_retrieve_passages` then `draft_summary_narrative`; persists a new `TaxSummary` row with `status=draft`) in `backend/src/services/tax_summary_service.py`, per FR-002, FR-003, FR-006, `data-model.md`'s state transitions (depends on T014, T015)
- [ ] T017 [US2] Implement `POST /api/tax/summaries` in `backend/src/api/tax.py`, per `contracts/tax-api.md` (depends on T016)
- [ ] T018 [US2] Build the `TaxSummaryGenerator` component (period picker, generate button, rendered draft showing figures, cited passages, narrative, and a visible "draft" label) in `frontend/src/components/TaxSummaryGenerator.tsx`
- [ ] T019 [US2] Add `generateSummary(start?, end?)` to `frontend/src/services/taxApi.ts` and wire `TaxSummaryGenerator` into `frontend/src/app/tax/page.tsx`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Review and Sign Off on a Draft (Priority: P3)

**Goal**: An admin signs off on a draft to make it an official, immutable record, or discards it — nothing from this feature is ever treated as final without a deliberate human decision.

**Independent Test**: Generate a draft, sign off on it, and confirm it's retained with a recorded sign-off time; separately, generate another draft, discard it, and confirm it's no longer pending.

- [ ] T020 [US3] Implement `TaxSummaryService.sign_off(session, summary_id)` — recomputes `reporting_service.profit_and_loss` for the draft's period and compares it to the stored figures; raises a staleness error on mismatch; otherwise sets `status=signed_off` and `signed_off_at` — in `backend/src/services/tax_summary_service.py`, per FR-007, FR-009, `data-model.md`'s validation rules (depends on T016)
- [ ] T021 [US3] Implement `TaxSummaryService.discard(session, summary_id)` (deletes the row; raises a conflict error if the summary is already signed off) in `backend/src/services/tax_summary_service.py`, per FR-010
- [ ] T022 [US3] Implement `TaxSummaryService.list_summaries(session)` and `get_summary(session, summary_id)` in `backend/src/services/tax_summary_service.py`, per FR-010
- [ ] T023 [US3] Implement `POST /api/tax/summaries/{id}/sign-off`, `DELETE /api/tax/summaries/{id}`, `GET /api/tax/summaries`, `GET /api/tax/summaries/{id}` in `backend/src/api/tax.py`, per `contracts/tax-api.md` (depends on T020, T021, T022)
- [ ] T024 [US3] Add sign-off and discard controls to the rendered draft in `frontend/src/components/TaxSummaryGenerator.tsx`, calling the respective API functions (depends on T018)
- [ ] T025 [US3] Build the `TaxSummaryHistory` component (past summaries list with status; reopens any summary — draft or signed-off — to view its full detail, reusing `TaxSummaryGenerator`'s rendering) in `frontend/src/components/TaxSummaryHistory.tsx`
- [ ] T026 [US3] Add `signOffSummary`/`discardSummary`/`listSummaries`/`getSummary` to `frontend/src/services/taxApi.ts`, and wire `TaxSummaryHistory` into `frontend/src/app/tax/page.tsx` alongside `TaxSummaryGenerator`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently.

---

## Phase 6: User Story 4 - Ask for a Summary in Natural Language (Priority: P4)

**Goal**: An admin asks the AI chat interface for a summary in plain language and gets the same draft a direct request for that period would produce.

**Independent Test**: Ask the chat interface for a summary with an implied period, and confirm it produces the same draft a direct request for that period would.

- [ ] T027 [US4] Implement `resolve_summary_request(question, today)` in `backend/src/agent/tax_tools.py` — sees only the question text and today's date (never ledger data or the reference library), resolves a `start`/`end` range or marks itself unresolvable rather than guessing (mirrors `resolve_audit_request`'s shape, per `research.md`)
- [ ] T028 [US4] Implement `POST /api/agent/tax/query` in `backend/src/api/agent.py` — resolves the date range via `resolve_summary_request`, calls the same `TaxSummaryService.generate` a direct request would use for that range, and returns the generated summary's own `narrative` as the response's `narrative` (no separate narration call — `generate` already produces one overall narrative, unlike `007`'s per-flag explanations); returns `422` with a clarifying question in `narrative` when the period can't be confidently resolved — per `contracts/tax-api.md` (depends on T027, T016)
- [ ] T029 [US4] Add `queryTaxSummary(question)` to `frontend/src/services/taxApi.ts`, add a free-text question box to `frontend/src/app/tax/page.tsx` wired to `POST /api/agent/tax/query`, reusing `TaxSummaryGenerator`'s rendering for the returned data (depends on T028)

**Checkpoint**: All four user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T030 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the retrieval step, the `embed_text`/`draft_summary_narrative`/`resolve_summary_request` tools, and the tax-summary flow — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [ ] T031 Run the `quickstart.md` validation flow end-to-end and fix any gaps found
- [ ] T032 [P] Code cleanup pass across `backend/` and `frontend/` for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - US1 (P1) has no dependency on other stories.
  - US2 (P2) depends on US1 existing to be meaningfully grounded, though it remains independently testable via the "no relevant material" edge case even against an empty library.
  - US3 (P3) depends on US2's persisted `TaxSummary` rows existing to sign off on or discard.
  - US4 (P4) depends on US2's `generate` existing to call from the natural-language path.
  - Recommended order given these dependencies: US1 → US2 → US3 → US4 (matches priority order already).
- **Polish (Phase 7)**: Depends on all desired phases being complete.

### Within Each User Story

- Service function(s) before endpoint(s); endpoint(s) before the frontend piece that calls them.
- Story complete and checkpointed before moving to the next priority.

### Parallel Opportunities

- Foundational model tasks T002, T003, T004 can run in parallel (different files); T005 (migration) depends on all three. T006, T007 can run in parallel with each other and with T002–T005.
- Within each user story phase, backend service/endpoint tasks are sequential (each depends on the prior step), but frontend tasks for a story can start once that story's endpoint contract is stable.
- Polish tasks T030 and T032 can run in parallel with each other.

---

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Complete Phase 4: User Story 2.
5. **STOP and VALIDATE**: run the relevant `quickstart.md` steps for US1+US2 (empty library, add a document, generate a grounded draft, no-relevant-material and zero-activity edge cases).
6. Demo if ready — a draft summary can now be produced and reviewed, even without sign-off or history yet. Note: unlike prior features, US1 alone isn't a meaningful demo on its own (a document library with nothing to do with it) — the real MVP here is US1+US2 together.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validate (library management).
3. Add US2 → validate → demo (grounded draft generation, the MVP).
4. Add US3 → validate → demo (sign-off, discard, history — the safety gate).
5. Add US4 → validate → demo (chat-driven summary requests).
6. Polish phase → diagram update, quickstart validation, cleanup.

---

## Notes

- No test tasks were generated (not explicitly requested); add them ahead of their corresponding implementation task if the team decides to adopt TDD for this feature.
- T030 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- This feature introduces no new backend dependency (`research.md`) — the `openai` client and `numpy` are already present from prior features.
- Commit after each task or logical group, on the `008-tax-compliance-summaries` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
