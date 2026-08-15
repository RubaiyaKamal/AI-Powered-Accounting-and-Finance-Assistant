# Feature Specification: Income Entry

**Feature Branch**: `010-income-entry`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "Minimal income entry: allow the admin to record income/revenue transactions (amount, date, source/category, optional description) so the ledger has a funding side, not just expenses. Each income entry posts a journal entry crediting a Revenue account (or an Equity/opening-capital account for non-operating income) and debiting Cash, mirroring how expense entries already debit an expense account and credit Cash. This unblocks the existing income-statement (profit-and-loss) and balance-sheet reports, which currently always show $0 revenue and an unbalanced balance sheet because there is no way to record money coming in. Scope is intentionally minimal: manual structured entry only (no natural-language parsing, no AI category suggestion) — mirror only the CRUD + ledger-posting parts of 001-expense-entry, not its AI stories."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record an income transaction manually (Priority: P1)

An office admin doing daily bookkeeping records money that came in — a sale,
a service payment, or an owner's capital contribution — by entering an
amount, a date, a source, and an optional short description.

**Why this priority**: Without this, the system can only ever record money
leaving the business (expenses). Every financial report that is supposed to
show the full picture (income statement, balance sheet) is structurally
incomplete without it — this is the single missing piece that unblocks both.

**Independent Test**: Can be fully tested by submitting a new income entry
with an amount, date, and source, then confirming it appears in the income
list with exactly those values and that the same amount now appears in the
ledger as money received — no other feature is required.

**Acceptance Scenarios**:

1. **Given** the income entry form, **When** the admin enters a positive
   amount, a valid date, and a source, and submits, **Then** a new income
   entry is saved, appears in the list of income entries, and is
   immediately reflected in the ledger (no separate approval step).
2. **Given** the income entry form, **When** the admin submits with a
   negative or zero amount, **Then** the system rejects the submission and
   explains why, and no entry is saved.
3. **Given** the income entry form, **When** the admin leaves the amount or
   date blank, **Then** the system rejects the submission and indicates
   which field is missing.

---

### User Story 2 - View, edit, and delete existing income entries (Priority: P2)

The admin reviews previously recorded income, corrects a mistake (wrong
amount, wrong source), or removes an entry that was recorded in error.

**Why this priority**: Income data is never perfect on first entry; without
correction, mistakes permanently distort the income statement and balance
sheet. This depends on User Story 1 already existing.

**Independent Test**: Can be fully tested by creating an entry, editing one
of its fields and confirming the change is saved and the ledger reflects the
corrected amount, then deleting it and confirming it no longer appears in the
list or in the ledger.

**Acceptance Scenarios**:

1. **Given** a list of existing income entries, **When** the admin filters
   by a date range and/or a source, **Then** only matching entries are
   shown.
2. **Given** an existing income entry, **When** the admin edits its amount,
   date, source, or description and saves, **Then** the entry reflects the
   updated values and the ledger's recorded effect is corrected to match.
3. **Given** an existing income entry, **When** the admin deletes it,
   **Then** it no longer appears in the income list, and its ledger effect
   is reversed so it no longer counts in any future report calculation.

---

### User Story 3 - See income reflected in the income statement and balance sheet (Priority: P2)

After recording income entries, the admin opens the existing income
statement and balance sheet reports and sees the income counted correctly
alongside expenses.

**Why this priority**: This is the actual reason the feature exists — the
reports already exist but are only ever showing the expense side. This
story is the observable proof that the gap is closed.

**Independent Test**: Can be fully tested by recording one opening
capital/investment income entry and one or more sales/service income
entries alongside existing expense entries, then confirming the income
statement's revenue total includes the sales/service entries and the
balance sheet's assets equal its liabilities plus equity.

**Acceptance Scenarios**:

1. **Given** one or more income entries recorded in a period, **When** the
   admin views the income statement for that period, **Then** the revenue
   total includes those entries and net profit/loss is computed from
   revenue minus expenses.
2. **Given** at least one opening capital/investment entry and any number of
   revenue and expense entries, **When** the admin views the balance sheet,
   **Then** total assets equal total liabilities plus total equity.

---

### Edge Cases

- What happens when a future-dated income entry is recorded (e.g. an
  expected payment)? The system should accept it (matches how expense
  entries already handle future dates) but it should be clearly
  distinguishable from already-received income.
- What happens when the admin edits an income entry's amount or source
  after it has already been posted to the ledger? The system must reverse
  the original ledger effect and post a new one for the corrected values —
  it must never leave both the old and new effect counted at once.
- What happens when the admin deletes the income entry that funded the
  business's opening cash? The balance sheet is not retroactively "fixed" —
  it will simply reflect the reduced funding, same as deleting any other
  entry reflects reality going forward.
- What happens when the admin filters income entries by a date range where
  the end date is before the start date? The system should reject the
  filter with a clear message rather than returning an empty or misleading
  result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create an income entry consisting of an
  amount, a date, a source, and an optional free-text description.
- **FR-002**: The system MUST reject an income entry whose amount is zero or
  negative, with a clear explanation of why it was rejected.
- **FR-003**: The system MUST reject an income entry that is missing a
  required field (amount or date) and indicate which field is missing.
- **FR-004**: Users MUST be able to view a list of income entries,
  filterable by date range and by source.
- **FR-005**: Users MUST be able to edit any field of an existing income
  entry; the ledger effect of that entry MUST be corrected to match the new
  values.
- **FR-006**: Users MUST be able to delete an existing income entry; its
  ledger effect MUST be reversed and the entry excluded from all future
  report calculations.
- **FR-007**: The system MUST provide a predefined starter set of income
  sources covering at least one operating-revenue source (e.g. Sales) and
  one non-operating, capital-funding source (e.g. Owner Investment), and
  MUST allow the admin to add custom sources beyond that starter set.
- **FR-008**: Every saved income entry MUST immediately produce a
  corresponding ledger effect (money received, increasing cash, increasing
  either revenue or equity depending on the source) without requiring a
  separate review or approval step, since the entry is already a direct,
  human-entered statement of fact (not an AI suggestion).
- **FR-009**: The system MUST persist every income entry so entries remain
  available across sessions and are not lost on restart.
- **FR-010**: The system MUST record when each income entry was created and
  when it was last modified.
- **FR-011**: The existing income statement (profit-and-loss) report MUST
  include income entries coded to revenue sources in its revenue total.
- **FR-012**: The existing balance sheet report MUST include income entries'
  effect on cash and, for capital-funding sources, on equity.

### Key Entities *(include if feature involves data)*

- **Income Entry**: A single recorded instance of money received, with an
  amount, a date, a source, an optional description, a creation timestamp,
  and a last-modified timestamp.
- **Income Source**: A label used to group income entries for reporting and
  filtering, and to determine whether an entry represents operating revenue
  or a non-operating capital contribution. Ships with a predefined starter
  set and is extensible — the admin can add custom sources beyond it
  (FR-007).

### Assumptions

- Mirrors 001-expense-entry's scope decisions where this feature doesn't
  say otherwise: single business/single admin user, single currency, no
  "closed accounting period" locking.
- Explicitly out of scope for this minimal feature (unlike 001's fuller
  scope): natural-language entry creation, AI-suggested source, and
  field-level edit history tracking. These may be added later the same way
  001 added them, but are not required to unblock the reports.
- Every income entry maps to exactly one ledger effect at time of save — an
  entry can only be "corrected" (edit/delete), not partially approved or
  held for review, since it is always a direct human statement rather than
  an AI-derived suggestion (see Constitution Principle III: human-in-the-loop
  applies to AI-derived actions, not to the admin's own manual entries).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can record a new income entry via the manual form in
  under 30 seconds.
- **SC-002**: A recorded income entry appears in the income statement's
  revenue total, and in the balance sheet's asset/equity totals, without any
  additional manual step beyond saving the entry.
- **SC-003**: A user can locate any previously recorded income entry by
  filtering on date range or source within 10 seconds.
- **SC-004**: 0% of saved income entries have a zero or negative amount.
- **SC-005**: A balance sheet built from a set of income entries that
  includes at least one capital-funding entry, plus any revenue and expense
  entries, balances (total assets = total liabilities + total equity).
