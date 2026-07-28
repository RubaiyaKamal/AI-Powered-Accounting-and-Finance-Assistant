# Feature Specification: Receipt/Invoice Image Capture

**Feature Branch**: `003-receipt-image-capture`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Receipt/invoice image capture: allow an admin to upload a photo or scan of a receipt or invoice and have the system extract the amount, date, vendor/description, and a suggested category by sending the image directly to GPT-4o mini's vision input (one LLM call handles both text extraction and field structuring, no separate OCR library). The extracted draft is shown for confirmation (or a specific clarifying question if a required field couldn't be read), mirroring the existing natural-language entry flow, and commits through the same existing POST /api/expenses endpoint once confirmed. The uploaded image itself is not persisted after extraction — only the resulting expense entry is."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record an expense by uploading a receipt or invoice photo (Priority: P1)

An admin has a paper receipt or a PDF/photo invoice and, instead of typing
the details manually or dictating them as a sentence, uploads a photo or
scan of it. The system reads the amount, date, and vendor/description off
the image, shows the admin a parsed draft to confirm or correct, and saves
the entry once confirmed.

**Why this priority**: This is the entire feature — image-based capture is
the one new capability being added. It must work end to end (upload →
parsed draft → confirm → saved entry) to deliver any value at all.

**Independent Test**: Can be fully tested by uploading a clear, legible
receipt photo and confirming the system shows a parsed amount, date, and
description matching the receipt, then confirming it saves an expense entry
with exactly those values.

**Acceptance Scenarios**:

1. **Given** a clear photo of a receipt showing an amount, a date, and a
   vendor name, **When** the admin uploads it, **Then** the system shows
   the parsed amount, date, and a description (including the vendor) for
   confirmation before saving anything — no entry is created without
   explicit confirmation.
2. **Given** a parsed draft shown for confirmation, **When** the admin
   confirms it as-is, **Then** an expense entry is saved with exactly the
   shown values, tagged as created from a receipt image; **When** the admin
   instead corrects a field first, **Then** the entry is saved with the
   corrected value, not the originally parsed one.
3. **Given** an uploaded image from which the amount or date cannot be
   confidently read (e.g., faded, cropped, or partially obscured), **When**
   the admin uploads it, **Then** the system asks a specific clarifying
   question for the missing field (e.g., "What was the amount?") instead of
   guessing a value or silently rejecting the upload.
4. **Given** an entry successfully created from a receipt image without an
   explicit category, **When** it is saved, **Then** it receives an
   AI-suggested category via the same mechanism already used for manual and
   natural-language entries (no separate category logic for this feature).

---

### Edge Cases

- What happens when the uploaded file is not a supported image type (e.g.,
  a `.docx` or an unsupported format)? The system rejects it with a clear
  message before attempting extraction.
- What happens when the uploaded image exceeds the size limit? The system
  rejects it with a clear message rather than attempting to process an
  oversized file.
- What happens when the image is a real photo but not a receipt/invoice at
  all (e.g., an unrelated picture)? The system is unable to extract the
  required fields and asks a clarifying question rather than fabricating
  plausible-looking values.
- What happens when a receipt shows multiple line items? The MVP treats the
  whole receipt as a single expense entry using its total amount, not an
  itemized breakdown — itemized splitting is out of scope for this feature.
- What happens if the admin uploads the same receipt twice? Both uploads
  are processed independently and each produces its own draft for
  confirmation; duplicate detection is an audit-time concern (already
  deferred in `001-expense-entry`'s spec), not an upload-time restriction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to upload a receipt or invoice image
  (common photo/scan formats) as an alternative way to create an expense
  entry.
- **FR-002**: Upon upload, the system MUST extract an amount, a date, and a
  vendor/description from the image and show them as a draft for the admin
  to review before anything is saved.
- **FR-003**: Users MUST be able to correct any extracted field before
  confirming, the same as the existing natural-language entry flow.
- **FR-004**: When a required field (amount or date) cannot be confidently
  read from the image, the system MUST ask a specific clarifying question
  for that field instead of guessing a value, silently discarding the
  upload, or falling back to a separate blank form.
- **FR-005**: The system MUST commit a confirmed entry through the same
  expense-creation path used by manual and natural-language entries — no
  separate write path for image-sourced entries (constitution Principle
  II).
- **FR-006**: An expense entry created from a receipt/invoice image MUST be
  identifiable as such, the same way natural-language-sourced entries are
  already distinguished from manually entered ones.
- **FR-007**: When no explicit category is determinable from the image,
  the system MUST suggest one using the existing AI category-suggestion
  mechanism (FR-010 of `001-expense-entry`) rather than a separate
  image-specific categorization step.
- **FR-008**: The system MUST NOT retain the uploaded image after
  extraction completes — only the resulting draft (pre-confirmation) and,
  once confirmed, the resulting expense entry are persisted.
- **FR-009**: The system MUST reject an uploaded file that is not a
  supported image type or that exceeds the configured size limit, with a
  clear explanation of why it was rejected.

### Key Entities *(include if feature involves data)*

None new. This feature adds a new *creation path* onto the existing
`Expense Entry` entity from `001-expense-entry` — it extends that entity's
source marker (alongside `manual` and `natural_language`) rather than
introducing a new persisted entity, consistent with FR-006 and FR-008 (the
image itself is never persisted).

### Assumptions

- Extracted vendor information is folded into the existing free-text
  `description` field on the expense entry rather than requiring a new
  dedicated `vendor` column — consistent with not modifying
  `001-expense-entry`'s already-shipped data model beyond its source marker
  (FR-006).
- Accepted image formats and the maximum upload size are implementation
  details (e.g., JPEG/PNG, a few megabytes), not business-scope decisions,
  and do not require their own clarification.
- Single-line-item MVP: a receipt with multiple purchased items is recorded
  as one expense entry for its total amount; itemized line-by-line entry
  creation is out of scope (Edge Cases).
- Single business, single admin user, single currency — same assumptions
  as `001-expense-entry`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin can create an expense entry from a receipt photo,
  from upload to confirmed save, in under 30 seconds of their own
  interaction time (excluding processing wait).
- **SC-002**: At least 90% of clear, legible receipt photos have their
  amount and date extracted correctly on the first attempt.
- **SC-003**: 100% of images from which a required field cannot be
  confidently read result in a clarifying question rather than a silently
  incorrect entry.
- **SC-004**: 0% of uploaded images remain stored anywhere in the system
  after the corresponding draft is confirmed or discarded.
