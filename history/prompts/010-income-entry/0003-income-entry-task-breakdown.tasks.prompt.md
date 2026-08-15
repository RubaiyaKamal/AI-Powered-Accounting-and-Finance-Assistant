---
id: 0003
title: Income entry task breakdown
stage: tasks
date: 2026-08-15
surface: agent
model: claude-sonnet-5
feature: 010-income-entry
branch: 010-income-entry
user: Rubaiya-Kamal
command: /sp.tasks
labels: ["income-entry", "ledger", "reporting"]
links:
  spec: specs/010-income-entry/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/010-income-entry/tasks.md
tests:
 - none (tasks stage; no code yet)
---

## Prompt

(No new user input at this stage — continuing the /sp.specify → /sp.plan →
/sp.tasks → /sp.implement sequence for 010-income-entry, per the project's
constitutional Principle I, on the approved plan from PHR 0002.)

## Response snapshot

Ran `check-prerequisites.sh --json`, confirmed all design docs present, and
read `002-ledger-journal-entries`'s `tasks.md` as the in-repo precedent for
format and phase structure (no test tasks, matching that feature's
precedent since TDD wasn't explicitly requested here either). Also read the
frontend `ReportViewer.tsx` and `Sidebar.tsx` directly to confirm two plan
assumptions before turning them into tasks: (1) the reports UI is fully
generic over whatever `revenue_lines`/`equity_lines` the API returns, so
User Story 3 needs zero new frontend code — only a verification task; (2)
the nav sidebar is a hardcoded `LINKS` array needing one new entry
(`/income`), the one existing-file frontend touch-point for this feature.

Produced `tasks.md` with 30 tasks across 6 phases: Setup (T001, file
skeleton), Foundational (T002–T008: `IncomeSource`/`IncomeEntry` models,
the `JournalEntry` nullable-columns + `income_entry_id` generalization, the
migration, and matching Pydantic schemas — all blocking), US1/P1 (T009–T018,
the MVP: income sources, `post_income_journal_entry`, entry creation, the
form/page/sidebar-link), US2/P2 (T019–T025: list/filter/edit/delete with
reversal-and-repost on amount/date/source change, mirroring `002`'s
coding-correction pattern), US3/P2 (T026, a single verification task — no
new code, since Decision 1 in `research.md` already made the reports
generic), and Polish (T027–T030: workflow diagram update — constitution
Principle V, not optional — README, quickstart run, cleanup). Documented
phase/task dependencies, parallel-execution opportunities, and an
incremental-delivery strategy (US1 alone is a demoable MVP).

## Outcome

- ✅ Impact: Actionable, dependency-ordered task list ready for /sp.implement; confirmed via direct code reading (not assumption) that US3 requires no new reporting or report-UI code.
- 🧪 Tests: none yet (tasks stage)
- 📁 Files: specs/010-income-entry/tasks.md
- 🔁 Next prompts: /sp.implement for 010-income-entry
- 🧠 Reflection: Verifying the "reports need zero changes" claim against the actual ReportViewer.tsx (not just reporting_service.py) before writing US3's tasks turned what could have been several speculative frontend tasks into one honest verification task.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): n/a (task-breakdown stage; no gate)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
