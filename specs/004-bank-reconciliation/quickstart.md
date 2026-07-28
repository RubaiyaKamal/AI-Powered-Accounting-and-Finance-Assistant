# Quickstart: Bank/Vendor Reconciliation

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up`, and that a handful of expense entries
already exist (e.g., one at $39.50 dated 2026-07-15 with a description
mentioning "Greenleaf Office Supplies").

1. **Import a bank statement (US1)**: Prepare a CSV with `date`, `amount`,
   `description` columns, including one line closely matching an existing
   expense entry, one line with an amount that doesn't match anything, and
   one intentionally malformed row (bad date). Upload it. Confirm the
   response reports the correct counts of imported/duplicate/invalid rows
   (FR-001–FR-003).
2. **Re-upload the same file (US1 edge case)**: Upload the identical CSV
   again. Confirm the previously-imported rows are now reported as
   duplicates and not re-imported.
3. **Automatic matching (US2)**: Confirm the clearly-matching line from
   step 1 was auto-matched to its expense entry without any manual action
   — check `GET /api/reconciliation/bank-transactions` shows it with
   `match.source=auto`, `match.status=confirmed`.
4. **Review queue — ambiguous case (US3)**: Set up two expense entries
   with the same amount and close dates, then import a bank transaction
   matching that amount with a description resembling one of them more
   than the other. Confirm it appears in
   `GET /api/reconciliation/review-queue` with a suggested match and AI
   reasoning explaining the choice (FR-006).
5. **Review queue — no match (US3)**: Confirm the amount-mismatched line
   from step 1 appears in the review queue with no suggestion at all
   (FR-007).
6. **Resolve the queue (US3)**: Confirm the ambiguous item's suggestion.
   Dismiss the no-match item as a bank fee. Confirm both disappear from
   the review queue and don't reappear on a subsequent
   `GET /api/reconciliation/review-queue` call (FR-009).
7. **Undo a match (US3 scenario 4)**: Undo the auto-matched item from step
   3. Confirm it returns to unmatched and reappears (unmatched, or back in
   the review queue on the next matching pass) rather than staying
   incorrectly linked (FR-011).
8. **Delete-cascade (Edge Case, FR-013)**: Delete the expense entry behind
   a confirmed match. Confirm the corresponding bank transaction is now
   unmatched again rather than pointing at a nonexistent entry.

If all eight steps behave as described, the feature satisfies its
acceptance scenarios end to end.
