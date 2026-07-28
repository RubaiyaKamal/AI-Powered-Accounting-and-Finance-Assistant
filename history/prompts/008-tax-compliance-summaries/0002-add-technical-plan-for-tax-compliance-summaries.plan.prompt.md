---
id: 0002
title: Add technical plan for tax compliance summaries
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 008-tax-compliance-summaries
branch: 008-tax-compliance-summaries
user: Rubaiya-Kamal
command: /sp.plan
labels: ["tax", "compliance", "rag", "embeddings", "sign-off", "ai-agent"]
links:
  spec: specs/008-tax-compliance-summaries/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/008-tax-compliance-summaries/plan.md
 - specs/008-tax-compliance-summaries/research.md
 - specs/008-tax-compliance-summaries/data-model.md
 - specs/008-tax-compliance-summaries/contracts/tax-api.md
 - specs/008-tax-compliance-summaries/quickstart.md
 - CLAUDE.md (agent-context update script ran; no visible diff — same pre-existing staleness gap noted in prior features' plan sessions)
tests: []
---

## Prompt

(no additional arguments — continuing the SDD pipeline from the prior /sp.specify turn)

## Response snapshot

Ran `setup-plan.sh`, checked whether an `openai` Python client was
already available (it is — a transitive dependency of `openai-agents`,
confirmed via `uv.lock`) before deciding the retrieval architecture, then
wrote the Phase 0/1 planning artifacts for `008-tax-compliance-summaries`:

- **research.md**: seven decisions — (1) in-process embedding retrieval
  via the already-present `openai` client + `numpy` (already present via
  `007`'s `scikit-learn`) for brute-force cosine similarity, with a
  keyword-overlap fallback when no `OPENAI_API_KEY` is set — **no new
  dependency**, rejecting `pgvector`/a dedicated vector DB as unneeded at
  this project's realistic scale; (2) paragraph-level chunking for
  precise citations; (3) reuse `ReportingService.profit_and_loss`
  verbatim rather than duplicating financial computation; (4) citations
  and figures frozen onto the summary row at generation time (denormalized
  snapshot, not a live FK) to satisfy the immutability/document-removal
  edge case; (5) staleness check at sign-off time by recomputing and
  comparing `profit_and_loss`; (6) two narrow LLM calls
  (`draft_summary_narrative`, `resolve_summary_request`) mirroring `005`/
  `007`'s established shape, notably adopting `007`'s "unresolvable, ask
  don't guess" behavior rather than `005`'s silent-default, since guessing
  a tax period is exactly what this feature's regulatory framing argues
  against; (7) direct endpoints in a new `api/tax.py`, NL endpoint in the
  existing `api/agent.py`.
- **data-model.md**: three new tables — `TaxRulesDocument`,
  `TaxRulesDocumentChunk` (nullable embedding column), and `TaxSummary`
  (figures + `cited_passages` JSON snapshot, `draft`/`signed_off` status
  only — discarding a draft hard-deletes the row rather than needing a
  third status, since a never-signed-off draft carries no audit-trail
  obligation).
- **contracts/tax-api.md**: document-library CRUD, `POST /api/tax/summaries`,
  `GET /api/tax/summaries[/{id}]`, `POST /api/tax/summaries/{id}/sign-off`
  (`422` on staleness, `409` if already signed off), `DELETE` for both
  documents and draft summaries (`409` if trying to discard a signed-off
  one), and `POST /api/agent/tax/query`.
- **quickstart.md**: 12-step manual validation flow covering all four
  user stories plus five edge cases (empty library, no relevant material,
  zero-activity period, stale-draft sign-off block, ambiguous NL query),
  including an explicit immutability check (remove a cited document,
  confirm the signed-off summary that cited it is unchanged).
- **plan.md**: Constitution Check — Principle III is directly satisfied
  since the constitution names "tax/compliance summaries" as requiring
  human review; Principle VI passes cleanly since this plan introduces
  **zero new dependencies**. Still flagged the retrieval architecture
  itself (in-process embeddings vs. `pgvector`/vector DB) as a suggested
  ADR (`tax-summary-retrieval-approach`) per the constitution's
  significance test, since it establishes a new pattern even without a
  new package — surfaced for user consent, not auto-created.

## Outcome

- ✅ Impact: Full Phase 0/1 planning artifacts ready for `/sp.tasks`;
  Constitution Check passed with one tracked action item (workflow
  diagram update) and one suggested-but-not-yet-created ADR.
- 🧪 Tests: None at this stage (planning-only); quickstart.md's 12 steps
  define the manual validation plan for implementation time.
- 📁 Files: `plan.md`, `research.md`, `data-model.md`,
  `contracts/tax-api.md`, `quickstart.md` all new under
  `specs/008-tax-compliance-summaries/`.
- 🔁 Next prompts: Awaiting user decision on the suggested ADR before or
  alongside `/sp.tasks`; then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: Checking `uv.lock` before writing the dependency decision
  paid off — confirming `openai` was already installed transitively
  turned what could have been framed as "add a new embeddings client" into
  "zero new dependencies," which meaningfully changes the Constitution
  Check's Principle VI story and is worth verifying rather than assuming
  in any future feature that touches the AI layer.

## Evaluation notes (flywheel)

- Failure modes observed: `update-agent-context.sh` again reported
  success with no visible `CLAUDE.md` diff — same pre-existing gap noted
  in `005` and `007`'s plan sessions, not a regression from this session.
- Graders run and results (PASS/FAIL): Constitution Check — PASS (one
  tracked action item, no violations, zero new dependencies).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
