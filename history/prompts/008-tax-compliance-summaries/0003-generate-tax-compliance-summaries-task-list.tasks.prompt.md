---
id: 0003
title: Generate tax compliance summaries task list
stage: tasks
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 008-tax-compliance-summaries
branch: 008-tax-compliance-summaries
user: Rubaiya-Kamal
command: /sp.tasks
labels: ["tax", "compliance", "rag", "tasks"]
links:
  spec: specs/008-tax-compliance-summaries/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/008-tax-compliance-summaries/tasks.md
tests: []
---

## Prompt

(no additional arguments)

## Response snapshot

Ran `check-prerequisites.sh`, then generated 32 tasks (T001-T032) across
7 phases for `008-tax-compliance-summaries/tasks.md`:

- **Phase 1 (Setup)**: scaffold new files only — no new dependency task,
  since `research.md` established this feature needs none.
- **Phase 2 (Foundational)**: `TaxRulesDocument`/`TaxRulesDocumentChunk`/
  `TaxSummary` models, migration, Pydantic schemas, and `embed_text`
  (the shared OpenAI-embeddings wrapper both the document-add path and
  the retrieval path need).
- **Phase 3 (US1)**: document CRUD (`add_document` handles chunking +
  embedding), `TaxDocumentLibrary` UI.
- **Phase 4 (US2)**: `_retrieve_passages` (cosine similarity or
  keyword-overlap fallback per chunk), `draft_summary_narrative`,
  `generate` (figures via `reporting_service.profit_and_loss` + retrieval
  + narration + persistence), `POST /api/tax/summaries`,
  `TaxSummaryGenerator` UI.
- **Phase 5 (US3)**: `sign_off` (staleness recompute-and-compare),
  `discard`, `list_summaries`/`get_summary`, the remaining REST endpoints,
  sign-off/discard controls added to `TaxSummaryGenerator`, and the new
  `TaxSummaryHistory` component.
- **Phase 6 (US4)**: `resolve_summary_request` (mirrors `007`'s
  "unresolvable, don't guess" shape) and `POST /api/agent/tax/query` —
  explicitly decided *against* a separate narration-wrapper LLM call here,
  unlike `007`'s `narrate_audit_run`: `generate()` already produces one
  overall narrative per summary (not per-item explanations the way
  `explain_flags` does), so the NL endpoint just reuses that narrative
  directly rather than adding a redundant LLM call.
- **Phase 7 (Polish)**: workflow diagram update, `quickstart.md`
  validation, cleanup.

Noted in the Implementation Strategy section that unlike prior features,
US1 alone isn't a meaningful standalone demo (an empty-of-purpose document
library) — the real MVP is US1+US2 together, and called this out
explicitly rather than defaulting to the usual "US1 alone is the MVP"
framing.

## Outcome

- ✅ Impact: `specs/008-tax-compliance-summaries/tasks.md` is ready for
  `/sp.implement`.
- 🧪 Tests: No test tasks generated (not requested, matching prior
  features' precedent); `quickstart.md`'s 12 steps remain the validation
  plan for implementation time (T031).
- 📁 Files: New `specs/008-tax-compliance-summaries/tasks.md` (32 tasks).
- 🔁 Next prompts: `/sp.implement` to build the feature (the suggested
  `tax-summary-retrieval-approach` ADR from the plan stage is still
  undecided — can proceed with or without it, per the constitution's
  "wait for consent, don't block" ADR protocol).
- 🧠 Reflection: Caught and corrected an over-application of `007`'s
  pattern during drafting — initially assumed a `narrate_audit_run`-style
  wrapper call would be needed for the NL path here too, then recognized
  that assumption didn't hold: audit needed a separate narration step
  because `explain_flags` produces many small per-flag explanations with
  no natural single "narrative," while this feature's `generate()` already
  produces exactly one overall narrative meant for a human to read.
  Reusing it directly avoids an unnecessary LLM call and is simpler
  (Principle VI) — worth remembering that not every reporting-adjacent
  feature needs the full two-call shape; the right shape depends on
  whether the underlying result already has a natural single narrative.

## Evaluation notes (flywheel)

- Failure modes observed: None.
- Graders run and results (PASS/FAIL): n/a (task generation, not a gated
  validation step).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
