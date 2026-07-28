# API Contract: Receipt/Invoice Image Capture

## `POST /api/agent/expenses/parse-receipt`

Upload a receipt/invoice image and get a parsed draft (User Story 1). Does
**not** write to the database — this is `parse_receipt_image` surfaced over
HTTP, per the constitution's Principle II, exactly mirroring the existing
`POST /api/agent/expenses/parse` (text) contract's response shape.

**Request**: `multipart/form-data`, one field:
- `file`: the image (`image/jpeg`, `image/png`, or `image/webp`; max 5MB)

**Response `200`** — fully parsed:
```json
{
  "status": "ready_for_confirmation",
  "draft": {
    "amount": "42.50",
    "date": "2026-07-15",
    "category_name_hint": "Office Depot — printer paper and pens",
    "description": "Office Depot — printer paper and pens"
  }
}
```

**Response `200`** — required field missing/unreadable (FR-004):
```json
{
  "status": "needs_clarification",
  "missing_field": "amount",
  "follow_up_question": "What was the amount on this receipt?"
}
```

**Errors**:
- `422` — uploaded file is not a supported image type, or exceeds the 5MB
  size limit (FR-009). Response body names the reason.

This endpoint is stateless and does not persist the upload (FR-008). The
frontend calls `POST /api/expenses` with `source=receipt_image` to commit,
same as the text-based natural-language flow already does with
`source=natural_language` — no new commit endpoint.
