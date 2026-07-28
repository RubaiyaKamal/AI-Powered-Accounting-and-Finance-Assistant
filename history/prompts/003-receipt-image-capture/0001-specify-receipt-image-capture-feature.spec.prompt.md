---
id: 0001
title: Specify receipt image capture feature
stage: spec
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 003-receipt-image-capture
branch: 003-receipt-image-capture
user: Rubaiya-Kamal
command: /sp.specify
labels: ["spec", "ocr", "receipt-capture", "vision"]
links:
  spec: specs/003-receipt-image-capture/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/003-receipt-image-capture/spec.md
 - specs/003-receipt-image-capture/checklists/requirements.md
tests:
 - N/A (spec-only stage; no code yet)
---

## Prompt

yes, start on that now

(Following an approved plan-mode plan, saved at C:\Users\Lap Zone\.claude\plans\splendid-hopping-willow.md, which identified that "Data Capture & Recording" from research/task-automation-mapping.md was only partially built — natural-language entry and categorization existed via 001-expense-entry, but OCR/invoice image capture did not exist at all. The plan recommended GPT-4o mini vision-based extraction (one LLM call, no separate OCR library) and no persistent image storage, both confirmed via AskUserQuestion during plan mode.)

## Response snapshot

Synced main (now includes both 001-expense-entry and 002-ledger-journal-entries, merged via PR #5 and #6), created branch `003-receipt-image-capture` (feature 003, no prior branches/specs for this short name). Wrote `specs/003-receipt-image-capture/spec.md` with a single P1 user story (upload a receipt/invoice photo → parsed draft → confirm/correct → saved entry), mirroring how 001-expense-entry's natural-language story bundled confirm/correct/missing-field-clarification into one story rather than splitting them artificially. 5 edge cases, 9 functional requirements, no new Key Entities (extends ExpenseEntry's existing source marker rather than persisting anything new — the image itself is explicitly never stored, per FR-008), assumptions (vendor folded into existing description field, single-line-item MVP, image format/size limits as implementation detail), and 4 measurable success criteria.

Deliberately kept "reuse AssistantChat vs. build a separate upload UI" out of spec.md — it's a plan-level decision, not a business-scope one, per the Quick Guidelines' "avoid HOW to implement." No [NEEDS CLARIFICATION] markers were needed; every open question either had a reasonable documented default or belonged at the plan stage. Checklist created and passes fully on the first draft — no clarification round needed this time (unlike 002's two clarifications).

## Outcome

- ✅ Impact: `003-receipt-image-capture` has a complete spec ready for `/sp.plan`. This is the third feature in the 7-category roadmap and completes the "Data Capture & Recording" category's remaining gap identified via the approved plan-mode session.
- 🧪 Tests: N/A — spec stage only, no code written yet.
- 📁 Files: specs/003-receipt-image-capture/spec.md, specs/003-receipt-image-capture/checklists/requirements.md
- 🔁 Next prompts: Run `/sp.plan` to design the technical approach (vision-extraction agent tool mirroring parse_expense_draft, upload endpoint, frontend upload control placement), then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: Having already resolved the two biggest architecture questions (vision vs. classic OCR, no persistent storage) during the plan-mode session meant this spec had zero ambiguity requiring a clarification round — a good sign that plan-mode's upfront research paid off rather than just deferring the same questions to /sp.clarify.

## Evaluation notes (flywheel)

- Failure modes observed: none — spec generation went cleanly on the first pass, likely because the plan-mode session had already done the hard architectural thinking.
- Graders run and results (PASS/FAIL): Spec quality checklist — PASS (all items, first draft, no clarification round needed).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.plan.
