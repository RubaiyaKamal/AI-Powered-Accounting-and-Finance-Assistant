---
description: "Task list for receipt/invoice image capture feature implementation"
---

# Tasks: Receipt/Invoice Image Capture

**Input**: Design documents from `/specs/003-receipt-image-capture/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/receipt-capture-api.md, quickstart.md (all present)

**Tests**: Not included — not explicitly requested in the feature specification, matching `001-expense-entry`/`002-ledger-journal-entries`'s precedent.

**Organization**: This feature has a single user story (P1), so tasks are grouped Setup → Foundational → US1 → Polish rather than across multiple story phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 for the one user story; Setup/Foundational/Polish tasks carry no story label
- File paths are relative to the repository root, per `plan.md`'s Project Structure. This feature only modifies existing `backend/` and `frontend/` files from `001-expense-entry` — no new components, tables, or projects.

## Phase 1: Setup

- [x] T001 Add `python-multipart` as an explicit dependency in `backend/pyproject.toml` (currently only a transitive dependency of FastAPI — make the file-upload requirement explicit rather than implicit)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Widen `ExpenseEntryCreate.source`'s `Literal` type to include `"receipt_image"` in `backend/src/schemas/expense_entry.py`, per `data-model.md`
- [x] T003 Add allowed content-types (`image/jpeg`, `image/png`, `image/webp`) and a max upload size constant (5MB) in `backend/src/config.py`, per `research.md`'s Upload Validation decision

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Record an expense by uploading a receipt or invoice photo (Priority: P1) 🎯 MVP

**Goal**: An admin uploads a receipt/invoice photo and gets a parsed draft (amount, date, vendor/description) to confirm or correct before it's saved as an expense entry.

**Independent Test**: Upload a clear, legible receipt photo and confirm the system shows a parsed amount, date, and description matching the receipt, then confirm it saves an expense entry with exactly those values.

- [x] T004 [US1] Implement `parse_receipt_image` (image bytes + content type → the same `{"status": "ready_for_confirmation", "draft": {...}}` / `{"status": "needs_clarification", ...}` shape `parse_expense_draft` already returns, via GPT-4o mini's multimodal input) in `backend/src/agent/expense_tools.py`, per FR-002, FR-004
- [x] T005 [US1] Implement `POST /api/agent/expenses/parse-receipt` (multipart upload; validates content-type/size from T003 before calling `parse_receipt_image`, returning `422` on an invalid upload per FR-009) in `backend/src/api/agent.py`, per `contracts/receipt-capture-api.md`
- [x] T006 [US1] Add a `parseReceiptImage(file)` client function to `frontend/src/services/expensesApi.ts`, per `contracts/receipt-capture-api.md`
- [x] T007 [US1] Add a file-upload control to `AssistantChat.tsx` that calls `parseReceiptImage`, reuses the component's existing draft/confirm/correct rendering, and tags the eventual `createExpense` call with `source="receipt_image"` in `frontend/src/components/AssistantChat.tsx`

**Checkpoint**: User Story 1 is fully functional and independently testable — this is the whole feature's MVP (and its only story).

> **Note**: FR-007 (AI category suggestion for entries with no explicit category) needs no new code — it is already satisfied by reusing the same `category_name_hint` → `POST /api/expenses` path the natural-language flow uses (T007 wires the draft's description into that same field). Verified via `quickstart.md` step 5, not a separate implementation task.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T008 [P] Update the workflow diagram (`docs/workflow-diagram.drawio`) to include the `parse_receipt_image` tool and the image-upload flow — required before this feature's PR merges, per the Constitution Check in `plan.md` (Principle V)
- [x] T009 Run the `quickstart.md` validation flow end-to-end (all 7 steps, including confirming no image is ever retained per FR-008) and fix any gaps found
- [x] T010 [P] Code cleanup pass across the modified `backend/` and `frontend/` files for this feature

### T009 findings (quickstart validation)

Ran the full flow live against `docker-compose up`, using a synthetic
receipt image (generated with Pillow: vendor name, date, line items, and a
total) since no physical receipt was available. All 7 steps passed on the
**first attempt** — no bugs found, a first for this project's features so
far, most likely a direct result of the plan's deliberate choice to reuse
already-debugged code paths (`parse_expense_draft`'s exact response shape,
the existing `POST /api/expenses` commit path, `AssistantChat`'s existing
draft/confirm UI) rather than building anything new end-to-end:

1. Clear receipt upload → correctly parsed amount ($39.50, matching the
   receipt's TOTAL line), date, and vendor as `category_name_hint`.
2. Confirmed draft → entry saved with `source=receipt_image` and correctly
   received an AI-suggested "Supplies" category (FR-005–FR-007 verified in
   one request).
3. Unsupported file type (a `.docx`) → `422` rejected before extraction.
4. Oversized image (6MB) → `422` rejected before extraction.
5. Blank/unreadable image → `needs_clarification` with a specific
   follow-up question for the amount (FR-004), not a guess or silent
   failure.
6. Confirmed via filesystem inspection inside the running container that
   no receipt/upload files exist anywhere (FR-008) — the image truly never
   leaves memory.
7. Frontend confirmed rendering the new "Upload a receipt/invoice photo"
   control on `/expenses` with no compile errors.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS User Story 1.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. T004 and T006 can start in parallel (different files, no cross-dependency); T005 depends on T004 (calls it) and T003 (validation constants); T007 depends on T005 and T006 existing.
- **Polish (Phase 4)**: Depends on User Story 1 being complete.

### Parallel Opportunities

- T002 and T003 (Foundational) can run in parallel — different files.
- T004 and T006 (US1) can run in parallel — different files, no cross-dependency until T005/T007 wire them together.
- T008 and T010 (Polish) can run in parallel with each other.

---

## Implementation Strategy

Since this feature has only one user story, there is no incremental
multi-story delivery plan — complete Setup → Foundational → US1 → Polish in
order, then validate via `quickstart.md` in full.

---

## Notes

- No test tasks were generated (not explicitly requested), matching prior features' precedent.
- T008 (workflow diagram update) is not optional polish — it's a constitution-mandated deliverable (Principle V) flagged in `plan.md`'s Constitution Check as pending before this feature's PR can merge.
- Commit after each task or logical group, on the `003-receipt-image-capture` branch, per the `github-commit-workflow` skill and the constitution's Principle IV.
