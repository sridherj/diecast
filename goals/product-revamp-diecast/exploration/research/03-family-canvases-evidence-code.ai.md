# Code Exploration: Family Canvases & Evidence — Terrain Map (Step 03)

**Goal context:** Product Revamp: Diecast — Vision Prototype. Step 03 asks: how should each
workflow family's canvas be shaped, and how should its output evidence be shown? Four locked
families: (1) new feature/initiative, (2) bug-fix/debug loop (hypothesis→experiment→observation
iterations), (3) spike/quick-conclusion, (4) data analysis/research. Each needs a distinct stage
model + canvas layout + iteration model + a fitted evidence treatment.
**Codebase:** `/data/workspace/diecast` (current cast-server UI) + the preso v2/v3 board/ticket
arc designs at `/data/workspace/second-brain/taskos/goals/taskos-gtm/` (WHAT docs a08–a11, v3
s8a/chain/dash, and the rendered microsite mocks M4–M9).
**Date:** 2026-06-11
**Framing:** VISION-FIRST. This is a terrain map only — what exists today and what the preso
flow already solved — as a baseline, never a boundary. Recommendations belong to the playbook.

> **MCP note:** code-review-graph knowledge graph is not built for this repo (SessionStart hook
> reported "No knowledge graph found"). All findings below come from Glob/Grep/Read. No MCP
> structural queries were available; none were needed for a terrain map of this size.

---

## 0. The one-sentence terrain summary

**Today, Diecast renders *every* goal as the same four-phase pipeline
(`requirements → exploration → plan → execution`) with the same five-tab layout, the same task
list, and prose-only artifacts.** There is no concept of a workflow family, no per-family canvas
shape, no iteration model beyond a flat task checkbox, and no fitted evidence surface. The single
genuinely strong asset is the **execution dispatch-tree** on the `/runs` page. Meanwhile, the
preso v2/v3 work has *already designed* the richest target surfaces this step needs — the
board→ticket→decision→escalation arc and, critically for step 03, a **spike-branching canvas
(M6)** and a **data/evidence rollup with a real SVG chart (M9)**. The prototype should treat the
current UI as the "one-shape-fits-all failure mode to escape" and the preso mocks as the
proven-design starting points for three of the four families.

---

## 1. Data Model & Schema

The product is a thin server over SQLite. Entities live in `cast-server/cast_server/models/`.

### Core entities

| Entity | File | Shape relevant to step 03 |
|--------|------|---------------------------|
| `Goal` | `models/goal.py` | `slug, title, status, phase, in_focus, tags, folder_path, external_project_dir`. **No `workflow_family`/`type` field.** A goal carries a single `phase` string (one of the 4 fixed phases) — there is no notion of "this goal is a debug loop vs a feature". |
| `Task` | `models/task_v2.py` (canonical), `models/task.py` (legacy) | `goal_slug, phase, parent_id, title, outcome, action, task_type, estimate_size (XS–XL), energy, assigned_to, status, tip, recommended_agent, task_artifacts[], rationale, is_spike`. |
| `AgentRun` | `models/agent_run.py` | `id, agent_name, goal_slug, task_id, status, output(dict), artifacts[], parent_run_id, session_id, claude_agent_id, input/output_tokens, cost_usd, context_usage(dict), resume_command, git_worktree_path`. This is the execution-layer record. |
| `AgentConfig` | `models/agent_config.py` | static agent registry metadata. |
| `Suggestion` | `models/suggestion.py` | task suggestions (with `is_spike`). |

### Schema-level facts that matter for the four families

- **`PHASES = ["requirements", "exploration", "plan", "execution"]`** is a hardcoded module
  constant in `cast-server/cast_server/config.py:52`. It is referenced in at least 7 files
  (`goal_service.py`, `task_service.py`, `api_goals.py`, `pages.py`, …). The four-phase pipeline
  is baked into the data layer, the routing layer, and the templates simultaneously. Any
  per-family stage model is a cross-cutting change today, not a config toggle.
- **`PHASE_ARTIFACTS`** (`config.py:53`) hardwires which files render in each phase tab:
  `requirements → [requirements.human.md, refined_requirements.collab.md]`,
  `exploration → [exploration/]`, `plan → [plan.collab.md]`, `execution → []`. Evidence is
  whatever markdown happens to live at those paths.
- **`is_spike: bool`** already exists on `Task` (`task_v2.py:68`) and flows through
  `task_service.create_task` → DB → suggestion cards. This is the *only* family-ish signal in
  the schema. But it is a boolean badge, not a stage model: there is **no `spike_ref`, no
  conclusion-artifact link, no decision linkage** — exactly the `spike_ref` wiring US2-S3 / FR-016
  require. The data groundwork exists; the relationship does not.
- **`task_type`** (`config.py:125`) enumerates `{Decision, Research, Execution, Exploration,
  Coding, Learning}`. Note "Decision" is a *task type label*, not a structured decision record
  (no rationale/reversibility/timestamp schema). US10/FR-021 decision records have no home in the
  current schema.
- **`assigned_to`** is `{User, Claude, User + Claude}` (`config.py:131`). There is **no
  agent-as-peer assignee and no checker assignee** — the opposite of the preso board's
  `any / human / agent / checker` filter. Humans-and-agents-as-peers is not modeled.
- **No `decision`, `reversibility`, `autonomy`, `escalation`, `hypothesis`, `experiment`,
  `observation`, `iteration` entities exist.** Grep across `cast-server/cast_server` for those
  terms returns only code-comment "Decision #N" provenance notes and an unrelated error-memory
  "escalated" status. The debug-loop family (hypothesis→experiment→observation) has zero schema
  support.

**ASCII — current data model (the whole story):**

```
Goal (1 fixed phase string)
 └── Task[] (phase ∈ 4 fixed phases; is_spike flag; assigned_to ∈ {User,Claude,both})
       ├── Task[] (subtasks via parent_id)
       └── AgentRun[] (task_id link; parent_run_id → dispatch tree)
                 └── AgentRun[] (children; rework rollups computed at render time)
```

There is no `WorkflowFamily`, no `Decision`, no `Iteration`. The model is goal→task→run. Four
families would each need either a `family` discriminator on `Goal` plus family-specific
stage/artifact tables, or a wholly different (greenfield) model — the prototype fakes this, so it
is unconstrained here.

---

## 2. Existing Implementation — how goals/phases/tasks render *today*

### The goal detail surface (`templates/pages/goal_detail.html`)

This is the closest thing to a "canvas" that exists, and it is identical for every goal:

1. **Header:** title, focus-star, status badge, status-transition buttons (`Accept/Decline`,
   `→ Inactive/Completed`), tags, directory-config form.
2. **Status guidance callouts:** hardcoded copy for `idea` ("Triage this idea") and `completed`.
3. **Five fixed tabs:** `Overview` + one tab per fixed phase. Phase tabs show a phase indicator
   (`✓ completed / ● current / ○ future`) and a `completed/total` task count. **The tab set never
   changes — a bug-fix goal shows "Requirements / Exploration / Plan / Execution" exactly like a
   feature goal.**
4. **Overview tab:** all tasks grouped by phase + a verbose "Add Task" form (title, phase,
   tip, outcome, action, task_type, estimate, energy, assigned_to, recommended_agent).
5. **Phase tabs:** lazy-loaded via HTMX (`hx-get=/api/goals/{slug}/tab/{phase}`,
   `hx-trigger="intersect once"`).
6. **Agent panel:** loaded at bottom via HTMX (`/api/agents/goals/{slug}/recommendations`).
7. Tab switching is client JS (`switchTab()` toggling `.active`, writing `#hash`). No URL-driven
   scenario state, no view transitions, no morph.

### Phase tab content (`fragments/phase_tab_content.html` + `api_goals.py:get_phase_tab`)

- **Tasks first** (primary), then a "Suggest Tasks" form, then an add-task form, then
  **rendered artifacts** in collapsible `<details>` (first one `open`).
- Empty states are hardcoded per phase: e.g. exploration → "Run the explore agent to research
  this space". These are the only "nudges" in the product, and they are static strings, not the
  opinionated nudged-next-step the vision wants.
- **Evidence = markdown.** `api_goals.py:get_phase_tab` reads `PHASE_ARTIFACTS` files, runs them
  through python-`markdown` (extensions: `fenced_code, tables, toc, codehilite`), and injects the
  HTML via the `artifact_content(html)` macro (`macros/markdown_viewer.html`) inside
  `.markdown-body`. **There is no screenshot surface, no chart/data-viz renderer, no test-run
  summary widget, no rendered-HTML-output embed.** Every family's "evidence" is prose-rendered-
  from-a-`.md`-file. (US4/FR-009's "fitted evidence forms" do not exist today.)

### Task rendering (`fragments/task_item.html`)

Genuinely the most feature-rich fragment, and worth lifting *patterns* from:
- Checkbox / in-progress / completed states; inline edit on click.
- Pills: `estimate_size` (with "Split?" warning on L/XL), `phase-badge`, `recommended_agent`
  badge (links to `/agents`), `Interactive` badge.
- **Agent run states inline on the task:** `Running…` (polls every 5s), `Queued`, `Scheduled`;
  run buttons (▶ run now, ⏰ schedule off-peak); `Agent done` / `Agent failed/partial` badges with
  artifact counts; retry + recheck buttons; **`Action needed`** badge when
  `last_run.output.human_action_needed` is true. ← *This is the only place a human-needed signal
  surfaces at the WHAT level today, and it is a tooltip-grade badge, not a first-class escalation
  rail.*
- Subtask list with inline add; subtask progress badge (`n/m`).
- `task_artifacts` render as `artifact-chip` buttons that open an artifact sidebar.

**No `is_spike` treatment on the live task item** — the spike badge only appears on *suggestion*
cards (`task_suggestion_card.html:11`), not on accepted tasks. A spike task, once accepted, is
visually indistinguishable from any other task.

### The execution dispatch tree (`/runs` page + `macros/run_node.html`) — the strong asset

`templates/pages/runs.html` + the recursive `render_run(run, depth)` macro is the one surface
that already does something the vision needs: it renders an **agent dispatch tree** as nested
`.run-group`/`.run-node` rows with:
- status dot, agent name, goal/task breadcrumb, **`↻ rework #N` tag**;
- rollup cells: `N steps` (descendant_count), `⚠ N failed` (failed_descendant_count),
  `⚠ N reworked` (rework_count), duration, cost;
- failure/warning **border tinting** that propagates up the tree (`has-failure`/`has-warning`);
- a **context-usage stacked bar** (system/memory/agents/messages segments vs a 200k limit) in the
  expand detail;
- per-run summary, artifacts list, error, and a **copy-resume command** (`claude --resume …`);
- live polling only on running/pending/rate_limited rows (`run_status_cells.html`, every 3s);
  expand/collapse state persisted in `localStorage`.
- Summary cards at top: cost today, tokens today, dispatcher `slots_used/max_slots`.

This is the maker-checker / dispatch-tree raw material for US3-S2 ("run list → dispatch tree →
maker-checker iteration with rework budget and named exits"). **But it lives on a global `/runs`
page, decoupled from any goal canvas or ticket**, and the only maker-checker signal is "rework"
(an iteration count). There are **no checker comments, no rule codes (M04/S03/R02), no rework
*budget* `X/3`, and no named exits (fix/retry/escalate)** in the live product. The preso mocks
(below) designed all of those — the product has the tree, the preso has the semantics.

### Agent panel (`fragments/agent_panel.html`)

Flat list of recommended agents (name + description) + a "Running" section + last-5 "Recent Runs".
No board, no peer assignees, no marketplace, no resume, no checker pairing. Agents-as-colleagues
(US5/US6) is entirely unbuilt in the live UI.

---

## 3. Gap Analysis — what's missing for per-family canvases & evidence

Prioritized for step 03's question (canvas shape + iteration model + evidence per family).

### Critical (the family thesis has no support today)

1. **No workflow-family concept anywhere.** One hardcoded 4-phase pipeline for all goals
   (`config.py:52`). The "four contrasting families" (US2/FR-006) and "canvas morphs between
   families" (US1-S2/FR-004) have zero structural foothold. *Severity: critical — this is the
   exact failure the goal exists to escape.*
2. **No iteration/loop model.** The debug family's hypothesis→experiment→observation loop and
   "iteration 2/3" history (US2-S1/S2, FR-007) have no schema and no rendering. The closest
   precedent is the `↻ rework #N` tag on `run_node.html` (execution-internal, not a WHAT-level
   iteration history) and the M5 ticket's v1→v2 activity log (preso only). *Severity: critical.*
3. **No fitted evidence surfaces.** Evidence is markdown-rendered prose
   (`api_goals.py:get_phase_tab`). No screenshot gallery, no chart/data-viz, no test-run summary,
   no rendered-HTML-output embed (US4/FR-009). The data-analysis family's "visualized output, not
   prose" (US2-S4) is impossible with the current renderer. *Severity: critical for families 1 &
   4.* (The one real chart in the whole ecosystem is M9's inline-SVG burndown — preso, not product.)
4. **No spike_ref linkage.** `is_spike` is a boolean with no conclusion artifact and no decision
   reference (US2-S3/FR-016). *Severity: critical for the spike family.*

### Medium

5. **No decision records / reversibility / autonomy** (US10/FR-021-023). No `Decision` entity, no
   L1/L2/L3, no escalation rail, no autonomy dial. "Decision" exists only as a task-type label.
6. **Human-needed signal is weak.** Only the `Action needed` tooltip badge on a task
   (`task_item.html:135`); no WHAT-level escalation surface (US3-S3, US5-S4).
7. **Agents are tools, not peers.** `assigned_to ∈ {User, Claude, both}`; no agent/checker
   assignees, no board. Contradicts the `any/human/agent/checker` parity the preso designed.
8. **Nudges are static empty-state strings** (`phase_tab_content.html:29`), not an opinionated,
   state-aware "primary next action" (US1-S4/FR-003).

### Low

9. **Tab state is hash + JS**, no URL-as-scenario-state and no view-transition machinery for the
   canvas-morph demo (Directional Ideas). Greenfield prototype, so this is a build-recipe note,
   not a constraint.
10. **Markdown rendering is server-side python-markdown**; fine for prose, but not an interactive
    artifact substrate.

---

## 4. Patterns & Conventions

### Current Diecast UI

- **Stack:** FastAPI + Jinja2 templates + **HTMX** (`static/htmx.min.js`) + a single hand-rolled
  `static/style.css`. No SPA, no React/Vue, no build step. EasyMDE is the only vendored JS
  (markdown editor). SQLite via raw `db/connection.py`.
- **Server-rendered fragments + HTMX swaps** are the universal interaction pattern: `hx-get/post/
  put` with `hx-target`/`hx-swap="outerHTML"`, lazy load on `intersect once`, polling via
  `hx-trigger="every Ns"`, out-of-band swaps (`hx-swap-oob`). Any "morph" today would be an HTMX
  fragment swap, not a client-state transition.
- **Templates organized** as `pages/` (full), `fragments/` (HTMX-swappable), `macros/` (reusable
  render fns incl. the recursive `run_node`), `partials/`. Naming is consistent kebab-case files.
- **Config-as-constants:** statuses, phases, task types, energy, assignees are all module-level
  sets/lists in `config.py` — easy to read, but they encode the single-pipeline assumption.
- **Phase state computed in `pages.py`** (`PHASES.index(phase)` comparisons → completed/current/
  future). The breadcrumb (`fragments/phase_breadcrumb.html`) is a linear `→`-joined stepper —
  inherently a single linear pipeline visual, not a branching/looping shape.

### Preso v2/v3 design conventions (the reusable craft)

- **Linear-style PM shell** is the locked archetype for the board arc: sidebar + board + columns +
  cards, `Assignee type: any / human / agent / checker` filter chip (4 exact values, `checker`
  load-bearing). Framing: **"Diecast publishes INTO your PM tool. It does not replace it."**
- **Canonical fake-data spine** (reuse verbatim across the prototype per FR-018): ticket
  `CAST-412` "Create Invoice entity + CRUD stack"; agents `crud-orchestrator`, `entity-creation`,
  `compliance-checker`; rule codes `M04 / S03 / R02`; `PR #2341`; rework budget `1/3`;
  reversibility `L1/L2/L3`; human handle `@you`; spike ticket `CAST-201` + `CAST-201-spike`;
  escalation ticket `CAST-417`.
- **`_mocks.css` design tokens:** `--bg #F5F4F0`, `--text #1A1A28`, `--muted #4A4860`,
  `--accent #D6235C` (no blue/purple). Reusable classes: `.pm-row-head`, `.pm-avatar.agent`,
  `.pm-chip` (`.status-spike/.status-progress/.status-done`), `.act-row/.act-body/.act-time`
  (activity log), `.linked-item/.li-id`, `.ticket-main/.ticket-view/.t-head/.t-title/.t-desc`,
  `.dec-box` (decision frontmatter), `.pm-integration` strip, `.mock-annotation`. These are the
  exact component primitives a family canvas would compose from.
- **Brand rules:** product name `Diecast`; modules stay lowercase `cast-*`; "Layer" not "Tier";
  no em dashes; no GPT-isms. (FR-018.)

---

## 5. Entry Points & Flow

### Current flow: open a goal → see the universal pipeline

```
GET /goals/{slug}  (routes/pages.py:goal_detail)
  → goal_service.get_goal(slug)
  → compute phase_states for the 4 fixed PHASES (completed/current/future)
  → collect tasks_by_phase, tab_counts
  → render pages/goal_detail.html  (5 fixed tabs)
        ├─ Overview tab: task_list.html (all phases)
        └─ Phase tab (lazy):
             GET /api/goals/{slug}/tab/{phase}  (routes/api_goals.py:get_phase_tab)
               → task_service.get_tasks_for_goal(slug, phase)
               → attach active_run / last_run per task (+ auto-recheck timed-out runs)
               → read PHASE_ARTIFACTS[phase] files → python-markdown → HTML
               → render fragments/phase_tab_content.html  (tasks → artifacts<details>)
```

Every goal traverses this identical path. The phase set, the tab labels, the artifact patterns,
and the evidence renderer are all phase-keyed off the same 4 constants — there is no branch on
goal type. **This is the single linear pipeline the four-family vision must replace.**

### Execution drill-in flow (the asset)

```
GET /runs  (routes/pages.py)
  → agent_service builds a run tree (parent_run_id → children) with computed rollups
    (descendant_count, failed_descendant_count, rework_count, ctx_class, wall_duration)
  → macros/run_node.html render_run() recurses depth-first
       ├─ row-1: status dot, agent, crumbs, ↻ rework #N, caret
       ├─ row-2 (run_status_cells): pill, ctx-pill, N steps, ⚠N failed, ⚠N reworked, duration, cost, Resume
       ├─ .thread → children (recursion) with propagated failure/warning tint
       └─ .detail (expand): summary, skills, error, artifacts, context-usage bar, cancel/recheck
  → live rows poll /api/agents/runs/{id}/status_cells every 3s
```

### Preso board arc flow (designed, rendered as static mocks, not wired to product)

```
M4 board (PM shell, assignee filter, YOU row + AGENT row, 11 agent tickets across
   Backlog / In Progress / Checker Review / Done)
  → M5 one ticket CAST-412: activity log (orchestrator → entity-creation v1 →
       compliance-checker posts M04/S03/R02 → v2 → approved → PR #2341), aside =
       assignee + checker + rework budget 1/3 + linked PR
  → M7 decision artifact .dec-box (id, reversibility=L2, escalation, spike_ref, consequences,
       revisit_when) attached to ticket CAST-201
  → M8 escalation CAST-417 needs_work + escalated·L3 → checker routes to @you with 3
       pre-framed options; sidebar lists downstream consumers + escalation-policy link
  (+ M6 spike branching CAST-201/CAST-201-spike; + M9 activity rollup with SVG burndown)
```

---

## 6. Per-family terrain mapping (the heart of step 03)

What the current code offers vs. what the preso already designed, per locked family.

### Family 1 — New feature / initiative (richest backbone)

- **Current terrain:** This is the *only* family the current UI is shaped for — it literally
  *is* the `requirements → exploration → plan → execution` pipeline. The 5-tab goal detail,
  phase breadcrumb stepper, task lists, and `/runs` dispatch tree all assume this arc. So the
  feature family is the one place where current chrome is reusable as a *baseline*.
- **Preso assets:** the full board→ticket→decision→escalation arc (M4/M5/M7/M8) is a feature
  ticket's execution-and-evidence story.
- **Evidence today:** markdown artifacts only. Vision wants screenshots + test-run summary
  (US4-S1) — **not present**; must be invented for the prototype.

### Family 2 — Bug-fix / debug loop (maximally different shape)

- **Current terrain:** *nothing family-specific.* A bug goal renders as the same 4-phase
  pipeline. The only loop-shaped precedent in the entire product is the **`↻ rework #N` tag +
  failure-tint propagation** on `run_node.html` — an execution-internal retry counter, not a
  hypothesis→experiment→observation model.
- **Preso assets:** **M5 ticket-iterations is the closest design** — a v1→v2 iteration activity
  log with a paired checker and a visible `rework budget 1/3`. That is structurally a
  maker-checker loop and a strong seed for the debug-loop's iteration history. The
  hypothesis/experiment/observation vocabulary itself is *not* in any mock — it must be authored.
- **Iteration history:** M5's timestamped activity log + the run-tree rework rollups are the two
  precedents for "iteration 2/3" rendering (US2-S2).

### Family 3 — Spike / quick-conclusion

- **Current terrain:** `is_spike` boolean exists (schema + suggestion badge) but has **no canvas,
  no conclusion artifact, no spike_ref**. A spike is just a flagged task.
- **Preso assets:** **M6-A26-spike-branching is essentially a ready-made spike canvas.** It is a
  two-panel layout: main ticket `CAST-201` (in progress, L2 decision) beside `CAST-201-spike`
  (`pm-chip status-spike`, closed · learned) rendered with a **dashed border + muted background
  to signal isolation**; spike artifacts "stay here" (scratchpad), a **learned-note that
  explicitly "attaches to CAST-201"**, and a timeline showing branch → close → decision-agent
  writes `decisions/2026-04-15-postgres-only.md`. This directly models the time-boxed-question →
  conclusion → feeds-a-decision (`spike_ref`) shape from US2-S3/FR-016. M7 then shows the
  resulting decision artifact with a `spike_ref` field.
- **Evidence:** the conclusion is the "learned-note" + the linked decision file — a fitted,
  non-prose evidence form already designed.

### Family 4 — Data analysis / research

- **Current terrain:** research output is markdown prose rendered via python-markdown
  (`api_goals.py`). `task_type=Research` exists as a label. **No visualization surface at all.**
  The data-analysis "visualized output, not prose-only" (US2-S4) is the single hardest gap.
- **Preso assets:** **M9-A29-activity-rollup is the only real data-viz in the ecosystem** — a
  two-column top with an **inline-SVG sprint burndown (actual-vs-ideal, Thu escalation marker)**
  plus a numbers panel, and three roll-up columns (Shipped per-agent counts, Checker rule
  frequencies M04/S03/R02, Blocked/escalated). It proves the design system can carry a chart, and
  is a seed for the data-analysis family's chart/table evidence treatment. (It is a *project
  metrics* rollup, not a generic data-analysis result, so the family canvas needs new authoring;
  M9 supplies the visual idiom.)

### Cross-family summary table

| Family | Current canvas | Current iteration model | Current evidence | Strongest preso seed |
|--------|----------------|-------------------------|------------------|----------------------|
| Feature | the 4-phase pipeline (only one that fits) | task checkboxes + run tree | markdown prose | M4/M5/M7/M8 board arc |
| Debug loop | none (same pipeline) | `↻ rework #N` (exec-internal) | markdown prose | **M5** v1→v2 + rework budget |
| Spike | `is_spike` badge only | none | markdown prose | **M6** branch+learned-note+decision file |
| Data/research | none (same pipeline) | none | **markdown prose only** | **M9** inline-SVG burndown + rollups |

---

## 7. Tests, Config & Dependencies

- **Tests:** `cast-server` tests live under `/data/workspace/diecast/tests/`. There are no UI/
  canvas rendering tests relevant to families (the UI is server-rendered HTML + HTMX; coverage is
  on services/routes). Not load-bearing for a greenfield prototype. No test seam constrains the
  family design.
- **Runtime deps (current UI):** FastAPI, Jinja2, HTMX (vendored), python-`markdown` (with
  `fenced_code/tables/toc/codehilite`), EasyMDE (vendored), SQLite. `pyproject.toml` at repo root.
  Notably **no charting lib, no client framework, no view-transition tooling** — the data-viz
  evidence gap is also a dependency gap today.
- **Preso assets are pure static HTML/CSS** (`_mocks.css` + per-mock `<main>` blocks) — zero deps,
  directly liftable into a static prototype. Rendered decks exist at
  `presentation_v2/presentation/review.html` (777 KB) and `presentation_v3/presentation/
  index.html` (358 KB) if a fuller visual reference is wanted.
- **Constraint for the prototype:** FR-001 mandates self-contained browser-openable HTML/JS/CSS,
  no backend. The current cast-server stack (FastAPI/HTMX/SQLite) is therefore *not* the build
  substrate — the prototype is greenfield static. The current UI informs (tab/phase/task idioms,
  the run-tree pattern) but does not bind (FR-020).

---

## Key Takeaways (opinionated, architectural)

1. **The current UI is the antithesis of the family thesis, by construction.** Four hardcoded
   phases (`config.py:52`) drive the data model, routing, and templates in lockstep. There is no
   `workflow_family` field, no per-family stage model, and the phase breadcrumb is an inherently
   *linear* stepper. "One shape fits all goals" is not a bug to fix — it is the architecture. The
   prototype should treat today's goal-detail page as the explicit "before" the four contrasting
   canvases are defined *against*, not a base to extend.

2. **Evidence is the single biggest gap, and it is total.** Every artifact, every family, is
   `markdown → python-markdown → <div class="markdown-body">`. There is no screenshot surface, no
   chart, no test-run summary, no rendered-HTML embed. The *only* genuine data-visualization in
   either codebase is M9's inline-SVG burndown (preso). US4/FR-009's "fitted evidence forms" must
   be designed from scratch for three of four families; M9 supplies the visual idiom and proves the
   palette can carry a chart.

3. **The `/runs` dispatch tree is the one asset worth preserving and re-homing.**
   `macros/run_node.html` already renders a recursive agent tree with rework tags, failure-tint
   propagation, rollups, context-usage bars, cost, and resume commands — most of US3-S2's
   "execution drill-in." Its weaknesses are exactly the gaps the preso filled: it shows *rework
   count* but no checker comments, no rule codes, no rework *budget X/3*, no named exits. **Marry
   the run-tree's live tree to the preso M5 ticket's maker-checker semantics** and you have the
   debug-loop / execution surface. Today the tree is orphaned on a global page, detached from any
   goal or ticket.

4. **The preso v2/v3 work already designed three of the four family canvases — they just were
   never wired to the product.** M6 (spike branching with isolation styling + learned-note +
   decision file) is a near-complete spike-family canvas; M5 (v1→v2 iterations + rework budget) is
   a debug-loop seed; M9 (burndown + rollups) is the data/evidence idiom; M4/M5/M7/M8 are the
   feature family's execution arc. These are static HTML mocks with a clean reusable token set
   (`_mocks.css`) and a locked canonical fake-data spine (CAST-412, M04/S03/R02, @you, L1/L2/L3,
   rework 1/3). **For step 03, the spike and debug families especially are reuse-not-reinvent.**

5. **`is_spike` is the only family-aware bit in the schema, and it proves the pattern is cheap to
   model but expensive to *render*.** The flag flows end-to-end (model → service → DB → suggestion
   card) yet produces only a badge, with no spike_ref, no conclusion, no canvas. The lesson for the
   prototype: a `family` discriminator is trivial fake data; the real work is the four distinct
   *canvases, iteration models, and evidence treatments* — which is precisely what this step must
   specify and what the live product has never had.

6. **Iteration history has exactly two precedents, both partial.** The run-tree's `↻ rework #N`
   (execution-internal) and M5's timestamped v1→v2 activity log (preso, static). Neither is a
   WHAT-level "iteration 2/3" history for a debug loop. The hypothesis→experiment→observation
   vocabulary appears *nowhere* in either codebase and must be authored fresh.

7. **Agents-as-peers and decisions/autonomy are unbuilt in the product but fully designed in the
   preso.** `assigned_to ∈ {User, Claude, both}` vs the preso's `any/human/agent/checker`; no
   `Decision` entity vs M7's `.dec-box` with reversibility/escalation/spike_ref/consequences; the
   `Action needed` task badge vs M8's L3-escalation-to-@you-with-3-options rail. For step 03 these
   matter because the spike family's conclusion *feeds a decision* (spike_ref) — that linkage is
   designed (M6→M7) but has no product home.

## Key Files

**Current Diecast UI (terrain to escape / patterns to lift):**
- `cast-server/cast_server/config.py:52` — `PHASES` + `PHASE_ARTIFACTS`: the hardcoded single
  pipeline. The crux of the "one shape fits all" constraint.
- `cast-server/cast_server/templates/pages/goal_detail.html` — the universal 5-tab goal canvas.
- `cast-server/cast_server/templates/fragments/phase_tab_content.html` — tasks + markdown-only
  evidence; static empty-state "nudges".
- `cast-server/cast_server/routes/api_goals.py` (`get_phase_tab`, ~l.262) — the markdown→HTML
  evidence renderer (no fitted forms).
- `cast-server/cast_server/templates/macros/run_node.html` — **the strong asset:** recursive
  dispatch tree with rework tags + rollups + ctx bars.
- `cast-server/cast_server/templates/fragments/run_status_cells.html` — rollup pills (steps/
  failed/reworked), live polling.
- `cast-server/cast_server/templates/fragments/task_item.html` — richest live fragment; inline
  run states + the lone `Action needed` human-needed signal.
- `cast-server/cast_server/models/task_v2.py` — `is_spike` + `task_type` + `estimate_size`;
  the only family-ish flag.
- `cast-server/cast_server/models/goal.py` — Goal has a single `phase`, no `family`.
- `cast-server/cast_server/templates/fragments/phase_breadcrumb.html` — the linear `→` stepper
  (wrong shape for loops/branches).

**Preso v2/v3 designs that already solve step-03 surfaces (reuse-not-reinvent):**
- `…/thesis_microsite/mocks/M6-A26-spike-branching.html` — **spike-family canvas** (isolation
  styling, learned-note, decision file).
- `…/thesis_microsite/mocks/M5-A25-ticket-iterations.html` — **debug-loop seed** (v1→v2 activity
  log, rework budget 1/3, checker comments M04/S03/R02).
- `…/thesis_microsite/mocks/M9-A29-activity-rollup.html` — **data-viz idiom** (inline-SVG
  burndown + per-agent/rule rollups) — the only real chart in either codebase.
- `…/thesis_microsite/mocks/M4-A24-board-overview.html` — board shell + assignee filter
  (`any/human/agent/checker`) + YOU/AGENT rows.
- `…/thesis_microsite/mocks/M7-A27-decision-attached.html` — `.dec-box` decision frontmatter
  (reversibility/escalation/spike_ref/consequences).
- `…/thesis_microsite/mocks/M8-A28-escalation-human.html` — L3 escalation → @you, 3 pre-framed
  options.
- `…/thesis_microsite/mocks/_mocks.css` — reusable PM-shell/card/chip/ticket-aside/burndown
  classes + locked palette tokens.
- `…/thesis_microsite/mocks/MOCKS_INDEX.md` — index + per-mock verification notes (component map).
- `…/presentation_v2/what/a08-board-view.md` … `a11-escalation.md` — authoritative WHAT specs
  (canonical data spine: CAST-412, agents, rule codes, PR #2341, rework 1/3, L1/L2/L3, @you).
- `…/presentation_v3/what/s8a-board-view.md`, `A-v3-chain.md`, `A-v3-dash.md` — v3 reuse pointers
  + brand rules (Diecast/Layer/lowercase cast-*) + the 8-agent Layer-2 chain.
- `…/presentation_v3/presentation/index.html` — full rendered v3 deck (visual reference).

---

## Scope notes / honesty

- This is a **terrain map**, not a recommendation. Which assets to lift, which family stage models
  to author, and the exact evidence treatments are the playbook's job (Step 03 success criteria:
  a per-family canvas blueprint + named evidence treatment).
- The "current UI" findings are from the live `cast-server` templates/models/routes. The "preso
  already solved" findings lean on the WHAT docs and `MOCKS_INDEX.md` structural notes plus a
  structural grep of M6; I did not deep-read every mock's full HTML (reference-only per the preso's
  own Locked Decision #11, and unnecessary for a terrain map). If the playbook wants pixel-level
  lift, the mock HTML + `_mocks.css` are the files to open.
- No code-review-graph MCP was available (graph not built); findings are Glob/Grep/Read-derived.
