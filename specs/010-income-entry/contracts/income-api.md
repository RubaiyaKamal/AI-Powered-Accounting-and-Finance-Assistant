# API Contract: Income Entry

All request/response bodies are Pydantic models on the FastAPI backend, per
the constitution's validation requirement. Amounts are decimal, dates are
ISO-8601 (`YYYY-MM-DD`), timestamps are ISO-8601 datetime.

## `GET /api/income-sources`

List income sources (used to populate the source picker on the income
entry form).

**Response `200`**
```json
{ "items": [
  {"id": "uuid", "name": "Sales", "account": {"id": "uuid", "code": "4000", "name": "Sales Revenue", "type": "revenue"}, "is_custom": false},
  {"id": "uuid", "name": "Owner Investment", "account": {"id": "uuid", "code": "3000", "name": "Owner's Capital", "type": "equity"}, "is_custom": false}
] }
```

---

## `POST /api/income-sources`

Add a custom income source (FR-007). Creates a new `revenue`- or
`equity`-type account for it in the same call — the admin doesn't manage
accounts directly for this feature, only sources.

**Request**
```json
{ "name": "Consulting Fees", "account_type": "revenue" }
```

**Response `201`**: same shape as a list item, with `is_custom: true` and a
freshly created account (auto-assigned next available code in the
account's type range: `4xxx` for `revenue`, `3xxx` for `equity`).
**Errors**: `409` — a source with that name already exists. `422` —
`account_type` is not `revenue` or `equity`.

---

## `POST /api/income`

Record a new income entry (User Story 1). Posts the corresponding journal
entry (debit Cash / credit the source's account) in the same call — no
separate approval step (FR-008).

**Request**
```json
{ "amount": "1200.00", "date": "2026-08-01", "source_id": "uuid", "description": "August retainer" }
```

**Response `201`**
```json
{
  "id": "uuid",
  "amount": "1200.00",
  "date": "2026-08-01",
  "source": {"id": "uuid", "name": "Sales", "account": {"id": "uuid", "code": "4000", "name": "Sales Revenue", "type": "revenue"}},
  "description": "August retainer",
  "created_at": "2026-08-01T10:00:00Z",
  "updated_at": "2026-08-01T10:00:00Z"
}
```
**Errors**: `422` — `amount` is zero/negative, `date`/`amount` missing, or
`source_id` does not reference an existing income source.

---

## `GET /api/income`

List income entries (User Story 2). Query params: `date_from`, `date_to`,
`source_id` — all optional, combinable.

**Response `200`**
```json
{ "items": [ /* same shape as the create response, one per entry */ ], "total": 1 }
```
**Errors**: `422` — `date_from` after `date_to` (mirrors the expense-entry
and journal-entry list contracts' same validation).

---

## `GET /api/income/{id}`

Fetch a single income entry.

**Response `200`**: same shape as the create response.
**Errors**: `404` — no such income entry.

---

## `PATCH /api/income/{id}`

Edit an existing income entry (US2 scenario 2). If `amount`, `date`, or
`source_id` changes, the entry's active journal entry is reversed and a
new one is posted for the corrected values in the same call; a
`description`-only edit does not touch the ledger.

**Request** *(all fields optional; only provided fields are changed)*
```json
{ "amount": "1500.00" }
```

**Response `200`**: same shape as the create response, reflecting the new
values.
**Errors**: `404` — no such income entry. `422` — `amount` is
zero/negative, or `source_id` does not reference an existing income
source.

---

## `DELETE /api/income/{id}`

Delete an income entry (US2 scenario 3). Reverses its active journal entry
in the same call before deleting the row.

**Response `204`**: no body.
**Errors**: `404` — no such income entry.

---

## Existing endpoints affected (no request/response shape change, behavior only)

- `GET /api/journal-entries` and `GET /api/journal-entries/{id}` (from
  `002-ledger-journal-entries`) now also return journal entries whose
  `expense_entry_id` is `null` and whose (new) `income_entry_id` is set —
  see `data-model.md`'s `JournalEntry` generalization. The response schema
  gains `income_entry_id` alongside the now-nullable `expense_entry_id`.
- `GET /api/reports/profit-and-loss` and `GET /api/reports/balance-sheet`
  (from `005-reporting`) are functionally unchanged (no code edits) but
  their `revenue_lines` / `equity_lines` now populate once income entries
  exist — this is the feature's actual goal (FR-011, FR-012).
