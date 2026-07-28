# Phase 0 Research: Ledger & Journal Entries

The backend/frontend/database/AI stack is fixed by the constitution and
already established by `001-expense-entry` — no `NEEDS CLARIFICATION`
markers remain in Technical Context. This document records the feature-scoped
design decisions specific to double-entry posting, confidence-gated
automation, and correction/reversal mechanics.

## Decision: Offset account for expense-derived journal entries

**Decision**: Every journal entry posted from an expense entry debits the
coded Expense account and credits a single fixed default account, "Cash".
**Rationale**: `ExpenseEntry` (from `001-expense-entry`) does not currently
capture a payment method or source account (bank vs. accounts payable vs.
petty cash) — that data simply doesn't exist yet. A single fixed "Cash"
offset account keeps every posting mechanically balanced and correct without
inventing data the spec never asked for. This is explicitly a
YAGNI-justified simplification (constitution Principle VI): multi-account
offsets become meaningful only once expense entries can record how they were
paid, which is out of this feature's scope (spec Assumptions).
**Alternatives considered**: Prompting the AI to also guess the offset
account (rejected — no signal exists in an expense entry to base that guess
on, and it would be a second LLM-influenced ledger decision with no
corresponding spec requirement); adding a payment-method field to
`ExpenseEntry` as part of this feature (rejected — that's a change to an
already-shipped, merged feature's data model, out of proportion to this
feature's stated scope).

## Decision: Coding-suggestion trigger model

**Decision**: Coding suggestions are generated on demand via a dedicated
`POST /api/expenses/{id}/coding/suggest` call, not automatically as a side
effect of expense-entry creation.
**Rationale**: Matches User Story 1's acceptance scenario wording directly
("Given an expense entry that has not yet been coded, When the admin opens
it, Then the system shows a suggested account...") — coding is triggered by
the admin engaging with the coding flow, not baked silently into the
already-shipped `POST /api/expenses` endpoint. Keeps this feature decoupled
from `001-expense-entry`'s creation path (smaller diff, easier independent
testing per the spec's per-story "Independent Test" requirement) while still
satisfying FR-003 ("for every uncoded expense entry, the system MUST suggest
a coding") — the suggestion becomes available whenever it's requested, which
the frontend requests immediately after an entry is created or first opened.
**Alternatives considered**: Hooking coding generation directly into
`ExpenseEntryService.create_entry` (rejected — couples this feature's write
path into `001-expense-entry`'s already-tested creation logic for no
functional gain, since the UI can just as easily call `suggest` right after
create); a background job/queue that codes entries asynchronously (rejected
— unnecessary complexity at this project's scale, no requirement for
async/batch processing).

## Decision: Reversal mechanics for corrections and deletions

**Decision**: A "reversal" is itself a new `JournalEntry` row with the debit
and credit accounts swapped (same amount), referencing the entry it
reverses; the original entry is marked `status=reversed` rather than
deleted. Correcting a coding (FR-011) or deleting an already-posted expense
entry (FR-012) both create a reversal, and a correction additionally posts a
fresh journal entry for the new coding.
**Rationale**: This is standard double-entry bookkeeping practice (a
reversing entry, not a destructive edit) — it keeps the ledger's full
history intact and auditable, which directly serves SC-003 ("trace any
journal entry back to its source") and the constitution's traceability
principle. Never deleting/mutating a posted journal entry in place also
means the "debits always equal credits across the whole ledger" invariant
(SC-002) holds at every point in time, not just after corrections settle.
**Alternatives considered**: Directly updating the amounts/accounts on the
existing journal entry row in place (rejected — destroys the audit trail of
what was actually posted and when, which fails SC-003 and the spec's
explicit "the ledger stays balanced and auditable" edge-case requirement);
hard-deleting the old entry and inserting a new one (rejected — same
audit-trail loss, plus it would leave a gap that looks like the ledger was
tampered with rather than corrected).

## Decision: Confidence threshold configuration

**Decision**: A single configurable threshold (default 0.8 / 80%), read from
an environment variable (`ACCOUNT_CODING_CONFIDENCE_THRESHOLD`) via
`backend/src/config.py`, mirroring how `AGENT_MODEL` is already configured
in that file.
**Rationale**: The spec's Assumptions section explicitly calls the exact
numeric default an implementation detail, not a business-scope decision —
consistent with keeping it out of `spec.md` and resolving it here. Env-var
configuration (not hardcoded) follows the constitution's "never hardcode
... use `.env`" default policy and lets the threshold be tuned without a
code change if real usage shows 80% is miscalibrated.
**Alternatives considered**: Hardcoding 0.8 directly in `ledger_service.py`
(rejected — constitution's default policy disfavors hardcoded config values
that plausibly need tuning); a per-account configurable threshold (rejected
— no requirement for that granularity, adds complexity YAGNI would reject).

## Decision: AI integration shape for account coding

**Decision**: One new scoped tool, `suggest_account_coding(description,
existing_accounts) -> (account_name, confidence_score)`, following the exact
pattern `001-expense-entry`'s `suggest_category` tool already established.
The tool never writes to the database and never returns a monetary amount —
only an account name and a confidence score; `ledger_service` resolves the
name to an `Account` row and makes the auto-post-vs-review decision in
deterministic code based on the threshold (Decision above).
**Rationale**: Directly reuses a proven pattern from the same codebase
(`backend/src/agent/expense_tools.py::suggest_category`) rather than
inventing a new AI-integration shape; keeps the constitution's Principle II
boundary in exactly the same place it's already drawn for category
suggestion.
**Alternatives considered**: Having the LLM directly call a
`post_journal_entry` tool with computed debit/credit amounts (rejected —
this is precisely the failure mode Principle II and the user's own feature
description explicitly rule out: "the LLM only decides what to post via a
scoped tool call, never generates the ledger numbers itself").

## Outstanding item carried to Complexity Tracking / tasks

Per Constitution Check, the workflow diagram (`docs/workflow-diagram.drawio`,
Principle V) must be updated to include the new coding-suggestion and
auto-posting flow before this feature's PR merges. Carried forward as an
explicit task in `tasks.md` rather than silently skipped, matching how
`001-expense-entry` handled the diagram's first creation.
