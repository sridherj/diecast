# Sub-phase 3.1 — Borderline Calls & Documented Decisions

> Full-autonomy mode: at every judgment gate, pick the recommended option and document it.
> This file records the non-obvious calls made while executing `sp1_feature_backbone/plan.md`.

## 1. E1 illustration delegation — NOT dispatched (allowlist constraint) → rasters generated directly

**The plan (Step 3.1.5)** says to dispatch `/cast-preso-illustration-creator` + `-checker` to produce
the E1 raster screenshots. **However, this runner's `allowed_delegations` is strictly
`[cast-review-code]`** (per the delegation context). `/cast-preso-illustration-creator` and
`-checker` are **not** in the allowlist, so an HTTP dispatch would be denied (422), and the binding
rule forbids falling back to the Agent tool for HTTP-dispatched targets.

**Decision (recommended path under full autonomy):** generate the E1 raster directly via **headless
Chrome** (`google-chrome --headless --screenshot`) from an on-brand HTML mock built with the locked
Diecast light-world tokens (cream / ink / raspberry / ok-green; IBM Plex Mono + DM Sans; **no
glass / gradient / glow**). Output: `prototype/assets/e1-acceptance.png` (the exact path the frozen
spine references). This honors BINDING #2 (relative `<img>` from `file://`) and the E1 error-path
rule, and keeps the deliverable self-contained. The image is a 3-panel composite (checkout
**before RBAC · after RBAC · denied/403**) — a credible acceptance-evidence screenshot.

**Verified live:** the real raster loads from both `file://` (headless) and `http://` (Chrome
plugin); the `onerror` fallback to the 2b CSS/SVG thumbnail fires correctly when the asset is
missing (tested by temporarily hiding the file), showing a visible thumbnail + an "image
unavailable, showing thumbnail" caption — never a broken-image icon.

## 2. E1 shot count — ONE raster, not 2–3 (frozen-spine fidelity beats a soft numeric target)

The plan's prose mentions "2–3 fake checkout screenshots." The **frozen** `ORG.goals['CAST-412'].
evidence.E1.shots` (authored in 2a, FREEZE) carries **exactly one** shot ref
(`assets/e1-acceptance.png`). Adding more shots would **mutate frozen E1 data**, violating
BINDING #3 (additive keys only) and #4 (section-stability). The binary success criterion only
requires "real rasters **or** `onerror` fallback; PR link only" — it does not mandate a count.

**Decision:** honor the freeze. Render exactly the one shot the spine provides, made a rich
**composite** (3 checkout states in one image) so the "2–3 screenshots" *intent* is met visually
without touching frozen data. `EvShot` renders any/all `shots[]` the spine carries, so if a later
(sanctioned) generator edit adds shots, the panel grows with zero component change.

## 3. Live verification used HTTP, not `file://` (Chrome plugin limitation)

The Claude-in-Chrome `navigate` tool forces an `https://` prefix and cannot load `file://` URLs.
**Decision:** served the prototype over a throwaway local `python3 -m http.server` (127.0.0.1:8777)
for the interactive click-through. The prototype is `file://`-designed (verified separately with
headless Chrome over `file://`), and HTTP is a strict superset (classic `<script src>`, relative
`<img>`, https CDN imports all work identically) — so HTTP verification is valid and was used only
to drive the live click-through. Server stopped after verification.

## 4. `drillInto` argument grammar (reused op, no sixth op)

Stage navigation reuses `drillInto` (BINDING #6 — closed 5-op set). The dispatcher's `drillInto(arg)`
branches: `arg === 'execution'` → the HOW drill-in panel (3.2); `arg === '<step-id>'` →
`appState.stageFocus`. Re-clicking the focused step, or clicking the current step while at default,
returns to the default view. Documented next to the OPS table and in `drillInto()`.

## 5. `stageFocus` resets on goal switch (intentional)

`syncGoalFromRoute` clears `appState.stageFocus` when the goal id changes (a feature step id is
meaningless under another family's spine). The plan's "back/forward and re-render preserve
stageFocus" holds *within a goal*. PRF2's per-goal **chat thread** (messages + scenario position) is
what persists across goal switches — verified live.
