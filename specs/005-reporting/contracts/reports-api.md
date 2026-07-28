# API Contract: Financial Reporting

All request/response bodies are Pydantic models on the FastAPI backend.
Amounts are decimal, dates are ISO-8601 (`YYYY-MM-DD`). All four direct
endpoints are read-only (`GET`) — none of them write to the database.

## `GET /api/reports/trial-balance`

Point-in-time trial balance (User Story 1). Query params: `as_of` — date,
optional, defaults to today.

**Response `200`**
```json
{
  "as_of": "2026-07-28",
  "lines": [
    {"account_id": "uuid", "account_code": "1000", "account_name": "Cash", "account_type": "asset", "debit_total": "0.00", "credit_total": "1240.50", "balance": "-1240.50"},
    {"account_id": "uuid", "account_code": "5100", "account_name": "Utilities Expense", "account_type": "expense", "debit_total": "1240.50", "credit_total": "0.00", "balance": "1240.50"}
  ],
  "total_debits": "1240.50",
  "total_credits": "1240.50",
  "is_balanced": true
}
```

---

## `GET /api/reports/profit-and-loss`

Profit & Loss for a period (User Story 2). Query params: `start`, `end` —
dates, both optional; if either is omitted, both default to the current
calendar month.

**Response `200`**
```json
{
  "start": "2026-07-01",
  "end": "2026-07-31",
  "revenue_lines": [],
  "total_revenue": "0.00",
  "expense_lines": [
    {"account_id": "uuid", "account_code": "5100", "account_name": "Utilities Expense", "account_type": "expense", "debit_total": "1240.50", "credit_total": "0.00", "balance": "1240.50"}
  ],
  "total_expenses": "1240.50",
  "net_profit": "-1240.50"
}
```

**Errors**: `422` — `end` is before `start`.

---

## `GET /api/reports/balance-sheet`

Point-in-time balance sheet (User Story 3). Query params: `as_of` — date,
optional, defaults to today.

**Response `200`**
```json
{
  "as_of": "2026-07-28",
  "asset_lines": [
    {"account_id": "uuid", "account_code": "1000", "account_name": "Cash", "account_type": "asset", "debit_total": "0.00", "credit_total": "1240.50", "balance": "-1240.50"}
  ],
  "total_assets": "-1240.50",
  "liability_lines": [],
  "total_liabilities": "0.00",
  "equity_lines": [],
  "total_equity": "0.00",
  "is_balanced": false
}
```
`is_balanced` is `false` here only to illustrate the field's shape with the
seeded chart of accounts (no Equity account exists yet to absorb the
period's net loss) — see spec Edge Cases: the report still renders in
full, with the discrepancy visibly flagged, rather than hiding or erroring.

**Errors**: none — always returns a statement (possibly `is_balanced: false`,
per spec Edge Cases; never a 4xx/5xx for a normal request).

---

## `GET /api/reports/cash-flow`

Cash flow for a period (User Story 4). Query params: `start`, `end` —
dates, both optional; if either is omitted, both default to the current
calendar month.

**Response `200`**
```json
{
  "start": "2026-07-01",
  "end": "2026-07-31",
  "opening_balance": "0.00",
  "closing_balance": "-1240.50",
  "net_change": "-1240.50"
}
```

**Errors**: `422` — `end` is before `start`.

---

## `POST /api/agent/reports/query`

Ask for a report in natural language (FR-007's chat path). The agent
resolves report type and date/range from the question, calls the *exact
same* deterministic calculation the corresponding direct endpoint above
uses, and narrates the result — it never computes or states a figure
itself (FR-001).

**Request**: `{ "question": "how did we do last month?" }`

**Response `200`**
```json
{
  "report_type": "profit_and_loss",
  "data": { "...": "same shape as GET /api/reports/profit-and-loss's response" },
  "narrative": "For June 2026, the business recorded no revenue and $1,240.50 in expenses, mostly Utilities, for a net loss of $1,240.50."
}
```
`data` is always present and always numerically identical to what the
matching direct `GET` endpoint would return for the same resolved report
type and period (FR-007) — `narrative` is the only LLM-generated text in
the response; every number inside it is copied from `data`, never
independently produced.

**Errors**: `422` — the question could not be confidently resolved to one
of the four report types or a date/period (the agent asks a clarifying
question in `narrative` instead of guessing, per spec Edge Cases); `data`
is `null` in this case.
