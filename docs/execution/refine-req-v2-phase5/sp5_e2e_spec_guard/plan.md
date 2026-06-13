# Sub-phase 5: End-to-End Proof (SC-006) + Spec Lockstep + FR-007 Guard

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Prove Phase 5 end-to-end and lock it into canon. A **simulated** downstream change traces the
**entire** chain green, the binary SC-006 gate passes, the round-trip behavior is documented in a new
canonical spec, and the FR-007 byte-identity guard is extended to prove the writer is the only
mutator. Phase 5 is done and provable **without** real downstream emitters.

## Dependencies

- **Requires completed:** sp4 (the full apply path: intake → conflict → surgical apply → version
  bump → change summary → outbox → notification).
- **Consumes (landed):** `tests/fixtures/synthetic_child.py` (emits the simulated downstream
  write-back); `bin/cast-spec-checker`; the existing FR-007 guard suite.

## Scope

**In scope:**
- `test_roundtrip_e2e.py` (SC-006) tracing the whole chain, asserting the **negatives**.
- The new canonical spec `cast-requirements-roundtrip.collab.md` (via `/cast-update-spec` create mode) + registry entry.
- Extending the FR-007 read-only guard with a post-writeback byte-identity test.
- A final name-reconciliation pass across sp3a/sp3b/sp4.

**Out of scope (do NOT do these):**
- No real planner/executor emitters (deferred to a later goal). The proof uses `synthetic_child.py`.
- Do **not** duplicate `cast-requirements-render.collab.md` or `cast-delegation-contract.collab.md`
  in the new spec — **reference** them by heading.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/test_roundtrip_e2e.py` | Create | Does not exist (mark `eval_*` / slow if it drives a live subagent) |
| `docs/specs/cast-requirements-roundtrip.collab.md` | Create | Does not exist |
| `docs/specs/_registry.md` | Modify | Append the new spec row |
| `cast-server/tests/test_fr007_readonly_guard.py` | Modify | Extend with the post-writeback byte-identity test |
| `cast-server/tests/fixtures/synthetic_child.py` | Use/extend | Emits the `requirements_writeback` artifact for SC-006 |

## Detailed Steps

### Step 5.1: SC-006 end-to-end test

`test_roundtrip_e2e.py`: `synthetic_child.py` emits a valid `requirements_writeback` →
`change_request` row → conflict verdict → surgical file apply → version bump → change summary with
provenance badge → outbox row → notification surfaced. Assert:
- **0** modifications to existing content applied without a passed gate or surfaced conflict
  (the negative — not just the happy path).
- **0** lost / duplicate notifications after an injected crash between commit and relay.
- The full happy-path chain is green for a pure addition.

If it drives a live subagent (`cast-requirements-writeback` / `cast-comment-reanchor`), mark it
slow / `eval_*` so the default suite excludes it (mirror Phase 4's e2e exclusion convention).

### Step 5.2: New canonical spec (create mode)

→ **Delegate:** `/cast-update-spec` (create mode) for
**`docs/specs/cast-requirements-roundtrip.collab.md`** covering: the change-request lifecycle
(`proposed→applied|conflicted|rejected|superseded`), the same-door API
(`POST /api/goals/{slug}/change-requests`, owner decision #1), the graduated-trust policy
(`WRITEBACK_GATE_POLICY`, owner decision #3), conflict semantics (`detect_conflict`:
`clean|conflicted|orphaned`, `base_version` = integer version per owner decision #2), the
sole-writer carve-out (`cast-requirements-writeback`, referencing — not duplicating —
`cast-delegation-contract.collab.md`), and the notification surface (the **extended**
`{convergence, open_comment_count}` + round-trip descriptor, referencing
`cast-requirements-render.collab.md`). Register it in `docs/specs/_registry.md`.

> Headless note (Phase 3a sp5b precedent): if `/cast-update-spec`'s interactive approval gate can't
> run headless, author the spec in create-mode shape directly and record `auto-persisted:
> non-interactive run`. Then `bin/cast-spec-checker docs/specs/cast-requirements-roundtrip.collab.md`
> must exit 0.

→ Review `/cast-update-spec` output for: references (not duplications) of the render + delegation
specs; the four owner decisions stated verbatim; lint clean.

### Step 5.3: Extend the FR-007 guard

Extend `cast-server/tests/test_fr007_readonly_guard.py` with a post-write-back byte-identity test:
the writer changes **exactly** the target region; **no other path** (render, `rerender`, save) mutates
the `.collab.md`. This is the structural proof that US7's silent-drift bug cannot recur.

→ **Delegate:** `/cast-pytest-best-practices` over the e2e + guard suites. Review for the
crash-injection assertion quality (0 lost / 0 dup) and the negative-assertion (no ungated
modification) coverage.

### Step 5.4: Final reconciliation pass

If Phase 4 (or any sibling) landed with drifted names for `block_diff` / `create_next` /
`cast-comment-reanchor` / the `{convergence, open_comment_count}` surface, adopt the **landed** names
across sp3a/sp3b/sp4 (standing rule). As of authoring (2026-06-12) all four are confirmed landed with
the names in `_shared_context.md` — verify once more before closing.

## Verification

### Automated Tests (permanent)
- `uv run pytest cast-server/tests/test_roundtrip_e2e.py` (or its `eval_*` invocation) — green;
  asserts the SC-006 negatives (0 ungated modifications, 0 lost/dup notifications).
- `uv run pytest cast-server/tests/test_fr007_readonly_guard.py` — green, including the
  post-writeback byte-identity test.

### Validation Scripts (temporary)
- `bin/cast-spec-checker docs/specs/cast-requirements-roundtrip.collab.md` → exit 0.
- `grep -n "cast-requirements-roundtrip" docs/specs/_registry.md` → registry row present.

### Manual Checks
- Read the new spec: confirm it **references** (does not paste) the render + delegation specs.
- Confirm the four owner decisions appear verbatim in the spec.

### Success Criteria
- [ ] SC-006 e2e passes: full chain green for an addition; **0** ungated modifications; **0** lost/dup notifications after an injected crash.
- [ ] `cast-requirements-roundtrip.collab.md` created, lints clean (`cast-spec-checker` exit 0), registered in `_registry.md`.
- [ ] New spec references render + delegation specs by heading; no duplication.
- [ ] FR-007 guard extended: writer is the only mutator; byte-identity proven.
- [ ] Name reconciliation pass complete; landed names adopted everywhere.

## Execution Notes
- **SC-006 must assert the negative** — no existing content mutated without a passed gate / surfaced
  conflict — not just the happy path. The negative is the whole point of Phase 5.
- **Spec lockstep:** the new spec is the contract Phase-5-and-later goals cite. It must reference
  `cast-requirements-render.collab.md` (the change summary + conflict surface ride that page) and
  `cast-delegation-contract.collab.md` (the sole-writer carve-out) — not duplicate them.
- **Spec-linked files:** you create a spec and extend the FR-007 guard (covered by
  `cast-requirements-render.collab.md`). Read that spec first; the guard extension must preserve its
  read-only render invariant while adding the new "writer is the sole mutator" assertion.
