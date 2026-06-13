# Sub-phase 1: Design Note — Files-Canonical + Thin Spine Contract

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1/_shared_context.md` before starting.

## Objective

Write the design note that codifies the resolved architecture for all of Phase 1 (and the marker every
later phase reads before touching this subsystem): **files stay byte-canonical; the DB is a thin spine of
version snapshots + comment rows + a conflict hash; there are NO per-element IDs and NO deterministic
anchoring engine.** This note is "the contract the rest of this phase implements" (plan Activity A — write
first). It is also the canonical "do NOT re-inherit the playbooks' ULID/anchor keystone" record, so a
future phase that drifts back toward stored anchors has a single authoritative document to be corrected
against.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** Clean checkout. `docs/design/` does not exist yet — this sub-phase creates it.

## Scope

**In scope:**
- Create the `docs/design/` directory.
- Write `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md`.
- Record: files-canonical + thin DB spine; the three deterministic-machinery sites kept (comment rows
  exist / version snapshots / conflict = content-hash compare); no per-element IDs; no anchoring engine;
  comments store `quoted_text` + `section_hint`, re-located by a Claude subagent at runtime (Phase 4).
- Record what was explicitly **rejected**: the playbooks' DB-canonical/ULID keystone AND
  heading-path/ordinal anchors.
- Record the **fallback**: if runtime re-anchoring proves flaky, reintroduce a lightweight anchor (a
  deliberate future decision, not a Phase 1 hedge).
- Link to `plan.collab.md`'s "Decisions Resolved at Plan Review" (decisions #1 and #9 specifically).

**Out of scope (do NOT do these):**
- Any code, schema, or test. This sub-phase is documentation only.
- A `/cast-update-spec` call or a `docs/specs/` entry — Phase 1 ships no user-facing behavior, so no spec
  this phase (Phases 3a/3b/4/5 own the specs).
- Re-deciding any architecture. The decisions are settled; this note *records* them.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/design/` | Create directory | Does not exist |
| `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` | Create | Does not exist |

## Detailed Steps

### Step 1.1: Create the directory and the dated, authored filename

- `mkdir -p docs/design`
- Filename **exactly**: `2026-06-11-requirements-files-canonical-thin-spine.collab.md`.
  - Date prefix `2026-06-11` satisfies `cast-init-conventions.collab.md` FR-003 (date prefix under
    `docs/design/`). Keep this date even though the run executes later — it is the plan's canonical name
    (the Canonical Decisions table pins this exact path).
  - `.collab.md` suffix satisfies FR-001 (authorship suffix; this records owner decisions).

### Step 1.2: Write the design note body

Structure it so a future implementer can find "what was decided and what was killed" in under a minute:

1. **Title + one-line summary** — files-canonical + thin DB spine; no per-element IDs; no anchoring engine.
2. **The decision.** Files (`refined_requirements.collab.md`) are the single byte-canonical source of
   truth (FR-007 — never mutated). The DB holds only the thin spine.
3. **The three deterministic-machinery sites we keep** (the only places where being wrong = silent data
   loss): (a) comment rows exist (a comment must never be lost), (b) version snapshots are recorded,
   (c) conflict detection = content-hash compare. Tie each to its table/function:
   `requirement_comments`, `requirement_versions`, `requirements_render.hashing.content_hash`.
4. **What we deleted, and why.** No `block_anchor` column, no element surrogate, no per-element ULID, no
   heading-path/ordinal anchor. Comments instead store `quoted_text` + `section_hint` and are re-located
   at runtime by a Claude subagent (trust-and-iterate). Cite plan-review decisions #1 and #9.
5. **What was rejected.** The exploration playbooks' DB-canonical/ULID keystone (playbook 02) AND
   deterministic anchoring (heading-path/ordinal). Name them so a reader who finds the playbooks knows
   they were considered and dropped.
6. **The fallback.** If runtime re-anchoring proves flaky in practice, the escape hatch is to reintroduce
   a *lightweight* anchor — a deliberate, separately-decided future change, NOT something to pre-build now.
7. **FK lifecycle note.** Sidecar rows use `ON DELETE CASCADE` (meaningless without their goal) — a
   deliberate deviation from `agent_runs`' `SET NULL`.
8. **Spec-convention compliance note.** Per `cast-init-conventions.collab.md`: the `_v2` filename
   versioning rule does NOT apply to requirement *versions* — those live in the DB sidecar; FR-011 keeps
   only the current file in the goal folder.
9. **Link** to `docs/plan/2026-06-11-refine-requirements-v2-phase1-foundation.md` and its plan-review
   "Decisions" block.

Keep it tight (roughly 1–2 pages). It is a decision record, not a tutorial — no code listings beyond
naming the canonical identifiers.

## Verification

### Automated Tests (permanent)
- None. This sub-phase ships no code; there is nothing to unit-test.

### Validation Scripts (temporary)
- `test -f docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md && echo OK`
- `bin/cast-spec-checker docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` — run
  it; a design `.collab.md` is not a spec-kit spec, so a clean exit is not required, but eyeball that it
  does not error catastrophically. (Informational only — do not gate on it.)

### Manual Checks
- Filename matches the canonical path in `_shared_context.md` exactly (date prefix + `.collab.md`).
- The note explicitly contains the strings: "no per-element ID", "no anchoring engine", "rejected"
  (re: ULID/DB-canonical keystone), and the three table/function names.

### Success Criteria
- [ ] `docs/design/` exists.
- [ ] `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` exists with the canonical name.
- [ ] The note records: files-canonical, thin-spine three sites, deleted machinery, rejected keystone, fallback.
- [ ] The note names `requirement_versions`, `requirement_comments`, `comment_events`, and
      `requirements_render.hashing.content_hash` as the canonical identifiers.
- [ ] The note links back to the Phase 1 plan and its plan-review decisions.

## Execution Notes

- This is genuinely "write first." Although no code *imports* this note, the plan orders it first because
  it is the reference sp2a/sp2b/sp3/sp4 (and Phases 4/5) read to avoid re-adding deleted machinery. Don't
  skip it as "just docs."
- Do NOT invent new architecture in the note. If you find yourself making a decision, stop — it was
  already made at plan review; quote it, don't re-derive it.
- **Spec-linked files:** none. This sub-phase modifies no spec-linked production file.
