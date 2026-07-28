---
id: 0003
title: Generate bank reconciliation task list
stage: tasks
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 004-bank-reconciliation
branch: 004-bank-reconciliation
user: Rubaiya-Kamal
command: /sp.tasks
labels: ["tasks", "reconciliation", "bank-transactions"]
links:
  spec: specs/004-bank-reconciliation/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/004-bank-reconciliation/tasks.md
 - specs/004-bank-reconciliation/data-model.md
tests:
 - N/A (tasks stage; no code yet)
---

## Prompt

(empty — /sp.tasks invoked with no additional arguments, continuing per Auto Mode's bias toward continuing without stopping)

## Response snapshot

Ran check-prerequisites.sh — confirmed all Phase 0/1 docs present. Before writing tasks, caught a real gap in data-model.md while working out where T019/T020-equivalent tasks would live: the plan never specified where an ambiguous transaction's AI-computed suggestion (chosen expense entry + reasoning) gets stored between being computed at import time and displayed later in the review queue. Fixed by adding suggested_expense_entry_id (FK, ON DELETE SET NULL) and ai_reasoning columns to BankTransaction, with a clarifying note distinguishing this system-computed matching metadata from FR-012's immutability guarantee (which only covers the three CSV-sourced fields) — this is the same kind of design gap caught during 002's implementation, just caught one stage earlier here, during task planning instead of live coding.

Generated tasks.md with 28 tasks across 6 phases: Setup (T001-T002: rapidfuzz dependency, file skeleton), Foundational (T003-T007: two new models including the corrected BankTransaction schema, one migration, two schema modules), US1 (T008-T013: CSV parsing, import with dedup, the import endpoint, and the frontend upload UI — MVP), US2 (T014-T019: candidate scoring, three-way classification, and — explicitly noted as living here rather than US3 for the same structural reason as 002's posting primitives — the adjudicate_match tool itself, since matching's ambiguous branch can't complete without it at import time), and US3 (T020-T025: the review-queue listing with live-recomputed candidates, confirm/dismiss/undo service methods and endpoints, and the frontend queue UI). Polish (T026-T028): diagram update, quickstart validation, cleanup.

## Outcome

- ✅ Impact: `004-bank-reconciliation` has a complete, dependency-ordered task list ready for `/sp.implement`, with a real data-model gap caught and fixed before any code was written rather than during later live verification.
- 🧪 Tests: N/A — tasks stage only, no code written yet.
- 📁 Files: specs/004-bank-reconciliation/tasks.md, specs/004-bank-reconciliation/data-model.md (corrected)
- 🔁 Next prompts: Run `/sp.implement` to execute the task list.
- 🧠 Reflection: The "where does AI-computed state live between computation and display" question is a recurring category of gap across these last two features (002's journal-entry-vs-coding state, now this one) — worth treating as a standard checklist item during future data-model design: for any AI output that isn't immediately actionable, explicitly ask where it's persisted and for how long before task planning, not after.

## Evaluation notes (flywheel)

- Failure modes observed: one real plan/data-model gap (AI suggestion storage location), caught during task planning rather than implementation — an improvement over 001/002's pattern of catching similar gaps only during live docker-compose verification.
- Graders run and results (PASS/FAIL): Task format validation — PASS (every task follows the required checklist format; Setup/Foundational/Polish tasks correctly omit the Story label).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.implement.
