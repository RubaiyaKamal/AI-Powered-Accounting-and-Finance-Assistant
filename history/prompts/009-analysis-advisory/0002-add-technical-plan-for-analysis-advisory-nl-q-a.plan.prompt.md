---
id: 0002
title: Add technical plan for analysis advisory NL Q&A
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 009-analysis-advisory
branch: 009-analysis-advisory
user: Rubaiya-Kamal
command: /sp.plan
labels: ["analysis", "advisory", "nl-qa", "forecasting", "linear-regression", "ai-agent"]
links:
  spec: specs/009-analysis-advisory/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/009-analysis-advisory/plan.md
 - specs/009-analysis-advisory/research.md
 - specs/009-analysis-advisory/data-model.md
 - specs/009-analysis-advisory/contracts/analysis-api.md
 - specs/009-analysis-advisory/quickstart.md
 - CLAUDE.md (agent-context update script ran; same pre-existing staleness gap noted in prior features' plan sessions)
tests: []
---

## Prompt

now create the plan

## Response snapshot

Wrote the Phase 0/1 planning artifacts for `009-analysis-advisory`,
resolving the architectural tension flagged at spec time:

- **research.md**: six decisions — (1) bounded classify-then-compute,
  explicitly rejecting the literal "text-to-SQL" reading of the Input —
  reasoned through why even a *successful*, non-hallucinated LLM-authored
  SQL query is still a real risk (a subtly wrong filter returns a real
  but incorrect number), and why this codebase's precedent of writing the
  active-postings filter exactly once and reusing it everywhere is the
  safer pattern to extend here too; (2) every figure reuses
  `reporting_service.profit_and_loss`'s own `expense_lines`/
  `total_expenses` output — no new aggregation query; (3) account-name
  resolution bound to the real chart of accounts, mirroring `002`'s
  `suggest_account_coding` pattern exactly; (4) forecasting via
  `scikit-learn`'s `LinearRegression` (already present since `007`) over
  a 6-month lookback window with a 3-month minimum, rejecting heavier
  time-series libraries as unjustified at this project's realistic data
  scale; (5) a single NL endpoint covers all four request kinds, with
  *no* direct REST endpoint for the single-amount kind, since spec.md's
  US1/FR-001 describe that capability only via natural language; (6)
  period defaults mirror direct-request defaults (current month) for
  breakdown/comparison/forecast — only request-kind or account ambiguity
  triggers FR-004's clarifying-question path, not every omitted period.
- **data-model.md**: four computed response shapes (Spending Amount,
  Breakdown, Comparison, Forecast) — no new tables, all built from
  `profit_and_loss` output, matching `005-reporting`'s fully-computed
  precedent since this feature has no review/sign-off lifecycle.
- **contracts/analysis-api.md**: `GET /api/analysis/{breakdown,
  comparison,forecast}` and `POST /api/agent/analysis/query` (the sole
  entry point for `amount`-kind requests too).
- **quickstart.md**: 10-step validation flow covering all four user
  stories plus five edge cases (empty period, invalid range, insufficient
  forecast data, unknown account, ambiguous question).
- **plan.md**: Constitution Check — Principle III is N/A (Analysis &
  Advisory isn't one of the constitution's named regulated-action
  examples, unlike `007`/`008`); Principle VI passes cleanly with zero
  new dependencies. Flagged the query-approach + forecasting-method
  decisions together as one suggested ADR
  (`spending-qa-query-approach`), since both are genuine architectural
  choices even without a new package, surfaced for consent rather than
  auto-created.

## Outcome

- ✅ Impact: Full Phase 0/1 planning artifacts ready for `/sp.tasks`;
  Constitution Check passed with one tracked action item (workflow
  diagram update) and one suggested-but-not-yet-created ADR.
- 🧪 Tests: None at this stage (planning-only); quickstart.md's 10 steps
  define the manual validation plan for implementation time.
- 📁 Files: `plan.md`, `research.md`, `data-model.md`,
  `contracts/analysis-api.md`, `quickstart.md` all new under
  `specs/009-analysis-advisory/`.
- 🔁 Next prompts: Awaiting user decision on the suggested ADR before or
  alongside `/sp.tasks`; then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: This plan formalizes the pushback flagged in the spec
  session — worth confirming the reasoning held up under more detailed
  design pressure, and it did: reusing `profit_and_loss` for literally
  every figure (amount, breakdown, comparison, and forecast's training
  data) turned out to be a clean, unifying decision that also happens to
  be the simplest one, not just the safest — the two didn't trade off
  against each other here, which is a good sign the design is on the
  right track rather than being safety-first at the cost of elegance.

## Evaluation notes (flywheel)

- Failure modes observed: `update-agent-context.sh` again reported
  success with no visible `CLAUDE.md` diff — same pre-existing gap noted
  in `005`/`007`/`008`'s plan sessions.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (one
  tracked action item, no violations, zero new dependencies, Principle
  III correctly scoped N/A).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
