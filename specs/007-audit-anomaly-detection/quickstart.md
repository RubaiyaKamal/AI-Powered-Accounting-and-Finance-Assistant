# Quickstart: Audit & Anomaly Detection

Manual validation flow once the feature is implemented. Assumes the stack
is running via `docker-compose up`, and that the ledger already has a
reasonable amount of posted activity (at least 20 posted journal entries —
`research.md`'s minimum-data threshold — spanning several accounts and
amounts, via the `001`/`002` expense-entry and ledger features).

1. **Insufficient data (edge case)**: On a freshly seeded ledger with
   fewer than 20 posted entries, `POST /api/audit/runs` with no body.
   Confirm the response has `status: "insufficient_data"`,
   `entries_flagged: 0`, and an empty `flags` array — not an error.
2. **Seed deliberate anomalies**: Post a small set of typical expense
   entries (similar amounts, typical accounts), then add: one entry with
   an amount far larger than the rest, one entry with a suspiciously round
   amount (e.g., exactly $1,000.00), and two entries with identical
   amount/date/account (a duplicate-looking pair) — at least 20 entries
   total.
3. **Run an audit (US1)**: `POST /api/audit/runs` with no body (defaults
   to the whole ledger). Confirm `status: "completed"`, and that the
   deliberately unusual entries from step 2 appear in `flags` with reason
   categories matching what makes each one stand out
   (`unusual_amount`, `round_number`, `duplicate_looking`), while the
   typical entries do not appear. Confirm each flag's `explanation` text
   accurately describes its actual reason categories.
4. **Clean period (edge case)**: `POST /api/audit/runs` with a date range
   containing only the typical (non-anomalous) entries from step 2.
   Confirm `status: "completed"`, `entries_flagged: 0`, `flags: []`.
5. **Resolve a flag (US2)**: Pick a flag's `id` from step 3.
   `PATCH /api/audit/flags/{id}` with `{"resolution": "false_positive"}`.
   Confirm the response reflects the new resolution and a `resolved_at`
   timestamp.
6. **Re-view shows the resolution (US2)**: `GET /api/audit/runs/{id}` for
   the run from step 3. Confirm the flag resolved in step 5 shows
   `resolution: "false_positive"` (not `unreviewed`), while the other
   flags from that run still show `unreviewed`.
7. **Audit history (US3)**: `GET /api/audit/runs`. Confirm all runs from
   the steps above appear, most recent first, each with its date range and
   flag count.
8. **Reversed-entry edge case**: Correct one of the flagged entries from
   step 2 (triggering `002`'s automatic reverse-and-repost). Re-fetch the
   audit run from step 3 via `GET /api/audit/runs/{id}`. Confirm that
   flag's original score/reasons/explanation are unchanged (it's a
   historical record), while the referenced journal entry's own status
   shows it's no longer the active posting.
9. **Natural-language audit query (US4)**: `POST /api/agent/audit/query`
   with `{"question": "check this month for anything unusual"}`. Confirm
   the response's `data` is numerically identical to an equivalent direct
   `POST /api/audit/runs` request for the current month, and `narrative`
   describes the same flagged entries in prose without introducing any new
   number or entry.
10. **Ambiguous query edge case**: `POST /api/agent/audit/query` with
    `{"question": "check for fraud"}` (no period determinable). Confirm
    the response asks a clarifying question in `narrative` rather than
    guessing a period and fabricating results.

If all ten steps behave as described, the feature satisfies its
acceptance scenarios end to end.
