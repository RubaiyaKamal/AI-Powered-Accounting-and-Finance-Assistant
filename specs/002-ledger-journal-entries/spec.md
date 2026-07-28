# Feature Specification: Ledger & Journal Entries

**Feature Branch**: `002-ledger-journal-entries`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Ledgers & Journal Entries — chart-of-accounts coding and double-entry journal posting on top of the existing expense entries. An admin should be able to have entries automatically coded to the correct chart-of-accounts category with an AI-suggested confidence score, review/approve or correct that coding, and have the system post proper double-entry (debit/credit) journal entries against a chart of accounts rather than free-text numbers — the LLM only decides what to post via a scoped tool call, never generates the ledger numbers itself."

## Clarifications

### Session 2026-07-28

- Q: Should a coding suggestion at or above the confidence threshold be posted to the ledger automatically, or must every coding always be explicitly approved by the admin first? → A: Auto-post above threshold; only below-threshold suggestions require explicit admin review.
- Q: When an admin corrects the coding of an expense entry whose journal entry has already been posted, should the system automatically reverse and repost, or require a manual reversal step first? → A: Fully automatic — correcting the coding auto-reverses and reposts in one action.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get an AI-suggested account coding for an expense (Priority: P1)

An admin has recorded expense entries (via the existing expense-entry feature)
and now needs each one coded to the correct chart-of-accounts account so it
can be posted to the ledger. Instead of manually picking an account for every
entry, the system suggests one automatically, together with a confidence
score, and the admin reviews it — accepting it as-is or correcting it to a
different account.

**Why this priority**: This is the entry point for everything else in this
feature — nothing can be posted to the ledger until it has an account coding.
It must work before double-entry posting or ledger viewing are worth
building.

**Independent Test**: Can be fully tested by taking an existing expense entry,
confirming the system shows a suggested account and a confidence score, then
either accepting it or picking a different account, and confirming the
entry's coding reflects that choice.

**Acceptance Scenarios**:

1. **Given** an expense entry that has not yet been coded, **When** the admin
   opens it, **Then** the system shows a suggested chart-of-accounts account
   and a confidence score for that suggestion.
2. **Given** a suggested coding, **When** the admin accepts it, **Then** the
   entry's coding is recorded as approved with that account.
3. **Given** a suggested coding, **When** the admin instead selects a
   different account, **Then** the entry's coding is recorded with the
   admin-chosen account and is no longer marked as AI-suggested.
4. **Given** a suggested coding with a confidence score below the system's
   review threshold, **When** the suggestion is generated, **Then** it is
   flagged for mandatory admin review rather than treated as pre-approved.

---

### User Story 2 - Post a balanced double-entry journal entry (Priority: P2)

Once an expense entry's account coding is approved, the admin needs it
reflected in the ledger as a proper double-entry journal entry — a debit and
a matching credit — rather than as a single free-text number, so the books
stay balanced and auditable.

**Why this priority**: This is the feature's core value (a real ledger, not
just categorized expenses), but it structurally depends on User Story 1 — an
entry must be coded before it can be posted.

**Independent Test**: Can be fully tested by approving the coding on an
expense entry and confirming a journal entry is created whose debit and
credit lines are for the same amount and sum to zero, referencing the coded
account and the expense entry it came from.

**Acceptance Scenarios**:

1. **Given** an expense entry with an approved account coding, **When** the
   coding is approved, **Then** the system posts a journal entry with a debit
   line and a credit line whose amounts are equal, so the entry balances.
2. **Given** a posted journal entry, **When** it is viewed, **Then** it shows
   which expense entry it was generated from and which accounts were debited
   and credited.
3. **Given** an expense entry whose coding is later corrected, **When** the
   correction is saved, **Then** the system adjusts the ledger (via a
   reversing and a replacement journal entry) so the ledger always reflects
   the current coding rather than becoming inconsistent with it.
4. **Given** an attempt to post a journal entry, **When** the system
   constructs it, **Then** the debit and credit amounts are computed by
   deterministic application logic, never generated as free text by the AI.

---

### User Story 3 - View the ledger (Priority: P3)

The admin wants to browse posted journal entries — by account, by date range,
or by the expense entry that generated them — to review the books or trace a
number back to its source.

**Why this priority**: Valuable for review and trust in the system, but the
ledger still functions (coding and posting still work) without a dedicated
browsing view — this is a visibility layer on top of Stories 1–2, not a
blocker for them.

**Independent Test**: Can be fully tested by posting a few journal entries and
confirming they can be listed and filtered by account and by date range, and
that each one links back to its source expense entry.

**Acceptance Scenarios**:

1. **Given** a set of posted journal entries, **When** the admin filters by
   account and/or date range, **Then** only matching journal entries are
   shown.
2. **Given** a journal entry in the list, **When** the admin opens it,
   **Then** they can see its source expense entry, the accounts debited and
   credited, and the amount.

---

### Edge Cases

- What happens when no chart-of-accounts account can be confidently
  suggested for an expense entry (e.g., a vague or empty description)? The
  entry is flagged for manual coding rather than the system guessing.
- What happens when an admin deletes an expense entry that has already been
  posted to the ledger? The system reverses the associated journal entry
  (rather than silently deleting ledger history) so the ledger stays
  balanced and auditable.
- What happens if posting a journal entry would not balance (debit ≠
  credit) due to a system error? The system MUST refuse to post it rather
  than record an unbalanced entry.
- What happens when the admin tries to code an entry to an account that has
  since been removed from the chart of accounts? The system rejects the
  coding and asks the admin to choose a current account.
- What happens when the same expense entry is coded and approved twice in
  quick succession (e.g., a double click)? The system posts exactly one
  journal entry per approved coding, not a duplicate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a chart of accounts, where each
  account has a code, a name, and a type (Asset, Liability, Equity, Revenue,
  or Expense).
- **FR-002**: The system MUST ship with a predefined starter chart of
  accounts covering the categories already used by expense entries, and MUST
  allow the admin to add custom accounts beyond that starter set.
- **FR-003**: For every uncoded expense entry, the system MUST suggest a
  chart-of-accounts account coding along with a numeric confidence score.
- **FR-004**: A coding suggestion at or above the confidence threshold MUST
  be posted to the ledger automatically, without waiting for admin action;
  only suggestions below the threshold require explicit admin review (see
  FR-005).
- **FR-005**: Suggestions below the confidence threshold MUST always be
  routed to mandatory admin review rather than being auto-approved,
  regardless of the answer to FR-004.
- **FR-006**: Users MUST be able to review a suggested coding and either
  approve it as-is or correct it to a different account; correcting a
  coding MUST remove its AI-suggested marker.
- **FR-007**: When a coding is approved (whether automatically or manually),
  the system MUST post a balanced double-entry journal entry — one debit
  line and one credit line of equal amount — against the chart of accounts.
  The debit and credit amounts MUST be produced by deterministic application
  logic, never generated as free text by the AI.
- **FR-008**: The system MUST refuse to post any journal entry whose debit
  and credit amounts do not balance.
- **FR-009**: Users MUST be able to view the list of posted journal entries,
  filterable by date range and/or account.
- **FR-010**: For every journal entry, users MUST be able to see which
  source expense entry generated it and which accounts were debited and
  credited.
- **FR-011**: When an admin edits the coding of an expense entry whose
  journal entry has already been posted, the system MUST automatically
  reverse the old journal entry and post a replacement reflecting the
  corrected coding, in a single action — the admin does not perform a
  separate manual reversal step.
- **FR-012**: When an expense entry that has already been posted to the
  ledger is deleted, the system MUST reverse its journal entry rather than
  leave an orphaned or silently removed ledger record.
- **FR-013**: The system MUST record, for every coding, whether it was
  AI-suggested or admin-chosen, mirroring how expense-entry categories track
  their source.
- **FR-014**: The system MUST persist the chart of accounts and all journal
  entries (including reversed ones) so the ledger remains complete and
  available across sessions.
- **FR-015**: The system MUST NOT allow a journal entry to be posted against
  an account that no longer exists in the current chart of accounts.

### Key Entities *(include if feature involves data)*

- **Account**: A single line in the chart of accounts, with a code, a name,
  and a type (Asset, Liability, Equity, Revenue, Expense). Ships with a
  predefined starter set (FR-002) and is extensible.
- **Account Coding**: The link between an expense entry and the account it
  has been assigned to, including a confidence score (when AI-suggested) and
  whether it was AI-suggested or admin-chosen (FR-013). Belongs to exactly
  one Expense Entry.
- **Journal Entry**: A posted, balanced double-entry ledger record generated
  from an approved Account Coding — a debit line and a credit line of equal
  amount, referencing the accounts involved and the source Expense Entry
  (FR-007, FR-010). May later be reversed (FR-012) if its source entry or
  coding is deleted or corrected.

### Assumptions

- This feature covers only the existing Expense Entry data (per the user
  description, "on top of the existing expense entries") — Income Entry
  ledger coding, if it becomes a separate feature later, is out of scope
  here.
- A confidence threshold exists as a configurable value, but the specific
  numeric default (e.g., 80%) is an implementation detail, not a
  business-scope decision, and does not require its own clarification.
- Single business, single admin user per deployment — no multi-user
  permissions or role model, consistent with the existing expense-entry
  feature's assumptions.
- Single currency — no multi-currency support or conversion is in scope.
- There is no "closed accounting period" concept yet — journal entries can
  still be reversed/replaced regardless of age, matching the expense-entry
  feature's assumption that there is no period-locking yet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every expense entry receives an account coding suggestion with
  a confidence score without any manual lookup work by the admin.
- **SC-002**: 100% of posted journal entries have debit and credit amounts
  that sum to zero (i.e., the ledger is always balanced), verifiable at any
  time.
- **SC-003**: An admin can trace any journal entry back to its source
  expense entry, and any expense entry forward to its journal entry, within
  a few seconds.
- **SC-004**: An admin can correct a miscoded expense entry and see the
  ledger reflect the correction without performing any manual debit/credit
  arithmetic themselves.
- **SC-005**: An admin can locate all journal entries for a given account or
  date range within 10 seconds.
