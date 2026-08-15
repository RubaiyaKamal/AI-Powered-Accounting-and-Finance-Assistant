# Phase 1 Data Model: Income Entry

Derived from the Key Entities section of `spec.md` and the storage decisions
in `research.md`. `IncomeSource` and `IncomeEntry` are new tables; the
existing `journal_entries` table (from `002-ledger-journal-entries`) is
generalized in place.

## IncomeSource

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `name` | text | not null, unique (case-insensitive) | e.g. "Sales", "Owner Investment" |
| `account_id` | FK → Account.id | not null | the Revenue- or Equity-type account this source posts to (FR-007) |
| `is_custom` | boolean | not null, default `true` | `false` only for the seeded starter sources, mirroring `Category.is_custom` |

**Seed data** (migration-time, `is_custom=false`): "Sales" → new Revenue
account `4000 Sales Revenue`; "Owner Investment" → new Equity account
`3000 Owner's Capital` (`research.md` Decision 5).

**Validation rules**:
- `account_id` must reference an `Account` whose `type` is `revenue` or
  `equity` — an income source pointing at an expense/asset/liability
  account would make every posting unbalanced in spirit even though the
  debit/credit mechanics would still run (enforced at the API layer).

**Relationships**: has many `IncomeEntry` rows; belongs to one `Account`.

## IncomeEntry

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `amount` | numeric(12,2) | not null, `> 0` | FR-002 |
| `date` | date | not null | FR-003 |
| `source_id` | FK → IncomeSource.id | not null | FR-001 |
| `description` | text, max 500 | nullable | FR-001 |
| `created_at` | timestamptz | not null, default now() | FR-010 |
| `updated_at` | timestamptz | not null, default now(), updated on every edit | FR-010 |

**Validation rules**:
- `amount` must be `> 0` (FR-002); enforced by a DB check constraint,
  mirroring `expense_entries`'s `ck_expense_entries_amount_positive`.
- `source_id` must reference an `IncomeSource` row that still exists
  (validated at the API layer, DB FK as second line of defense).

**Relationships**: belongs to one `IncomeSource`; has zero or one active
posted `JournalEntry` at a time via `journal_entries.income_entry_id`
(same one-active-posting-at-a-time shape as `ExpenseEntry` →
`AccountCoding` → `JournalEntry`, just without the intermediate coding
row — see `research.md` Decision 2).

**No field-level edit history** — explicitly out of scope for this feature
(spec Assumptions); unlike `ExpenseEntry`, there is no
`IncomeEntryEditHistory` table.

## JournalEntry (generalized — modifies the existing `002` table)

| Field | Type | Constraints | Change |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | unchanged |
| `expense_entry_id` | UUID | **now nullable**, not a DB-enforced FK | was `not null`; null when this posting originated from an income entry |
| `income_entry_id` | UUID | **new column**, nullable, not a DB-enforced FK | same audit-survival reasoning as `expense_entry_id` (must survive the source `IncomeEntry`'s deletion — FR-006); null when this posting originated from an expense entry |
| `account_coding_id` | FK → AccountCoding.id | **now nullable** | was `not null`; null when this posting originated from an income entry, since income entries have no `AccountCoding` step (`research.md` Decision 1/2) |
| `debit_account_id` | FK → Account.id | not null | unchanged — for income postings, always the Cash offset account |
| `credit_account_id` | FK → Account.id | not null | unchanged — for income postings, the `IncomeSource`'s mapped Revenue/Equity account |
| `amount` | numeric(12,2) | not null, `> 0` | unchanged; for income postings, always copied from `IncomeEntry.amount` |
| `date` | date | not null | unchanged; for income postings, copied from `IncomeEntry.date` |
| `status` | enum(`posted`, `reversed`) | not null, default `posted` | unchanged |
| `reverses_journal_entry_id` | FK → JournalEntry.id, nullable | unchanged | |
| `created_at` | timestamptz | not null, default now() | unchanged |

**New constraint**: `ck_journal_entries_exactly_one_source` — exactly one of
(`expense_entry_id`, `income_entry_id`) must be non-null. A journal entry
always traces back to exactly one source record, never both and never
neither.

**Validation rules** (in addition to the existing ones from `002`):
- For an income posting: `debit_account_id` is always the fixed Cash
  offset account (money coming in increases cash); `credit_account_id` is
  always the posting `IncomeEntry`'s `IncomeSource.account_id` (mirrors the
  expense posting's fixed roles, with debit/credit swapped — see
  `research.md` for why the direction differs).

**Relationships**: belongs to either one `ExpenseEntry` (via
`account_coding_id` → `AccountCoding`) or one `IncomeEntry` directly, never
both; references two `Account` rows (debit, credit); optionally references
another `JournalEntry` it reverses.

**State transitions**: identical to `002`'s — `posted` → `reversed`
(immutable once reversed; a new `JournalEntry` with swapped debit/credit
accounts, `reverses_journal_entry_id` set, and the same `income_entry_id`
carried over is created alongside the status change, never in place).

## Impact on existing reports (no schema/query changes)

`reporting_service.py`'s `_account_balances` groups by `debit_account_id` /
`credit_account_id` and joins to `Account.type` — it never reads
`expense_entry_id`, `income_entry_id`, or `account_coding_id`. Once income
postings exist in `journal_entries`, `profit_and_loss`'s `revenue_lines`
and `balance_sheet`'s `equity_lines` populate automatically (FR-011,
FR-012) with no changes to that file, `schemas/reports.py`, or
`api/reports.py`.
