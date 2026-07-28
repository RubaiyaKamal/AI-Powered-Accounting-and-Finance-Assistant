# Quickstart: Receipt/Invoice Image Capture

Manual validation flow once the feature is implemented. Assumes the stack is
running via `docker-compose up` (frontend, backend, PostgreSQL).

1. **Upload a clear receipt photo (US1)**: In the assistant chat, upload a
   clear, legible photo of a receipt showing an amount, a date, and a
   vendor name. Confirm the assistant shows a parsed amount, date, and
   description (including the vendor) before asking for confirmation
   (FR-002).
2. **Confirm and save (US1)**: Confirm the parsed draft. Verify an expense
   entry is saved with exactly the shown values, and that it's tagged as
   created from a receipt image (`source=receipt_image`).
3. **Correct before saving (US1)**: Upload another receipt, but before
   confirming, correct one field (e.g., the amount). Confirm the saved
   entry reflects the corrected value, not the originally parsed one
   (FR-003).
4. **Unreadable image (US1 edge case)**: Upload a blurry or cropped image
   where the amount can't be read. Confirm the assistant asks a specific
   follow-up question for the amount (FR-004) rather than guessing or
   silently failing.
5. **AI category suggestion (US1 scenario 4)**: Upload a receipt whose
   vendor/description doesn't map to an obvious existing category. Confirm
   the saved entry receives an AI-suggested category via the same mechanism
   already used for manual/natural-language entries (FR-007).
6. **Rejected upload (Edge Case)**: Try uploading a non-image file (e.g., a
   `.docx`) and, separately, an oversized image. Confirm both are rejected
   with a clear message before any extraction is attempted (FR-009).
7. **No image retained (FR-008)**: After completing steps 1–5, confirm
   nowhere in the system (filesystem, database, object storage) is the
   uploaded image itself retained — only the resulting expense entries are.

If all seven steps behave as described, the feature satisfies its
acceptance scenarios end to end.
