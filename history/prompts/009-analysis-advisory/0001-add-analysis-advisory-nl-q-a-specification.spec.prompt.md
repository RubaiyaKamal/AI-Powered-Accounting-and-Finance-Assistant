---
id: 0001
title: Add analysis advisory NL Q&A specification
stage: spec
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 009-analysis-advisory
branch: 009-analysis-advisory
user: Rubaiya-Kamal
command: /sp.specify
labels: ["analysis", "advisory", "nl-qa", "forecasting", "ai-agent"]
links:
  spec: specs/009-analysis-advisory/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/009-analysis-advisory/spec.md
 - specs/009-analysis-advisory/checklists/requirements.md
tests:
 - Manual: spec quality checklist self-review — all items passed on first validation pass
---

## Prompt

Analysis & Advisory / NL Q&A ("March mein utilities pe kitna kharcha hua?", spending patterns, forecasting)
Method: RAG/text-to-SQL transaction database pe + LLM narration; forecasting ke liye time-series/statistical models jinhe LLM explain kare.          now create this

## Response snapshot

Started the SDD pipeline for a new feature (branch `009-analysis-advisory`,
next in this repo's numbered sequence), translating the Hinglish request
into English. The user named "text-to-SQL" as the method, but rather than
letting the spec commit to that literally, framed FR-002/FR-003
technology-agnostically ("resolve into one of the supported kinds of
requests," "deterministic computation") — flagged in the response (and in
the checklist Notes) that free-form LLM-authored SQL is a real
architectural risk this codebase has specifically avoided elsewhere (the
"active postings only" filter has been carefully reused verbatim across
`002`/`005`/`007`/`008` specifically to prevent this class of bug; letting
an LLM freely construct SQL per-question would risk silently reintroducing
it). The actual retrieval mechanism (structured query resolution vs. raw
SQL) is a planning-stage decision, deferred to `/sp.plan`.

Wrote `specs/009-analysis-advisory/spec.md` with 4 prioritized user
stories (ask a single spending question in NL [P1, the flagship,
explicitly-named example] — a departure from prior features where NL was
always the *last*-added capability, since here it's the primary named
capability; view spending pattern breakdowns/comparisons [P2]; get a
spending forecast [P3]; ask for patterns/forecasts via chat too [P4]), 11
functional requirements, and 5 edge cases. The key scope-bounding decision
is FR-003: a *fixed* set of four supported request kinds (amount,
breakdown, comparison, forecast) rather than fully open-ended analytical
Q&A — without this boundary, "ask anything about the ledger" would be
untestable and would risk exactly the SQL-hallucination problem the
Input's own method described (LLM-authored SQL) exists to avoid.

No new persisted entities (mirrors `005-reporting`'s fully-computed-
on-demand shape, since nothing here needs a review/sign-off lifecycle the
way `007`/`008` did). Generated the spec quality checklist; all items
passed on the first validation pass.

## Outcome

- ✅ Impact: `specs/009-analysis-advisory/spec.md` is ready for
  `/sp.plan` — establishes the fixed-request-kind scope boundary, the
  constitution-aligned figure/AI boundary, and the "forecast must be
  labeled an estimate" requirement.
- 🧪 Tests: No automated tests at this stage (spec-only); quality
  checklist self-review passed on first pass.
- 📁 Files: New `specs/009-analysis-advisory/spec.md` and
  `checklists/requirements.md`.
- 🔁 Next prompts: `/sp.plan` — will need to resolve the structured-query
  mechanism (rejecting literal LLM-authored SQL in favor of a bounded
  parameter-resolution approach reusing the existing active-postings
  filter) and the forecasting method (likely linear regression via
  `scikit-learn`, already present from `007` — no new dependency
  anticipated); then `/sp.tasks` and `/sp.implement`.
- 🧠 Reflection: This is the fourth AI-touching feature built this session
  (`005` reporting, `007` audit, `008` tax, now `009` analysis) and the
  first where the user's named method (raw text-to-SQL) was judged to
  need active pushback rather than straightforward technology-agnostic
  translation — worth flagging explicitly rather than silently
  substituting a safer approach, since the user should see that reasoning
  before planning locks it in.

## Evaluation notes (flywheel)

- Failure modes observed: None — spec validation passed on the first
  pass, consistent with every prior feature in this repo.
- Graders run and results (PASS/FAIL): Spec quality checklist — PASS (all
  12 items, first iteration).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
