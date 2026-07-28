# API Contract: Analysis & Advisory / Natural-Language Q&A

All request/response bodies are Pydantic models on the FastAPI backend.
Amounts are decimal, dates are ISO-8601 (`YYYY-MM-DD`).

## `GET /api/analysis/breakdown`

Ranked spending across accounts for a period (User Story 2). Query
params: `start`, `end` — dates, both optional; if either is omitted, both
default to the current calendar month.

**Response `200`**
```json
{
  "start": "2026-07-01",
  "end": "2026-07-31",
  "lines": [
    { "account_code": "5020", "account_name": "Salaries Expense", "amount": "120000.00", "share": "0.892" },
    { "account_code": "5000", "account_name": "Utilities Expense", "amount": "6250.00", "share": "0.046" }
  ],
  "total": "134497.50"
}
```

**Errors**: none — always returns a valid breakdown (possibly `lines: []`,
`total: "0.00"` for a period with no activity — FR-003/spec Edge Cases).

---

## `GET /api/analysis/comparison`

Change in spending between two periods (User Story 2). Query params:
`period_a_start`, `period_a_end`, `period_b_start`, `period_b_end` — all
required dates.

**Response `200`**
```json
{
  "period_a": { "start": "2026-06-01", "end": "2026-06-30" },
  "period_b": { "start": "2026-07-01", "end": "2026-07-31" },
  "lines": [
    { "account_code": "5000", "account_name": "Utilities Expense", "period_a_amount": "250.00", "period_b_amount": "6250.00", "change": "6000.00" }
  ],
  "total_period_a": "250.00",
  "total_period_b": "134497.50",
  "total_change": "134247.50"
}
```

**Errors**: `422` — `period_a_end` before `period_a_start`, or
`period_b_end` before `period_b_start`.

---

## `GET /api/analysis/forecast`

A spending estimate for a future period (User Story 3). Query params:
`target_start`, `target_end` — required dates naming the period to
forecast.

**Response `200`**
```json
{
  "status": "completed",
  "target_start": "2026-08-01",
  "target_end": "2026-08-31",
  "forecast_amount": "141000.00",
  "is_estimate": true,
  "method": "linear trend over the last 4 months",
  "historical_points": [
    { "start": "2026-04-01", "end": "2026-04-30", "amount": "128000.00" },
    { "start": "2026-05-01", "end": "2026-05-30", "amount": "131000.00" },
    { "start": "2026-06-01", "end": "2026-06-30", "amount": "133000.00" },
    { "start": "2026-07-01", "end": "2026-07-31", "amount": "134497.50" }
  ]
}
```

**Response `200` (insufficient data)**
```json
{
  "status": "insufficient_data",
  "target_start": "2026-08-01",
  "target_end": "2026-08-31",
  "forecast_amount": null,
  "is_estimate": true,
  "method": null,
  "historical_points": []
}
```

**Errors**: `422` — `target_end` before `target_start`.

---

## `POST /api/agent/analysis/query`

Ask a spending question in natural language (User Stories 1 and 4). The
agent resolves the question into one of the four supported request kinds
and its parameters, calls the *exact same* deterministic computation the
matching direct endpoint (or, for `amount`, the same computation
underlying a breakdown line) uses, then narrates the result — it never
computes or states a figure itself (FR-002).

**Request**: `{ "question": "how much did we spend on utilities in March?" }`

**Response `200`**
```json
{
  "request_kind": "amount",
  "data": { "...": "shape depends on request_kind — SpendingAmount, SpendingBreakdown, SpendingComparison, or SpendingForecast" },
  "narrative": "In March 2026, you spent $250.00 on Utilities Expense."
}
```
`data` is always numerically identical to what the matching direct
endpoint (where one exists) would return for the same resolved
parameters (FR-010) — `narrative` is the only LLM-generated text; every
number inside it is copied from `data`, never independently produced.

**Errors**: `422` — the question could not be confidently matched to one
of the four supported request kinds, or (for an `amount`-kind question)
no real account could be matched to what was asked about, or a period
could not be determined where one is required; the agent asks a
clarifying question in `narrative` instead of guessing (per spec Edge
Cases); `request_kind` and `data` are `null` in this case.
