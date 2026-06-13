---
status: decided
authored_by: human
date: 2026-06-11
phase: refine-requirements-v2 / Phase 1 — Foundation
supersedes: exploration playbook 02 (DB-canonical / per-element-ULID keystone)
---

# Requirements v2: Files-Canonical + Thin DB Spine

> **One line:** The `.collab.md` file stays the single byte-canonical source of truth. The DB is a
> thin spine of version snapshots + comment rows + a conflict hash — **no per-element IDs, no
> anchoring engine.** This note is the contract Phase 1 implements and the marker every later phase
> reads before touching this subsystem.

## Why this note exists

Exploration's playbooks proposed a DB-canonical "keystone": every requirement element gets a stored
ULID, the DB becomes authoritative, and comments anchor to those IDs. **Plan review rejected that.**
A future phase that drifts back toward stored anchors (the playbooks still describe ULIDs) should be
corrected against *this* document. If you find yourself making an architecture decision here, stop —
it was already settled at plan review; quote it, do not re-derive it.

## The decision

- **Files are canonical.** `refined_requirements.collab.md` is the single byte-canonical source of
  truth and is **never mutated** by this subsystem (FR-007). The live file keeps evolving in the goal
  folder; only the current version lives there (FR-011).
- **The DB holds only a thin spine.** Version snapshots, comment rows, and a content hash for conflict
  detection. Nothing else.

## The three deterministic-machinery sites we keep

These are the *only* places where being wrong means **silent data loss**, so they — and only they —
get deterministic machinery:

| Site | Why it must be deterministic | Canonical identifier |
|------|------------------------------|----------------------|
| Comment rows exist | A reviewer's comment must never be lost | `requirement_comments` |
| Version snapshots are recorded | A prior version must always be recoverable | `requirement_versions` |
| Conflict detection = content-hash compare | A silent overwrite of concurrent edits must be caught | `requirements_render.hashing.content_hash` |

The append-only `comment_events` trail backs the comment lifecycle (created / resolved / reopened /
orphaned / relocated) so history retrieval is free. Comment *CRUD* itself is Phase 4 — Phase 1 only
ships the `requirement_versions` snapshot service.

## What we deleted, and why

- **No per-element ID.** No per-element ULID, no element surrogate key.
- **No anchoring engine.** There is no `block_anchor` column, no heading-path anchor, and no ordinal
  anchor — no anchoring engine of any kind, and no deterministic re-location machinery.
- `Block.ref` (`"US1"`, `"FR-007"`) is **parsed in-memory only** — never persisted to a DB column and
  never used as a comment anchor (plan-review Decision #2).

Instead, comments store `quoted_text` (the reviewer's selection, verbatim) plus a `section_hint`
(nearest heading at capture time — a hint, not a key). They are **re-located at runtime by a Claude
subagent** (trust-and-iterate, a Phase 4 concern). This follows plan-review decisions **#1 and #9** in
`plan.collab.md`'s "Decisions Resolved at Plan Review": delete the deterministic anchoring engine;
re-anchor with a subagent at read time.

## What was rejected

Named here so a reader who later finds these in the exploration output knows they were considered and
deliberately dropped:

- **The playbooks' DB-canonical / ULID keystone** (exploration playbook 02) — **rejected.** Files stay
  canonical; the DB does not become the source of truth and elements get no stored IDs.
- **Deterministic anchoring** (heading-path or ordinal anchors) — **rejected.** No anchor is stored or
  computed for re-location; the runtime subagent does that work from `quoted_text` + `section_hint`.

## The fallback

If runtime re-anchoring proves flaky in practice, the escape hatch is to reintroduce a *lightweight*
anchor. That is a **deliberate, separately-decided future change — NOT something to pre-build now.**
Phase 1 ships zero anchoring machinery; do not hedge by adding a "just in case" anchor column.

## FK lifecycle note

All three sidecar tables use `FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE`
(`comment_events` cascades via `requirement_comments`). Sidecar rows are meaningless without their
goal, so they are deleted with it. This is a **deliberate deviation** from `agent_runs`' `SET NULL`
pattern and is documented in the `schema.sql` comment alongside the DDL.

## Spec-convention compliance note

Per `cast-init-conventions.collab.md`: the `_v2` filename-versioning rule does **not** apply to
requirement *versions*. Those live in the DB sidecar (`requirement_versions`), not as parallel files;
FR-011 keeps only the current `.collab.md` in the goal folder. This design note's own filename
satisfies the convention — date prefix `2026-06-11` (FR-003) and `.collab.md` authorship suffix
(FR-001, recording owner decisions). Phase 1 introduces no user-facing behavior, so it ships **no
spec** — specs come with Phases 3a/3b/4/5.

## Links

- Phase 1 plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1-foundation.md` (and its plan-review
  `## Decisions` block — the five resolved issues are folded into the plan and the sub-phases).
- Cross-phase interface ledger: `docs/plan/refine-requirements-v2-decisions-so-far.md`.
- The "Decisions Resolved at Plan Review" block (decisions **#1** and **#9**) in the goal's
  `plan.collab.md` is the source of the delete-the-anchoring-engine / re-anchor-with-a-subagent calls
  cited above.
