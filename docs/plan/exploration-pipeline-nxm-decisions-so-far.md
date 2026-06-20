# Decisions So Far — exploration-pipeline-nxm fan-out planning

Cumulative cross-sub-phase decisions, appended after each round. Children adopt these
naming/interface choices unless they document a deviation.

(Round 1 in progress — no prior decisions yet.)

## Round 1 — Spikes (1a, 1b)

### Sub-phase 1a — Workflow-engine spike
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-1a-spike-workflow-engine.md
- **Entrypoint mechanism (to resolve in execution):** Option A = a main-agent SKILL/COMMAND launches the Workflow tool (preferred, matches FR-001 "entrypoint = skill/command, not a subagent"); Option B = server-side dispatch. Spike picks one by demonstration.
- Toy success: 2 steps × 2 hats, each cell a separate clean-context agent → 4 distinct notes; launched from skill/command (not subagent); within min(16,cores−2) cap.
- **Decision gate → Phase 3a:** viable → build engine as planned; not → fallback to orchestrator-agent with ENFORCED per-hat child isolation.
- Interface 3a consumes: Workflow receives `(approved_steps, hat-matrix)` as args.

### Sub-phase 1b — Viewer + commenting spike
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-1b-spike-viewer-commenting.md
- **Embed:** `<iframe srcdoc>` (spec-aligned, null-origin sandbox; no head/style collision). Alt: `<iframe src>` to a serve endpoint (same-origin, allows direct fetch).
- **Comment submit:** srcdoc is null-origin → direct in-iframe `fetch` to same-door API blocked → use a **postMessage-to-host bridge**; comment layer binds mouseup/getSelection to the iframe's document.body.
- **Decision gate → Phase 3b:** in-iframe commenting works (direct OR postMessage bridge) → in-viewer commenting; else → full-page render fallback (like requirements /render today), linked from viewer.
- Viewer seam touchpoints: api_artifacts.py:52 gate, api_goals.py get_phase_tab glob + render_md branch, macros/markdown_viewer.html.

## Round 2 — Foundations (2a, 2b)

### Sub-phase 2a — Single-hat researcher
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-2a-single-hat-agent.md
- **Agent name: `cast-hat-researcher`** (cast-{noun}-{role}). Pure function `(step, hat_id, goal_context) → one note file`.
- **Output:** exactly ONE note at `goals/{slug}/exploration/research/{NN}-{step-slug}-{hat-id}.ai.md` (+ contract-v2 `.output.json` terminal signal, same as fleet).
- **hat_id vocabulary:** always-on = `contrarian`, `first-principles`, `90-10` (literal — matches spec US3 `…-90-10.ai.md`); gateable (5) = expert-practitioner, tool-landscape, ai-native, community-wisdom, framework-methodology (text reused from cast-web-researcher angles, reframed single-hat).
- Angle independence: select EXACTLY one hat block by hat_id; never emit unselected blocks; each cell = fresh clean context (flagged to 3a).
- 80/20 carved OUT of first-principles; 90-10 implements spec's 6 questions + note shape. No `/update-spec` (internal agent, not user-facing).
- **This I/O contract is the interface Phase 3a's `parallel()` over hats consumes.** 1a used a stub at the same contract.

### Sub-phase 2b — Dual md/html viewer
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-2b-dual-viewer.md
- **Embed: `<iframe srcdoc sandbox="allow-scripts allow-popups">`** — NO `allow-same-origin` (null-origin security). `allow-scripts` REQUIRED so Phase 3b's postMessage comment bridge can run.
- **Artifact dict gains `kind` discriminator** (`"markdown"`/`"html"`, derived from extension); `_add_html_file` collector mirrors `_add_md_file`; `.artifact-html-frame` class.
- Render-class `.html` (US4): `authorship=None`, NO edit button.
- Seam touchpoints extended: `api_artifacts.py:52` read gate, `api_goals.py get_phase_tab` glob, `macros/markdown_viewer.html` iframe branch.
- **`/cast-update-spec` on `docs/specs/cast-requirements-render.collab.md`** is a first-class activity (adds dual-viewer behavior + exploration consumer; preserves US4/US7).
- [PENDING 1b]: if srcdoc breaks layout/commenting → fallback `<iframe src>` serve endpoint; the `kind` seam is unchanged.

## Round 3 — Engine + Commenting (3a, 3b)

### Sub-phase 3a — N×M Workflow engine
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-3a-workflow-engine.md
- **Workflow script: `agents/cast-explore-workflow/workflow.py`** (cast-explore-workflow; co-located with the launching skill).
- **`hat-matrix` arg shape:** `{goal_slug, goal_context, steps:[{nn, slug, name, hats:[hat_id…]}]}` (hat_id = 2a vocabulary verbatim).
- Script = `pipeline()` per step → `parallel()` over `M_applicable(step)` calling `cast-hat-researcher` (2a contract) → per-step synthesis barrier = `parallel()` calling UNCHANGED `cast-playbook-synthesizer` (fed the surviving hat notes).
- Relevance gating runs in interactive Phase-1 (a skill) → emits the hat-matrix; always-on hats never gated; dropped/queued cells surfaced (not suppressed).
- **Entrypoint wiring = single `[PENDING 1a]` seam** (build against Option-A skill/command; Option-B server-dispatch or orchestrator-fallback only reshape this one seam). Register the workflow in config/routing.
- md artifact paths unchanged (research/playbooks/summary) → the interface Phase 4 consumes. No prior-phase revisions.

### Sub-phase 3b — Diecast-wide HTML commenting
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-3b-html-commenting.md
- **postMessage-to-host bridge:** reuse cast-comment-html `comment-layer.js`+`anchor.js`; replace its `submit()` transport with `window.parent.postMessage({comments[], goal_slug, artifact_ref})`; host bridge proxies PER-COMMENT POSTs to the same-door create endpoint (no new endpoint).
- **NEW field `artifact_ref`** (goal-relative artifact path, e.g. `exploration/exploration.html`) on the comment create/relocate/displacement path so a comment knows WHICH artifact its quote came from. Additive + defaulted (default=requirements → existing behavior unchanged). Mirrors `block_ref`/`anchor_space` server-resolved fields. **← reconciliation: verify against requirements comment flow + roundtrip spec.**
- `anchor_space='render'` (already written by `create_comment`); verbatim-substring via `container_text_index`; `block_ref` honest-NULL for ref-less containers. NO stable anchor-ids (deferred).
- `[PENDING 1b]`: bridge vs full-page fallback.

## Round 4 — Convergence (Phase 4)

### Sub-phase 4 — Exploration WHAT/HOW HTML render
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-4-exploration-render.md
- **Decision: build a PARALLEL lean render-job**, do NOT extend `render_job_service.py` (it's a 2400-line requirements-coupled apparatus). New module **`cast_server/services/exploration_render_service.py`** + publish helper **`publish_exploration_html(slug, html, *, source_digest, served_by, ...)`** → `goals/{slug}/exploration/exploration.html` (atomic + AUTO-GENERATED + source-digest + served-by envelope). Shared agent-runner lifted to `cast_server/render_common/agent_runner.py` (or imported from render_job_service).
- Agents (cast-{noun}-{role}, matches cast-hat-researcher family): **`cast-exploration-what`** (content, no HTML — opinionated POV + distinct hat takes per step), **`cast-exploration-how`** (bespoke self-contained HTML, hats DISTINCT not blended), **`cast-exploration-render-checker`** (sees only the page + step/hat labels; grades FR-017's 4 criteria; ONE bare-JSON verdict).
- WHAT agent's ONLY content source = 3a's md files (research/playbooks/summary). The render is a VIEW, never new content.
- exploration.html inherits viewer (2b) with ZERO new viewer code (lands in exploration/ glob, .html ext) and commenting (3b) with ZERO new comment code (`artifact_ref="exploration/exploration.html"`).
- No prior-phase revisions flagged.

## Round 5 — E2E (Phase 5)

### Sub-phase 5 — End-to-end integration & parity
- Plan: docs/plan/2026-06-20-exploration-pipeline-nxm-5-e2e-parity.md
- Produces: an unattended e2e run on a real goal; a **SC-001..SC-009 verification matrix** (concrete check each — exact filename-SET equality vs the persisted hat-matrix, not just counts; First Principles grep for absent 80/20; render-checker verdict; comment e2e); md-substrate byte-compat with cast-high-level-planner; and a durable **`parity-notes.md`** (4 axes: playbook quality, angle sharpness, cost, time) comparing N×M vs cast-explore on the SAME goal for the merge decision.
- Collision-safe: snapshot/copy both pipelines' output trees side-by-side before any read. No new feature work.
- No prior-phase revisions flagged.

## EXECUTION — Group 2 as-built (2a, 2b)
- **2a DONE:** `agents/cast-hat-researcher/` built — agent + `config.yaml` + README + tests
  (acceptance, check-failure-path.sh, check-distinctness.sh). 8 hat_ids
  (`90-10, contrarian, first-principles` always-on + 5 gateable). **Web Fetching Protocol extracted to
  `web-fetching-protocol.md` (shared, referenced — review #4 DRY honored).** Registered as a skill.
  I/O: `(step, hat_id, goal_context) → exploration/research/{NN}-{slug}-{hat-id}.ai.md`.
- **2b DONE:** artifact viewer renders dual md/html. `api_goals.py` `_add_html_file` + `kind`
  discriminator (`"markdown"`/`"html"`); render-class `.html` → `authorship=None`, no edit button (US4);
  `markdown_viewer.html` `artifact_content(html, kind)` → `<iframe srcdoc>` branch (sandbox, no
  allow-same-origin). `api_artifacts.py` admits `.html`. **`cast-requirements-render.collab.md` updated
  (/cast-update-spec) — spec-checker exit 0.** `tests/test_dual_viewer.py` 6 passed (incl. adversarial
  srcdoc escaping, review #6). Seam consumed by 3b + Phase 4.

## EXECUTION — Group 3 as-built (3a, 3b)
- **3a DONE+TESTED:** `agents/cast-explore-workflow/` — **`workflow.mjs` (JS, not .py)** + entrypoint
  `cast-explore-workflow.md` + `cast-explore-workflow.collab.md` spec. Tests pass: barrier glob∩hat_id
  (#9 — excludes `-code.ai.md` + slug-prefix collisions + path-traversal), all-hats-fail placeholder
  (#7 — surfaces dropped hats, never calls synthesizer empty). Cost-at-gate (#8) in the entrypoint.
- **3b DONE+TESTED:** `static/comment-bridge.js` (host bridge) + `comment_layer_inject.py` + comment-layer.js
  transport → `postMessage`. New `artifact_ref` field on the same-door create/relocate path (additive,
  DEFAULTED=requirements). jsdom `test_comment_bridge.js` (22 assertions: source-identity guard, per-comment
  fan-out w/ artifact_ref, reply targetOrigin '*' to originating frame only, multi-iframe routing) +
  `test_html_comment_bridge_contract.py`. **Regression: 222 passed — existing requirements commenting intact.**

## EXECUTION — Group 4 as-built (Phase 4 render)
- **4 DONE+TESTED:** `cast_server/render_common/` shared core (agent_runner, atomic, job_runtime,
  quality_loop, sentinel, verdict) — render_job_service.py refactored onto it (#2A; direct-import
  coupling rejected). `cast_server/services/exploration_render_service.py` = **498 lines (<500 target)**.
  Agents `cast-exploration-what/how/render-checker`. Publishes `exploration/exploration.html` (atomic +
  served-by). Inherits viewer (2b) + commenting (3b) with zero new code. Degraded-step test (#7) added.
  **336 passed — render_job_service regression green after the shared-core refactor.**

## EXECUTION — Group 5 as-built (Phase 5 e2e + parity)
- **5 DONE (verify-only, partial e2e):** SC matrix `phase5/sc-verification.md`, `parity-notes.md`,
  `byte-compat-check.md`, `RUNBOOK-live-verification.md` (R1-R9 live steps). Static PASS (contract+code):
  SC-002, SC-003, SC-006, SC-007, SC-008. [NEEDS-LIVE] (contract verified, instance pending Run-1):
  SC-001, SC-004, SC-005, SC-009. Full suite: 1181 passed; the 1 fail + 1 error are PRE-EXISTING
  delegation/tier tests (commit 25f16b8 "skip 9 failing delegation/UI tests"), unrelated to this diff.
