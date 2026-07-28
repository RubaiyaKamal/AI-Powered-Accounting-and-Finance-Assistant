# Phase 0 Research: Receipt/Invoice Image Capture

The backend/frontend/database/AI stack is fixed by the constitution and
already established by `001-expense-entry`/`002-ledger-journal-entries` —
no `NEEDS CLARIFICATION` markers remain in Technical Context. The two
biggest architecture questions for this feature (extraction method,
persistent storage) were already resolved during the plan-mode session that
preceded this spec; this document records those decisions plus the
remaining feature-scoped ones.

## Decision: Extraction method — GPT-4o mini vision, not classic OCR

**Decision**: Send the uploaded image directly to GPT-4o mini's multimodal
input (one LLM call performs both text extraction and field structuring).
**Rationale**: Already decided and confirmed with the user before this spec
was written (see `C:\Users\Lap Zone\.claude\plans\splendid-hopping-willow.md`).
No new system dependency (a Tesseract-based pipeline would require OS-level
binaries in `backend/Dockerfile`); stays inside the constitution's fixed AI
layer (OpenAI Agents SDK + GPT-4o mini); the project's own research
citations favor LLM-based extraction over template-based OCR for messy,
real-world receipt layouts.
**Alternatives considered**: Classic OCR (Tesseract) + a second LLM call to
structure the raw text — rejected for the reasons above; a cloud OCR
vendor (Google Vision, AWS Textract) — rejected, introduces a second AI
vendor the constitution's Technology & Architecture Constraints doesn't
already fix, a governance-level change this feature doesn't need to make.

## Decision: No persistent image storage

**Decision**: The uploaded image is read into memory for the single
extraction request and discarded afterward — never written to disk, object
storage, or a database column.
**Rationale**: Already decided during the plan-mode session. Avoids
standing up new storage infrastructure for a project of this scope;
mirrors how `parse_expense_draft` already works (draft → human confirms →
commits through `POST /api/expenses`, nothing written before confirmation).
Directly implements FR-008 and SC-004.
**Alternatives considered**: Storing the image temporarily (e.g., in a
`/tmp`-backed volume) for a "re-process" retry feature — rejected, no
such requirement exists in the spec, and it would need a cleanup/expiry
mechanism this project's scope doesn't call for (YAGNI, constitution
Principle VI).

## Decision: Where the new capability lives (agent tool + endpoint)

**Decision**: `parse_receipt_image` is added to the existing
`backend/src/agent/expense_tools.py` (alongside `parse_expense_draft` and
`suggest_category`), exposed via a new `POST /api/agent/expenses/parse-receipt`
endpoint in the existing `backend/src/api/agent.py`, returning the exact
same `{"status": "ready_for_confirmation", "draft": {...}}` /
`{"status": "needs_clarification", ...}` shape `parse_expense_draft`
already returns.
**Rationale**: This is the same domain (drafting an expense entry for
confirmation) reached through a different input modality — a new file/module
would duplicate the draft-shape contract for no benefit. Reusing the exact
response shape also means the frontend's existing draft-rendering/confirm
UI in `AssistantChat.tsx` needs only a new *trigger* (file upload), not new
rendering logic.
**Alternatives considered**: A separate `receipt_tools.py` module and a
dedicated `ReceiptUpload` frontend component — rejected per Constitution
Check (Principle VI): this doubles the surface area (two draft shapes, two
confirm UIs) for a feature that is conceptually "one more way to reach the
same draft-then-confirm flow," not a distinct capability.

## Decision: `source` marker — extend the existing enum, not a new field

**Decision**: `ExpenseEntryCreate.source` (currently `Literal["manual",
"natural_language"]`) gains a third value, `"receipt_image"`. No new
column, no new table.
**Rationale**: Directly implements FR-006 with the smallest possible schema
change — the `source` column already exists precisely to distinguish
creation paths (per `001-expense-entry`'s data-model.md), and this is a
third creation path, not a new concept.
**Alternatives considered**: A separate boolean/column like
`created_from_image` — rejected, redundant with the existing `source`
column's purpose.

## Decision: Upload validation (format/size)

**Decision**: Accept `image/jpeg`, `image/png`, and `image/webp` content
types; reject anything else and anything over 5MB, both with a clear `422`
error before attempting extraction.
**Rationale**: The spec's Assumptions section explicitly calls the exact
formats/size limit an implementation detail, not a business-scope decision.
5MB comfortably covers a phone photo of a receipt while bounding request
size and the base64-encoded payload sent to the vision model.
**Alternatives considered**: No size limit — rejected, an unbounded upload
is an easy, low-value abuse vector and a poor default even at this
project's small scale.

## Outstanding item carried to Complexity Tracking / tasks

Per Constitution Check, the workflow diagram (`docs/workflow-diagram.drawio`,
Principle V) must be updated to include the `parse_receipt_image` tool and
the new upload flow before this feature's PR merges — carried forward as an
explicit task in `tasks.md`, matching how both prior features handled their
own diagram updates.
