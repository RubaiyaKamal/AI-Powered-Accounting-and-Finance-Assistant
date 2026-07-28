# API Contract: Bank/Vendor Reconciliation

All request/response bodies are Pydantic models on the FastAPI backend.
Amounts are decimal, dates are ISO-8601 (`YYYY-MM-DD`), timestamps are
ISO-8601 datetime.

## `POST /api/reconciliation/import`

Upload a bank statement CSV (User Story 1). Runs the matching pass
immediately for every newly imported (non-duplicate) transaction (User
Story 2).

**Request**: `multipart/form-data`, one field:
- `file`: the CSV (`text/csv`), with `date`, `amount`, `description`
  columns (case-insensitive header match; extra columns ignored)

**Response `200`**
```json
{
  "imported": 42,
  "duplicates_skipped": 3,
  "invalid_rows_skipped": [
    {"row": 17, "reason": "unparseable date"}
  ],
  "auto_matched": 30,
  "needs_review": 12
}
```

**Errors**: `422` — file is not a valid CSV, or is missing a required
column entirely.

---

## `GET /api/reconciliation/bank-transactions`

List bank transactions (User Story 2/3). Query params: `status` —
`matched` | `unmatched` (no `Match` row yet) | `dismissed` — optional.

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid",
      "date": "2026-07-15",
      "amount": "39.50",
      "description": "GREENLEAF OFFICE SUPPLIES",
      "match": {
        "id": "uuid",
        "expense_entry_id": "uuid",
        "source": "auto",
        "status": "confirmed",
        "ai_reasoning": null
      }
    }
  ],
  "total": 1
}
```
`match` is `null` for an unmatched (unresolved) transaction.

---

## `GET /api/reconciliation/review-queue`

List transactions needing admin attention (User Story 3): those with no
`Match` row, whether ambiguous (AI-adjudicated, with a suggestion) or
fully unmatched (no suggestion).

**Response `200`**
```json
{
  "items": [
    {
      "bank_transaction": {
        "id": "uuid",
        "date": "2026-07-15",
        "amount": "39.50",
        "description": "GREENLEAF OFFICE SUPPLIES"
      },
      "suggested_expense_entry": {"id": "uuid", "amount": "39.50", "date": "2026-07-14", "description": "Office supplies"},
      "ai_reasoning": "Two entries on 07/14 and 07/16 both total $39.50; the 07/14 entry's description more closely matches 'GREENLEAF OFFICE SUPPLIES'.",
      "candidates_considered": [
        {"id": "uuid", "amount": "39.50", "date": "2026-07-14", "description": "Office supplies"},
        {"id": "uuid", "amount": "39.50", "date": "2026-07-16", "description": "Supplies run"}
      ]
    }
  ],
  "total": 1
}
```
`suggested_expense_entry`, `ai_reasoning`, and `candidates_considered` are
all `null`/omitted for a fully-unmatched transaction with no plausible
candidates (Edge Cases, FR-007).

---

## `POST /api/reconciliation/bank-transactions/{id}/match`

Confirm a suggested match or pick a different expense entry (US3 scenario
3, FR-008).

**Request**: `{ "expense_entry_id": "uuid" }`

**Response `201`**
```json
{ "id": "uuid", "bank_transaction_id": "uuid", "expense_entry_id": "uuid", "source": "manual", "status": "confirmed", "ai_reasoning": null }
```

**Errors**: `404` — no such bank transaction or expense entry. `409` — the
bank transaction is already resolved, or the expense entry is already
matched to a different bank transaction (FR-010).

---

## `POST /api/reconciliation/bank-transactions/{id}/dismiss`

Mark a bank transaction as having no corresponding expense entry (US3
scenario 3, FR-008) — e.g., a bank fee.

**Response `201`**
```json
{ "id": "uuid", "bank_transaction_id": "uuid", "expense_entry_id": null, "source": "manual", "status": "dismissed", "ai_reasoning": null }
```

**Errors**: `404` — no such bank transaction. `409` — already resolved.

---

## `DELETE /api/reconciliation/matches/{id}`

Undo a confirmed match (US3 scenario 4, FR-011), returning the bank
transaction to unmatched.

**Response**: `204 No Content`.
**Errors**: `404` — no such match, or the match is `dismissed` (per
FR-009/FR-011, only confirmed matches can be undone).
