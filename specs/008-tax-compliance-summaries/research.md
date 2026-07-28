# Phase 0 Research: Tax & Compliance Summaries

The backend/frontend/database/AI stack is fixed by the constitution and
already established by prior features — no `NEEDS CLARIFICATION` markers
remain in Technical Context. This document records the feature-scoped
design decisions: how retrieval is implemented, how figures and citations
stay grounded, and how the sign-off/immutability guarantee is enforced.

## Decision: in-process embedding retrieval — no new dependency, no vector database

**Decision**: Reference-document passages are embedded once at add-time
using OpenAI's embeddings API, called via the `openai` Python client
already installed transitively through `openai-agents` (no new package).
At summary-request time, the query is embedded once and ranked against
all stored passage embeddings via cosine similarity computed with `numpy`
(already present since `007`'s `scikit-learn` dependency) — brute-force,
in-process, no index structure. When no `OPENAI_API_KEY` is configured,
retrieval falls back to a deterministic keyword-overlap score (shared
words between the query and each passage) instead of failing closed.
**Rationale**: The user's request named "RAG" as the method — this is a
real retrieval step ahead of generation, not the LLM being handed the
whole document library to sort through itself. At this project's
realistic scale (one admin's own reference library — realistically tens
of documents, at most a few hundred paragraph-sized chunks), brute-force
cosine similarity over an in-memory array is a sub-second operation with
no need for approximate-nearest-neighbor indexing. Needing zero new
dependencies (both `openai` and `numpy` are already present) keeps this
squarely within Principle VI's preference for the smallest change that
satisfies the spec. The keyword-overlap fallback mirrors every other
AI-touching feature in this codebase, all of which degrade gracefully
rather than fail when no API key is configured.
**Alternatives considered**: `pgvector` (rejected — a new Postgres
extension and a new SQLAlchemy vector-column dependency, adding real
infrastructure weight for a retrieval workload this project's scale
doesn't need); a dedicated vector database service (rejected — new
deployment/infrastructure complexity far beyond a single-business,
single-admin scope); keyword-only retrieval as the sole method, no
embeddings at all (rejected as the primary method — weaker semantic
matching than embeddings, though it's exactly what the no-API-key
fallback uses, since some retrieval is strictly better than none when a
key isn't configured).

## Decision: chunk documents into paragraph-sized passages; retrieve and cite at passage level

**Decision**: When a document is added, its text is split into
paragraph-sized chunks (split on blank lines); each chunk is embedded and
stored as its own row. Retrieval ranks and returns chunks, not whole
documents, and a summary cites specific chunks.
**Rationale**: Precise citations (FR-005) — an admin reviewing a draft
should see exactly which passage supports a statement, not have to
re-read an entire reference document to find it. Chunk-level embeddings
also retrieve more accurately than whole-document embeddings, whose
signal gets diluted the longer and more topically mixed a document is.
**Alternatives considered**: Whole-document embedding and citation only
(rejected — coarser citations, weaker relevance for anything but very
short documents).

## Decision: reuse `ReportingService.profit_and_loss` verbatim for period figures

**Decision**: A summary's financial figures (total revenue, total
expenses, net profit) come directly from calling the existing
`ReportingService.profit_and_loss(session, start, end)` — no new
aggregation logic is written for this feature.
**Rationale**: This exact computation already exists, is already
deterministic, and is already exercised by `005-reporting`. Duplicating
it here would be redundant complexity (Principle VI) for an identical
result — nothing in this feature's spec calls for different figures than
a P&L already provides.
**Alternatives considered**: A tax-specific aggregation function —
rejected, no functional requirement asks for anything P&L doesn't already
compute.

## Decision: citations and figures are frozen onto the summary row at generation time

**Decision**: `TaxSummary` stores its figures as plain values and its
cited passages as a denormalized snapshot (document title + chunk text
copied in) at generation time — not live foreign keys to
`TaxRulesDocumentChunk` rows.
**Rationale**: FR-007's immutability guarantee, and the spec's explicit
edge case that removing a reference document must not alter or blank out
an already-signed-off summary that cited it. A live FK would either dangle
(if the chunk is deleted) or silently reflect edits (if chunks could be
edited) — either way violating "a signed-off summary remains exactly what
was signed off." Mirrors `007`'s `AnomalyFlag`, which stores what was
actually detected rather than re-deriving it live on every read.
**Alternatives considered**: Foreign-key references to chunks with
`ON DELETE SET NULL`/`RESTRICT` — rejected, still allows a chunk's
*content* to end up orphaned or requires forbidding document deletion
entirely, either of which is more complex than just copying a few
kilobytes of text once at generation time.

## Decision: staleness check recomputes and compares at sign-off time

**Decision**: When an admin attempts to sign off on a draft, the system
recomputes `profit_and_loss` fresh for the draft's period and compares it
to the figures already stored on the draft. A mismatch blocks sign-off
with a warning that the draft is out of date (FR-009).
**Rationale**: Simplest correct implementation of the requirement — no
separate versioning, snapshot-hash, or change-tracking infrastructure is
needed; the same deterministic function already used to produce the
figures is exactly what's needed to check whether they've changed.
**Alternatives considered**: A stored hash/checksum of the period's
underlying journal entries, checked for drift — rejected, more moving
parts than directly recomparing the computed totals themselves, for the
same outcome.

## Decision: two narrow LLM calls, following the established codebase pattern

**Decision**: `draft_summary_narrative(figures, cited_passages)` — sees
only the already-computed figures and already-retrieved passages, never
raw ledger rows or the full document library, and writes the summary's
prose. `resolve_summary_request(question, today)` — the natural-language
entry point (US4), sees only the question text and today's date, and
resolves a date range or marks itself unable to (mirroring
`resolve_report_request`/`resolve_audit_request`'s exact shape, including
`007`'s "unresolvable, don't guess" behavior rather than reporting's
silent-default behavior, since guessing a tax period is exactly the kind
of thing this feature's regulatory-risk framing argues against).
**Rationale**: Consistent with `005`/`007`'s established precedent —
keeps the AI's role strictly bounded to narration/classification, never
computation or retrieval-scoring itself.
**Alternatives considered**: None seriously — this is now the established
codebase-wide shape for every reporting-adjacent natural-language
feature.

## Decision: direct endpoints in a new `api/tax.py`; NL endpoint in the existing `api/agent.py`

**Decision**: Document-library and summary endpoints get a new
`backend/src/api/tax.py` router. The one natural-language endpoint
(`POST /api/agent/tax/query`) is added to the existing
`backend/src/api/agent.py`.
**Rationale**: Identical reasoning already established in `005` and `007`
— `api/agent.py` is this codebase's single home for every agent-mediated
endpoint; direct data endpoints get their own resource-oriented router.
**Alternatives considered**: None — this is now settled codebase
convention.
