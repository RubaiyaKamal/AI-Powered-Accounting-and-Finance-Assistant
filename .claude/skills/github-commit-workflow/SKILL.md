---
name: github-commit-workflow
description: Enforces this project's required Git/GitHub workflow for the AI-Powered Accounting Assistant assignment — one branch per feature, merging into main only via pull request, small/frequent conventional commits (never one giant final commit), and required repo artifacts (README, /specs, workflow diagram, Docker setup). Use this skill BEFORE running any git command that commits, branches, pushes, or merges in this repo, whenever the user asks to "commit this", "push this feature", "merge into main", "open a PR", or "let's start on <feature>" — even if they don't mention Git explicitly. Also use it as a pre-submission checklist to verify the repo meets every version-control requirement before the assignment is submitted.
---

# GitHub Workflow for the Accounting Assistant Assignment

This repo is graded partly on *how* it was built, not just what it contains. The grader can see branch history, PR history, and commit granularity — a repo with all the right features but one giant "final commit" on main gets heavily penalized. This skill exists so that habit never happens here.

## Core rule: nothing lands on `main` except through a merged PR

Before writing any code for a new piece of work, check the current branch:

```bash
git branch --show-current
```

If it's `main` (or you're not sure a branch exists yet for this work), create one **before** touching files:

```bash
git checkout -b feature/<short-kebab-name>
```

### Branch naming
Name the branch after the feature being built, not the person or the date:
- `feature/expense-entry` — CRUD for expense records
- `feature/income-entry` — CRUD for income records
- `feature/ai-agent` — OpenAI Agents SDK integration / agent tool wiring
- `feature/pl-report` — Profit & Loss generation
- `feature/balance-sheet` — Balance sheet generation
- `feature/audit-flow` — monthly audit / anomaly detection
- `feature/docker-setup` — Dockerfiles + docker-compose
- `fix/<short-description>` for bug fixes, e.g. `fix/expense-date-validation`

One branch per feature — not per file, not per day, and not one mega-branch for "backend" that quietly absorbs five unrelated features. If a "feature" is naturally two independent pieces of work (e.g. the ledger schema and the P&L endpoint that reads it), that's two branches and two PRs.

## Commit discipline: small, frequent, one logical change each

A commit should do one thing you could describe without the word "and". If you catch yourself writing a commit message with "and" in it, split the commit.

Use conventional commit format: `type(scope): short description`

| type | when |
|---|---|
| `feat` | new capability (an endpoint, a UI component, an agent tool) |
| `fix` | bug fix |
| `refactor` | restructuring without behavior change |
| `test` | adding/updating tests |
| `docs` | README, specs, comments |
| `chore` | tooling, deps, config, Docker |
| `style` | formatting only |

Examples grounded in this project's stack (Next.js frontend, FastAPI+Pydantic backend, PostgreSQL, OpenAI Agents SDK):
- `feat(api): add monthly audit endpoint`
- `fix(expenses): correct date validation on entry form`
- `feat(agent): wire P&L tool call into OpenAI Agents SDK`
- `feat(ui): add expense entry form`
- `fix(reconciliation): handle unmatched bank feed lines`
- `docs(readme): add docker-compose run instructions`
- `chore(docker): add postgres service to docker-compose`

Commit as you complete each working increment — after a passing endpoint, after a working form, after a fixed bug — not at the end of a multi-day session. If a session produces more than ~150-200 changed lines in one commit, that's a signal to have committed earlier along the way.

## Opening the PR

Once a branch's feature is functionally complete (it doesn't need to be the *whole* app, just that one feature working), push it and open a PR into `main`:

```bash
git push -u origin feature/<name>
gh pr create --title "feat: <feature summary>" --body "$(cat <<'EOF'
## Summary
- what this branch adds

## Test plan
- how to verify it works
EOF
)"
```

Don't let a branch quietly grow to contain three unrelated features before its first PR — open PRs early and often, matching the branch-per-feature principle. Never merge by pushing directly to `main` or fast-forwarding locally; merge through the PR on GitHub so there's a reviewable record.

## Required repo artifacts

Before submission, the repo root must contain:

- **`README.md`** — clear setup + run instructions: cloning, installing dependencies, environment variables (OpenAI API key, DB connection string), `docker-compose up`, and how to run the frontend/backend/tests individually if not using Docker.
- **`/specs`** — the SDD (spec-driven development) documents: one subfolder per feature with its spec/plan/tasks, e.g. `specs/expense-entry/spec.md`. If this project is using the `sp.specify` / `sp.plan` / `sp.tasks` skills, their output already lands here — just make sure it's committed, not left local.
- **A workflow/architecture diagram** — image, PDF, or a link to one, showing how the frontend, backend, database, and AI layer communicate. The system architecture described in `research/task-automation-mapping.md` (Section 6) is the source content for this — render it as an actual diagram (e.g. a Mermaid diagram exported to an image, or a draw.io/PDF export) and reference it from the README.
- **Docker setup** — a `Dockerfile` for the frontend, a `Dockerfile` for the backend, and a `docker-compose.yml` that brings up frontend + backend + PostgreSQL together.

If any of these are missing when you're asked to "get this ready to submit" or "check the repo," flag it — don't wait to be asked specifically about each one.

## Pre-submission checklist

Run through this before the repo URL is submitted:

- [ ] Every merged feature has its own `feature/*` (or `fix/*`) branch — check with `git log --merges --oneline` or the GitHub PR list
- [ ] No commit is a disproportionate dump of the whole project relative to the rest of history (no "final commit")
- [ ] Commit messages follow `type(scope): description`
- [ ] All merges into `main` happened via PR, not direct push
- [ ] `README.md` exists with setup + run instructions
- [ ] `/specs` folder exists with SDD documents
- [ ] A workflow diagram exists (file in-repo or a linked doc) and is referenced from the README
- [ ] Docker setup exists (`Dockerfile`(s) + `docker-compose.yml`) and `docker-compose up` actually brings the stack up
- [ ] The GitHub repo is public (or shared-access) and the URL is ready to hand in
