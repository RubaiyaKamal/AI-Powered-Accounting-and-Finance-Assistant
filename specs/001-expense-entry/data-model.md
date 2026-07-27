# Phase 1 Data Model: Expense Entry

Derived from the Key Entities section of `spec.md` and the storage decisions
in `research.md`.

## ExpenseEntry

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `amount` | numeric(12,2) | not null, `> 0` (FR-002) | rejected at API layer before hitting DB, DB constraint as a second line of defense |
| `date` | date | not null (FR-003) | future dates allowed (Edge Cases) |
| `category_id` | FK → Category.id | not null | always resolved before the row is written — either user-chosen or AI-suggested (FR-010) |
| `category_source` | enum(`user`, `ai_suggested`) | not null, default `user` | flips to `user` the moment an AI-suggested category is overridden (FR-011) |
| `description` | text | nullable | free text |
| `source` | enum(`manual`, `natural_language`) | not null | which path created this entry (User Story 1 vs. 3) |
| `created_at` | timestamptz | not null, default now() | FR-013 |
| `updated_at` | timestamptz | not null, default now(), updated on every edit | FR-013 |

**Validation rules** (enforced in the Pydantic request model, not just the DB):
- `amount` must be strictly greater than 0 (FR-002).
- `amount` with more than 2 decimal places or above a configurable large-value
  threshold is flagged back to the caller for confirmation rather than
  silently accepted (Edge Cases — likely typo).
- `date` is required; no upper bound (future dates are valid per Edge Cases).
- `category_id` must reference an existing `Category` row.

**Relationships**: has many `ExpenseEntryEditHistory` rows (one per field
change); belongs to one `Category`.

## Category

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `name` | text | not null, unique (case-insensitive) | prevents "Utilities" / "utilties" fragmentation |
| `is_custom` | boolean | not null, default `true` | `false` only for the seeded starter set |

**Seed data** (migration-time, `is_custom=false`): Utilities, Rent, Salaries,
Supplies (FR-014's starter set, matching the assignment's own examples).

**Relationships**: has many `ExpenseEntry` rows.

## ExpenseEntryEditHistory

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID (PK) | not null, default random | |
| `expense_entry_id` | FK → ExpenseEntry.id | not null, `ON DELETE CASCADE` | history is meaningless without its parent entry (research.md) |
| `field_name` | text | not null | one of `amount`, `date`, `category_id`, `description` |
| `old_value` | text | nullable | stored as text regardless of the field's real type, for simplicity and uniform display (FR-015) |
| `new_value` | text | nullable | |
| `changed_at` | timestamptz | not null, default now() | FR-015 |

**Relationships**: belongs to exactly one `ExpenseEntry` (spec's Key Entities
section).

**State transitions**: none beyond simple row lifecycle (created on entry
creation and on each subsequent edit; deleted via cascade when the parent
entry is deleted — no independent update/delete path for history rows,
since history must stay an accurate record of what happened).
