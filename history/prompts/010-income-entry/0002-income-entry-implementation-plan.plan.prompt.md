---
id: 0002
title: Income entry implementation plan
stage: plan
date: 2026-08-15
surface: agent
model: claude-sonnet-5
feature: 010-income-entry
branch: 010-income-entry
user: Rubaiya-Kamal
command: /sp.plan
labels: ["income-entry", "ledger", "reporting"]
links:
  spec: specs/010-income-entry/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/010-income-entry/plan.md
 - specs/010-income-entry/research.md
 - specs/010-income-entry/data-model.md
 - specs/010-income-entry/contracts/income-api.md
 - specs/010-income-entry/quickstart.md
tests:
 - none (plan stage; no code yet)
---

## Prompt

(No new user input at this stage — continuing the /sp.specify → /sp.plan →
/sp.tasks → /sp.implement sequence for 010-income-entry, per the project's
constitutional Principle I, on the already-approved spec from PHR 0001.)

## Response snapshot

Ran `.specify/scripts/bash/setup-plan.sh --json` to scaffold `plan.md`, then
read `002-ledger-journal-entries`'s plan/data-model/contracts as the
in-repo precedent to mirror, plus the actual current code
(`ledger_service.py`, `reporting_service.py`, `journal_entry.py`,
`account.py`, `expense_entry_service.py`, `expenses.py` API, and their
Pydantic schemas) to ground every design decision in what already exists
rather than inventing conventions.

Key design decision, captured in `research.md`: generalize the existing
`journal_entries` table (make `expense_entry_id`/`account_coding_id`
nullable, add nullable `income_entry_id`, add an exactly-one-source check
constraint) rather than building a parallel income-ledger table — because
`reporting_service.py` only ever queries `journal_entries` + `accounts` and
never touches `expense_entry_id`/`account_coding_id`, this means the
existing income-statement and balance-sheet reports need **zero code
changes** to start showing real revenue/equity data once income postings
exist. Also decided: a new `income_sources` table with a direct FK to an
`accounts` row (no AI-coding-suggestion step, matching the spec's
manual-only scope) with two starter sources — "Sales" → a new Revenue
account, "Owner Investment" → a new Equity account — the minimum needed to
make the balance sheet's `assets == liabilities + equity` success criterion
(SC-005) demonstrable.

Produced `plan.md` (Technical Context, Constitution Check — PASS with one
tracked action item: the workflow diagram needs updating before merge, same
as `002`'s precedent), `research.md` (5 decisions with alternatives
considered), `data-model.md` (`IncomeSource`, `IncomeEntry`, and the
generalized `JournalEntry`), `contracts/income-api.md` (7 endpoints:
income-sources CRUD-lite + income CRUD, plus a note on the two existing
endpoints whose behavior — not shape — changes), and `quickstart.md`
(6 manual validation steps plus a worked $5.50-per-entry demo walkthrough
showing the exact resulting report numbers). Ran
`update-agent-context.sh claude`; it reported no new language/framework/db
entries needed since this feature introduces no new dependencies.

## Outcome

- ✅ Impact: Full technical design ready for /sp.tasks — confirms the feature can be built as a additive, minimal-risk change touching one existing table plus new CRUD, with zero changes to the reporting layer that actually satisfies the original request.
- 🧪 Tests: none yet (plan stage)
- 📁 Files: specs/010-income-entry/{plan.md,research.md,data-model.md,quickstart.md,contracts/income-api.md}
- 🔁 Next prompts: /sp.tasks for 010-income-entry, then /sp.implement
- 🧠 Reflection: Reading the actual `reporting_service.py` before designing (rather than assuming a new report-layer change would be needed) was what made the "generalize journal_entries, touch nothing else" design possible — it's the difference between a multi-file reporting change and a one-column migration.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (one tracked action item, not a violation).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
