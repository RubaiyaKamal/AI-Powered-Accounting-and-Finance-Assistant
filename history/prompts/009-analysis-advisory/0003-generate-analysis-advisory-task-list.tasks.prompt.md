---
id: 0003
title: Generate analysis advisory task list
stage: tasks
date: 2026-07-28
surface: agent
model: claude-sonnet-5
feature: 009-analysis-advisory
branch: 009-analysis-advisory
user: Rubaiya-Kamal
command: /sp.tasks
labels: ["analysis", "advisory", "nl-qa", "forecasting", "tasks"]
links:
  spec: specs/009-analysis-advisory/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/009-analysis-advisory/tasks.md
tests: []
---

## Prompt

now create the tasks

## Response snapshot

Generated `specs/009-analysis-advisory/tasks.md` — 25 tasks across 7
phases (Setup, Foundational, US1–US4, Polish), following this repo's
established checklist format (`- [ ] T0XX [P?] [USn] Description` with
exact file paths).

Key sequencing decision, called out explicitly in a note ahead of Phase
6 (US4): `resolve_spending_request` (T004) is written *once*, in US1's
phase, with full knowledge of all four request kinds (`amount`,
`breakdown`, `comparison`, `forecast`) from the start — because
correctly discriminating "amount" from the other three requires knowing
about all of them, even though only the `amount` branch is wired into
the query endpoint at that point. Each later user story then only adds
a new routing branch to the same already-built endpoint (T013 for
breakdown/comparison, T018 for forecast) and its own direct REST
endpoint — never re-touching the resolver's fundamental shape. This
means US4 (P4, NL access to patterns/forecast) needed no new backend
machinery by the time US3 finished; its two tasks are verification/
frontend-rendering confirmation only. This is a deliberate divergence
from `005-reporting`'s Phase 7 precedent (which deferred its entire NL
layer to one late cross-cutting phase) — chosen here specifically so
US1, the P1 MVP, remains genuinely deliverable early and standalone, as
spec.md's priority ordering requires, rather than blocked on the whole
feature existing first.

Also included: US1 (T003–T008, amount via NL only, no direct REST form
per the plan's explicit decision), US2 (T009–T015, breakdown +
comparison, both direct and NL), US3 (T016–T020, forecast via
`scikit-learn` `LinearRegression`, both direct and NL), and Polish
(T023–T025, including the constitution-mandated workflow diagram
update flagged as a pending action item in `plan.md`'s Constitution
Check).

## Outcome

- ✅ Impact: Full task breakdown ready for `/sp.implement`; MVP scope
  (US1) and incremental delivery plan both spelled out.
- 🧪 Tests: None generated (not requested in spec.md); `quickstart.md`'s
  10 steps remain the manual validation plan referenced from `tasks.md`.
- 📁 Files: `specs/009-analysis-advisory/tasks.md` (new).
- 🔁 Next prompts: Awaiting user instruction to begin `/sp.implement`
  (established pattern: "now build this").
- 🧠 Reflection: The US1/US4 sequencing tension flagged before writing
  this file (US1 nominally P1 but structurally dependent on the
  resolver knowing all four kinds) resolved cleanly by separating "the
  resolver's classification vocabulary" (cheap prompt text, can be
  complete from the start) from "the endpoint's routing implementation"
  (must be incremental, since the underlying compute functions don't
  exist yet) — these are different concerns that don't have to phase
  together, unlike `005-reporting`'s case where narration content itself
  differed per report type.

## Evaluation notes (flywheel)

- Failure modes observed: `create-phr.sh` produced a template with all
  placeholders unresolved (no automatic substitution) — filled in
  manually via the agent-native fallback path described in the sp.tasks
  skill's PHR instructions.
- Graders run and results (PASS/FAIL): Task format validation — PASS
  (all 25 tasks follow `- [ ] T0XX [P?] [USn] Description` with file
  paths; Setup/Foundational/Polish correctly carry no story label).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
