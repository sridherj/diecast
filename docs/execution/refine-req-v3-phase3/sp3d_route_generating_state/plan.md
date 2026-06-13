# Sub-phase 3d: The Route Serves a Live Generating State and Swaps In the Finished Render

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase3/_shared_context.md` before starting.

## Objective

Make `GET /goals/{slug}/render` never block on generation: a fresh-hash view serves the cached file
untouched; a stale-or-missing render starts the job (idempotent) and immediately serves a live
"generating…" state — the prior stale render with a regenerating banner when one exists, else a
dedicated generating page — which polls a new status endpoint and swaps in the finished render. Stub
and 404 behavior unchanged; the comment path untouched and instant. Under the structural override, a
flagged best-attempt page is **servable** (status `ready`) and the route surfaces its
`structural_violation` "needs review" badge.

## Dependencies

- **Requires completed:** 3c (`render_job_service`, `render_jobs`, the orchestrator seam, the
  `served-by` artifact stamp).
- **Assumed codebase state:** `pages.py` `/render` route, `_theme.css.j2` tokens, the v2 cache
  artifact + embedded `source-hash` header all exist.

## Scope

**In scope:**
- `requirements_render_service.resolve_render(goal_slug, …) -> RenderResolution` (the read side).
- Route rework in `pages.py` (thin dispatch over `resolve_render`).
- The generating state in two flavors (stale-render-with-banner; dedicated generating page).
- The status endpoint `GET /goals/{slug}/render/status`.
- Reader-visible `structural_violation` "needs review" badge derived from the `served-by` stamp.

**Out of scope (do NOT do these):**
- Do NOT modify the job pipeline / fallback logic (3c).
- Do NOT touch `api_requirements.py`, the comment JS, or the tray fragments — leave their tests
  untouched and green.
- Do NOT edit the spec (3e).
- Do NOT add streaming/SSE — poll + reload only.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/requirements_render_service.py` | Modify | Has the 3c orchestrator seam |
| `cast-server/cast_server/routes/pages.py` | Modify | Has the `/render` route |
| `cast-server/cast_server/requirements_render/templates/generating.html.j2` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/templates/_theme.css.j2` | Modify | Has Phase 2 `.comment-affordance` additions |
| `cast-server/tests/test_render_route_and_service.py` | Modify | Exists; gains route + status tests |

## Detailed Steps

### Step 3d.1: `resolve_render(goal_slug, …) -> RenderResolution`

A frozen result with `state ∈ {ready, stub, missing, generating}`, the servable path (fresh `.html`,
or the stale one when generating), and the current `source_hash`. The route becomes a thin dispatch
over this. **`ready` is derived from the artifact** (embedded `source-hash` == current source hash) —
covering maker, flagged, AND fallback publishes with zero extra state.

### Step 3d.2: Route rework in `pages.py`

slug validation → `resolve_render` → dispatch:
- `ready`: serve file (today's path). If the served artifact's header carries
  `served-by: structural_violation`, inject the **"needs review" badge** (response-layer; see 3d.4).
- `missing`/`stub`: today's prompt-to-begin / deterministic behavior, unchanged.
- `generating`: `render_job_service.ensure_job(slug, hash)` (idempotent) then serve the generating
  state with HTTP 200.

### Step 3d.3: Generating state, two flavors

- **Stale render exists:** serve the stale `.html` with a **response-layer injection** (before
  `</body>`) of a `.render-refreshing` banner ("This page is regenerating — you're reading the
  previous version") + a small inline poll script. **The file on disk is never modified** — injection
  is response-only, so the cache artifact stays byte-stable.
- **No render yet:** a small server-rendered `generating.html.j2` (themed with `_theme.css.j2` tokens)
  with the same poll script and a `<noscript>` meta-refresh fallback (FR-028 spirit — content never
  depends on JS; without JS the page converges via refresh).

### Step 3d.4: Poll script + the `structural_violation` badge (OVERRIDE ripple, plan-review A3)

Poll script: `fetch` the status endpoint every ~4s; on `ready`, `location.reload()` (the route then
serves the finished render — "swap-in" = reload-on-ready).

- **On `failed`** (the terminal no-servable-artifact state — a first-generation crash before any
  output could publish, surfaced once the reaper marks the row `failed`): the script **stops polling**
  and swaps the banner/page for a terminal "generation failed — reload to retry" affordance rather than
  polling forever.
- **Flagged best-attempt is NOT `failed`.** Under the override, a structural-exhaustion render is
  *published* (`status=flagged`), so the status endpoint returns **`ready`** for it. The route serves
  it AND injects a reader-visible **"needs review" badge** (response-layer, themed) derived from the
  served artifact's `served-by: structural_violation` stamp. A stale-render-exists structural failure
  also publishes the best attempt (status → `ready` + badge), never `failed`.
- No streaming machinery.

### Step 3d.5: Status endpoint

`GET /goals/{slug}/render/status` (page-adjacent, in `pages.py`) → JSON
`{state: "ready"|"generating"|"failed", source_hash}`. `ready` derived from the artifact (embedded
hash == current); `generating` from the live job registry/row; `failed` only when nothing servable
exists. Slug validated → 404 as everywhere. (The `served-by` stamp drives the badge on the
**page** read-path, not the status JSON — readiness stays a pure artifact-hash derivation.)

## Verification

### Automated Tests (permanent)
Route tests (fake runner) in `test_render_route_and_service.py`:
- fresh hash → 200 served file, byte-untouched, **no job started**;
- stale hash → 200 generating state AND **exactly one** job started;
- repeat view while running → **no second job**;
- after fake job completes → next poll reports `ready` and a reload serves the new render;
- stub → 200 prompt-to-begin, no job; unknown slug → 404;
- **maker fallback (literal no-output)** → status `ready` (the deterministic page IS the render),
  `served-by: fallback` observable on the job row;
- **OVERRIDE: structural-exhaustion flagged best-attempt** → status `ready`, the served page carries
  the `served-by: structural_violation` stamp AND the injected "needs review" badge (assert the badge
  is in the **response**, not in the on-disk artifact);
- **`failed` state** (no servable artifact) → status `failed`; the generating page's terminal affordance
  is reachable.

Status-endpoint tests: `ready` iff the artifact's embedded `source-hash` equals the current source
hash; `generating` while a job row is `running`; `failed` only when no servable artifact exists.

### Validation Scripts (temporary)
- Manual e2e (recorded, non-blocking): edit this goal's source, open `/render` → generating state
  appears immediately; finished render swaps in without a manual reload. (Browser pass is a
  carry-forward; autonomous runs cannot drive a browser — static verdict + human-eyeball note.)

### Manual Checks
- Confirm the banner/badge/poll script never enter the on-disk artifact (grep the cached `.html` after
  a flagged + a refreshing serve — both must be byte-stable).
- Confirm `api_requirements.py` + comment JS/tests untouched and green.

### Success Criteria
- [ ] `resolve_render` returns `{ready, stub, missing, generating}` + servable path + current hash;
      `ready` derived purely from the embedded artifact hash.
- [ ] Stale-hash view starts exactly one idempotent job and serves the generating state at 200.
- [ ] Stale-render-with-banner is **response-layer only**; the cached artifact stays byte-stable.
- [ ] Poll stops on `failed` with a terminal affordance; never polls forever.
- [ ] **OVERRIDE: flagged best-attempt serves at `ready` with a reader-visible "needs review" badge**
      (response-layer) derived from `served-by: structural_violation`.
- [ ] Comment path + its tests untouched and green; stub/404 unchanged.

## Execution Notes

- **OVERRIDE ripple:** the source plan's 3d text treats structural exhaustion as a fallback (status
  `ready` via the deterministic page). Under the override it is a **flagged best-attempt** served at
  `ready` **with a badge** — the deterministic page only appears on literal no-output. Keep `failed`
  strictly for the no-servable-artifact case.
- One source of truth: readiness derives from the artifact, not a second state store — no
  cache-vs-table divergence possible.
- A render exception on the serve path keeps today's contract (existing `.html` intact, plain 500, no
  traceback); a *job* failure never 500s a view.
- **Spec consistency:** US1/FR-001 ("returns 200 with the render") gains the generating-state variant
  AND the flagged-render badge — flag for **3e's** `/cast-update-spec`; do not edit the spec here.
