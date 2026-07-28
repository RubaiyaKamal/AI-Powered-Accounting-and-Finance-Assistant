# Phase 1 Data Model: Financial Reporting

No new database tables. Every report is a read-only computation over the
`accounts` and `journal_entries` tables already created by
`002-ledger-journal-entries` (see that feature's `data-model.md` for their
schema). This document describes the **computed response shapes** each
report produces — the Key Entities from `spec.md`, made concrete — and the
one shared query rule (`research.md`'s "active postings only" decision)
every one of them applies.

## Shared building block: `AccountBalance`

Every report is built from the same per-account aggregation:

| Field | Type | Notes |
|---|---|---|
| `account_id` | UUID | |
| `account_code` | string | |
| `account_name` | string | |
| `account_type` | enum(`asset`, `liability`, `equity`, `revenue`, `expense`) | drives which report section the account belongs to (FR-010) |
| `debit_total` | decimal | sum of `journal_entries.amount` where this account is the `debit_account_id`, filtered to active postings (`research.md`) and, for period reports, to the date range |
| `credit_total` | decimal | same, where this account is the `credit_account_id` |
| `balance` | decimal | `debit_total - credit_total` for debit-normal types (`asset`, `expense`); `credit_total - debit_total` for credit-normal types (`liability`, `equity`, `revenue`) |

**Filter applied in every query**: `status = 'posted' AND reverses_journal_entry_id IS NULL`
(`research.md`'s "active postings only" decision) — this is what makes
FR-006 (reversed entries never distort a balance) true by construction,
not by post-processing.

## Trial Balance

Point-in-time (`as_of` date, defaults to today — `research.md`), cumulative
from inception through `as_of`.

| Field | Type | Notes |
|---|---|---|
| `as_of` | date | |
| `lines` | list of `AccountBalance` | every account with a non-zero balance as of `as_of`; zero-balance accounts are omitted |
| `total_debits` | decimal | sum of `debit_total` across `lines` |
| `total_credits` | decimal | sum of `credit_total` across `lines` |
| `is_balanced` | boolean | `total_debits == total_credits` — FR-002, FR-009's internal consistency check |

## Profit & Loss Statement

Period-based (`start`/`end`, defaults to the current calendar month —
`research.md`), only entries dated within `[start, end]`.

| Field | Type | Notes |
|---|---|---|
| `start` | date | |
| `end` | date | |
| `revenue_lines` | list of `AccountBalance` | accounts of type `revenue` with activity in the period |
| `total_revenue` | decimal | sum of `revenue_lines[].balance` |
| `expense_lines` | list of `AccountBalance` | accounts of type `expense` with activity in the period |
| `total_expenses` | decimal | sum of `expense_lines[].balance` |
| `net_profit` | decimal | `total_revenue - total_expenses` (may be negative — a net loss) — FR-003 |

## Balance Sheet

Point-in-time (`as_of` date, defaults to today), cumulative from inception
through `as_of` — same accumulation window as the Trial Balance, but
grouped into the three balance-sheet sections instead of one flat list.

| Field | Type | Notes |
|---|---|---|
| `as_of` | date | |
| `asset_lines` | list of `AccountBalance` | accounts of type `asset` |
| `total_assets` | decimal | sum of `asset_lines[].balance` |
| `liability_lines` | list of `AccountBalance` | accounts of type `liability` |
| `total_liabilities` | decimal | sum of `liability_lines[].balance` |
| `equity_lines` | list of `AccountBalance` | accounts of type `equity` |
| `total_equity` | decimal | sum of `equity_lines[].balance` |
| `is_balanced` | boolean | `total_assets == total_liabilities + total_equity` — FR-004, FR-009 |

## Cash Flow Statement

Period-based (`start`/`end`, defaults to the current calendar month),
scoped to the single `Cash` account (`research.md`'s single-account
assumption — the system has one designated cash/offset account today).

| Field | Type | Notes |
|---|---|---|
| `start` | date | |
| `end` | date | |
| `opening_balance` | decimal | the Cash account's balance as of the day before `start` (i.e., the Trial Balance's cash line as of `start - 1 day`) |
| `closing_balance` | decimal | the Cash account's balance as of `end` |
| `net_change` | decimal | `closing_balance - opening_balance` — MUST equal the sum of Cash-account activity within `[start, end]` (FR-005's reconciliation guarantee) |

## Relationships to existing entities

- Every `AccountBalance.account_id` references an existing `Account` row
  (`002`) — reports never create, modify, or delete an `Account`.
- Every aggregated total is a sum over existing `JournalEntry` rows (`002`)
  — reports never create, modify, or delete a `JournalEntry`.
- None of the four report shapes above are persisted; they are computed
  fresh on every request (`reporting_service.py`, Phase 1 contracts) and
  never cached, so a report always reflects the current state of the
  ledger.
