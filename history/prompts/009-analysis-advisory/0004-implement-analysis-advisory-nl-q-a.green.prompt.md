---
id: 0004
title: Implement analysis advisory NL Q&A
stage: green
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 009-analysis-advisory
branch: 009-analysis-advisory
user: Rubaiya-Kamal
command: /sp.implement
labels: ["analysis", "advisory", "nl-qa", "forecasting", "linear-regression", "ai-agent"]
links:
  spec: specs/009-analysis-advisory/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/schemas/analysis.py
 - backend/src/services/analysis_service.py
 - backend/src/agent/analysis_tools.py
 - backend/src/api/analysis.py
 - backend/src/api/agent.py
 - backend/src/main.py
 - frontend/src/services/analysisApi.ts
 - frontend/src/components/SpendingQuery.tsx
 - frontend/src/components/SpendingBreakdown.tsx
 - frontend/src/components/SpendingForecast.tsx
 - frontend/src/app/analysis/page.tsx
 - frontend/src/components/Sidebar.tsx
 - docs/workflow-diagram.drawio
 - specs/009-analysis-advisory/tasks.md
tests: []
---

## Prompt

now build this

## Response snapshot

Implemented all 25 tasks from `tasks.md` for `009-analysis-advisory`,
verified live against the running docker-compose stack (not just
lint/typecheck):

- **Backend**: `schemas/analysis.py` (SpendingAmount/Breakdown/
  Comparison/Forecast response shapes); `services/analysis_service.py`
  (`spending_amount`, `breakdown`, `comparison`, `forecast` — every
  figure via `reporting_service.profit_and_loss`, forecast via
  scikit-learn's `LinearRegression` over up to 6 preceding months,
  requiring ≥3 with activity else `status="insufficient_data"`);
  `agent/analysis_tools.py` (`resolve_spending_request` classifies into
  all four request kinds from the start, bounding `account_name` to the
  real chart of accounts and deliberately leaving `request_kind` set to
  `"amount"` — not nulled — when the kind is clear but no account
  matched, so the endpoint can distinguish "couldn't tell what you
  meant" from "that account doesn't exist" per spec US1 AC4;
  `narrate_spending_result` narrates results, always framing a forecast
  as an estimate); `api/analysis.py` (3 direct GET endpoints);
  `api/agent.py` (`POST /api/agent/analysis/query`, the sole delivery
  mechanism for the amount kind); registered in `main.py`.
- **Frontend**: `analysisApi.ts`, `SpendingQuery.tsx` (NL question box,
  renders all four result shapes by reusing `BreakdownTable`/
  `ComparisonTable`/`ForecastView` exported from the other two
  components), `SpendingBreakdown.tsx` (period breakdown + two-period
  comparison), `SpendingForecast.tsx`, `/analysis` page, sidebar link.
- **Verification**: `ruff check` clean after fixing an import-sort and
  an ambiguous-variable-name issue; `tsc --noEmit` clean; restarted both
  containers and exercised the running stack directly — breakdown,
  invalid-range comparison (422), zero-activity amount, insufficient-
  data forecast, and empty-period breakdown all verified via direct
  `curl` against the real seeded ledger (July 2026 activity only,
  hence insufficient forecast data — a data-availability fact of this
  dev environment, not a defect). The NL endpoint was exercised against
  the real LLM (an `OPENAI_API_KEY` is configured in this environment)
  for: amount ("utilities in July 2026"), breakdown ("spending the most
  on this month"), unknown account ("advertising" — correctly 422'd
  with "couldn't find an account" rather than a fabricated figure),
  ambiguous question ("how are we doing" — correctly 422'd with a
  clarifying question), zero-activity amount (January 2026 — correctly
  answered $0.00, not an error), comparison, and forecast (correctly
  reported insufficient data with the estimate framing intact). Also
  confirmed a direct `GET /api/analysis/breakdown` for the current
  month numerically matches the NL breakdown's total (FR-010). Finally
  confirmed `/analysis` renders all four sections in the browser after
  a frontend container restart (Next.js needed one to pick up the new
  top-level route directory).
- Updated `docs/workflow-diagram.drawio` (Principle V): added a
  "Spending Analyzer" box (mirroring the existing detector/retrieval
  boxes' style, explicitly noting "no new tables"), the two new agent
  tools in the tools box, "Analysis" in the frontend label, and two new
  edges.
- Marked all 25 tasks `[X]` in `tasks.md`.

## Outcome

- ✅ Impact: Feature fully implemented and live-verified; all four user
  story acceptance scenarios and the P4 edge cases exercised
  successfully against the real running stack.
- 🧪 Tests: No automated test files added (not requested, matching
  `005`/`007`/`008`'s precedent) — verification was live manual testing
  via `curl` and the browser, plus `ruff`/`tsc` static checks, per this
  session's standing instruction to verify against the running stack
  rather than stopping at lint/typecheck.
- 📁 Files: 9 new backend/frontend files, 5 modified files (`api/agent.py`,
  `main.py`, `Sidebar.tsx`, `workflow-diagram.drawio`, `tasks.md`) — 6
  commits total, one per logical group (service+schemas, agent tools,
  API layer, frontend, diagram, task-list checkmarks).
- 🔁 Next prompts: Push the branch and await the user's own PR merge
  (per saved memory: do not call `gh pr create` proactively).
- 🧠 Reflection: The US1/US4 sequencing decision made at tasks-generation
  time (writing the resolver's full 4-kind vocabulary upfront in Phase 3
  rather than deferring it, unlike `005-reporting`'s precedent) held up
  well in practice — the live NL tests for breakdown/comparison/forecast
  all classified correctly on the first try, with no resolver rework
  needed in what was nominally "Phase 6." The FR-005/FR-004 distinction
  (unmatched account vs. genuinely unclear question) required one
  deliberate design choice not spelled out in `tasks.md`'s task text —
  keeping `request_kind` as `"amount"` rather than nulling it when the
  account doesn't match — worth remembering as the general shape for any
  future bounded-choice resolver in this codebase that needs to
  distinguish "wrong specific value" from "couldn't classify at all."

## Evaluation notes (flywheel)

- Failure modes observed: Next.js's dev server didn't pick up the new
  `/analysis` route directory without a container restart (404 until
  restarted) — a known dev-server behavior for newly added top-level
  route folders, not a code defect. `create-phr.sh` again produced an
  unresolved-placeholder template; filled in manually per the
  agent-native fallback.
- Graders run and results (PASS/FAIL): `ruff check` — PASS (after 2
  fixes); `tsc --noEmit` — PASS; live endpoint verification against
  seeded data — PASS for all reachable scenarios (forecast's
  sufficient-history path untestable in this dev DB's current seed data,
  which only has one month of activity — the insufficient-data path,
  which shares all the same code up to the branch point, was verified).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Seed a few months of
  historical expense activity in a dev fixture to exercise the
  sufficient-history forecast branch directly, rather than only via
  code inspection.
