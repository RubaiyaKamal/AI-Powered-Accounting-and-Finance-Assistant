---
id: 0002
title: Add technical plan for reporting
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 005-reporting
branch: 005-reporting
user: Rubaiya-Kamal
command: /sp.plan
labels: ["plan", "reporting", "trial-balance", "profit-and-loss", "balance-sheet", "cash-flow", "sql-aggregation"]
links:
  spec: specs/005-reporting/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/005-reporting/plan.md
 - specs/005-reporting/research.md
 - specs/005-reporting/data-model.md
 - specs/005-reporting/contracts/reports-api.md
 - specs/005-reporting/quickstart.md
 - CLAUDE.md
tests:
 - N/A (plan stage; no code yet)
---

## Prompt

yes, run /sp.plan

## Response snapshot

Ran `setup-plan.sh`, then read the spec, the constitution (confirming Principle II — Deterministic Financial Computation — already states almost verbatim the constraint this feature's spec formalizes), and `004-bank-reconciliation`'s plan/research/data-model/contracts as a style/format reference. Inspected the existing `ledger_service.py`/`journal_entry.py`/`account.py` to ground the design in real data: journal entries currently only ever debit an Expense account and credit a single seeded "Cash" account (no income-entry feature yet), and reversal semantics use `status="reversed"` on the original plus a new `status="posted", reverses_journal_entry_id=<original>` entry — discovered that naively filtering only `status == "posted"` would double-count a reversal's offsetting effect, so reports must filter `status == "posted" AND reverses_journal_entry_id IS NULL` (reusing `active_journal_entry()`'s exact rule globally). Also confirmed via `grep` that no general chat/tool-calling agent endpoint exists yet in this codebase — every existing `*_tools.py` (`suggest_account_coding`, `adjudicate_match`) is a single-shot JSON-completion call, not real OpenAI Agents SDK function-tool-calling.

Wrote `plan.md` (Constitution Check: PASS on all applicable principles, Principle III marked N/A since reporting has no posting/matching action to gate, one ACTION REQUIRED on Principle V for the diagram update, carried to tasks.md), `research.md` (5 decisions: SQL `SUM`/`GROUP BY` over pandas since Postgres already does the exact aggregation needed — pandas would be complexity without payoff per Principle VI; the active-postings-only filter derived from the reversal-double-counting analysis above; point-in-time vs. period report defaults; two narrow single-shot LLM calls — `resolve_report_request` and `narrate_report` — instead of introducing SDK tool-calling machinery, reusing the existing codebase pattern; direct endpoints in a new `api/reports.py` router with the natural-language endpoint added to the existing `api/agent.py`), `data-model.md` (no new tables — describes the four computed response shapes: Trial Balance, P&L, Balance Sheet, Cash Flow, all built from a shared `AccountBalance` aggregation), `contracts/reports-api.md` (4 GET endpoints + 1 POST natural-language endpoint, with the contract explicitly stating the chat endpoint's `data` must be numerically identical to the matching direct endpoint's response), and `quickstart.md` (8-step manual validation flow covering all four reports, the reversed-entry edge case, the no-data edge case, and both the successful and ambiguous natural-language query paths). Ran `update-agent-context.sh claude` — no diff resulted, since this feature introduces no new dependency (confirming the SQL-over-pandas decision keeps the tech stack unchanged).

## Outcome

- ✅ Impact: `005-reporting` has a complete Phase 0/1 plan ready for `/sp.tasks`. Zero new backend dependencies and zero new database tables — the smallest technical footprint of any feature so far, since it's purely a read/aggregation layer over `002`'s existing ledger data.
- 🧪 Tests: N/A — plan stage only, no code written yet.
- 📁 Files: specs/005-reporting/{plan.md,research.md,data-model.md,quickstart.md,contracts/reports-api.md}; CLAUDE.md checked (no changes needed).
- 🔁 Next prompts: Run `/sp.tasks` to break this into a dependency-ordered task list (likely US1 Trial Balance → US2 P&L → US3 Balance Sheet → US4 Cash Flow → natural-language query path → diagram update), then `/sp.implement`.
- 🧠 Reflection: The "which entries count" analysis (reversal double-counting) was the one genuinely tricky correctness question in this plan — worth a dedicated unit test in `tasks.md` specifically constructing a reversed-and-reposted entry and asserting the old account nets to exactly zero, not just an eyeballed manual check in quickstart.md.

## Evaluation notes (flywheel)

- Failure modes observed: none — the reversal-filter question was caught during research by tracing through `ledger_service.py`'s actual reversal code rather than assuming `status == "posted"` was sufficient, avoiding what would have been a real correctness bug if implementation had started from an unexamined assumption.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (one tracked action item, not a violation).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.tasks.
