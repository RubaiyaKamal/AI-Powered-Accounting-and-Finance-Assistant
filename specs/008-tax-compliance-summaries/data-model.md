# Phase 1 Data Model: Tax & Compliance Summaries

Derived from the Key Entities section of `spec.md` and the storage
decisions in `research.md`. Three new tables. `tax_summaries` stores its
figures and cited passages as fixed values/snapshots rather than live
references, per `research.md`'s immutability decision.

## TaxRulesDocument

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `title` | text | not null | admin-provided |
| `content` | text | not null | the full original text, kept for viewing (FR-001) |
| `created_at` | timestamptz | not null, default now() | |

**Relationships**: has many `TaxRulesDocumentChunk` rows, `ON DELETE
CASCADE` — removing a document removes its chunks from future retrieval
(FR-001's "remove" scenario). Already-signed-off summaries are unaffected
(they hold their own frozen copy — see `TaxSummary` below).

## TaxRulesDocumentChunk

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `document_id` | FK → TaxRulesDocument.id, `ON DELETE CASCADE` | not null | |
| `chunk_index` | integer | not null | position within the document, for stable ordering |
| `chunk_text` | text | not null | one paragraph-sized passage (`research.md`'s chunking decision) |
| `embedding` | array of float, nullable | nullable | the passage's embedding vector; `null` when the chunk was added while no `OPENAI_API_KEY` was configured — retrieval falls back to keyword-overlap scoring for chunks without one (`research.md`) |
| `created_at` | timestamptz | not null, default now() | |

**Relationships**: belongs to exactly one `TaxRulesDocument`.

## TaxSummary

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `start` | date | not null | the resolved period start |
| `end` | date | not null | the resolved period end |
| `status` | enum(`draft`, `signed_off`) | not null, default `draft` | discarding a draft deletes its row outright (FR-010) — there is no third "discarded" status to display, since a discarded draft was never official and carries no audit-trail obligation |
| `total_revenue` | decimal | not null | copied from `ReportingService.profit_and_loss` at generation time |
| `total_expenses` | decimal | not null | copied from `ReportingService.profit_and_loss` at generation time |
| `net_profit` | decimal | not null | copied from `ReportingService.profit_and_loss` at generation time |
| `cited_passages` | JSON array | not null, may be empty | each element is a fixed snapshot `{"document_title": str, "chunk_text": str}` copied at generation time — never a live reference to a `TaxRulesDocumentChunk` row (`research.md`'s immutability decision); an empty array means no relevant passage was found (FR-005) |
| `narrative` | text | not null | the AI-drafted prose, grounded only in the two fields above |
| `generated_at` | timestamptz | not null, default now() | |
| `signed_off_at` | timestamptz, nullable | nullable | set only when `status` becomes `signed_off` |

**Validation rules**:
- `status` only ever transitions `draft` → `signed_off` (FR-007); there is
  no `signed_off` → `draft` transition.
- Sign-off is refused (see `TaxSummaryService.sign_off`, `research.md`'s
  staleness-check decision) if recomputing `profit_and_loss` for
  `[start, end]` no longer matches `total_revenue`/`total_expenses` —
  the caller must regenerate a fresh draft for that period first (FR-009).

**Relationships**: none live — `cited_passages` is a self-contained
snapshot, not a foreign key, so a `TaxSummary` has no relationship to
`TaxRulesDocument`/`TaxRulesDocumentChunk` after generation.

**State transitions**:
1. `TaxSummaryService.generate` computes figures via
   `reporting_service.profit_and_loss`, retrieves the most relevant
   chunks (or none, per FR-005), drafts the narrative via
   `draft_summary_narrative`, and persists a new `TaxSummary` row with
   `status=draft`.
2. An admin either:
   - **Signs off** (US3, FR-007): the service re-verifies the figures are
     still current, then sets `status=signed_off` and `signed_off_at`.
     From this point the row is never mutated again.
   - **Discards** (FR-010): the row is deleted outright.
