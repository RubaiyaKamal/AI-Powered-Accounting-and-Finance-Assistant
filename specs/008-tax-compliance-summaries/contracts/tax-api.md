# API Contract: Tax & Compliance Summaries

All request/response bodies are Pydantic models on the FastAPI backend.
Amounts are decimal, dates are ISO-8601 (`YYYY-MM-DD`), timestamps are
ISO-8601 datetimes.

## `POST /api/tax/documents`

Add a reference document to the library (User Story 1).

**Request**
```json
{ "title": "Quarterly estimated tax thresholds", "content": "Full text of the reference document..." }
```

**Response `201`**
```json
{
  "id": "uuid",
  "title": "Quarterly estimated tax thresholds",
  "content": "Full text of the reference document...",
  "chunk_count": 4,
  "created_at": "2026-07-28T12:00:00Z"
}
```

---

## `GET /api/tax/documents`

List the reference library, most recently added first.

**Response `200`**
```json
{
  "items": [
    { "id": "uuid", "title": "Quarterly estimated tax thresholds", "chunk_count": 4, "created_at": "2026-07-28T12:00:00Z" }
  ],
  "total": 1
}
```

---

## `GET /api/tax/documents/{id}`

View a document's full content.

**Response `200`**: same shape as `POST /api/tax/documents`'s response.

**Errors**: `404` — no document with that id.

---

## `DELETE /api/tax/documents/{id}`

Remove a document (and its chunks) from the library. Does not affect any
already-generated summary, whose cited passages are frozen snapshots, not
live references (`data-model.md`).

**Response**: `204`.

**Errors**: `404` — no document with that id.

---

## `POST /api/tax/summaries`

Generate a draft tax/compliance summary for a chosen period (User Story
2). Query params/body: `start`, `end` — dates, both optional; if either
is omitted, both default to the current calendar month.

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
  "status": "draft",
  "total_revenue": "0.00",
  "total_expenses": "6504.00",
  "net_profit": "-6504.00",
  "cited_passages": [
    { "document_title": "Quarterly estimated tax thresholds", "chunk_text": "Businesses with net losses in a quarter are not subject to estimated tax payments for that period." }
  ],
  "narrative": "For July 2026, the business recorded a net loss of $6,504.00. Per the referenced quarterly-threshold guidance, no estimated tax payment applies for a loss quarter. This is an unreviewed draft — sign off before treating it as final.",
  "generated_at": "2026-07-28T12:00:00Z",
  "signed_off_at": null
}
```
`cited_passages` is `[]` when no relevant reference material was found —
the `narrative` explicitly says so in that case rather than presenting
unsourced guidance (FR-005).

**Errors**: `422` — `end` is before `start`.

---

## `GET /api/tax/summaries`

List past summaries (drafts and signed-off), most recent first (User
Story 3).

**Response `200`**
```json
{
  "items": [
    {
      "id": "uuid", "start": "2026-07-01", "end": "2026-07-31", "status": "draft",
      "total_revenue": "0.00", "total_expenses": "6504.00", "net_profit": "-6504.00",
      "generated_at": "2026-07-28T12:00:00Z", "signed_off_at": null
    }
  ],
  "total": 1
}
```

---

## `GET /api/tax/summaries/{id}`

Reopen a summary's full detail (draft or signed-off) — same response
shape as `POST /api/tax/summaries`.

**Errors**: `404` — no summary with that id.

---

## `POST /api/tax/summaries/{id}/sign-off`

Sign off on a draft, making it an official, immutable record (User Story
3, FR-007).

**Response `200`**: same shape as `POST /api/tax/summaries`'s response,
with `status: "signed_off"` and `signed_off_at` set.

**Errors**: `404` — no summary with that id. `409` — the summary is
already signed off. `422` — the period's figures have changed since this
draft was generated; regenerate a fresh draft before signing off (FR-009).

---

## `DELETE /api/tax/summaries/{id}`

Discard a draft (FR-010).

**Response**: `204`.

**Errors**: `404` — no summary with that id. `409` — the summary is
already signed off and cannot be discarded.

---

## `POST /api/agent/tax/query`

Ask for a summary in natural language (User Story 4). The agent resolves
a date range from the question, generates the summary via the *exact
same* deterministic process `POST /api/tax/summaries` uses, and narrates
the result — it never computes a figure or invents a citation itself
(FR-004, FR-005).

**Request**: `{ "question": "draft a tax summary for last quarter" }`

**Response `200`**
```json
{
  "data": { "...": "same shape as POST /api/tax/summaries's response" },
  "narrative": "I drafted a summary for Q2 2026 — a net loss of $6,504.00, with no estimated tax payment due per your quarterly-threshold reference. It's saved as an unreviewed draft."
}
```
`data` is always numerically and textually identical to what
`POST /api/tax/summaries` would return for the same resolved period.

**Errors**: `422` — the question could not be confidently resolved to a
date range (the agent asks a clarifying question in `narrative` instead
of guessing, per spec Edge Cases); `data` is `null` in this case.
