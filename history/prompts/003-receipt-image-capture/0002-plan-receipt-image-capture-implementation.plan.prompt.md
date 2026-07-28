---
id: 0002
title: Plan receipt image capture implementation
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 003-receipt-image-capture
branch: 003-receipt-image-capture
user: Rubaiya-Kamal
command: /sp.plan
labels: ["plan", "ocr", "receipt-capture", "vision"]
links:
  spec: specs/003-receipt-image-capture/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/003-receipt-image-capture/plan.md
 - specs/003-receipt-image-capture/research.md
 - specs/003-receipt-image-capture/data-model.md
 - specs/003-receipt-image-capture/contracts/receipt-capture-api.md
 - specs/003-receipt-image-capture/quickstart.md
tests:
 - N/A (plan stage; no code yet)
---

## Prompt

(empty — /sp.plan invoked with no additional arguments, continuing the SDD workflow immediately after /sp.specify, following Auto Mode's bias toward continuing without stopping)

## Response snapshot

Ran setup-plan.sh to scaffold plan.md on branch 003-receipt-image-capture. Filled Technical Context reusing the exact existing stack (no new languages/frameworks; file upload handled natively by FastAPI's UploadFile, already a transitive dependency — no new package needed). Constitution Check: PASS on all six principles, one tracked action item (Principle V — workflow diagram must be updated, same pattern as both prior features).

Key design decision made here (deliberately left out of spec.md as a plan-level, not business-scope, choice): reuse the existing AssistantChat component with an added file-upload control, rather than building a separate upload UI — and correspondingly, add parse_receipt_image to the existing expense_tools.py module (alongside parse_expense_draft) rather than a new receipt_tools.py file, since it returns the exact same ready_for_confirmation/needs_clarification draft shape. This keeps the feature a small additive extension rather than a parallel code path.

Phase 0 (research.md): recorded the two decisions already made and confirmed during the earlier plan-mode session (GPT-4o mini vision extraction, no persistent image storage) plus three new feature-scoped decisions: (1) parse_receipt_image lives in expense_tools.py, exposed via a new POST /api/agent/expenses/parse-receipt endpoint in the existing agent.py; (2) the source marker is a one-value widening of ExpenseEntryCreate's existing Literal type, not a new column; (3) upload validation accepts JPEG/PNG/WEBP up to 5MB, rejected before extraction is attempted.

Phase 1: wrote data-model.md (trivial — no new entities, just documents the source enum widening and the explicit "never persisted" note for the image itself), contracts/receipt-capture-api.md (one endpoint, multipart upload, same response shape as the existing text-parse endpoint), and quickstart.md (7 manual validation steps covering the happy path, correction, unreadable-image clarification, category suggestion, rejected uploads, and confirming no image is ever retained). Ran update-agent-context.sh claude — no-op, stack already recorded identically for 001/002.

## Outcome

- ✅ Impact: `003-receipt-image-capture` has a complete, minimal technical plan ready for `/sp.tasks`. The plan explicitly keeps this feature's footprint small — three modified files on the backend, two on the frontend, zero new components, zero new tables.
- 🧪 Tests: N/A — plan stage only, no code written yet.
- 📁 Files: specs/003-receipt-image-capture/{plan.md, research.md, data-model.md, quickstart.md, contracts/receipt-capture-api.md}
- 🔁 Next prompts: Run `/sp.tasks` to break this into dependency-ordered tasks, then `/sp.implement`.
- 🧠 Reflection: This is the smallest plan of the three features so far — a direct consequence of deliberately reusing existing components/modules instead of building parallel ones, which the Constitution Check's Principle VI row made explicit rather than leaving implicit.

## Evaluation notes (flywheel)

- Failure modes observed: none — plan generation proceeded cleanly using the already-clarified spec and the architecture decisions already locked in during plan mode.
- Graders run and results (PASS/FAIL): Constitution Check gate — PASS (5/6 clean, 1 tracked action item, no violations requiring Complexity Tracking entries).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.tasks.
