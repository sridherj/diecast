# Exploration Pipeline N×M: Sub-phase 3b — Diecast-wide commenting on HTML artifacts

## Overview

Make **any** HTML artifact in the dual viewer annotatable: a text selection inside the
`<iframe srcdoc>` embed (built in 2b) yields a comment that lands in the existing same-door
comment API with `anchor_space='render'`, relocated by verbatim-substring matching via the
already-built `comment_anchor.resolve_render_anchor`. The hard part is **not** new anchoring
machinery — that exists and is proven for requirements. The hard part is two boundary crossings:
(1) `srcdoc` is null-origin, so the comment layer cannot `fetch` the same-door API directly — it
must **postMessage to the host**, which proxies the POST (inherited from 1b); and (2) the server's
render-space resolver is currently **hardwired to `refined_requirements.html`** — to be
artifact-generic it must be told *which served artifact* the quote was minted against. This
sub-phase keeps the capability artifact-generic so Phase 4's `exploration.html` inherits commenting
for free.

## Position in Overall Plan

```
        ┌─ 1a (Workflow spike) ─────────────────────────────────────┐
        │                                              2a ─► 3a ─┐    │
1 spikes ┤                                                       ▼    ▼
        └─ 1b (viewer+comment spike) ─► 2b (dual viewer) ─► [3b HERE] ─► 4 ─► 5
                                                            commenting
```

- **Depends on:** 2b (dual md/html viewer + `<iframe srcdoc sandbox="allow-scripts">` embed + `kind` discriminator) and the **1b decision** (in-iframe postMessage bridge vs full-page fallback).
- **Feeds:** Phase 4's `exploration.html` consumes this commenting capability unchanged; nothing in 3b is exploration-specific.
- **Parallel track:** Track B (1b → 2b → 3b) must land before Phase 4's convergence; it does not block Track A (3a).

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front-matter declares `scope_mode: hold`, and
FR-012 is explicit and bounded: *"verbatim-substring relocation this round; stable anchor-ids
deferred."* The "Out of Scope" section pins the boundary (*"A stable anchor-id scheme for HTML
comments (deferred)"*). So: maximum rigor on the bridge + the artifact-generic resolver seam +
error paths, **zero** scope expansion (no stable ids, no write-back round-trip to exploration md,
no new anchoring algorithm).

## Depends On (from prior plans)

From the decisions ledger and the live code, 3b **consumes** these without re-deciding them:

- **From 1b** — comment-submit crosses the iframe boundary via a **postMessage-to-host bridge**
  (srcdoc is null-origin → direct in-iframe `fetch` to the same-door API is blocked by CORS/origin).
  The comment layer binds `mouseup`/`getSelection` to the iframe's `document.body`. Decision gate:
  if the bridge proves infeasible → **full-page render surface fallback** (serve the artifact on its
  own page like requirements `/render` does today, linked from the viewer). All bridge-shaped
  choices below are marked `[PENDING 1b]` — they are the plan-of-record but yield to the 1b verdict.
- **From 2b** — the embed is `<iframe srcdoc sandbox="allow-scripts allow-popups">` (NO
  `allow-same-origin`; `allow-scripts` is present *precisely* so this sub-phase's comment layer +
  bridge run). The artifact dict carries a `kind` discriminator (`"markdown"`/`"html"`); render-class
  `.html` has `authorship=None` and no edit button. The viewer macro is `macros/markdown_viewer.html`
  with an iframe branch; the `.artifact-html-frame` class wraps it.
- **From the live same-door stack** (already built for requirements, refine-req-v3 sp2):
  - `POST /api/goals/{goal_slug}/requirements/comments` (`api_requirements.py:143`) — the canonical
    dual-assertion handler; `comment_service.create_comment` is the single write path.
  - `create_comment` (`comment_service.py:127`) **already** writes `anchor_space='render'` and
    resolves `block_ref` SERVER-SIDE via `comment_anchor.resolve_render_anchor` against the served
    render HTML. `block_ref=None` for a ref-less container is a **success**, not a miss (Decision #1).
  - `resolve_render_anchor` (`comment_anchor.py:142`) — the single render-space resolver; pure;
    verbatim-substring placement via `container_text_index`; `block_ref` bridge is honest-NULL.
  - The relocate backstop (`api_requirements.py:223`, `_relocate_compare_text`) already routes a
    `'render'`-space comment to the served render's container text.

## The Central Finding (read before detailing)

`comment_service._resolve_served_render_html` (`comment_service.py:70`) is **hardwired** to
`goal_dir / "refined_requirements.html"`. Today, *every* render-space comment anchors against the
requirements render. For Diecast-wide commenting, the server must resolve **the artifact the quote
was actually minted from** (e.g. `exploration/exploration.html`). Therefore the bridge POST must
carry an **artifact identifier**, and the create/relocate/displacement read paths must thread it
through to a generalized `_resolve_served_render_html(goal_slug, artifact_ref)`. This is the load-
bearing seam of 3b. It is purely additive: absent an artifact identifier, the resolver defaults to
`refined_requirements.html` (requirements + all existing comments keep working byte-for-byte).

---

## Sub-phase 3b: Diecast-wide commenting on HTML artifacts

**Outcome:** Selecting text in *any* served HTML artifact in the dual viewer and submitting a
comment persists a row via the same-door API with `anchor_space='render'`, `block_ref` resolved
against **that artifact's** served render (NULL accepted for ref-less containers); the comment
re-anchors correctly by verbatim-substring after a re-render; and the same path works unchanged for
`refined_requirements.html` (consumer #2) and — in Phase 4 — `exploration.html`, with no
exploration-specific code.

**Dependencies:** 2b (viewer + embed + `kind` seam); the 1b decision (bridge vs full-page).

**Estimated effort:** 2–3 sessions.

**Verification:**
- `pytest cast-server` green, including new tests for the artifact-ref-threaded resolver and the
  bridge endpoint (artifact identifier honored; default = requirements, unchanged).
- Manual / browser: open a phase tab with an HTML artifact (use `refined_requirements.html` as the
  stand-in until exploration.html exists), select text, "+ Comment", Submit → a `requirement_comments`
  row exists with `anchor_space='render'` and the artifact's `block_ref` (or honest NULL).
- Re-render the artifact (or hand-edit + re-serve), reload the viewer → the comment shows
  `displaced=False` when its quote survived verbatim, `displaced=True` when it didn't (surfaced, not
  suppressed — per [[feedback_surface_dont_suppress]] discipline already baked into `list_comments`).
- Regression: existing requirements comments (no artifact-ref) still create, list, displace, and
  relocate exactly as before.

### Key activities

**A. Generalize the served-render resolver to be artifact-keyed (the central seam).**
- Extend `comment_service._resolve_served_render_html(goal_slug, db_path, goals_dir)` to accept an
  optional `artifact_ref: str | None`. When `None` → today's `refined_requirements.html` (backward-
  compatible default). When set → resolve a **validated, goal-relative** path under `goal_dir`
  (e.g. `exploration/exploration.html`) and read it; missing file → `""` (degrade, never crash, as
  today).
- Thread `artifact_ref` through the three call sites that read the served render:
  `create_comment` (line ~154), `_resolve_render_compare_text` (line ~98, used by list/displacement
  and relocate), and the source→render migration path (line ~400). Store `artifact_ref` on the
  comment row so displacement/relocate later resolve against the **same** artifact the quote was
  minted from.
- **Persistence:** add a nullable `artifact_ref` column to `requirement_comments` (NULL =
  requirements, the existing default). This is the minimal schema touch that keeps multi-artifact
  comments from cross-anchoring. → **Design review flag below.**
- Naming: `artifact_ref` mirrors the existing `block_ref`/`anchor_space` server-resolved fields;
  it is **server-validated, never trusted from the client beyond path-shape** (same trust boundary
  the docstring states for `block_ref`).

**B. Expose `artifact_ref` on the same-door create endpoint (additive, defaulted).**
- Add an optional `artifact_ref: str | None = None` field to `CreateCommentRequest`
  (`api_requirements.py:45`). Default `None` preserves the requirements contract verbatim.
- Validate it as a goal-relative artifact path (reuse the slug/path-traversal guard already invoked
  by `_require_goal` and the `validate_artifact_path_read` family in `api_artifacts.py` — same-door
  means same validation, no second path validator). Reject `..`, absolute paths, non-`.html`.
- Pass it into `comment_service.create_comment(..., artifact_ref=payload.artifact_ref)`.
- **Do NOT add a new endpoint.** US8/spec convention is *same-door* authoring; this is one new
  optional field on the one canonical handler. (Anti-pattern guard: no parallel comment route.)

**C. Make the injected comment layer artifact-aware + bridge-ready `[PENDING 1b]`.**
- Reuse `cast-comment-html`'s `comment-layer.js` + `anchor.js` (verbatim `context_quote` /
  `uniqueContext` / `chooseOccurrence`) as the in-iframe layer — **do not rewrite anchoring.** The
  `{quoted_text, section_hint, body, prefix, suffix, ordinal}` capture shape is already exactly the
  same-door shape (US9, FR-012).
- The injection point: 2b serves HTML into `srcdoc`. The layer is injected the same way
  `comment_html.build_page` does it — append the `<style>+<script>` block before `</body>` of the
  artifact HTML **as it is placed into `srcdoc`** (server-side, in the viewer's HTML-artifact branch
  of `macros/markdown_viewer.html` / its backing route). The injected `window.__CCH__` config gains
  two fields: `goal_slug` and `artifact_ref` (so the bridge knows where to route the POST).
- **Replace `comment-layer.js`'s `submit()` transport** (currently a direct `fetch(CFG.submit)`).
  Under srcdoc/null-origin a direct fetch is blocked → on Submit, `postMessage` the `{comments[],
  goal_slug, artifact_ref}` payload to the host (`window.parent.postMessage(payload, targetOrigin)`).
  Keep the existing `download()` path as the last-resort fallback (already there).
- `mouseup`/`getSelection` already bind to `document.body` inside the layer — inside `srcdoc` that
  is the iframe's body, which is the intended selection surface (1b confirmed binding target).

**D. Build the host-side postMessage bridge (the boundary crossing) `[PENDING 1b]`.**
- In the host viewer JS (the page embedding the iframe), add a single `message` listener that:
  1. Verifies the message shape + that it came from the artifact iframe (guard the event source;
     `srcdoc` frames post with a `null` origin — match on the specific iframe `contentWindow`, not on
     origin string, since null-origin can't be allow-listed by URL).
  2. For each comment in the payload, issues the same-door `POST
     /api/goals/{goal_slug}/requirements/comments` with `{quoted_text, section_hint, body,
     artifact_ref, author_kind:"human"}` (the host IS same-origin to cast-server → the fetch is
     permitted). HTMX or plain `fetch` — match the viewer's existing convention.
  3. postMessages the per-comment result (201 row id, or error) back into the iframe so the layer can
     toast success/failure — **surface failures, never silently drop** ([[feedback_surface_dont_suppress]]).
- **Contract (name it explicitly in the ledger):** message type `cch:submit` host-bound carries
  `{type:"cch:submit", goal_slug, artifact_ref, comments:[...]}`; reply type `cch:submitted` carries
  `{type:"cch:submitted", ok, results:[{id|error}]}`.
- Per-comment POST (not a batch endpoint) — the same-door create handler is per-comment; the bridge
  loops. Keeps the server contract untouched.

**E. Verbatim-substring relocation — reuse, do not rebuild.**
- Relocation/re-anchor is **already** `resolve_render_anchor` server-side at create time, plus the
  client-side `findAndWrap`/`chooseOccurrence` on reload (re-highlights surviving quotes by verbatim
  context). For 3b the only change is that both must run against **this artifact's** served render
  (Activity A threads `artifact_ref`).
- Accept `block_ref=None` for ref-less containers as success (Decision #1 — already implemented in
  `resolve_render_anchor`; exploration HTML may well be ref-less this round since stable anchor-ids
  are deferred). No `_ID_RE` change, no anchor-id scheme — explicitly out of scope.
- The relocate endpoint's backstop (`_relocate_compare_text`) already picks render-space text for a
  `'render'` comment; once it resolves via the artifact-keyed resolver (A), relocation validates
  against the right artifact automatically.

**F. Honor the 1b full-page fallback if the bridge is infeasible `[PENDING 1b]`.**
- If 1b concluded the postMessage bridge does not work (e.g. selection/highlight breaks across the
  sandbox, or `srcdoc` strips the layer): fall back to serving the artifact on a **full-page render
  surface** (the proven `cast-comment-html` serve path, mirroring requirements `/render` today),
  with the dual viewer rendering the artifact read-only and **linking out** to the commentable
  full-page surface. The same-door API + artifact-keyed resolver (A, B, E) are **identical** in both
  branches — only C/D (in-iframe injection + bridge) are swapped for a standalone serve. This keeps
  the fallback cheap and the server contract single.

**G. Spec update.**
- `/cast-update-spec` on `docs/specs/cast-requirements-render.collab.md`: extend US7/US8 to state the
  render-space comment anchor is **artifact-keyed** (not requirements-only); record that
  verbatim-substring relocation + honest-NULL `block_ref` generalize to any served `.html`; note the
  same-door endpoint gains an optional `artifact_ref`. Verify the diff before applying; do not touch
  the US4/US7 "render not authored artifact" + "selectable units, no ids" contracts (they hold
  as-is). **Verify output.**
- `cast-requirements-roundtrip.collab.md` is **reference only** — confirm the plan adds NO write-back
  round-trip to exploration md (comments on exploration HTML are feedback-only; out of scope per the
  requirements doc).

### Design review

- **⚠️ Architecture (load-bearing): served-render resolver is requirements-hardwired.**
  `comment_service.py:70` reads only `refined_requirements.html`. Without Activity A's `artifact_ref`
  threading, comments on `exploration.html` would silently anchor against the requirements render
  (wrong document, garbage `block_ref`, false displacement). → Activity A makes the resolver
  artifact-keyed; default-`None` preserves requirements behavior. **Add regression tests asserting the
  default path is byte-identical to today.**
- **⚠️ Schema: new `artifact_ref` column on `requirement_comments`.** A migration touches a table
  the requirements feature owns. Mitigate: nullable column, NULL = requirements (the existing
  meaning), additive only; no backfill needed. Confirm the migration runner pattern this repo uses
  before writing it (read an existing migration first).
- **⚠️ Security: artifact path traversal via the bridge POST.** `artifact_ref` arrives from the
  client. It MUST be validated server-side as goal-relative, `.html`-only, no `..`/absolute — reuse
  the existing `validate_artifact_path_read` guard (`api_artifacts.py`), do NOT hand-roll a second
  validator. `block_ref`/`anchor_space` stay server-resolved (never client-trusted), unchanged.
- **⚠️ Security: postMessage origin.** `srcdoc` frames are null-origin → cannot allow-list by URL.
  Match the event `source` against the specific artifact-iframe `contentWindow` reference, and
  validate the payload shape, before issuing any POST. Never echo arbitrary postMessage data into a
  fetch without shape-checking.
- **Error paths (surface, don't suppress):** bridge POST 422 (quote not a verbatim substring of the
  served render) and 5xx must round-trip back into the iframe as a visible toast; the comment stays
  in the layer's local list (not lost). Mirrors `comment-layer.js`'s existing
  download-on-failure + toast. A failed single comment in a batch does not abort the others.
- **Naming:** `artifact_ref` follows the established `block_ref`/`anchor_space` server-field
  convention ✓. postMessage types `cch:submit`/`cch:submitted` namespace under the existing `cch`
  (cast-comment-html) prefix ✓.
- **Spec consistency:** same-door (one endpoint, one write path) preserved — only an optional field
  is added, no parallel route (US8 honored) ✓. "Selectable units, no ids" (US7) preserved — no
  anchor-id scheme introduced ✓.

## Build Order (within 3b)

```
A (artifact-keyed resolver + schema) ──► B (endpoint field) ──┐
                                                              ├──► E (relocation threads artifact_ref) ──► G (spec)
C (artifact-aware layer) ──► D (host bridge) ─────────────────┘
                              │
                              └─[PENDING 1b: if infeasible]─► F (full-page fallback; A/B/E unchanged)
```

**Critical path:** A → B → D → E → G. A is the keystone (everything render-space depends on it);
do A first. C/D can proceed in parallel with A/B once the `cch:submit` contract (Activity D) is
pinned.

## Design Review Flags

| Flag | Action |
|------|--------|
| Served-render resolver hardwired to `refined_requirements.html` → wrong-document anchoring for non-requirements artifacts | Activity A: artifact-keyed resolver, default `None`=requirements; regression tests assert default is unchanged |
| New `artifact_ref` column on `requirement_comments` (requirements-owned table) | Nullable, additive, NULL=requirements; read an existing migration first; no backfill |
| `artifact_ref` is client-supplied → path traversal | Server-validate via existing `validate_artifact_path_read`; `.html`-only, goal-relative, no `..` |
| postMessage from null-origin srcdoc cannot be origin-allow-listed | Match event `source` to the specific iframe `contentWindow`; shape-check payload before any POST |
| Bridge POST failures (422 verbatim miss / 5xx) could vanish across the iframe boundary | Round-trip `cch:submitted` result into the iframe → visible toast; keep comment in local list; per-comment failures don't abort the batch |
| Spec drift: render-space comments generalize beyond requirements | `/cast-update-spec` on `cast-requirements-render.collab.md` (US7/US8); preserve US4/US7 contracts |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 1b verdict is "bridge infeasible" → in-iframe commenting can't ship | Med | Activity F: full-page fallback reuses the proven `cast-comment-html` serve; A/B/E (server contract) unchanged, so the pivot is cheap and isolated to C/D |
| Artifact-keyed resolver regresses existing requirements comments | High | Default `artifact_ref=None`→requirements; explicit byte-identical regression tests on the default path before touching exploration |
| Ref-less `exploration.html` (no anchor ids this round) yields all-NULL `block_ref`, perceived as "broken" | Low | Decision #1 is explicit: ref-less NULL is SUCCESS, not a miss; `displaced` (verbatim presence) is the real health signal, independent of `block_ref` |
| Migration on a shared table breaks requirements feature | Med | Nullable additive column, no backfill; follow the repo's existing migration pattern (read one first); run full `pytest cast-server` |
| Selection/highlight breaks inside the sandboxed srcdoc (layout collapse) | Med | The layout-preserving per-text-node `wrapRange` is already in `comment-layer.js` (recent fix, commit 5d7ef83); reuse as-is, don't reintroduce wholesale-range wrapping |

## Open Questions

- **[PENDING 1b] Bridge vs full-page** — does the postMessage bridge actually carry a
  selection→comment POST across the `srcdoc` null-origin boundary, or does 3b ship the full-page
  fallback (Activity F)? This is the single gating unknown; the 1b spike resolves it. The plan-of-
  record is the bridge; A/B/E are identical either way.
- **`artifact_ref` granularity** — is a goal-relative path (`exploration/exploration.html`) the right
  identifier, or should it be a logical artifact id? Leaning **path** (it is what the server reads off
  disk and what the viewer already globs in 2b's `kind` seam) — confirm against the 2b artifact-dict
  shape during execution. Does not change the API surface (still one string field).
- **Re-render relocation trigger** — for requirements, source→render migration runs on version
  snapshot. For exploration HTML there is no version table this round; relocation is purely the
  reload-time client `findAndWrap` + the relocate endpoint on demand. Confirm no version-snapshot
  coupling is assumed for non-requirements artifacts (it shouldn't be — `create_comment` stamps
  `version=0` when none exists).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` | US7 (selectable units, no ids; anchor_space='render' against published-render container text), US8 (same-door comment authoring), US4 (render not authored artifact) | 1 — render-space comments generalize from requirements-only to any served `.html`; resolve via `/cast-update-spec` (Activity G). US4/US7 DOM contracts unchanged. |
| `cast-requirements-roundtrip.collab.md` | Same-door intake (reference only) | None — NO write-back round-trip to exploration md added (out of scope; comments are feedback-only). |

## Suggested Revisions to Prior Sub-Phases

None required. 1b and 2b decisions are consumed as-is. One **forward note for Phase 4**: when
`exploration.html` is built, it should be served by the same artifact-keyed resolver path (Activity
A) and (optionally) embed labeled-unit containers if cheap — but per "Out of Scope" and Decision #1,
ref-less is acceptable this round and `block_ref=None` is honest success; Phase 4 need not add anchor
ids to get working comments.
```

## Plan Review Decisions (2026-06-20)

- **Issue #3 (Architecture / Security) — Decision: A3 A (accepted).** Maintain an **iframe registry** (`artifact_ref → contentWindow`); validate inbound postMessage `event.source` against the registry; reply with `postMessage(payload, "*")` to the **originating contentWindow only**; explicitly handle multiple commentable iframes per tab (e.g. `exploration.html` + `refined_requirements.html`).
- **Issue #5 (Tests) — Decision: T1 A+B (accepted).** The bridge must not be manual-only. Add (A) a **jsdom/DOM unit test** for the host bridge listener — foreign-window rejection, payload shape-check, per-comment POST fan-out, `cch:submit`/`cch:submitted` round-trip — and (B) a **server test** asserting the proxied POST body matches `CreateCommentRequest` (with `artifact_ref`). Autonomous runs can't drive Chrome, so the bridge needs CI coverage independent of a real browser.
