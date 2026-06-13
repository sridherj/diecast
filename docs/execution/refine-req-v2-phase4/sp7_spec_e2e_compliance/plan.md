# Sub-phase 7: Spec lockstep + e2e harness + compliance (settle the phase)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Settle Phase 4's spec debt and ship the mandatory e2e harness. Extend the Phase 3a render spec with
the full Phase 4 surface (so Phase 5 can cite it), add the render-page comment flows to the e2e
harness (`cast-ui-testing.collab.md` US2 makes this mandatory), and run the final compliance sweep
over the new agent + the `cast-refine-requirements` allow-list. This is **last** — it runs after all
interfaces have settled.

## Dependencies

- **Requires completed:** ALL prior sub-phases (sp1–sp6). The spec must describe the **landed**
  surface, and the e2e harness must target the real selectors/routes.
- **Assumed codebase state:** the comment API, versions/changes endpoints, diff route, JS layer, and
  `cast-comment-reanchor` agent all exist and pass their unit/golden tests.

## Scope

**In scope:**
- Extend (or create, if 3a hasn't landed it) `docs/specs/cast-requirements-render.collab.md` with
  the Phase 4 contract — via `/cast-update-spec`.
- e2e harness update under `cast-server/tests/ui/` per `cast-ui-testing.collab.md` US2.
- `/cast-agent-compliance` over `cast-comment-reanchor` + the `allowed_delegations` addition to
  `cast-refine-requirements` (the allow-list audit footgun).
- The manual SC-002 dry run (leave a comment on this goal's own render, produce a version, watch it
  carry forward) — record the result.

**Out of scope (do NOT do these):**
- Any production behavior change. If the spec/e2e work surfaces a real bug, record it as a finding
  and route it back to the owning sub-phase — do not patch production from sp7.
- Re-litigating locked decisions (#1/#7/#8/#9) — the spec records them, doesn't reopen them.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-requirements-render.collab.md` | Modify (update mode) via `/cast-update-spec` | Phase 3a spec landed |
| `docs/specs/_registry.md` | Modify (bump row) | Registry exists |
| `cast-server/tests/ui/` (e2e harness) | Modify/Create | Phase 3a US1 coverage exists |

## Detailed Steps

### Step 7.1: Spec extension
→ **Delegate: `/cast-update-spec`** (update mode) on `docs/specs/cast-requirements-render.collab.md`.
If 3a's spec hasn't landed, use create mode covering both phases' surface. Extend with:
- The comment API contract (endpoints, the HX negotiation rule, `author_kind` semantics, the
  409/422 state-machine errors, the relocate verbatim backstop).
- The versions + changes endpoints; `create_next()` semantics + the convergence rule (`unconverged`
  iff `open_comment_count > 0`).
- The diff-view route (`/goals/{slug}/render/diff`) + the **transient-`id` exception** to the
  zero-`id` thin-spine contract (scoped to the diff view only).
- The tray/displaced **derived-state** model (this session's decision #1 — displacement is never
  stored; the save handler is untouched / "lazy + surfaced tray" reinterpretation).
- The `cast-comment-reanchor` I/O contract + the subagent bare-JSON carve-out.
- The FR-011 folder invariant (only the current requirements file ever in the goal folder).
- The progressive-enhancement note (Phase 4 adds `<script src>`; file:// viewing degrades to a
  readable read-only render).
- Bump the registry row in `docs/specs/_registry.md`.

**Review the delegated output for:** names match this plan's Naming Contract **exactly** (Phase 5
will cite this spec); no locked decision is softened; the carve-out and transient-`id` exception are
recorded as deliberate, not flagged as drift.

### Step 7.2: e2e harness
→ **Delegate** the harness update per `cast-ui-testing.collab.md` US2 — extend
`cast-server/tests/ui/` with the render-page comment flows:
- select → pill → composer → comment appears with `<mark>`;
- resolve from the thread;
- toggle → diff view renders;
- tray shows a displaced comment after an editor save that rewords its quote.

**Review the delegated output for:** selectors target the classes this plan names
(`.comment-pill`, `.comment-mark`, `.comment-tray`, `.comment-composer`); flows match the locked UX
(decision #7) and the diff toggle (decision #8).

> **No-browser note (project default):** if the run can't drive Chrome, record a static verdict +
> human-eyeball carry-forward for the live-render flows; never block the sub-phase. The harness code
> still lands (it runs in CI where a browser is available).

### Step 7.3: Compliance sweep
→ **Delegate: `/cast-agent-compliance`** for:
- `cast-comment-reanchor` (re-confirm config canon if sp4b's run predates final naming).
- The `allowed_delegations` addition to `cast-refine-requirements` (the allow-list audit footgun —
  confirm `cast-comment-reanchor` is listed and the entry is well-formed).

**Review the delegated output for:** no real config drift; the allow-list change is recognized as
intentional.

### Step 7.4: Manual SC-002 dry run
On THIS goal's own render, leave a comment, `POST /versions`, and confirm the comment carries
forward (still open, listed after the bump; displaced→tray if its quote moved). Record the outcome
in the manifest Progress Log.

## Verification

### Automated Tests (permanent)
- e2e harness suite (`cast-server/tests/ui/`) — the four render-page flows above pass in a
  browser-capable CI.
- Spec checker / registry consistency (whatever `bin/cast-spec-checker` or the spec-lint step asserts
  on the registry) — green.

### Validation Scripts (temporary)
```bash
bin/cast-spec-checker docs/specs/cast-requirements-render.collab.md; echo "exit=$?"
grep -n "cast-requirements-render" docs/specs/_registry.md       # bumped row present
# Run the e2e suite per the harness's own entrypoint (see cast-ui-testing.collab.md).
```

### Manual Checks
- The spec's endpoint list and the `cast-comment-reanchor` schema match `_shared_context.md`'s
  Naming Contract token-for-token.
- The transient-`id` exception and the lazy/derived-displacement model are explicitly recorded.

### Success Criteria
- [ ] `cast-requirements-render.collab.md` extended with the full Phase 4 surface; registry bumped;
      checker exit 0.
- [ ] e2e flows for select→pill→composer→`<mark>`, resolve, toggle→diff, displaced→tray exist and
      target the named selectors.
- [ ] `/cast-agent-compliance` clean for `cast-comment-reanchor` + the allow-list addition.
- [ ] SC-002 manual dry run recorded (comment carries forward through a version bump).
- [ ] No production behavior changed in this sub-phase (findings routed back, not patched here).

## Execution Notes

- This is the spec-debt settlement: the only new spec *file* decision is reuse-vs-create depending
  on 3a's landing order (no fork either way — extend if it exists).
- Phase 5 reads this spec to import `block_diff` + cite the same-door API — getting the names exact
  here is what keeps Phase 5 from reimplementing the engine.
- The unified `needs_attention` notification badge is **Phase 5's** build (high-level decision #4) —
  Phase 4 surfaces in-page only (tray + Goal Card chip). Do not add a notification surface here.

**Spec-linked files:** this sub-phase IS the spec update. Use `/cast-update-spec` (it shows a diff
and is the single write path); do not hand-edit the spec outside that flow.
