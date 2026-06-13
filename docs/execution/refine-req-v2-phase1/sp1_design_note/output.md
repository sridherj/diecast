# sp1_design_note — Output

**Status:** completed

## What was done

Wrote the Phase 1 design note that codifies the resolved **files-canonical + thin DB spine**
architecture and serves as the canonical "do NOT re-inherit the playbooks' ULID/anchor keystone"
record for all later phases.

- Created `docs/design/` (did not exist before this sub-phase).
- Created `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` (exact canonical
  filename from `_shared_context.md`).

## What the note records (for dependent sub-phases)

The note is documentation-only — it ships no code, schema, or test — but it pins the contract sp2a /
sp2b / sp3 / sp4 (and Phases 4/5) implement:

1. **Files canonical:** `refined_requirements.collab.md` is the byte-canonical source of truth, never
   mutated (FR-007). DB holds only the thin spine.
2. **Three deterministic-machinery sites kept** (only places where wrong = silent data loss), each tied
   to its identifier: comment rows exist → `requirement_comments`; version snapshots recorded →
   `requirement_versions`; conflict = content-hash compare → `requirements_render.hashing.content_hash`.
   Append-only history → `comment_events`.
3. **Deleted machinery:** no per-element ID, no anchoring engine (no `block_anchor`, no heading-path /
   ordinal anchor); `Block.ref` is in-memory only (Decision #2). Comments store `quoted_text` +
   `section_hint`, re-located by a runtime Claude subagent (decisions #1 and #9).
4. **Rejected:** the exploration playbook 02 DB-canonical/ULID keystone AND deterministic anchoring.
5. **Fallback:** reintroduce a lightweight anchor only if runtime re-anchoring proves flaky — a
   deliberate future decision, not a Phase 1 hedge.
6. **FK lifecycle:** sidecar tables use `ON DELETE CASCADE` (deliberate deviation from `agent_runs`'
   `SET NULL`).
7. **Spec-convention note:** `_v2` filename rule does not apply to requirement versions (DB sidecar);
   FR-011 keeps only the current file in the goal folder. No spec ships this phase.
8. **Links:** Phase 1 plan + its plan-review `## Decisions`; the decisions-so-far ledger.

## Verification (all success criteria met)

- `docs/design/` exists ✔
- Canonical-named file exists ✔
- Required strings present: `no per-element ID`, `no anchoring engine`, `rejected`,
  `requirement_versions`, `requirement_comments`, `comment_events`,
  `requirements_render.hashing.content_hash` ✔
- Links back to the Phase 1 plan + plan-review decisions #1/#9 ✔
- `bin/cast-spec-checker` run (informational only, not gated): reports the expected "missing required
  section" lint because a design `.collab.md` is not a spec-kit spec — it did not error catastrophically.

## Notes for dependents

- sp2a/sp2b/sp3 can proceed: the note confirms the canonical identifiers (`requirement_versions`,
  `requirement_comments`, `comment_events`, `requirements_render.hashing.content_hash`) and the
  "no anchor column / no element surrogate" constraint they must honor.
