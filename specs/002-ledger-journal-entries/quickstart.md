# Quickstart: Ledger & Journal Entries

Manual validation flow once the feature is implemented. Assumes the stack is
running via `docker-compose up` (frontend, backend, PostgreSQL) and that at
least one expense entry already exists (per `001-expense-entry`'s
quickstart).

1. **AI-suggested coding, high confidence (US1)**: Open an expense entry
   with a clear description (e.g. "electricity bill"). Confirm the system
   shows a suggested account (e.g. "Utilities Expense") and a confidence
   score, and — since this should score above the threshold — confirm it is
   already `approved` with a posted journal entry, with no extra click
   required (FR-004).
2. **AI-suggested coding, low confidence / manual review (US1)**: Open an
   expense entry with a vague description. Confirm the suggested coding is
   shown as `pending_review` (not auto-posted). Approve it and confirm a
   journal entry is then posted (US1 scenario 2).
3. **Correcting a coding (US1)**: On a coded entry, pick a different account
   than the one suggested. Confirm the coding updates to the new account,
   is no longer marked AI-suggested, and (US2 scenario 3) the old journal
   entry is reversed and a new one posted for the corrected account.
4. **Double-entry balance (US2)**: For any posted journal entry, confirm it
   shows one debit line and one credit line for the same amount, and that
   the amount matches the source expense entry's amount exactly (FR-007).
5. **Deleting a posted expense (Edge Case)**: Delete an expense entry that
   already has a posted journal entry. Confirm the journal entry is
   reversed (not silently deleted) — the ledger still shows both the
   original and reversing entries (FR-012).
6. **Viewing the ledger (US3)**: Open the ledger view. Filter by the
   "Utilities Expense" account and confirm only journal entries touching
   that account are shown. Filter by a date range and confirm the same.
   Open a journal entry and confirm it links back to its source expense
   entry.

If all six steps behave as described, the feature satisfies its acceptance
scenarios end to end.
