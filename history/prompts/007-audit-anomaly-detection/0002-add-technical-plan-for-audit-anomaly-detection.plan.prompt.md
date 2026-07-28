---
id: 0002
title: Add technical plan for audit anomaly detection
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 007-audit-anomaly-detection
branch: 007-audit-anomaly-detection
user: Rubaiya-Kamal
command: /sp.plan
labels: ["audit", "anomaly-detection", "isolation-forest", "scikit-learn", "ai-agent"]
links:
  spec: specs/007-audit-anomaly-detection/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/007-audit-anomaly-detection/plan.md
 - specs/007-audit-anomaly-detection/research.md
 - specs/007-audit-anomaly-detection/data-model.md
 - specs/007-audit-anomaly-detection/contracts/audit-api.md
 - specs/007-audit-anomaly-detection/quickstart.md
 - CLAUDE.md (agent-context update script ran; no visible diff — Active Technologies/Recent Changes sections appear stale since before this feature too, pre-existing gap not introduced here)
tests: []
---

## Prompt

(no additional arguments — continuing the SDD pipeline from the prior /sp.specify turn)

## Response snapshot

Ran `.specify/scripts/bash/setup-plan.sh`, read the constitution and prior
features' plans (`004`, `005`) for style precedent, then wrote the Phase 0
research decisions and Phase 1 design artifacts for
`007-audit-anomaly-detection`:

- **research.md**: six decisions — (1) hybrid detector: `scikit-learn`'s
  `IsolationForest` for statistical outlier scoring + two deterministic
  rule checks (exact-duplicate, round-number), since real GL-anomaly tools
  (EY Helix, MindBridge, referenced by the user) combine ML with rule
  heuristics rather than relying on ML alone; (2) fit the model fresh per
  audit run, no persisted/retrained model — simplest approach given this
  project's realistic data scale; (3) active-postings-only filter, reused
  verbatim from `002`/`005`; (4) one batched LLM narration call per run
  (not per flag) to keep latency bounded under the 30s SC-001 target; (5)
  minimum 20-entry threshold before attempting detection; (6) direct
  endpoints in a new `api/audit.py`, NL endpoint in the existing
  `api/agent.py`, mirroring `005`'s established split.
- **data-model.md**: two new persisted tables — `AuditRun` (a triggered
  detection pass, `completed`/`insufficient_data` status) and
  `AnomalyFlag` (one flagged entry per run, with score, reason
  categories, explanation, and a `resolution` lifecycle) — both with real
  enforced FKs, following `004`'s `Match` precedent rather than `002`'s
  non-enforced-FK pattern, since a flag is an operational annotation, not
  a financial posting.
- **contracts/audit-api.md**: `POST /api/audit/runs`, `GET /api/audit/runs`,
  `GET /api/audit/runs/{id}`, `PATCH /api/audit/flags/{id}`, and
  `POST /api/agent/audit/query`.
- **quickstart.md**: 10-step manual validation flow covering all four user
  stories plus the insufficient-data, clean-period, resolution-persistence,
  reversed-entry, and ambiguous-NL-query edge cases.
- **plan.md**: Constitution Check table — Principle III (Human-in-the-Loop)
  is directly satisfied since the constitution *already names* "audit
  anomaly flags, fraud-pattern detection" as requiring human review;
  Principle II is extended by analogy (flags/scores must come from the
  deterministic detector, never the LLM). Flagged the `scikit-learn`
  dependency addition — this project's first ML dependency — as a
  suggested ADR (`anomaly-detection-approach`) per the constitution's
  significance test, surfaced for user consent rather than auto-created.

Ran `update-agent-context.sh claude`; it reported success but produced no
visible diff to `CLAUDE.md` — its Active Technologies/Recent Changes
sections still only mention `001-expense-entry`, a gap that predates this
session (features `002`-`006` aren't listed there either), so not treated
as a regression to fix here.

## Outcome

- ✅ Impact: Full Phase 0/1 planning artifacts ready for `/sp.tasks`;
  Constitution Check passed with one tracked action item (workflow diagram
  update) and one suggested-but-not-yet-created ADR.
- 🧪 Tests: None at this stage (planning-only); quickstart.md's 10 steps
  define the manual validation plan for implementation time.
- 📁 Files: `plan.md`, `research.md`, `data-model.md`,
  `contracts/audit-api.md`, `quickstart.md` all new under
  `specs/007-audit-anomaly-detection/`.
- 🔁 Next prompts: Awaiting user decision on the suggested ADR
  (`/sp.adr anomaly-detection-approach`) before or alongside `/sp.tasks`;
  then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: This is the first feature in this codebase to add a
  dependency in a genuinely new category (ML/statistics, via
  `scikit-learn`) rather than another lightweight utility library (like
  `rapidfuzz` in `004`) — flagged it explicitly for ADR consent per the
  constitution's three-part significance test (long-term consequences,
  real alternatives considered, cross-cutting) rather than deciding
  silently, even though the Constitution Check itself passed without
  requiring Complexity Tracking justification.

## Evaluation notes (flywheel)

- Failure modes observed: `update-agent-context.sh` did not visibly
  update `CLAUDE.md` despite reporting success — worth investigating in a
  future session if keeping that file in sync becomes important, but not
  blocking since it's informational context, not a constitution-mandated
  deliverable.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (one
  tracked action item, no violations).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
