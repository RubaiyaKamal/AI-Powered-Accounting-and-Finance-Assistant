# Phase 0 Research: Financial Reporting

The backend/frontend/database/AI stack is fixed by the constitution and
already established by prior features — no `NEEDS CLARIFICATION` markers
remain in Technical Context. This document records the feature-scoped
design decisions specific to which entries count toward a report, how
figures are computed without pandas, and how the AI's role is bounded.

## Decision: SQL aggregation (SQLAlchemy `SUM`/`GROUP BY`), not pandas

**Decision**: Every report figure is produced by a SQLAlchemy async query
that sums `JournalEntry.amount` grouped by account (and, for the two
period reports, filtered by `date BETWEEN start AND end`) directly in
PostgreSQL. No `pandas` DataFrame is introduced.
**Rationale**: The user's request named "SQL/pandas" as shorthand for "not
computed by the LLM" — the actual requirement (constitution Principle II)
is that figures come from deterministic backend computation, not that a
specific library is used. The aggregations this feature needs (sum debit
amounts per account, sum credit amounts per account, optionally within a
date range) are exactly what SQL `GROUP BY`/`SUM` already does in one
round trip; pulling rows into a `pandas.DataFrame` to do the same sum in
Python would add a new dependency and an extra data-marshalling step for
no additional capability, which Principle VI (Simplicity) weighs against.
**Alternatives considered**: `pandas` (rejected — no dataset here is large
or irregular enough to benefit from a DataFrame; every current feature in
this codebase does its aggregation directly in SQLAlchemy/Postgres, and
adding `pandas` as this feature's one new dependency for a handful of
`SUM(...) GROUP BY account_id` queries would be complexity without payoff);
computing sums in a Python loop over ORM objects (rejected — strictly worse
than letting Postgres do the aggregation: more memory, more code, and no
determinism advantage over `SUM`/`GROUP BY`, which is exactly as
deterministic).

## Decision: Which journal entries count — active postings only

**Decision**: Every report query filters to
`JournalEntry.status == "posted" AND JournalEntry.reverses_journal_entry_id IS NULL`
— i.e., the same "currently active, non-reversal, non-reversed posting"
definition `ledger_service.active_journal_entry()` already uses for a
single account coding, applied globally across all codings for
aggregation.
**Rationale**: A reversed entry (`status="reversed"`) and its reversal
entry (`reverses_journal_entry_id` set) are a matched pair whose sole
purpose is to cancel each other out — they must be excluded *together*.
Filtering only on `status == "posted"` would incorrectly keep the reversal
entry (which is `status="posted"`) while dropping the original it was
meant to cancel, double-counting the correction instead of netting it to
zero. Reusing the exact WHERE clause `active_journal_entry()` already
established for the single-coding case is both correct and consistent
with existing code, directly satisfying spec FR-006 (reversed entries and
their originals must never distort a balance) and the Edge Case about
reversed entries.
**Alternatives considered**: Filtering only on `status == "posted"`
(rejected — demonstrably wrong per the worked example above: it
double-counts a reversal's offsetting effect instead of netting the pair
to zero); including every entry ever posted regardless of status
(rejected — would count reversed-away entries as if they were still in
effect, the opposite bug).

## Decision: Report period defaults and the shared "as of" vs. "for period" split

**Decision**: Trial Balance and Balance Sheet are point-in-time
("as of `date`", cumulative from inception) and default to today when no
date is given. Profit & Loss and Cash Flow are period-based
("for `start`–`end`") and default to the current calendar month when no
range is given. All four accept an explicit override.
**Rationale**: This mirrors standard accounting practice (a trial balance
or balance sheet is a snapshot; a P&L or cash flow statement is a
period summary) and was already anticipated as a reasonable default in
`spec.md`'s Assumptions, not something requiring its own clarification.
**Alternatives considered**: Requiring an explicit date/range on every
request with no default (rejected — makes the natural-language chat path
worse, since a vague request like "how's the business doing" would always
fail rather than resolving to a sensible default).

## Decision: Two narrow, single-shot LLM calls — not a general tool-calling agent

**Decision**: The natural-language path is two small, single-purpose LLM
calls, each following the exact pattern already used by
`suggest_account_coding` (`002`) and `adjudicate_match` (`004`) — a single
prompt, a single JSON-shape response, a deterministic fallback when no
`OPENAI_API_KEY` is configured:
1. `resolve_report_request(question, today)` → returns which of the four
   report types is meant, plus a date (point-in-time reports) or date
   range (period reports). It is given the question text and today's
   date only — no ledger data.
2. `narrate_report(report_type, computed_result)` → returns a plain-language
   description of the already-computed figures. It is given only the
   final computed numbers (the same object the direct REST endpoint
   returns) — never raw `journal_entries` rows, and never asked to
   calculate anything itself.
No OpenAI Agents SDK function-tool-calling (`Agent(tools=[...])`) is
introduced; both calls are plain `Agent` + `Runner.run` single completions,
identical in shape to every existing `*_tools.py` module in this codebase.
**Rationale**: This is a materially simpler design than giving one agent
four callable tools and letting it decide which to invoke, while satisfying
the exact same requirement (FR-007: the chat path resolves to the same
deterministic calculation and produces identical figures to a direct
request) — because the backend, not the model, is what actually calls
`reporting_service.py`. Every existing AI integration in this codebase uses
the single-shot-JSON pattern; introducing real SDK tool-calling machinery
here would be the first of its kind with no functional requirement forcing
that added complexity (Principle VI).
**Alternatives considered**: A single LLM call that receives the question
and is trusted to both pick the report *and* state the figures (rejected
outright — this is precisely the "LLM computes/states a number itself"
failure mode FR-001 exists to prevent); real Agents SDK function-tool
calling with one tool per report (rejected — strictly more moving parts for
the same outcome; nothing in the spec requires the model to chain multiple
tool calls or reason across tools, only to classify one request and later
narrate one result).

## Decision: Direct REST endpoints live alongside the existing `agent` router

**Decision**: The four direct report endpoints get a new
`backend/src/api/reports.py` router (`GET /api/reports/trial-balance`,
`/profit-and-loss`, `/balance-sheet`, `/cash-flow`). The one
natural-language endpoint (`POST /api/agent/reports/query`) is added to
the existing `backend/src/api/agent.py`, not a new router.
**Rationale**: `api/agent.py` is already this codebase's single home for
every agent-mediated endpoint (`parse`, `parse-receipt`); the four direct
report endpoints are plain data-retrieval, not agent-mediated, so they get
their own resource-oriented router the same way `api/ledger.py` and
`api/reconciliation.py` did for their non-agent endpoints.
**Alternatives considered**: Putting all five new endpoints under
`api/reports.py` including the natural-language one (rejected — would
split agent-mediated endpoints across two files with no clear rule for
which file a future agent-mediated endpoint belongs in; keeping "anything
agent-mediated goes in `api/agent.py`" as a single, consistent rule is
simpler to maintain).

## Outstanding item carried to Complexity Tracking / tasks

Per Constitution Check, the workflow diagram (`docs/workflow-diagram.drawio`,
Principle V) must be updated to include the `resolve_report_request` and
`narrate_report` tools and the new reporting flow before this feature's PR
merges — carried forward as an explicit task in `tasks.md`.
