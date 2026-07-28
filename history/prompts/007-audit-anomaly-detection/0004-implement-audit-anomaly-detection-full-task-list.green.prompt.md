---
id: 0004
title: Implement audit anomaly detection full task list
stage: green
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 007-audit-anomaly-detection
branch: 007-audit-anomaly-detection
user: Rubaiya-Kamal
command: /sp.implement
labels: ["audit", "anomaly-detection", "isolation-forest", "scikit-learn", "ai-agent"]
links:
  spec: specs/007-audit-anomaly-detection/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - backend/pyproject.toml
 - backend/uv.lock
 - backend/src/models/audit_run.py
 - backend/src/models/anomaly_flag.py
 - backend/src/models/__init__.py
 - backend/migrations/versions/20260728_0004_audit_anomaly_detection_schema.py
 - backend/src/schemas/audit.py
 - backend/src/services/audit_service.py
 - backend/src/agent/audit_tools.py
 - backend/src/api/audit.py
 - backend/src/api/agent.py
 - backend/src/main.py
 - frontend/src/services/auditApi.ts
 - frontend/src/components/AuditRunner.tsx
 - frontend/src/components/AuditHistory.tsx
 - frontend/src/app/audit/page.tsx
 - frontend/src/components/Sidebar.tsx
 - docker-compose.yml
 - docs/workflow-diagram.drawio
 - specs/007-audit-anomaly-detection/tasks.md
tests:
 - Manual: ruff check (backend, full repo) — all checks passed
 - Manual: tsc --noEmit (frontend) — no errors, after every phase
 - Manual: quickstart.md's 10-step flow executed live against the running docker-compose stack with real seeded ledger data (22+ posted entries) and a live OpenAI key — insufficient-data, seeded-anomaly detection with correct reason categories and LLM explanations, clean-period zero-flags, resolution recording/persistence across re-view and history, reversed-entry historical-record edge case, and all three NL-query scenarios
---

## Prompt

/sp.implement

## Response snapshot

Implemented all 28 tasks (T001-T028) from
specs/007-audit-anomaly-detection/tasks.md across 7 phases:

- Phase 1-2: added `scikit-learn` (this project's first ML dependency),
  scaffolded new files, built `AuditRun`/`AnomalyFlag` SQLAlchemy models +
  Alembic migration + Pydantic schemas, and the shared active-postings
  entry-range query.
- Phase 3 (US1, MVP): the hybrid detector — `IsolationForest` (fixed
  seed, contamination=0.1) over [amount, one-hot account pair,
  day-of-week, day-of-month] features, combined with deterministic
  duplicate/round-number rule checks and a best-effort reason-category
  decomposition for ML flags (comparing to per-account mean/stdev, rare
  account pairings, weekend timing) — plus `explain_flags` (one batched
  LLM call per run), `run_audit`, `POST /api/audit/runs`, and the
  `AuditRunner` UI.
- Phase 4 (US2): flag resolution (`PATCH /api/audit/flags/{id}`) with
  confirmed_issue/false_positive/no_action_needed.
- Phase 5 (US3): audit history (`GET /api/audit/runs[/{id}]`) and the
  `AuditHistory` UI, reusing `AuditRunner`'s exported `AuditRunResults`.
- Phase 6 (US4): `resolve_audit_request`/`narrate_audit_run` (mirroring
  005-reporting's split) and `POST /api/agent/audit/query` — unlike
  reporting, an unresolvable period returns 422 rather than silently
  defaulting, per this feature's spec Edge Cases.
- Phase 7: workflow diagram update (added the detector as its own
  deterministic component, distinct from the LLM tools box), full
  quickstart validation, cleanup.

Found and fixed three real bugs during live testing: (1) `_evaluate_entries`
computed `resolved_end=today()` for display but never applied it as an
actual query filter when no range was given, letting a future-dated entry
slip into "evaluated"; (2) `explain_flags`' JSON-array parsing broke
whenever gpt-4o-mini wrapped its reply in a markdown code fence, silently
triggering the fallback for every flag in a run — added `_strip_code_fence`;
(3) Docker-on-Windows: installing `scikit-learn` inside the backend
container failed repeatedly with intermittent file-copy/rename errors
because `.venv` lived on the Windows bind mount — fixed by adding an
anonymous `.venv` volume to `docker-compose.yml`'s backend service,
mirroring the frontend's existing `node_modules` pattern.

Seeded 22+ real expense entries (typical + four deliberate anomalies:
an amount outlier, a round number, and a duplicate pair) through the
actual expense→coding→posting flow to validate detection against real
data rather than synthetic fixtures. Committed after each phase (7
commits) per the constitution's Principle IV.

## Outcome

- ✅ Impact: Feature 007-audit-anomaly-detection is fully implemented —
  hybrid statistical/ML anomaly detection over posted journal entries,
  with a persisted review/resolution lifecycle and a natural-language
  query path, all constitution-compliant (flags/scores are 100%
  deterministic; the LLM only explains/narrates; human review required
  before any flag is "resolved").
- 🧪 Tests: No automated test suite generated (not requested, matching
  prior-feature precedent); validated via lint/typecheck after every
  phase plus a full live run of quickstart.md's 10 steps against real
  seeded data and a live LLM.
- 📁 Files: 4 new backend modules (models x2, service, agent tools) + 1
  migration + 1 schema module, 1 new API router + 1 modified router +
  main.py registration, 3 new/modified frontend files + Sidebar nav
  link, 1 docker-compose.yml infra fix, 1 diagram update, 1 tasks.md
  fully checked off.
- 🔁 Next prompts: Open a PR from 007-audit-anomaly-detection into main;
  the suggested ADR (`anomaly-detection-approach`) from the plan stage
  is still undecided — user proceeded straight to implementation without
  requesting it, consistent with the "wait for consent, don't block"
  protocol.
- 🧠 Reflection: All three bugs found during this session were caught by
  insisting on live end-to-end verification against the running stack
  rather than trusting lint/typecheck alone — the code-fence bug in
  particular produced no error or exception anywhere (the fallback path
  is silent by design, matching this codebase's existing fallback
  philosophy), so it would have shipped invisibly without manually
  inspecting the actual explanation text in a live response.

## Evaluation notes (flywheel)

- Failure modes observed: (1) date-filter bug in `_evaluate_entries`
  (label vs. actual query mismatch) — caught by comparing evaluated-entry
  counts against manually-computed expectations from raw journal-entry
  data; (2) silent LLM markdown-fence JSON-parsing failure in
  `explain_flags` — caught by noticing explanation text looked templated
  rather than natural prose, then reproducing directly against the
  container; (3) Docker-on-Windows bind-mount file-copy failures
  installing `scikit-learn` — recovered by giving `.venv` its own volume
  instead of retrying (retries alone didn't help, confirming it wasn't
  transient).
- Graders run and results (PASS/FAIL): ruff check — PASS (full repo,
  every phase); tsc --noEmit — PASS (every phase); live quickstart.md
  10-step walkthrough — PASS (all steps, including two edge cases
  re-verified explicitly: reversed-entry historical record, and clean
  vs. insufficient-data period behavior).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
