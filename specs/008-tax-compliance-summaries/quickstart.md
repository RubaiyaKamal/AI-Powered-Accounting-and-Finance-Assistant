# Quickstart: Tax & Compliance Summaries

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up`, and that some posted expense activity
already exists (via the `001`/`002` expense-entry and ledger features).

1. **Empty library (edge case)**: `GET /api/tax/documents` on a fresh
   system. Confirm an empty `items` list, not an error.
2. **Add a reference document (US1)**: `POST /api/tax/documents` with a
   short reference document whose content is relevant to a net-loss
   scenario (e.g., "Businesses with a net loss in a quarter owe no
   estimated tax payment for that quarter."). Confirm it appears via
   `GET /api/tax/documents` and its full content via
   `GET /api/tax/documents/{id}`.
3. **Generate a grounded draft (US2)**: `POST /api/tax/summaries` for a
   period with posted expense activity and no revenue (matching this
   project's existing single-cash-account, expense-only ledger).
   Confirm `status: "draft"`, `total_revenue`/`total_expenses`/
   `net_profit` match what `GET /api/reports/profit-and-loss` returns for
   the same period, `cited_passages` includes the document from step 2,
   and `narrative` references that passage without inventing anything
   beyond it.
4. **No relevant material (edge case)**: `POST /api/tax/summaries` for a
   period whose activity has nothing in common with the library's
   documents (or run this before step 2, against an empty library).
   Confirm `cited_passages: []` and the `narrative` explicitly states no
   relevant reference material was found — it does not present tax
   guidance from nowhere.
5. **Zero-activity period (edge case)**: `POST /api/tax/summaries` for a
   date range with no posted entries at all. Confirm a valid draft with
   zero figures, not an error.
6. **Sign off (US3)**: `POST /api/tax/summaries/{id}/sign-off` for the
   draft from step 3. Confirm `status: "signed_off"` and `signed_off_at`
   is set.
7. **Immutability after sign-off (US3)**: Remove the reference document
   from step 2 via `DELETE /api/tax/documents/{id}`, then
   `GET /api/tax/summaries/{id}` for the signed-off summary from step 6.
   Confirm its `cited_passages` and `narrative` are unchanged — the
   removal of the source document did not alter the signed-off record.
8. **Stale-draft sign-off block (edge case)**: `POST /api/tax/summaries`
   for a fresh draft over a period with existing activity. Post a new
   expense entry dated within that period (changing its true P&L), then
   attempt `POST /api/tax/summaries/{id}/sign-off` on the now-stale
   draft. Confirm a `422` blocking sign-off with a message indicating the
   draft is out of date and must be regenerated.
9. **Discard (US3)**: Generate another draft, then
   `DELETE /api/tax/summaries/{id}`. Confirm it no longer appears via
   `GET /api/tax/summaries`.
10. **History (US3)**: `GET /api/tax/summaries`. Confirm the signed-off
    summary from step 6 appears with its status, and any remaining
    drafts appear with theirs.
11. **Natural-language query (US4)**: `POST /api/agent/tax/query` with
    `{"question": "draft a tax summary for this month"}`. Confirm the
    response's `data` is identical to an equivalent direct
    `POST /api/tax/summaries` request for the current month, and
    `narrative` describes the same figures and citations in prose.
12. **Ambiguous query (edge case)**: `POST /api/agent/tax/query` with
    `{"question": "what do we owe"}` (no period determinable). Confirm
    the response asks a clarifying question in `narrative` rather than
    guessing a period.

If all twelve steps behave as described, the feature satisfies its
acceptance scenarios end to end.
