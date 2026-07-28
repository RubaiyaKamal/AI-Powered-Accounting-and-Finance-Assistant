# Feature Specification: Tax & Compliance Summaries

**Feature Branch**: `008-tax-compliance-summaries`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Tax & Compliance Summaries. Method: use RAG (retrieval-augmented generation) over the ledger and admin-provided tax rules reference documents to draft a summary — but human sign-off is required before it's treated as final, since this is a regulatory-risk area."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a Tax Rules Reference Library (Priority: P1)

An admin adds the tax rules, thresholds, or filing guidance documents relevant to their business (their own reference material, not built-in tax law) so the system has something concrete to ground future summaries in, and can view or remove documents from that library at any time.

**Why this priority**: Every other part of this feature depends on there being reference material to retrieve from — without it, a "compliance summary" would either be empty or, worse, tempted to invent guidance. This library is the foundation everything else is grounded in.

**Independent Test**: Can be fully tested by adding a reference document, confirming it appears in the library with its content viewable, and confirming it can be removed and no longer appears.

**Acceptance Scenarios**:

1. **Given** the admin has a tax rule or filing guidance document, **When** they add it to the reference library with a title, **Then** it appears in the library and its content is viewable.
2. **Given** a document in the library, **When** the admin removes it, **Then** it no longer appears in the library or in retrieval for any future summary.
3. **Given** an empty library, **When** the admin views it, **Then** the system clearly shows there are no reference documents yet, rather than an error.

---

### User Story 2 - Generate a Draft Tax/Compliance Summary (Priority: P2)

An admin requests a tax/compliance summary for a chosen period and receives a draft that combines the business's actual financial figures for that period with the most relevant passages from their reference library, clearly written and clearly marked as a draft that has not been reviewed or approved yet.

**Why this priority**: This is the feature's core value — turning raw ledger data and reference material into a readable draft — but it only produces something meaningful once a reference library exists (User Story 1), and its output isn't safe to rely on until the sign-off step (User Story 3) exists to gate it.

**Independent Test**: Can be fully tested by adding a reference document relevant to a period's activity, posting journal entries in that period, requesting a summary for that period, and confirming the draft shows the correct computed figures, cites the relevant reference passage, and is visibly labeled as an unreviewed draft.

**Acceptance Scenarios**:

1. **Given** posted journal entries in a chosen period and at least one relevant reference document, **When** the admin requests a summary for that period, **Then** the system produces a draft showing the period's actual computed financial figures, references the relevant passage(s) from the library, and is clearly labeled as a draft.
2. **Given** a chosen period with posted activity but no reference document relevant to it, **When** the admin requests a summary, **Then** the draft still shows the correct computed figures but clearly states that no relevant reference material was found, rather than inventing guidance.
3. **Given** a chosen period with no posted activity at all, **When** the admin requests a summary, **Then** the system produces a valid draft reflecting zero activity rather than an error.

---

### User Story 3 - Review and Sign Off on a Draft (Priority: P3)

Having reviewed a draft summary, the admin either signs off on it — making it an official, retained record — or discards it to regenerate later, so that nothing produced by this feature is ever treated as final without a deliberate human decision.

**Why this priority**: This is what makes the feature safe to use for something with real regulatory consequences. It's the last step in the chain, layered on top of a working draft (User Story 2).

**Independent Test**: Can be fully tested by generating a draft, signing off on it, and confirming it's retained with a recorded sign-off time and is distinguishable from unsigned drafts; and separately, by discarding a draft and confirming it's no longer treated as pending.

**Acceptance Scenarios**:

1. **Given** a draft summary, **When** the admin signs off on it, **Then** it is recorded as signed off with a timestamp, and its figures and cited reference passages become fixed at that point in time.
2. **Given** a signed-off summary, **When** the underlying ledger data or reference library later changes, **Then** the signed-off summary's content does not change — it remains exactly what was signed off.
3. **Given** a draft the admin does not want to keep, **When** they discard it, **Then** it is no longer shown as a pending draft.
4. **Given** a draft whose underlying period's ledger data has changed since the draft was generated, **When** the admin attempts to sign off, **Then** the system warns that the draft may be out of date and requires it to be regenerated before it can be signed off.

---

### User Story 4 - Ask for a Summary in Natural Language (Priority: P4)

An admin asks the AI chat interface something like "draft a tax summary for last quarter" instead of picking a period from a form.

**Why this priority**: A convenient alternate entry point consistent with how this system already lets admins ask for reports and audits in plain language, but the direct, form-driven flow (User Story 2) is the primary and sufficient way to deliver this feature's core value.

**Independent Test**: Can be fully tested by asking the chat interface for a summary with an implied period, and confirming it produces the same draft a direct request for that period would.

**Acceptance Scenarios**:

1. **Given** a natural-language request that clearly implies a period, **When** the admin submits it, **Then** the system drafts a summary for the corresponding period identical to what a direct request for that period would produce.
2. **Given** a request too vague to determine a period, **When** the admin submits it, **Then** the system asks a clarifying question rather than guessing.

---

### Edge Cases

- What happens when no reference documents exist, or none are relevant to the requested period? The draft MUST still show the correct computed figures and MUST clearly state that no relevant reference material was found — it MUST NOT fill the gap with the AI's own general tax knowledge.
- What happens when an admin tries to sign off on a draft whose underlying figures are no longer current (e.g., a correction was posted to that period after the draft was generated)? The system MUST warn and block sign-off until the draft is regenerated against current data.
- What happens when a reference document cited in an already-signed-off summary is later removed from the library? The signed-off summary MUST keep showing what was actually cited at sign-off time — removing a document from the library MUST NOT alter or blank out any already-signed-off summary.
- What happens when a summary is requested for a period with no posted activity? The system MUST produce a valid draft reflecting zero activity, not an error.
- What happens when an admin asks for a summary via chat using a period too vague to resolve? The system MUST ask a clarifying question rather than guessing a period and drafting a potentially misleading summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An admin MUST be able to add a tax rules reference document (a title and its text content) to a reference library, view its content, and remove it.
- **FR-002**: An admin MUST be able to request a tax/compliance summary for any chosen date range.
- **FR-003**: Before drafting a summary, the system MUST retrieve the reference-library passages most relevant to the requested period's content — a summary MUST NOT be produced without first attempting this retrieval step.
- **FR-004**: Every financial figure appearing in a summary (revenue, expenses, net income, or any other computed total) MUST be produced by deterministic computation over the ledger — the same computations already relied on for reporting — and MUST NOT be generated, estimated, or altered by the AI itself. An AI-produced figure not traceable to a deterministic computation is a defect, not an acceptable variation.
- **FR-005**: Every reference-document excerpt referenced in a summary MUST be an actual passage retrieved from the admin's reference library. When no relevant passage is found for the requested period, the system MUST say so explicitly rather than presenting the AI's own general knowledge as if it were grounded guidance.
- **FR-006**: Every newly generated summary MUST be clearly and visibly labeled as an unsigned draft until an admin explicitly signs off on it.
- **FR-007**: An admin MUST be able to sign off on a draft summary. Once signed off, the summary's figures, cited passages, and narrative text MUST be fixed — later changes to the ledger or reference library MUST NOT alter a summary that has already been signed off.
- **FR-008**: The system MUST NOT export, present, or otherwise treat an unsigned draft as an official or final compliance document.
- **FR-009**: If the ledger data underlying a draft's period has changed since the draft was generated, the system MUST warn the admin and MUST NOT allow sign-off until the draft is regenerated against current data.
- **FR-010**: An admin MUST be able to discard a draft they don't want to keep, and MUST be able to view a history of past summaries (drafts and signed-off) with each one's status.
- **FR-011**: Summary requests MUST be triggerable both directly (an explicit date-range selection) and via the AI chat interface using natural language; the chat path MUST produce the same draft a direct request for the same resolved period would, and MUST ask a clarifying question instead of guessing when the intended period can't be confidently determined.

### Key Entities *(include if feature involves data)*

- **Tax Rules Document**: An admin-provided reference document in the retrieval library — a title and its text content, added and removable by the admin. Never authored or fabricated by the system itself.
- **Tax/Compliance Summary**: A generated record for a chosen date range — the period's deterministically computed financial figures, the reference passages retrieved and cited (or a note that none were found), a narrative explanation, and a status (draft or signed off). Once signed off, immutable; a signed-off summary retains its own fixed copy of the figures and cited passages rather than a live link to the ledger or library.

### Assumptions

- Single business, single admin user — consistent with every other feature's assumptions in this project. Sign-off is a single-step approval by that one admin; no multi-person approval chain is in scope.
- The system does not embed or claim knowledge of real-world tax law. All tax-rule content a summary can reference comes exclusively from documents the admin explicitly adds to the reference library — this is a drafting aid grounded in the business's own reference material, not a source of tax guidance in itself. This boundary exists specifically because of this feature's regulatory-risk nature.
- Reference documents are text-based (plain text or pasted content); parsing scanned or complex-format documents (e.g., PDF layout extraction) is out of scope for this feature's initial version.
- This feature drafts summaries for internal review only — no filing, e-filing submission, or integration with any tax authority or third-party compliance system is in scope.
- If no date range is specified for a summary request, it defaults to the current calendar month, consistent with this project's other period-based reports (Profit & Loss, Cash Flow).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of financial figures in every generated summary are traceable to a deterministic computation over the ledger, verifiable at any time.
- **SC-002**: 100% of tax-rule statements in a summary are traceable to an actual retrieved passage from the admin's reference library — zero fabricated or unsourced tax guidance.
- **SC-003**: 100% of summaries treated as official/final have an explicit, timestamped sign-off action on record; no summary reaches that status any other way.
- **SC-004**: An admin can generate a draft summary for a chosen period in under 30 seconds.
- **SC-005**: A signed-off summary's content remains byte-for-byte unchanged even after the underlying ledger or reference library later changes, verified 100% of the time.
