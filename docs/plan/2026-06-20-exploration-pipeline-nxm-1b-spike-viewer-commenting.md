# Exploration Pipeline — N×M Workflow: Phase 1b Spike — Dual md/html viewer + in-frame commenting

## Overview

This is a **time-boxed spike** (1–2 sessions) that answers two binary questions, and nothing
more: **(a)** does a full standalone HTML render (the *existing* `refined_requirements.html`,
own `<head>`/`<style>`) display cleanly inside the artifact viewer's phase-tab surface via
**iframe/`srcdoc`** without colliding with the host page, and **(b)** does a text selection
*inside* that iframe yield a real comment row through the **same-door** comment API
(`POST /api/goals/{slug}/requirements/comments`, `anchor_space='render'`). The spike is
validated against an artifact that **already exists** so it doesn't wait on any Track-A work or
on the dual-viewer build itself — it probes the seam directly.

The key insight driving the experiments: `cast-comment-html`'s annotation layer
(`comment-layer.js`) attaches its `mouseup`/`getSelection` listeners to **the served page's own
`document.body`**. When the render is embedded as an iframe, those listeners would have to live
inside the *iframe's* document, and the comment POST has to cross the iframe boundary back to the
host's same-door API. Whether that injection + cross-boundary POST works (especially under
`srcdoc`, which yields an opaque/null-origin document) is the entire risk this spike retires.

**This is throwaway probe code.** No production wiring, no spec updates, no new agents. The
deliverable is a **verdict + evidence** that sets the architecture for Phase 2b (viewer) and
Phase 3b (commenting).

## Operating Mode

**SCOPE REDUCTION** — the parent goal is `scope_mode: hold` (per `refined_requirements.collab.md`
frontmatter), but *this sub-phase is explicitly a spike*. The plan doc names it "Spike —", the
build order frontloads it as a Phase-1 de-risking probe, and the requirements language is
"determine whether … tested against the existing …". Per Spike-First Planning, a spike commits to
**surgical minimalism**: prove/disprove the two questions with the smallest possible probe, defer
all production concerns to Phase 2b/3b. Anything beyond the two decision gates is out of scope for
1b.

## Position in Overall Plan

```
        ┌─ Phase 1a (spike: Workflow engine) ─────────────┐
        │                                                 ▼
Phase 1 ┤                                   Phase 2a ─► Phase 3a ─┐
(spikes)│                                                         ▼
        └─ Phase 1b (spike: viewer+comment) ─► Phase 2b ─► Phase 3b ─► Phase 4 ─► Phase 5
           ▲ YOU ARE HERE                      (viewer)   (commenting)
```

- **Dependencies:** None. Runs in parallel with Phase 1a. Probes the *existing*
  `refined_requirements.html` + same-door API — neither Track-A engine nor the dual viewer.
- **Unblocks (this spike is a decision gate for 2+ downstream sub-phases — hence its urgency):**
  - **Phase 2b** (dual md/html viewer) — the iframe/`srcdoc` embed approach this spike validates
    is exactly what 2b productionizes in `macros/markdown_viewer.html`.
  - **Phase 3b** (Diecast-wide commenting) — the in-iframe-vs-full-page decision this spike
    renders is Phase 3b's foundational fork: in-viewer comment layer **or** a linked full-page
    serve.

## Sub-phase 1b: Spike — Dual md/html viewer + in-frame commenting

**Outcome:** A written verdict (with reproducible evidence) on two binaries:
1. **Render-in-viewer** — the existing `refined_requirements.html` displays cleanly inside the
   phase-tab artifact area via iframe/`srcdoc`, with **no `<head>`/`<style>` collision** with the
   host page (host CSS doesn't leak in; render CSS doesn't leak out; host layout/scroll intact).
2. **Comment-in-iframe** — a text selection *inside* that iframe produces a persisted comment row
   via the same-door API (`POST …/requirements/comments`), with `anchor_space='render'` and the
   `{quoted_text, section_hint, body}` shape.

The verdict drives the **decision gate** that shapes Phase 3b.

**Dependencies:** None.

**Estimated effort:** 1–2 sessions (Session 1 = render embed + Experiment A; Session 2 =
in-iframe comment injection + Experiment B + gate write-up). If Experiment A fails outright, the
fallback is decided same-session and B becomes "test commenting on the full-page serve instead."

**Verification (spike success criteria — both must be observed and screenshotted/logged):**
- **SC-A (render):** Loading the probe phase tab shows the rendered `refined_requirements.html`
  (its Goal Card + L1/L2 hierarchy visible) inside the iframe; the host page's tabs, nav, and
  scroll behave unchanged; no host-stylesheet bleed into the render and no render-stylesheet bleed
  into the host (verified by toggling a deliberately-clashing host rule, e.g. `body { background:
  red }`, and confirming the iframe interior is unaffected).
- **SC-B (comment):** Selecting text inside the iframe and submitting a comment results in a new
  `requirement_comments` row for the goal with `anchor_space='render'`, retrievable via
  `GET /api/goals/{slug}/requirements/comments` — confirmed by the row's `quoted_text` matching
  the selection and `body` matching what was typed.

### Key activities

**Setup (≤30 min) — get a real render artifact to probe.**
- Confirm a `refined_requirements.html` exists for a probe goal. The exploration goal itself has
  `refined_requirements.collab.md` but may not have a published `.html` yet. Generate one the
  honest way by hitting the existing route: `GET /goals/{slug}/render` against any goal that has
  refined requirements (this calls `requirements_render_service.rerender_requirements_html` /
  `resolve_render` and writes `goals/{slug}/refined_requirements.html`). Use whatever goal already
  has a clean published render to avoid coupling the spike to render-maker quality. Copy the
  resulting `.html` to a known probe path.
- **No new artifact contract** — the spike consumes the file at its existing path
  (`goals/{slug}/refined_requirements.html`); it does not invent a new location.

**Experiment A — iframe/`srcdoc` embed in the phase-tab viewer (the render question).**
- Build a *throwaway* probe route or a minimal local HTML harness that embeds the existing
  `refined_requirements.html` two ways and compares:
  - **A1 — `srcdoc`:** `<iframe srcdoc="{escaped full html}">`. This is the spec-aligned target
    (the requirements `Constraint`: "a full standalone HTML doc cannot be inline-injected … →
    iframe/srcdoc is required"). Note `srcdoc` yields a **null-origin** document — flag this, it's
    load-bearing for Experiment B.
  - **A2 — `src` to a serve endpoint:** `<iframe src="/goals/{slug}/render">` (or a probe serve of
    the file). Same-origin document; easier cross-frame scripting. Kept as the comparison arm
    because it changes B's feasibility.
- For each arm, verify **SC-A**: render visible, Goal Card legible, host page intact. Apply the
  collision probe (clashing host rule) and confirm isolation in both directions.
- Decide iframe **sizing**: standalone renders have their own scroll; test `height` via a fixed
  tall value vs a `postMessage`/`onload` content-height handshake. Pick the *simplest thing that
  shows the render without a double-scrollbar mess* — sizing polish is Phase 2b's problem, the
  spike only needs "renders cleanly, no obvious breakage."
- **Touchpoint note (for Phase 2b, not built here):** the real seam is
  `macros/markdown_viewer.html` `artifact_content()` (currently `{{ html | safe }}` inside
  `.markdown-body`) + the phase-tab glob in `api_goals.py` `get_phase_tab`
  (`_add_md_file` / `*.md` glob at ~line 422, keyed off `PHASE_ARTIFACTS`) + the read gate
  `api_artifacts.py:55` (`validate_artifact_path_read`, currently `.md`-only). The spike **reads**
  these to size the change but **does not modify** them — modification is Phase 2b.

**Experiment B — text selection inside the iframe → same-door comment (the comment question).**
- Inject the `cast-comment-html` layer (`assets/comment-layer.css` + `anchor.js` +
  `comment-layer.js`, via the `build_page` injection pattern in `comment_html.py`) into the
  embedded render's HTML **before** it's set as the iframe content. The layer's `mouseup` /
  `window.getSelection()` listeners bind to the **iframe's** `document.body` (the layer builds all
  its own UI; the host injects nothing into the host page) — confirm selection inside the iframe
  fires the "+ Comment" popover.
- Replace the layer's default Submit target (today: `POST /submit` to its own stdlib server,
  `window.__CCH__.submit`) with a probe that calls the **same-door** API:
  `POST /api/goals/{slug}/requirements/comments` with body
  `{quoted_text, section_hint, body, author_kind:'human'}` (the `CreateCommentRequest` shape in
  `api_requirements.py`). The server resolves `anchor_space`/`block_ref` server-side (per
  `cast-requirements-render` FR-057) — the client never sends `block_ref`.
- **The crux to observe — does the POST cross the boundary?** Two sub-cases keyed off Experiment A:
  - If embedded via **`srcdoc` (A1, null origin):** an in-iframe `fetch('/api/...')` is a
    cross-origin request from an opaque origin → likely **CORS-blocked / fails**. Test whether the
    layer can instead `postMessage` the `{quoted_text, section_hint, body}` payload **up to the
    host frame**, which then does the same-origin POST. Record whether `postMessage` selection
    bridging works.
  - If embedded via **`src` to a same-origin serve (A2):** the in-iframe `fetch` is same-origin
    and should succeed directly. Record whether direct in-iframe POST works.
- Verify **SC-B**: after submit, `GET …/requirements/comments` returns a new row with matching
  `quoted_text`/`body` and `anchor_space='render'`. Use a probe goal that has a published render
  on disk so the server's render-space relocate/anchor backstop
  (`_resolve_render_compare_text`) has text to validate against.
- **Note (selection quality is NOT a spike gate):** `comment-layer.js` grows unique
  prefix/suffix context (`anchor.js` `uniqueContext`) and computes `section_hint` from the nearest
  heading — that's fine as-is. The spike does **not** need to prove re-anchor-on-rerender survival
  (that's Phase 3b, verbatim-substring relocation per FR-012). It only needs "a selection yields a
  persisted row via the right door."

**Decision gate — write the verdict.**
- **Gate G1 (render):** SC-A holds in **at least one** of A1/A2 → embedding a standalone HTML
  render in the viewer is viable; Phase 2b proceeds. (Prefer `srcdoc`/A1 per the spec constraint;
  if only A2 works, Phase 2b serves via a route, which is a bigger change — record that delta.)
  - If **neither** arm renders cleanly (intractable collision/breakage) → escalate: Phase 2b's
    "HTML in the phase tab" premise is at risk; fall back to **linking** to the existing full-page
    `/goals/{slug}/render` from the viewer (US10's status quo) rather than in-place embed. (Low
    probability — `srcdoc` isolation is well-understood — but stated for honesty.)
- **Gate G2 (commenting) — the load-bearing fork for Phase 3b:**
  - **In-iframe commenting works** (SC-B passes, whether via direct same-origin POST or
    `postMessage`-to-host bridge) → **Phase 3b proceeds in-viewer**: the comment layer lives inside
    the embedded render and routes through the same-door API. Record *which* mechanism
    (direct vs postMessage) so 3b builds the proven one.
  - **In-iframe commenting does NOT work** (selection can't be captured across the boundary, or no
    POST mechanism persists a row) → **fallback: comment on a full-page render surface** — the
    viewer shows the render (read-only, per G1) and **links out** to a `cast-comment-html`-style
    full-page serve (as requirements `/render` does today) where commenting happens. Phase 3b
    builds the link-out + full-page comment serve instead of in-viewer annotation.
- Write the gate outcome + the screenshots/curl evidence into the spike's findings (return as the
  agent message and/or a short note in the goal's `exploration/`), so Phase 2b and 3b inherit a
  decided architecture, not an open question.

### Design review

- **Spec consistency (`cast-requirements-render.collab.md`):**
  - ⚠️ **US7 "selectable units, no ids" must be honored, not bypassed.** The render's DOM has
    **no `id=`/`data-block-anchor`** by contract (US7 / FR-012). The spike's comment layer must
    anchor purely on **quote + prefix/suffix context** (which `anchor.js`/`comment-layer.js`
    already do) — do **not** add ids to the render to make selection easier. Action: confirm the
    probe layer never injects anchors; it reads text only.
  - ⚠️ **`anchor_space='render'` is required (FR-057 / US4).** Comments on a render anchor in
    **render space**, validated against the served render's container text — never source space.
    The same-door `create_comment` resolves `block_ref` **server-side**; the client must not send
    it. Action: confirm the probe POST omits `block_ref` and the row lands `anchor_space='render'`.
    *(If the current `CreateCommentRequest`/`create_comment` defaults a render POST to
    `'source'`, that's a finding for Phase 3b — flag it, don't patch it in the spike.)*
  - ✓ **No `/update-spec` in 1b.** A spike doesn't change behavior contracts. The dual-viewer
    behavior + exploration consumer get spec'd in **Phase 2b** (already an activity there). The
    spike only *reads* the spec as a constraint.
- **Security:**
  - Path/serve hygiene — if the spike adds a throwaway serve of the `.html`, it must stay within
    the goal dir (reuse the `_validate_artifact_path_base` GOALS_DIR containment rule); do not open
    an arbitrary-file serve. Throwaway probe code still shouldn't introduce a traversal hole.
  - `srcdoc` null-origin is a **feature** here (sandbox isolation), not a bug — note that the
    isolation that protects the host is the same thing that blocks the direct POST (hence the
    `postMessage` bridge arm). This tension is the real finding of the spike.
- **Architecture consistency:**
  - The spike reuses the **same-door** comment API (`api_requirements.py` `create_comment`) rather
    than inventing a new endpoint — correct, this is the FR-013 "one door" invariant the whole
    Track-B design rests on. ✓
  - `cast-comment-html`'s `build_page` injection pattern is the reuse vehicle for the layer; the
    spike adapts only the **submit target**, not the capture/anchor logic. ✓
- **Error & rescue (spike-appropriate, minimal):** if Experiment B's POST fails, the failure
  **is the data** — capture the browser console error (CORS vs 4xx vs network) verbatim; that
  error message *is* what selects the G2 branch. Don't swallow it.

## Build Order

```
Setup (get a real refined_requirements.html on disk)
   │
   ▼
Experiment A ──► SC-A? ──► Gate G1 (render viable / fallback to link-out)
 (A1 srcdoc,        │
  A2 src)           ▼
              Experiment B ──► SC-B? ──► Gate G2 (in-viewer commenting / full-page fallback)
              (inject layer,
               POST to same-door,
               direct vs postMessage)
   │
   ▼
Write verdict + evidence → feeds Phase 2b (viewer) & Phase 3b (commenting)
```

**Critical path:** Setup → Experiment A → Experiment B → Verdict. (A and B are sequential — B's
mechanism depends on A's embed choice. A1-vs-A2 within Experiment A run in parallel.)

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 1b | US7 "no ids/anchors" DOM contract — don't add ids to ease selection | Confirm probe layer anchors on quote+context only; reads text, never mutates render DOM |
| 1b | `anchor_space='render'` + server-resolved `block_ref` (FR-057) | Probe POST omits `block_ref`; verify row lands `anchor_space='render'`; if it defaults to `'source'`, log as a Phase 3b finding |
| 1b | `srcdoc` null-origin blocks direct in-iframe `fetch` to same-door API | Test `postMessage`-to-host bridge as the comment-submit path; record which mechanism works for Phase 3b |
| 1b | No `/update-spec` in the spike | Spec changes (dual-viewer behavior, exploration consumer) deferred to Phase 2b — spike reads spec as constraint only |
| 1b | Throwaway serve must respect GOALS_DIR containment | Reuse `_validate_artifact_path_base` containment if a probe serve is added; no arbitrary-file serve |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `srcdoc` null-origin blocks the in-iframe POST to the same-door API | High (it's the central question) | Test both embed arms; if `srcdoc`, test `postMessage`-to-host bridge; the result *is* the G2 decision, not a blocker |
| No published `refined_requirements.html` exists to probe | Med | Generate one via the existing `GET /goals/{slug}/render` route (writes the file the honest way); use any goal with clean refined requirements |
| Spike scope-creeps into building the real viewer | Med | SCOPE REDUCTION enforced: throwaway probe only; the `macros/markdown_viewer.html` / `api_goals.py` / `api_artifacts.py` seams are **read** for sizing, **modified** in Phase 2b |
| Host CSS bleeds into the render (or vice-versa) breaking isolation | Low | iframe (esp. `srcdoc`) gives document isolation by design; verify with the clashing-rule collision probe; if it somehow leaks, that's a G1 finding |
| Comment row lands `anchor_space='source'` not `'render'` | Med | Verify the landed row; if wrong, it's a concrete Phase 3b fix item (same-door create_comment must stamp render space for render artifacts) — flag, don't patch in the spike |

## Open Questions

- **Direct in-iframe POST vs `postMessage`-to-host bridge** — which mechanism actually persists a
  comment across the iframe boundary under `srcdoc`? **Resolved by Experiment B** — the answer
  picks the Phase 3b submit path. (If `src`/same-origin embed is chosen at G1, direct POST is
  available and this collapses.)
- **Does the same-door `create_comment` stamp `anchor_space='render'` for a render-sourced POST,
  or default to `'source'`?** Probed in Experiment B (inspect the landed row). If it defaults to
  `'source'`, Phase 3b must teach the create path to recognize render artifacts — logged here so
  it isn't lost.
- **`srcdoc` vs `src`-to-route as the Phase 2b embed mechanism** — `srcdoc` matches the spec
  constraint and needs no new serve route, but complicates commenting; `src`-to-route eases
  commenting but adds a serve endpoint + path-validation surface. **G1 records the trade**; the
  final pick is Phase 2b's, informed by G2.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` | US4 (render not an authored artifact; atomic, `served-by` stamp), US7 / FR-012 (selectable units, **no ids/anchors**, quote anchoring), FR-057 / SC-023 (`anchor_space`/`block_ref`, server-resolved render-space anchoring) | None for the spike (read-only probe). Phase 2b will `/update-spec` to add the dual md/html **viewer** behavior + exploration render consumer — out of scope for 1b. |
| `refined_requirements.collab.md` (this goal) | Constraint: "a full standalone HTML doc cannot be inline-injected → **iframe/srcdoc** required"; FR-011/012/013; US7–US10 | The spike validates the iframe/srcdoc Constraint empirically before Phase 2b commits to it. |

## Depends On (from prior plans)

None — Round 1, no prior sub-phase decisions. The spike adopts the spec's pinned names/paths:
`goals/{slug}/refined_requirements.html` (existing render artifact),
`POST /api/goals/{slug}/requirements/comments` (same-door API, `CreateCommentRequest` shape),
`anchor_space='render'` (FR-057), and the `cast-comment-html` layer assets
(`comment-layer.js` / `anchor.js` / `comment-layer.css`).
