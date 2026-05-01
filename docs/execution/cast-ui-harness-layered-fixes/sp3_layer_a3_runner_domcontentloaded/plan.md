# Sub-phase 3: Layer A3 — Runner `domcontentloaded` migration (FR-003)

> **Pre-requisite:** Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` before starting.

## Objective

Replace every `wait_until="networkidle"` (and every `page.wait_for_load_state("networkidle", ...)`)
in `cast-server/tests/ui/runner.py` with `domcontentloaded`. The dashboard, runs page,
goal-detail, and others use HTMX polling — `networkidle` never resolves on a polling
page, so each child times out 30s into the assertion phase. Four of the six current
red children are masked by this single bug.

This sub-phase delivers FR-003 and SC-003 of the layered-fixes plan.

## Dependencies
- **Requires completed:** None. Runs in parallel with sp1 and sp2.
- **Assumed codebase state:** `cast-server/tests/ui/runner.py` exists with the
  per-screen `_assert_<screen>` functions and the call-site list summarized below.

## Scope

**In scope:**
- Change every `page.goto(url, wait_until="networkidle")` to
  `page.goto(url, wait_until="domcontentloaded")`.
- Change every `page.wait_for_load_state("networkidle", timeout=...)` to either:
  - `page.wait_for_load_state("domcontentloaded", timeout=...)`, OR
  - delete the call entirely if the next assertion is already an `expect(...).to_be_visible(timeout=…)`
    that auto-waits.
- Verify per-screen overrides: today none of the screens genuinely needs `load`
  semantics. Default to `domcontentloaded` everywhere.

**Out of scope (do NOT do these):**
- Do NOT change selectors or assertion logic — that's sp4's territory. This sub-phase
  is a mechanical wait-strategy swap.
- Do NOT touch `conftest.py` or `test_full_sweep.py`.
- Do NOT introduce a `WAIT_UNTIL = "domcontentloaded"` constant unless duplication
  exceeds the 3+ identical-line bar from the plan. Inline the literal.
- Do NOT add explicit `page.wait_for_timeout(...)` sleeps to replace networkidle's
  effect. Rely on Playwright's auto-wait inside `expect(...)`.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/runner.py` | Modify | Has 11 `page.goto(..., wait_until="networkidle")` and 2 `page.wait_for_load_state("networkidle", ...)` calls. |

## Detailed Steps

### Step 3.1: Enumerate the call sites

Confirmed list (line numbers approximate; re-grep before editing):

```
runner.py:162   page.goto(f"{base_url}/", wait_until="networkidle")          # _assert_dashboard
runner.py:234   page.goto(f"{base_url}/agents", wait_until="networkidle")    # _assert_agents
runner.py:285   page.goto(f"{base_url}/runs", wait_until="networkidle")      # _assert_runs (entry)
runner.py:323   page.goto(f"{base_url}/runs", wait_until="networkidle")      # _assert_runs (re-nav, e.g., post-cancel)
runner.py:349   page.goto(f"{base_url}/scratchpad", wait_until="networkidle")
runner.py:398   page.goto(f"{base_url}/goals/{goal_slug}", wait_until="networkidle")
runner.py:412   page.wait_for_load_state("networkidle", timeout=ASSERTION_TIMEOUT_MS)
runner.py:436   page.wait_for_load_state("networkidle", timeout=ASSERTION_TIMEOUT_MS)
runner.py:498   page.goto(f"{base_url}/runs", wait_until="networkidle")      # _assert_runs (cancel flow follow-up)
runner.py:510   page.goto(f"{base_url}/focus", wait_until="networkidle")
runner.py:526   page.goto(f"{base_url}/about", wait_until="networkidle")
```

Run `grep -n "networkidle" cast-server/tests/ui/runner.py` before editing to confirm
the current call sites and line numbers.

### Step 3.2: Mechanical replacements

For each `page.goto(..., wait_until="networkidle")`, change the kwarg value to
`"domcontentloaded"`. Nothing else.

For the two `page.wait_for_load_state("networkidle", timeout=ASSERTION_TIMEOUT_MS)`
calls (lines ~412, ~436):

1. Read the surrounding context — what assertion does the call precede?
2. If the next assertion is `expect(page.locator(...)).to_be_visible(timeout=ASSERTION_TIMEOUT_MS)`
   or any `expect()` with auto-wait, **delete the `wait_for_load_state` line**. The
   auto-wait inside `expect()` handles readiness.
3. If the next operation is a non-auto-waiting one (e.g., a raw `.click()` on a
   selector that may not yet be in the DOM), keep the call but switch to
   `"domcontentloaded"`.

In practice, both occurrences in the goal-detail flow follow `expect(...).to_be_visible(...)`
patterns. Default action: **delete** them. Only retain the call (with the new
strategy) if the next operation has no auto-wait.

### Step 3.3: Quick re-grep

After editing:

```
grep -n "networkidle" cast-server/tests/ui/runner.py
```

Should return zero matches.

```
grep -n "wait_until=" cast-server/tests/ui/runner.py
```

Every hit should now be `wait_until="domcontentloaded"`.

### Step 3.4: Verify the per-screen flow still completes

Run a single child manually against a live test cast-server (or against the dev
server, if you trust it for a smoke test):

```
python cast-server/tests/ui/runner.py \
  --screen=dashboard \
  --base-url=http://127.0.0.1:8005 \
  --goal-slug=<some-existing-slug> \
  --output=/tmp/dashboard-out.json
```

Confirm:
1. The output JSON's `assertions_failed[]` does NOT contain any "Navigation timeout
   exceeded" or "networkidle" errors.
2. Real assertion failures (selector-not-found, status code mismatches) still appear
   if they were going to appear — sp3 isn't supposed to make them pass, only to stop
   masking them. Those are sp4's territory.

## Verification

1. **Static check:** `grep -n "networkidle" cast-server/tests/ui/runner.py` returns
   zero matches.
2. **Static check:** `grep -n "wait_until=" cast-server/tests/ui/runner.py` returns
   only `wait_until="domcontentloaded"`.
3. **Dynamic check:** Run the full harness via `pytest cast-server/tests/ui/`. Inspect
   each child's `output.json` (orchestrator dumps paths in the `children` map).
   `assertions_failed[]` MUST contain zero entries that mention `networkidle` or
   "Navigation timeout exceeded after 30000ms" with `goto` in the trace. (SC-003.)
4. **Dynamic check:** Snapshot artifacts at `/tmp/diecast-uitest-debug-*/` show
   pages rendered with content (not blank screenshots from a timed-out goto).

## Acceptance Criteria

- Zero `networkidle` references remain in `runner.py`.
- All `page.goto` calls use `wait_until="domcontentloaded"`.
- `page.wait_for_load_state("networkidle", ...)` calls are either removed (preferred,
  when followed by auto-waiting `expect()`) or migrated to `"domcontentloaded"`.
- Re-running the harness shows zero `networkidle`/goto-timeout entries in any child's
  `assertions_failed[]`.
- No new abstractions, constants, or helpers. Mechanical edit only.

## Risk / Notes

- **Don't preempt sp4.** If after this swap a child still fails because a selector
  doesn't exist, that's a Layer B (sp4) fix, NOT a sp3 problem. Resist the urge to
  patch selectors here.
- **HTMX polling is the reason `networkidle` was wrong.** Pages like `/runs` poll
  every few seconds for run status — there's no quiet network state to wait for.
  `domcontentloaded` fires once the initial DOM is parsed, which is the right moment
  for Playwright's per-element auto-wait to take over.
- **`expect(...).to_be_visible(timeout=...)` already auto-waits.** That's why deleting
  the trailing `wait_for_load_state` calls (Step 3.2) is safe — the assertion itself
  retries until visible.
- **Per-screen override note.** FR-003 allows per-screen overrides only if a specific
  screen genuinely requires `load`. None expected today; document any deviation in a
  one-line comment if you hit one.
