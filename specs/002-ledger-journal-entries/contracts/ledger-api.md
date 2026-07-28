# API Contract: Ledger & Journal Entries

All request/response bodies are Pydantic models on the FastAPI backend, per
the constitution's validation requirement. Amounts are decimal, dates are
ISO-8601 (`YYYY-MM-DD`), timestamps are ISO-8601 datetime, confidence scores
are decimals in `[0, 1]`.

## `GET /api/accounts`

List the chart of accounts (used to populate account pickers and to give the
AI coding-suggestion tool its candidate list).

**Response `200`**
```json
{ "items": [{"id": "uuid", "code": "5000", "name": "Utilities Expense", "type": "expense", "is_custom": false}] }
```

---

## `POST /api/accounts`

Add a custom account (FR-002).

**Request**
```json
{ "code": "5100", "name": "Marketing Expense", "type": "expense" }
```

**Response `201`**: same shape as a list item.
**Errors**: `409` — an account with that code or name (case-insensitive)
already exists. `422` — invalid `type`.

---

## `POST /api/expenses/{expense_id}/coding/suggest`

Generate (or regenerate) an AI account-coding suggestion for an expense
entry (User Story 1). If the resulting confidence score is at or above the
configured threshold, the coding is auto-approved **and** a journal entry is
posted in the same call (FR-004); otherwise the coding is created with
`status=pending_review` and no journal entry is posted (FR-005).

**Request**: *(no body — the expense entry's existing description/amount
drive the suggestion)*

**Response `200`**
```json
{
  "coding": {
    "id": "uuid",
    "expense_entry_id": "uuid",
    "account": {"id": "uuid", "code": "5000", "name": "Utilities Expense", "type": "expense"},
    "confidence_score": "0.92",
    "source": "ai_suggested",
    "status": "approved"
  },
  "journal_entry": {
    "id": "uuid",
    "debit_account": {"id": "uuid", "name": "Utilities Expense"},
    "credit_account": {"id": "uuid", "name": "Cash"},
    "amount": "5000.00",
    "date": "2026-07-01",
    "status": "posted"
  }
}
```
`journal_entry` is `null` when `status` is `pending_review`.

**Errors**: `404` — no such expense entry. `409` — this expense entry
already has an active (non-reversed) coding; use `PATCH
/api/expenses/{expense_id}/coding` to change it instead.

---

## `GET /api/expenses/{expense_id}/coding`

Fetch the current coding (and its posted journal entry, if any) for an
expense entry.

**Response `200`**: same shape as the `suggest` response above.
**Errors**: `404` — no coding exists yet for this expense entry (call
`suggest` first).

---

## `POST /api/expenses/{expense_id}/coding/approve`

Explicitly approve a `pending_review` coding (US1 scenario 2, for
below-threshold suggestions) — posts the journal entry.

**Response `200`**: same shape as the `suggest` response, with
`status=approved` and a non-null `journal_entry`.
**Errors**: `404` — no coding exists for this expense entry. `409` — the
coding is already `approved`.

---

## `PATCH /api/expenses/{expense_id}/coding`

Correct an entry's coding to a specific account (US1 scenario 3). Always
sets `source=user` and `status=approved`. If a `posted` journal entry
already existed for this coding, it is reversed and a new one is posted for
the corrected account in the same call (FR-011).

**Request**
```json
{ "account_id": "uuid" }
```

**Response `200`**: same shape as the `suggest` response.
**Errors**: `404` — no such expense entry, or `account_id` does not
reference an existing account (FR-015).

---

## `GET /api/journal-entries`

List posted journal entries (User Story 3). Query params: `date_from`,
`date_to`, `account_id` — all optional, combinable, and match against either
the debit or credit account when `account_id` is given (FR-009). Reversed
entries are included (for auditability) and marked with `status=reversed`.

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "expense_entry_id": "uuid",
      "debit_account": {"id": "uuid", "name": "Utilities Expense"},
      "credit_account": {"id": "uuid", "name": "Cash"},
      "amount": "5000.00",
      "date": "2026-07-01",
      "status": "posted"
    }
  ],
  "total": 1
}
```

**Errors**: `422` — `date_from` after `date_to` (mirrors the expense-entry
list contract's same validation).

---

## `GET /api/journal-entries/{id}`

Fetch a single journal entry, including its source expense entry link
(FR-010) and, if it is itself a reversal, the entry it reverses.

**Response `200`**
```json
{
  "id": "uuid",
  "expense_entry_id": "uuid",
  "debit_account": {"id": "uuid", "name": "Utilities Expense"},
  "credit_account": {"id": "uuid", "name": "Cash"},
  "amount": "5000.00",
  "date": "2026-07-01",
  "status": "reversed",
  "reverses_journal_entry_id": null
}
```

**Errors**: `404` — no such journal entry.
