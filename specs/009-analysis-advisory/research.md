# Phase 0 Research: Analysis & Advisory / Natural-Language Q&A

The backend/frontend/database/AI stack is fixed by the constitution and
already established by prior features — no `NEEDS CLARIFICATION` markers
remain in Technical Context. This document records the feature-scoped
design decisions: how questions are resolved into safe, deterministic
computation, how forecasting works, and how the AI's role stays bounded.

## Decision: bounded classify-then-compute — not free-form LLM-authored SQL

**Decision**: A single narrow LLM call (`resolve_spending_request`)
classifies a question into one of four fixed request kinds — `amount`,
`breakdown`, `comparison`, `forecast` — plus its parameters (an account
name, drawn only from the real chart of accounts given in the prompt, and
one or two date periods). The classification result is handed to plain
Python functions in `analysis_service.py` that compute the actual figures
deterministically. The LLM never sees raw ledger rows, never constructs a
SQL query, and never states a number itself.
**Rationale**: The user's request named "text-to-SQL" as the method, but
letting an LLM freely author SQL per question is a materially different
risk profile than anything else in this codebase: even a "successful,"
non-hallucinated query can still be subtly *wrong* (a missed `WHERE
status='posted'`, a forgotten exclusion of reversed entries, an
off-by-one date boundary) and still return a real, deterministically-
computed-by-Postgres number that is nonetheless incorrect — the exact
failure mode this project has structurally avoided by writing the
"active postings only" filter exactly once (`002`'s
`active_journal_entry()`) and reusing it verbatim in every later feature
(`005`, `007`, `008`) rather than re-deriving it. A fresh LLM-authored
query per question would reintroduce that risk on every single request.
Classifying into a small, fixed set of *pre-written, pre-tested*
computations keeps every actual number's correctness independent of what
the LLM produces, satisfying Principle II in the same way every other
feature in this codebase already does.
**Alternatives considered**: Free-form LLM-authored SQL, executed
read-only against the database (the literal reading of the Input's
"text-to-SQL" phrasing) — rejected for the reason above. A general
retrieval-augmented approach dumping raw ledger rows into the prompt for
the LLM to reason over — rejected outright, this is precisely "the LLM
computes a figure itself," the one thing Principle II exists to prevent.

## Decision: every figure comes from `ReportingService.profit_and_loss`

**Decision**: The single-account amount, the breakdown, the comparison,
and each historical data point feeding the forecast are all derived from
calling the existing `reporting_service.profit_and_loss(session, start,
end)` — specifically its `expense_lines` (per-account totals) and
`total_expenses` fields. No new aggregation query is written.
**Rationale**: This computation already exists, is already deterministic,
and is already exercised by `005-reporting`. A breakdown is simply
`expense_lines` sorted by balance; a single-account amount is one line
from that same list; a comparison is two calls diffed; a forecast's
training data is a short series of `total_expenses` values from several
calls. Reusing it rather than writing parallel aggregation logic is
directly what Principle VI calls for, and it means this feature's numbers
can never drift from what `/api/reports/profit-and-loss` would show for
the same period — there is only one code path that sums a journal entry.
**Alternatives considered**: A new dedicated aggregation function for
"spending by account" — rejected, `profit_and_loss`'s `expense_lines`
already computes exactly this; writing a second version would violate
Principle VI and create two places that could silently disagree.

## Decision: account-name resolution bounded to the real chart of accounts

**Decision**: When `resolve_spending_request` is given a question, its
prompt includes the actual list of expense account names from the chart
of accounts, and it is instructed to reply with one of those names
verbatim, or `null` if none clearly matches — the exact same
constrained-choice pattern `002-ledger-journal-entries`'s
`suggest_account_coding` already established for matching an expense
description to an account.
**Rationale**: This is what makes FR-005 (never fabricate an account)
enforceable by construction rather than by hoping the LLM behaves: the
model is never in a position to invent an account name, because it can
only select from a list it was actually given. If it returns `null` for
an `amount`-kind request, the service layer reports "no such account"
(FR-005) rather than presenting a zero or invented figure.
**Alternatives considered**: Letting the LLM emit any account name it
infers from the question and validating it against the database
afterward — functionally similar in outcome but strictly worse: it
invites a widening gap between "what the model said" and "what actually
exists," rather than bounding the model's choice space up front.

## Decision: forecasting via linear regression over a fixed recent-months window

**Decision**: A forecast fits `scikit-learn`'s `LinearRegression` (a
single feature: month index) against `total_expenses` from up to the
past 6 complete calendar months (via repeated `profit_and_loss` calls),
then predicts the requested future month. At least 3 of those months
must have posted activity for a fit to be attempted; below that, the
system reports there isn't enough data yet (FR-009) rather than fitting a
line through one or two points.
**Rationale**: `scikit-learn` is already a dependency (added for `007`'s
anomaly detector) — no new package. At this project's realistic scale (a
small business's month-by-month history, realistically a handful to a
few dozen months), a simple linear trend is an honest, explainable
estimate; a heavier time-series method (`statsmodels`'s ARIMA, seasonal
decomposition, `prophet`) would add real complexity and a new dependency
for a benefit (capturing seasonality, autocorrelation) this project's
typical data volume is too short to make meaningful. 6 months balances
having enough points to fit a trend against not overweighting stale,
long-past spending patterns; 3 months is a conservative floor below which
a linear fit is more noise than signal — both are implementation-level
defaults, not business-scope decisions.
**Alternatives considered**: `statsmodels`/ARIMA or `prophet` (rejected —
new dependencies, complexity, and modeling assumptions this project's
data volume doesn't support); a naive "same as last month" or
moving-average projection (rejected as the *sole* method — doesn't
capture a rising/falling trend the way regression does, though the
underlying data — recent months' actual totals — is the same either way);
an unbounded lookback window using all history (rejected — over-weights
very old spending patterns that may no longer be representative of the
business's current trajectory).

## Decision: single NL endpoint covers all four request kinds; no direct REST for "amount"

**Decision**: `POST /api/agent/analysis/query` handles all four request
kinds (amount, breakdown, comparison, forecast) via
`resolve_spending_request` + `narrate_spending_result`. Breakdown,
comparison, and forecast additionally get direct REST endpoints under a
new `api/analysis.py` router (per FR-006/FR-007's explicit "directly"
requirement); the single-account amount request kind does not, since
spec.md's User Story 1 and FR-001 describe it only as a natural-language
capability, with no acceptance scenario asking for a form-based
equivalent.
**Rationale**: Matches spec's actual scope rather than over-building a
redundant direct "get one account's total for a period" endpoint nothing
in the spec asks for — Principle VI. `resolve_spending_request` naturally
can't be fully written (its prompt needs to describe all four kinds and,
for `breakdown`/`comparison`/`forecast`, be tested against real
computation functions) until `analysis_service.py`'s functions for all
four kinds exist — mirroring `005-reporting`'s Phase 7 note about why its
own cross-cutting NL resolver couldn't be built before all its report
functions existed.
**Alternatives considered**: A direct `GET /api/analysis/amount`
endpoint mirroring the other three — rejected, not requested by any
functional requirement; adding it would be speculative scope beyond what
the spec calls for.

## Decision: period defaults mirror the direct-request defaults; only kind/account ambiguity triggers a clarifying question

**Decision**: When a natural-language request's kind is clearly
determinable but no period is stated, the period defaults the same way
the corresponding direct endpoint would (current calendar month) rather
than triggering FR-004's clarifying-question path. A clarifying question
is reserved for when the request kind itself can't be determined, or (for
an `amount`-kind request) when no real account can be matched.
**Rationale**: FR-004 says a clarifying question is needed when "the
intended account/category *or period* can't be determined" — but for
breakdown/comparison/forecast, an *unstated* period already has a
well-defined, spec-sanctioned default (current month), so it *has* been
determined, just implicitly. Treating every omitted period as
unresolvable would make the natural-language path stricter and less
useful than the direct forms it's supposed to mirror (FR-010's
"identical figures" requirement), and would contradict `005-reporting`'s
established default-period precedent that this spec's own Assumptions
section explicitly opts into.
**Alternatives considered**: Always requiring an explicit period in
natural language (rejected — makes the chat path needlessly stricter
than the direct forms for no stated reason); silently defaulting even
when the request *kind* itself is unclear (rejected — this is exactly
what FR-004 exists to prevent, and mirrors `007`/`008`'s established
"don't guess the thing you can't tell" behavior for genuinely ambiguous
requests).
