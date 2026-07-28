---
id: 0002
title: Plan ledger and journal entries implementation
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 002-ledger-journal-entries
branch: 002-ledger-journal-entries
user: Rubaiya-Kamal
command: /sp.plan
labels: ["plan", "ledger", "journal-entries", "chart-of-accounts", "double-entry"]
links:
  spec: specs/002-ledger-journal-entries/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/002-ledger-journal-entries/plan.md
 - specs/002-ledger-journal-entries/research.md
 - specs/002-ledger-journal-entries/data-model.md
 - specs/002-ledger-journal-entries/contracts/ledger-api.md
 - specs/002-ledger-journal-entries/quickstart.md
tests:
 - N/A (plan stage; no code yet)
---

## Prompt

(technical design: data model for Account/Account Coding/Journal Entry, service layer, API contracts) whenever you want to continue.

(This was the user's own phrasing from the end of the prior /sp.specify turn, re-submitted as the trigger to run /sp.plan next in the SDD workflow.)

## Response snapshot

Ran `.specify/scripts/bash/setup-plan.sh --json` to scaffold `plan.md` on branch `002-ledger-journal-entries`. Filled Technical Context (reusing 001-expense-entry's exact stack — Python 3.12/FastAPI/SQLAlchemy/Alembic/OpenAI Agents SDK backend, Next.js/TypeScript frontend, PostgreSQL — no new languages or frameworks). Constitution Check: PASS on all six principles, with one tracked action item (Principle V — the workflow diagram must be updated before this feature's PR merges, since it adds a new AI tool and an auto-posting flow) carried to tasks.md rather than blocking.

Phase 0 (`research.md`): recorded five feature-scoped decisions — (1) a single fixed "Cash" offset account for the credit side of every expense-derived journal entry, since ExpenseEntry has no payment-method field yet; (2) coding suggestions generated on-demand via a dedicated endpoint rather than hooked into the existing expense-creation path, to keep this feature decoupled from already-shipped code; (3) reversal-as-a-new-entry (never mutating a posted journal entry in place) to preserve full audit history; (4) confidence threshold as an env-var-configured value (default 0.8), not hardcoded; (5) a new `suggest_account_coding` AI tool that returns only an account name + confidence score, mirroring `suggest_category`'s existing Principle-II-compliant shape.

Phase 1: wrote `data-model.md` (Account, AccountCoding, JournalEntry — full field tables, validation rules, state transitions, including the reversal state machine), `contracts/ledger-api.md` (7 endpoints: accounts CRUD-lite, coding suggest/get/approve/correct, journal-entries list/detail), and `quickstart.md` (6 manual validation steps covering both the auto-post and manual-review confidence paths, correction/reversal, deletion-triggered reversal, and ledger browsing). Ran `update-agent-context.sh claude` — no-op since the tech stack is identical to what's already recorded for 001-expense-entry.

## Outcome

- ✅ Impact: `002-ledger-journal-entries` has a complete technical plan, ready for `/sp.tasks`. The plan explicitly documents one integration touch-point into already-shipped code (`DELETE /api/expenses/{id}` gains a call to reverse any posted journal entry, per FR-012) — called out rather than left implicit.
- 🧪 Tests: N/A — plan stage only, no code written yet.
- 📁 Files: specs/002-ledger-journal-entries/{plan.md, research.md, data-model.md, quickstart.md, contracts/ledger-api.md}
- 🔁 Next prompts: Run `/sp.tasks` to break this into dependency-ordered, per-user-story tasks, then `/sp.implement`.
- 🧠 Reflection: Reusing 001-expense-entry's exact plan/research/data-model/contract structure and tone kept this fast and internally consistent; the two /sp.specify clarifications (auto-post threshold, auto-reversal) made several plan-level design decisions (the state machine, the "no separate manual reversal step" endpoint shape) unambiguous rather than requiring further guessing at plan time.

## Evaluation notes (flywheel)

- Failure modes observed: none — plan generation proceeded cleanly using the already-clarified spec.
- Graders run and results (PASS/FAIL): Constitution Check gate — PASS (5/6 clean, 1 tracked action item, no violations requiring Complexity Tracking entries).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.tasks.
