# Feature Specification: Expense Entry

**Feature Branch**: `001-expense-entry`
**Created**: 2026-07-27
**Status**: Draft
**Input**: User description: "Expense entry: allow a user to create, view, edit, and delete daily expense records (amount, date, category, description), including natural-language entry creation (e.g. \"add a 5000 electricity bill for July\") and AI-assisted auto-categorization of uncategorized entries."

## Clarifications

### Session 2026-07-27

- Q: Should categories come from a fixed, predefined list that the admin cannot extend, or should the admin be able to create new custom categories on the fly? → A: Predefined starter list (e.g. Utilities, Rent, Salaries, Supplies) that the admin can extend with custom categories.
- Q: Is field-level edit history required for expense entries now, or is storing only current state sufficient, deferring change-auditing to the later audit feature? → A: Track full field-level edit history (what changed, old→new value, when) from the start.
- Q: When natural-language parsing can't determine a required field, should the assistant ask a clarifying follow-up question in the same chat turn, or fall back to opening the manual entry form pre-filled with whatever it could parse? → A: Ask a clarifying follow-up question in the same chat turn.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record an expense manually (Priority: P1)

An office admin sitting down to do daily bookkeeping records a new expense by
filling in an amount, a date, a category, and an optional short description.

**Why this priority**: This is the most basic bookkeeping action in the whole
system — without it, nothing else (reports, audits, Q&A) has any data to work
from. It must work before anything else is worth building.

**Independent Test**: Can be fully tested by submitting a new expense with an
amount, date, and category, and then confirming it appears in the expense
list with exactly those values — no other feature is required.

**Acceptance Scenarios**:

1. **Given** the expense entry form, **When** the admin enters a positive
   amount, a valid date, and a category, and submits, **Then** a new expense
   entry is saved and appears in the list of entries.
2. **Given** the expense entry form, **When** the admin submits with a
   negative or zero amount, **Then** the system rejects the submission and
   explains why, and no entry is saved.
3. **Given** the expense entry form, **When** the admin leaves the amount or
   date blank, **Then** the system rejects the submission and indicates which
   field is missing.

---

### User Story 2 - View, edit, and delete existing expenses (Priority: P2)

The admin reviews previously recorded expenses, corrects a mistake (wrong
amount, wrong category), or removes an entry that was recorded in error.

**Why this priority**: Bookkeeping data is never perfect on first entry;
without the ability to correct or remove entries, every mistake becomes
permanent and reports built on top of this data are untrustworthy.

**Independent Test**: Can be fully tested by creating an entry, editing one of
its fields and confirming the change is saved, then deleting it and
confirming it no longer appears in the list.

**Acceptance Scenarios**:

1. **Given** a list of existing expense entries, **When** the admin filters by
   a date range and/or a category, **Then** only matching entries are shown.
2. **Given** an existing expense entry, **When** the admin edits its amount,
   date, category, or description and saves, **Then** the entry reflects the
   updated values everywhere it is shown, and the prior value is retained in
   that entry's edit history.
3. **Given** an existing expense entry, **When** the admin deletes it,
   **Then** it no longer appears in the expense list or in any subsequent
   report calculations.
4. **Given** an existing expense entry with prior edits, **When** the admin
   views the entry, **Then** its edit history (field, old value, new value,
   when) is available to view.

---

### User Story 3 - Record an expense using natural language (Priority: P3)

The admin types a plain-language sentence such as "add a 5000 electricity
bill for July" into the assistant, instead of filling out the structured
form, and the system creates the equivalent expense entry.

**Why this priority**: This is the feature's core AI differentiator over a
plain bookkeeping form, but it depends on User Story 1 already existing
(the same underlying entry-creation capability, just reached a different way).

**Independent Test**: Can be fully tested by sending a single natural-language
sentence containing an amount, a date, and an implied category, and
confirming an expense entry with the corresponding parsed values is created
after the admin confirms it.

**Acceptance Scenarios**:

1. **Given** a natural-language request that clearly states an amount, a
   date (or a date that can be reasonably inferred, e.g. "for July"), and a
   category or description, **When** the admin sends it, **Then** the system
   shows the admin the parsed amount, date, and category and asks for
   confirmation before saving.
2. **Given** the system has shown a parsed entry for confirmation, **When**
   the admin confirms, **Then** the entry is saved exactly as shown; **When**
   the admin instead corrects a field, **Then** the entry is saved with the
   corrected value, not the originally parsed one.
3. **Given** a natural-language request missing a required field (e.g. no
   amount), **When** the admin sends it, **Then** the system asks a specific
   follow-up question for the missing field instead of guessing or silently
   rejecting the request.

---

### User Story 4 - Get an AI-suggested category for an entry (Priority: P4)

When the admin records an expense (manually or via natural language) without
specifying a category, the system suggests one based on the description.

**Why this priority**: Improves data quality and saves time, but the system
is still useful without it (the admin can always pick a category manually) —
this is an enhancement on top of Stories 1–3, not a blocker for them.

**Independent Test**: Can be fully tested by submitting an entry with a
description but no category and confirming a suggested category is shown and
can be accepted or overridden in a single action.

**Acceptance Scenarios**:

1. **Given** an entry submitted without a category but with a description,
   **When** it is saved, **Then** the system attaches a suggested category
   and visibly marks it as AI-suggested rather than user-chosen.
2. **Given** an AI-suggested category on an entry, **When** the admin picks a
   different category, **Then** the entry's category is updated and it is no
   longer marked as AI-suggested.

---

### Edge Cases

- What happens when the admin enters an amount with excessive decimal
  precision or an implausibly large value (likely a typo, e.g. an extra
  zero)? The system should flag it for confirmation rather than silently
  accepting it.
- What happens when a natural-language request describes an expense dated in
  the future? The system should accept it (planned/scheduled expenses are
  valid) but the entry should be clearly distinguishable from past expenses.
- What happens when the admin tries to filter by a date range where the end
  date is before the start date? The system should reject the filter with a
  clear message rather than returning an empty or misleading result.
- What happens when two entries look like accidental duplicates (same
  amount, date, and category entered twice)? The system should still save
  both (duplicate detection is an audit-time concern, not an entry-time
  restriction — see the audit feature) but should not silently merge them.
- What happens when the admin deletes an entry that was already used in a
  previously generated report? The report already generated is not
  retroactively changed; only future report generation reflects the deletion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create an expense entry consisting of an
  amount, a date, a category, and an optional free-text description.
- **FR-002**: The system MUST reject an expense entry whose amount is zero or
  negative, with a clear explanation of why it was rejected.
- **FR-003**: The system MUST reject an expense entry that is missing a
  required field (amount or date) and indicate which field is missing.
- **FR-004**: Users MUST be able to view a list of their expense entries,
  filterable by date range and by category.
- **FR-005**: Users MUST be able to edit any field of an existing expense
  entry, and the updated values MUST be reflected everywhere the entry is
  used.
- **FR-006**: Users MUST be able to delete an existing expense entry; deleted
  entries MUST be excluded from all future report calculations.
- **FR-007**: Users MUST be able to create an expense entry by submitting a
  natural-language description instead of using the structured form.
- **FR-008**: When creating an entry from natural language, the system MUST
  show the admin the parsed amount, date, and category and require explicit
  confirmation (or correction) before the entry is saved.
- **FR-009**: When a natural-language request is missing information needed
  to create a valid entry, the system MUST ask a specific follow-up question
  in the same chat turn (e.g., "What was the amount?") rather than guessing
  a value, silently discarding the request, or falling back to a separate
  form.
- **FR-010**: When an entry is submitted without an explicit category, the
  system MUST suggest one based on the entry's description, visibly marked
  as AI-suggested.
- **FR-011**: Users MUST be able to accept or override an AI-suggested
  category in a single action; overriding MUST remove the "AI-suggested"
  marker from that entry.
- **FR-012**: The system MUST persist every expense entry (and its edit
  history — see FR-015) so that entries remain available across sessions
  and are not lost on restart.
- **FR-013**: The system MUST record when each expense entry was created and
  when it was last modified.
- **FR-014**: The system MUST provide a predefined starter set of categories
  (e.g. Utilities, Rent, Salaries, Supplies) and MUST allow the admin to add
  new custom categories beyond that starter set.
- **FR-015**: The system MUST record a field-level edit history for every
  expense entry: each time a field is changed, it MUST retain the field
  name, the old value, the new value, and when the change was made.
- **FR-015a**: Users MUST be able to view an entry's edit history alongside
  the entry itself.

### Key Entities *(include if feature involves data)*

- **Expense Entry**: A single recorded expense, with an amount, a date, a
  category, an optional description, a creation timestamp, a last-modified
  timestamp, and a flag indicating whether it was created via the manual
  form or via natural language, and whether its category is AI-suggested or
  user-chosen.
- **Category**: A label used to group expense entries for reporting and
  filtering. Ships with a predefined starter set (e.g., Utilities, Rent,
  Supplies, Salaries) and is extensible — the admin can add custom
  categories beyond the starter set (FR-014).
- **Edit History Entry**: A record of a single field change on an expense
  entry — the field name, its old value, its new value, and when the change
  occurred (FR-015). Belongs to exactly one Expense Entry.

### Assumptions

- Single business, single admin user per deployment: no multi-user
  permissions or role model is in scope for this feature (matches the
  assignment's description of "an office admin or business owner").
- Single currency: no multi-currency support or conversion is in scope; all
  amounts are in one implicit local currency.
- There is no "closed accounting period" concept yet — any entry can be
  edited or deleted regardless of age. Locking finalized periods, if needed,
  is a future feature, not part of this one.
- Duplicate-looking entries (same amount/date/category) are allowed at entry
  time; flagging likely duplicates is treated as an audit-time concern
  (a separate, already-planned feature), not an expense-entry restriction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can record a new expense entry via the manual form in
  under 30 seconds.
- **SC-002**: A user can record a well-formed expense (amount, date, and
  category or description all present) via a single natural-language
  sentence, with all fields parsed correctly on the first attempt at least
  90% of the time.
- **SC-003**: A user can locate any previously recorded expense entry by
  filtering on date range or category within 10 seconds.
- **SC-004**: 100% of expense entries saved without an explicit category
  receive an AI-suggested category that the user can accept or override in a
  single action.
- **SC-005**: 0% of saved expense entries have a zero or negative amount.
