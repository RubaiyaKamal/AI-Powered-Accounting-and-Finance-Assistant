# Phase 1 Data Model: Analysis & Advisory / Natural-Language Q&A

No new database tables — every shape below is a read-only computation
over the existing `accounts` and `journal_entries` tables (`002`), built
entirely from `reporting_service.profit_and_loss`'s own output
(`research.md`). This document describes the **computed response
shapes**, made concrete from the Key Entities in `spec.md`.

## Spending Amount

Answers "how much did we spend on X in period Y?" (US1). One line from a
`profit_and_loss` call's `expense_lines`, filtered to the resolved
account.

| Field | Type | Notes |
|---|---|---|
| `account_code` | string | |
| `account_name` | string | |
| `start` | date | resolved period start |
| `end` | date | resolved period end |
| `amount` | decimal | `0.00` if the account had no activity in the period — distinct from "account doesn't exist" (FR-005), which is a different, non-numeric response |

## Spending Breakdown

Ranked spending across accounts for a period (US2). Directly
`profit_and_loss(start, end).expense_lines`, sorted by balance descending,
with each line's share of the period's total added.

| Field | Type | Notes |
|---|---|---|
| `start` | date | |
| `end` | date | |
| `lines` | list of `{account_code, account_name, amount, share}` | sorted highest to lowest; `share` = `amount / total` (0 when `total` is 0) |
| `total` | decimal | same value as `profit_and_loss`'s `total_expenses` for this period |

## Spending Comparison

Change in spending between two periods, overall and by account (US2).
Two `profit_and_loss` calls, merged by account.

| Field | Type | Notes |
|---|---|---|
| `period_a` | `{start, end}` | the earlier or first-named period |
| `period_b` | `{start, end}` | the later or second-named period |
| `lines` | list of `{account_code, account_name, period_a_amount, period_b_amount, change}` | includes every account with activity in *either* period (an account absent from one period contributes `0.00` for that period); `change` = `period_b_amount - period_a_amount` |
| `total_period_a` | decimal | |
| `total_period_b` | decimal | |
| `total_change` | decimal | `total_period_b - total_period_a` |

## Spending Forecast

An estimate for a future period, with its method exposed for narration
(US3). Never presented as a certain figure — `is_estimate` is always
`true`, and the response always carries enough of the historical basis
for a caller (or narrator) to explain it.

| Field | Type | Notes |
|---|---|---|
| `target_start` | date | the forecasted period's start |
| `target_end` | date | the forecasted period's end |
| `forecast_amount` | decimal | the projected total expenses for the target period |
| `is_estimate` | boolean | always `true` — never omitted, so no caller can accidentally treat this as a certain figure |
| `method` | string | a short, fixed description, e.g. `"linear trend over the last N months"` |
| `historical_points` | list of `{start, end, amount}` | the actual `profit_and_loss` totals the trend was fit to (`research.md`'s up-to-6-month window) |

**Insufficient data**: When fewer than 3 of the lookback window's months
have any posted activity (`research.md`), no `forecast_amount` is
computed; the response instead carries a `status: "insufficient_data"`
flag (in place of `forecast_amount`/`method`/`historical_points`) so the
caller can render FR-009's "not enough data yet" message rather than a
number.

## Relationships to existing entities

- Every account reference (`account_code`/`account_name`) is drawn from
  an existing `Account` row (`002`) — this feature never creates,
  modifies, or classifies an account.
- Every amount is ultimately a sum over existing `JournalEntry` rows,
  filtered to active postings exactly as `reporting_service.profit_and_loss`
  already does — this feature adds no new filtering logic of its own.
- None of the shapes above are persisted; they're computed fresh on every
  request and never cached, matching `005-reporting`'s precedent.
