# Shared Context: refine-req-v3-phase3 (The WHAT→HOW Maker Pipeline Renders Bespoke HTML)

> Read this file at session start before executing any sub-phase plan in this project.

## Source Documents

- **Plan (authoritative):** `docs/plan/2026-06-12-refine-requirements-v3-phase3-maker-pipeline.md`
- **Reconciliation report:** `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- **Decisions-so-far (binding owner decisions):** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
- **Phase-1 gate / carry-forwards:** `docs/goal/refine-requirements-better-rendering-v3/spikes/PHASE1-GATE.md`

## Project Background

On the happy path, `GET /goals/{slug}/render` is served by a **two-agent pipeline**:
`cast-requirements-what` emits per-block/per-family communication intent (a machine-checkable
WHAT doc), and `cast-requirements-how` turns it into a self-contained, bespoke, per-family HTML
page selecting from the named cast-preso archetype library. The canonical
`US-NN`/`FR-NNN`/`SC-NNN` ids ride along as a **logical (non-DOM) backbone** — printed as small
visible anchor labels, never as `id=`/`data-block-anchor` attributes. The v2 deterministic
renderer is demoted to a **fallback branch**. Generation runs as a **background job**: a view of a
changed source serves a live "generating…" state immediately and swaps in the finished render when
ready; the comment path is independent and always instant; the v2 source-hash lazy-regeneration
cache is reused unchanged.

Both agents run as tool-free `claude -p` subprocesses driven by a new `render_job_service` — the
same headless invocation pattern already used by `eval_render_checker.py` and `agent_service.py`'s
`/context` call (`claude -p <msg> --append-system-prompt <agent.md> --model <m> --tools ""`). The
tmux HTTP-dispatch path is **wrong** for this job (it pops a visible terminal; a page view must
never do that). `--tools ""` makes "the maker never writes the canonical source" **structural**,
not behavioral.

**Phase 1 is GREEN** (`G1 = GO-TO-PHASE-3`, both spikes cleared). This plan assumes that gate
passed; if it had failed, this plan would be void.

## Operating Mode

**HOLD SCOPE.** `refined_requirements.collab.md` front matter pins `scope_mode: hold`. Owner
decisions in `decisions-so-far.md` are binding and not re-opened. Checker + rework loop (4a),
diff/comment-resolution (4b), and gap-fill upstream asks (5) are **out of scope** — Phase 3 designs
only the seams they plug into.

## Codebase Conventions

- **Pure render package vs. service split.** `cast_server/requirements_render/` is pure
  (no I/O, no DB, no LLM): `parser.py`, `block_diff.py`, `renderer.py`, `families.py`,
  `goal_card.py`, `stub.py`, `hashing.py`, `zero_click.py`, `templating.py`, `templates/`. All
  I/O and subprocess work lives in `cast_server/services/`. The new `maker_gate.py` joins the
  **pure** package; the new `render_job_service.py` joins the **service** layer.
- **Single-implementation discipline.** One markdown stripper (Phase 2's `strip_inline_markdown`),
  one container-text walker (3b's, exposed as a shared helper), one `verbatim_locate`. Copying a
  second implementation is drift by construction — import, never re-implement.
- **Subagent bare-output carve-out.** The two new agents follow the `cast-comment-reanchor`
  precedent: `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `allowed_delegations: []`, bare output (no `.output.json` envelope). Registry discovery via
  `bin/generate-skills`.
- **Subprocess hygiene (production precedent = `agent_service.py`):** `env -u CLAUDECODE` +
  explicit job-dir cwd + clean child env. A `claude -p` that inherits a parent session's
  `CLAUDECODE`/cwd can hang or recurse.
- **`build/` is a non-goal, non-CI-collected runtime area.** Job artifacts live under
  `build/render-jobs/{slug}/{hash12}/`, never inside `goals/{slug}/` (keeps the FR-026 folder
  invariant intact).
- **DB migration test pattern:** `tests/test_schema_migration.py` covers `schema.sql` changes.

## Key File Paths

| File | Role |
|------|------|
| `cast-server/cast_server/requirements_render/parser.py` | `parse_requirements`, `Block.ref` (`US1`/`FR-007`/`SC-001` in-memory refs) |
| `cast-server/cast_server/requirements_render/stub.py` | `is_stub`, `STUB_WORD_THRESHOLD` |
| `cast-server/cast_server/requirements_render/renderer.py` | `render_requirements()` — deterministic substrate (fallback body) |
| `cast-server/cast_server/requirements_render/families.py` | `WorkFamily`, `FAMILY_RECIPES`, `RECIPE_REALIZATION` (WHAT starting vocabulary) |
| `cast-server/cast_server/requirements_render/goal_card.py` | **Phase 2's `strip_inline_markdown`** (hard dependency for 3b) |
| `cast-server/cast_server/requirements_render/zero_click.py` | `extract_zero_click_view` |
| `cast-server/cast_server/requirements_render/maker_gate.py` | **NEW (3b)** — pure gate module |
| `cast-server/cast_server/services/requirements_render_service.py` | v2: `rerender_requirements_html` (atomic write + AUTO-GENERATED header + `source-hash` cache). Gains the orchestrator seam (3c) + `resolve_render` (3d) |
| `cast-server/cast_server/services/render_job_service.py` | **NEW (3c)** — background-job pipeline + `AgentRunner` |
| `cast-server/cast_server/services/agent_service.py` | `claude -p` subprocess + env-hygiene precedent (`env -u CLAUDECODE`) |
| `cast-server/cast_server/config.py` | gains `RENDER_JOBS_DIR`, stage-timeout list, reaper ceiling multiple, in-flight cap |
| `cast-server/cast_server/db/schema.sql` | gains the `render_jobs` CREATE TABLE (3c) |
| `cast-server/cast_server/routes/pages.py` | `/render` route + new `/render/status` endpoint (3d) |
| `cast-server/cast_server/routes/api_requirements.py` | comment API — **untouched** |
| `agents/cast-comment-reanchor/` | subagent carve-out precedent (config + bare-output) |
| `cast-server/tests/eval_render_checker.py` | `claude -p` server-side invocation precedent |

## Data Schemas & Contracts (copy verbatim — these are fixed by the plan, not discovered at exec)

### WHAT doc (`cast-requirements-what/v1`) — markdown body + YAML front matter

```yaml
contract: cast-requirements-what/v1
goal_slug: <slug>
family: <WorkFamily value>
source_hash: <hash>
sections:
  - title: <family-appropriate communication section name — NEVER a US/FR/SC slot name>
    outcome: <what a reader must take away (preso L1/L2 discipline)>
    block_refs: [US1, FR-003, ...]   # canonical ids feeding this section
unmapped_refs: []   # every parsed ref must appear in exactly one section; leftovers fail the gate loudly
gaps: []            # RESERVED Phase-5 seam (FR-015). Defined now, ALWAYS empty in Phase 3, zero behavior.
```

Body: per-section communication-intent prose (L1 vs L2 emphasis). Hard rules: sections NEVER named
after US/FR/SC slots; ids are metadata the HOW layer prints as small anchor labels; the WHAT layer
never invents content absent from the source.

### HOW output — one complete self-contained HTML document between sentinels

```
<!-- BEGIN RENDER -->
<!doctype html> … complete self-contained page … 
<!-- END RENDER -->
```

- **Strict extraction:** content = first `<!-- BEGIN RENDER -->` to the *first following*
  `<!-- END RENDER -->`. Missing / mis-ordered / duplicate sentinels, a markdown-fenced or chatty
  wrapper, or unparseable WHAT front matter all count as **no-output**.
- **OPTIONAL `GAPS-DETECTED` trailer (revision f — Phase 3 documentation-only forward reference):**
  the HOW contract permits an optional `GAPS-DETECTED` trailer to appear *after* `<!-- END RENDER -->`,
  i.e. **outside** the extraction window. Phase 5 activates it; **Phase 3 attaches zero behavior** —
  strict extraction already stops at the first `END RENDER`, so the trailer is byte-ignored. The WHAT
  front matter's reserved `gaps: []` is the paired seam. Do **not** write parsing/handling code for
  either in Phase 3.
- DOM contract: zero `id=`, zero `data-block-anchor`; each requirement unit one contiguous semantic
  `<section>`/`<li>` under a real `<h2>`/`<h3>`; CSS inline; no CDN fonts; no external fetches beyond
  the FR-028-sanctioned `/static/htmx.min.js` + `/static/requirements_comments.js` + `data-goal-slug`
  on `<body>`.
- **Verbatim carriage:** each unit's anchorable text (source body with inline markdown stripped)
  appears verbatim and contiguous within that unit's container.
- Every canonical id from the WHAT doc emitted verbatim exactly once as a small visible anchor label;
  never invented, never renamed. Empty recipe blocks omitted, never padded.

### `GateReport` (frozen)

```python
GateReport = {"passed": bool, "violations": list[str]}   # violations are prompt-ready strings
# e.g. "FR-003 label missing for SC-002", "verbatim carriage failed for US1: …"
```

### `render_jobs` table — Phase 3 INITIAL CREATE TABLE (revision a)

```
id, goal_slug, source_hash,
status,        -- running | published | fallback | superseded | failed | flagged
attempts, error,
started_at, finished_at,
heartbeat_at   -- written by the per-job thread at EVERY stage boundary (revision a)
```

- **4a-2's migration later adds ONLY the four flag columns** (`human_review`, `review_reason`,
  `published_attempt`, `published_score`) — Phase 3 does **not** create those.
- Readiness is **never** derived from this table — the artifact's embedded `source-hash` is the
  single source of truth. The table is the observability / status / failure-reason surface and the
  seam where 4a records its richer human-review flag.

### Pipeline stage seam (named functions — the 4a/5 insertion seam)

```
run_what → gate_what (check_what_doc) → run_how → gate_html (check_html) → publish
```

## Pre-Existing Decisions (binding — from decisions-so-far.md)

- **Anchor backbone is logical only**; DOM keeps v2 quote/verbatim-substring anchoring; no `id=`.
- **Background-job render model**; net-new agents reusing the preso toolkit/archetypes; family-
  communication page vocabulary (never US/FR/SC slots); v2 hash cache reused unchanged; maker never
  writes the canonical `.collab.md`.
- **Fallback policy:** the deterministic renderer is served **ONLY on a literal no-output failure**
  (crash / timeout / nothing produced).
- **STRUCTURAL-VIOLATION OWNER OVERRIDE (2026-06-12, supersedes the older flagged fork):** on
  structural-retry exhaustion, serve the **best attempt + human-review flag (`structural_violation`)**
  — **not** the deterministic page. "Never SILENTLY drop" still binds: the degradation is **surfaced
  via flags/badges**, not hidden. Guiding principle: **surface, don't suppress.**
- **Phase-3 flag mechanism (owner-confirmed for THIS split, 2026-06-12):** because Phase 3 runs
  before 4a and has no scoring, Phase 3 records the flag with the machinery it already owns —
  a `flagged` **status** value, the **reason in the existing `error` field**, and a **served-artifact
  stamp** (`served-by: structural_violation` beside `source-hash` in the AUTO-GENERATED header) that
  3d turns into a reader-visible "needs review" badge. 4a-2's four flag columns layer on top later.
  Phase 3 does **not** pull 4a's columns forward.
- **Model tier = `opus`** for `cast-requirements-what` / `-how` (placeholders already say `opus`;
  the `[USER-DEFERRED]` knob is a later tune-down, not a Phase-3 decision).

## Relevant Specs

- **`cast-requirements-render.collab.md` (Draft v2)** — `linked_files` overlap with this plan's
  files. Sub-phase **3e** runs the single `/cast-update-spec` pass (happy-path inversion,
  generating-state route, non-DOM id backbone + verbatim-carriage clause, determinism scope narrowed
  to the fallback substrate). Sub-phases 3a/3c/3d **flag** spec deltas but do not edit the spec —
  3e records them. Read the spec on-demand only when touching spec-linked files.
- **`cast-goal-classification.collab.md` (Draft v1)** — `WorkFamily` enum, `FAMILY_RECIPES`,
  classification front matter. **Consumed, not modified.**

## Cross-Phase Hard Edges (do not violate)

- **2a → 3b (HARD):** 3b's verbatim-carriage check imports Phase 2's `strip_inline_markdown` from
  `goal_card.py`. If Phase 2 has not landed it, 3b **blocks on the helper or lifts it to a shared
  pure module — it never inline-copies a second stripper.**
- **3b walker → 4b-1 (HARD, no-copy):** 3b exposes the container-text walker as the public
  `container_text_index(html)` helper in `maker_gate.py`; 4b-1 imports it.
- **Seams reserved for later phases:** 4a inserts `run_checker → decide_quality` between `gate_html`
  and `publish` and adds its four flag columns; 4b widens the `gate_html` report (carriage + survival)
  and imports the walker; Phase 5 activates `gaps[]` + the `GAPS-DETECTED` trailer and registers gap
  stages in the stage-timeout list.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 3a (WHAT/HOW agents) | Sub-phase | Phase 1 green | 3c, 3e | 3b |
| 3b (maker gate) | Sub-phase | Phase 1 green; **Phase 2 `strip_inline_markdown` (hard)** | 3c, 3e | 3a |
| 3c (render job service) | Sub-phase | 3a, 3b | 3d, 3e | — |
| 3d (route + generating state) | Sub-phase | 3c | 3e | — |
| 3e (spec + e2e gate) | Sub-phase | 3a, 3b, 3c, 3d | — (terminal) | — |

No decision gates: the source plan defines none. 3e's `/cast-update-spec` is an inline skill-approval
gate handled within 3e; the human-eyeball browser pass is a non-blocking carry-forward
(no-browser-for-visual-gates rule).
