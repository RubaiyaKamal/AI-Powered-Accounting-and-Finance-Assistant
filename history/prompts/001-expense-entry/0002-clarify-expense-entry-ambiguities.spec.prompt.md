---
id: 0002
title: Clarify expense entry ambiguities
stage: spec
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 001-expense-entry
branch: 001-expense-entry
user: Rubaiya-Kamal
command: /sp.clarify
labels: ["clarify", "expense-entry", "spec-refinement"]
links:
  spec: specs/001-expense-entry/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-expense-entry/spec.md
  - specs/001-expense-entry/checklists/requirements.md
tests:
  - none (specification document, not executable)
---

## Prompt

/sp.clarify (no arguments). Ran the full ambiguity/coverage taxonomy scan
against specs/001-expense-entry/spec.md. The 3 existing [NEEDS
CLARIFICATION] markers (category taxonomy, edit-history requirement,
NL-missing-field handling) were confirmed as the only genuinely high-impact
gaps; all other taxonomy categories (security/auth, performance, data
volume, concurrency, integrations, terminology) were already Clear or
low-impact given the single-admin scope already documented in Assumptions.
Asked all 3 as sequential recommended-option questions. The user's first two
replies to Question 1 (category taxonomy) were unrelated pasted assignment
text (once a repeat of "keep specs in the repository...", once a block about
manual+AI entry/reports/Pydantic requirements) rather than answers — these
were acknowledged, the reports/Pydantic content was noted for /sp.plan, and
after two non-answers the recommended option was accepted by default and
clearly flagged as such so the user could correct it. Questions 2 and 3 were
answered directly and unambiguously ("Option A" both times).

## Response snapshot

Resolved all 3 clarifications and integrated them incrementally, writing the
spec after each: (1) categories ship with a predefined starter list
(Utilities, Rent, Salaries, Supplies) that the admin can extend with custom
categories — resolved FR-014, updated the Category key entity; (2) full
field-level edit history (field, old value, new value, when) is tracked from
the start, not deferred to the later audit feature — resolved FR-015, added
FR-015a (viewing edit history) and a new "Edit History Entry" key entity,
and added an acceptance scenario to User Story 2 covering viewing history;
(3) when natural-language parsing can't determine a required field, the
assistant asks a clarifying follow-up question in the same chat turn rather
than falling back to a form — folded into FR-009 (which already said almost
the same thing) rather than kept as a near-duplicate FR-016, which was
removed. Added a `## Clarifications` / `### Session 2026-07-27` section
recording all 3 Q&A pairs verbatim. Updated the quality checklist — both
previously-open items ("no markers remain", "all FRs have clear acceptance
criteria") now pass; checklist notes the FR-016→FR-009 merge and marks the
spec ready for `/sp.plan`.

## Outcome

- ✅ Impact: `specs/001-expense-entry/spec.md` has zero remaining
  [NEEDS CLARIFICATION] markers and is ready for `/sp.plan`; edit-history
  tracking is now a first-class requirement rather than deferred, which
  will shape the data model in planning.
- 🧪 Tests: none (specification stage)
- 📁 Files: `specs/001-expense-entry/spec.md`,
  `specs/001-expense-entry/checklists/requirements.md`
- 🔁 Next prompts: run `/sp.plan` for `001-expense-entry` (carrying forward
  the manual+AI entry, agent CRUD/reports/audits/Q&A, Postgres-backed
  reports, and Pydantic-validation requirements the user supplied
  mid-session); consider running `/sp.specify` next for the AI agent/chat
  interface or P&L report feature.
- 🧠 Reflection: when a user's reply to a pending clarification question is
  clearly off-topic (recognizable pasted text, not a letter/short-answer),
  the right move is to name that plainly, capture anything useful in it for
  the right later stage, and fall back to the stated recommendation rather
  than re-asking the identical question indefinitely — repeating verbatim
  risks the same mismatch again and stalls the workflow.

## Evaluation notes (flywheel)

- Failure modes observed: two consecutive non-answers to the same
  clarification question (user pasted unrelated assignment text instead of
  A/B/C or "yes"). Recovered by defaulting to the stated recommendation and
  clearly flagging it as a default, rather than a third identical prompt.
- Graders run and results (PASS/FAIL): N/A — checklist self-evaluation only.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
