# Sub-phase 6: UI Test Agent Prompt Update + `Delegate: /cast-pytest-best-practices`

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp5 is committed (cleanup complete; only the new threaded path exists).

## Objective

Lock the new threaded `/runs` behavior under the diecast UI harness. Update the `cast-ui-test-runs` agent prompt with threaded-layout assertions, extend `runner.py` with any new selector / capability primitives, and run the harness end-to-end via `cast-server/tests/ui/test_full_sweep.py`. Then delegate `/cast-pytest-best-practices` over the new pytest files added across sp1–sp3 (`test_runs_tree.py`, the new cases in `test_runs_api.py`, and `test_runs_template.py`) and act on findings.

This sub-phase runs AFTER cleanup so the agent's assertions match the actually-shipped DOM. Running before cleanup would risk asserting transitional state that sp5 will remove.

## Dependencies

- **Requires completed:** sp5 (cleanup). The dev page must reflect the final shipped DOM.
- **Assumed codebase state:** Pre-sp6 tree at HEAD + sp1 + sp2 + sp3 + sp4 + sp5 commits. The `cast-ui-test-runs` agent prompt currently asserts the OLD flat-runs layout.

## Scope

**In scope:**
- UPDATE `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` — replace flat-runs assertions with threaded-layout assertions per the plan's "UI tests — agent-driven" section.
- EXTEND `cast-server/tests/ui/runner.py` IF the agent's new assertions require new primitives (clipboard grant via `context.grant_permissions(['clipboard-read', 'clipboard-write'])`, viewport resize helper, localStorage inspection helper, `htmx:afterSwap` wait helper). Add only the primitives the agent's prompt actually references.
- RUN `cast-server/tests/ui/test_full_sweep.py` end-to-end. The runs-screen agent must report green.
- INVOKE `Delegate: /cast-pytest-best-practices` over `test_runs_tree.py`, the 2 new cases in `test_runs_api.py`, and `test_runs_template.py`. Act on findings (typically: rename for clarity, parametrize repetitive cases, ensure fixtures are scoped right). Re-run the suite after applying findings.

**Out of scope (do NOT do these):**
- Any service / route / template / CSS / JS change — sp1–sp5 own those.
- Spec capture — sp7 owns that, after this sub-phase ships.
- Editing other UI test agents (e.g., `cast-ui-test-goals`) — only the runs agent.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` | Modify | Asserts old flat-runs layout. |
| `cast-server/tests/ui/runner.py` | Modify (additive) | Lacks clipboard-grant / viewport helpers if the agent prompt needs them. |
| (No code edits if `/cast-pytest-best-practices` returns "no findings") | — | — |

## Detailed Steps

### Step 6.1: Inventory the existing agent prompt

```bash
cat cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md
```

Read the file end-to-end. Identify:
- The "What to assert" section (or equivalent).
- The "Selectors used" section.
- Any helper functions referenced via `runner.py`.

Replace the flat-runs assertions with the threaded-layout list below. Keep the header / orchestration plumbing intact (the agent's contract with `cast-ui-test-orchestrator` must not change shape).

### Step 6.2: Replace assertions with the threaded-layout list

The new assertions, taken verbatim from the plan's "UI tests — agent-driven" section:

1. `.run-group`, `.run-node`, `.thread`, `.ctx-pill` markup is present.
2. Two-line layout: status dot + agent name in `.row-1`; status pill + ctx pill paired at start of `.row-2`.
3. Eager tree: a known multi-level seed renders L2/L3 children on initial page load (no HTMX wait).
4. Pagination preserves tree shape on page 2 (click "Next"; assert children still attached).
5. Click on a row toggles `.expanded`; the `.detail` panel becomes visible.
6. Reload → expand state survives (verify by checking `localStorage["runs:expanded:<id>"]` AND that the `.expanded` class re-applies).
7. `.copy-resume` click writes clipboard; row does NOT expand. Use `context.grant_permissions(['clipboard-read', 'clipboard-write'])` (Playwright API).
8. `ctx_class=low/mid/high` → `.ctx-pill` background tint matches; `.run-node.is-child.ctx-high .agent-name` is the danger color.
9. Failed-descendant seed → `.run-group.has-failure` (red border).
10. Rework-only seed (no failure) → `.run-group.has-warning` (amber border). (Symmetric with #9; closes the asymmetric-coverage gap.)
11. Rework second instance has `.rework-tag`; L1 shows `⚠ N reworked` rollup with propagated count from a deep rework (i.e., a rework at L3 is reflected in L1's pill).
12. Status filter `?status=failed` returns L1s with any failed descendant (rollup-aware — the L1's own status may be `completed`).
13. HTMX poll preserves expand state: expand a parent of a running run → wait 4s → expand state intact; cells refreshed.
14. Mobile viewport (480×800) hides `.relative-time` and `.task` crumbs.

For each, the agent prompt should specify:
- The **selector** to query.
- The **expected** state.
- The **seed prerequisite** (which seeded run / fixture provides the test data).

### Step 6.3: Extend `runner.py` with required primitives

Read `cast-server/tests/ui/runner.py`. For each new assertion above, decide whether the agent prompt references a `runner.py` helper that doesn't yet exist. Likely additions:

- `grant_clipboard(context)` — wraps `context.grant_permissions(['clipboard-read', 'clipboard-write'])`. Agent calls before assertion #7.
- `resize_viewport(page, width: int, height: int)` — wraps `page.set_viewport_size({"width": width, "height": height})`. Used by assertion #14.
- `read_clipboard(page)` — `await page.evaluate("navigator.clipboard.readText()")`. Used by assertion #7.
- `read_localstorage(page, key: str)` — `await page.evaluate(f"localStorage.getItem('{key}')")`. Used by assertion #6.
- `wait_for_htmx_settle(page, timeout: int = 4000)` — waits for `htmx:afterSwap` or for the network to idle. Used by assertion #13.

Each new helper:
- Has a one-line docstring: who calls it, what it returns.
- Is small, well-named, single-purpose.
- Is usable from any UI test agent — the agent prompt just calls `runner.read_clipboard(page)`.

If a primitive already exists, do NOT duplicate. Reuse.

### Step 6.4: Run the UI harness end-to-end

```bash
uv run pytest cast-server/tests/ui/test_full_sweep.py -v
```

The orchestrator dispatches `cast-ui-test-runs` (and the other screen agents). The runs agent drives Playwright through every assertion in step 6.2, writing a structured `output.json`. `test_full_sweep.py` aggregates and asserts.

Expected outcome: green.

If the agent reports a failure:
- Inspect the per-agent `output.json` artifacts under `cast-server/tests/ui/runs/`.
- Determine whether the failure is in the agent prompt (assertion expects wrong selector / state), in `runner.py` (helper has a bug), or in the actual app (an sp1–sp5 regression).
- Fix at the right layer. Do NOT relax the assertion to make it pass — every assertion in step 6.2 is locked by the plan's review.

### Step 6.5: Delegate `/cast-pytest-best-practices`

After the UI suite is green, run:

```
Delegate: /cast-pytest-best-practices
```

Scope the delegation to the three pytest files added by this plan:

- `cast-server/tests/test_runs_tree.py` (new in sp1).
- `cast-server/tests/test_runs_api.py` — only the 2 new cases (`test_list_runs_returns_l1_with_descendants`, `test_list_runs_pagination_by_l1_only`).
- `cast-server/tests/test_runs_template.py` (new in sp3).

The skill audits these files against the diecast pytest best-practices canon (fixture scoping, parametrization, naming, assertion clarity). It returns a list of findings.

For each finding:
- If it's a clear improvement (rename, parametrize, scope tightening), apply it.
- If it's contentious (e.g., the skill suggests deleting a redundant test that the plan explicitly required), surface to user and ask before changing.
- After applying findings, re-run `uv run pytest cast-server/tests/test_runs_tree.py cast-server/tests/test_runs_template.py` to confirm green.

### Step 6.6: Final regression check

```bash
# Full test suite — UI + unit:
uv run pytest cast-server/tests/

# UI sweep specifically:
uv run pytest cast-server/tests/ui/test_full_sweep.py
```

Both must be green before this sub-phase is complete.

## Verification

### Automated Tests (permanent)
- `cast-server/tests/ui/test_full_sweep.py` — green.
- `cast-server/tests/test_runs_tree.py` — green after `/cast-pytest-best-practices` findings applied.
- `cast-server/tests/test_runs_template.py` — green after findings applied.
- `cast-server/tests/test_runs_api.py` — green (the 2 new cases plus all pre-existing).
- Full suite — no regressions.

### Validation Scripts (temporary)

```bash
# 1. Agent prompt mentions the new assertion list:
grep -n 'has-warning\|copy-resume\|ctx-pill\|rework-tag' \
  cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md
# Expect: multiple hits.

# 2. New runner primitives exist:
grep -n 'grant_clipboard\|read_clipboard\|read_localstorage\|resize_viewport\|wait_for_htmx_settle' \
  cast-server/tests/ui/runner.py
# Expect: hits for each primitive the agent uses.

# 3. The agent's output.json artifact records all 14 assertions as passed:
ls cast-server/tests/ui/runs/cast-ui-test-runs/.cast/.agent-run_*.output.json | tail -1 | xargs cat | jq '.summary'
```

### Manual Checks
- Re-read the updated `cast-ui-test-runs.md` end-to-end. Each of the 14 assertions has a clear selector + expected state + seed prerequisite.
- The `/cast-pytest-best-practices` findings list (printed by the delegated skill) is captured in the sp6 commit message or PR description so reviewers can see what was applied.

### Success Criteria
- [ ] `cast-ui-test-runs.md` covers all 14 threaded-layout assertions.
- [ ] `runner.py` exposes the primitives the agent prompt references.
- [ ] `cast-server/tests/ui/test_full_sweep.py` green.
- [ ] `/cast-pytest-best-practices` findings reviewed and applied; pytest still green.
- [ ] Full test suite green.

## Execution Notes

- The diecast UI harness is screen-based — DO NOT introduce parallel pytest-style UI tests. The locked decision in the plan: agent-driven via `cast-ui-test-orchestrator`, not pytest-Playwright.
- When extending `runner.py`, prefer additive primitives over modifying existing helpers. Other screen agents share the file; signature changes are breaking.
- `Delegate: /cast-pytest-best-practices` is a skill invocation, not a sub-agent dispatch. The output is a structured findings list; you apply the changes directly.
- If the skill returns "no findings" for any file, that's still a verifiable outcome — record it in the sub-phase commit message.
- Asymmetric coverage was a review concern: `has-failure` was tested but `has-warning` was not. Assertion #10 closes that gap. Don't drop it.

**Spec-linked files:** `docs/specs/cast-ui-testing.collab.md` lists `cast-server/tests/ui/runner.py` and `cast-server/tests/ui/agents/cast-ui-test-runs/`. Read that spec before extending runner.py and confirm: (a) the new primitives don't conflict with existing SAV behaviors; (b) the agent-prompt update preserves the orchestrator contract (output.json shape unchanged, status reporting unchanged). Surface anything ambiguous to the user.
