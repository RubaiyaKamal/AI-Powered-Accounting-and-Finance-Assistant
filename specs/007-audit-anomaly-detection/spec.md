# Feature Specification: Audit & Anomaly Detection (Fraud/Anomaly Flags)

**Feature Branch**: `007-audit-anomaly-detection`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Audit & Anomaly Detection (fraud/anomaly flags) for posted journal entries. Method: use statistical/ML models (such as Isolation Forest, clustering) to detect anomalies in the ledger — similar in spirit to real-world tools like EY Helix GL Anomaly Detector and MindBridge. Then have the LLM explain in plain language why a given entry was flagged as anomalous."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run an Audit and See Flagged Entries (Priority: P1)

An admin wants to check the ledger for unusual or suspicious-looking postings
— entries that stand out from the business's normal patterns — without
manually scanning every journal entry. They trigger an audit over a chosen
date range and see a ranked list of the entries most likely to be
anomalous, each with a plain-language explanation of what makes it stand
out.

**Why this priority**: This is the entire point of the feature — detection
without an understandable reason attached isn't actionable for a
non-technical business owner, and a reason without underlying detection is
just guesswork. Both halves together are the smallest slice that delivers
real audit value.

**Independent Test**: Can be fully tested by posting a mix of typical and
deliberately unusual journal entries (e.g., one far larger than the rest,
one suspiciously round number, two identical-looking duplicates), running
an audit over that period, and confirming the unusual entries are flagged
with explanations that correctly describe what made each one stand out
while the typical entries are not flagged.

**Acceptance Scenarios**:

1. **Given** a mix of typical and statistically unusual posted journal
   entries within a chosen date range, **When** the admin runs an audit over
   that range, **Then** the system returns a ranked list of the most
   anomalous entries, each with a plain-language explanation of why it was
   flagged.
2. **Given** a date range where every posted entry looks statistically
   normal, **When** the admin runs an audit over that range, **Then** the
   system clearly reports that no anomalies were found rather than forcing
   flags on ordinary entries.
3. **Given** a date range with too few posted entries to produce a
   statistically meaningful result, **When** the admin runs an audit, **Then**
   the system clearly indicates there isn't enough data yet, rather than
   presenting misleading flags.

---

### User Story 2 - Review and Resolve a Flagged Entry (Priority: P2)

Having seen a flagged entry, the admin wants to record what they decided
about it — confirmed issue, false positive, or no action needed — so it's
clear which flags have already been looked at and the same item doesn't
keep demanding attention indefinitely.

**Why this priority**: Detection alone becomes noise over time if nothing
tracks what's already been triaged. This turns the flagged list into a
working audit trail rather than a one-time report.

**Independent Test**: Can be fully tested by flagging an entry via an audit
run, recording a resolution for it, and confirming that resolution is still
visible the next time that flag is viewed.

**Acceptance Scenarios**:

1. **Given** a flagged entry, **When** the admin records a resolution for
   it, **Then** that resolution is saved and shown whenever the flag is
   viewed again.
2. **Given** a flagged entry that already has a recorded resolution,
   **When** the admin views the audit run's results again, **Then** the
   entry is clearly shown as already reviewed rather than as new.

---

### User Story 3 - Review Past Audit History (Priority: P3)

An admin wants to see what audit runs have been performed over time — when,
over what period, and how many anomalies each turned up — to support a
recurring review habit (e.g., a monthly check) rather than starting from
scratch every time.

**Why this priority**: Valuable for building an ongoing audit discipline
and demonstrating due diligence over time, but it's a secondary view on top
of data User Story 1 already produces — useful once running and reading a
single audit already works.

**Independent Test**: Can be fully tested by running two or more audits
over different periods and confirming both appear in a history view with
their date range and flag counts, and each can be reopened to see its
original results.

**Acceptance Scenarios**:

1. **Given** multiple past audit runs, **When** the admin views audit
   history, **Then** each run is listed with the period it covered and how
   many entries it flagged.
2. **Given** a past audit run, **When** the admin opens it from the
   history view, **Then** they see the same flagged entries and
   explanations (and any recorded resolutions) as when it was first run.

---

### User Story 4 - Ask About Anomalies in Natural Language (Priority: P4)

An admin asks the AI chat interface something like "check this month for
anything unusual" instead of picking exact dates and clicking "run audit."

**Why this priority**: A convenient alternate entry point consistent with
how this system already lets admins ask for reports in plain language, but
the direct, form-driven audit flow (User Story 1) is the primary and
sufficient way to deliver this feature's core value.

**Independent Test**: Can be fully tested by asking the chat interface an
audit-style question with an implied period, and confirming it triggers the
same detection process and returns the same flagged entries and
explanations a direct audit run over that same period would.

**Acceptance Scenarios**:

1. **Given** a natural-language request that clearly implies a period
   (e.g., "this month," "last quarter"), **When** the admin submits it,
   **Then** the system runs the audit over the corresponding period and
   returns the same flagged entries a direct request for that period would.
2. **Given** a request too vague to determine a period (e.g., "check for
   fraud"), **When** the admin submits it, **Then** the system asks a
   clarifying question rather than guessing a period and risking a
   misleading result.

---

### Edge Cases

- What happens when a date range has too few posted entries for the
  detection method to produce a statistically meaningful result? The
  system MUST clearly say so rather than presenting spurious or arbitrary
  flags.
- What happens when literally none of the evaluated entries are anomalous?
  The system MUST report a clean "no anomalies found" result rather than
  forcing a minimum number of flags to appear.
- What happens when an entry that was previously flagged is later
  corrected (reversed and reposted) by the existing ledger correction flow?
  The original flag MUST remain visible in that audit run's history for
  audit-trail purposes, but MUST be distinguishable as referring to an
  entry that is no longer the active posting.
- What happens when an admin re-runs an audit over a period they've
  already reviewed? Previously reviewed flags MUST show their recorded
  resolution rather than appearing as new, unaddressed items.
- What happens when the AI explanation service is unavailable? The system
  MUST still produce a usable, data-grounded plain-language explanation for
  each flag (describing the actual detected signal) via a fallback, rather
  than showing a flag with no explanation at all.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect statistically unusual posted journal
  entries using an unsupervised outlier-detection method — one that does
  not require pre-labeled examples of past fraud or errors — applied to
  each entry's own attributes (amount, date, accounts involved, and how it
  compares to similar entries), not to free-text reasoning about the
  entry.
- **FR-002**: Every anomaly determination (which entries are flagged, and
  their ranking) MUST come from the deterministic statistical/ML detection
  process — never from the AI/LLM's own judgment. The AI/LLM's only
  permitted role is explaining, in plain language, why an entry the
  detection process already flagged looks unusual. A flag that cannot be
  traced back to the detection process's own output is a defect, not an
  acceptable variation.
- **FR-003**: An admin MUST be able to trigger an audit run over a chosen
  date range (or the entire ledger to date) and receive a ranked list of
  the most anomalous posted journal entries found in that range.
- **FR-004**: Each flagged entry MUST include a plain-language explanation
  that reflects the specific signal(s) that caused it to be flagged (for
  example: an unusually large amount for that account, a suspiciously
  round number, an entry that looks like a duplicate of another, or an
  unusual account pairing) — not a generic "this looks unusual" message.
- **FR-005**: An audit run MUST limit how many entries it flags to a
  practical, review-sized subset of genuine outliers — it MUST NOT flag
  every entry, and MUST NOT flag entries indiscriminately just to produce
  a non-empty result.
- **FR-006**: An admin MUST be able to record a resolution for a flagged
  entry (at minimum: confirmed issue, false positive, or no action
  needed), and that resolution MUST remain visible whenever that flag is
  viewed again, so reviewed items are clearly distinguished from new ones.
- **FR-007**: The system MUST retain a history of past audit runs
  (when each was run, what date range it covered, and how many entries it
  flagged) so an admin can revisit prior audits over time.
- **FR-008**: When a requested date range has too little posted activity
  for the detection method to produce a statistically meaningful result,
  the system MUST clearly indicate this rather than presenting misleading
  or arbitrary flags.
- **FR-009**: Audit runs MUST be triggerable both directly (an explicit
  date range selection) and via the AI chat interface using natural
  language; the chat path MUST trigger the same underlying detection
  process and MUST produce the same flagged entries as a direct request
  for the same resolved period, and MUST ask a clarifying question instead
  of guessing when the intended period can't be confidently determined.
- **FR-010**: Anomaly detection MUST only evaluate active (posted,
  non-reversed) journal entries — matching the ledger feature's existing
  definition of an entry's currently-active posting — so a corrected or
  reversed entry does not itself generate a spurious flag.

### Key Entities *(include if feature involves data)*

- **Audit Run**: A single triggered detection pass over a chosen date
  range (or the whole ledger to date) — records when it was run, the
  period it covered, how many posted entries it evaluated, and how many it
  flagged.
- **Anomaly Flag**: One posted journal entry identified as unusual within
  a specific Audit Run — carries its anomaly ranking/score, the reason
  category or categories that triggered it (e.g., unusual amount, round
  number, duplicate-looking, unusual account pairing), a plain-language
  explanation, and a review resolution (unreviewed by default, or a
  recorded outcome once an admin reviews it).

### Assumptions

- Single business, single admin user — consistent with every other
  feature's assumptions in this project. Detection signals are therefore
  based on entry attributes (amount, timing, account pairing, duplication)
  rather than user-behavior patterns, since there is only one user.
- No pre-labeled examples of past fraud or bookkeeping errors exist to
  train a supervised model — detection relies on unsupervised statistical
  methods that learn what's "normal" from the ledger's own data
  distribution, consistent with the approach named in this feature's
  request and standard practice for general-ledger anomaly detection
  tooling (the "Isolation Forest / clustering" phrasing in the Input
  above names example techniques, not a locked-in implementation choice —
  the actual requirement is deterministic, unsupervised statistical
  detection, decided at planning time).
- A flag is advisory only: this feature never blocks, reverses, edits, or
  auto-corrects a journal entry or account coding on its own — it surfaces
  entries for human review, consistent with this project's existing
  human-in-the-loop principle for judgment calls.
- Audit runs are triggered on demand, not on an automatic schedule, for
  this feature's initial scope — consistent with how reporting and
  reconciliation are also on-demand in this system today.
- What counts as "too little data" for a meaningful audit run is a
  reasonable implementation-level default (a small minimum count of posted
  entries in the requested range), not a business-scope decision requiring
  clarification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin can run an audit over any chosen period and see a
  result — either flagged entries or a clear "no anomalies found" outcome
  — in under 30 seconds, with no manual entry-by-entry review required to
  get that first pass.
- **SC-002**: Every flagged entry's plain-language explanation accurately
  reflects the actual signal(s) that caused it to be flagged, verifiable
  against that entry's real data 100% of the time — no fabricated or
  generic reasoning.
- **SC-003**: For an audit run over a period with sufficient historical
  data, no more than 10% of evaluated entries are flagged, keeping each
  run's review effort practical rather than overwhelming.
- **SC-004**: 100% of anomaly flags and rankings are traceable back to the
  deterministic detection process's own output — never something
  introduced independently by the AI/LLM.
- **SC-005**: A resolution recorded on a flagged entry remains visible and
  correctly attributed 100% of the time the entry is viewed again, whether
  from the original audit run or from audit history.
