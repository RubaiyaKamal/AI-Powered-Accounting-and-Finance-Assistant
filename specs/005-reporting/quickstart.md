# Quickstart: Financial Reporting

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up`, and that at least one expense entry has
already been recorded, coded, and posted to the ledger (via the
`001-expense-entry` and `002-ledger-journal-entries` features) — e.g., a
$45.00 Utilities expense dated within the current calendar month.

1. **Trial Balance (US1)**: `GET /api/reports/trial-balance` (no `as_of`,
   defaults to today). Confirm the Utilities Expense and Cash accounts both
   appear with the expected balances, and `total_debits == total_credits`
   (`is_balanced: true`).
2. **Profit & Loss (US2)**: `GET /api/reports/profit-and-loss` (no
   `start`/`end`, defaults to the current calendar month). Confirm
   `total_expenses` matches the $45.00 posting, `total_revenue` is `0.00`
   (no income-entry feature yet — spec Assumptions), and `net_profit` is
   `-45.00`.
3. **Balance Sheet (US3)**: `GET /api/reports/balance-sheet` (no `as_of`,
   defaults to today). Confirm the Cash account appears under
   `asset_lines` with the expected balance.
4. **Cash Flow (US4)**: `GET /api/reports/cash-flow` (current month).
   Confirm `net_change` equals `closing_balance - opening_balance` and
   matches the $45.00 posting's effect on Cash.
5. **Reversed-entry edge case**: Correct the expense entry's account coding
   (triggering `002`'s automatic reverse-and-repost). Re-run the Trial
   Balance from step 1 and confirm the old account's balance returns to
   zero and the new account shows the $45.00 instead — the reversed entry
   and its reversal must not leave any residual balance on the old account
   (FR-006).
6. **No-data edge case**: `GET /api/reports/profit-and-loss?start=2020-01-01&end=2020-01-31`
   (a period with no activity). Confirm a valid zero-value response
   (`total_revenue: "0.00"`, `total_expenses: "0.00"`, `net_profit: "0.00"`),
   not an error (FR-008).
7. **Natural-language query (FR-007)**: `POST /api/agent/reports/query`
   with `{"question": "how did we do this month?"}`. Confirm the response's
   `report_type` is `"profit_and_loss"`, its `data` is numerically identical
   to step 2's response, and `narrative` describes those same figures in
   prose without introducing any new number.
8. **Ambiguous query edge case**: `POST /api/agent/reports/query` with
   `{"question": "show me the numbers"}` (no report type or period
   determinable). Confirm the response asks a clarifying question in
   `narrative` rather than guessing a report and fabricating figures.

If all eight steps behave as described, the feature satisfies its
acceptance scenarios end to end.
