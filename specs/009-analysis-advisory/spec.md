# Feature Specification: Analysis & Advisory / Natural-Language Q&A

**Feature Branch**: `009-analysis-advisory`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Analysis & Advisory / Natural-Language Q&A over the ledger — ask questions like 'how much did we spend on utilities in March?', view spending pattern analysis, and get spending forecasts. Method: resolve natural-language questions into structured queries over the transaction/ledger database (not free-form LLM-authored SQL) with LLM narration of the deterministically-computed results; for forecasting, use a deterministic statistical/time-series method that the LLM explains in plain language — the LLM never computes or states a figure itself."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a Natural-Language Spending Question (Priority: P1)

An admin asks a plain-language question — "how much did we spend on utilities in March?" — and gets a direct, accurate answer drawn from the business's actual posted ledger activity.

**Why this priority**: This is the feature's flagship, most concretely requested capability, and the smallest slice that delivers real value: an admin gets an instant answer to a specific spending question without digging through the ledger or reports themselves.

**Independent Test**: Can be fully tested by posting expense activity to a known account in a known period, asking a natural-language question about that account and period, and confirming the answer states the correct figure.

**Acceptance Scenarios**:

1. **Given** posted expense activity on a specific account within a specific period, **When** the admin asks a natural-language question naming that account (or a close everyday term for it) and period, **Then** the system answers with the correct total spending for that account and period.
2. **Given** a question naming a period with no matching activity, **When** the admin asks it, **Then** the system answers with a zero figure rather than an error.
3. **Given** a question that doesn't clearly name an account/category, a period, or otherwise doesn't match a kind of question the system can answer, **When** the admin asks it, **Then** the system asks a clarifying question rather than guessing.
4. **Given** a question naming an account or category that doesn't exist in the business's chart of accounts, **When** the admin asks it, **Then** the system says so rather than returning a fabricated or zero figure.

---

### User Story 2 - View Spending Pattern Analysis (Priority: P2)

An admin views a breakdown of spending by category/account for a chosen period, and can compare spending between two periods to see what's trending up or down.

**Why this priority**: A natural extension of answering single spending questions — instead of asking about one account at a time, the admin sees the whole picture at once. Valuable on its own, but less urgent than the flagship single-question capability.

**Independent Test**: Can be fully tested by posting expense activity across several accounts in a period, requesting a breakdown for that period, and confirming every account with activity appears with its correct total, ranked from highest to lowest; and separately, by requesting a comparison between two periods and confirming the reported change matches the actual difference in posted activity.

**Acceptance Scenarios**:

1. **Given** posted expense activity across several accounts within a chosen period, **When** the admin requests a spending breakdown for that period, **Then** the system shows every account with activity, its total, and its share, ranked from highest to lowest spending.
2. **Given** two chosen periods with posted expense activity, **When** the admin requests a comparison between them, **Then** the system shows the change in spending, overall and by account, between the two periods.
3. **Given** a chosen period with no posted expense activity, **When** the admin requests a breakdown, **Then** the system shows an empty breakdown rather than an error.

---

### User Story 3 - Get a Spending Forecast (Priority: P3)

An admin requests a spending forecast for an upcoming period and receives an estimate, clearly labeled as such, along with a plain-language explanation of how it was derived from the business's own spending history.

**Why this priority**: Forward-looking and valuable for planning, but it depends on there being enough historical spending data to project from — most useful once the business has an established posting history, making it reasonably lower priority than understanding what's already happened.

**Independent Test**: Can be fully tested by posting a consistent trend of expense activity across several past periods, requesting a forecast for the next period, and confirming the forecast is clearly labeled as an estimate, is reasonably consistent with the established trend, and comes with a plain-language explanation of the method and data it's based on.

**Acceptance Scenarios**:

1. **Given** enough historical posted spending data to establish a trend, **When** the admin requests a forecast for a future period, **Then** the system returns an estimated figure clearly labeled as a forecast (not a certainty), along with a plain-language explanation of the method and historical data behind it.
2. **Given** too little historical spending data to produce a statistically meaningful forecast, **When** the admin requests one, **Then** the system clearly says there isn't enough data yet rather than presenting a low-confidence guess as if it were reliable.

---

### User Story 4 - Ask for Patterns or a Forecast in Natural Language (Priority: P4)

An admin asks the AI chat interface something like "what are we spending the most on this month?" or "what will we likely spend next month?" instead of using a dedicated breakdown or forecast view.

**Why this priority**: A convenient, consistent alternate entry point — this system already lets admins ask for reports, audits, and tax summaries in plain language — but the direct, dedicated views (User Stories 2 and 3) are the primary and sufficient way to deliver those capabilities.

**Independent Test**: Can be fully tested by asking the chat interface a pattern or forecast question with a clearly implied period, and confirming it returns the same result a direct breakdown or forecast request for that period would.

**Acceptance Scenarios**:

1. **Given** a natural-language request that clearly implies a breakdown, comparison, or forecast and a period, **When** the admin submits it, **Then** the system returns the same result a direct request of that kind would produce for that period.
2. **Given** a request too vague to determine what kind of analysis or period is wanted, **When** the admin submits it, **Then** the system asks a clarifying question rather than guessing.

---

### Edge Cases

- What happens when a question or request refers to a period with no posted activity at all? The system MUST return a valid zero-value answer or empty breakdown, never an error and never a fabricated figure.
- What happens when a question can't be confidently matched to one of the supported kinds of spending questions (an amount, a breakdown, a comparison, or a forecast), or its account/category or period can't be determined? The system MUST ask a clarifying question rather than guessing and risking a misleading answer.
- What happens when a question names an account or category that doesn't exist in the chart of accounts? The system MUST say so explicitly rather than returning a zero or invented figure.
- What happens when a forecast is requested but there isn't enough historical data to produce a statistically meaningful estimate? The system MUST clearly say so rather than presenting an unreliable guess as if it were dependable.
- What happens when an entry included in a past answer is later corrected (reversed and reposted)? Only the currently active posting MUST be counted going forward — a reversed entry and its original MUST never both contribute to a spending figure, pattern breakdown, or forecast input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An admin MUST be able to ask a natural-language question about spending (e.g., "how much did we spend on utilities in March?") and receive an answer stating the actual figure.
- **FR-002**: Every numeric figure in any answer, breakdown, or forecast MUST be produced by deterministic computation over the ledger — never generated, estimated, or altered by the AI itself. The AI's only permitted roles are: interpreting a question into one of the supported kinds of requests, and narrating/explaining the already-computed result in plain language. A figure that cannot be traced back to a deterministic computation is a defect, not an acceptable variation.
- **FR-003**: The system MUST support, at minimum, these kinds of spending requests: (a) total spending for a specific account/category over a chosen period, (b) a ranked breakdown of spending across accounts/categories for a chosen period, (c) a comparison of spending between two chosen periods, and (d) a forecast of expected spending for a future period.
- **FR-004**: When a request cannot be confidently matched to one of the supported kinds, or the intended account/category or period can't be determined, the system MUST ask a clarifying question rather than guessing.
- **FR-005**: When a request refers to an account or category that doesn't exist in the business's chart of accounts, the system MUST say so rather than returning a zero or fabricated figure.
- **FR-006**: An admin MUST be able to view a spending breakdown for any chosen period, and a comparison between any two chosen periods, directly — without needing to phrase either as a natural-language question.
- **FR-007**: An admin MUST be able to request a spending forecast for a future period directly — without needing to phrase it as a natural-language question.
- **FR-008**: Every forecast MUST be computed by a deterministic statistical method applied to the business's own historical ledger data, and MUST be clearly labeled as an estimate, not a certainty. The AI's role in a forecast is limited to explaining the method and result in plain language — it MUST NOT be the source of the forecasted figure itself.
- **FR-009**: When there is not enough historical data for a statistically meaningful forecast, the system MUST clearly say so rather than presenting a low-confidence estimate as if it were reliable.
- **FR-010**: All supported spending requests (amounts, breakdowns, comparisons, and forecasts) MUST be requestable both directly and via the AI chat interface using natural language; the chat path MUST resolve to the same underlying deterministic computation a direct request would use and MUST produce identical figures.
- **FR-011**: Every spending figure, breakdown, comparison, and forecast input MUST include only active (posted, non-reversed) ledger entries — matching the ledger's existing definition of a currently active posting — so a corrected or reversed entry never distorts an answer.

### Key Entities *(include if feature involves data)*

This feature introduces no new persisted entities. Every answer, breakdown,
comparison, and forecast is a read-only computation over the existing
**Account** (chart of accounts) and **Journal Entry** (posted double-entry
postings) data already maintained by the Ledger & Journal Entries feature
— computed fresh on every request, never cached or retained as history,
consistent with how the existing Reporting feature operates.

- **Spending Answer**: A single computed figure — total spending for one
  account/category over a chosen period.
- **Spending Breakdown**: A computed, ranked list of spending totals across
  accounts/categories for a chosen period.
- **Spending Comparison**: Two computed breakdowns (or totals), for two
  chosen periods, plus the computed change between them.
- **Spending Forecast**: An estimated figure for a future period, computed
  by a deterministic statistical method from historical spending data,
  plus a plain-language explanation of that method.

### Assumptions

- Single business, single admin user, single currency — consistent with
  every other feature's assumptions in this project.
- "Spending" is scoped to expense-account activity on the ledger,
  consistent with the existing Reporting feature's assumption that this
  system currently has expense-side activity only (no distinct
  revenue-side feature yet).
- The system answers a fixed, well-defined set of supported spending
  question kinds (an amount, a breakdown, a comparison, or a forecast) —
  not fully open-ended, arbitrary analytical questions. A question outside
  this set gets a clarifying response, not a best-effort guess; this is a
  deliberate scope boundary, not a limitation to be worked around.
- Forecasting projects from the business's own historical monthly spending
  trend only — no external economic data, seasonality research, or
  industry benchmarks are incorporated. A forecast is a reasonable,
  honestly-labeled estimate for internal planning, not authoritative
  financial advice.
- If no period is specified in a request, it defaults to the current
  calendar month, consistent with this project's other period-based
  features (Profit & Loss, Cash Flow, Tax/Compliance Summaries).
- What counts as "enough historical data" for a meaningful forecast is a
  reasonable implementation-level default, not a business-scope decision
  requiring clarification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of numeric figures in every answer, breakdown,
  comparison, and forecast are traceable to a deterministic computation
  over the ledger, verifiable at any time.
- **SC-002**: An admin can get an answer to a specific spending question,
  or view a spending breakdown for a chosen period, in under 15 seconds.
- **SC-003**: 100% of forecasts are clearly labeled as estimates and
  accompanied by a plain-language explanation of the method and data used
  — never presented as a certain figure.
- **SC-004**: 100% of requests that fall outside the supported kinds of
  spending questions, or whose account/category/period can't be
  determined, receive a clarifying response rather than a guessed answer.
- **SC-005**: 100% of chat-path answers, breakdowns, comparisons, and
  forecasts are numerically identical to what the equivalent direct
  request for the same resolved parameters would produce.
