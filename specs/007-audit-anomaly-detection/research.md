# Phase 0 Research: Audit & Anomaly Detection

The backend/frontend/database/AI stack is fixed by the constitution and
already established by prior features — no `NEEDS CLARIFICATION` markers
remain in Technical Context. This document records the feature-scoped
design decisions: which detection method to use, how signals combine, how
the AI's explanatory role is bounded, and how the persisted audit-run
history fits the existing codebase patterns.

## Decision: `scikit-learn`'s `IsolationForest`, combined with rule-based checks

**Decision**: Anomaly detection is a hybrid of two layers computed
entirely in `audit_service.py`: (1) `scikit-learn`'s `IsolationForest`
scores each evaluated journal entry on a numeric feature vector (amount,
one-hot encoded debit/credit account pair, day-of-week, day-of-month), and
(2) two deterministic rule checks — exact-duplicate detection (same
amount, date, and account pair as another entry in the same evaluated set)
and round-number detection (amount is an exact multiple of a round unit,
e.g. 100) — run independently. An entry is flagged if either layer
signals it; its reason categories list every signal that fired, and its
rank is driven by the `IsolationForest` score (with rule-flagged entries
guaranteed inclusion regardless of score).
**Rationale**: The user's request named "Isolation Forest, clustering" as
example methods and explicitly referenced real general-ledger anomaly
tools (EY Helix GL Anomaly Detector, MindBridge) as the model to follow —
those tools are themselves known to combine statistical/ML scoring with
rule-based heuristics (duplicate postings, round-dollar amounts, threshold
patterns), not ML alone. `IsolationForest` is purpose-built for exactly
this shape of problem: unsupervised outlier scoring over small-to-medium
tabular data, without needing labeled fraud examples (none exist for this
project — see spec Assumptions), and it naturally captures multivariate
patterns (an unremarkable amount on an unusual account, or at an unusual
time) that a single-variable threshold check would miss. Exact-duplicate
and round-number detection are added as explicit rules because an outlier
detector systematically under-flags them: two identical entries reinforce
each other's "normalcy" to a novelty detector rather than standing out,
and a round number is only weakly distinguishable in a numeric feature
space unless checked directly.
**Alternatives considered**: Pure rule-based statistics (per-account
z-score/MAD thresholds) as the sole method — rejected as insufficient
alone: doesn't capture combined/multivariate patterns the way
`IsolationForest` does, and doesn't satisfy the feature's explicit
ML-based-detection requirement (FR-001). Clustering (e.g., DBSCAN, treating
low-density points as outliers) — considered, since the user's request
named it as an example too, but rejected as the *primary* technique in
favor of `IsolationForest`: DBSCAN's outlier behavior is sensitive to its
distance/epsilon parameter, which is unstable to tune well with the
modest, evolving data volumes typical of a small business's ledger, while
`IsolationForest`'s main parameter (`contamination`, the expected outlier
fraction) maps directly and stably onto this feature's own FR-005 ("bound
how many entries get flagged"). ML-only scoring with no rule layer —
rejected per the rationale above (misses duplicates/round-numbers, both
well-established, cheap-to-check audit heuristics).

## Decision: fit the model fresh per audit run — no persisted/retrained model

**Decision**: Each audit run fits a new `IsolationForest` on that run's
own evaluated entry set (with a fixed random seed for reproducibility) and
discards it — no trained model is persisted, versioned, or reused across
runs.
**Rationale**: At this project's realistic scale (a small business's full
ledger history — low thousands of rows at most), fitting a fresh
`IsolationForest` is a sub-second operation, so there's no performance
reason to persist one. Persisting/reusing a model would add real
complexity (retraining cadence, drift detection, model versioning tied to
schema/feature changes) that Principle VI (Simplicity) weighs against, for
a benefit (avoiding a cheap re-fit) that doesn't materialize at this
scale. What "normal" looks like can also legitimately shift as a business
grows, so re-deriving it fresh per run is arguably more correct, not just
simpler.
**Alternatives considered**: A single persisted, periodically-retrained
model — rejected as premature complexity with no scale justification;
introduces model-lifecycle questions (when to retrain, how to detect
staleness) this feature doesn't need to answer yet.

## Decision: which journal entries are evaluated — active postings only

**Decision**: Every audit run evaluates only
`JournalEntry.status == "posted" AND JournalEntry.reverses_journal_entry_id IS NULL`
— the same "currently active, non-reversal, non-reversed posting"
definition established in `002` (`ledger_service.active_journal_entry()`)
and reused verbatim in `005`'s reporting aggregations.
**Rationale**: A reversed entry and its reversal are a matched pair whose
purpose is to cancel each other out; including either independently would
seed the model with data that's no longer in effect and could itself
generate a spurious flag, directly violating FR-010. Reusing the
established filter is both correct and consistent with the rest of the
codebase.
**Alternatives considered**: None seriously — this is the codebase-wide
rule for "which entries count," already validated by two prior features.

## Decision: one batched LLM narration call per audit run, not one per flag

**Decision**: `explain_flags(flagged_entries)` — a single LLM call that
receives the whole list of already-flagged entries (each with its reason
categories and the underlying data that triggered them) for one audit run,
and returns a plain-language explanation for each. `resolve_audit_request`
(the natural-language entry point) is a second, separate narrow LLM call,
following the same two-call shape `005-reporting` established
(`resolve_report_request` / `narrate_report`).
**Rationale**: Batching keeps total added latency to one LLM round-trip
per audit run regardless of how many entries it flags, which is what
makes spec's SC-001 (a result within 30 seconds) reliably achievable —
one call per flag would multiply latency roughly linearly with flag count
and risk missing that target on any run with several flags. This mirrors
`narrate_report`'s "narrate the whole already-computed result" pattern,
generalized from one result object to a list of them.
**Alternatives considered**: One `explain_flag` call per flagged entry —
rejected for the latency reason above; also more LLM calls for no
accuracy benefit, since every call receives the same kind of
already-computed, per-entry signal data either way.

## Decision: minimum data threshold before running detection

**Decision**: An audit run requires at least 20 posted (active) journal
entries in the requested range (or across the whole ledger, if no range is
given) before attempting detection. Below that, the system returns an
explicit "not enough data yet" result and does not run the detector or
produce any flags.
**Rationale**: An unsupervised outlier detector needs a reasonable sample
to establish what "normal" looks like; scoring a handful of entries would
produce arbitrary, low-confidence flags that look authoritative but
aren't, directly violating FR-008 and the spec's low-data edge case. 20 is
a conservative, implementation-level default (not a business-scope
decision) — enough for `IsolationForest` to have more than one "similar"
entry per feature combination in a small chart of accounts.
**Alternatives considered**: No minimum (always attempt detection) —
rejected, produces misleading flags on sparse data. A much higher
threshold (e.g., 200) — rejected as unrealistic for a small business's
early ledger history, which would leave the feature unusable for months
after adoption.

## Decision: direct REST endpoints live alongside the existing `agent` router

**Decision**: Direct audit endpoints get a new `backend/src/api/audit.py`
router (`POST /api/audit/runs`, `GET /api/audit/runs`,
`GET /api/audit/runs/{id}`, `PATCH /api/audit/flags/{id}`). The one
natural-language endpoint (`POST /api/agent/audit/query`) is added to the
existing `backend/src/api/agent.py`, not a new router.
**Rationale**: Identical reasoning to `005-reporting`'s research.md:
`api/agent.py` is this codebase's single home for every agent-mediated
endpoint; the direct audit endpoints are plain data operations (trigger a
detection pass, read results, record a resolution), so they get their own
resource-oriented router the same way `api/reports.py` and
`api/reconciliation.py` did.
**Alternatives considered**: Putting all endpoints under `api/audit.py`
including the natural-language one — rejected for the same consistency
reason `005` already established.
