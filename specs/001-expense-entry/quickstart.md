# Quickstart: Expense Entry

Manual validation flow once the feature is implemented. Assumes the stack is
running via `docker-compose up` (frontend, backend, PostgreSQL).

1. **Manual create (US1)**: Open the expenses page, submit an entry with
   amount `1000`, today's date, category `Rent`. Confirm it appears in the
   list. Then try submitting `0` and a negative amount — both must be
   rejected with a clear message (FR-002).
2. **View/filter/edit/delete (US2)**: Filter the list by this month's date
   range. Edit the entry's amount to `1200`. Open the entry and confirm the
   edit history shows `amount: 1000 → 1200` with a timestamp (FR-015,
   FR-015a). Delete the entry and confirm it disappears from the list.
3. **Natural-language entry (US3)**: In the assistant chat, send "add a 5000
   electricity bill for July". Confirm the assistant shows parsed amount
   `5000`, a July date, and a category before asking for confirmation
   (FR-008). Confirm it, then verify the entry appears in the list tagged as
   created via natural language.
4. **Missing-field follow-up (US3 edge case)**: Send "add an expense for
   July" (no amount). Confirm the assistant asks a specific follow-up
   question for the amount in the same turn (FR-009) rather than guessing or
   silently failing.
5. **AI category suggestion (US4)**: Submit an entry with a description
   ("office wifi bill") but no category. Confirm a suggested category
   appears, marked as AI-suggested (FR-010). Override it with a different
   category and confirm the AI-suggested marker is removed (FR-011).
6. **Custom category (FR-014)**: Add a new category, e.g. "Marketing", and
   confirm it's usable immediately when creating or editing an entry.

If all six steps behave as described, the feature satisfies its acceptance
scenarios end to end.
