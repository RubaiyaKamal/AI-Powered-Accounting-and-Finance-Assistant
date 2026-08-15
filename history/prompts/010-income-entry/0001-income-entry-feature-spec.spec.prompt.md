---
id: 0001
title: Income entry feature spec
stage: spec
date: 2026-08-15
surface: agent
model: claude-sonnet-5
feature: 010-income-entry
branch: 010-income-entry
user: Rubaiya-Kamal
command: /sp.specify
labels: ["income-entry", "reporting", "ledger"]
links:
  spec: specs/010-income-entry/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/010-income-entry/spec.md
 - specs/010-income-entry/checklists/requirements.md
tests:
 - none (spec stage; no code yet)
---

## Prompt

also add income statement and balance sheet in this project and add demo values 5.5 for every task in this  how they work

(Follow-up context established via clarifying questions before this spec was
written: the user confirmed (1) income statement and balance sheet reports
already exist in the codebase but the app has no way to record revenue, so
the fix is to build a minimal Income Entry feature first — following this
project's spec-first workflow — rather than just seeding expense-only demo
data, and (2) demo entries should be created through the running app's API
once the feature exists, not via a direct DB seed script.)

Feature description passed to /sp.specify: "Minimal income entry: allow the
admin to record income/revenue transactions (amount, date, source/category,
optional description) so the ledger has a funding side, not just expenses.
Each income entry posts a journal entry crediting a Revenue account (or an
Equity/opening-capital account for non-operating income) and debiting Cash,
mirroring how expense entries already debit an expense account and credit
Cash. This unblocks the existing income-statement (profit-and-loss) and
balance-sheet reports, which currently always show $0 revenue and an
unbalanced balance sheet because there is no way to record money coming in.
Scope is intentionally minimal: manual structured entry only (no
natural-language parsing, no AI category suggestion) — mirror only the CRUD
+ ledger-posting parts of 001-expense-entry, not its AI stories."

## Response snapshot

Investigated the existing codebase first and found the income statement
(profit-and-loss) and balance sheet reports already fully implemented
(`backend/src/api/reports.py`, `reporting_service.py`, frontend `/reports`
page) as feature 005-reporting — computed deterministically from
`journal_entries` + `accounts`. Also found the real gap: `ledger_service`
only ever posts "debit the coded account / credit Cash" from expense
entries, so revenue/equity can never be recorded, guaranteeing $0 revenue
and an unbalanced balance sheet.

Branched `010-income-entry` off `origin/main` (constitution Principle IV:
branch-per-feature) via `create-new-feature.sh --number 10 --short-name
income-entry`. Wrote `specs/010-income-entry/spec.md` with 3 prioritized user
stories (P1: record an income entry and have it post to the ledger
immediately; P2: view/edit/delete income entries with ledger corrections;
P2: see income reflected in the income statement and balance sheet), 12
functional requirements, key entities (Income Entry, Income Source), and 5
measurable success criteria — including SC-005, which ties directly back to
the balance-sheet-must-balance motivation for building this. Scope
deliberately excludes NL entry, AI source suggestion, and field-level edit
history (documented as Assumptions, not [NEEDS CLARIFICATION] markers,
since the user already made these calls via the clarifying questions).
Created and passed the spec-quality checklist
(`specs/010-income-entry/checklists/requirements.md`) — all items pass, no
spec updates needed before `/sp.plan`.

## Outcome

- ✅ Impact: New feature spec ready for planning; unblocks income-statement/balance-sheet reports from ever showing real revenue/equity data.
- 🧪 Tests: none yet (spec stage)
- 📁 Files: specs/010-income-entry/spec.md, specs/010-income-entry/checklists/requirements.md
- 🔁 Next prompts: /sp.plan for 010-income-entry, then /sp.tasks, then /sp.implement
- 🧠 Reflection: The user's literal ask ("add income statement and balance sheet") was already satisfied by existing code; the real unmet need was a revenue-recording capability, surfaced only by reading `ledger_service.py`'s fixed debit/credit direction. Investigating before acting avoided building a duplicate/wrong feature.

## Evaluation notes (flywheel)

- Failure modes observed: none — clarifying questions correctly resolved the two real ambiguities (feature-vs-seed-only, and seed method) before any code was written.
- Graders run and results (PASS/FAIL): spec quality checklist — PASS (all items)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
