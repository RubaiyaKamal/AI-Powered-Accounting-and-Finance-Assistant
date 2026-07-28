# Phase 1 Data Model: Ledger & Journal Entries

Derived from the Key Entities section of `spec.md` and the storage decisions
in `research.md`. All new tables reference the existing `expense_entries`
table from `001-expense-entry`.

## Account

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `code` | text | not null, unique | short chart-of-accounts code, e.g. `5000` |
| `name` | text | not null, unique (case-insensitive) | e.g. "Utilities Expense", "Cash" |
| `type` | enum(`asset`, `liability`, `equity`, `revenue`, `expense`) | not null | FR-001 |
| `is_custom` | boolean | not null, default `true` | `false` only for the seeded starter chart of accounts, mirroring `Category.is_custom` from `001-expense-entry` |

**Seed data** (migration-time, `is_custom=false`): one Expense-type account
per existing seeded `Category` (Utilities, Rent, Salaries, Supplies), plus a
single `Cash` Asset-type account used as the fixed credit-side offset
(`research.md`'s Offset Account decision).

**Relationships**: has many `AccountCoding` rows; has many `JournalEntry`
rows (as either the debited or credited account).

## AccountCoding

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `expense_entry_id` | UUID, unique | not null, **not a DB-enforced FK** | one active coding per expense entry (US1); intentionally not FK-constrained — see Validation rules below |
| `account_id` | FK → Account.id | not null | the coded Expense-type account |
| `confidence_score` | numeric(3,2) | nullable | `0.00`–`1.00`; null when `source=user` (no AI suggestion involved) |
| `source` | enum(`ai_suggested`, `user`) | not null | mirrors `ExpenseEntry.category_source` (FR-013) |
| `status` | enum(`approved`, `pending_review`) | not null | `pending_review` when `source=ai_suggested` and `confidence_score` is below the configured threshold (FR-005); everything else is `approved` |
| `created_at` | timestamptz | not null, default now() | |
| `updated_at` | timestamptz | not null, default now(), updated on every re-coding | |

**Validation rules**:
- `account_id` must reference an `Account` row that still exists (FR-015) —
  enforced at the API layer before write, DB foreign key as second line of
  defense.
- A `pending_review` coding cannot have an associated `posted` `JournalEntry`
  (enforced by `ledger_service`, not a DB constraint — see State
  transitions below).
- `expense_entry_id` is deliberately **not** a DB-enforced foreign key
  (caught and corrected during implementation): FR-012 requires that
  deleting an expense entry with posted history reverses the journal entry
  rather than being blocked or silently destroying that history. A
  RESTRICT-style FK would block the delete; a CASCADE FK would destroy the
  coding/journal audit trail FR-012 explicitly requires to survive. The
  `expense_entry_id` value is validated to reference a real, existing
  `ExpenseEntry` only at creation time (`suggest_coding`), the one point
  where it must be live.

**Relationships**: belongs to exactly one `ExpenseEntry`; belongs to one
`Account`; has zero or more `JournalEntry` rows over its lifetime (one
`posted` at a time, plus any `reversed` history from prior corrections).

**State transitions**:
1. Created via `POST /api/expenses/{id}/coding/suggest` → `status` is
   `approved` (confidence ≥ threshold, auto-posts immediately — FR-004) or
   `pending_review` (below threshold — FR-005).
2. `pending_review` → `approved` via `POST /api/expenses/{id}/coding/approve`
   (US1 scenario 2) — posts a `JournalEntry`.
3. `approved` or `pending_review` → `approved` (different `account_id`,
   `source` forced to `user`) via `PATCH /api/expenses/{id}/coding` (US1
   scenario 3) — if a `posted` `JournalEntry` already existed, it is
   reversed and a new one is posted for the corrected account (FR-011).

## JournalEntry

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `expense_entry_id` | UUID | not null, **not a DB-enforced FK** | source entry (FR-010); same audit-survival reasoning as `AccountCoding.expense_entry_id` above |
| `account_coding_id` | FK → AccountCoding.id | not null | the coding this posting was generated from — safe to enforce, since `AccountCoding` rows are never deleted by this feature |
| `debit_account_id` | FK → Account.id | not null | the coded Expense account (US2 scenario 1) |
| `credit_account_id` | FK → Account.id | not null | the fixed offset account (`research.md`) |
| `amount` | numeric(12,2) | not null, `> 0` | always copied from `ExpenseEntry.amount`, never AI-generated (FR-007) |
| `date` | date | not null | copied from `ExpenseEntry.date` at posting time |
| `status` | enum(`posted`, `reversed`) | not null, default `posted` | FR-011, FR-012 |
| `reverses_journal_entry_id` | FK → JournalEntry.id, nullable, self-referencing | nullable | set only on the reversing entry itself, pointing back at the entry it reverses |
| `created_at` | timestamptz | not null, default now() | |

**Validation rules**:
- `debit_account_id` and `credit_account_id` MUST NOT be equal (a journal
  entry that debits and credits the same account is never valid).
- The system MUST refuse to construct a `JournalEntry` if the computed debit
  amount and credit amount are not equal (FR-008) — since both lines always
  carry the same `amount` value by construction here, this is enforced by
  the service layer never accepting two different amounts for the two legs,
  not by a runtime balance check on unequal columns.
- `debit_account_id` and `credit_account_id` must reference `Account` rows
  that still exist (FR-015).

**Relationships**: belongs to one `ExpenseEntry`; belongs to one
`AccountCoding`; references two `Account` rows (debit, credit); optionally
references another `JournalEntry` it reverses.

**State transitions**: `posted` → `reversed` (immutable once reversed; a new
`JournalEntry` with swapped debit/credit accounts and
`reverses_journal_entry_id` set is created alongside the status change,
never in place — `research.md`'s Reversal Mechanics decision). A `reversed`
entry never transitions further.
