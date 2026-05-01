# Sub-phase 4: Inline JS — Collapse Persistence + Clipboard Copy

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp2 is committed (macro renders `.run-node` containers with `data-run-id` and `.copy-resume` buttons with `data-cmd`).

## Objective

Make the threaded layout interactive without a framework. Two small, dependency-free modules go inline at the end of `pages/runs.html`:

1. **Collapse persistence** — clicking a `.run-node` toggles `.expanded`; the state writes to `localStorage["runs:expanded:<run_id>"]`. On page load AND on `htmx:afterSwap`, every run-node's expanded class is reapplied from localStorage.
2. **Copy-resume** — clicking a `.copy-resume` button writes its `data-cmd` to the clipboard, flashes a `.copied` class for ~1.1s, and stops propagation so the row does NOT also expand.

The state lives on the outer `.run-node`, NOT on the swapped `.run-status-cells` span — so the 3s HTMX poll cannot disturb expand state. Sp3 already enforces this with a structural test; this sub-phase adds the user-visible behavior.

## Dependencies

- **Requires completed:** sp2 (macro emits `.run-node[data-run-id]` and `.copy-resume[data-cmd]`).
- **May proceed in parallel with sp3.** No file overlap; sp3 touches `routes/api_agents.py` and a new test file, sp4 touches only `pages/runs.html`.
- **Assumed codebase state:** Pre-sp4 tree at HEAD + sp1 + sp2 commits. No inline JS for these behaviors yet.

## Scope

**In scope:**
- APPEND inline `<script>` block at end of `cast-server/cast_server/templates/pages/runs.html` body.
- Two modules: collapse persistence + clipboard copy. No external deps. ES2017+ is fine (modern browsers only).

**Out of scope (do NOT do these):**
- Touching the macro, the fragment, the CSS, or any route — those are sp2 / sp3.
- Adding a JS bundler or framework. This is hand-written inline JS.
- Capping localStorage key count — listed as a Risk in the plan; deferred until observed.
- Deleting legacy `run_row.html` script handlers (if any survive) — sp5 owns deletions.
- Spec capture — sp7.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/templates/pages/runs.html` | Modify (append `<script>`) | No inline collapse / clipboard JS today. |

## Detailed Steps

### Step 4.1: Append the inline script block

At the end of the `pages/runs.html` body (just before `</body>` if structured that way; otherwise at the end of the page-content block):

```html
<script>
(function () {
  'use strict';

  const STORAGE_PREFIX = 'runs:expanded:';

  function applyExpandedFromStorage(root) {
    const scope = root || document;
    scope.querySelectorAll('.run-node[data-run-id]').forEach(node => {
      const id = node.dataset.runId;
      if (!id) return;
      if (localStorage.getItem(STORAGE_PREFIX + id) === '1') {
        node.classList.add('expanded');
      }
    });
  }

  function toggleExpanded(node) {
    const id = node.dataset.runId;
    if (!id) return;
    const willExpand = !node.classList.contains('expanded');
    node.classList.toggle('expanded', willExpand);
    if (willExpand) {
      localStorage.setItem(STORAGE_PREFIX + id, '1');
    } else {
      localStorage.removeItem(STORAGE_PREFIX + id);
    }
  }

  // Click handler: toggle expand unless the click was on a button / link / copy-resume.
  document.addEventListener('click', function (e) {
    if (e.target.closest('.copy-resume')) return;          // handled below
    if (e.target.closest('a, button, input, textarea')) return;
    const node = e.target.closest('.run-node');
    if (node) toggleExpanded(node);
  });

  // Copy-resume click: write data-cmd to clipboard, flash .copied, stop propagation.
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.copy-resume');
    if (!btn) return;
    e.stopPropagation();           // do NOT also expand the row
    const cmd = btn.dataset.cmd || '';
    if (!cmd) return;
    navigator.clipboard.writeText(cmd).then(() => {
      btn.classList.add('copied');
      setTimeout(() => btn.classList.remove('copied'), 1100);
    }).catch(() => {
      // Clipboard write can fail under permissions / focus rules — degrade silently.
    });
  });

  // Initial restore on page load.
  applyExpandedFromStorage();

  // Re-apply after any HTMX swap (pagination, status_cells poll). The swapped
  // status_cells fragment lives INSIDE .run-node, so the outer node usually
  // survives — but pagination swaps the whole list, dropping all .expanded
  // classes. Re-applying here keeps state coherent.
  document.body.addEventListener('htmx:afterSwap', function () {
    applyExpandedFromStorage();
  });
})();
</script>
```

Notes:
- Wrapped in an IIFE so vars don't leak to global scope.
- Two separate top-level click listeners by design — separation of concerns. Both check `closest()` so clicks on inner spans (status pills, agent name, etc.) still bubble correctly.
- `e.stopPropagation()` on the copy-resume handler is critical; without it the click also runs through the expand handler.
- `htmx:afterSwap` reapplies because pagination swaps the whole list.

### Step 4.2: Confirm CSS hooks exist

Sp2 should have included styles for `.run-node.expanded` (showing the `.detail` panel) and `.copy-resume.copied` (flash). Verify:

```bash
grep -n '\.run-node\.expanded\|\.copy-resume\.copied' cast-server/cast_server/static/style.css
```

If `.run-node.expanded .detail` rule is missing (the mockup may toggle visibility differently), add a one-line rule:

```css
.run-node.expanded ~ .detail,
.run-node.expanded + .thread + .detail { display: block; }
.run-node:not(.expanded) ~ .detail { display: none; }
```

Adjust selector to match the macro's actual DOM order (the macro emits `<div class="detail">` as a sibling of `.run-node` inside `.run-group`). If the mockup uses the `hidden` HTML attribute on `.detail`, the JS could toggle that instead — but flipping a class is more idiomatic and CSS-friendlier.

### Step 4.3: Manual sanity check

In the browser:

1. Expand 3 rows at different depths inside one L1 group. Reload the page. Confirm the same 3 rows are still expanded.
2. Click a `.copy-resume` button. Confirm the browser clipboard contains the run's resume command. Confirm the `.copied` flash appears for ~1s. Confirm the click did NOT expand the row.
3. Expand a parent of a running child. Wait 9 seconds (3 status_cells polls). Confirm the parent stays expanded.
4. Click "Next" on pagination. Confirm any rows that were already expanded on page 2 (from a previous visit) re-render expanded.
5. Open the goal-link `<a class="goal">` in the row. Confirm clicking the link navigates AND does NOT also expand the row (because the click handler ignores anchors).

## Verification

### Automated Tests (permanent)
- No new pytest cases this sub-phase; the markup-shape guard from sp3 already enforces that the swap target is the inner span. Behavioral coverage of the JS lands in sp6 (UI-test agent assertions: "reload preserves expand state", "⧉ click writes clipboard", "click on `.copy-resume` does not expand").
- Full suite `uv run pytest` — no regressions.

### Validation Scripts (temporary)

```bash
# 1. Inline script is present in the page template:
grep -n 'STORAGE_PREFIX' cast-server/cast_server/templates/pages/runs.html
# Expect: one hit.

# 2. The IIFE wrapper is in place:
grep -n '(function ()' cast-server/cast_server/templates/pages/runs.html
# Expect: at least one hit (the new script).

# 3. htmx:afterSwap listener exists:
grep -n 'htmx:afterSwap' cast-server/cast_server/templates/pages/runs.html
# Expect: one hit.
```

### Manual Checks
- All 5 items in step 4.3 verified.
- DevTools → Application → Local Storage. Confirm keys with prefix `runs:expanded:` exist after expanding rows. Confirm they're removed when the row is collapsed.

### Success Criteria
- [ ] Reload preserves expand state across all depths.
- [ ] Copy-resume writes clipboard, flashes `.copied`, does not expand row.
- [ ] HTMX status_cells poll preserves expand state on the parent.
- [ ] Pagination → expanded state from prior visits is reapplied.
- [ ] Goal link click navigates without expanding row.
- [ ] localStorage keys carry the `runs:expanded:<id>` format.
- [ ] Full test suite green.

## Execution Notes

- Do NOT use `localStorage.setItem(key, JSON.stringify(true))`. The presence-of-key-equals-expanded contract is documented in `_shared_context.md` and locked in the spec sp7 will write.
- `navigator.clipboard.writeText` requires HTTPS in production browsers, but `localhost` is exempt. Dev works without ceremony.
- If any pre-existing inline script in `pages/runs.html` already uses `htmx:afterSwap`, fold the new logic into the existing listener rather than registering a second one (avoids ordering bugs).
- The expand handler ignores clicks on `<button>` and `<a>`. Confirm the `caret` element in the macro is NOT a `<button>` — if it is, the row won't expand on caret click. Sp2's macro renders the caret as a `<span class="caret">`, which is what we want.

**Spec-linked files:** None this sub-phase.
