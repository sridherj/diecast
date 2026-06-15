# Web Research: Annotation & Iteration — Comments, Versions, Change-Summaries, and the React Question (Step 4)

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement.
Step 4 designs the iteration engine: inline comments/annotations (Google-Docs-style, anchored to
requirement elements), the open/resolved lifecycle with a retained resolution trail (FR-009/FR-010),
version progression where unresolved comments drive v2/v3 (US4/US5), per-version change summaries
that diff stable-ID elements (FR-017), and the agent-parity contract so an agent comments/resolves/
versions through the **same door** as a human (FR-013). **Central kill-or-confirm:** does this require
migrating off FastAPI+Jinja+HTMX to React/Next.js, or do element-anchored comments on stable IDs (and/or
vanilla-JS annotation libraries) suffice on the existing stack?

**Date:** 2026-06-11
**Researcher angle:** cast-web-researcher (7 expert lenses)
**Hard dependency consumed:** Step 2 canonical-store note
(`exploration/research/02-canonical-source-of-truth-code.ai.md`) — its findings about *stable element
identity* are the keystone this entire step rests on, and they materially change the answer below.

---

## TL;DR — The Verdict (for the synthesizer)

1. **React/Next.js is NOT required. Confirmed, with high confidence, on three independent legs.**
   - **(a) The hardest part of "Google-Docs-style comments" — robust text anchoring — disappears if you
     have stable element IDs.** Step 2's recommendation (a `spec_elements` table with a persisted
     surrogate per US/FR/SC) gives you exactly that. Comments then anchor to a *durable row key*, not a
     fragile character range. This is element-level commenting, not character-level — and element-level
     is the correct granularity for requirements review anyway (you comment on "FR-014", not on the word
     "router" inside it).
   - **(b) Even if you wanted character-level highlighting, the mature libraries that do it are vanilla
     JS, not React.** RecogitoJS, Annotorious, `@recogito/text-annotator`, and the Hypothesis client all
     run as plain JS against arbitrary HTML; React wrappers are *optional add-ons*, never required.
   - **(c) The only thing that genuinely forces React/CRDT/OT is realtime multi-user co-editing — which
     the spec explicitly puts OUT OF SCOPE** (single-writer, async). Removing co-editing removes the one
     requirement that justifies an SPA rewrite. The remaining surface (post a comment, list comments,
     toggle resolved, render a diff) is a textbook HTMX server-rendered CRUD feature.

2. **Recommended approach: element-anchored comments as DB rows keyed to Step 2's element surrogate,
   served and mutated through HTMX fragments — NOT a third-party annotation library.** The libraries
   solve a problem (anchoring free-text selections in unstructured prose) that Step 2's architecture
   designs away. Adopting one would re-introduce text-anchor fragility you already paid to eliminate.
   Reserve the library option only for a possible future "comment on a sub-span *within* an element"
   nicety, and even then prefer the W3C selector *data model* over the library's UI.

3. **Model the comment/version system on the W3C Web Annotation Data Model + Protocol and the GitHub
   PR-review-comment model — not on Google Docs.** Both give you the two things FR-013 demands: a
   machine-readable JSON shape (so an agent's comment is identical to a human's) and a plain REST API
   surface (so "the same door" is literally the same HTTP endpoint). Google Docs is the *UX reference*;
   GitHub/W3C are the *architecture reference*.

4. **Version = immutable snapshot of element rows; comments key to the element surrogate, not the
   version.** A comment opened on `elem_7abx` in v2 survives into v3 automatically if `elem_7abx` still
   exists, exactly like a GitHub review comment carries `original_commit_id` → `commit_id`. "Unresolved
   comments ⇒ unconverged ⇒ produce next version" becomes a trivial query: *any open comments on the
   current version's elements?*

5. **The change-summary (FR-017) is a structured element diff, not a text diff.** Because every element
   has a stable surrogate, the diff is set arithmetic over `{added, removed, modified, unchanged}` rows —
   the same "operations to transform A→B" output that semantic JSON-diff tools produce. This is far
   cleaner than line-diffing two markdown files, and it is the *same* machinery Step 7 reuses for
   round-trip provenance.

---

## How this maps to the 5 substeps

| Substep | Where answered |
|---------|----------------|
| 1. JS annotation libs + element-anchored patterns → React yes/no verdict | §Lens 2, §Lens 6, §TL;DR(1) |
| 2. Comment data model (anchor, open/resolved, resolution trail) | §Lens 5 "Comment data model", §Lens 4 (W3C shape) |
| 3. Version-progression flow (open comments ⇒ unconverged ⇒ v_n+1) | §Lens 5 "Versioning model", §Lens 1 (GitHub re-anchoring) |
| 4. Change-summary as stable-ID element diff (FR-017) | §Lens 5 "Change summary", §Lens 3 (semantic diff) |
| 5. Agent-parity contract (same API as human) | §Lens 3, §Lens 4 (W3C Protocol + GitHub bots) |

---

## Lens 1 — Expert Practitioner: how teams actually ship anchored comments (and where it hurts)

**The dirty secret of "comments anchored to text": re-anchoring is the entire problem, and it is never
fully solved.** Hypothesis — the most battle-tested open web-annotation system — stores **three**
selectors per target and runs a **four-strategy** re-anchoring cascade just to re-attach a highlight
after the document changes:

1. **RangeSelector** — XPath + offsets; fastest, but breaks the moment DOM structure changes.
2. **TextPositionSelector** — absolute character offsets into the document string; survives DOM
   restructuring but is invalidated by *any* content edit before the offset.
3. **TextQuoteSelector** — the exact quote plus a 32-char prefix/suffix for context-based fuzzy search.

When all strategies fail, the annotation is **orphaned** — it detaches and floats to a list with no
home in the text. ([Hypothesis: Fuzzy Anchoring](https://web.hypothes.is/blog/fuzzy-anchoring/);
[dom-anchor-text-quote / dom-anchor-text-position](https://groups.google.com/a/list.hypothes.is/g/dev/c/JCH8BRkp-cs)).
**Takeaway:** if you anchor to *text*, you are signing up to maintain a fuzzy-matching engine and to
accept orphans as a permanent failure mode. For a document that is *edited every version* (the whole
point of requirements iteration), text anchoring is anchoring on sand.

**Even Google Docs punts on this.** The Google Drive API exposes anchored comments as an opaque JSON
anchor string `{r: revisionId, a: [region]}`, and the docs explicitly warn: *"anchors are immutable and
their position relative to content cannot be guaranteed between revisions… recommended for documents
where position doesn't change, such as image files or read-only documents."*
([Google Drive API — Manage comments](https://developers.google.com/workspace/drive/api/guides/manage-comments)).
In other words, the gold-standard product everyone wants to imitate does *not* expose a stable
text-anchoring primitive to API clients — its in-product magic is proprietary OT machinery we are
explicitly out-of-scope for.

**The model that DID solve this for editable, versioned documents is GitHub PR review comments.** A
review comment anchors to **`(path, commit_id, position)`** and additionally stores
`original_commit_id` / `original_position`. As new commits land, GitHub re-maps `position` to the new
`commit_id`; when it can't, the comment is marked **outdated** (the graceful, visible analog of an
orphan) rather than silently lost.
([GitHub REST — PR review comments](https://docs.github.com/en/rest/pulls/comments)). Two lessons we
adopt directly:
- **Anchor to a stable unit + a version, with a re-map step between versions.** Our stable unit is the
  element surrogate; our version is the spec version. This is strictly easier than GitHub's because our
  unit (`elem_7abx`) is *explicitly persistent*, whereas a diff `position` is derived.
- **"Outdated" is a first-class state, not a crash.** If a commented element is deleted in the next
  version, the comment becomes `orphaned/outdated` and is surfaced for triage — never silently dropped
  (this is the resolution-trail requirement, FR-010, doing double duty).

**Practitioner verdict:** the experts' hard-won lesson is *don't anchor to text if you can anchor to a
stable ID.* Step 2 hands us stable IDs. We should take the gift and skip the fuzzy-anchoring tax
entirely.

---

## Lens 2 — Tools & Technologies: the annotation library landscape (and the React question, head-on)

| Library | Stack / React? | Anchoring model | Fit for us |
|---------|----------------|-----------------|------------|
| **`@recogito/text-annotator`** (RecogitoJS successor) | **Vanilla JS core**; optional React wrapper. `createTextAnnotator(document.getElementById('content'))` on arbitrary HTML | W3C-aligned: `{quote, start, end}` char-offset selectors + UUID per annotation; body = arbitrary payload (comments/tags) | Works on our Jinja HTML with **no React**. But solves *text-span* anchoring we don't need. ([repo](https://github.com/recogito/text-annotator-js)) |
| **RecogitoJS** (v1) | Vanilla JS | W3C TextQuote/TextPosition selectors | Same as above; older. |
| **Annotorious** | Vanilla JS (OpenSeadragon plugin for zoom images) | W3C Web Annotation + Media Fragments | Image/region annotation — not our use case. ([guides](https://annotorious.github.io/guides/)) |
| **Hypothesis client** | Vanilla JS (large; built as an embeddable sidebar) | 3-selector fuzzy cascade (§Lens 1) | Heavyweight; designed for annotating *third-party* pages. Overkill + fragile for our own structured doc. |
| **Velt / CommentBox.io / commercial SDKs** | **React-first** (Velt is explicitly "Google-Docs-style comments *with React*") | Proprietary | Would *introduce* a React dependency for zero benefit. ([Velt blog](https://velt.dev/blog/build-google-docs-comments-react)) — this is the trap. |
| **dom-anchor-text-quote / -text-position / -fragment** | Vanilla JS micro-libs (the guts of Hypothesis) | Individual selector implementations | Useful *only* if we later want sub-element span anchoring; adopt the algorithm, not a framework. |

**Decisive stack fact from Step 2's code exploration:** cast-server is **deliberately build-free** —
FastAPI + Jinja2 + **HTMX** + vanilla CSS, with **no `package.json`, no npm, no React/Vite/webpack**;
EasyMDE is *vendored* as a static file
(`02-canonical-source-of-truth-code.ai.md` §4 Patterns; `base.html:13,153`). Introducing React/Next.js
would mean adopting an entire JS build toolchain the project has explicitly avoided — a massive,
architecture-defining cost, not an incremental one.

**The React question, answered three ways:**
- *Do the best-in-class annotation libraries require React?* **No.** RecogitoJS/Annotorious/text-annotator/
  Hypothesis are all vanilla-JS-first; React is an optional wrapper. The libraries that *are*
  React-first (Velt, most commercial SDKs) are conveniences, not necessities.
- *Does our specific feature need a library at all?* **No** (see Lens 6). Element-level comments on
  stable IDs are DB rows + HTMX fragments.
- *Is there any requirement that forces React?* **Only realtime collaborative editing — and that is
  out of scope.** The async, single-writer constraint is precisely what lets us stay on HTMX.

HTMX is the right tool and is already in the stack: server returns HTML fragments, no virtual DOM, no
state library, ~14KB; inline-edit/delete-with-confirm/sortable patterns are idiomatic HTMX and map
1:1 onto "add comment / resolve comment / list thread"
([htmx in 2026: when you don't need React](https://dev.to/pockit_tools/htmx-in-2026-when-you-dont-need-react-and-when-you-absolutely-do-2mf4);
[FastAPI + HTMX no-build full-stack](https://blakecrosley.com/guides/fastapi-htmx)).

---

## Lens 3 — AI/ML Approaches: agents as first-class commenters, and LLM-generated diffs/summaries

**FR-013's "same door" is the AI-native crux.** The industry pattern for "AI leaves review feedback"
has converged on exactly the contract we want: the agent emits **structured JSON** (`{path, line/anchor,
severity, message}`) and posts it through the **same API endpoint** a human's comment goes through. This
is precisely how AI code-review bots operate today — a coordinator agent dedups findings and posts a
structured review comment via the GitHub/GitLab review-comment REST API, the *identical* endpoint a
human reviewer uses ([Cloudflare: orchestrating AI code review at scale](https://blog.cloudflare.com/ai-code-review/);
[Kinde: AI code-review bot with GitHub Actions](https://www.kinde.com/learn/ai-for-software-engineering/code-reviews/building-your-personal-ai-code-review-bot-github-actions-llm-integration/)).
**Design implication:** if comments are DB rows created via a plain `POST /api/specs/{slug}/comments`
that takes `{element_id, body, author_type}`, then "agent comments like a human" is *free* — the agent
calls the same route with `author_type=agent`. No parallel agent pathway to build or maintain. This is
the difference between v2 and v4 that the Multi-Lens insight flagged.

**LLM-generated change summaries (FR-017) — but grounded in a deterministic diff.** The robust pattern
is two-layer: (1) compute a **deterministic structural diff** of element rows between versions
(added/removed/modified — see Lens 5), then (2) optionally have the LLM *narrate* that diff into prose
("FR-014 was split into FR-014/FR-021 to separate routing from recording"). Never let the LLM *invent*
the diff — that's how you get hallucinated change logs. The deterministic diff is the source of truth;
the LLM is a renderer. This mirrors how AI agents are told to return feedback in structured JSON that
scripts then reliably extract and post
([structured-JSON review output](https://dev.to/pockit_tools/ai-code-review-in-your-cicd-pipeline-automating-pr-reviews-test-generation-and-bug-detection-56j4)).

**Contrarian AI angle — embedding-based semantic anchoring (note, don't adopt):** one could anchor a
comment to *meaning* (an embedding of the element text) and re-attach it across versions by cosine
similarity. This is the "AI-native" temptation. **Reject it for the anchor itself** — non-deterministic
re-anchoring is a debugging nightmare and an audit-trail hazard for a *source-of-truth* document.
Stable surrogate IDs are deterministic and auditable. Embedding similarity is, at most, a *fallback
suggestion* when an element is deleted ("this orphaned comment looks related to the new FR-021 — re-attach?")
— a human/agent-confirmed hint, never the primary anchor.

---

## Lens 4 — Community & Open Source: the interoperable standards that answer FR-013 for free

**The W3C Web Annotation stack is the open-standard answer to "design comments so humans and agents use
the same mechanism."** It is a published W3C Recommendation with two halves:

- **Web Annotation Data Model** — a JSON-LD shape: an `Annotation` has a `body` (the comment content) and
  a `target` (what it's attached to), where the target carries a `selector`. This is *exactly* our
  comment shape: body = comment text + state, target = element surrogate.
  ([W3C Web Annotation WG](https://www.w3.org/annotation/);
  [model](https://w3c.github.io/web-annotation/model/wd/)).
- **Web Annotation Protocol** — a RESTful HTTP API (built on Linked Data Platform) for creating/managing
  annotations in a container: `POST` an annotation to a container, `GET` to list, etc.
  ([W3C Annotation Protocol](https://www.w3.org/TR/annotation-protocol/)). This is the "same door"
  literally specified as an HTTP contract — any client (human UI, agent, CI bot) speaks it identically.

**We should borrow the *shape and contract*, not necessarily the full JSON-LD ceremony.** The valuable,
portable ideas:
- A comment is `{ target: {element_id, version, optional sub-selector}, body: {text, author, author_type},
  state: open|resolved, created_at }` — a clean, standard-aligned structure.
- The **selector** abstraction lets us start with the simplest selector (an element-ID/"FragmentSelector"
  pointing at our surrogate) and *add* a `TextQuoteSelector` later for sub-span comments **without
  changing the data model** — the W3C model is explicitly designed for multiple/refined selectors. This
  is the cheap forward-compatibility path.

**OSS prior art worth citing in the playbook:** Hypothesis (open annotation at web scale, the
fuzzy-anchoring reference); the [web-annotation-ecosystem](https://github.com/jankaszel/web-annotation-ecosystem)
catalog of W3C-compliant tools; and the GitHub/GitLab review-comment conventions (de-facto standard for
*versioned, editable* document review with bot participation). **Community consensus is unambiguous:
anchor to a stable unit + a version, expose a plain REST surface, and treat machine clients as
first-class — which is exactly what an element-surrogate + HTMX/JSON endpoint gives us.**

---

## Lens 5 — Frameworks & Patterns: the concrete recommended design

### Pattern choice: **element-anchored comments as DB rows, served via HTMX** (not a JS annotation lib)

Because Step 2 establishes a `spec_elements` table with a **persisted surrogate** per element (decoupled
from the human-facing `FR-001` display label), the comment system collapses to ordinary relational CRUD
+ server-rendered fragments. No fuzzy anchoring, no orphan engine, no client framework.

```
spec_versions (id PK, goal_slug FK, version_no, status∈{draft,unconverged,converged,archived}, created_at)
spec_elements (surrogate PK [ULID], goal_slug FK, version_id FK, kind∈{US,FR,SC,scenario},
               display_label, ordinal, body, prev_surrogate? [links same element across versions])
comments      (id PK, goal_slug FK, element_surrogate FK, version_id_opened FK,
               sub_selector? [JSON, W3C TextQuoteSelector for future sub-span],
               author, author_type∈{human,agent}, body,
               state∈{open,resolved,orphaned}, resolved_in_version_id?, created_at, resolved_at)
comment_events(id PK, comment_id FK, event∈{opened,replied,resolved,reopened,orphaned},
               actor, actor_type, version_id, note, at)   ← the retained resolution trail (FR-010)
```

- **Anchor (FR-008/FR-009):** `comments.element_surrogate` → a durable row, not a text range. Optional
  `sub_selector` (W3C TextQuoteSelector) only if/when sub-element highlighting is wanted later — the
  schema is forward-compatible without it.
- **Open/resolved + retained trail (FR-010):** `comments.state` for current status; `comment_events` is
  the append-only audit log so resolution history is never lost (this also satisfies US5 Scenario 3:
  "retrieve old version with comments and resolution state intact").
- **Agent parity (FR-013):** `author_type` is the only field that differs between a human and an agent
  comment; both arrive through the same `POST /api/specs/{slug}/comments`. (Lens 3 + Lens 4.)

### Versioning model: **version = immutable element snapshot; comments key to the element, not the version**

- A new version **copies forward** element rows (new `version_id`, same/derived `surrogate` via
  `prev_surrogate`), edits land on the new rows, the prior version is marked `archived` (Step 2 says
  archived versions live as DB rows; only the *current* version's file projection stays in the goal
  folder — FR-011).
- **"Open comments ⇒ unconverged ⇒ produce v_n+1"** is a one-line query: a version with any
  `comments.state='open'` on its elements is `unconverged`; resolving all of them (or producing the next
  version that addresses them) is what converges it (US4 Scenario 2).
- **Comment carry-over (the GitHub re-map, Lens 1):** when v_n+1 is produced, for each open comment, if
  the element's `surrogate` (via `prev_surrogate` chain) still exists → comment rides along (still
  `open` unless explicitly resolved). If the element was deleted → comment transitions to `orphaned` and
  is surfaced for triage. Deterministic, auditable, no fuzzy matching.

### Change summary (FR-017): **structured element diff, not text diff**

Because elements have stable surrogates, the version diff is set arithmetic, yielding the same
"operations to transform A→B" output semantic-diff tools produce
([semantic JSON diff: add/remove/replace/move ops](https://github.com/maxmalkin/sdiff-rs);
[SemanticDiff parses to representation-independent structure](https://semanticdiff.com/online-diff/json/)):

```
diff(v_n, v_{n+1}) over surrogate set:
  added     = surrogates in v_{n+1} not in v_n
  removed   = surrogates in v_n not in v_{n+1}
  modified  = surrogates in both whose body changed   (optional inner text-diff for display)
  unchanged = surrogates in both, body identical
→ render: "v3 changes: +2 FRs (FR-021, FR-022), 1 modified (US6: added Scenario 5), 0 removed"
```

This is **dramatically more robust and reviewable than line-diffing two markdown files**, and it is the
*same* engine Step 7 reuses to render round-trip write-backs as a provenance-tagged delta (the note
explicitly hands this artifact to Step 7).

### UI/UX pattern (HTMX, no framework)

- Each rendered element carries `id="elem_<surrogate>"` (Step 5's HTML render emits per-element wrappers
  with these IDs — note this dependency to Step 5; today's render is one opaque blob, per Step 2 §2c).
- A margin "comment" affordance per element → `hx-get` loads the comment thread fragment into a side
  panel/popover; `hx-post` adds a comment; `hx-post .../resolve` toggles state and swaps the badge.
  Idiomatic HTMX inline-action patterns; no client state library
  ([HTMX implementation patterns](https://www.softwareseni.com/building-modern-uis-with-htmx-essential-implementation-patterns/)).
- This reuses cast-server's existing render-after-mutate + artifact-sidebar + path-validation
  conventions (Step 2 §4), and the `/preso/review/{slug}` precedent proves rich generated HTML already
  serves from the goal folder.

---

## Lens 6 — Contrarian View: kill two premises, not one

**Premise 1 (kill): "Google-Docs-style comments ⇒ React/Next.js."** Dead. Justified above on three legs.
The belief conflates *comment UX* with *realtime co-editing*. Google Docs needs OT/CRDT because multiple
cursors edit the same text simultaneously; *that* is what an SPA buys you. Strip co-editing (explicitly
out of scope) and the residual feature is async CRUD — HTMX's home turf.

**Premise 2 (kill, and this is the spicier one): "Therefore we should adopt a JS annotation library
like RecogitoJS/Hypothesis."** Also wrong, for the *opposite* reason people assume. Those libraries
exist to solve **anchoring free-text selections in prose you don't control** — fuzzy matching, orphan
recovery, selector cascades (Lens 1). **Step 2's architecture deletes that problem.** Once every
requirement element has a stable surrogate and the renderer emits `id="elem_<surrogate>"` wrappers,
"comment on this element" is a foreign key, not a text search. Adopting an annotation library here would
*re-import* the fragile text-anchoring machinery you spent Step 2 engineering away — strictly negative
value. The contrarian, lower-code answer is: **no annotation library; DB rows + HTMX.** Keep the W3C
*data model* as your schema's north star (forward-compat for sub-span selectors), but don't pull the
client library.

**Premise 3 (sharpen, don't kill): "Comments must be character-range precise like Google Docs."**
Question it. For a *requirements* document, the reviewable unit is the requirement element (FR/US/SC/
scenario), not an arbitrary word span. Element-level commenting is *more* legible (every comment is
unambiguously "about FR-014"), more robust (no re-anchoring), and matches how engineers actually review
specs (GitHub comments anchor to a line, not a column). Offer sub-span highlighting later as a
progressive enhancement via an optional W3C `TextQuoteSelector` in `comments.sub_selector` — but ship
element-level first. **Don't gold-plate the anchor granularity before the loop even works.**

**One genuine risk the contrarian must concede:** element-level comments are weaker if a single element
is a giant wall of text (you can't point at the offending clause). Mitigation: this is really an
argument for *finely-grained elements* (scenario-level, clause-level surrogates) in Step 2's model, plus
the optional sub-selector escape hatch — not an argument for React.

---

## Lens 7 — First Principles: decompose to irreducible primitives

Strip the feature to its atoms and the architecture falls out:

- **What is a comment?** `anchor + body + author + lifecycle-state + thread`. The only hard atom is
  *anchor*, and "anchor" reduces to *a durable reference to a thing in the document*. If the document's
  things have durable IDs (Step 2), the anchor is a foreign key — the simplest possible primitive.
  Everything else (body, author, state, replies) is ordinary data.
- **What is a version?** *An immutable snapshot of the set of elements at a point in time.* Immutability
  is the key property: it makes diffs well-defined, archival trivial (Step 2: archived = DB rows), and
  "review the delta" possible. Mutable-in-place versions can't be diffed or audited.
- **What does "unresolved comments drive the next version" mean, atomically?** A boolean over the current
  version: `∃ comment where state=open` ⇒ `unconverged`. Versioning is *gated by* comment state; it is
  not itself a comment feature. One predicate.
- **What is a change summary?** *The difference between two element sets.* With stable IDs it is pure set
  arithmetic (Lens 5). Without stable IDs it degrades to text-diff heuristics. The IDs are load-bearing.
- **What does "agent uses the same mechanism as a human" require, minimally?** That the human UI has *no
  privileged path to the data* — i.e., the UI is a client of the same API the agent calls. The forcing
  function: **build the JSON/REST comment+version API first, then build the HTMX UI on top of it.** If
  the UI ever writes to the DB through a path the agent can't call, FR-013 is already violated. (This is
  the W3C-Protocol / GitHub-bot pattern, Lenses 3–4.)

**First-principles conclusion:** the irreducible requirement is *stable element identity + an immutable
version snapshot + an API-first comment store.* None of those three primitives is a frontend concern.
React/Next.js addresses a problem (concurrent rich-text co-editing) that is not in this feature's atom
set. The lightest stack that satisfies the atoms is: **Step 2's element table + a versioned snapshot +
a plain REST/HTMX comment API.**

---

## Open questions / hand-offs for the playbook & later steps

1. **Element granularity is a Step 2/Step 4 seam.** Element-level comments are only as precise as the
   element rows are fine-grained. Recommend Step 2's `spec_elements` model down to *scenario* and
   ideally *clause* level so comments can target meaningfully. Flag if Step 2 lands coarser.
2. **Renderer must emit `id="elem_<surrogate>"` per element (Step 5 dependency).** Today's render is one
   opaque HTML blob (Step 2 §2c, `api_artifacts.py:132`); Step 5's per-element-wrapped HTML is a
   prerequisite for the margin-comment UI. Element IDs in *markdown* (FR-007) can be carried as trailing
   `<!-- elem:<surrogate> -->` sentinels or an HTML-comment-free sidecar so the spec-checker still passes.
3. **Reply threads vs flat comments:** spec says comment + resolved; recommend modeling `comment_events`
   to allow replies cheaply now (agents will reply to humans). Confirm with owner whether threads are
   in v2 scope or deferred.
4. **Notification surface (overlaps US7/FR-019):** "what changed" notifications for downstream write-backs
   reuse the change-summary engine; coordinate the notification mechanism design with Step 7.
5. **Sub-span anchoring (TextQuoteSelector) is explicitly deferred** — schema is forward-compatible
   (`comments.sub_selector` JSON), but don't build the fuzzy-match client in v2.

---

## Citation index

- Hypothesis — Fuzzy Anchoring (3-selector, 4-strategy cascade, orphans): https://web.hypothes.is/blog/fuzzy-anchoring/
- Hypothesis dev — dom-anchor-text-quote / -text-position / -fragment: https://groups.google.com/a/list.hypothes.is/g/dev/c/JCH8BRkp-cs
- Recogito text-annotator-js (vanilla JS, optional React wrapper, W3C selectors): https://github.com/recogito/text-annotator-js
- Annotorious (vanilla JS image annotation, W3C-conformant): https://annotorious.github.io/guides/
- Velt — "Google Docs comments *with React*" (the React-coupling trap): https://velt.dev/blog/build-google-docs-comments-react
- Google Drive API — Manage comments (immutable anchors, not stable across revisions): https://developers.google.com/workspace/drive/api/guides/manage-comments
- GitHub REST — PR review comments (`commit_id`/`position`/`original_*`, outdated state, bot parity): https://docs.github.com/en/rest/pulls/comments
- W3C Web Annotation Working Group (Data Model + Protocol overview): https://www.w3.org/annotation/
- W3C Web Annotation Protocol (RESTful create/manage, LDP containers): https://www.w3.org/TR/annotation-protocol/
- W3C Web Annotation Data Model (working draft): https://w3c.github.io/web-annotation/model/wd/
- web-annotation-ecosystem (catalog of W3C-compliant tools): https://github.com/jankaszel/web-annotation-ecosystem
- W3C Web Annotation selectors (TextQuote/TextPosition, robust anchoring): https://anchorpoint.readthedocs.io/en/latest/api/selectors.html
- Cloudflare — orchestrating AI code review at scale (agent posts via same review API): https://blog.cloudflare.com/ai-code-review/
- Kinde — AI code-review bot via GitHub Actions + LLM (structured JSON → same endpoint): https://www.kinde.com/learn/ai-for-software-engineering/code-reviews/building-your-personal-ai-code-review-bot-github-actions-llm-integration/
- AI code review in CI/CD — structured-JSON comment output: https://dev.to/pockit_tools/ai-code-review-in-your-cicd-pipeline-automating-pr-reviews-test-generation-and-bug-detection-56j4
- htmx in 2026 — when you don't need React (and when you do = realtime/SPA): https://dev.to/pockit_tools/htmx-in-2026-when-you-dont-need-react-and-when-you-absolutely-do-2mf4
- FastAPI + HTMX no-build full-stack: https://blakecrosley.com/guides/fastapi-htmx
- HTMX implementation patterns (inline edit / delete-confirm / fragments): https://www.softwareseni.com/building-modern-uis-with-htmx-essential-implementation-patterns/
- sdiff-rs — semantic structured diff (insert/delete/replace ops): https://github.com/maxmalkin/sdiff-rs
- SemanticDiff — parse-to-representation-independent JSON diff: https://semanticdiff.com/online-diff/json/
- **Internal dependency:** `exploration/research/02-canonical-source-of-truth-code.ai.md` (stable
  element identity, build-free stack, render-after-mutate precedent) — the keystone this note builds on.
