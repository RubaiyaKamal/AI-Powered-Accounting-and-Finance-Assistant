---
id: 0001
title: Add reporting feature specification
stage: spec
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 005-reporting
branch: 005-reporting
user: Rubaiya-Kamal
command: /sp.specify
labels: ["spec", "reporting", "trial-balance", "profit-and-loss", "balance-sheet", "cash-flow", "deterministic-computation"]
links:
  spec: specs/005-reporting/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/005-reporting/spec.md
 - specs/005-reporting/checklists/requirements.md
tests:
 - N/A (spec-only stage; no code yet)
---

## Prompt

Reporting (trial balance, P&L, balance sheet, cash flow)
Important point: LLM khud calculations NAHI karega (free text se numbers generate karna galat hai) — balke LLM sirf orchestrate karega, actual calculation SQL/pandas se hogi, aur result ko LLM sirf explain/narrate karega. Ye point paper mein clearly likhna hai.                      now create this

## Response snapshot

Created branch `005-reporting` (feature 005, following the 001–004 numbering convention) from an up-to-date `main` (which already had 004-bank-reconciliation merged). Wrote `specs/005-reporting/spec.md` with 4 prioritized user stories (P1: Trial Balance — the foundation every other statement derives from; P2: Profit & Loss for a chosen period; P3: Balance Sheet as of a chosen date; P4: Cash Flow Statement, scoped down given the system currently models only a single Cash offset account), 5 edge cases, 10 functional requirements, 4 key entities described as read-only computed statements (none are new persisted entities — all read from the existing Account/Journal Entry data from the Ledger feature), assumptions (no Income Entry feature yet so P&L is expense-only for now; single-account direct-method cash flow; sensible date/period defaults), and 5 measurable success criteria.

The critical constraint the user emphasized — the AI agent must never compute financial figures itself, only orchestrate report selection and narrate deterministically-computed results — is stated as FR-001 (listed first, most prominent) and echoed in the Edge Cases and Success Criteria (SC-005: chat-returned figures must match direct-report figures to the last decimal). This mirrors and applies the project's existing Constitution Principle II (Deterministic Financial Computation), which already states this exact rule project-wide — confirmed by grepping `.specify/memory/constitution.md` before writing the spec, so the spec restates rather than invents the constraint. No [NEEDS CLARIFICATION] markers were needed: the AI-chat-access question was resolved from existing evidence (the system architecture diagram already anticipates `generate_pl`/`generate_balance_sheet`/`answer_query` agent tools), and remaining ambiguities (report defaults, export, entity model) had clear defaults documented under Assumptions. The requirements-quality checklist passed all items on the first pass.

## Outcome

- ✅ Impact: `005-reporting` has a complete spec ready for `/sp.plan`. This is the fifth feature in the project roadmap, and the first to formalize the deterministic-computation constraint as its own feature's explicit requirement rather than an implicit constitutional rule.
- 🧪 Tests: N/A — spec stage only, no code written yet.
- 📁 Files: specs/005-reporting/spec.md, specs/005-reporting/checklists/requirements.md
- 🔁 Next prompts: Run `/sp.plan` to design the technical approach (report calculation service reading Account/JournalEntry via SQL/pandas, agent tool signatures for generate_trial_balance/generate_pl/generate_balance_sheet/generate_cash_flow, API endpoints, and reporting UI), then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: This feature has the least new data-model surface of any feature so far (zero new persisted entities) — worth watching during planning whether that keeps the implementation unusually small/low-risk compared to 001–004, which all introduced new tables.

## Evaluation notes (flywheel)

- Failure modes observed: none — spec generation went cleanly in one pass with no clarification round needed.
- Graders run and results (PASS/FAIL): Spec quality checklist — PASS (all items, first pass).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.plan.
