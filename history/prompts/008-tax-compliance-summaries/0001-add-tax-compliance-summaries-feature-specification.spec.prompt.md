---
id: 0001
title: Add tax compliance summaries feature specification
stage: spec
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 008-tax-compliance-summaries
branch: 008-tax-compliance-summaries
user: Rubaiya-Kamal
command: /sp.specify
labels: ["tax", "compliance", "rag", "sign-off", "ai-agent"]
links:
  spec: specs/008-tax-compliance-summaries/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/008-tax-compliance-summaries/spec.md
 - specs/008-tax-compliance-summaries/checklists/requirements.md
tests:
 - Manual: spec quality checklist self-review — all items passed on first validation pass
---

## Prompt

Tax & Compliance Summaries
Method: RAG (ledger + tax rules documents pe) se summary draft karo; lekin insaan ka sign-off zaroori hai kyunke ye regulatory risk hai.            now create this

## Response snapshot

Started the SDD pipeline for a new feature (branch
`008-tax-compliance-summaries`, next in this repo's numbered sequence),
translating the Hinglish request into English: draft a tax/compliance
summary via retrieval over an admin-maintained reference-document library
plus the ledger's own deterministic figures, gated by mandatory human
sign-off before anything is treated as final. This feature is explicitly
named in the project's constitution (Principle III: "tax/compliance
summaries MUST be presented for human review and MUST NOT be
auto-finalized"), so it was anticipated rather than out of scope.

Wrote `specs/008-tax-compliance-summaries/spec.md` with 4 prioritized user
stories (build a reference-document library [P1] — a prerequisite, since
retrieval needs something to retrieve from; generate a draft summary [P2];
review and sign off [P3]; ask via natural language [P4]), 11 functional
requirements, 2 key entities (Tax Rules Document, Tax/Compliance Summary),
5 edge cases, and 5 measurable success criteria. The single most important
requirement is FR-005/SC-002: the system must explicitly say when no
relevant reference material was found rather than filling the gap with
the AI's own general tax knowledge — the core anti-hallucination guarantee
this feature exists to provide, given the regulatory-risk framing.
Also specified FR-009 (an edge case not explicitly requested by the user
but a natural consequence of the sign-off requirement): sign-off must be
blocked and the admin warned if the underlying ledger data has changed
since a draft was generated, preventing a stale draft from being signed
off as if it reflected current figures.

Kept the "RAG" phrasing confined to the verbatim Input quote and phrased
the actual requirement technology-agnostically ("the system MUST retrieve
the reference-library passages most relevant... before drafting"),
matching the exact pattern `005-reporting` and `007-audit-anomaly-detection`
already established for their own method-naming phrasing.

Generated the spec quality checklist; all items passed on the first
validation pass, so no `[NEEDS CLARIFICATION]` markers or user clarifying
questions were needed.

## Outcome

- ✅ Impact: `specs/008-tax-compliance-summaries/spec.md` is ready for
  `/sp.plan` — establishes scope (admin-provided reference documents only,
  no built-in tax law, no e-filing, single-step sign-off), the
  constitution-aligned boundary between deterministic figures and
  AI-drafted narrative, and the immutability guarantee for signed-off
  summaries.
- 🧪 Tests: No automated tests at this stage (spec-only); quality
  checklist self-review passed on first pass.
- 📁 Files: New `specs/008-tax-compliance-summaries/spec.md` and
  `checklists/requirements.md`.
- 🔁 Next prompts: `/sp.plan` — will need to resolve the retrieval
  mechanism decision (this project has no vector/embedding infrastructure
  today; given the small realistic scale — one admin's own reference
  library, likely a handful to dozens of documents — a lightweight
  in-process embedding-similarity approach may be sufficient without a
  dedicated vector database, but this is a real architectural decision
  research.md should weigh explicitly, likely another ADR candidate); then
  `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: This is the third feature in a row explicitly named by
  the constitution (Principle III lists "audit anomaly flags,
  fraud-pattern detection, and tax/compliance summaries" together as
  requiring human review) — the user is working through that principle's
  named examples in order (audit/anomaly detection was 007, this is the
  tax/compliance one). Continued the established discipline of full SDD
  (spec → plan → tasks → implement) rather than jumping to code, even
  though the user's request was terse ("now create this"), since this is
  exactly the kind of regulatory-risk feature the constitution's
  Principle I rationale calls out as needing the spec-first discipline
  most.

## Evaluation notes (flywheel)

- Failure modes observed: None — spec validation passed on the first
  pass, consistent with every prior feature in this repo.
- Graders run and results (PASS/FAIL): Spec quality checklist — PASS (all
  12 items, first iteration).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
