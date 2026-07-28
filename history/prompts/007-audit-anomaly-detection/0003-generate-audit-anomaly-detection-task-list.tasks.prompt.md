---
id: 0003
title: Generate audit anomaly detection task list
stage: tasks
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 007-audit-anomaly-detection
branch: 007-audit-anomaly-detection
user: Rubaiya-Kamal
command: /sp.tasks
labels: ["audit", "anomaly-detection", "tasks"]
links:
  spec: specs/007-audit-anomaly-detection/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/007-audit-anomaly-detection/tasks.md
tests: []
---

## Prompt

(no additional arguments)

## Response snapshot

Ran `check-prerequisites.sh`, read the tasks template and
`004-bank-reconciliation`'s `tasks.md` for style precedent, then generated
28 tasks (T001-T028) across 7 phases for
`007-audit-anomaly-detection/tasks.md`:

- **Phase 1 (Setup)**: add `scikit-learn` dependency; scaffold new files.
- **Phase 2 (Foundational)**: `AuditRun`/`AnomalyFlag` SQLAlchemy models,
  migration, Pydantic schemas, and the shared active-postings entry-range
  query (`_evaluate_entries`, reusing the `002`/`005` filter).
- **Phase 3 (US1, MVP)**: the hybrid detector (`_detect` — IsolationForest
  + duplicate/round-number rules), the batched `explain_flags` tool,
  `run_audit` (threshold check → detect → explain → persist),
  `POST /api/audit/runs`, and the `AuditRunner` frontend component.
- **Phase 4 (US2)**: `resolve_flag`, `PATCH /api/audit/flags/{id}`,
  resolution controls in the UI.
- **Phase 5 (US3)**: list/get past runs, `GET /api/audit/runs[/{id}]`,
  the `AuditHistory` component.
- **Phase 6 (US4)**: `resolve_audit_request`/`narrate_audit_run` (mirroring
  `005`'s `resolve_report_request`/`narrate_report` split),
  `POST /api/agent/audit/query`, and the chat-style query box.
- **Phase 7 (Polish)**: workflow diagram update, `quickstart.md`
  validation, cleanup.

Each task cites the specific `spec.md` FR(s), `data-model.md`/
`contracts/audit-api.md` sections, or `research.md` decision it
implements, following this repo's established task-writing convention.
Dependencies section documents phase/task ordering; noted `scikit-learn`
as this project's first ML dependency in the Notes section, pointing back
to the still-pending ADR suggestion from the plan stage.

## Outcome

- ✅ Impact: `specs/007-audit-anomaly-detection/tasks.md` is ready for
  `/sp.implement`; US1 alone is a demoable MVP (run an audit, see flagged
  entries with plain-language explanations).
- 🧪 Tests: No test tasks generated (not requested, matching prior
  features' precedent); `quickstart.md`'s 10 steps remain the validation
  plan for implementation time (T027).
- 📁 Files: New `specs/007-audit-anomaly-detection/tasks.md` (28 tasks).
- 🔁 Next prompts: `/sp.implement` to build the feature (still pending
  user decision on the suggested `anomaly-detection-approach` ADR from
  the plan stage — can proceed with or without it, per the constitution's
  "wait for consent, don't block" ADR protocol).
- 🧠 Reflection: Kept US4's natural-language tools
  (`resolve_audit_request`/`narrate_audit_run`) in their own phase after
  US1-US3, but noted `explain_flags` (per-flag explanation, required by
  every audit run regardless of entry point) belongs in US1 itself rather
  than the NL phase — a similar split to how `005-reporting` separated
  its four report functions from the cross-cutting NL resolution/narration
  layer, adapted here since this feature has only one "report type"
  (an audit run) rather than four.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): n/a (task generation, not a gated
  validation step).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
