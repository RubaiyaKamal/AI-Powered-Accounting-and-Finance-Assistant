# Phase 1 Data Model: Receipt/Invoice Image Capture

No new entities or tables. This feature adds a third creation path onto the
existing `ExpenseEntry` entity from `001-expense-entry`'s data model.

## ExpenseEntry (extended)

| Field | Change |
|---|---|
| `source` | `Literal["manual", "natural_language"]` → `Literal["manual", "natural_language", "receipt_image"]`. No column type change — `source` is already a plain string column (`String(20)`), so this is a Pydantic/API-layer widening only, not a migration. |

All other `ExpenseEntry` fields, validation rules, and relationships are
unchanged from `001-expense-entry`'s data-model.md.

## Not persisted

The uploaded receipt/invoice image itself is never written to any table,
file, or object store (FR-008, `research.md`'s No Persistent Image Storage
decision) — it exists only in the request/response cycle of
`POST /api/agent/expenses/parse-receipt`, read into memory and discarded
once that request completes.
