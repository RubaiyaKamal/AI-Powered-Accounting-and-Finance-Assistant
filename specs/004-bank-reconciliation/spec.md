# Feature Specification: Bank/Vendor Reconciliation

**Feature Branch**: `004-bank-reconciliation`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Bank/vendor reconciliation: allow an admin to bring in a bank statement's transaction lines and have the system automatically match them against existing recorded expense entries by amount, date, and description similarity (embedding/fuzzy matching). Confident matches are marked automatically; ambiguous near-matches are adjudicated by an LLM that explains its reasoning, and anything still unmatched is surfaced in a review queue rather than silently resolved or auto-matched."

## Clarifications

### Session 2026-07-28

- Q: How are bank transaction lines brought into the system? → A: Uploading a bank statement file (CSV) — not manual line-by-line entry.
- Q: Can an imported bank transaction line be edited or deleted afterward? → A: No — immutable once imported; a data-entry error is fixed by correcting the source file and re-importing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import bank statement transactions (Priority: P1)

An admin brings the transaction lines from a bank statement into the
system so they can be reconciled against the expenses already recorded.

**Why this priority**: Nothing else in this feature can happen without
bank transaction data existing in the system first.

**Independent Test**: Can be fully tested by importing a set of bank
transaction lines (date, amount, description) and confirming they appear
in the system, unmatched, ready for reconciliation.

**Acceptance Scenarios**:

1. **Given** a set of bank transaction lines, **When** the admin imports
   them, **Then** each line is recorded with its date, amount, and
   description, and starts in an unmatched state.
2. **Given** a bank transaction that is identical (same date, amount, and
   description) to one already imported, **When** the admin attempts to
   import it again, **Then** the system detects the duplicate and does not
   create a second copy.

---

### User Story 2 - Automatic matching of confident pairs (Priority: P2)

Once bank transactions are imported, the system automatically pairs each
one with the expense entry it clearly corresponds to, without requiring
the admin to review every single line.

**Why this priority**: This is the core time-saving value of
reconciliation — most transactions in a real reconciliation are
unambiguous and shouldn't need manual review. It depends on US1 (there
must be bank transactions to match).

**Independent Test**: Can be fully tested by importing a bank transaction
that clearly corresponds to an existing expense entry (matching amount,
close date, similar description) and confirming the system marks both as
matched to each other automatically.

**Acceptance Scenarios**:

1. **Given** an imported bank transaction whose amount, date, and
   description closely match exactly one existing expense entry, **When**
   matching runs, **Then** the system marks them as matched to each other
   without requiring admin confirmation.
2. **Given** two bank transactions with similarly strong matches to two
   different expense entries, **When** matching runs, **Then** neither
   expense entry is matched to more than one bank transaction (and vice
   versa) — matches are always one-to-one.
3. **Given** a bank transaction with no plausible corresponding expense
   entry at all, **When** matching runs, **Then** it is left unmatched
   rather than forced into an incorrect match.

---

### User Story 3 - Review ambiguous and unmatched transactions (Priority: P3)

For bank transactions the system couldn't confidently auto-match — either
because multiple expense entries are plausible candidates or because none
are — the admin reviews a queue, sees the AI's reasoning for any ambiguous
candidates it considered, and resolves each one.

**Why this priority**: Completes the reconciliation workflow — automatic
matching (US2) alone would leave genuinely ambiguous or missing data
silently unresolved, which is worse than surfacing it for a human
decision. Depends on US1 and US2 already existing.

**Independent Test**: Can be fully tested by triggering a reconciliation
pass that produces at least one ambiguous and one fully unmatched
transaction, then confirming both appear in a review queue with the
ambiguous one showing the AI's reasoning, and that resolving each (confirm
a suggested match, pick a different expense entry, or dismiss as having no
corresponding expense entry) removes it from the queue.

**Acceptance Scenarios**:

1. **Given** a bank transaction with two or more plausible candidate
   expense entries, **When** matching runs, **Then** it appears in the
   review queue along with the AI's explanation of which candidate(s) it
   considered and why none was confident enough to auto-match.
2. **Given** a bank transaction with no plausible candidate at all,
   **When** matching runs, **Then** it appears in the review queue without
   a suggested match.
3. **Given** an item in the review queue, **When** the admin confirms a
   suggested match, selects a different expense entry, or dismisses it
   (e.g., a bank fee with no corresponding expense entry), **Then** the
   item is resolved and no longer appears in the queue on subsequent
   reconciliation passes.
4. **Given** a confirmed match (automatic or manual), **When** the admin
   views it later, **Then** they can undo it, returning both the bank
   transaction and the expense entry to an unmatched state.

---

### Edge Cases

- What happens when the expense entry a bank transaction was matched to is
  later deleted? The match is broken and the bank transaction returns to
  the review queue rather than silently pointing at nothing.
- What happens when the bank amount and the expense amount differ slightly
  (e.g., a bank fee was deducted)? Treated as, at best, an ambiguous
  candidate for AI adjudication — never auto-matched on a partial amount.
- What happens when an admin tries to confirm a match for a bank
  transaction or expense entry that has already been matched to something
  else? The system rejects it — matches are always one-to-one (FR-010).
- What happens when no expense entries exist yet at all? Every imported
  bank transaction lands directly in the review queue as fully unmatched;
  the system does not error.
- What happens when the uploaded CSV has a malformed or unparseable row
  (missing amount, unreadable date)? That row is rejected with a clear
  reason and the rest of the file's valid rows are still imported — one
  bad row does not fail the entire upload.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to bring bank transaction lines (date,
  amount, description) into the system for reconciliation.
- **FR-002**: Users MUST be able to bring bank transaction lines into the
  system by uploading a bank statement file (CSV), rather than entering
  each line by hand.
- **FR-003**: The system MUST detect and skip an exact duplicate of an
  already-imported bank transaction (same date, amount, and description)
  rather than creating a second copy.
- **FR-004**: For each imported bank transaction, the system MUST attempt
  to identify a matching expense entry using amount, date, and description
  similarity.
- **FR-005**: When exactly one expense entry is a confident match for a
  bank transaction, the system MUST mark them as matched automatically,
  without requiring admin review.
- **FR-006**: When multiple expense entries are plausible but no single
  one is confident enough to auto-match, the system MUST have the AI
  adjudicate between the candidates and record its reasoning for the admin
  to review, rather than guessing or auto-matching the top candidate.
- **FR-007**: A bank transaction with no plausible matching expense entry
  MUST be placed in a review queue rather than left unresolved with no
  visibility or forced into an incorrect match.
- **FR-008**: Users MUST be able to view the review queue and, for each
  item, confirm a suggested match, select a different expense entry, or
  dismiss it as having no corresponding expense entry.
- **FR-009**: Once an item in the review queue is resolved (confirmed,
  matched, or dismissed), the system MUST NOT re-surface it in future
  reconciliation passes.
- **FR-010**: A bank transaction and an expense entry MUST each be matched
  to at most one counterpart at a time (one-to-one matching) — the system
  MUST reject an attempt to match either side to more than one
  counterpart.
- **FR-011**: Users MUST be able to view which bank transactions are
  matched to which expense entries, and undo a previously confirmed match,
  returning both sides to an unmatched state.
- **FR-012**: Once imported, a bank transaction line's date, amount, and
  description MUST be treated as immutable — the system MUST NOT provide a
  way to edit them. A data-entry error is corrected by fixing the source
  bank statement file and re-importing (FR-003's duplicate detection
  applies to the corrected re-import).
- **FR-013**: When the expense entry side of a confirmed match is later
  deleted, the system MUST return the bank transaction to the review queue
  rather than leave the match pointing at a nonexistent entry (Edge
  Cases).

### Key Entities *(include if feature involves data)*

- **Bank Transaction**: A single line brought in from a bank statement,
  with a date, an amount, and a description. Starts unmatched; may become
  matched (automatically or by admin confirmation) to exactly one Expense
  Entry, or dismissed as having no corresponding entry.
- **Match**: The link between a Bank Transaction and an Expense Entry,
  including whether it was created automatically or by admin confirmation,
  and — for matches that went through AI adjudication — the reasoning
  recorded for the admin (FR-006).

### Assumptions

- Reconciliation matches bank transactions against `Expense Entry` records
  from `001-expense-entry`, not against posted ledger journal entries from
  `002-ledger-journal-entries` — an expense entry doesn't need to have gone
  through account coding/posting to be reconciled. Ledger-level (cash
  account movement) reconciliation is a possible future refinement, not
  part of this feature's scope.
- Matching is strictly one-to-one: a single bank transaction covering
  multiple expense entries (or vice versa) — e.g., a bulk bank withdrawal
  covering several recorded expenses — is out of scope; each such case
  would surface as unmatched/ambiguous for manual handling rather than
  being auto-split.
- Single business, single admin user, single currency — same assumptions
  as prior features in this project.
- The specific confidence threshold that separates "auto-match" from
  "route to AI adjudication" from "no plausible candidate at all" is an
  implementation detail (like `002-ledger-journal-entries`'s coding
  confidence threshold), not a business-scope decision, and does not
  require its own clarification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 80% of bank transactions that have a clear
  corresponding expense entry are matched automatically, with no admin
  action required.
- **SC-002**: 100% of bank transactions that aren't confidently
  auto-matched are visible in the review queue — none are silently
  dropped or left unresolved with no visibility.
- **SC-003**: An admin can resolve a review queue of a typical month's
  worth of ambiguous/unmatched transactions (a few dozen) in under 15
  minutes.
- **SC-004**: 0% of bank transactions or expense entries end up matched to
  more than one counterpart at the same time.
