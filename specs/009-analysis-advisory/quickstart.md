# Quickstart: Analysis & Advisory / Natural-Language Q&A

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up`, and that posted expense activity
already exists across several accounts and, ideally, several past months
(via `001`/`002`), to exercise breakdown, comparison, and forecasting
meaningfully.

1. **Breakdown for an active period (US2)**: `GET /api/analysis/breakdown`
   for a period with posted expense activity across several accounts.
   Confirm every account with activity appears, ranked highest to lowest,
   and that the totals match `GET /api/reports/profit-and-loss`'s
   `expense_lines`/`total_expenses` for the same period.
2. **Breakdown for an empty period (edge case)**: `GET
   /api/analysis/breakdown` for a period with no posted activity. Confirm
   `lines: []` and `total: "0.00"`, not an error.
3. **Comparison between two periods (US2)**: `GET /api/analysis/comparison`
   for two periods with different activity. Confirm `total_change` equals
   `total_period_b - total_period_a`, and that an account active in only
   one period still appears with `0.00` for the other.
4. **Invalid comparison range (edge case)**: `GET /api/analysis/comparison`
   with `period_a_end` before `period_a_start`. Confirm `422`.
5. **Forecast with sufficient history (US3)**: Ensure posted expense
   activity exists across at least 3 past calendar months, then `GET
   /api/analysis/forecast` for the next period. Confirm `status:
   "completed"`, a `forecast_amount`, a `method` description, and
   `historical_points` reflecting the actual past months' totals.
6. **Forecast with insufficient history (edge case)**: On a ledger with
   fewer than 3 months of posted activity (or a business only weeks old),
   request a forecast. Confirm `status: "insufficient_data"` and no
   fabricated `forecast_amount`.
7. **Natural-language amount question (US1)**: `POST
   /api/agent/analysis/query` with `{"question": "how much did we spend
   on utilities in March?"}` (adjust the month to one with seeded
   Utilities activity). Confirm `request_kind: "amount"` and `data.amount`
   matches that account's line in a direct breakdown for the same period.
8. **Unknown account (edge case)**: `POST /api/agent/analysis/query` with
   a question naming an account/category that doesn't exist in the chart
   of accounts (e.g., "how much did we spend on advertising?" where no
   such account exists). Confirm the response clearly states no matching
   account was found rather than a zero or fabricated figure.
9. **Ambiguous question (edge case)**: `POST /api/agent/analysis/query`
   with `{"question": "how are we doing"}` (no determinable request kind).
   Confirm `422` with a clarifying question in `narrative`.
10. **Natural-language breakdown/forecast question (US4)**: `POST
    /api/agent/analysis/query` with `{"question": "what are we spending
    the most on this month?"}`. Confirm `request_kind: "breakdown"` and
    `data` matches a direct `GET /api/analysis/breakdown` for the current
    month. Repeat with a forecast-style question (e.g., "what will we
    likely spend next month?") and confirm `request_kind: "forecast"`
    with data matching a direct forecast request for the same period.

If all ten steps behave as described, the feature satisfies its
acceptance scenarios end to end.
