# Feature Specification: Financial Reporting (Trial Balance, P&L, Balance Sheet, Cash Flow)

**Feature Branch**: `005-reporting`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Reporting feature: trial balance, profit & loss (P&L), balance sheet, and cash flow statement generation. Critical constraint: the LLM/AI agent must never perform the financial calculations itself (no computing totals/balances from free text or from its own reasoning) — all calculations (aggregations, sums, balances) must be done deterministically via SQL/pandas against the ledger/journal data, and the LLM's role is limited to orchestrating which report to generate and narrating/explaining the computed result to the user. This must be explicitly documented as a constraint in the spec."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Trial Balance (Priority: P1)

An admin wants to confirm the books are balanced as of a given date — every
account's running debit or credit balance, and proof that total debits equal
total credits across the whole chart of accounts.

**Why this priority**: The trial balance is the foundation every other
statement is built from (P&L, balance sheet, and cash flow all derive from
the same account balances). It's also the simplest possible proof that the
ledger is internally consistent, so it must exist before the other, more
composed statements are worth generating.

**Independent Test**: Can be fully tested by posting a handful of journal
entries (via the existing ledger feature), requesting a trial balance as of
today, and confirming every account with activity appears with the correct
balance and that total debits equal total credits.

**Acceptance Scenarios**:

1. **Given** a set of posted journal entries, **When** the admin requests a
   trial balance as of a chosen date, **Then** the system shows every account
   with a non-zero balance as of that date, on its normal debit or credit
   side, with total debits equal to total credits.
2. **Given** no journal entries have been posted yet, **When** the admin
   requests a trial balance, **Then** the system shows an empty statement
   (all zeros) rather than an error.
3. **Given** a journal entry that was later reversed, **When** the trial
   balance is generated, **Then** the reversed entry and its reversal net to
   zero and do not distort any account's balance.

---

### User Story 2 - Generate a Profit & Loss Statement (Priority: P2)

An admin wants to see whether the business made or lost money over a chosen
period — total revenue, total expenses (broken down by account), and the
resulting net profit or loss.

**Why this priority**: This is the single most-requested "how is the
business doing" report, but it is a period-based summary built on top of the
same account balances the trial balance already proves are correct — it
depends on that foundation being trustworthy first.

**Independent Test**: Can be fully tested by posting expense journal entries
dated within a chosen period, requesting a P&L for that period, and
confirming the expense total matches the sum of those entries and nets out
to the correct profit/loss figure.

**Acceptance Scenarios**:

1. **Given** posted journal entries dated within a chosen period, **When**
   the admin requests a P&L for that period, **Then** the system shows total
   revenue, total expenses grouped by account, and the resulting net
   profit/loss for that period only.
2. **Given** a chosen period with no revenue or expense activity, **When**
   the P&L is requested, **Then** the system shows a zero-value statement
   rather than an error.
3. **Given** two adjacent periods, **When** a P&L is requested for each,
   **Then** entries dated in one period never appear in the other.

---

### User Story 3 - Generate a Balance Sheet (Priority: P3)

An admin wants a snapshot of what the business owns, owes, and is worth as of
a specific date — total assets, total liabilities, and total equity.

**Why this priority**: Valuable for a complete financial picture and for
anyone reviewing the business's overall position, but it is a point-in-time
view assembled from the same account data as the trial balance — useful
once the more frequently-needed trial balance and P&L already work.

**Independent Test**: Can be fully tested by posting journal entries across
several accounts, requesting a balance sheet as of a chosen date, and
confirming total assets equal total liabilities plus total equity.

**Acceptance Scenarios**:

1. **Given** posted journal entries across asset, liability, and equity
   accounts, **When** the admin requests a balance sheet as of a chosen
   date, **Then** the system shows total assets, total liabilities, and
   total equity as of that date, with assets equal to liabilities plus
   equity.
2. **Given** a chosen date before any journal entries existed, **When** the
   balance sheet is requested, **Then** the system shows an empty (all-zero)
   statement rather than an error.

---

### User Story 4 - Generate a Cash Flow Statement (Priority: P4)

An admin wants to see how much cash moved in and out of the business over a
chosen period, and why.

**Why this priority**: Useful for cash-management visibility, but it is the
most composed of the four statements (it explains a *change* between two
balance-sheet snapshots) and is the least urgent given this system currently
tracks a single cash position rather than multiple bank/investment accounts.

**Independent Test**: Can be fully tested by posting journal entries that
affect the cash account within a chosen period, requesting a cash flow
statement for that period, and confirming the reported net change in cash
matches the sum of those entries and reconciles to the change in the cash
account's balance between the period's start and end.

**Acceptance Scenarios**:

1. **Given** posted journal entries affecting the cash account within a
   chosen period, **When** the admin requests a cash flow statement for that
   period, **Then** the system shows the net change in cash for that period,
   and it reconciles exactly to the cash account's balance change over the
   same period.
2. **Given** a chosen period with no cash activity, **When** the cash flow
   statement is requested, **Then** the system shows a zero net change
   rather than an error.

---

### Edge Cases

- What happens when a requested date or period has no posted journal
  entries at all? Every report MUST return a valid, zero-value statement —
  never an error and never a fabricated/estimated figure.
- What happens when a journal entry has been reversed? Reports MUST only
  reflect the currently active (non-reversed) entries, so a corrected
  posting is never double-counted alongside the entry it replaced.
- What happens when an admin asks for a report through the AI chat
  interface using natural language (e.g., "how did we do last quarter")
  instead of picking exact dates from a form? The agent MUST resolve the
  request to a concrete report type and date range and call the
  corresponding deterministic report tool — it MUST NOT compute or state
  any financial figure itself; if it cannot confidently determine which
  report or period is meant, it MUST ask a clarifying question rather than
  guess and risk misreporting.
- What happens if a computed statement fails its own internal balance check
  (e.g., trial balance debits ≠ credits, or balance sheet assets ≠
  liabilities + equity) due to a data or logic error elsewhere in the
  system? The system MUST surface this as a visible discrepancy warning on
  the report rather than silently displaying an unbalanced statement as if
  it were correct.
- What happens when the chart of accounts contains a custom account whose
  type doesn't cleanly map to one of the four standard report sections
  (Asset/Liability/Equity → balance sheet; Revenue/Expense → P&L)? Every
  account type already recognized by the ledger feature MUST have a defined
  home in exactly one report section, so no account is silently dropped
  from every statement it should appear in.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every numeric figure shown in any report (account balances,
  subtotals, totals, net profit/loss, net cash change) MUST be produced by
  deterministic backend calculation against the ledger/journal data — never
  generated, estimated, or altered by the AI agent. The AI agent's only
  permitted roles are: (a) interpreting a natural-language request to
  determine which report and date/period is wanted, (b) invoking the
  corresponding deterministic report calculation, and (c) narrating/
  explaining the already-computed result in plain language. An agent
  response containing a financial figure that cannot be traced back to a
  report calculation's output is a defect, not an acceptable variation.
- **FR-002**: The system MUST generate a Trial Balance as of any admin-chosen
  date, listing every account with a non-zero balance as of that date on its
  normal debit or credit side, and MUST show that total debits equal total
  credits.
- **FR-003**: The system MUST generate a Profit & Loss statement for any
  admin-chosen date range, showing total revenue, total expenses (broken
  down by account), and the resulting net profit or loss for that range.
- **FR-004**: The system MUST generate a Balance Sheet as of any admin-chosen
  date, showing total assets, total liabilities, and total equity as of that
  date, and MUST show that assets equal liabilities plus equity.
- **FR-005**: The system MUST generate a Cash Flow Statement for any
  admin-chosen date range, showing the net change in cash for that range,
  reconciling to the cash account's balance change over the same range.
- **FR-006**: All four reports MUST exclude reversed journal entries and
  their original (reversed) counterparts from distorting any balance —
  only the currently active posting for each coding is counted, matching the
  ledger feature's existing reversal model.
- **FR-007**: All four reports MUST be requestable both directly (an
  explicit report type and date/date-range selection) and via the AI chat
  interface using natural language; the chat path MUST resolve to the same
  underlying deterministic calculation and MUST produce numerically
  identical figures to the direct request for the same report and period.
- **FR-008**: When a requested date or period has no posted (active)
  journal entries, the system MUST return a valid zero-value statement
  rather than an error or a fabricated figure.
- **FR-009**: Each report MUST perform its own internal consistency check
  (trial balance: debits = credits; balance sheet: assets = liabilities +
  equity) and MUST visibly flag the report as unbalanced if that check ever
  fails, rather than presenting an inconsistent statement as normal.
- **FR-010**: Every account type maintained by the chart of accounts MUST be
  classified into exactly one of the four reports' sections (Asset,
  Liability, or Equity for the balance sheet; Revenue or Expense for the
  P&L), so no account with posted activity is silently omitted from every
  report it should appear in.

### Key Entities *(include if feature involves data)*

None of the four reports introduce a new persisted entity — each is a
read-only calculation over the existing **Account** (chart of accounts) and
**Journal Entry** (posted double-entry postings) data already maintained by
the Ledger & Journal Entries feature:

- **Trial Balance**: A point-in-time computed statement — one row per
  account with a non-zero balance as of the chosen date, plus totals
  proving debits equal credits.
- **Profit & Loss Statement**: A period-computed statement — total revenue,
  total expenses by account, and net profit/loss for the chosen date range.
- **Balance Sheet**: A point-in-time computed statement — total assets,
  liabilities, and equity as of the chosen date, proving assets equal
  liabilities plus equity.
- **Cash Flow Statement**: A period-computed statement — the net change in
  the cash account's balance over the chosen date range.

### Assumptions

- This feature currently has only expense-side journal entries to report on
  (per the existing Ledger & Journal Entries feature, every expense entry
  debits an expense account and credits the single "Cash" offset account) —
  there is no separate Income Entry feature yet. The P&L will therefore show
  expense activity without a distinct revenue source until an income-side
  feature exists; the reporting calculations themselves MUST work correctly
  the moment revenue-side journal entries begin to appear, without requiring
  a spec change.
- Because all journal entries currently move against a single "Cash" offset
  account (no separate bank/loan/investment accounts yet), the Cash Flow
  Statement is scoped to a single-account, direct-method view of the net
  change in that one cash position. Multi-account cash pooling and a
  separate Operating/Investing/Financing activity breakdown are out of
  scope until additional account types exist to support that classification.
- If no date is specified for a point-in-time report (trial balance,
  balance sheet), it defaults to "as of today." If no range is specified for
  a period report (P&L, cash flow), it defaults to the current calendar
  month — both are reasonable, industry-standard defaults, not scope
  decisions requiring clarification.
- Exporting reports to PDF/CSV and side-by-side period comparisons are not
  requested and are out of scope for this feature; reports are viewed
  on-screen (or narrated via chat) only.
- Single business, single admin user, single currency — consistent with
  every prior feature's assumptions in this project.
- No "closed accounting period" concept exists yet — a report can be
  regenerated for any historical date/period at any time, matching the
  ledger feature's existing assumption that there is no period-locking.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A generated Trial Balance shows total debits equal to total
  credits 100% of the time, for any date requested.
- **SC-002**: A generated Balance Sheet shows total assets equal to total
  liabilities plus total equity 100% of the time, for any date requested.
- **SC-003**: An admin can view any of the four core financial statements
  for a chosen date or period in under 5 seconds, with no manual
  spreadsheet work or arithmetic.
- **SC-004**: Every numeric figure in every generated report can be traced
  back to specific posted journal entries, verifiable at any time.
- **SC-005**: 100% of report figures returned through the AI chat interface
  match, to the last decimal, the figures returned by the equivalent direct
  report request for the same report and period — the narration never
  diverges from the underlying computed numbers.
