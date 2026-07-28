# API Contract: Audit & Anomaly Detection

All request/response bodies are Pydantic models on the FastAPI backend.
Amounts/scores are decimal, dates are ISO-8601 (`YYYY-MM-DD`), timestamps
are ISO-8601 datetimes.

## `POST /api/audit/runs`

Trigger an audit run over a chosen date range (User Story 1). Body:
`start`, `end` — dates, both optional; if either is omitted, both default
to the entire ledger to date (earliest posted entry through today).

**Request**
```json
{ "start": "2026-07-01", "end": "2026-07-31" }
```

**Response `201`**
```json
{
  "id": "uuid",
  "start": "2026-07-01",
  "end": "2026-07-31",
  "status": "completed",
  "entries_evaluated": 42,
  "entries_flagged": 3,
  "created_at": "2026-07-28T12:00:00Z",
  "flags": [
    {
      "id": "uuid",
      "journal_entry": { "...": "same shape as GET /api/journal-entries/{id}'s response" },
      "score": "0.87",
      "reason_categories": ["unusual_amount"],
      "explanation": "This $12,000 posting to Supplies Expense is far larger than the account's typical $50-$300 range.",
      "resolution": "unreviewed",
      "resolved_at": null
    }
  ]
}
```

**Response `201` (insufficient data)**
```json
{
  "id": "uuid",
  "start": "2026-07-01",
  "end": "2026-07-31",
  "status": "insufficient_data",
  "entries_evaluated": 6,
  "entries_flagged": 0,
  "created_at": "2026-07-28T12:00:00Z",
  "flags": []
}
```

**Errors**: `422` — `end` is before `start`.

---

## `GET /api/audit/runs`

List past audit runs, most recent first (User Story 3).

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "start": "2026-07-01",
      "end": "2026-07-31",
      "status": "completed",
      "entries_evaluated": 42,
      "entries_flagged": 3,
      "created_at": "2026-07-28T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

## `GET /api/audit/runs/{id}`

Reopen a past audit run's full results (User Story 3) — same response
shape as `POST /api/audit/runs`, including each flag's current
`resolution`.

**Errors**: `404` — no run with that id.

---

## `PATCH /api/audit/flags/{id}`

Record a resolution for a flagged entry (User Story 2).

**Request**
```json
{ "resolution": "false_positive" }
```
`resolution` MUST be one of `confirmed_issue`, `false_positive`,
`no_action_needed`.

**Response `200`**
```json
{
  "id": "uuid",
  "journal_entry": { "...": "..." },
  "score": "0.87",
  "reason_categories": ["unusual_amount"],
  "explanation": "This $12,000 posting to Supplies Expense is far larger than the account's typical $50-$300 range.",
  "resolution": "false_positive",
  "resolved_at": "2026-07-28T12:05:00Z"
}
```

**Errors**: `404` — no flag with that id. `422` — `resolution` is not one
of the allowed values.

---

## `POST /api/agent/audit/query`

Ask for an audit in natural language (User Story 4). The agent resolves a
date range from the question, triggers the *exact same* deterministic
audit process `POST /api/audit/runs` uses, and returns its result — it
never decides which entries are anomalous itself (FR-002).

**Request**: `{ "question": "check this month for anything unusual" }`

**Response `200`**
```json
{
  "data": { "...": "same shape as POST /api/audit/runs's response" },
  "narrative": "I checked July 2026 and found 3 entries worth a look — one unusually large Supplies Expense posting and two that look like duplicates."
}
```
`data` is always present when a period could be resolved, and is always
numerically identical to what `POST /api/audit/runs` would return for the
same resolved range (FR-009).

**Errors**: `422` — the question could not be confidently resolved to a
date range (the agent asks a clarifying question in `narrative` instead of
guessing, per spec Edge Cases); `data` is `null` in this case.
