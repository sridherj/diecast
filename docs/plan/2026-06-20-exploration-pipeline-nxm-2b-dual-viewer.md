# Exploration Pipeline N×M: Phase 2b — Dual md/html Artifact Viewer (general capability)

## Overview

Phase 2b makes the Diecast phase-tab artifact viewer render `.html` artifacts (via
`<iframe srcdoc>`) alongside the `.md` it already renders, treats `.html` as a **render-class**
artifact per `cast-requirements-render` US4, and proves the capability against a real producer by
surfacing the existing refined-requirements HTML in-viewer (consumer #2, US10/US13). This is the
**horizontal Track B foundation**: it ships independent of the Workflow engine, validated against an
artifact that already exists today. The extended viewer seam defined here — how `.html` is *detected*,
*served*, and *rendered* — is the exact interface that **Phase 3b (in-iframe commenting)** and
**Phase 4 (exploration render)** consume, so it is specified precisely below.

Key insight from the decisions ledger (Round 1, 1b spike): embed via **`<iframe srcdoc>`** (null-origin
sandbox, no `<head>/<style>` collision with the host page). The null-origin choice has a downstream
consequence Phase 3b must own — direct in-iframe `fetch` to the same-door API is blocked, so commenting
goes through a **postMessage-to-host bridge**. Phase 2b builds the *render* half cleanly and leaves a
deliberate, documented seam for that bridge; it does **not** wire commenting.

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` frontmatter declares `scope_mode: hold`, and the
requirements use balanced, exact language ("renders `.html` (iframe/srcdoc) alongside `.md`";
"extended to allow `.html`"). The discipline here: build exactly the dual-viewer *render* capability +
consumer #2 + the spec update — no commenting (that is Phase 3b), no exploration render (Phase 4), no
stable anchor-ids (deferred per spec Out of Scope). Every activity must pass "is this needed for the md
*or* html artifact to render correctly in the phase tab, without regressing today's md path?"

## Position in Overall Plan

```
Phase 1b (spike: viewer+comment) ─► Phase 2b (THIS) ─► Phase 3b (commenting) ─► Phase 4 (exploration render)
                                          │
                                          └─► (also unblocks Phase 4's "render visible in viewer" leg)
```

Phase 2b is on **Track B**, depends only on the **Phase 1b spike decision** (srcdoc embed validated),
and must land before Phase 4's A+B convergence. It runs in parallel with Track A (2a/3a).

## Depends On (from prior plans)

From the **Round 1 / 1b spike** (`docs/plan/2026-06-20-exploration-pipeline-nxm-1b-spike-viewer-commenting.md`,
recorded in the decisions ledger):

- **Embed mechanism = `<iframe srcdoc>`** (null-origin sandbox; spec-aligned; no head/style collision).
  Phase 2b adopts this verbatim. `[PENDING 1b spike outcome]` — if the spike found srcdoc breaks page
  layout or a same-origin `<iframe src>` serve endpoint was preferred, see "Open Questions" for the swap.
- **Comment-submit = postMessage-to-host bridge** (null-origin blocks direct fetch). Phase 2b does NOT
  implement this, but the iframe `sandbox` attribute it sets MUST permit `allow-scripts` so Phase 3b's
  injected layer + postMessage can run. This is the single forward-looking constraint Phase 2b honors.
- **Decision gate → Phase 3b:** in-iframe commenting works → in-viewer commenting; else full-page
  fallback. Phase 2b is agnostic to that outcome — it renders either way.
- **Viewer seam touchpoints (named by 1b):** `api_artifacts.py:52` gate, `api_goals.py get_phase_tab`
  glob + `render_md` branch, `macros/markdown_viewer.html`. These are exactly the files 2b edits.

## The Extended Viewer Seam (KEY INTERFACE — consumed by Phase 3b & Phase 4)

This is the contract Phase 3b and Phase 4 build on. Specify and name it precisely; downstream phases
adopt these names verbatim.

**Artifact dict shape (extended).** Today `get_phase_tab` builds artifact dicts of
`{name, path, html, authorship}` (see `api_goals.py:407`). Phase 2b adds one discriminator field:

```
{
  "name": str,
  "path": str,
  "authorship": str | None,   # None for render-class .html (US4: no .human/.ai/.collab suffix)
  "kind": "markdown" | "html", # NEW — the render dispatcher key
  "html": str,                 # markdown→HTML (kind="markdown") OR verbatim file bytes (kind="html")
}
```

- `kind` is derived from the file extension at collection time (`.html` → `"html"`, `.md` → `"markdown"`).
  Naming: `kind` (not `type`/`format`) — short, matches the dispatcher's role and avoids the Python
  builtin shadow.
- For `kind="html"` the `html` field carries the **verbatim file contents** (NOT `md.markdown()`-processed).
  This is the load-bearing change: a full standalone HTML doc has its own `<head>/<style>` and must be
  passed through untouched into `srcdoc`.

**Render dispatch (template).** `macros/markdown_viewer.html` gains a `kind` parameter on
`artifact_content`; `phase_tab_content.html` passes `artifact.kind`. The macro branches:
- `kind == "markdown"` → today's `<div class="artifact-content markdown-body">{{ html|safe }}</div>` (UNCHANGED).
- `kind == "html"` → `<iframe class="artifact-html-frame" sandbox="allow-scripts allow-popups"
  srcdoc="{{ html|e }}">`. The `srcdoc` value is HTML-attribute-escaped by Jinja's `|e`; the browser
  un-escapes it into a null-origin document. `sandbox` omits `allow-same-origin` (this IS the null
  origin) but includes `allow-scripts` so Phase 3b's bridge can run.

**Detection / serving (routes).** Two gates extended, both keyed off extension:
- `api_artifacts.py` `validate_artifact_path_read` (line 55): the `.md`-only check is widened to admit
  `.html` for **reading** (editing stays `.md`-only — `.html` renders are read-only per US4).
- `api_goals.py` `get_phase_tab` glob (line 422 / 427): the per-directory `glob("*.md")` is widened to
  also collect `*.html`, dispatching to a new `_add_html_file()` collector alongside `_add_md_file()`.

**Render-class semantics (US4 applied to `.html`).** Any `.html` artifact is treated as render-class:
read-only (no edit button — `authorship=None` already suppresses it in `artifact_header`), exempt from
the authorship-suffix convention, and (for producers) written atomically with a `served-by`/generated-by
stamp. Phase 2b does not *produce* HTML (Phase 4 does), but it *classifies* it so the viewer never
offers an edit affordance on a render.

## Key activities

1. **Extend the read gate to admit `.html` (`api_artifacts.py`).**
   - Widen `validate_artifact_path_read` (line 55) from `.md`-only to accept `.html` as well. Keep
     `validate_artifact_path` (the EDIT gate, line 47) **unchanged** — `.html` renders are read-only.
   - The `artifact_sidebar` route reads via `validate_artifact_path_read` then unconditionally runs
     `md.markdown()` (line 136) — add a branch: if the resolved file is `.html`, pass contents verbatim
     and tag the sidebar context with `kind="html"` so the sidebar template can also iframe it (keeps
     the sidebar and phase-tab consistent; cheap, same seam).
   - Path-traversal protection is already provided by `_validate_artifact_path_base` (resolve +
     `is_relative_to` GOALS_DIR / external_project_dir) — **reused unchanged**, applies to `.html` for free.

2. **Extend the phase-tab glob + add the HTML collector (`api_goals.py` `get_phase_tab`).**
   - In the directory branch (line 422–428), after the `glob("*.md")` loops, add parallel
     `glob("*.html")` loops (top-level and per-subdir) calling a new `_add_html_file(f, section="")`.
   - In the single-file branch (line 430) admit `*.html` patterns too (forward-compat for Phase 4's
     `exploration/exploration.html` and for `refined_requirements.html`).
   - `_add_html_file` mirrors `_add_md_file` but: reads the file verbatim into `html` (NO `render_md`),
     sets `kind="html"`, sets `authorship=None` (render-class, US4 — `extract_authorship` returns None
     for non-suffixed names anyway, but set explicitly for clarity), labels from `f.stem`.
   - `_add_md_file` sets `kind="markdown"` on its dict (the only change to the existing collector).
   - Ordering note: collect `.html` *after* `.md` per directory so a phase tab with both shows md first
     then the rendered html (deterministic, matches "shows both" verification). Document this ordering
     as the contract Phase 4 relies on (exploration md notes/playbooks above, `exploration.html` below —
     or adjust if Phase 4 wants the render first; flag in Open Questions).

3. **Add the iframe/srcdoc render branch (`macros/markdown_viewer.html`).**
   - Add a `kind="markdown"` default param to `artifact_content(html, kind="markdown")`.
   - Branch: `markdown` → existing div (untouched, regression-safe by default param); `html` →
     `<iframe class="artifact-html-frame" sandbox="allow-scripts allow-popups" srcdoc="{{ html|e }}"
     loading="lazy">`. Give the iframe a sensible default height + `style="width:100%;border:0"`;
     a small inline resize script (postMessage height handshake) is **deferred to Phase 3b** (it owns the
     bridge) — for 2b use a generous min-height + scroll, or a one-line `onload` height-fit script.
   - Update the one call site: `phase_tab_content.html:69` →
     `{{ artifact_content(artifact.html, artifact.kind) }}`.
   - Add minimal `.artifact-html-frame` CSS (full-width, no border, block display) to the viewer
     stylesheet so the iframe doesn't collapse.

4. **Wire `PHASE_ARTIFACTS` so the requirements HTML is collected in-viewer (consumer #2, US10/US13).**
   - `refined_requirements.html` lands at `goals/{slug}/refined_requirements.html` (produced today by
     `render_job_service` / `requirements_render_service`, served via `/goals/{slug}/render`). Add it to
     `PHASE_ARTIFACTS["requirements"]` (`config.py:55`) as a single-file `.html` pattern so the
     requirements phase tab surfaces it via the new `_add_html_file` path — **without** removing the
     existing `/render` route (US10 generalizes the surface; it does not retire the page).
   - `[PENDING]` confirm at implementation: the requirements HTML is written eagerly to disk on render
     (it is — `_atomic_write(html_path, ...)` in `requirements_render_service`), so a goal that has been
     rendered once will have the file present for the glob. If absent (never rendered), the glob simply
     finds nothing — graceful, no error. Note this is a *lazy* surface: it appears once `/render` (or a
     render job) has produced the file. Acceptable for 2b validation; do not add a render-trigger here.

5. **Regression-guard the markdown path.**
   - Add/extend a viewer test asserting a phase tab with **only** `.md` artifacts renders byte-identically
     to today (the `kind="markdown"` default param makes this true by construction — assert it).
   - Add a test for a phase tab with **both** a `.md` and a `.html` artifact: the md renders in a
     `markdown-body` div, the html renders inside an `<iframe srcdoc=...>` whose decoded content equals
     the file bytes verbatim, and the html artifact has **no edit button** (render-class).
   - Add a test that `validate_artifact_path_read` accepts `.html` and `validate_artifact_path` (edit)
     still rejects it (read-only guard).
   - Manual check (no autonomous browser per memory — static verdict + human-eyeball carry-forward):
     load a real `refined_requirements.html` into the requirements phase tab; confirm no `<head>/<style>`
     collision with the host page (the whole point of srcdoc) and the requirements render is legible.

6. **`/update-spec` on `cast-requirements-render.collab.md` (delegate).**
   - **→ Delegate: `/cast-update-spec`** on `docs/specs/cast-requirements-render.collab.md` with this
     change brief:
     - **Add** dual md/html **viewer** behavior: the phase-tab artifact viewer now renders `.html`
       render-class artifacts via `<iframe srcdoc>` (null-origin sandbox) alongside `.md`; the
       `.md`-only read gate (`api_artifacts.py`) and phase-tab globs (`api_goals.py`) are extended to
       admit `.html`; the `kind` discriminator + `_add_html_file` collector are the seam.
     - **Add** the **exploration render consumer** as a forward pointer: exploration is render consumer #1
       (Phase 4 produces `exploration/exploration.html`); refined-requirements is consumer #2, now
       reachable in the dual viewer (US10/US13/FR-013), not only on `/render`.
     - **Preserve / cite (do NOT change):** US4 "render not authored artifact" (atomic write,
       generated-by/`served-by` stamp, read-only, no authorship suffix) — now applied to ALL render-class
       `.html` in the viewer; and **US7 "selectable units, no ids"** — the DOM contract carried forward to
       rendered HTML so Phase 3b's verbatim-substring anchoring (and the existing `anchor_space='render'`
       path in `comment_anchor.py`) keeps working. The spec must state US4/US7 are reused, not superseded.
     - **Out of scope to add** (state explicitly so the spec doesn't over-claim): in-iframe commenting
       (Phase 3b) and the exploration render pipeline (Phase 4) — 2b ships the *viewer render* only.
   - `cast-update-spec` shows a diff and waits for the user's approval, auto-bumps version/date, and
     should register/refresh the entry in `docs/specs/_registry.md`. **Verify output:** confirm the diff
     adds viewer behavior + consumer pointer, leaves US4/US7 acceptance scenarios intact, and the version
     bumped. Optionally run **`/cast-spec-checker`** on the result to lint shape.

## Verification

- A phase tab containing both a `.md` and a `.html` artifact renders both — md as today, html inside an
  `<iframe srcdoc>` — confirmed by the dual-artifact test (activity 5) and a manual eyeball.
- `refined_requirements.html` appears in the **requirements phase tab** (consumer #2), not only on
  `/goals/{slug}/render` — manual check on a goal that has been rendered (US10/SC-008).
- The `.html` artifact shows **no edit button** (render-class, US4) — asserted in test.
- The md-only viewer path is **unchanged** (default-param + byte-identical regression test) — the
  Phase-2b risk "extending the viewer regresses existing md rendering" is closed.
- `validate_artifact_path_read` admits `.html`; the edit gate still rejects it — asserted in test.
- `/cast-update-spec` diff approved: viewer behavior + exploration-consumer pointer added; US4/US7
  preserved; version bumped; registry refreshed.

## Design Review Flags

| Flag | When | Action |
|------|------|--------|
| **Spec consistency** — adding the dual-viewer is NEW behavior on a spec'd pipeline (today HTML serves only on `/render`) | Always | `/update-spec` on `cast-requirements-render` is a first-class activity (#6), not a bullet. Must preserve US4 + US7. |
| **Security — srcdoc XSS / null-origin** | iframe render of arbitrary HTML | `sandbox` WITHOUT `allow-same-origin` keeps the frame null-origin (can't read host cookies/DOM). Only render-class `.html` produced by trusted maker pipelines is admitted — the read gate + path validation (`_validate_artifact_path_base`) prevent arbitrary file paths. Do NOT add `allow-same-origin` (would defeat the isolation the spec relies on). |
| **Security — path traversal** | `.html` now readable | Reused unchanged from `_validate_artifact_path_base` (resolve + `is_relative_to`). No new surface — same guard that protects `.md`. |
| **Naming** — new discriminator field | artifact dict + macro param | `kind` (values `"markdown"`/`"html"`), `_add_html_file` collector mirroring `_add_md_file`, `.artifact-html-frame` class. Mirrors existing `_add_md_file`/`render_md` patterns ✓ |
| **Architecture** — render dispatch lives in the template macro | iframe branch | Keeps the route thin (it only sets `kind` + verbatim bytes); presentation logic stays in `markdown_viewer.html` ✓ matches the existing macro-owns-rendering pattern. |
| **Forward-compat — Phase 3b bridge** | sandbox attr | `allow-scripts` MUST be present so Phase 3b's postMessage comment bridge can run; do not ship a script-less sandbox. Flagged so 3b isn't blocked by a too-tight 2b sandbox. |
| **Surface, don't suppress** (memory) | requirements html absent | If `refined_requirements.html` doesn't exist yet, the glob finds nothing — graceful empty, not an error. No silent fallback that hides "not yet rendered"; the `/render` route still owns generation. |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Extending the viewer regresses today's md rendering | Med | `kind="markdown"` default param → md call sites unchanged; byte-identical md regression test (activity 5). |
| `srcdoc` value escaping breaks on real requirements HTML (quotes/entities) | Med | Jinja `|e` HTML-attribute-escapes the whole doc into `srcdoc`; browser un-escapes. Test decodes srcdoc and asserts byte-equality with the file. If a pathological doc breaks, fallback `[PENDING 1b]` = same-origin `<iframe src>` serve endpoint (ledger alt). |
| `allow-scripts` in sandbox = script execution in render-class HTML | Med | Acceptable + required for Phase 3b; mitigated by NO `allow-same-origin` (null origin can't touch host) and admitting only trusted maker-produced renders via the read gate. |
| iframe height/scroll UX (no auto-resize until 3b) | Low | 2b uses generous min-height + internal scroll or a one-line onload height-fit; full postMessage resize handshake deferred to Phase 3b (it owns the bridge). |
| Requirements HTML surfaced in-viewer diverges from `/render` (two surfaces, one artifact) | Low | Same file, same bytes — the viewer iframes the on-disk `refined_requirements.html`; `/render` keeps its generation/poll logic. No duplication of render logic. |

## Open Questions

- **`[PENDING 1b spike outcome]` — srcdoc vs same-origin serve endpoint.** Plan assumes the 1b spike
  validated `<iframe srcdoc>` (per ledger). If the spike instead found srcdoc collides with host layout or
  that a same-origin `<iframe src>` (a `/goals/{slug}/artifact/{path}` serve route) was needed for the
  comment fetch, swap activity 3's branch to `src` + add the serve route. The artifact-dict `kind` seam is
  unaffected either way. Resolve by reading the 1b spike plan's decision gate before implementing.
- **Artifact ordering in the phase tab** — should the rendered `.html` appear *above* or *below* the
  source `.md` artifacts? 2b proposes md-first, html-after (deterministic). Phase 4 may want
  `exploration.html` first (it's the marquee surface). Leaning: keep md-first for 2b; let Phase 4 set its
  own ordering when it produces the render. Confirm with the user if it matters for the requirements tab.
- **Sidebar parity scope** — activity 1 extends the task `artifact_sidebar` to iframe `.html` too. Is the
  sidebar an in-scope consumer for 2b, or phase-tab-only? Leaning: include it (same seam, cheap, keeps the
  two viewers consistent); cut if HOLD SCOPE wants the absolute minimum (phase tab is the US8-named surface).

## Spec References

| Spec | Sections Referenced | Conflicts / Action |
|------|---------------------|--------------------|
| `cast-requirements-render.collab.md` | US4 (render not authored artifact — atomic, served-by stamp, read-only, no authorship suffix), US7 (selectable units, **no ids/anchors**), US8 (same-door comment, `anchor_space='render'`), US10/FR-013 (render consumer) | **1 — NEW viewer behavior.** `/update-spec` (activity 6) ADDS the dual md/html viewer + exploration-consumer pointer; PRESERVES US4 + US7 verbatim (applied to rendered HTML). Comment bridge (US8) is referenced as the Phase-3b consumer of this seam, not built here. |
| `cast-requirements-roundtrip.collab.md` | same-door comment intake (reference only) | None — commenting is Phase 3b. |
```

## Plan Review Decisions (2026-06-20)

- **Issue #6 (Tests) — Decision: T2 A (accepted).** Add an **adversarial fixture** to the srcdoc escape test: an HTML doc containing `</script>`, `"`/`'`/backtick, `&`, and a render-comment marker; assert the `srcdoc` value round-trips **byte-exact** AND the iframe DOM parses exactly one `<script>`. The benign byte-equality test alone is insufficient (2b's own risk table flags srcdoc-escaping breakage as Med).
