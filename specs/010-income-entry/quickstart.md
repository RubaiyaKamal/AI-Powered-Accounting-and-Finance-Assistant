# Quickstart: Income Entry

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up` (frontend, backend, PostgreSQL) and that
migrations have applied the starter income sources ("Sales" → Sales Revenue,
"Owner Investment" → Owner's Capital).

1. **Record income (US1)**: Open the income entry form. Enter a positive
   amount, a date, and pick "Owner Investment" as the source. Submit.
   Confirm the entry appears in the income list and that
   `GET /api/journal-entries` now shows a posted entry debiting Cash and
   crediting "Owner's Capital" for that amount — no separate approval step
   (FR-008).
2. **Reject invalid entries (US1)**: Submit the form with a zero or
   negative amount — confirm it's rejected with a clear message and no
   entry is saved. Submit with the date blank — confirm the same.
3. **Edit an income entry (US2)**: Change a saved entry's amount. Confirm
   the entry reflects the new amount, the old journal entry is reversed,
   and a new one is posted for the corrected amount (mirrors
   `002-ledger-journal-entries`'s coding-correction behavior).
4. **Delete an income entry (US2)**: Delete a saved entry. Confirm it no
   longer appears in the income list, and its journal entry is now
   `reversed`, not gone — the ledger still shows both entries.
5. **Filter income entries (US2)**: With several entries recorded across
   different dates/sources, filter by date range and confirm only matching
   entries show; filter by an end date before the start date and confirm a
   clear rejection rather than an empty/misleading result.
6. **See it in the reports (US3)**: Record one "Owner Investment" entry and
   one "Sales" entry, plus (from `001-expense-entry`) at least one expense
   entry with a posted journal entry. Open the income statement
   (`GET /api/reports/profit-and-loss`) and confirm the "Sales" entry
   appears in `revenue_lines` and `net_profit` reflects revenue minus
   expenses. Open the balance sheet (`GET /api/reports/balance-sheet`) and
   confirm `total_assets == total_liabilities + total_equity`
   (`is_balanced: true`) — this is SC-005, the reason this feature exists.

## Demo data walkthrough (all amounts $5.50)

To see the reports populated end-to-end through the running app (not a DB
seed script — exercises the real create/post path for both entry types):

1. `POST /api/income` three times with `amount: "5.50"`, `source_id` =
   "Owner Investment"'s id, dates spread across the current month.
2. `POST /api/income` three times with `amount: "5.50"`, `source_id` =
   "Sales"'s id, dates spread across the current month.
3. For each starter expense category ("Utilities", "Rent", "Salaries",
   "Supplies"), `POST /api/expenses` with `amount: "5.50"` and that
   category, then `POST /api/expenses/{id}/coding/suggest` to post it to
   the ledger (per `002-ledger-journal-entries`'s quickstart).
4. Open `/reports` in the frontend (or call the two report endpoints
   directly): the income statement shows revenue = $16.50 (3 × $5.50
   Sales), expenses = $22.00 (4 × $5.50), net loss = -$5.50; the balance
   sheet shows Cash = $16.50 (3 × $5.50 Owner Investment + 3 × $5.50 Sales
   − 4 × $5.50 expenses), Sales Revenue = $16.50 credit, Owner's Capital =
   $16.50 credit, and total assets ($16.50) equals total liabilities + total
   equity ($0 + $16.50 − $5.50 net-loss-to-equity)... **note**: this
   project's `balance_sheet` computes `total_equity` from posted Equity-type
   account balances only (it does not roll net income into equity
   automatically, since there's no closing-entry step in scope) — so with
   these exact numbers the sheet balances as
   `assets ($16.50) == liabilities ($0) + equity ($16.50)`, matching
   SC-005, while the income statement separately reports the period's
   $5.50 net loss. Both are correct, independent views of the same ledger.

If all six quickstart steps behave as described, the feature satisfies its
acceptance scenarios end to end.
