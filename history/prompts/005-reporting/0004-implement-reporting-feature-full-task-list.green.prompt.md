---
id: 0004
title: Implement reporting feature full task list
stage: green
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 005-reporting
branch: 005-reporting
user: Rubaiya-Kamal
command: /sp.implement
labels: ["reporting", "trial-balance", "profit-and-loss", "balance-sheet", "cash-flow", "ai-agent"]
links:
  spec: specs/005-reporting/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/schemas/reports.py
 - backend/src/services/reporting_service.py
 - backend/src/agent/reporting_tools.py
 - backend/src/api/reports.py
 - backend/src/api/agent.py
 - backend/src/main.py
 - frontend/src/services/reportsApi.ts
 - frontend/src/components/ReportViewer.tsx
 - frontend/src/components/ReportQuery.tsx
 - frontend/src/app/reports/page.tsx
 - frontend/src/app/layout.tsx
 - docs/workflow-diagram.drawio
 - specs/005-reporting/tasks.md
tests:
 - Manual: ruff check (backend, full repo) — all checks passed
 - Manual: tsc --noEmit (frontend) — no errors, after each phase
 - Manual: quickstart.md flow executed live against docker-compose stack — all 8 steps confirmed (4 report endpoints, no-data period, invalid date-range 422, NL query resolvable/ambiguous/trial-balance cases with a live OpenAI key)
---

## Prompt

/sp.implement

full task list

## Response snapshot

Implemented all 26 tasks (T001-T026) from specs/005-reporting/tasks.md
across 8 phases, following the plan/data-model/contracts/research
already committed on this branch:

- Phase 1-2: scaffolded new files; built the shared `AccountBalance`
  schema and `ReportingService._account_balances`, the single SQL
  SUM/GROUP BY aggregation (filtered to active postings only — posted,
  non-reversal, non-reversed) that every report builds on.
- Phase 3-6: implemented all four reports (trial_balance,
  profit_and_loss, balance_sheet, cash_flow) as deterministic service
  functions, their GET endpoints, and progressive ReportViewer UI
  extensions (report-type selector, date/range inputs, statement
  tables with balanced/reconciliation indicators).
- Phase 7: added the natural-language path — `resolve_report_request`
  and `narrate_report` as two narrow single-shot LLM calls (mirroring
  existing `suggest_account_coding`/`adjudicate_match` patterns, with
  keyword-match/templated fallbacks when no OPENAI_API_KEY is set),
  wired into `POST /api/agent/reports/query` which calls the same
  ReportingService functions the direct endpoints use and returns a
  422 with a clarifying narrative when the report type can't be
  resolved. Built the ReportQuery UI component.
- Phase 8: updated docs/workflow-diagram.drawio's Agent Tools box to
  list the two new tools; validated the full quickstart.md flow live
  against the running docker-compose stack (with a real OpenAI key),
  confirming correct figures, balanced/reconciled totals, the
  reversed-entry edge case (pre-existing seed data), the no-data
  period, the invalid-date-range 422, and all three NL-query
  scenarios; no cleanup gaps found.

Committed after each phase (8 commits total) per the constitution's
Principle IV and the github-commit-workflow skill. Marked all 26 tasks
[X] in tasks.md. Verified with `ruff check` (backend) and
`tsc --noEmit` (frontend) after every phase, and a live end-to-end
pass against the running stack after implementation completed.

## Outcome

- ✅ Impact: Feature 005-reporting is fully implemented — four
  read-only financial statements plus a natural-language query path,
  all backed by deterministic SQL aggregation with the AI strictly
  bounded to classification and narration (constitution Principle II).
- 🧪 Tests: No automated test suite was generated (not requested,
  matching prior-feature precedent noted in tasks.md); validated via
  lint/typecheck plus a full live run of quickstart.md's 8 steps.
- 📁 Files: 4 new backend modules, 1 modified backend module
  (api/agent.py) + main.py registration, 3 new/modified frontend
  files, 1 diagram update, 1 tasks.md fully checked off.
- 🔁 Next prompts: Consider adding an automated test suite
  (contract/integration/unit, per plan.md's Project Structure) if the
  team decides to backfill TDD coverage; open a PR from
  005-reporting into main.
- 🧠 Reflection: The docker-compose backend/frontend containers had
  drifted from a broken host-side `.venv` (Linux symlinks created
  inside the Windows bind mount) partway through — required removing
  and resyncing the venv twice. Worth flagging to the user that mixing
  host `uv run` and the containerized dev server against the same
  bind-mounted `backend/` can corrupt `.venv` across OS boundaries.

## Evaluation notes (flywheel)

- Failure modes observed: Host-container `.venv` corruption (Linux
  venv symlinks written into a Windows bind mount by the backend
  container, breaking host-side `uv run`/`ruff`) — recovered via
  `Remove-Item -Recurse -Force` + `uv sync`, twice. No code-level
  failure modes; all four reports and the NL path matched the
  documented contracts on the first live run.
- Graders run and results (PASS/FAIL): ruff check — PASS (both
  per-phase and full-repo); tsc --noEmit — PASS (every phase); live
  quickstart.md 8-step walkthrough — PASS (all steps).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
