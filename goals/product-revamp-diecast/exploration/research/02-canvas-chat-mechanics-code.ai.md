# Code Exploration: Canvas + Chat Mechanics (Terrain Map)

**Goal context:** Product Revamp — Diecast Vision Prototype. Build a clickable HTML vision
prototype whose core thesis is a **canvas-primary, chat-steered** workspace: a WHAT-first
adaptive canvas that a persistent chat rail can visibly *morph* between workflow families,
with promotable chat artifacts. Plus the three-access-tiers positioning (terminal / chat /
canvas over one skill-agent substrate, FR-017).
**Exploration step:** 02 — How should an opinionated canvas + chat steering actually behave?
**Codebase:** /data/workspace/diecast (the live cast-server UI + agent substrate)
**Date:** 2026-06-11
**Framing reminder (locked):** VISION-FIRST. This is a *terrain map only*. What exists is
context, never a constraint (FR-020 says the design is explicitly NOT bound to today's UI).
Where today's code is useless to the vision, that is called out plainly.

---

## TL;DR for the synthesizer

- The current UI is a **server-rendered FastAPI + Jinja2 + HTMX** app (no SPA, no client
  framework, no build step). 7 page surfaces, ~691 lines of page templates, a 4,156-line
  hand-rolled `style.css` with a real design-token system. Interactions are
  `hx-get`/`hx-post` swaps of HTML fragments.
- **There is no canvas and no chat rail today.** The product is a **tab-and-list CRUD tool**:
  Dashboard (goal list) → Goal Detail (5 tabs: Overview + 4 phase tabs) → Runs (dispatch
  tree) → Agents (catalog grid) → Focus / Scratchpad. The morph/nudge/promote/drill-in
  mechanics the vision needs **do not exist in any form**. This is greenfield.
- The **one genuinely strong, directly-reusable asset** is the **execution drill-in** — the
  recursive `run_node.html` macro renders the agent dispatch tree with maker-checker rework
  tags, per-run context-usage bars, skill chips, and artifacts. That *is* US3's "execution
  tab" already built, and it is the best existing proof of the "HOW behind the WHAT" idea.
- **FR-017 is real and provable in code.** The same `agents/cast-*/cast-*.md` file is the
  single substrate for all three tiers: `bin/generate-skills` materializes it into
  `~/.claude/skills/cast-*/SKILL.md` (terminal slash-command tier), and the server dispatches
  it by driving a real `claude` CLI in tmux that reads a `.agent-{run_id}.prompt` file (canvas
  tier). The "same artifact lands either way" claim is literally true: both paths produce the
  same `.agent-run_{id}.output.json` contract-v2 envelope. The **chat tier is the only one of
  the three that has no surface today.**
- The current visual identity is a warm "workshop" aesthetic (cream `#F5F4F0`, crimson
  `#D6235C`, IBM Plex Mono headings, DM Sans body, Caveat hand-accent, 5px grid). Competent
  but utilitarian; FR-020 frees the prototype from it.

---

## 1. Data Model & Schema

The prototype needs **no backend** (FR-001), so the live schema is terrain for *what concepts
already exist* and *what vocabulary is canonical*, not a thing to reuse. The conceptual model
the UI renders today:

| Concept | Where it lives | Shape relevant to canvas/chat |
|---------|----------------|-------------------------------|
| **Goal** | `goals/<slug>/goal.yaml`, surfaced via `goal_service` | `title`, `slug`, `status` (idea→accepted→…→completed/declined), `phase`, `tags_list`, `in_focus`, `external_project_dir`. Goals are file-backed (a YAML per dir), not a single DB. |
| **Phase** | Fixed enum rendered as tabs | The 4 phases are **hardcoded** as `requirements / exploration / planning / execution` (see Gap Analysis — this is the single biggest structural obstacle to the vision's *adaptive* canvas). |
| **Task** | DB + `task_service` | `phase`, `status`, `task_type` (Decision/Research/Execution/Exploration/Coding/Learning), `outcome`, `action`, `assigned_to` (Me / Claude / Me + Claude), `recommended_agent`, `energy`, `estimated_time`. Note `assigned_to` already encodes a **human-or-agent assignee** — the seed of US5's peer-assignee board. |
| **Agent run** | `agent_runs` table + canonical file | The execution record. Carries `status`, `parent_run_id` (tree), `session_id`, `skills_used`, `context_usage`, `rework_count`/`rework_index`/`is_rework`, `artifacts`, `output.summary`, `failed_descendant_count`. See `agent_service.py`. |
| **Invocation source** | `input_params.source` discriminator | `services/_invocation_sources.py` defines `USER_PROMPT = "user-prompt"` and `SUBAGENT_START = "subagent-start"`; server-dispatched runs are a third path. **These three sources are the data-model embodiment of FR-017's three tiers** (see Angle 5). |
| **Decision** | **Does not exist.** | No decision entity, table, or template anywhere. US10/FR-021-023 (decisions as first-class records with reversibility L1/L2/L3) is **net-new** — `task_type="Decision"` is the closest existing hook and it is just a label on a task. |
| **Workflow family** | **Does not exist.** | No notion of "feature vs debug vs spike vs data-analysis" canvas shapes. The 4 hardcoded phases are the *only* workflow model. |

**Canonical vocabulary already in code** (reuse per FR-018): `cast-*` lowercase module names
(60 agents under `agents/`), maker-checker rework framing (`rework_count`, `↻ rework #N` tag in
`run_node.html:21`), context-usage breakdown (system/memory/agents/messages), `parent_run_id`
dispatch trees. The vision's "13 sub-agents", "rework budget 1/3", "maker-checker" language all
have real referents here.

```
Goal (goal.yaml, file-backed)
 ├─ status: idea→accepted→…→completed     (linear lifecycle, no branching)
 ├─ phase: ONE OF [requirements, exploration, planning, execution]   ← hardcoded enum
 ├─ in_focus: bool                         → Focus page
 └─ Tasks (DB)
      ├─ phase (same 4-enum), status, task_type, assigned_to (Me|Claude|Me+Claude)
      └─ recommended_agent ──────────────► Agent (agents/cast-*/)
                                              └─ AgentRun (agent_runs table + file)
                                                   ├─ parent_run_id ──► recursive tree
                                                   ├─ skills_used[], context_usage{}
                                                   ├─ rework_count, is_rework
                                                   └─ output: {summary, artifacts[]}
```

The schema is **linear and phase-locked**. The vision is **adaptive and workflow-shaped**.
That mismatch is the headline finding of this map.

---

## 2. Existing Implementation — the 7 UI surfaces

Server-rendered pages, each a Jinja template extending `base.html`. Route → page map from
`routes/pages.py`:

| Route | Template | LOC | What it is today | Relevance to canvas/chat vision |
|-------|----------|-----|------------------|----------------------------------|
| `/` → `/dashboard` | `pages/dashboard.html` | 97 | Two-column: goal list (Active/Inactive/Completed tabs) + sidebar (scratchpad, goal suggestions). Create-goal inline form. | The *entry* surface. Vision wants a scenario-chooser ("Follow a feature / Chase a bug / Run a spike / Answer a data question / Hire an agent"). Today it is a flat goal list — no workflow framing. |
| `/goals/{slug}` | `pages/goal_detail.html` | 237 | **The closest thing to a "canvas" today** — but it is a **tab container**, not a canvas. 5 fixed tabs: Overview + one per phase. Phase tabs lazy-load via HTMX `intersect`. Header has status badge, focus star, status-transition buttons, status guidance callouts. Bottom: agent panel (HTMX-loaded). | This is what the WHAT-first canvas *replaces*. The tabs ARE the phase-locked model. There is **no "nudged next step"** beyond status-transition buttons; **no WHAT-above-the-fold/HOW-drill-in split** (US3) — tasks of all types are mixed in lists. |
| `/runs` | `pages/runs.html` | 146 | **The execution surface.** Summary cards (cost/tokens/dispatcher slots), status filters, and a threaded timeline of run trees via `runs_list.html` → recursive `macros/run_node.html`. | **The single strongest reusable asset for US3 (execution drill-in) and US5 (maker-checker activity).** See Angle 5. |
| `/agents` | `pages/agents.html` | 88 | Catalog grid of 60 registered agents: name, type badge, description, tags, trigger phrases, run-count badge, collapsible I/O details. Client-side filter buttons by type. | Raw material for US6 marketplace / US8 agent-ops — but it is a **flat admin catalog**, exactly the "looks like admin CRUD" failure mode Step 4 warns against. No resumes, credibility stats, maker-checker pairing, or hire flow. |
| `/focus` | `pages/focus.html` | 53 | In-focus goals with their active tasks grouped by phase. | A "what's hot" view. No vision analog; minor. |
| `/scratchpad` | `pages/scratchpad.html` | 46 | Freeform notes. | Tangential. |
| `/about` | `pages/about.html` | 24 | Static positioning page. | Maps to the "setup/positioning backdrop" (Out of Scope as a flow, but FR-017's positioning claim could live here). |

**Fragment inventory** (`templates/fragments/`, 23 files) — the HTMX swap targets. Notable for
the vision: `agent_panel.html` (per-goal agent list + running/recent runs, self-polls every
5s), `phase_breadcrumb.html` + `phase_tab_content.html` (the phase machinery), `status_badge.html`,
`task_suggestion_card.html` / `suggestion_card.html` (AI-suggested tasks/goals — a latent
"nudge" primitive), `artifact_editor.html` + `artifact_sidebar.html` (a slide-in editor — the
nearest existing thing to a "promote artifact onto canvas" surface).

**Macros** (`templates/macros/`): `run_node.html` (the recursive dispatch-tree renderer),
`markdown_viewer.html`, `components.html`. **Partials**: `run_skills_chips.html` (inline skill
chips on a run), `run_skills_detail.html`.

**Code quality:** clean and consistent. HTMX attributes are tidy, fragments are small and
single-purpose, the recursive run macro is genuinely elegant. This is *well-built for what it
is* — a CRUD dashboard. It is simply the wrong *shape* for an adaptive canvas.

---

## 3. Gap Analysis — what the vision needs that does NOT exist

Severity is relative to the vision (FR-003/004/005), not to today's product working correctly.

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| G1 | **No canvas.** The "primary surface" is a tab container (`goal_detail.html` tabs), not a spatial/stateful canvas. WHAT-first layout, nudged next step, evidence-as-first-class — none exist. | **Critical** | `goal_detail.html:92-209` is `.tab-container` with `switchTab()` JS. |
| G2 | **No chat rail at all.** Grep for `chat` across templates/routes/CSS returns only the word "Conversation" as a context-bar *legend label* (`runs.html:59`). The core thesis interaction (FR-004 — chat that morphs the canvas) has zero substrate. | **Critical** | `grep -rn chat` → only `context-bar-conversation` legend. |
| G3 | **Phase model is hardcoded and linear.** The 4 phases (`requirements/exploration/planning/execution`) are baked into the tab loop and the task `phase` enum. The vision's whole point is **per-family adaptive shapes** (debug = hypothesis→experiment→observation; spike = timebox→conclusion). The current model cannot express them. | **Critical** | `goal_detail.html:98-115` `{% for phase in phases %}`; phase passed from route. |
| G4 | **No "morph" mechanism.** Tab switching is instant `classList` toggling (`switchTab()`, `goal_detail.html:221-227`) — no transitions, no view-transition API, no animated reshape. FR-004's "visibly morph" demand has no precedent in the codebase. | **High** | No CSS `view-transition`, no FLIP, no keyframe morphs in `style.css`. |
| G5 | **No promote/pin primitive.** `artifact_sidebar.html` is the nearest analog (a slide-in artifact viewer toggled by `openArtifactSidebar()` in `base.html:137`), but nothing promotes a chat-generated object onto a goal as a persistent pinned card (FR-005). | **High** | `base.html:137-144` only opens/closes a sidebar container. |
| G6 | **No decision records.** US10/FR-021-023 entirely net-new. No entity, no template, no autonomy-dial, no L1/L2/L3 reversibility, no clarify-vs-proceed gate. `task_type="Decision"` is a label only. | **High** | No `decision` anywhere in templates/services. |
| G7 | **No WHAT/HOW split.** US3 wants WHAT above the fold, HOW behind a tab. Today every phase tab mixes outcome, tasks, and execution detail in flat lists; the rich execution tree lives on a *separate page* (`/runs`), not as a drill-in *within* the goal. | **Medium** | `goal_detail.html` agent panel is a thin list (`agent_panel.html`); the real tree is `/runs`. |
| G8 | **Agents surface is admin-CRUD, not colleagues.** No resume, no credibility stats, no hire/assess/onboard flow, no maker-checker pairing in-card (US6/FR-011). | **Medium** | `agents.html` is a filterable grid of name+desc+tags. |
| G9 | **No evidence-rich output surfaces.** US4/FR-009 wants screenshots / charts / rendered HTML / test summaries as first-class. Today a run's `output.summary` is plain text and `artifacts` are a bulleted list of paths (`run_node.html:48-61`). | **Medium** | `run_node.html:38-61` renders summary text + path list only. |
| G10 | **Client-side state is minimal.** Only `localStorage` for run-expand state (`runs.html:81`) and tab hash (`goal_detail.html:229`). No scenario-script engine, no state-as-URL/JSON machinery for scripted demo moments (Step 6 build concern). | Low (for this step) | `localStorage.getItem('runs:expanded:'+id)`. |

**The honest verdict:** of the seven vision threads touching this step, **the canvas and the
chat rail — the two that matter most — have no code to build on.** The codebase contributes
*vocabulary, the execution-tree component, and the FR-017 substrate proof*, and nothing else
structural. This is a feature, not a bug, of the VISION-FIRST framing: it confirms the
prototype should be designed greenfield.

---

## 4. Patterns & Conventions

What the current stack does, so the prototype can *deliberately choose* whether to echo or
abandon each (FR-020 permits abandoning all of it).

- **Architecture:** server-rendered MVCS. Routes (`routes/*.py`) → services
  (`services/*.py`) → file/DB. Templates render server-side; **HTMX** does partial swaps
  (`hx-get`/`hx-post` + `hx-target` + `hx-swap`). **No JS framework, no bundler, no npm.**
  Vendored deps only: `htmx.min.js`, `easymde` (markdown editor). This is a **zero-build**
  philosophy — directly aligned with the prototype's "self-contained, browser-openable HTML"
  deliverable (FR-001), even though the prototype won't use a server.
- **Interaction idiom:** every dynamic action is an HTMX request returning an HTML fragment.
  E.g. dashboard tabs: `hx-get="/api/goals/dashboard?tab=active"` `hx-target="#dashboard-goals"`
  (`dashboard.html:38-46`). Polling is declarative: `hx-trigger="every 5s"` on running runs
  (`agent_panel.html:30`). **Lesson for the prototype:** the canvas-morph can be faked the same
  cheap way — swap a panel's innerHTML — but the *vision* wants a visible transition, which
  HTMX alone does not give (Gap G4). The directional idea in the spec (CSS-transitioned panel
  swaps keyed to scripted chat steps) is the right call and has no incumbent to fight.
- **Design tokens** (`style.css:1-50`, a real `:root` system):
  - Color: `--color-bg:#F5F4F0` (warm cream), `--color-text:#1A1A28`, `--color-accent:#D6235C`
    (crimson), surface `#ECEAE4`. Semantic: success `#2D7D4F`, warning `#B5821A`, danger
    `#B22439`, info `#3B5BB0`, focus `#6B47B0`.
  - Type: `--font-heading: 'IBM Plex Mono'` (monospace headings — a strong, opinionated
    choice), `--font-body: 'DM Sans'`, `--font-display-accent: 'Caveat'` (handwriting accent).
  - Geometry: `--grid-size:5px` with a faint grid texture (`--grid-color`), radii 4/8/12px,
    `--sidebar-width:240px`.
  - This is a coherent **"warm workshop / blueprint"** identity. It is competent but reads
    utilitarian-dev-tool, not the Linear-class craft Step 1 is chasing. **FR-020/Step 1 free
    the prototype to propose a new identity**; this is the baseline to beat, not adopt.
- **Navigation chrome:** fixed left sidebar (`base.html:16-45`) with 5 inline-SVG icon links
  (Dashboard / Scratchpad / Focus / Runs / Agents), `active_page` class toggling. The vision's
  "continuous chrome and canonical vocabulary across the board→ticket→decision→escalation arc"
  (FR-010) has a *consistency* precedent here, but the IA itself (5 flat nav items) does not
  match a workflow-family-centric product.
- **Toast/feedback:** shared `showToast()` + `copyToClipboard()` helpers in `base.html:56-127`;
  HTMX error events surface as toasts. A polished micro-interaction layer worth echoing.
- **Naming:** kebab-case `cast-*` everywhere; templates organized `pages/` vs `fragments/` vs
  `macros/` vs `partials/`. Clean.

---

## 5. Entry Points & Flow — the FR-017 substrate (the headline)

This is the part of the map that *most* serves the goal, because FR-017 (terminal/chat/canvas
over one substrate) is a **positioning claim that the code can prove is true.**

### 5a. The one substrate: an agent `.md` file

An agent is a directory under `agents/cast-*/`:
- `cast-code-explorer.md` — the definition, with YAML frontmatter (`name`, `model`,
  `description` + trigger phrases, `memory`, `effort`) followed by the full system prompt
  (`agents/cast-code-explorer/cast-code-explorer.md:1-12`).
- `config.yaml` — runtime knobs (`model`, `timeout_minutes`, `context_mode`, `proactive`).
- `README.md`, `tests/`.

`bin/generate-skills` **materializes that same `.md`** into `~/.claude/skills/cast-*/SKILL.md`
(`bin/generate-skills:6-12, 40-46`). So the agent definition and the slash-command skill are
**literally the same source file**. That is the substrate. Hence every generated skill carries
`<!-- Generated by bin/generate-skills — do not edit -->`.

### 5b. Three access tiers, all hitting that substrate

```
                         ┌──────────────────────────────────────────┐
                         │   agents/cast-*/cast-*.md  (ONE source)   │
                         └───────────────┬──────────────────────────┘
                  bin/generate-skills    │            (read directly at dispatch)
                  materializes ↓          │                       ↓
   TIER 1 TERMINAL            TIER 3 CHAT (MISSING)        TIER 2 CANVAS/SERVER
   human types in `claude`   no surface today             POST /api/agents/{name}/trigger
   /cast-code-explorer  ──►  (the core gap)         ──►   agent_service.trigger_agent()
   loads ~/.claude/skills/                                 → _launch_agent():
     cast-*/SKILL.md                                         tmux.create_session(
        │                                                      "claude --dangerously-skip-
        │                                                       permissions --model … --name")
        │                                                     tmux.open_terminal()
        │                                                     write .agent-{id}.prompt
        │                                                     send_keys("Read the file … and
        │                                                       follow its instructions exactly")
        ▼                                                         ▼
   ───────────────  BOTH paths produce the SAME envelope  ───────────────
            .agent-run_{id}.output.json   (contract_version "2")
            { status, summary, artifacts[], next_steps, … }
```

**Tier 2 (canvas/server) dispatch path, concretely** (`agent_service.py`):
1. `POST /api/agents/{name}/trigger` (`api_agents.py:88`) validates an optional
   `DelegationContext`, defaults `output_dir` to `<GOALS_DIR>/<slug>`, calls
   `agent_service.trigger_agent(...)` (`api_agents.py:132`).
2. `trigger_agent` (`agent_service.py:1866`) **refuses dispatch unless the goal has a usable
   `external_project_dir`** (`MissingExternalProjectDirError`, `agent_service.py:473-506`) —
   agents run *inside the target project*, not the cast repo. It writes the delegation context
   to `.delegation-{run_id}.json` (`agent_service.py:1923`).
3. `_launch_agent` (`agent_service.py:2068`) ensures a `.cast` symlink into the project
   (`goal_service.ensure_cast_symlink`, line 2114), builds
   `cmd = 'claude --dangerously-skip-permissions --model {model} --name "{display}"'`
   (`agent_service.py:2224`), creates a tmux session + a **visible terminal tab**
   (`tmux.create_session` / `tmux.open_terminal`, lines 2286-2292), waits for Claude to be
   ready, writes the prompt to `.agent-{run_id}.prompt`, and
   `tmux.send_keys(session, "Read the file {prompt_file} and follow its instructions exactly.")`
   (`agent_service.py:2309-2313`).

   > **This is exactly the mechanism running *this* exploration agent right now.** The prompt I
   > was launched from is `goals/product-revamp-diecast/.agent-run_…b6d98b.prompt`; the
   > delegation context is the sibling `.delegation-…json`; I will close by writing
   > `.agent-run_…output.json`. The substrate is self-evidencing.

4. **Child dispatch** (an agent spawning a sub-agent) uses the same path with `parent_run_id`
   set (`agent_service.py:2227-2274`), which builds the `parent_run_id` tree the `/runs` page
   renders. There is even an inline bash polling snippet the parent uses to await the child's
   `.output.json` (`agent_service.py:1384-1390`).

**Tier 1 (terminal):** a human in Claude Code types `/cast-code-explorer`; Claude loads
`~/.claude/skills/cast-code-explorer/SKILL.md` (the generated copy of the same `.md`). Hooks
register the invocation as a `user-prompt`-sourced run (`_invocation_sources.USER_PROMPT`,
`api_agents.py:161` `POST /api/agents/user-invocations`). So terminal usage is *also tracked*
by the same server, in the same `agent_runs` table.

**Tier 3 (chat):** **no surface exists.** The `subagent-invocations` endpoints
(`api_agents.py:187-229`, source `SUBAGENT_START`) track `Task()`-dispatched cast-* subagents,
which is the closest thing to a programmatic invocation, but there is no conversational chat UI
anywhere. The prototype must invent this tier whole — which is fine, it is fake/scripted.

### 5c. The execution drill-in flow (US3) — the reusable jewel

`/runs` → `runs_page` (`pages.py:221`) → `runs_list.html` → recursive `render_run()` macro
(`macros/run_node.html:7`). For each run it renders:
- Row 1: status dot, agent name, goal/task breadcrumb, **`↻ rework #N` tag** when `is_rework`
  (`run_node.html:21`) — *maker-checker iteration made visible*.
- Status cells (`run_status_cells.html`), polled every 3s for running rows
  (`api_agents.py:348` `/runs/{run_id}/status_cells`).
- **Skill chips** (`run_skills_chips.html`) — first 2 skills inline + `+N` overflow.
- Recursive children under a `.thread` rail, with `has-failure`/`has-warning` border state
  rolled up from descendants (`run_node.html:8, 30-36`).
- Expandable detail: summary, **context-usage bar** broken into system/memory/agents/messages
  segments (`run_node.html:62-85`), error, artifacts, and Recheck/Cancel actions.

This component *is* US3 Scenario 2 ("run list → dispatch tree → maker-checker iteration with
rework budget and named exits") **already built in HTML/CSS.** The prototype should lift its
*visual logic* (the tree rail, rework tags, context bars, skill chips) directly — it is the
single highest-value reuse for this whole goal.

---

## 6. Tests & Coverage

Not central to a *vision prototype* (no backend to test), but it characterizes how the team
builds, which matters for Step 6's "cheapest credible build."

- `cast-server/tests/` has `e2e/`, `integration/`, `ui/`, `fixtures/` — a real test pyramid.
- The `ui/` suite implies Playwright-style UI testing already exists; the prototype could be
  smoke-tested the same way if desired, but the spec only requires clickability.
- The 60 agents each ship a `tests/` dir — the team treats agents as tested units (relevant to
  US6's "marketplace credibility / benchmark" framing: the *data* for "99.9% compliant across
  505 runs" has a plausible real source in run history + agent tests).
- **No tests exist for any canvas/chat behavior** because none exists. N/A for this step.

---

## 7. Config & Dependencies

- **Server stack:** FastAPI + Jinja2 + Uvicorn; SQLite (`db/`, `migrations/`, `alembic/`);
  tmux for agent session management (`infra/tmux_manager.py`). Runs at `http://localhost:8005`.
- **Frontend deps (total):** `htmx.min.js` + `easymde` (vendored), Google Fonts (IBM Plex
  Mono / DM Sans / Caveat). **That's it** — no React/Vue/Svelte, no Tailwind, no build tool.
  The whole UI is one 4,156-line `style.css` + Jinja templates.
- **External substrate dependency:** the `claude` CLI itself (invoked as
  `claude --dangerously-skip-permissions --model … --name …`), `git`, and tmux + a GUI
  terminal (`tmux.open_terminal`). Agents require a configured `external_project_dir` per goal.
- **Contract:** `contract_version "2"` output envelope, parsed server-side by
  `load_canonical_file` (`agent_service.py:519-522`, reads `.agent-run_{run_id}.output.json`);
  `/api/agents/jobs/{run_id}` does a **file-canonical read-through** (file wins over DB,
  malformed → 502, `api_agents.py:232-281`). Spec lives at
  `docs/specs/cast-delegation-contract.collab.md`.
- **Implication for the prototype:** the zero-dependency, single-stylesheet, hand-rolled-HTML
  posture is *exactly* what the deliverable wants (browser-openable, no backend). The team is
  already fluent in no-build HTML — Step 6's build recipe is low-risk on that axis.

---

## Key Takeaways

1. **The two surfaces the vision is *about* — the adaptive canvas and the chat rail — do not
   exist in any form.** This is greenfield, and the VISION-FIRST framing is vindicated: there
   is almost nothing to be anchored to. Design the canvas and chat from the research/playbooks,
   not from `goal_detail.html`.

2. **The phase model is hardcoded, linear, and tab-shaped** (`requirements/exploration/planning/
   execution` baked into the tab loop and task enum). It is the *opposite* of the vision's
   per-family adaptive shapes. The prototype must model "workflow family → canvas shape" as a
   new first-class concept; nothing in today's data model or templates expresses it. **This is
   the biggest conceptual leap.**

3. **The execution drill-in (`macros/run_node.html` + `/runs`) is the one genuinely excellent,
   directly-liftable asset.** It already renders dispatch trees, maker-checker rework tags,
   context-usage bars, skill chips, and rolled-up failure state — i.e. US3's execution tab and
   US5's maker-checker activity log, in real HTML/CSS. Lift its visual logic wholesale.

4. **FR-017 is provable, not aspirational — and the chat tier is its one missing leg.** The
   same `agents/cast-*/cast-*.md` is the single substrate: `bin/generate-skills` makes it a
   terminal slash-command skill, and the server dispatches it by driving a real `claude` CLI in
   tmux off a `.prompt` file; both paths emit the identical `contract_version "2"` envelope. The
   side-by-side moment in the spike flow can faithfully depict a true mechanism. (Bonus: the
   `agent_runs.input_params.source` discriminator already distinguishes `user-prompt` vs
   `subagent-start` vs server dispatch — the three tiers are even discernible in the data.)

5. **`assigned_to` (Me / Claude / Me + Claude) is a latent peer-assignee primitive** for US5's
   "humans and agents as peer assignees" board — the only place today's model already blurs the
   human/agent line. Worth echoing as the canonical vocabulary for the board's assignee filter.

6. **Decisions, evidence-rich outputs, promote/pin, and the marketplace are all net-new.**
   US10 decisions, US4 fitted evidence, US1 artifact promotion, and US6 agent-as-colleague
   surfaces have **zero** code precedent. They are pure prototype invention (which is fine —
   all fake) but should not be under-budgeted on the assumption that "the UI mostly exists."

7. **The current identity is a competent "warm workshop" baseline to beat, not adopt.** Cream +
   crimson + IBM Plex Mono + DM Sans + Caveat + 5px grid is coherent but utilitarian. FR-020
   and Step 1 explicitly free the prototype to propose a 2026-grade identity; treat the live CSS
   tokens as the floor.

## Key Files

- `cast-server/cast_server/templates/macros/run_node.html` — **the reusable jewel**: recursive
  dispatch-tree renderer with rework tags, context bars, skill chips (US3/US5 already built).
- `cast-server/cast_server/templates/pages/goal_detail.html` — today's "closest to a canvas"
  (it is a 5-tab container); the phase-locked model the vision replaces.
- `cast-server/cast_server/templates/pages/runs.html` — the execution surface; summary cards +
  threaded run timeline.
- `cast-server/cast_server/templates/pages/agents.html` — the flat agent catalog; raw material
  for US6 marketplace, currently admin-CRUD.
- `cast-server/cast_server/templates/pages/dashboard.html` — the entry surface (goal list); the
  scenario-chooser replaces it.
- `cast-server/cast_server/templates/base.html` — global chrome: sidebar nav, toast helpers,
  artifact-sidebar open/close, the design-token-driven shell.
- `cast-server/cast_server/static/style.css` — the entire 4,156-line design system; tokens at
  `:root` (lines 1-50) define the identity to beat.
- `cast-server/cast_server/routes/api_agents.py` — the dispatch + invocation-tracking API; the
  `/trigger` endpoint (line 88) and the three invocation-source endpoints (161-229) = FR-017.
- `cast-server/cast_server/services/agent_service.py` — `trigger_agent` (1866) + `_launch_agent`
  (2068): how a `claude` CLI is driven in tmux off a `.prompt` file (the substrate, lines
  2224-2313); `load_canonical_file` (519) = the contract-v2 envelope reader.
- `cast-server/cast_server/services/_invocation_sources.py` — `user-prompt` vs `subagent-start`
  source discriminators = the three tiers in the data model.
- `bin/generate-skills` — materializes `agents/cast-*/cast-*.md` → `~/.claude/skills/*/SKILL.md`;
  the proof that one `.md` is both agent and terminal skill.
- `agents/cast-code-explorer/cast-code-explorer.md` + `config.yaml` — canonical agent-definition
  shape (frontmatter + system prompt; runtime knobs) for the "agent resume" surfaces (US6).
- `cast-server/cast_server/templates/fragments/agent_panel.html` — the thin per-goal agent
  list + self-polling run status; what US3's in-goal execution drill-in supersedes.
- `cast-server/cast_server/templates/fragments/artifact_sidebar.html` /
  `artifact_editor.html` — nearest existing analog to a promote/pin surface (a slide-in viewer).

---

## Notes for the synthesizer

- **MCP code-graph tools were not used** (graph not built for this repo per the SessionStart
  notice: "No knowledge graph found"). This map was produced via direct Read/Grep/Glob over the
  cast-server tree — sufficient for a UI-surface terrain map of this size (~691 LOC of pages,
  one stylesheet, ~10 relevant services).
- **Scope honored:** mapped the named surfaces (dashboard, focus, goal_detail, agents, runs)
  and the skill/agent invocation substrate for FR-017. Did not map unrelated subsystems
  (scratchpad internals, suggestion engine, migrations) beyond noting their existence.
- **The single most important thing to carry forward:** treat this codebase as *vocabulary +
  one reusable component (`run_node`) + a provable FR-017 substrate*, and design the canvas and
  chat fresh. The terrain confirms there is no incumbent canvas/chat to negotiate with.
