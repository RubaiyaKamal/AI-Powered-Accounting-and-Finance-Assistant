# Phase 1 Data Model: Audit & Anomaly Detection

Derived from the Key Entities section of `spec.md` and the storage
decisions in `research.md`. Two new tables — `audit_runs` and
`anomaly_flags` — both real, enforced foreign keys where they reference
existing data, following `004-bank-reconciliation`'s precedent (a flag,
like a `Match`, is an operational annotation rather than itself a
financial posting, so it doesn't need `002`'s deliberately non-enforced-FK
survive-deletion treatment).

## AuditRun

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `start` | date | not null | the resolved start of the evaluated range (after defaulting — `research.md`) |
| `end` | date | not null | the resolved end of the evaluated range |
| `entries_evaluated` | integer | not null | how many active posted journal entries fell in `[start, end]` |
| `entries_flagged` | integer | not null | how many of those were flagged; `0` for a clean run |
| `status` | enum(`completed`, `insufficient_data`) | not null | `insufficient_data` when `entries_evaluated` was below the minimum threshold (`research.md`) — detection did not run, `entries_flagged` is `0` |
| `created_at` | timestamptz | not null, default now() | when the run was triggered |

**Relationships**: has many `AnomalyFlag` rows (one per entry flagged in
this run; empty for a clean or `insufficient_data` run).

## AnomalyFlag

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `audit_run_id` | FK → AuditRun.id, `ON DELETE CASCADE` | not null | which run produced this flag |
| `journal_entry_id` | FK → JournalEntry.id, `ON DELETE CASCADE` | not null | the flagged entry |
| `score` | numeric | not null | the `IsolationForest` anomaly score, normalized so **higher = more anomalous**; entries flagged only by a rule check (not the model) still get a score for consistent ranking (`research.md`) |
| `reason_categories` | array of text | not null, at least one element | e.g. `["unusual_amount"]`, `["round_number", "duplicate_looking"]` — every signal that fired for this entry (FR-004) |
| `explanation` | text | not null | plain-language explanation from `explain_flags` (or its deterministic fallback) — always present by the time a run's results are returned, never generated lazily on read |
| `resolution` | enum(`unreviewed`, `confirmed_issue`, `false_positive`, `no_action_needed`) | not null, default `unreviewed` | FR-006 |
| `resolved_at` | timestamptz | nullable | set when `resolution` moves away from `unreviewed` |
| `created_at` | timestamptz | not null, default now() | |

**Validation rules**:
- `reason_categories` MUST contain at least one recognized category
  (`unusual_amount`, `round_number`, `duplicate_looking`,
  `unusual_account_pairing`, `unusual_timing`) — enforced at the
  application layer when the detector constructs each flag, since Postgres
  array columns don't natively constrain element values.

**Relationships**: belongs to exactly one `AuditRun`; references exactly
one `JournalEntry` (not exclusive — the same entry could, in principle, be
flagged again in a later, overlapping audit run; each run's flag is its
own row with its own resolution, per spec's "previously reviewed flags
show their resolution, not appear as new" edge case being about *that
run's* flag, not a cross-run identity merge).

**State transitions**:
1. An `AuditRun` is created with `status=insufficient_data` and zero
   `AnomalyFlag` rows when `entries_evaluated` is below the minimum
   threshold (FR-008, spec Edge Cases).
2. Otherwise, an `AuditRun` is created with `status=completed`;
   `audit_service.py` computes zero or more `AnomalyFlag` rows in the same
   request (detection → batched narration → persist run + flags
   together), each starting with `resolution=unreviewed`.
3. An admin resolves a flag (US2, FR-006) by updating its `resolution` to
   `confirmed_issue`, `false_positive`, or `no_action_needed` and setting
   `resolved_at` — this is the only mutation an `AnomalyFlag` ever
   undergoes; nothing about the flag's score, reasons, or explanation
   changes after creation, preserving the audit-trail edge case (a flag on
   an entry later reversed by the ledger's correction flow keeps its
   original score/reasons/explanation as historical record — the frontend
   distinguishes "entry no longer active" by checking the referenced
   `JournalEntry.status` at display time, not by mutating the flag).
