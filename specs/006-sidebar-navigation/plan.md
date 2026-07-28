# Implementation Plan: Sidebar Navigation & Header Logo

**Branch**: `006-sidebar-navigation` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-sidebar-navigation/spec.md`

## Summary

Move the app's page-navigation links out of the top navbar into a new left
sidebar with active-link highlighting, and add a logo to the header's right
side. Purely a frontend layout restructuring — no new dependency, no
backend change, no data model. Scoped down (per spec) from a fuller design
system change: no icons on nav links (the app has none today), no
responsive/collapsible behavior (no requirement for it), no new asset
pipeline for the logo (inline SVG instead of an image file, since
`frontend/public/` doesn't exist yet).

## Technical Context

**Language/Version**: TypeScript / Node 20, Next.js (App Router), React —
same frontend stack as every prior feature; no backend involved.
**Primary Dependencies**: None new — `next/link` and `next/navigation`'s
`usePathname()` (both already available via Next.js itself).
**Storage**: N/A — no data model.
**Testing**: Manual browser verification (per this feature's quickstart
below, folded into this plan rather than a separate file — no data model or
API to warrant one); no automated test suite exists for frontend layout in
this codebase yet, so none is added here disproportionately.
**Target Platform**: Web application, same Docker frontend service.
**Project Type**: web (frontend-only change)
**Performance Goals**: N/A — static layout, no runtime cost concern.
**Constraints**: Must not alter backend behavior/API/data model (FR-005).
Must not break any existing page's rendering (FR-004, SC-002).
**Scale/Scope**: 4 nav links today (1 of which, `/reports`, doesn't exist
yet pending `005-reporting`); single admin user, same as every prior
feature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Spec-Driven Development | ✅ PASS | This minimal `spec.md` exists before implementation; scaled proportionally to a UI-only change, not skipped |
| II. Deterministic Financial Computation | N/A | No financial computation involved — pure layout |
| III. Human-in-the-Loop for Regulated/High-Risk Actions | N/A | No posting/matching/audit action involved |
| IV. Branch-Per-Feature & PR-Only Merges | ✅ PASS | Own branch `006-sidebar-navigation`, independent of `005-reporting`; merges to `main` only via PR |
| V. Documented Architecture & Workflow | ✅ PASS (no action needed) | This change doesn't alter the frontend↔backend↔agent↔database request flow the diagram documents — it only restructures where existing links render client-side; no diagram update required |
| VI. Simplicity & Traceability | ✅ PASS | No new dependency; inline SVG over a new asset pipeline; text-only sidebar links over introducing an icon library; no responsive logic without a stated requirement |

**Gate result**: PASS, no violations, no Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-sidebar-navigation/
├── plan.md    # This file
└── spec.md    # Minimal spec (no research.md/data-model.md/contracts/ — no data model, no API)
```

### Source Code (repository root)

```text
frontend/
└── src/
    ├── app/
    │   ├── layout.tsx      # MODIFIED: remove old <nav>, add <Logo/> to header, wrap <Sidebar/>+<main> in .app-shell
    │   └── globals.css     # MODIFIED: header flex row, .app-shell/.app-sidebar/.app-logo rules, re-scope main
    └── components/
        ├── Sidebar.tsx     # NEW: client component, nav links + usePathname() active-state
        └── Logo.tsx        # NEW: inline SVG icon component
```

**Structure Decision**: No new top-level directories — modifies the
existing shared layout and adds two small components to the existing
`frontend/src/components/` directory, consistent with every prior
feature's frontend structure.

## Verification (in place of a separate quickstart.md)

- Start the frontend and visually confirm: header shows the title on the
  left and the logo on the right; sidebar lists all four links with the
  current page highlighted; page content renders beside the sidebar, not
  re-centered under it.
- Click through all sidebar links and confirm routing + active-highlight
  updates (`/reports` 404s until `005-reporting` merges — accepted).
- `npx tsc --noEmit` clean.

## Complexity Tracking

*No entries — Constitution Check passed without violations.*
