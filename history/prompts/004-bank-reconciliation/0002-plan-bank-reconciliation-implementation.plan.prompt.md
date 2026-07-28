---
id: 0002
title: Plan bank reconciliation implementation
stage: plan
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 004-bank-reconciliation
branch: 004-bank-reconciliation
user: Rubaiya-Kamal
command: /sp.plan
labels: ["plan", "reconciliation", "bank-transactions", "fuzzy-match"]
links:
  spec: specs/004-bank-reconciliation/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/004-bank-reconciliation/plan.md
 - specs/004-bank-reconciliation/research.md
 - specs/004-bank-reconciliation/data-model.md
 - specs/004-bank-reconciliation/contracts/reconciliation-api.md
 - specs/004-bank-reconciliation/quickstart.md
tests:
 - N/A (plan stage; no code yet)
---

## Prompt

(empty — /sp.plan invoked with no additional arguments, continuing per Auto Mode's bias toward continuing without stopping)

## Response snapshot

Ran setup-plan.sh to scaffold plan.md. Filled Technical Context: same stack as prior features, plus one new dependency (rapidfuzz, for description string-similarity matching) and Python's built-in csv module for parsing (no new dependency there). Constitution Check: PASS on all six principles, one tracked action item (Principle V, diagram update).

Phase 0 (research.md) recorded five decisions: (1) rapidfuzz-based deterministic fuzzy matching instead of an embeddings API call, keeping match scoring fully deterministic per Principle II; (2) a three-tier classification (auto-match/ambiguous-AI-adjudication/no-match) gated by an exact-amount requirement before scoring description similarity, mirroring 002's confidence-threshold pattern; (3) a minimal bank-agnostic 3-column CSV contract (date/amount/description) parsed with the stdlib csv module; (4) a deliberate divergence from 002's pattern — undo/deletion here uses a real, enforced FK with ON DELETE CASCADE and hard-deletes Match rows, since (unlike journal entries) a reconciliation match isn't a financial posting requiring an audit trail, explicitly reasoned through rather than left as an unexplained inconsistency; (5) a new adjudicate_match tool mirroring suggest_account_coding's shape (chooses among deterministically-bounded candidates, can return null, never invents a match from the full dataset).

Phase 1: wrote data-model.md (BankTransaction immutable-by-design with a duplicate-detection unique constraint; Match with a real cascading FK, a full state-transition writeup distinguishing "unmatched," "ambiguous-with-suggestion-but-no-Match-row-yet," and the three ways an item gets resolved), contracts/reconciliation-api.md (5 endpoints: CSV import, list with status filter, review queue with AI reasoning, manual match, dismiss, undo), and quickstart.md (8 manual validation steps covering import, duplicate detection, auto-match, ambiguous-with-reasoning, no-match, queue resolution, undo, and the delete-cascade edge case). Ran update-agent-context.sh claude — no-op, stack already recorded identically.

## Outcome

- ✅ Impact: `004-bank-reconciliation` has a complete technical plan ready for `/sp.tasks`. Notably, this plan explicitly documents and justifies a design choice (hard-delete + real FK cascade) that intentionally diverges from `002`'s established pattern (soft reversal-entries + non-enforced FK) — the plan makes clear this is a considered difference driven by what each spec actually requires, not an inconsistency.
- 🧪 Tests: N/A — plan stage only, no code written yet.
- 📁 Files: specs/004-bank-reconciliation/{plan.md, research.md, data-model.md, quickstart.md, contracts/reconciliation-api.md}
- 🔁 Next prompts: Run `/sp.tasks` to break this into dependency-ordered tasks, then `/sp.implement`.
- 🧠 Reflection: Explicitly writing down *why* this feature's deletion semantics differ from a prior feature's, rather than silently picking whichever pattern seemed convenient, is worth doing every time two similar-looking features actually have different underlying requirements — it prevents a future reader (or a future me) from "fixing" the difference into an inconsistency.

## Evaluation notes (flywheel)

- Failure modes observed: none — plan generation proceeded cleanly using the already-clarified spec.
- Graders run and results (PASS/FAIL): Constitution Check gate — PASS (5/6 clean, 1 tracked action item, no violations requiring Complexity Tracking entries).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none needed; proceed to /sp.tasks.
