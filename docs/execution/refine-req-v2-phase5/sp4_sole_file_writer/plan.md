# Sub-phase 4: The Sole File Writer — `cast-requirements-writeback` agent (surgical apply)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Build the **one and only** code path that mutates the canonical `.collab.md`. A single subagent
applies an accepted / auto-applied `change_request` as a **targeted addition/annotation that leaves
the rest of the file byte-identical**, appends provenance, bumps the version via `create_next()`, and
emits the change summary with a provenance badge. **The server never writes the file** — this agent
is the only mutator. The silent-drift bug US7 exists to kill becomes structurally impossible (no
whole-file overwrite path).

## Dependencies

- **Requires completed:** sp2 (an `accepted`/`applied` change to act on), sp3a (conflict verdict
  gates the apply), sp3b (notification on apply — the outbox row written in the apply txn).
- **Critical path. Heaviest sub-phase (~1.5 sessions).**
- **Consumes (landed):** `cast-comment-reanchor` (quote→region at apply time);
  `requirement_version_service.create_next`; `block_diff.diff_blocks`/`summarize`;
  `orchestration_service.update_manifest_status` (the surgical-edit template).

## Scope

**In scope:**
- A new `agents/cast-requirements-writeback/` subagent (sole file-writer).
- Apply logic: reanchor → `detect_conflict` → surgical apply (additions/clean only) → provenance →
  `create_next()` version bump → change summary with provenance badge → outbox row in the apply txn.
- Path-scoping the writer to the goal's `refined_requirements.collab.md`.

**Out of scope (do NOT do these):**
- **Never** a whole-file overwrite. Never build on `api_artifacts.save_artifact`'s `write_text`
  whole-file path (that is the code-G4 silent-drift bug US7 kills).
- The server (sp2 intake, any route) must **not** write the file — only this agent does.
- Do **not** auto-merge a `conflicted` change — refuse it, surface it, leave the file untouched.
- Do **not** edit any file outside the goal dir.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-writeback/cast-requirements-writeback.md` | Create | Does not exist |
| `agents/cast-requirements-writeback/config.yaml` | Create | Does not exist |
| `cast-server/cast_server/services/change_request_service.py` | Modify | sp2 created it; add the apply-path helpers (event transitions, outbox row, version bump glue) |
| `cast-server/tests/test_writeback_apply.py` | Create | Does not exist |
| (skills regen) `bin/generate-skills` | Run | After authoring the agent |

## Detailed Steps

### Step 4.1: Author the subagent

`agents/cast-requirements-writeback/` cloned from the Phase 2/3a/4 subagent precedent
(`agents/cast-comment-reanchor/`, `agents/cast-requirements-checker/`):
`model: sonnet, dispatch_mode: subagent, interactive: false, context_mode: lightweight`. It mirrors
`cast-update-spec`'s **"sole write path"** posture. The agent receives an accepted/auto-applied
`change_request` (id + fields) and:
1. Resolves `target_quote` → region via **`cast-comment-reanchor`** (the only locator). Orphan →
   refuse + surface, never apply.
2. Runs `detect_conflict` (sp3a). `conflicted` → refuse, surface, file untouched. `clean` / pure
   addition → proceed.
3. Applies **surgically** (Step 4.2).
4. Appends provenance; bumps the version via `create_next()`; emits the change summary
   (Step 4.3); writes the outbox row in the apply txn (sp3b's relay delivers it).

> Run `bin/generate-skills` after authoring (decisions-so-far lockstep rule).

### Step 4.2: Surgical apply — lift `update_manifest_status()` as the template

`orchestration_service.update_manifest_status()` already rewrites **one keyed region** of a markdown
doc and leaves the rest untouched — **lift it as the exact surgical-edit-by-key template.** For an
addition, append the new element at the file tail (or under the named section_hint); for a
clean modification, replace exactly the located region. **Every other byte stays identical.**

- **Never** `api_artifacts.save_artifact` / `write_text` whole-file overwrite.
- Read the current file, locate the region (reanchor verdict), splice, write only via the surgical
  template. Verify byte-identity of all non-target regions before committing the write.

### Step 4.3: Provenance + version bump + change summary

- **Provenance:** append the `origin_*` + `author`/`author_type` to the change record / version
  metadata.
- **Version bump:** call `requirement_version_service.create_next(goal_slug, new_content,
  created_by=<agent>)` → returns `{version, convergence, open_comments, displaced_comment_ids}`. This
  is the version gate (it also reports displacement for any comments the edit moved — hand those to
  `cast-comment-reanchor` exactly as Phase 4 does).
- **Change summary:** reuse `block_diff.diff_blocks(old_parsed, new_parsed)` + `summarize(diff)`
  (landed) and add **one provenance-badge column** — e.g.
  `+FR-021 — added by planning · agent cast-high-level-planner · derived from plan.collab.md`.
- **Event trail:** write the `applied` `change_request_events` row + the `notifications_outbox` row
  in the **same apply txn** (BEGIN IMMEDIATE), so a crash leaves nothing half-applied.

### Step 4.4: Path-scoping (security)

The writer must be path-scoped to the goal's `refined_requirements.collab.md`. Refuse any target
outside the goal dir (out-of-tree edit **refused, never crash**). Mirror the subphase-runner's
path-traversal posture (resolve the path, assert it is within the goal dir).

## Verification

### Automated Tests (permanent)
`cast-server/tests/test_writeback_apply.py`:
- **Accepted addition** → the new FR appears at the file tail; **every other byte identical** (diff
  shows exactly the added region). Provenance row + `applied` event + version bump + change-summary
  delta with the provenance badge all present + outbox row queued.
- **`conflicted` change** → **refused**, surfaced, file **untouched** (byte-identical to before).
- **Orphaned target** (quote no longer locates) → refused + surfaced, file untouched.
- **Path-scope:** a change targeting a path outside the goal dir → refused (no crash, no write).
- The writer is the **only** path that mutates the `.collab.md`: assert `rerender`/render code still
  never mutates it (cross-check with the FR-007 guard, extended fully in sp5).

### Validation Scripts (temporary)
- Apply a fixture addition via the agent against a temp goal dir; `git diff --stat` (or a byte-diff)
  on the `.collab.md` shows exactly one added region.

### Manual Checks
- `grep -rn "write_text\|save_artifact" agents/cast-requirements-writeback/ cast-server/cast_server/services/change_request_service.py` → **no** whole-file overwrite path.
- `ls agents/cast-requirements-writeback/` → `.md` + `config.yaml` present; `bin/generate-skills` ran.

### Success Criteria
- [ ] Addition applies surgically; all non-target bytes identical.
- [ ] `conflicted` / `orphaned` → refused + surfaced, file untouched.
- [ ] Provenance appended; version bumped via `create_next()`; change summary carries the provenance badge.
- [ ] `applied` event + outbox row written in one apply txn.
- [ ] Writer is path-scoped to the goal's `.collab.md`; out-of-tree target refused, never crashes.
- [ ] No whole-file overwrite anywhere; server writes no file.
- [ ] `bin/generate-skills` re-run.

## Execution Notes
- **Delegation-contract carve-out:** `cast-delegation-contract.collab.md` says the server never
  writes artifact files. This agent is the **carve-out** — the server owns the proposal DB, the agent
  owns the file apply. No conflict, but sp5 must **restate** this in the new roundtrip spec.
- One writer = one place for provenance + conflict gate + version bump. Do not let sp2's intake or any
  route write the file — if you find yourself adding a `write_text` to a route, stop.
- **Spec-linked files:** you modify `change_request_service.py` and author an agent; the sole-writer
  carve-out is documented in sp5's new spec. Read `cast-delegation-contract.collab.md` and
  `cast-requirements-render.collab.md` before touching the apply path so the change-summary +
  conflict-surface semantics stay aligned with the render contract.
