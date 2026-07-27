<!--
Sync Impact Report
==================
Version change: 1.0.1 → 1.0.2 (patch: deliverable resolved)
Modified principles: V. Documented Architecture & Workflow (text updated to
  record the diagram's shareable URL)
Added sections: none
Removed sections: none
Templates requiring updates:
  - README.md ............................................ ✅ updated with
    the shareable diagram URL
Follow-up TODOs: none — Principle V is now fully satisfied.
-->
<!--
Sync Impact Report (previous)
==================
Version change: 1.0.0 → 1.0.1 (patch: clarification / deliverable resolved)
Modified principles: V. Documented Architecture & Workflow (text unchanged;
  clarified that the diagram file now exists)
Added sections: none
Removed sections: none
-->
<!--
Sync Impact Report (previous)
==================
Version change: TEMPLATE → 1.0.0 (initial ratification)
Modified principles: N/A (first adoption; all six principles newly authored)
Added sections:
  - Core Principles I–VI (Spec-Driven Development, Deterministic Financial
    Computation, Human-in-the-Loop for Regulated Actions, Branch-Per-Feature &
    PR-Only Merges, Documented Architecture & Workflow, Simplicity & Traceability)
  - Technology & Architecture Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none (template placeholders only)
-->

# AI-Powered Accounting Assistant Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
Every feature MUST have a written specification — what it does, its inputs,
outputs, and edge cases — committed under `/specs/<feature-name>/spec.md`
*before* implementation begins. Code that has no corresponding spec MUST NOT
be merged. Specs are produced via `/sp.specify`, refined via `/sp.clarify`,
planned via `/sp.plan`, and broken into tasks via `/sp.tasks` — in that order.
Rationale: this project is graded explicitly on whether development followed
specifications, not just on the resulting feature set; writing the spec first
is also how ambiguous accounting behavior (e.g., what counts as a duplicate
entry, how partial-month audits should behave) gets resolved before code
makes an implicit, undocumented choice.

### II. Deterministic Financial Computation
All numeric financial outputs — ledger balances, trial balance, P&L, balance
sheet, cash flow, reconciliation totals — MUST be produced by deterministic
backend computation (SQL/pandas/ledger-service logic), never generated
directly as text by the LLM. The AI agent's role is limited to: interpreting
intent, choosing and calling the correct backend tool, and narrating the
returned result in natural language. An agent response that contains a
financial figure not traceable to a tool-call result is a bug.
Rationale: LLMs hallucinate numbers; an accounting assistant that occasionally
invents a balance is worse than useless. Keeping computation deterministic and
tool-mediated keeps every figure auditable back to a database query.

### III. Human-in-the-Loop for Regulated or High-Risk Actions
Audit anomaly flags, fraud-pattern detection, and tax/compliance summaries
MUST be presented for human review and MUST NOT be auto-finalized or
auto-filed by the agent. Journal postings and category corrections below a
configured confidence threshold MUST route to a review queue rather than
committing silently. The agent MAY draft, flag, and explain; a human decides.
Rationale: these are the actions with real regulatory, financial-statement,
and reputational consequences if wrong; the research phase of this project
identified them explicitly as requiring mandatory sign-off, not full
automation.

### IV. Branch-Per-Feature & PR-Only Merges
Every feature or fix is developed on its own `feature/*` or `fix/*` branch and
merged into `main` only via a reviewed pull request — never by direct push or
local merge to `main`. Commits MUST be small, frequent, and use conventional
commit messages (`feat:`, `fix:`, `docs:`, `chore:`, etc.); a single large
"final commit" is a violation of this principle, not a style preference.
Rationale: this is an explicit, graded assignment requirement, and it is
enforced day-to-day by the repository's `github-commit-workflow` skill
(`.claude/skills/github-commit-workflow/SKILL.md`) — this principle makes
that workflow a constitutional requirement rather than an optional habit.

### V. Documented Architecture & Workflow
The system's user flow, AI-agent flow (UI → API → agent → tools → database →
response), and data flow MUST be captured in a single workflow diagram built
in Lucidchart or draw.io (the tool choice is fixed by the assignment, not a
free choice), kept reachable via a shareable URL recorded in this file and in
`README.md`. Any change that alters how a request moves between frontend,
backend, agent, and database MUST update the diagram in the same pull request
that makes the change.

**Diagram**: source at `docs/workflow-diagram.drawio` (draw.io/diagrams.net
format). **Shareable URL**:
https://drive.google.com/file/d/1D4b_y4cMLGdlJ-qPyWbK3mcLiT9Fn680/view?usp=sharing
Rationale: the diagram is a required, separately graded deliverable, and a
diagram that drifts from the real system is worse than no diagram — tying its
update to the same PR is what keeps it honest.

### VI. Simplicity & Traceability
Prefer the smallest change that satisfies the current spec; do not add
abstractions, feature flags, or configurability for hypothetical future needs
(YAGNI). Every non-trivial implementation or architectural decision MUST be
traceable to either a spec (`/specs/`), a Prompt History Record
(`history/prompts/`), or, for significant architectural choices, an
Architecture Decision Record (`history/adr/`) created via `/sp.adr`.
Rationale: this project's grading explicitly looks at *how* the system was
built, not only the final code — traceability from decision back to spec or
PHR/ADR is how that history stays legible after the fact.

## Technology & Architecture Constraints

The stack is fixed by the research phase of this project (see
`research/task-automation-mapping.md`) and changes to it are governance-level
decisions, not casual refactors:

- **Frontend**: Next.js (TypeScript), communicating with the backend over
  REST/JSON.
- **Backend/API**: Python + FastAPI, dependencies managed with `uv`, all
  request/response payloads validated with Pydantic models.
- **Database**: PostgreSQL, accessed through an ORM (SQLAlchemy), with
  Pydantic schemas mirroring the database schema.
- **AI Layer**: OpenAI Agents SDK with GPT-4o mini as the underlying model,
  exposed to the rest of the system only through backend-defined tool
  functions — the agent never touches PostgreSQL directly (see Principle II).
- **Containerization**: Docker, with a `Dockerfile` each for frontend and
  backend and a `docker-compose.yml` wiring frontend, backend, and PostgreSQL
  together; this is a required, separately checked deliverable.

Deviating from this stack (e.g., swapping the agent framework, the model
provider, or the database) requires amending this constitution first, not
just changing code, since the research paper's framework/model comparison and
rationale (Sections 2–3 of `research/task-automation-mapping.md`) depend on
these choices.

## Development Workflow & Quality Gates

The SDD command sequence for any new feature is:
`/sp.constitution` (this file, rarely re-run) → `/sp.specify` → `/sp.clarify`
(optional but recommended for ambiguous accounting behavior) → `/sp.plan` →
`/sp.tasks` → `/sp.implement`. `/sp.analyze` MAY be run after `/sp.tasks` and
before `/sp.implement` to check spec/plan/task consistency.

Before a feature's pull request is opened for merge, it MUST satisfy:
- A spec exists under `/specs/<feature-name>/` and the implementation matches
  it (Principle I).
- No financial figure in the diff is produced by the LLM directly
  (Principle II).
- Any audit/fraud/tax-summary code path routes through human review before
  being treated as final (Principle III).
- The branch/commit/PR discipline in Principle IV was followed.
- If the change alters user/agent/data flow, the workflow diagram
  (Principle V) has been updated and its URL is still valid.

Before the overall project is submitted, the repository MUST contain: a
`README.md` with setup and run instructions, a `/specs` folder showing specs
preceded code, the workflow diagram's shareable URL, and a working Docker
setup — mirroring the pre-submission checklist already maintained in
`.claude/skills/github-commit-workflow/SKILL.md`.

## Governance

This constitution supersedes ad-hoc conventions and prior informal agreements
for this repository. Amendments are made by editing this file directly:
propose the change, update the affected principle(s), bump
`CONSTITUTION_VERSION` per semantic versioning (MAJOR for incompatible
principle removal/redefinition, MINOR for a new principle or materially
expanded guidance, PATCH for wording/clarification only), update
`LAST_AMENDED_DATE`, and prepend a fresh Sync Impact Report summarizing what
changed and which dependent templates/docs were checked.

Every pull request implicitly asserts compliance with the principles above;
a reviewer (human or agent) who notices a violation should block the merge
rather than wave it through. Any deliberate exception (e.g., a temporary
non-deterministic estimate shown to users) MUST be justified in writing in
the relevant `plan.md`'s Complexity Tracking table, not silently introduced.
Day-to-day operational guidance for the coding agent lives in `CLAUDE.md`,
which defers to this file for principle-level rules.

**Version**: 1.0.2 | **Ratified**: 2026-07-27 | **Last Amended**: 2026-07-28
