# Sub-phase 2: Recursive Macro + Fragment + CSS + Both Route Swaps

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp1 is committed (`get_runs_tree` callable, `idx_agent_runs_parent` exists).

## Objective

Render the threaded layout. Add the recursive Jinja macro (`run_node.html`) and the line-2 fragment (`run_status_cells.html`), port the mockup's CSS into `style.css`, and swap **both** the page route (`runs_page` in `routes/pages.py`) and the HTMX list endpoint (`list_runs` in `routes/api_agents.py`) to call `get_runs_tree`. After this sub-phase, visiting `http://127.0.0.1:8000/runs` shows the threaded tree on page 1 AND clicking "Next" preserves the tree shape on page 2 (today's bug: page 2 silently reverts to flat top-level rendering).

## Dependencies

- **Requires completed:** sp1 (data layer). `get_runs_tree` must return the documented dict shape; templates assume `children`, `descendant_count`, `failed_descendant_count`, `rework_count`, `status_rollup`, `total_cost_usd`, `wall_duration_seconds`, `ctx_class`, `is_rework`, `rework_index` exist on each tree node.
- **Assumed codebase state:** Pre-sp2 tree at HEAD + sp1 commits. `runs_page` (`routes/pages.py:175–191`) and `list_runs` (`routes/api_agents.py:222–232`) still call `get_all_runs(top_level_only=True, ...)`. Mockup at `docs/plan/mockups/runs-threaded.html` is the visual source of truth.

## Scope

**In scope:**
- NEW `cast-server/cast_server/templates/macros/run_node.html` — recursive macro `render_run(run, depth=0)` using direct self-recursion.
- NEW `cast-server/cast_server/templates/fragments/run_status_cells.html` — the line-2 cells. Wrapper `<span class="run-status-cells" id="run-cells-{{ run.id }}">…</span>`. Carries `hx-get`/`hx-trigger`/`hx-swap` ONLY when `run.status in ('running', 'pending', 'rate_limited')`. (The endpoint that serves this URL is added in sp3 — until then, polls 404 silently for running rows. That's acceptable inside one PR's commit chain.)
- UPDATE `cast-server/cast_server/templates/fragments/runs_list.html` — `{% import "macros/run_node.html" as rn %}` and replace the per-L1 row render with `{{ rn.render_run(run) }}`.
- UPDATE `cast-server/cast_server/static/style.css` — APPEND threaded styles ported from the mockup. Do NOT remove legacy styles in this sub-phase (sp5 owns deletion).
- UPDATE `cast-server/cast_server/routes/pages.py` — `runs_page` calls `get_runs_tree(...)` instead of `get_all_runs(top_level_only=True, ...)`. Pass through `status_filter`, `page`, `per_page`, `exclude_test`.
- UPDATE `cast-server/cast_server/routes/api_agents.py` — `list_runs` (line 222) calls `get_runs_tree(...)`. Same parameter wiring.
- Remove the `xfail` markers added by sp1 to `test_list_runs_returns_l1_with_descendants` and `test_list_runs_pagination_by_l1_only`.

**Out of scope (do NOT do these):**
- The HTMX `/status_cells` endpoint and `test_runs_template.py` — sp3.
- Inline JS for collapse/clipboard — sp4.
- Deleting legacy fragments / endpoints / unused CSS — sp5.
- UI test agent prompt edits — sp6.
- Spec capture — sp7.
- Editing `get_all_runs` (still used elsewhere).

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/templates/macros/run_node.html` | Create | Does not exist. |
| `cast-server/cast_server/templates/fragments/run_status_cells.html` | Create | Does not exist. |
| `cast-server/cast_server/templates/fragments/runs_list.html` | Modify | Renders flat top-level rows via `run_row.html`. |
| `cast-server/cast_server/templates/pages/runs.html` | Read-only review | Body shape unchanged this sub-phase. (sp4 appends script.) |
| `cast-server/cast_server/static/style.css` | Modify (append) | Pre-existing flat-runs styles intact; no threaded styles yet. |
| `cast-server/cast_server/routes/pages.py` | Modify | `runs_page` (lines 175–191) calls `get_all_runs(top_level_only=True, ...)`. |
| `cast-server/cast_server/routes/api_agents.py` | Modify | `list_runs` (lines 222–232) calls `get_all_runs(top_level_only=True, ...)`. |
| `cast-server/tests/test_runs_api.py` | Modify (un-xfail) | Two cases marked `xfail(strict=True)` by sp1. |

## Detailed Steps

### Step 2.1: Create the recursive macro `run_node.html`

```jinja
{# cast-server/cast_server/templates/macros/run_node.html #}
{% macro render_run(run, depth=0) %}
<div class="run-group{% if run.failed_descendant_count and not run.rework_count %} has-failure{% elif run.rework_count and not run.failed_descendant_count %} has-warning{% endif %}">
  <div class="run-node{% if depth > 0 %} is-child{% endif %}{% if run.ctx_class %} ctx-{{ run.ctx_class }}{% endif %}"
       data-run-id="{{ run.id }}"
       data-resume-cmd="{{ run.resume_command|default('', true)|e }}">

    <div class="row-1">
      <span class="status-dot {{ run.status }}"></span>
      <span class="agent-name">{{ run.agent_name }}</span>
      <span class="crumbs">
        {% if run.goal_slug %}<a class="goal" href="/goals/{{ run.goal_slug }}">{{ run.goal_slug }}</a>{% endif %}
        {% if run.task_id %}<span class="sep">·</span><span class="task">{{ run.task_title or run.task_id }}</span>{% endif %}
      </span>
      <span class="caret" aria-hidden="true">▾</span>
    </div>

    {% include "fragments/run_status_cells.html" %}
  </div>

  {% if run.children %}
    <div class="thread{% if run.failed_descendant_count and not run.rework_count %} has-failure{% elif run.rework_count and not run.failed_descendant_count %} has-warning{% endif %}">
      {% for child in run.children %}
        {{ render_run(child, depth + 1) }}
      {% endfor %}
    </div>
  {% endif %}

  <div class="detail" id="run-detail-{{ run.id }}" hidden>
    {# artifacts, summary, error, full ctx bar, action buttons (Open run / View transcript / Recheck / Cancel) — port from mockup #}
    {# Resume button is REMOVED here; the line-2 ⧉ owns it (Decision #11). #}
  </div>
</div>
{% endmacro %}
```

Key invariants:
- The recursion uses Jinja's direct self-call (`render_run(child, depth + 1)`); do NOT introduce `{% import "macros/run_node.html" as self %}` (the imported-self pattern adds an indirection without value — Decision in plan).
- The outer `.run-group` carries `has-failure`/`has-warning`. The inner `.run-node` carries `is-child` and `ctx-{class}`. Don't conflate them.
- The `.thread` mirrors the same `has-failure`/`has-warning` so the rail itself can render the right color via CSS.
- The `<div class="detail">` is the L3 expansion target. Hidden by default; sp4's JS toggles it.

### Step 2.2: Create the fragment `run_status_cells.html`

```jinja
{# cast-server/cast_server/templates/fragments/run_status_cells.html #}
<span class="run-status-cells row-2"
      id="run-cells-{{ run.id }}"
      {% if run.status in ('running', 'pending', 'rate_limited') %}
      hx-get="/api/agents/runs/{{ run.id }}/status_cells"
      hx-trigger="every 3s"
      hx-swap="outerHTML"
      {% endif %}>
  <span class="pill {{ run.status }}">{{ run.status }}</span>
  {% if run.ctx_class %}<span class="ctx-pill {{ run.ctx_class }}">ctx {{ run.ctx_class }}</span>{% endif %}
  {% if run.descendant_count %}<span class="rollup">{{ run.descendant_count }} steps</span>{% endif %}
  {% if run.failed_descendant_count %}<span class="rollup bad">⚠ {{ run.failed_descendant_count }} failed</span>{% endif %}
  {% if run.rework_count and not run.failed_descendant_count %}<span class="rollup warn">⚠ {{ run.rework_count }} reworked</span>{% endif %}
  {% if run.is_rework %}<span class="rework-tag">↻ rework #{{ run.rework_index }}</span>{% endif %}
  {% if run.wall_duration_seconds is not none %}<span class="duration">{{ run.wall_duration_seconds | format_duration }}</span>{% elif run.active_seconds %}<span class="duration">{{ run.active_seconds | format_duration }}</span>{% endif %}
  {% if run.total_cost_usd %}<span class="cost">${{ '%.4f' | format(run.total_cost_usd) }}</span>{% endif %}
  <button class="copy-resume" type="button" data-cmd="{{ run.resume_command|default('', true)|e }}" aria-label="Copy resume command">⧉</button>
  <span class="relative-time" data-ts="{{ run.created_at }}">{{ run.created_at | relative_time }}</span>
</span>
```

Notes:
- Reuse existing Jinja filters (`format_duration`, `relative_time`) if they exist; else add them in `cast_server/templates/_filters.py` (or wherever current filters live) — but only if missing. Don't duplicate.
- The `data-cmd` attribute on `.copy-resume` is what sp4's JS reads.
- HTMX attrs are conditional: completed runs do not poll. Required by `test_runs_template.py` (sp3) which asserts the attrs land on the inner span, never the outer node.

### Step 2.3: Update `runs_list.html`

Top of file:

```jinja
{% import "macros/run_node.html" as rn %}
```

Replace the per-L1 row render block (currently invokes `run_row.html`) with:

```jinja
{% for run in runs %}
  {{ rn.render_run(run) }}
{% endfor %}
```

Pagination footer and surrounding structure unchanged. `run_row.html` and `run_children.html` are NOT deleted here — sp5 handles deletion after grep confirms zero refs.

### Step 2.4: Append threaded styles to `style.css`

Port verbatim from `docs/plan/mockups/runs-threaded.html`'s `<style>` block. Group the new rules at the bottom of `style.css` under a comment header `/* === threaded /runs (sp2) === */` so sp5's cleanup boundary is grep-able.

Class list to port (no omissions — match the plan's "CSS additions" list):

- `.run-group`, `.run-group.has-failure`, `.run-group.has-warning`
- `.run-node`, `.run-node.is-child`, `.run-node.expanded`
- `.row-1`, `.row-2`
- `.status-dot.{completed,running,failed,pending,rate}` (verify rates and pending exist; add if missing)
- `.agent-name` and `.run-node.is-child.ctx-low .agent-name`, `.ctx-mid`, `.ctx-high` agent-name tints
- `.crumbs .goal` (muted gray; hover → accent + underline)
- `.pill.{completed,running,failed,pending,rate}` (keep existing if present; verify mockup tones)
- `.ctx-pill.{low,mid,high}` (NEW — green/amber/red)
- `.rollup`, `.rollup.bad`, `.rollup.warn`
- `.copy-resume`, `.copy-resume.copied`
- `.rework-tag` (purple)
- `.thread`, `.thread.has-failure`, `.thread.has-warning`, `.thread::before` connector
- `.detail`, `.ctx-bar`, `.ctx-seg.{system,memory,agents,messages}`, `.ctx-legend`
- Mobile media query `@media (max-width: 600px) { .relative-time, .task { display: none; } }`

Do NOT remove legacy `.run-row*`, `.run-children-container`, `.child-run`, `.child-indent` here — sp5's cleanup step grep-gates the deletion. Some templates may still refer to them transitionally.

### Step 2.5: Swap `runs_page` route

`cast-server/cast_server/routes/pages.py:175–191` — replace:

```python
runs_data = get_all_runs(
    top_level_only=True,
    status_filter=status_filter,
    page=page,
    per_page=per_page,
    exclude_test=exclude_test,
)
```

with:

```python
runs_data = get_runs_tree(
    status_filter=status_filter,
    page=page,
    per_page=per_page,
    exclude_test=exclude_test,
)
```

Imports: add `get_runs_tree` to the existing `from cast_server.services.agent_service import ...` line (do NOT duplicate). Keep `get_all_runs` import only if other callers in this file need it; remove if unused (verify with `grep -n get_all_runs cast-server/cast_server/routes/pages.py`).

### Step 2.6: Swap `list_runs` HTMX endpoint

`cast-server/cast_server/routes/api_agents.py:222–232` — same swap. This is the route that powers HTMX pagination (clicking "Next" on the page footer fires `hx-get="/api/agents/runs?page=N"` which renders `runs_list.html`). Without this swap, page 2 silently reverts to flat rendering — exactly the bug the redesign exists to fix.

### Step 2.7: Un-xfail the two API tests sp1 added

In `cast-server/tests/test_runs_api.py`, remove the `pytest.mark.xfail(strict=True, reason="awaits sp2 route swap")` decorators from `test_list_runs_returns_l1_with_descendants` and `test_list_runs_pagination_by_l1_only`. They should turn green now.

## Verification

### Automated Tests (permanent)
- `uv run pytest cast-server/tests/test_runs_api.py -k "list_runs_returns_l1_with_descendants or list_runs_pagination_by_l1_only"` — both green (no longer xfail).
- Full suite `uv run pytest` — no regressions.

### Validation Scripts (temporary)

```bash
# 1. Both routes call the new function:
grep -n 'get_runs_tree' cast-server/cast_server/routes/pages.py cast-server/cast_server/routes/api_agents.py
# Expect: a hit in each file.

# 2. Macro and fragment exist:
ls cast-server/cast_server/templates/macros/run_node.html
ls cast-server/cast_server/templates/fragments/run_status_cells.html

# 3. Macro is direct self-recursion (no self-import):
grep -n 'import "macros/run_node' cast-server/cast_server/templates/macros/run_node.html
# Expect: no output.

# 4. runs_list imports the macro:
grep -n 'import "macros/run_node.html"' cast-server/cast_server/templates/fragments/runs_list.html
# Expect: one hit.

# 5. CSS section header is present (boundary marker for sp5):
grep -n 'threaded /runs (sp2)' cast-server/cast_server/static/style.css
# Expect: one hit.

# 6. HTMX attrs are conditional in the fragment:
grep -A 4 'hx-get=' cast-server/cast_server/templates/fragments/run_status_cells.html
# Expect: surrounded by an {% if run.status in (...) %} guard.
```

### Manual Checks

Restart the server (`bin/cast-server` or whatever the dev command is) and perform the visual checklist:

1. Visit `http://127.0.0.1:8000/runs`. Confirm two lines per row, status dot + agent name on line 1, status pill + ctx pill paired at start of line 2.
2. Find a multi-level run (e.g. a `cast-preso-orchestrator` run). Confirm L2 and L3 children are visible without clicking expand.
3. Click "Next" in the pagination footer. Confirm page 2 still renders threaded layout (the bug-fix this sub-phase exists for).
4. Confirm a single rail per group; nested groups render their own rail; no per-depth horizontal indent of row content.
5. A child with `ctx_class=low` is green; `mid` amber; `high` red. Child agent name tints to match.
6. Locate a preso-style group with re-runs. Confirm `↻ rework #2` tag on the second instance and `⚠ N reworked` rollup pill on the parent.
7. Locate a group with a failed descendant. Group has solid red left border; parent line 2 shows `⚠ N failed` red rollup.
8. Locate a group with reworks but no unresolved failures. Group has amber left border (`has-warning`).
9. Set status filter to `failed`. Confirm L1s whose own status is `completed` but with a failed descendant appear.
10. Resize viewport to 480px. Confirm relative-time and task text hide.

(Items 11–18 from the plan's manual verification list — collapse persistence, HTMX poll safety, copy-resume — are intentionally deferred to sp4 and sp3 verifications. This sub-phase's manual checks scope is items 1–10.)

### Success Criteria
- [ ] `run_node.html` exists with recursive `render_run` macro using direct self-recursion.
- [ ] `run_status_cells.html` exists with conditional hx-* attrs.
- [ ] `runs_list.html` imports and invokes the macro.
- [ ] `style.css` has the new `/* === threaded /runs (sp2) === */` block.
- [ ] `runs_page` and `list_runs` both call `get_runs_tree`.
- [ ] Page 1 and page 2 both render threaded layout.
- [ ] All 10 manual visual checks pass.
- [ ] Sp1's xfail markers in `test_runs_api.py` removed; tests green.
- [ ] Full test suite green.

## Execution Notes

- The mockup uses CSS variables for accent colors. Confirm the existing `style.css` defines them; if not, port the `:root { --accent: ...; --danger: ...; ... }` block from the mockup too.
- Jinja's `{% include "fragments/run_status_cells.html" %}` inside the macro inherits the macro's `run` context — no explicit context pass needed.
- `relative_time` and `format_duration` filters: search `cast-server/cast_server/templates/` and `cast-server/cast_server/main.py` (or wherever filters are registered). If only one of the two exists, add the missing one in the same place.
- `goal_slug` and `task_title` may not be in every run row dict. Use `|default('', true)` defensively.
- Resume command field name: confirm whether `agent_runs.resume_command` is hydrated by the service layer's tree path. If not, hydrate it (cheap — it's a single text column).

**Spec-linked files:** None this sub-phase.
