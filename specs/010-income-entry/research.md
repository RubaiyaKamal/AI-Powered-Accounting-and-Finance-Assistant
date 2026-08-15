# Phase 0 Research: Income Entry

## Decision 1: How to let `journal_entries` represent an income posting

**Decision**: Generalize the existing `journal_entries` table rather than
create a parallel `income_journal_entries` table. Make `expense_entry_id`
and `account_coding_id` nullable, add a new nullable `income_entry_id`
column (not a DB-enforced FK, same rationale as `expense_entry_id`: a
journal entry must survive its source entry's deletion for audit purposes),
and add a check constraint requiring exactly one of
(`expense_entry_id`, `income_entry_id`) to be set.

**Rationale**: `reporting_service.py` (income statement, balance sheet,
trial balance, cash flow) queries `journal_entries` + `accounts` only — it
never touches `expense_entry_id` or `account_coding_id`. A single unified
table means all four existing reports pick up income data with **zero
reporting-layer changes**, which is the entire point of this feature
(unblocking reports that already exist). A parallel table would require
either a UNION in every report query or duplicating `reporting_service.py`
logic — both violate Principle VI (Simplicity).

**Alternatives considered**:
- *Parallel `income_journal_entries` table*: rejected — forces
  `reporting_service.py` to query two tables and merge results, the exact
  duplication Principle VI warns against, for a feature whose stated goal
  is to reuse the existing reports unmodified.
- *Reuse `account_codings` for income too* (treat an income entry as if it
  were an expense entry for coding purposes): rejected — `account_codings`
  has a NOT NULL unique `expense_entry_id`, and repurposing that column to
  sometimes hold an income entry's id is misleading schema abuse; income
  entries also don't need a coding *suggestion* step at all (spec: no AI),
  so the whole `AccountCoding` concept (confidence score, suggested/
  approved/pending_review status) doesn't apply — it would carry meaning
  that's always fixed/unused for income.

## Decision 2: How an income entry picks which account to credit

**Decision**: New `income_sources` table, each row holding a direct FK to
one `accounts` row (`account_id`, NOT NULL). Creating an income entry means
picking a source; the source's `account_id` is where the credit posts. No
per-entry account-coding/approval step.

**Rationale**: The spec explicitly excludes AI category suggestion for this
feature — the source-to-account mapping is decided once, at source-creation
time (mirrors the starter chart-of-accounts pattern in
`002-ledger-journal-entries`'s migration, which mapped one starter category
to one starter expense account 1:1). This keeps entry creation a single
deterministic step: no confidence score, no pending/approved state machine
— matches FR-008's "immediately produce a corresponding ledger effect...
without requiring a separate review or approval step."

**Alternatives considered**:
- *Reuse `categories` table for income sources too*: rejected — categories
  are conceptually expense-specific in this codebase (an admin picking
  "Utilities" as an income source would be nonsensical), and categories
  have no account mapping at all today; conflating the two would require
  adding account-mapping fields to a table other features already depend on
  for expense-only behavior.
- *Free-text source string on `income_entries`, resolved to an account by
  name lookup at post time*: rejected — no validation that the string maps
  to a real account, and no way to list "the sources you can pick from" in
  the UI without inventing that list somewhere else anyway.

## Decision 3: Distinguishing operating revenue from capital funding

**Decision**: The account an `income_source` points to simply has
`type = "revenue"` or `type = "equity"` (both already valid `Account.type`
values per the existing `AccountType` literal in `schemas/account.py`).
`reporting_service.balance_sheet` and `.profit_and_loss` already branch on
`account_type` this way for every other account type — no new branching
logic needed.

**Rationale**: The existing reporting code already has the exact
`revenue`/`equity` split built in (`profit_and_loss` filters
`account_type == "revenue"`; `balance_sheet` filters `account_type ==
"equity"`). Reusing it rather than inventing a parallel
"operating vs. non-operating" flag on `income_entries` is the smallest
viable change (Principle VI).

**Alternatives considered**:
- *Add an `is_operating` boolean to `income_entries`*: rejected — redundant
  with the mapped account's `type`, which already carries this distinction
  through to every report.

## Decision 4: Edit/delete reversal strategy

**Decision**: Mirror `002-ledger-journal-entries`'s expense-correction
pattern exactly. On update, if `amount`, `date`, or `source_id` changed,
reverse the entry's current active journal entry (if any) and post a new
one with the corrected values; a `description`-only edit does not touch
the ledger. On delete, reverse the active journal entry, then delete the
`income_entries` row. `ledger_service.reverse_journal_entry` is reused
as-is (generalized to also copy `income_entry_id` when present) rather than
writing a second reversal function.

**Rationale**: This is the same integrity requirement FR-012 already
established for expense entries (`reverse_journal_entry_for_expense`,
called from `DELETE /api/expenses/{id}`) — reusing the identical mechanism
for income avoids inventing a second reversal semantics for what is
structurally the same problem.

**Alternatives considered**:
- *In-place mutation of the existing journal entry's amount*: rejected —
  breaks the audit trail `journal_entries` is designed to preserve (every
  correction must be visible as a reversal + new posting, not a silent
  overwrite); this is also how `002` already treats expense corrections.

## Decision 5: Starter income sources / accounts to seed

**Decision**: Seed exactly two starter income sources in the generalizing
migration, mirroring the four starter expense accounts `002` seeded:

| Source name | Account code | Account name | Account type |
|---|---|---|---|
| Sales | 4000 | Sales Revenue | revenue |
| Owner Investment | 3000 | Owner's Capital | equity |

**Rationale**: FR-007 requires "at least one operating-revenue source... and
one non-operating, capital-funding source" — this is the minimum that
satisfies it while giving SC-005 (a balance sheet that actually balances) a
real funding source to demo against, without inventing a larger chart of
accounts than the feature needs.

**Alternatives considered**:
- *No capital/equity starter source, only Sales*: rejected — would leave
  the balance-sheet-balances success criterion (SC-005) untestable, since
  every dollar of cash would still trace back only to revenue net of
  expenses, never an actual opening contribution.
