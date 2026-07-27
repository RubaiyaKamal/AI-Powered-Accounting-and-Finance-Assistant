# API Contract: Expense Entry

All request/response bodies are Pydantic models on the FastAPI backend, per
the constitution's validation requirement. Amounts are decimal, dates are
ISO-8601 (`YYYY-MM-DD`), timestamps are ISO-8601 datetime.

## `POST /api/expenses`

Create an expense entry (manual form — User Story 1 — or confirmed
natural-language draft — User Story 3, with `source=natural_language`).

**Request**
```json
{
  "amount": "5000.00",
  "date": "2026-07-01",
  "category_id": "uuid-or-null",
  "category_name_hint": "electricity bill (optional, used only if category_id omitted, to drive AI suggestion)",
  "description": "Electricity bill for July",
  "source": "manual"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "amount": "5000.00",
  "date": "2026-07-01",
  "category": {"id": "uuid", "name": "Utilities", "is_custom": false},
  "category_source": "ai_suggested",
  "description": "Electricity bill for July",
  "source": "manual",
  "created_at": "2026-07-28T10:00:00Z",
  "updated_at": "2026-07-28T10:00:00Z"
}
```

**Errors**
- `422` — amount is zero/negative (FR-002), or amount/date missing (FR-003).
  Response body names the offending field.

---

## `GET /api/expenses`

List expense entries (User Story 2). Query params: `date_from`, `date_to`,
`category_id` — all optional, combinable (FR-004).

**Response `200`**
```json
{
  "items": [ /* array of the same shape as POST's 201 response */ ],
  "total": 42
}
```

**Errors**
- `422` — `date_from` after `date_to` (Edge Cases).

---

## `GET /api/expenses/{id}`

Fetch a single entry including its edit history (FR-015a).

**Response `200`**
```json
{
  "id": "uuid",
  "amount": "5000.00",
  "date": "2026-07-01",
  "category": {"id": "uuid", "name": "Utilities", "is_custom": false},
  "category_source": "user",
  "description": "Electricity bill for July",
  "source": "manual",
  "created_at": "2026-07-28T10:00:00Z",
  "updated_at": "2026-07-28T10:00:00Z",
  "edit_history": [
    {
      "field_name": "amount",
      "old_value": "4000.00",
      "new_value": "5000.00",
      "changed_at": "2026-08-02T09:00:00Z"
    }
  ]
}
```

**Errors**: `404` — no entry with that id.

---

## `PATCH /api/expenses/{id}`

Edit one or more fields of an existing entry (FR-005); each changed field
generates one `ExpenseEntryEditHistory` row (FR-015).

**Request** (any subset of fields)
```json
{ "amount": "5500.00", "category_id": "uuid" }
```

**Response `200`**: same shape as `GET /api/expenses/{id}` (without
`edit_history`, to keep the write-response small — call `GET` to see
history). If `category_id` is supplied, `category_source` is set to `user`
(FR-011).

**Errors**: `404` — no such entry. `422` — new amount is zero/negative.

---

## `DELETE /api/expenses/{id}`

Delete an entry (FR-006). Cascades to its edit history rows.

**Response**: `204 No Content`.
**Errors**: `404` — no such entry.

---

## `GET /api/categories`

List all categories, starter + custom (used to populate the form's category
picker and to give the AI suggestion tool its candidate list).

**Response `200`**
```json
{ "items": [{"id": "uuid", "name": "Utilities", "is_custom": false}] }
```

---

## `POST /api/categories`

Add a custom category (FR-014).

**Request**: `{ "name": "Marketing" }`
**Response `201`**: `{"id": "uuid", "name": "Marketing", "is_custom": true}`
**Errors**: `409` — a category with that name (case-insensitive) already
exists.

---

## `POST /api/agent/expenses/parse`

Natural-language draft parsing (User Story 3). Does **not** write to the
database — this is the agent's `parse_expense_draft` tool surfaced over
HTTP, per the constitution's Principle II (LLM orchestrates, doesn't write
financial data directly).

**Request**: `{ "text": "add a 5000 electricity bill for July" }`

**Response `200`** — fully parsed:
```json
{
  "status": "ready_for_confirmation",
  "draft": {
    "amount": "5000.00",
    "date": "2026-07-31",
    "category_name_hint": "electricity bill",
    "suggested_category": {"id": "uuid", "name": "Utilities"},
    "description": "Electricity bill for July"
  }
}
```

**Response `200`** — required field missing (FR-009):
```json
{
  "status": "needs_clarification",
  "missing_field": "amount",
  "follow_up_question": "What was the amount?"
}
```

This endpoint is stateless from the API's point of view; the frontend/agent
conversation loop resends an updated `text` (or a merged draft) until
`status` is `ready_for_confirmation`, then calls `POST /api/expenses` with
`source=natural_language` to actually commit — keeping the same
human-confirmation gate (FR-008) as the rest of the create path.
