# Phase 0 Research: Bank/Vendor Reconciliation

The backend/frontend/database/AI stack is fixed by the constitution and
already established by prior features — no `NEEDS CLARIFICATION` markers
remain in Technical Context. This document records the feature-scoped
design decisions specific to matching, CSV ingestion, and undo/deletion
semantics.

## Decision: Deterministic fuzzy-string matching, not embeddings

**Decision**: Description similarity is computed with `rapidfuzz`'s
`token_set_ratio` (case/punctuation-normalized via its `default_process`),
combined with exact amount comparison and a date-proximity window
(candidates within a configurable number of days), producing a
deterministic composite score per candidate. No embeddings API call is
made for scoring. `token_set_ratio` specifically — not `token_sort_ratio`
— was chosen after live testing showed real bank-statement descriptions
are typically terser/abbreviated versions of the fuller expense
description (e.g. "WIFI CHARGES JULY" vs "Wi-fi charges for the month
July"): `token_sort_ratio` penalizes the expense description's extra words
as a mismatch, while `token_set_ratio` correctly scores a token-subset
relationship highly.
**Rationale**: The spec's own language ("embedding/fuzzy matching") allows
either interpretation; a pure string-similarity approach is simpler, adds
no new external API dependency or per-transaction cost, and is fully
deterministic and explainable — directly serving constitution Principle II
(the match *score* must be deterministic; only genuinely ambiguous cases
should ever reach the LLM, per FR-006). `rapidfuzz` is a small, well-known
Python library with no heavy ML dependencies (unlike a real embeddings
pipeline), keeping this feature's footprint proportional to its scope.
**Alternatives considered**: OpenAI embeddings for description similarity
(rejected — adds a per-transaction API call and cost for a scoring step
that doesn't need semantic understanding, just textual similarity; also
harder to reason about deterministically than a fuzzy-string ratio);
Python's built-in `difflib.SequenceMatcher` (rejected — `rapidfuzz` is
faster and more robust for this exact use case, at negligible added
dependency weight).

## Decision: Matching thresholds and classification

**Decision**: For each unmatched bank transaction, candidate expense
entries are scored only if the amount matches exactly and the date is
within a configurable window (default 5 days). Among amount/date-eligible
candidates, a composite score blends description similarity with date
closeness. Classification:
- **Auto-match**: exactly one candidate scores above a high threshold
  (default 90/100) with a clear margin over the next-best candidate.
- **Ambiguous (AI adjudication)**: two or more candidates score above a
  lower threshold (default 60/100), or the top candidate doesn't clear the
  auto-match bar by a sufficient margin over the runner-up.
- **No match**: no candidate clears even the lower threshold, or no
  amount/date-eligible candidates exist at all — routed straight to the
  review queue with no AI call (no plausible candidates to adjudicate
  between).
**Rationale**: Mirrors `002-ledger-journal-entries`'s confidence-threshold
pattern (auto-approve above a threshold, mandatory review below it) —
already a proven, constitution-aligned shape in this codebase. Requiring
an exact amount match before scoring description similarity directly
implements the spec's Edge Case ("a bank fee reduces the amount → treated
as, at best, ambiguous, never auto-matched") cheaply, since a
non-exact-amount candidate simply never reaches the auto-match path.
**Alternatives considered**: A single overall confidence score blending
amount/date/description without an amount-exactness gate (rejected — would
require the description-similarity blend to somehow "know" that a
$5-off amount should suppress auto-matching, which the exact-amount gate
achieves more simply and transparently); making thresholds business-scope
decisions requiring their own spec-level clarification (rejected — same
reasoning as `002`'s confidence threshold: exact numeric defaults are an
implementation detail, not a scope decision, per this spec's Assumptions).

## Decision: CSV format and parsing

**Decision**: Accept a CSV with three required columns, matched
case-insensitively by header name: `date`, `amount`, `description` (extra
columns are ignored). Parsed with Python's built-in `csv` module — no new
dependency. A malformed row (missing/unparseable date or amount) is
skipped and reported in the import response; valid rows in the same file
still import (spec Edge Cases).
**Rationale**: The clarified scope (FR-002) is CSV-only, and this project
has no existing convention for a specific bank's export format to target —
a minimal three-column contract is the smallest schema that satisfies
FR-001's stated fields (date, amount, description) without inventing
requirements the spec doesn't ask for.
**Alternatives considered**: Supporting a specific bank's proprietary CSV
column layout (rejected — no such requirement exists; a
minimal/normalized column contract keeps this feature bank-agnostic, and
real users can export/rename columns to match before uploading);
OFX/QFX format support (rejected — the spec clarified CSV specifically,
and OFX parsing is meaningfully more complex for no requirement calling
for it).

## Decision: Undo and deletion — hard delete, not reversal entries

**Decision**: Undoing a match (FR-011) deletes the `Match` row outright.
When the expense-entry side of a match is deleted, the `Match` row is
removed via a real, enforced foreign-key `ON DELETE CASCADE` (unlike
`002-ledger-journal-entries`'s deliberately non-enforced FK for the same
kind of relationship).
**Rationale**: A reconciliation `Match` is an operational link, not a
financial posting — nothing about it needs to survive as an audit trail
the way a posted journal entry does (which the constitution and spec
explicitly required to persist even after reversal, in `002`). The spec
here has no equivalent requirement; FR-013 just says the bank transaction
"returns to the review queue," which a plain cascade delete achieves for
free at the database level, with zero application code needed for that
case. This is a deliberate, spec-scoped difference from `002`'s pattern —
not an oversight — recorded here so a future reader doesn't assume the two
features should be consistent for consistency's sake.
**Alternatives considered**: Soft-deleting/status-flagging `Match` rows
instead of hard-deleting (rejected — no requirement for match history
after undo/cascade exists in this spec; adds complexity — status filtering
everywhere a "current match" is queried — for no stated benefit); mirroring
`002`'s non-FK + application-level cleanup approach (rejected — that
complexity existed in `002` specifically *because* journal entries had to
survive; here nothing needs to survive, so the simpler, DB-enforced
cascade is strictly better, per Principle VI).

## Decision: AI adjudication tool shape

**Decision**: A new `adjudicate_match(bank_transaction, candidates) ->
{"chosen_expense_entry_id": <id> | null, "reasoning": "<text>"}` function
in a new `backend/src/agent/reconciliation_tools.py`, following the same
lazy-import, deterministic-fallback pattern as `expense_tools.py` and
`ledger_tools.py`. It is given only the candidates the deterministic pass
already identified as plausible (never the full expense-entry table) and
may return `null` (no confident choice among the candidates either) — in
which case the transaction still lands in the review queue, just without
a suggested match, same as the no-candidates-at-all path.
**Rationale**: Directly reuses the proven shape from `suggest_account_coding`
(`002`) — an AI function that narrows among deterministically-bounded
options and explains itself, never inventing a match from the full
dataset. Allowing a `null` result acknowledges that even among plausible
candidates, the AI may genuinely have no confident pick — better to say so
than to force a choice (constitution Principle II/III).
**Alternatives considered**: Always forcing the AI to pick one of the
candidates (rejected — would violate the "ask rather than guess" pattern
this project consistently applies, e.g. `parse_expense_draft`'s
`needs_clarification` path).

## Outstanding item carried to Complexity Tracking / tasks

Per Constitution Check, the workflow diagram (`docs/workflow-diagram.drawio`,
Principle V) must be updated to include the `adjudicate_match` tool and the
CSV-import/matching flow before this feature's PR merges — carried forward
as an explicit task in `tasks.md`.
