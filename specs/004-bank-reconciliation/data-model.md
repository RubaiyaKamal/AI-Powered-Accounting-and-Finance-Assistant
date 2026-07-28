# Phase 1 Data Model: Bank/Vendor Reconciliation

Derived from the Key Entities section of `spec.md` and the storage
decisions in `research.md`. `matches.expense_entry_id` uses a real,
enforced foreign key (unlike `002-ledger-journal-entries`'s deliberately
non-enforced FKs) — see `research.md`'s Undo and Deletion decision for why
that's the correct choice here.

## BankTransaction

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `date` | date | not null | from the imported CSV row |
| `amount` | numeric(12,2) | not null | from the imported CSV row |
| `description` | text | not null | from the imported CSV row |
| `created_at` | timestamptz | not null, default now() | import time |

**Immutability**: no `updated_at` — per FR-012, a `BankTransaction` is
never edited after import. There is also no delete endpoint for it (only
`Match` rows can be removed, via undo) — a bank transaction, once
imported, is permanent source data.

**Validation rules**:
- `(date, amount, description)` together MUST be unique — enforced by a DB
  unique constraint, implementing FR-003's exact-duplicate detection at
  import time (checked before insert; a duplicate row is skipped, not
  rejected as an import failure — see `contracts/reconciliation-api.md`).

**Relationships**: has at most one `Match` row (whether `confirmed` or
`dismissed` — once either exists, the transaction is resolved, FR-009).

## Match

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `bank_transaction_id` | FK → BankTransaction.id, unique | not null | one resolution per bank transaction |
| `expense_entry_id` | FK → ExpenseEntry.id, `ON DELETE CASCADE` | nullable, unique when not null | null only when `status=dismissed`; the enforced cascade implements FR-013 for free — deleting the expense entry deletes the `Match` row, and the bank transaction's absence of a `Match` row is exactly "returned to the review queue" |
| `source` | enum(`auto`, `manual`) | not null | FR-005 vs. FR-008's manual confirm/correct |
| `status` | enum(`confirmed`, `dismissed`) | not null | `dismissed` = admin confirmed there's no corresponding expense entry (FR-008) |
| `ai_reasoning` | text | nullable | set only when this match followed AI adjudication (FR-006); null for both auto-matches (no ambiguity to explain) and manual matches |
| `created_at` | timestamptz | not null, default now() | |

**Validation rules**:
- `expense_entry_id`, when not null, must reference an `ExpenseEntry` that
  still exists (enforced by the FK itself).
- A partial unique index on `expense_entry_id` (`WHERE expense_entry_id IS
  NOT NULL`) enforces FR-010's expense-entry side of one-to-one matching;
  `bank_transaction_id`'s plain unique constraint enforces the
  bank-transaction side.

**Relationships**: belongs to exactly one `BankTransaction`; belongs to at
most one `ExpenseEntry` (null when dismissed).

**State transitions**:
1. A `BankTransaction` with no `Match` row is **unmatched** — either newly
   imported and not yet scored, or scored with no plausible candidate at
   all (straight to the review queue, no AI call — `research.md`).
2. Matching produces one of:
   - A `Match` row with `source=auto`, `status=confirmed`,
     `ai_reasoning=null` (the auto-match path, FR-005).
   - No `Match` row yet, but the transaction is flagged ambiguous with a
     recorded AI suggestion + reasoning for the review queue to display
     (FR-006) — this suggestion is *not* a `Match` row until the admin
     confirms it.
   - No `Match` row and no suggestion (no plausible candidates at all,
     FR-007).
3. From the review queue (US3), an admin resolves an unmatched transaction
   by creating a `Match` row: `source=manual`, `status=confirmed`
   (confirming the AI's suggestion or picking a different expense entry),
   or `status=dismissed`, `expense_entry_id=null` (FR-008).
4. **Undo** (FR-011) deletes a `confirmed` `Match` row outright, returning
   the `BankTransaction` to unmatched. Per FR-011's scope, undo applies to
   confirmed matches; a `dismissed` resolution is final, matching FR-009's
   "does not re-surface" guarantee.
