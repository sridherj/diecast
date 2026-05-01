# Sub-phase 4: Layer B — Assertion fixes per child (FR-004)

> **Pre-requisite:** Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` before starting.

## Objective

After Layer A is in place (sp1+sp2+sp3), re-run the harness and inspect each remaining
red child. For each `assertions_failed[]` entry that points at a fictional selector or
non-existent endpoint, patch the corresponding `_assert_<screen>` function in
`cast-server/tests/ui/runner.py` to reference what's actually rendered in the
templates and exposed by the routes.

This sub-phase delivers FR-004 and SC-004 of the layered-fixes plan.

## Dependencies
- **Requires completed:** sp1 (orchestrator output path), sp2 (server stdout capture),
  sp3 (domcontentloaded migration). All three MUST be merged before sp4 starts —
  otherwise the red list isn't trustworthy.
- **Assumed codebase state:** post-sp3 runner.py still has every `_assert_<screen>`
  function but with `wait_until="domcontentloaded"` everywhere.

## Scope

**In scope:**
- Re-run `pytest cast-server/tests/ui/` after Layer A merges; capture each child's
  `output.json` (paths surfaced in the orchestrator's `children` map).
- For each remaining `assertions_failed[]` entry whose error is "selector not found"
  or "endpoint 404" or similar wrong-target signal:
  1. Open the corresponding `templates/pages/<screen>.html` (and
     `templates/fragments/*.html` if relevant) and identify the real selector.
  2. Open `cast-server/cast_server/routes/api_*.py` and identify the real route shape.
  3. Patch the assertion in `runner.py`'s `_assert_<screen>` to use the real
     selector/route.
- For Scenario B1 specifically: `cast-ui-test-agents` may currently assert against a
  non-existent JSON `/api/agents` endpoint. Replace with either an HTML-fragment route
  under `/api/agents/*` (check `cast_server/routes/api_agents.py`) OR a DOM assertion
  on `/agents`.
- For Scenario B2 specifically: `cast-ui-test-scratchpad` delete-flow assertion must
  match the actual control rendered by `templates/pages/scratchpad.html` (or its
  fragments).
- For Scenario B3: if an assertion targets a feature that genuinely doesn't exist,
  REMOVE the assertion (the only acceptable deletion case).

**Out of scope (do NOT do these):**
- Do NOT delete assertions just to make the test green. Patch wrong assertions; only
  delete when the feature being tested doesn't exist (Scenario B3). Document any
  deletion in the commit message with "feature does not exist" rationale.
- Do NOT modify product code (templates, routes, services). Layer C is enumeration
  only; product fixes happen downstream in separate plans/tasks.
- Do NOT add new assertions. Repair only.
- Do NOT touch `conftest.py` or `test_full_sweep.py`.
- Do NOT modify the test agent definitions in `cast-server/tests/ui/agents/*` —
  per-screen assertions live in `runner.py`'s `_assert_<screen>` functions.
- Do NOT add `pytest.mark.flaky` retries. Flake is a Layer A bug.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/runner.py` | Modify | `_assert_<screen>` functions across the file. Edit only the assertions that fail post-Layer-A. |

## Detailed Steps

### Step 4.1: Re-run the harness; capture the red list

```
pytest cast-server/tests/ui/ -x --tb=long > /tmp/uitest-after-A.log 2>&1 || true
```

Then locate each child's `output.json` via the orchestrator's `children` map (printed
into the failure message by `_format_child_failures`). For each red child, copy
`assertions_failed[]` and the corresponding `console_errors[]` to a working notes
file. Recommended: `/tmp/uitest-layer-b-notes.md` (NOT committed; just for sp4
working memory).

### Step 4.2: Per-child triage

For EACH red child, in this order:

1. Read its `assertions_failed[]` entries.
2. Open the corresponding template file:
   - `agents` → `cast-server/cast_server/templates/pages/agents.html`
   - `dashboard` → `templates/pages/dashboard.html`
   - `runs` → `templates/pages/runs.html`
   - `scratchpad` → `templates/pages/scratchpad.html`
   - `goal-detail` → `templates/pages/goal_detail.html`
   - `focus` → `templates/pages/focus.html`
   - `about` → `templates/pages/about.html`
   - Plus `templates/fragments/*.html` and `templates/components/*.html` as needed.
3. For each failing assertion's selector, search the templates for the real one.
   Common drift patterns to expect:
   - `[data-testid="..."]` attrs that don't exist; the real selector is a class or
     `hx-*` attribute.
   - JSON endpoints that don't exist; the real endpoint returns an HTML fragment.
   - Selectors looking for an item that requires a goal-slug / run-id substitution.
4. Open `cast-server/cast_server/routes/api_*.py` to confirm any endpoint asserted
   against returns the expected status/shape.
5. Patch the assertion in `_assert_<screen>` (in `runner.py`) to match.

### Step 4.3: Special cases

**B1 (FR-004 Scenario 1) — `cast-ui-test-agents`.** Today's assertion may probe
`/api/agents` expecting JSON. Check `cast_server/routes/api_agents.py` for what
actually exists:

- `POST /api/agents/{name}/trigger`
- `GET /api/agents/jobs/{run_id}`
- (No bare GET on `/api/agents` returning a JSON list, per the run prompt.)

Replacement: assert agent visibility either via:
- A DOM assertion on `/agents` page (`expect(page.locator("...")).to_be_visible()`),
- Or by hitting an existing HTML-fragment route under `/api/agents/*` (verify the
  route exists; do NOT invent one).

**B2 (FR-004 Scenario 2) — `cast-ui-test-scratchpad` delete flow.** Open
`templates/pages/scratchpad.html` (and fragments). Locate the actual delete-control
markup — typically an `hx-delete` attr on a button. Patch the runner's selector and
the expected post-delete DOM state to match.

**B3 (FR-004 Scenario 3) — feature genuinely missing.** Delete the assertion. In the
commit message: "Removed `<assertion-name>`: feature does not exist in
`templates/pages/<screen>.html`."

### Step 4.4: Re-run; iterate

After patching all per-child assertions:

```
pytest cast-server/tests/ui/
```

Every remaining `assertions_failed[]` entry should now point at something concrete in
the codebase — either a 500-level server response (Layer C territory) or a genuine
DOM/state bug (Layer C territory). No "selector not found" or "endpoint 404 by
design" entries should remain.

If any entry still references a non-existent selector/route, you missed one in
Step 4.2. Repeat the triage for that child.

## Verification

1. **Spot check:** open `cast-server/tests/ui/runner.py` and walk each `_assert_<screen>`
   function. Cross-reference every CSS selector and every URL against the templates
   and routes. No selector should reference a `data-testid` or class that doesn't
   appear in the HTML; no URL should reference a route that returns 404 by design.
2. **Dynamic check:** re-run the harness. The remaining red list (per SC-004) MUST
   only contain entries where the selector/route exists in the codebase but the
   assertion still fails. Those are Layer C bugs, ready for sp5.
3. **No silent green-washing:** there should be no commit in this sub-phase that
   removes an assertion without an accompanying "feature does not exist" rationale.

## Acceptance Criteria

- Every remaining `assertions_failed[]` entry post-sp4 references a selector or
  endpoint that exists in `templates/pages/`, `templates/fragments/`,
  `templates/components/`, or `cast_server/routes/api_*.py`.
- No assertion was deleted to make the test green except where the feature being
  tested genuinely does not exist.
- Re-running the harness produces a red list that's strictly smaller than the
  post-sp3 red list, AND every remaining failure is reproducible by manual click-through
  (the Layer C precondition for SC-005).
- Only `runner.py` changed in this sub-phase.

## Risk / Notes

- **The 1-pass-might-not-be-enough trap.** Patching one selector sometimes reveals
  the next assertion was also wrong (e.g., the delete button worked but the
  "row gone" assertion targeted the wrong locator). Iterate until no fictional
  targets remain.
- **No new abstractions.** Don't introduce a `SELECTORS = {...}` registry or a
  per-screen helper module. Each `_assert_<screen>` stays its own readable block.
- **Decision gate.** When sp4 is done, present the remaining red list to the human
  before sp5. The human classifies each entry as "real product bug" (→ task in sp5)
  or "still a bad assertion" (→ another sp4 pass).
- **Beware the seam between sp3 and sp4.** If a `networkidle` substring still appears
  in `runner.py` after sp3, sp4 has nothing to do until sp3 is fixed. Re-grep before
  starting.
