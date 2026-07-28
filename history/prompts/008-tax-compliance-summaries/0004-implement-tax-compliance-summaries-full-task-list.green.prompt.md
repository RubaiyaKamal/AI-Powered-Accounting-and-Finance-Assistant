---
id: 0004
title: Implement tax compliance summaries full task list
stage: green
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 008-tax-compliance-summaries
branch: 008-tax-compliance-summaries
user: Rubaiya-Kamal
command: /sp.implement
labels: ["tax", "compliance", "rag", "embeddings", "sign-off", "ai-agent"]
links:
  spec: specs/008-tax-compliance-summaries/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/config.py
 - backend/src/models/tax_rules_document.py
 - backend/src/models/tax_rules_document_chunk.py
 - backend/src/models/tax_summary.py
 - backend/src/models/__init__.py
 - backend/migrations/versions/20260728_0005_tax_compliance_summaries_schema.py
 - backend/src/schemas/tax.py
 - backend/src/services/tax_document_service.py
 - backend/src/services/tax_summary_service.py
 - backend/src/agent/tax_tools.py
 - backend/src/api/tax.py
 - backend/src/api/agent.py
 - backend/src/main.py
 - frontend/src/services/taxApi.ts
 - frontend/src/components/TaxDocumentLibrary.tsx
 - frontend/src/components/TaxSummaryGenerator.tsx
 - frontend/src/components/TaxSummaryHistory.tsx
 - frontend/src/app/tax/page.tsx
 - frontend/src/components/Sidebar.tsx
 - docs/workflow-diagram.drawio
 - specs/008-tax-compliance-summaries/tasks.md
tests:
 - Manual: ruff check (backend, full repo) — all checks passed
 - Manual: tsc --noEmit (frontend) — no errors, after every phase
 - Manual: quickstart.md's 12-step flow executed live against the running docker-compose stack with real seeded ledger data and a live OpenAI key — all steps confirmed, including two re-verified explicitly at Polish time (no-relevant-material against a cleared library, and figures matching reporting_service.profit_and_loss exactly)
---

## Prompt

now build this

## Response snapshot

Implemented all 32 tasks (T001-T032) from
specs/008-tax-compliance-summaries/tasks.md across 7 phases:

- Phase 1-2: scaffolded files, added `EMBEDDING_MODEL` config, built
  `TaxRulesDocument`/`TaxRulesDocumentChunk` (nullable embedding column)/
  `TaxSummary` (figures + `cited_passages` JSON snapshot) models +
  migration + schemas, and `embed_text` (OpenAI embeddings via the
  already-present `openai` client — no new dependency).
- Phase 3 (US1): document add (paragraph chunking + per-chunk embedding),
  list/view/remove, `TaxDocumentLibrary` UI. Live-verified: a 3-paragraph
  document produced 3 chunks each with a real 1536-dim embedding stored
  in Postgres.
- Phase 4 (US2, MVP core): `_retrieve_passages` (cosine similarity via
  `numpy`, or keyword-overlap fallback per chunk), `draft_summary_narrative`,
  `generate` (figures via `reporting_service.profit_and_loss` — reused
  verbatim, not reimplemented), `POST /api/tax/summaries`,
  `TaxSummaryGenerator` UI. Live-verified against real seeded ledger data:
  a grounded draft correctly cited all three relevant reference passages
  with an accurate narrative; zero-activity period produced a valid
  zero-figure draft.
- Phase 5 (US3): `sign_off` (recomputes and compares `profit_and_loss`,
  blocking on drift), `discard` (blocked once signed off), history
  queries, remaining endpoints, sign-off/discard controls, and
  `TaxSummaryHistory`. Live-verified: sign-off, re-sign-off 409,
  discard-after-sign-off 409, stale-draft sign-off 422 (after posting a
  new expense entry into the draft's period), and — the feature's core
  safety guarantee — removing a cited reference document left a
  signed-off summary's citations completely unchanged.
- Phase 6 (US4): `resolve_summary_request` (mirrors `007`'s "unresolvable,
  don't guess" shape rather than `005`'s silent-default) and
  `POST /api/agent/tax/query`, deliberately reusing `generate()`'s own
  narrative instead of adding a redundant narration call (documented this
  as a correction of an initial over-application of `007`'s pattern
  during the tasks-stage planning). Live-verified: "draft a tax summary
  for this month" resolved correctly; "what do we owe" (no period)
  correctly returned 422 with a clarifying question.
- Phase 7: workflow diagram update (added a "Retrieval Index" box as its
  own deterministic component, alongside the existing "Anomaly Detector"
  box, both distinct from the LLM tools box), explicit re-verification of
  the no-relevant-material edge case (cleared the library entirely and
  confirmed `cited_passages: []` with an honest narrative) and the
  figures-match-reporting check (`total_revenue`/`total_expenses`/
  `net_profit` byte-for-byte identical between `/api/tax/summaries` and
  `/api/reports/profit-and-loss` for the same period), cleanup.

Committed after each phase (7 commits) per the constitution's Principle
IV. No new backend dependency was needed for this feature — confirmed
`openai` was already available transitively via `openai-agents` and
`numpy` via `007`'s `scikit-learn`, so no Docker/venv issues arose this
time (unlike `007`'s `scikit-learn` install saga).

## Outcome

- ✅ Impact: Feature 008-tax-compliance-summaries is fully implemented —
  RAG-grounded tax/compliance summary drafting over an admin-maintained
  reference library, with mandatory human sign-off, staleness protection,
  and full immutability after sign-off. This closes out all three
  features the constitution's Principle III named by example (audit
  anomaly detection in `007`, tax/compliance summaries here).
- 🧪 Tests: No automated test suite generated (not requested, matching
  prior-feature precedent); validated via lint/typecheck after every
  phase plus a full live run of quickstart.md's 12 steps, with two edge
  cases explicitly re-verified at Polish time rather than assumed correct
  from code review alone.
- 📁 Files: 3 new backend models + 1 migration + 1 schema module + 2
  service modules + 1 agent-tools module, 1 new API router + 1 modified
  router + main.py registration, 4 new/modified frontend files + Sidebar
  nav link, 1 diagram update, 1 tasks.md fully checked off.
- 🔁 Next prompts: Open a PR from 008-tax-compliance-summaries into main;
  the suggested ADR (`tax-summary-retrieval-approach`) from the plan
  stage was never explicitly accepted or declined — proceeded straight to
  implementation, consistent with the "wait for consent, don't block"
  protocol.
- 🧠 Reflection: This is the third feature built in this session following
  the same spec → plan → tasks → implement rhythm (005 reporting, 007
  audit, 008 tax) — the established codebase patterns (two-narrow-LLM-call
  shape, active-postings filter reuse, deterministic-computation-only
  figures, frozen snapshots for immutability) transferred cleanly each
  time, but each feature still needed at least one genuine judgment call
  rather than blind pattern-copying: 007 needed the `.venv` Docker volume
  fix and the code-fence-stripping fix; 008 needed recognizing that its
  NL path didn't need a `narrate_audit_run`-style wrapper at all. Worth
  continuing to verify live rather than assuming a new feature is just
  "the same shape as last time."

## Evaluation notes (flywheel)

- Failure modes observed: None new in this session — the code-fence
  stripping fix from `007` was proactively applied to `resolve_summary_request`
  from the start (learned from `007`'s live-testing discovery), avoiding
  a repeat of that silent-fallback bug here.
- Graders run and results (PASS/FAIL): ruff check — PASS (full repo,
  every phase); tsc --noEmit — PASS (every phase); live quickstart.md
  12-step walkthrough — PASS (all steps, with the no-relevant-material
  and figures-match-reporting checks explicitly re-verified rather than
  inferred).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
