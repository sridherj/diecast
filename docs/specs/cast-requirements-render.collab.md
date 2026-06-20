---
feature: cast-requirements-render
module: cast-server
linked_files:
  - cast-server/cast_server/routes/pages.py
  - cast-server/cast_server/requirements_render/renderer.py
  - cast-server/cast_server/requirements_render/goal_card.py
  - cast-server/cast_server/requirements_render/zero_click.py
  - cast-server/cast_server/services/requirements_render_service.py
  - bin/cast-render-zero-click
  - agents/cast-requirements-checker/cast-requirements-checker.md
  - agents/cast-requirements-checker/config.yaml
  - cast-server/tests/test_fr007_readonly_guard.py
  - docs/plan/2026-06-11-refine-requirements-v2-phase3a-html-render.md
  # Phase 4 — in-render commentary, versioning, deterministic diff (this spec extension)
  - cast-server/cast_server/services/comment_service.py
  - cast-server/cast_server/routes/api_requirements.py
  - cast-server/cast_server/services/requirement_version_service.py
  - cast-server/cast_server/requirements_render/block_diff.py
  - cast-server/cast_server/requirements_render/diff_render.py
  - cast-server/cast_server/static/requirements_comments.js
  - cast-server/cast_server/templates/fragments/requirements_comments/tray.html
  - cast-server/cast_server/templates/fragments/requirements_comments/thread_item.html
  - cast-server/cast_server/templates/fragments/requirements_comments/composer.html
  - cast-server/cast_server/templates/fragments/requirements_comments/changes_panel.html
  - cast-server/cast_server/requirements_render/templates/document.html.j2
  - cast-server/cast_server/requirements_render/templates/_theme.css.j2
  - agents/cast-comment-reanchor/cast-comment-reanchor.md
  - agents/cast-comment-reanchor/config.yaml
  - cast-server/tests/ui/runner.py
  - docs/plan/2026-06-11-refine-requirements-v2-phase4-annotation-versioning.md
  # v3 Phase 3 — the WHAT→HOW maker pipeline renders bespoke per-family HTML (this spec extension)
  - agents/cast-requirements-what/cast-requirements-what.md
  - agents/cast-requirements-what/config.yaml
  - agents/cast-requirements-how/cast-requirements-how.md
  - agents/cast-requirements-how/config.yaml
  - cast-server/cast_server/requirements_render/maker_gate.py
  - cast-server/cast_server/services/render_job_service.py
  - cast-server/cast_server/requirements_render/templates/generating.html.j2
  - docs/plan/2026-06-12-refine-requirements-v3-phase3-maker-pipeline.md
  # v3 Phase 4a — the LLM quality gate + quality-driven rework loop (this spec extension)
  - agents/cast-requirements-render-checker/cast-requirements-render-checker.md
  - agents/cast-requirements-render-checker/config.yaml
  - cast-server/cast_server/requirements_render/checker_verdict.py
  - cast-server/cast_server/config.py
  - cast-server/cast_server/db/schema.sql
  - cast-server/tests/eval_quality_gate.py
  - cast-server/tests/test_eval_quality_gate.py
  - cast-server/tests/test_quality_loop.py
  - cast-server/tests/test_checker_verdict.py
  - cast-server/tests/fixtures/quality_gate/low_quality_attempt.html
  - cast-server/tests/fixtures/quality_gate/gap_amnesty_attempt.html
  - docs/plan/2026-06-12-refine-requirements-v3-phase4a-quality-gate.md
  # v3 Phase 4b — comments & versions survive the maker; diff narration (this spec extension)
  - agents/cast-refine-requirements/cast-refine-requirements.md
  - agents/cast-refine-requirements/config.yaml
  - cast-server/tests/test_comment_survival.py
  - cast-server/tests/eval_reanchor.py
  - cast-server/tests/eval_sc003_survival.py
  - cast-server/tests/test_schema_migration.py
  - docs/plan/2026-06-12-refine-requirements-v3-phase4b-comment-survival.md
  # Phase 5 — gap-fill (ask upstream, never fabricate) + the flagged-renders list (this spec extension)
  - agents/cast-requirements-gapfill/cast-requirements-gapfill.md
  - agents/cast-requirements-gapfill/config.yaml
  - cast-server/tests/test_gap_reconciliation.py
  - cast-server/tests/fixtures/family_corpus/
  - cast-server/tests/eval_family_sweep.py
  - docs/plan/2026-06-12-refine-requirements-v3-phase5-gapfill-signoff.md
  # v8 Phase-5 follow-up — HOW two-mode (CREATE/UPDATE) + comment anchoring source→render snapshot
  - cast-server/cast_server/requirements_render/block_splice.py
  - cast-server/cast_server/requirements_render/comment_anchor.py
  - cast-server/tests/test_render_mode_decision.py
  - cast-server/tests/test_comment_anchor_render.py
  - cast-server/tests/test_maker_gate_update_fidelity.py
  - cast-server/tests/test_maker_gate_empty_shell.py
  - cast-server/tests/test_comment_service.py
  - docs/plan/2026-06-12-refine-requirements-v3-how-update-mode-render-anchoring.md
  - docs/plan/2026-06-13-refine-requirements-v3-spec-v8-change-brief.md
  # v9 Phase 2b (exploration-pipeline-nxm) — dual md/html artifact viewer (this spec extension)
  - cast-server/cast_server/routes/api_artifacts.py
  - cast-server/cast_server/routes/api_goals.py
  - cast-server/cast_server/templates/macros/markdown_viewer.html
  - cast-server/tests/test_dual_viewer.py
  - docs/plan/2026-06-20-exploration-pipeline-nxm-2b-dual-viewer.md
last_verified: "2026-06-20"
---

# Cast Requirements Render — Spec

> **Spec maturity:** draft
> **Version:** 10
> **Updated:** 2026-06-20 — v10 (Phase 3b, exploration-pipeline-nxm): **Diecast-wide commenting on ANY
> served `.html`.** Render-space anchoring becomes **artifact-keyed** — the `anchor_space='render'`
> anchor now resolves against the SPECIFIC served `.html` the quote was minted from, selected by a new
> goal-relative **`artifact_ref`** (a third additive nullable `requirement_comments` column; NULL =
> `refined_requirements.html`, so requirements + every existing comment keep working byte-identically).
> The same-door create endpoint gains **one** optional, defaulted `artifact_ref` field — server-validated
> goal-relative / `.html`-only / no-traversal, **NO** parallel route (US8 honored). In-iframe commenting
> (deferred in v9) is now **LIVE**: the injected null-origin srcdoc comment layer postMessages a
> `cch:submit` batch to a **host bridge** (`static/comment-bridge.js`) that proxies **per-comment**
> same-door POSTs and replies `cch:submitted`, validated on **SOURCE IDENTITY** (`event.source ===` the
> iframe's `contentWindow`; origin is `"null"` and is **never** checked) via an `artifact_ref →
> contentWindow` registry, routing the reply to the **originating frame only** (`targetOrigin "*"`),
> multiple commentable iframes per tab. Verbatim-substring relocation + honest-NULL `block_ref`
> generalize to any served `.html` (Phase 4's `exploration.html` inherits commenting for **free**;
> ref-less is honest success). US4 (render read-only), US7 (selectable units, **no** ids / **no**
> anchor-id scheme — none introduced) and US8 (same-door, single write path) are **REUSED, not
> superseded**. **Still out of scope:** stable anchor-ids (deferred) and any write-back round-trip to
> exploration md (comments are feedback-only). New: US23, FR-064–FR-066, SC-026.
> **Updated:** 2026-06-20 — v9 (Phase 2b, exploration-pipeline-nxm): the Diecast **phase-tab artifact
> viewer** now renders render-class `.html` artifacts via `<iframe srcdoc>` (null-origin sandbox:
> `allow-scripts allow-popups`, **no** `allow-same-origin`) **alongside** the `.md` it already renders.
> The `.md`-only **read** gate (`api_artifacts.validate_artifact_path_read`) and the phase-tab globs
> (`api_goals.get_phase_tab`) are extended to admit `.html`; the artifact-dict **`kind`** discriminator
> (`markdown` | `html`) + the `_add_html_file` collector (verbatim file bytes, never `md.markdown()`-
> processed) are the seam. The **edit** gate stays `.md`-only — `.html` renders are read-only. This makes
> the **refined-requirements HTML** reachable in-viewer (render **consumer #2**), not only on `/render`;
> **exploration** is render **consumer #1** (Phase 4 produces `exploration/exploration.html`). US4
> (render-class, read-only, no authorship suffix, atomic + `served-by` stamp) and US7 (selectable units,
> **no ids/anchors** — the DOM contract Phase 3b's verbatim-substring anchoring + the `anchor_space='render'`
> path consume) are **REUSED, not superseded**, now applied to ALL render-class `.html` in the viewer.
> **Out of scope (stated to avoid over-claiming):** in-iframe commenting (Phase 3b) and the exploration
> render pipeline (Phase 4) — v9 ships the *viewer render* only. New: US22, FR-062–FR-063, SC-025.
> **Updated:** 2026-06-13 — v8 (Phase-5 follow-up: HOW two-mode + render-snapshot anchoring): the HOW
> maker gains a CREATE/UPDATE two-mode contract (CREATE re-renders fresh + readability-first; UPDATE
> re-renders only changed blocks and keeps unchanged unit containers byte-identical) bounded by a
> massive-change threshold; comment anchoring **moves** from the canonical `.collab.md` to the
> published-render snapshot with a server-resolved `block_ref` bridge + `anchor_space` column; the US16
> blanket **verbatim-carriage clause is SUPERSEDED** (anchor labels + one-unit-one-container survive;
> CREATE leaf-text copy-exact is dropped for readability); US8/US12 displacement + US19 survival
> reorient to render space; `cast-comment-reanchor` steps to **contract v3** (additive render-space
> context) and runs once at the publish boundary for an UPDATE's expected misses; gap CRs are idempotent
> under UPDATE (reuse prior `gaps-state.json`, skip emit); + the empty-shell gate check and the
> splice-assembles-the-published-artifact architecture note (US Spike 1a verdict: FAIL →
> deterministic-splice). New: US16 partial supersession, US8/US12/US19 reorientation, US13 Scenario 5,
> FR-055–FR-061, SC-022–SC-024.
> **Updated:** 2026-06-12 — v7 (Phase 5): gap-fill — the maker fills genuine comprehension gaps by
> asking upstream, never fabricating (FR-015/FR-016 realized). The activated `gaps[]` WHAT-doc field
> + the `GAPS-DETECTED` HOW trailer (the bounded HOW-asks-WHAT round-trip), the tool-free
> `cast-requirements-gapfill` grounded-or-refuse subagent, the server-side verbatim evidence
> validation (`validate_evidence` reusing the single `verbatim_locate`), gap reconciliation through
> the **unchanged** v2 change-request gate under the goal's GATE-ALL policy, the `.rr-gap` page marker
> (question + fixed status string, NEVER the proposed answer) with un-mark-by-regeneration, the
> nine-family verification record (SC-002), and the minimal **flagged-renders list** that consumes the
> 4a recording-only flag columns (the honest degraded-page surface under the structural override).
> **v6 (Phase 4b):** comments & versions survive the maker — the comment-survival gate (override-aware:
> surfaced, never blocking), the `.comment-unplaced` tray badge, the `cast-comment-reanchor` contract-v2
> superset, and the stored-once diff-narration surface (validated against the deterministic change set,
> rendered by attachment only).
> **Status:** Draft

## Intent

Refine Requirements v2 gives a refined requirement document a **read-only HTML render** as its
primary human-consumption artifact. The render leads with an above-the-fold **Goal Card**
(classification pill + one-sentence job statement + 3–5 WHAT assertions, zero clicks), uses an
L1/L2/L3 visual hierarchy, discloses depth via native `<details>`, quarantines HOW to a muted
"Directional" section, and varies its section order per work-family via Phase 2's recipe model. The
goal's only measurable headline criterion is that an unfamiliar reader can state a goal's WHAT in
about two minutes.

This spec is the **contract Phase 4 (in-render commentary) cites and Phase 5 reuses.** It documents, as
stated-and-verifiable behaviours, the four user-facing surfaces that surround the pure renderer: the
`GET /goals/{slug}/render` route, the generated `refined_requirements.html` artifact class, the
zero-click extractor, and the `cast-requirements-checker` agent gate — plus the **DOM contract** Phase
4 depends on. The pure renderer itself (`render_requirements`) and the family-recipe semantics it
consumes are specified by `cast-goal-classification.collab.md`; this spec records only the
human-facing render surface, not the recipe machinery. Symbol and route names below are the **naming
contract** — Phase 4 adopts them verbatim.

**Phase 3 maker-pipeline surface (US14–US17, FR-029–FR-035, SC-010–SC-013; v4's happy-path
inversion).** On the happy path the render is no longer the deterministic substrate — it is produced by
a **two-agent maker pipeline**: `cast-requirements-what` emits per-family communication intent (a
machine-checkable WHAT doc), and `cast-requirements-how` turns it into a self-contained, bespoke,
per-family HTML page drawn from the named cast-preso archetype library. Both run as tool-free
`claude -p` subagents driven by `render_job_service`; `--tools ""` makes "the maker never writes the
canonical `.collab.md`" **structural**, not behavioural. The deterministic `render_requirements()` /
`rerender_requirements_html` path (US1–US2/FR-002–FR-003) is **demoted to the fallback branch**, served
**only** on a literal no-output maker failure (crash / timeout / empty / structurally-unextractable).
Generation is a **background job**: a view of a stale or missing render serves a live "generating…"
state immediately (the prior stale render plus a regenerating banner when one exists), polls
`GET /goals/{slug}/render/status`, and swaps in the finished render on `ready`; the comment path and
cached views are independent and never wait on generation. The canonical `US-NN`/`FR-NNN`/`SC-NNN`
ids ride along as a **logical (non-DOM) backbone** — assigned upstream by the deterministic parser,
emitted verbatim by the maker as small visible anchor labels, **never** as `id=`/`data-block-anchor`
attributes (US7/FR-012/FR-013 preserved unchanged) — and the maker contract **requires verbatim
carriage** of each unit's anchorable text. On structural-gate exhaustion the server serves the **best
attempt + a `structural_violation` human-review flag** (surfaced via the `flagged` job status, a
`served-by: structural_violation` artifact stamp, and a reader-visible "needs review" badge), **not**
the deterministic page — *surface, don't suppress*. The richer human-review flag columns and the
LLM-judged quality gate that replaces the structural happy-path gate are **Phase 4a scope** (forward
pointer only; this version specifies neither). The symbol/route/agent names below are the cross-phase
**naming contract** — Phase 4a/4b adopt them verbatim.

**Phase 4 surface (US8–US13, FR-014–FR-027, SC-005–SC-009; this version's extension).** On top of the
read-only render, Phase 4 adds the **iteration loop**: reviewers — human **or** agent, through the
*same* API door (FR-013, `author_kind` the only distinction) — leave comments anchored to a **stored
quote**, never to an element id or anchor. Open comments mark the spec **unconverged** and drive new
**versions**; each version yields a **deterministic block-level change summary** (the `block_diff`
engine Phase 5 imports verbatim). Only the current requirements file ever lives in the goal folder
(FR-011); older versions are DB rows with their comments and as-of resolution state intact. The single
load-bearing design rule (decisions #1/#9): **the only deterministic machinery is where being wrong
means silent data loss** — comment rows, version snapshots, and the structural change *set*.
Everything placement-related is a Claude subagent (`cast-comment-reanchor`) re-locating comments by
their stored quote, with **orphaning always surfaced, never silent**. Displacement is a **derived,
read-time property** — the human save path gains zero new machinery. The Phase 4 symbol/route/schema
names below are the cross-phase **naming contract**; Phase 5 imports `block_diff`/`summarize` and cites
the same-door API rather than reimplementing either.

**Phase 4a quality gate (US18, FR-037–FR-040, SC-014–SC-016; this version's extension — completes the
v4 forward pointers).** On the happy path no maker render reaches a reader unless **one** agent —
`cast-requirements-render-checker`, grading comprehension **and** visual quality in a single pass (the
owner explicitly rejected a multi-checker coordinator) — passes it. The checker drives a
**quality-driven rework loop** inserted into `render_job_service` as `run_checker → decide_quality`
between `gate_html` and `publish` (the seam Phase 3 reserved): the loop reworks until the comprehension
bar is met, guarded **only** by a high anti-infinite-loop ceiling — **never rationed by cost, latency,
or model tier** (owner decision, binding). The trust boundary is the shaping insight: the deterministic
`maker_gate` owns **fidelity to the source** (id parity, verbatim carriage, the DOM contract —
everything whose failure means silent data loss); the LLM checker owns **the reader's experience** (can
a cold reader state the WHAT; does the page look like quality work). The checker therefore judges only
the rendered artifact + family label — **never** the canonical source, **never** the WHAT doc (tool-free
by construction) — staying the unfamiliar reader that made SC-001's verdict trustworthy in v2. The gate
itself is **code-owned**: `checker_verdict.derive_pass`/`canonical_score` recompute the binary PASS and
the ranking score code-side (FR-010 extended to the visual dimension and to best-attempt ranking); the
agent-emitted `score` float is advisory only. This version **also resolves the v4 forward pointers**:
the two-branch degradation policy is now specified **as the OWNER OVERRIDE** — the deterministic page is
served **only** on a literal no-output failure; a structurally-broken-but-present attempt is scoreable,
servable, and flagged, **never** the silent deterministic swap (*surface, don't suppress*) — and the
four `render_jobs` human-review flag columns are specified here. The human-review **consumption** surface
(the flagged-renders LIST) is **Phase 5d**; this version ships the flag **recording-only** (columns +
envelope stamp + status-JSON exposure). The symbol/agent/column names below are the cross-phase **naming
contract** — Phase 4b/5 adopt them verbatim.

## User Stories

### US1 — Serve a read-only requirements render (Priority: P1)

**As a** reader unfamiliar with a goal, **I want to** open the goal's rendered requirements page,
**so that** I can state the goal's WHAT without reading the raw markdown.

**Independent test:** `GET /goals/{slug}/render` for a goal with refined requirements returns 200 and
HTML whose Goal Card carries the job statement and WHAT assertions.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a reader requests the render for a goal that has refined requirements, THE
  SYSTEM SHALL return 200 with the self-contained HTML render served by the page route in
  `routes/pages.py`.
- **Scenario 2:** WHEN the render is produced on the **fallback** branch (the maker emitting no
  extractable output — US17/FR-030), THE SYSTEM SHALL build it through the pure function
  `render_requirements(parsed, *, version=None) -> RenderResult` (a frozen `{html, warnings}`), which
  performs no I/O and stamps no timestamps so the output is deterministic. *(v4: on the happy path the
  render is the maker pipeline of US14; this pure function is the demoted fallback substrate, not the
  primary producer.)*

### US2 — Lazy regeneration keyed on the source content hash (Priority: P1)

**As a** maintainer, **I want to** have the `.html` regenerate only when the source actually changed,
**so that** serving the page is cheap and the artifact is byte-stable between edits.

**Independent test:** Two consecutive renders of an unchanged source produce byte-identical `.html`;
editing the source then requesting the render rewrites it with a new `source-hash`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the render is requested AND the embedded `source-hash` of the existing `.html`
  equals the current source `content_hash`, THE SYSTEM SHALL return the existing file untouched
  (no write).
- **Scenario 2:** WHEN the render is requested AND the source hash differs (or no `.html` exists yet),
  THE SYSTEM SHALL regenerate the render. *(v4 inversion — supersedes the synchronous-regen wording:
  on the happy path the regeneration is the **background maker job** of US15, which serves a live
  generating state immediately and swaps the finished render in on `ready`; the synchronous
  `rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None) -> Path | None` is invoked
  only on the stub short-circuit (US3) and the literal-no-output fallback (US17). The source-hash cache
  envelope of Scenario 1 is reused unchanged across both branches.)*

### US3 — Prompt-to-begin and not-found handling (Priority: P2)

**As a** reader, **I want to** get a clear page for goals with no usable requirements and a clean 404
for unknown goals, **so that** the route never leaks errors or stack traces.

**Independent test:** A known goal with no/stub requirements returns 200 prompt-to-begin; an unknown
slug returns 404; neither emits a traceback.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the render is requested for a known goal whose requirements are absent or a
  stub (`is_stub(parsed)` true, `STUB_WORD_THRESHOLD = 200` imported from the Phase 1 parser
  package), THE SYSTEM SHALL return 200 with a prompt-to-begin render rather than an error.
- **Scenario 2:** WHEN the render is requested for an unknown slug, THE SYSTEM SHALL return 404, which
  also defeats any path-traversal attempt by validating the slug against the goals DB before touching
  disk.
- **Scenario 3:** WHEN render generation raises, THE SYSTEM SHALL log the exception, leave any existing
  `.html` intact, and return a plain 500 — never a stack trace to the reader.

### US4 — The generated `.html` is a render, not an authored artifact (Priority: P1)

**As a** maintainer reading the goal directory, **I want to** recognise `refined_requirements.html` as
an auto-generated render, **so that** I never apply authored-artifact rules to it or hand-edit it.

**Independent test:** A generated `goals/{slug}/refined_requirements.html` opens with the
AUTO-GENERATED header and a `source-hash` comment, and carries no `.human`/`.ai`/`.collab` authorship
suffix.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the `.html` is generated, THE SYSTEM SHALL prefix it with an
  `<!-- AUTO-GENERATED: ... -->` header followed by a `<!-- source-hash: <content_hash> -->` comment.
- **Scenario 2:** WHEN classifying the artifact, THE SYSTEM SHALL treat `refined_requirements.html` as
  a **render class** file (the same write class as `tasks.md` and `goal.yaml`), read-only and exempt
  from the `.human`/`.ai`/`.collab` authorship-suffix convention of `cast-init-conventions.collab.md`.
- **Scenario 3:** WHEN any render runs, THE SYSTEM SHALL read the canonical `.collab.md` only and never
  write it (the FR-007 read-only guarantee), writing the `.html` atomically so a crash mid-write leaves
  either the whole old file or the whole new file.

### US5 — Zero-click extraction of the above-the-fold view (Priority: P2)

**As a** downstream consumer (the checker, a snapshot test), **I want to** extract just the
zero-click surface from a render, **so that** I can evaluate what a reader sees before expanding any
disclosure.

**Independent test:** `extract_zero_click_view(html)` returns the Goal Card and every `<summary>`
while dropping the bodies of closed `<details>`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `extract_zero_click_view(html: str) -> str` runs on a render, THE SYSTEM SHALL
  keep the always-open surface and each `<summary>` and drop the body of every closed `<details>`.
- **Scenario 2:** WHEN `bin/cast-render-zero-click` is invoked on unreadable input, THE SYSTEM SHALL
  exit 2.

### US6 — SC-001 checker agent as the WHAT-comprehension gate (Priority: P1)

**As a** phase owner, **I want to** an agent to read the render as an unfamiliar reader and restate
the job/outcome/scope, **so that** a render that fails the two-minute test fails the gate.

**Independent test:** The `cast-requirements-checker` agent, given a render, returns the canonical
verdict JSON; the binary PASS rule reads `can_state_what` and `missing[]`, never `score`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `cast-requirements-checker` evaluates a render, THE SYSTEM SHALL return a bare
  JSON object (no code fences) with fields `can_state_what`, `restated_job`, `restated_outcome`,
  `restated_scope` (`{in: [], out: []}`), `missing`, `score`, and `issues`; the four
  delegation-mandated fields are `can_state_what`, `restated_job`, `missing`, and `score`.
- **Scenario 2:** WHEN deciding pass/fail, THE SYSTEM SHALL pass only when `can_state_what == true` AND
  no `missing[]` entry names job, outcome, or scope — the gate is the boolean, never the `score` float.
- **Scenario 3:** WHEN the checker runs, THE SYSTEM SHALL operate as a subagent-mode agent outside the
  delegation + output-json contracts — it returns bare JSON and writes no `.output.json` envelope.

### US7 — Phase 4 DOM contract: selectable units, no ids or anchors (Priority: P1)

**As a** Phase 4 implementer, **I want to** anchor commentary to rendered blocks by stored quote, **so
that** the render needs no element ids or anchor attributes and stays a clean reading artifact.

**Independent test:** A golden structural test asserts every rendered block is one semantic element
under a real heading, with contiguous selectable text and **no** `id=` and **no** `data-block-anchor`
attributes anywhere.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a block is rendered, THE SYSTEM SHALL emit it as a single semantic
  `<section>`/`<li>` with contiguous text (no per-word/per-line span fragmentation, no `user-select`
  suppression) under a real `<h2>`/`<h3>` heading.
- **Scenario 2:** WHEN the document is rendered, THE SYSTEM SHALL emit **no** element `id` attributes
  and **no** `data-block-anchor` attributes; Phase 4 stores the quoted text and re-derives placement
  from the nearest enclosing heading.

### US8 — Same-door comment authoring (human and agent through one endpoint) (Priority: P1)

> **Updated (v8) — anchoring re-targeted to the render snapshot.** A comment's anchor is now minted
> against / validated against the **published render snapshot's container text** (`anchor_space='render'`),
> not the canonical `.collab.md`. A server-resolved `block_ref` (the canonical id of the enclosing
> labeled unit container) bridges the render-space quote back to source space and is **NEVER accepted
> from the client** (trust boundary: a spoofed `block_ref` would mis-route a future change-request — it
> stays out of the POST body schema). `create_comment` gains keyword-only `served_render_html` (a test
> seam; production reads the served `.html` off disk) and stores `block_ref` + `anchor_space` (additive
> columns; old rows default `'source'`). A `block_ref` of `None` on a **ref-less render** (zero anchor
> labels — a `pilot_poc`/`random_idea` page by design) is a **placed-comment SUCCESS**, never an
> unplaced miss to retry/badge. The same-door / `author_kind`-only / dual-parity / `422`/`404` contract
> below is otherwise unchanged. See FR-057.

**As a** reviewer (a human selecting text, or an agent curling the API), **I want to** leave a comment
anchored to a quoted span, **so that** the comment surfaces on the render and the goal is marked
unconverged — with no privileged write path for the UI.

**Independent test:** `POST /api/goals/{slug}/requirements/comments` with `{quoted_text, body}` creates
one row via a single `create_comment` call; the JSON 201 and the HTMX `thread_item.html` fragment
describe the **same** row modulo id/`author_kind` — one code path, asserted by the dual-assertion test.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a comment is posted to the comment endpoint, THE SYSTEM SHALL persist it through
  the flat `create_comment(goal_slug, quoted_text, section_hint, body, author, author_kind="human", *,
  version=None, db_path=None) -> dict` (version defaults to the current snapshot, `0` if none) and write
  its `created` `comment_events` row in the **same** transaction.
- **Scenario 2:** WHEN the request carries `HX-Request: true`, THE SYSTEM SHALL return the
  `thread_item.html` fragment; otherwise THE SYSTEM SHALL return a JSON `201`; the row is identical
  across the two paths and `author_kind ∈ {human, agent}` is the **only** human/agent distinction
  (FR-013 — no differing code path).
- **Scenario 3:** WHEN `quoted_text` or `body` is empty after stripping, or exceeds 10 KB, THE SYSTEM
  SHALL return `422` and persist nothing.
- **Scenario 4:** WHEN the slug is unknown, THE SYSTEM SHALL return `404` after validating it via
  `goal_service.get_goal` (the path-traversal rule), on every requirements endpoint.

### US9 — Comment state machine with deterministic guards (Priority: P1)

**As a** reviewer, **I want to** resolve, reopen, relocate, or orphan a comment, **so that** the
comment's lifecycle is auditable and an invalid transition or a non-verbatim relocate cannot silently
corrupt an anchor.

**Independent test:** `resolve` on an already-resolved comment returns `409`; `relocate` with a
`new_quoted_text` that is not a verbatim substring of the current goal file returns `422` and changes
no row; every accepted transition appends exactly one `comment_events` row in the same transaction.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `POST …/comments/{id}/resolve` runs on an open comment, THE SYSTEM SHALL flip it
  to `resolved` and append a `resolved` event in one transaction; a second resolve SHALL return `409`
  (`CommentStateError`). `reopen` is the inverse (`409` if already open).
- **Scenario 2:** WHEN `POST …/comments/{id}/relocate` runs with `{new_quoted_text, new_section_hint?}`,
  THE SYSTEM SHALL accept it **only if** `new_quoted_text` is a verbatim substring of the current goal
  file, else return `422` with no row change; on success it stores the old quote in the event `payload`
  JSON (`relocate_comment`).
- **Scenario 3:** WHEN `POST …/comments/{id}/orphan` runs, THE SYSTEM SHALL flip the comment to
  `orphaned` and append an `orphaned` event; an unknown comment id SHALL return `404`
  (`CommentNotFound`).
- **Scenario 4:** WHEN any state read is needed, THE SYSTEM SHALL derive convergence and displacement —
  never store them; `open_comment_count(goal_slug) > 0` is the sole convergence input.

### US10 — Versioned snapshots, carry-forward, and convergence (Priority: P1)

**As a** maintainer running the iteration loop, **I want to** snapshot the current requirements into a
new version that carries open comments forward and reports convergence, **so that** unresolved comments
drive the next version and older versions stay queryable with their as-of resolution state.

**Independent test:** `POST /api/goals/{slug}/requirements/versions` reads the current goal file,
snapshots a new version, archives the prior one in the same transaction, and returns the `create_next`
contract dict; open comments keep their original `version` (carry-forward by doing nothing); the goal
folder never gains a second requirements file.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a new version is requested, THE SYSTEM SHALL call `create_next(goal_slug,
  content, created_by, *, db_path=None) -> dict` returning `{version, convergence:
  "converged"|"unconverged", open_comments, displaced_comment_ids}`, wrapping `create_snapshot` (hash
  idempotency, single-transaction archive-flip, `BEGIN IMMEDIATE`).
- **Scenario 2:** WHEN open comments exist at snapshot time, THE SYSTEM SHALL set `convergence =
  "unconverged"` (the rule: `unconverged` **iff** `open_comment_count > 0`), carry every open comment
  forward unchanged (its row keeps its original `version`), and never refuse — open comments *drive* the
  new version.
- **Scenario 3:** WHEN computing `displaced_comment_ids`, THE SYSTEM SHALL list exactly the open
  comments whose `quoted_text` is NOT a verbatim substring of the new `content` — a pure string-find
  with no LLM and no subprocess (the seam the agent loop dispatches `cast-comment-reanchor` over).
- **Scenario 4:** WHEN `GET …/requirements/versions/{n}` is requested, THE SYSTEM SHALL return the
  version row plus its comments each stamped with the resolution state reconstructed (`_state_as_of`)
  from the append-only `comment_events` trail at that version's supersession instant; a missing goal
  file on `POST /versions` SHALL return `409` and the server SHALL read — never write — the goal file
  (FR-011 / delegation contract).

### US11 — Deterministic block diff and the tracked-changes view (Priority: P1)

**As a** reader (and Phase 5), **I want to** see a deterministic, block-level summary of what changed
between two versions and a tracked-changes render, **so that** a narration layer can describe the diff
but never invent entries.

**Independent test:** `summarize(diff_blocks(old, new))` is a pure, deterministic dict; `GET
…/requirements/changes` returns that same JSON byte-for-byte (or the HTMX "What changed" panel); `GET
/goals/{slug}/render/diff` serves the tracked-changes view fresh, never written to the goal folder.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff`
  runs, THE SYSTEM SHALL partition every block exactly once — every old block across `removed ∪
  modified.old ∪ unchanged.old`, every new block across `added ∪ modified.new ∪ unchanged.new` — with
  a pure move landing in `unchanged` (set arithmetic has no "moved"); the function performs no I/O, no
  DB, and no LLM call.
- **Scenario 2:** WHEN `summarize(diff)` runs, THE SYSTEM SHALL emit `{counts, items}` in a stable
  order (added → modified → removed; `unchanged` counted, never itemized) so the dict is
  byte-deterministic; an LLM may narrate these rows but SHALL never add entries not present.
- **Scenario 3:** WHEN `GET …/requirements/changes?base=N&head=M` is requested (default `head=current`,
  `base=head−1`), THE SYSTEM SHALL negotiate `summarize()` JSON | the `changes_panel.html` fragment;
  `base >= head` SHALL return `422`, an unknown version `404`, an unparseable snapshot `422` (never a
  `500`).
- **Scenario 4:** WHEN `GET /goals/{slug}/render/diff?base=N&head=M` is requested, THE SYSTEM SHALL
  render the tracked-changes view via `render_diff(old, new, *, base_version, head_version)`, served
  fresh and never persisted; `< 2 versions` SHALL return a `200` "no prior version" card, `base >= head`
  `422`, an unknown slug `404`.

### US12 — Derived displacement surfaced in the tray (lazy, never stored) (Priority: P1)

> **Updated (v8) — displacement computed in render space.** For a `render`-space comment, `displaced`
> is computed against the **served render's container text** (the published artifact the quote was
> minted against), resolved via the shared `container_text_index` walker — not the canonical source.
> `list_comments` chooses the comparison space per the comment's `anchor_space` (`render` → served
> render text via the `render_text` seam else looked up on disk; legacy `source` → the `.collab.md` via
> `current_text`), and a missing render degrades to the source check, never a crash. A ref-less-render
> NULL `block_ref` is **not** special-cased — displacement is purely "is the quote present in the served
> render text". The detector stays read-time / never-stored; Scenario 1 below reads through this
> re-target. See FR-057.

**As a** reviewer, **I want to** see which open comments no longer match the current text in a surfaced
tray, **so that** displacement is always visible without the save path storing anything positional.

**Independent test:** `list_comments(goal_slug)` stamps a derived `displaced: bool` on each **open**
comment by comparing its `quoted_text` against the current goal file at read time; a human save writes
no displacement state; the next `GET /comments` recomputes it.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN comments are listed, THE SYSTEM SHALL compute `displaced` per open comment as
  "the `quoted_text` is not found verbatim in the current file" — a read-time property only; orphaned
  and resolved comments are not stamped.
- **Scenario 2:** WHEN the render's tray is filled (`GET …/comments` → `tray.html`), THE SYSTEM SHALL
  group comments as open / displaced ("Needs re-anchor") / orphaned ("Triage") / resolved (collapsed),
  and a displaced open comment SHALL appear in the tray rather than as a `<mark>` on the body.
- **Scenario 3:** WHEN a human edits and saves the canonical `.collab.md`, THE SYSTEM SHALL add **no**
  new machinery to the save path (decision #1, "lazy + surfaced tray"); re-anchoring runs only at the
  next agent touchpoint (`create_next`), never on a human save.

### US13 — The re-anchor subagent surfaces orphans, never guesses (Priority: P1)

**As a** phase owner, **I want to** a dedicated subagent to re-locate displaced comments by their
stored quote and surface orphans explicitly, **so that** a confident mis-placement (silent data loss)
is impossible and a low-confidence case becomes a visible orphan.

**Independent test:** `cast-comment-reanchor` returns EXACTLY ONE bare JSON object matching the verdict
schema (no prose, no fences, no `.output.json` envelope); the route's relocate `422` substring backstop
rejects any non-verbatim `new_quoted_text` the agent might emit.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `cast-comment-reanchor` runs over `{displaced open comments, OLD content, NEW
  content}`, THE SYSTEM SHALL return `{"verdicts": [{"comment_id", "verdict": "relocated|orphaned",
  "new_quoted_text": "str|null", "new_section_hint": "str|null", "confidence": float, "reasoning":
  "str"}]}` as one bare JSON object — the documented subagent carve-out from
  `cast-delegation-contract.collab.md` (no envelope), like the classifier/checker precedent.
- **Scenario 2:** WHEN the agent is uncertain, THE SYSTEM SHALL prefer `orphaned` over a low-confidence
  relocate (decision #9 — an orphan is surfaced and recoverable; a confident mis-placement is not), and
  `new_quoted_text` SHALL always be a verbatim substring of the new document or `null`.
- **Scenario 3:** WHEN the agent loop applies a verdict, THE SYSTEM SHALL route it through the same-door
  `relocate`/`orphan` endpoints; a relocate whose quote fails the route's verbatim-substring check
  (`422`) SHALL downgrade to `orphan` (graceful, never silent corruption); a failed/timed-out/garbage
  dispatch SHALL be an explicit no-op (comments stay in the tray; the next cycle retries).
- **Scenario 4 (contract v2, Phase 4b):** WHEN `cast-comment-reanchor` is called with the **optional**
  `change_set` (a `summarize()` dict) and per-comment block context (`block_ref`/`block_disposition`),
  THE SYSTEM SHALL accept a backward-compatible **superset** — a legacy `{comments, old_content,
  new_content}` call (no `change_set`) behaves byte-identically to v1 (verdicts only, `narration`
  null) — and MAY emit a third `resolved` verdict (only on a demonstrable fix, bias order `relocated >
  resolved > orphaned`-when-unsure) plus a `narration` object whose every `item_note` keys to a
  `change_set.items` entry (never added/reworded); `new_quoted_text` SHALL stay a verbatim substring of
  `new_content` and SHOULD avoid inline-markdown markers so it places on the stripped-carriage DOM. The
  agent stays the bare-JSON subagent carve-out (`model: sonnet`, no `.output.json` envelope).
- **Scenario 5 (contract v3, v8 — render-space reanchor):** WHEN `cast-comment-reanchor` is called with
  the **optional** render-space context — the comment's prior-render container text (by `block_ref`) and
  the candidate new-render container text — THE SYSTEM SHALL accept a backward-compatible **superset of
  v2**: every new input is optional, so every existing call site (v1 and v2) stays byte-valid (same
  precedent as v2-over-v1). The verdict vocabulary (`relocated > resolved > orphaned`-when-unsure), the
  safety machinery (orphan-over-guess, the route `422` verbatim backstop, no-op-on-garbage), and the
  `model: sonnet` bare-JSON carve-out carry **untouched**. In **UPDATE** mode the dispatch runs **once at
  the publish boundary** over the job's expected-miss comments (FR-059), never per-attempt; a crash /
  unparseable / non-verbatim verdict leaves the comment **open + badged**, never dropped. See FR-044.

### US14 — The maker pipeline produces the render (the happy path) (Priority: P1)

**As a** reader opening a goal's render, **I want to** see a bespoke, family-appropriate page produced
by the WHAT→HOW maker pipeline, **so that** the requirements read like a purpose-built communication
artifact rather than a one-size-fits-all template dump.

**Independent test:** Two different work-families rendered through the real pipeline produce visibly
distinct pages whose section-heading sets differ and contain **no** `US`/`FR`/`SC` slot names; both
pass `maker_gate.check_html`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a non-stub render is generated on the happy path, THE SYSTEM SHALL produce it
  through the named-stage pipeline `run_what → gate_what → run_how → gate_html → publish` in
  `render_job_service`, where `cast-requirements-what` emits the WHAT doc (`cast-requirements-what/v1`
  front matter + communication-intent body) and `cast-requirements-how` emits one self-contained HTML
  document between `<!-- BEGIN RENDER -->`/`<!-- END RENDER -->` sentinels (strict first-pair
  extraction; anything else counts as no-output).
- **Scenario 2:** WHEN either maker agent runs, THE SYSTEM SHALL invoke it as a tool-free `claude -p`
  subagent (`dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `allowed_delegations: []`, `model: opus`) with `--tools ""` and clean child env (`env -u CLAUDECODE`
  + explicit job-dir cwd), so the maker **structurally cannot** write the canonical `.collab.md`.
- **Scenario 3:** WHEN a structural gate (`gate_what` / `gate_html`) reports a violation, THE SYSTEM
  SHALL run exactly **one** structural retry of that stage with the violation strings fed back as
  prompt feedback before proceeding to `publish`; WHAT-doc section names are family-communication
  names, **never** `US`/`FR`/`SC` slot names, and the WHAT layer never invents content absent from the
  source.

### US15 — Background generation with a live generating state (Priority: P1)

**As a** reader requesting a stale or never-rendered page, **I want to** get an immediate "generating…"
state that swaps in the finished render, **so that** a page view never blocks on the maker and never
pops a terminal.

**Independent test:** A changed source served via `GET /goals/{slug}/render` returns 200 immediately
with a generating state; polling `GET /goals/{slug}/render/status` returns `generating` then `ready`,
at which point the finished render is served; a cached (fresh-hash) view never starts a job.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `GET /goals/{slug}/render` resolves to `generating` (stale or missing render),
  THE SYSTEM SHALL start the idempotent single-flight background job for `(goal_slug, source_hash)`
  and immediately return 200 with a live generating state — the prior stale render plus a regenerating
  banner when one exists, else a dedicated generating page — leaving any on-disk `.html` byte-stable.
- **Scenario 2:** WHEN `GET /goals/{slug}/render/status` is polled, THE SYSTEM SHALL return JSON
  `{state, source_hash}` with `state ∈ ready` / `generating` / `failed`, where `ready` is a **pure
  artifact-hash derivation** (the served file's embedded `source-hash` equals the current source hash,
  covering maker, flagged, and fallback publishes alike) and `failed` is returned **only** when nothing
  servable exists for the current hash AND its latest `render_jobs` row is terminal-`failed`.
- **Scenario 3:** WHEN the render is already fresh (cache hit), a stub, a 404, or any comment-API
  request, THE SYSTEM SHALL serve it without starting or waiting on a generation job; a stub is served
  by the synchronous deterministic prompt-to-begin render (US3) and reports `ready` to the poller.

### US16 — Logical id backbone and verbatim carriage (Priority: P1)

> **⚠️ SUPERSEDED IN PART (v8).** The blanket **verbatim-carriage** obligation on leaf requirement text
> is **removed**. What SURVIVES unchanged and stays HARD: (1) each canonical id printed verbatim exactly
> once as a visible anchor label (Scenario 1), and (2) one contiguous semantic container per unit — the
> one-unit-one-container DOM rule (Scenario 3). What is REMOVED: the Scenario-2 copy-exact obligation
> that each unit's inline-markdown-stripped source body appear **verbatim and contiguous** in CREATE
> mode — **CREATE now optimizes for the most human-readable page and MAY paraphrase / distill leaf
> text.** Verbatim carriage was only ever a proxy that kept *source-anchored* comments placeable; v8
> moves comment anchoring to the render snapshot (US8/US12/US19 below, FR-057), so the proxy is retired.
> In **UPDATE** mode unchanged unit containers are kept byte-identical by the deterministic splice — a
> stronger guarantee than carriage, by construction (FR-055/FR-056). Scenario 2 below is read through
> this supersession: it now governs only UPDATE byte-identity of unchanged containers, not a blanket
> CREATE carriage requirement.

**As a** Phase 4b diff agent (and a reader scanning anchors), **I want to** the canonical ids carried
through the maker render verbatim as a non-DOM structure with each unit's source text carried
verbatim, **so that** every requirement unit stays traceable and re-anchorable without reintroducing
element ids.

**Independent test:** A maker render is checked by `maker_gate.check_html`: every canonical id from the
WHAT doc appears verbatim exactly once as a visible anchor label (none invented, none renamed), each
unit's inline-markdown-stripped source body appears verbatim and contiguous within one semantic
container, and the document carries **no** `id=` and **no** `data-block-anchor` attributes.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the maker renders, THE SYSTEM SHALL treat the canonical `US-NN`/`FR-NNN`/`SC-NNN`
  ids (assigned upstream by the deterministic parser) as a **logical, non-DOM backbone**: each id is
  emitted verbatim exactly once as a small visible anchor label, never invented or renamed, and the
  WHAT-doc `sections[].block_refs` id mapping is the structure the Phase 4b diff agent reads.
- **Scenario 2:** WHEN `check_html` validates a maker render, THE SYSTEM SHALL REQUIRE each requirement
  unit's anchorable text — its source body with inline markdown stripped via the single
  `strip_inline_markdown` — to appear **verbatim and contiguous** within one semantic container,
  asserted through the shared `container_text_index(html)` walker in `maker_gate.py`. *(**SUPERSEDED in
  CREATE mode, v8:** this leaf-text copy-exact requirement no longer applies to a CREATE render, which
  may paraphrase/distill for readability; it now governs only **UPDATE** mode, where unchanged unit
  containers are kept byte-identical by the deterministic splice and verified by `check_update_fidelity`
  on NORMALIZED container text — FR-056. The empty-shell guard, FR-060, replaces it as the CREATE-mode
  floor against degenerate output.)*
- **Scenario 3:** WHEN any maker render is emitted, THE SYSTEM SHALL preserve the US7/FR-012/FR-013 DOM
  contract unchanged (one contiguous semantic `<section>`/`<li>` per unit under a real `<h2>`/`<h3>`,
  zero `id=`, zero `data-block-anchor`); the logical id backbone is metadata printed as labels, never a
  DOM anchor. *(Rationale recorded: the real orphan-exposure risk is silent `<mark>`-placement loss on
  a paraphrased DOM, not DB orphaning — verbatim carriage is what keeps quote-anchoring sound.)*

### US17 — Two-branch degradation: literal-no-output fallback vs. structural-violation override (Priority: P1)

**As a** phase owner, **I want to** a no-output maker failure to fall to the deterministic page while a
structural-gate failure serves the flagged best attempt, **so that** every degradation is surfaced
(never the deterministic page silently swapped in for a quality miss) and a reader always sees the
truth about what they're looking at.

**Independent test:** A maker producing no extractable HTML yields a `fallback` job row and the
deterministic page; a maker producing extractable HTML that exhausts the structural gate yields a
`flagged` job row, a `served-by: structural_violation` artifact stamp, and a reader-visible "needs
review" badge — never the deterministic page.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `publish` finds no extractable HTML at all (Branch 1 — literal no-output:
  crash / timeout / empty / unparseable-by-extraction), THE SYSTEM SHALL serve the deterministic
  `render_requirements()` fallback page and record a `fallback` job status with the reason in the
  `error` field — this is the **only** trigger of the deterministic fallback.
- **Scenario 2:** WHEN `publish` has extractable HTML that exhausts the structural gate after its retry
  (Branch 2 — the **owner override**), THE SYSTEM SHALL publish the **best attempt** via
  `publish_maker_html(..., served_by="structural_violation")`, record a `flagged` job status with the
  joined gate violations in `error`, and the `/render` read path SHALL inject a reader-visible "needs
  review" badge from the `served-by` stamp — it SHALL **not** fall to the deterministic page.
- **Scenario 3:** WHEN `publish` re-reads the source hash and it has moved, THE SYSTEM SHALL record a
  `superseded` job and write nothing; every terminal job state (`published`/`flagged`/`fallback`/
  `superseded`/`failed`) is a `render_jobs` row carrying its reason, so no degradation is ever silent
  ("surface, don't suppress"). *(The richer human-review flag columns + LLM quality score that layer on
  top of this `flagged` status + `served-by` stamp are Phase 4a scope — forward pointer only.)*

### US18 — The LLM quality gate and the quality-driven rework loop (Priority: P1)

**As a** reader opening a goal's render, **I want to** every maker page to clear a single
comprehension-and-visual quality bar before I ever see it, **so that** a structurally-clean but
communicatively-bad render is reworked (or flagged for review) rather than published silently.

**Independent test:** A structurally-VALID but communicatively-bad attempt (the committed
`low_quality_attempt.html`) PASSES `maker_gate.check_html` yet FAILS `checker_verdict.derive_pass`;
driven through `_execute_pipeline` with an injected failing-then-passing checker it reworks and then
publishes clean, and with an always-failing checker it serves the best attempt flagged `human_review=1`
— never the deterministic page.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a maker attempt has been produced and passed `gate_html`, THE SYSTEM SHALL run
  `cast-requirements-render-checker` over the rendered artifact + family label (zero-click view first,
  then full HTML) and compute the binary PASS **code-side** via `checker_verdict.derive_pass`
  (`can_state_what` AND no gated `missing[]` token AND zero `severity:"error"` issues in either
  dimension); the agent-emitted `score` float never decides the gate, and the ranking score is
  `canonical_score` recomputed from issue counts.
- **Scenario 2:** WHEN an attempt fails the quality OR structural gate AND the ceiling
  (`QUALITY_MAX_ATTEMPTS`) and the consecutive-structural stop (`QUALITY_STRUCTURAL_STOP`) are not yet
  hit, THE SYSTEM SHALL rework with provenance-tagged feedback (deterministic structural violations as
  hard requirements; the checker's `rework_feedback` as quality guidance), escalating to a forced
  `run_what` re-gen when three consecutive verdicts name the same gated WHAT token (bounded by
  `QUALITY_MAX_WHAT_REWORKS`, retaining the prior good WHAT if the re-gen fails its own gate).
- **Scenario 3:** WHEN the loop reaches a terminal state, THE SYSTEM SHALL apply the **PREFER VALID,
  THEN SCORE** policy of FR-039 — a clean attempt publishes immediately (`served-by: maker`, no flag);
  otherwise the best attempt is served flagged — and the loop SHALL be bounded **only** by the
  anti-infinite-loop ceiling, never by a cost / latency / model-tier budget (owner decision, binding).

### US19 — Open comments survive the maker render (Priority: P1)

> **Reoriented (v8) — survival is a render-space property.** *In-block* = the quote placed inside a
> labeled unit container on the render it was minted against; *survival* = it places in the same
> `block_ref`'s container on the next render. In **UPDATE** mode the deterministic splice keeps unchanged
> unit containers byte-identical, so survival of a comment on an **unchanged** block is **structural** (no
> reanchor needed). A comment on a **modified/removed** block is an **expected miss** that routes to the
> ONE publish-boundary `cast-comment-reanchor` v3 dispatch (relocate / resolve / orphan) — never blocking
> the publish, never silently dropped, never auto-resolved; an expected miss never flips `passed`. The
> DECISION #10 OVERRIDE (an in-block CREATE miss → flagged best-attempt + `.comment-unplaced` badge;
> deterministic page only on literal no-output) carries unchanged. Scenarios below read through this
> render-space reorientation. See FR-058/FR-059.

**As a** reviewer whose open comments anchor to a verbatim quote, **I want to** every open comment to
still place on a freshly-regenerated maker DOM (or have its loss made visible), **so that** a maker
regenerate leaves every comment anchored with zero new orphans and a placement miss is surfaced,
never silently dropped.

**Independent test:** `check_comment_survival(html, parsed, comments)` walks the candidate HTML once
via the shared `container_text_index` walker and returns a `SurvivalReport` (`passed`, `violations`,
`unplaced`, `placed`); an in-block quote that fails to place yields a prompt-ready violation and
`passed=False`, while a cross-boundary quote that fails to place is recorded in `unplaced` but never
flips `passed`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the survival gate classifies an open comment whose `quoted_text` is a substring
  of some block's anchorable text (**in-block**), THE SYSTEM SHALL require it to place in that block's
  container (1b container-text semantics); a miss SHALL be a witnessed verbatim-carriage violation that
  flips `passed=False`, is added to `violations` and `unplaced`, and (via `gate_html`) merges into the
  **same** `html_report.violations` structural channel.
- **Scenario 2:** WHEN the survival gate classifies a **cross-boundary** quote (not within any single
  block's anchorable text — spans blocks, a markdown-strip seam, or render decoration), THE SYSTEM
  SHALL record a miss in `unplaced` only, **never** as a `violation` and never flipping `passed` (it
  can fail on the deterministic substrate too) — the classifier is retained, the downstream blocking
  is not.
- **Scenario 3:** WHEN an in-block survival miss reaches `publish` under the DECISION #10 OVERRIDE,
  THE SYSTEM SHALL serve the **best attempt flagged** (`served-by: structural_violation`) rather than
  block publish or swap in the deterministic page (which fires only on literal no-output); both
  in-block and cross-boundary misses additionally surface read-time as a `.comment-unplaced` tray
  badge toggled by `requirements_comments.js` when `highlight()` returns `false` — nothing about the
  miss is stored.

### US20 — Diff narration: stored once per version cut, validated, attachment-only (Priority: P1)

**As a** reader of the "What changed" panel, **I want to** an LLM-authored narration that describes
the deterministic change set without ever inventing a change, **so that** the panel can read like prose
yet structurally cannot show a change absent from the source.

**Independent test:** `POST …/versions/{head}/narration` recomputes `summarize(diff_blocks(old, new))`
server-side and accepts the body **only** when every `item_note` keys to a deterministic `summarize()`
item (any mismatch → `422` all-or-nothing listing the offending keys); `GET …/changes` then returns
the stored narration as a sibling key while `counts`/`items` stay byte-for-byte `summarize()`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a parent that cut a version posts a narration, THE SYSTEM SHALL validate the
  slug (`goal_service.get_goal`, unknown → 404), recompute the deterministic change set server-side,
  and persist `overview` + `item_notes` to the `version_diff_narrations` row (`UNIQUE(goal_slug,
  base_version, head_version)` → a re-post UPSERTS, never duplicates), with size caps mirroring FR-017
  (`overview` ≤ 2 KB, each note ≤ 2 KB, ≤ 1 note per item) and `created_by` riding the body same-door.
- **Scenario 2:** WHEN any `item_note` key does **not** equal a recomputed `summarize().items` entry,
  THE SYSTEM SHALL reject the whole post with `422` listing the offending keys (no silent
  note-dropping); the deterministic change set is the source of truth and the narration only decorates.
- **Scenario 3:** WHEN the "What changed" panel renders, THE SYSTEM SHALL attach each stored note to
  its deterministic item by `(change, heading_or_ref)` lookup and flow the LLM-authored text through
  the autoescaped Jinja template (never `innerHTML` / `| safe`); a version cut with no narration simply
  shows the deterministic panel (the floor), so the UI **cannot** show an invented change.

### US21 — Gap-fill: the maker fills genuine comprehension gaps by asking upstream, never fabricating (Priority: P1)

**As a** reader of a family render, **I want to** see a genuinely-missing detail either supplied from the
goal's own upstream artifacts or honestly marked as a gap, **so that** the page never ships a silently
incomplete explanation **and** never invents requirement content to paper over a hole.

**Independent test:** inject a gap (delete a key detail a block needs) into a corpus doc and regenerate;
the render either (a) supplies the detail — but only by emitting a change-request through the **unchanged**
v2 same-door gate, leaving canonical untouched until human approval, the page showing a `.rr-gap` marker
until the approved detail lands and the next view regenerates from canonical — or (b) marks the gap with
a posed question + a fixed status string; the page **never** renders an un-approved proposed answer as
requirement content, and the server-side `validate_evidence` demotes any answer whose evidence quote does
not verbatim-locate in the corpus allowlist.

**Acceptance scenarios (EARS-style):**

- **Scenario 1 (ask, never fabricate):** WHEN the WHAT layer detects a gap that "would materially help the
  reader" (bounded by `GAPFILL_MAX_GAPS`, default 5), THE SYSTEM SHALL name it in the WHAT doc's `gaps[]`
  (gate-enforced: unique sequential `gap_id`, every `block_refs` member a real `Block.ref`, a non-empty
  `question`, and **never** an answer) and ask upstream via the tool-free `cast-requirements-gapfill`
  subagent over an explicit corpus allowlist (the goal's own upstream artifacts only — never the wider
  repo), which supplies a detail **only** with a verbatim evidence quote or **refuses** ("when in doubt,
  REFUSE" — refusal is a correct answer the page reports honestly).
- **Scenario 2 (the FR-016 structural invariant):** WHEN the agent supplies a grounded detail, THE SYSTEM
  SHALL route it **only** as a `kind="addition"` change-request through `change_request_service.create`
  (the governed write path, consumed byte-unchanged) under the goal's **GATE-ALL** policy (every gap CR
  intakes `proposed` and waits for explicit human approval); the maker NEVER consumes the answer directly,
  the `proposed_body` lives solely on the CR review surface, and the gap un-marks **only** when the
  approved detail lands in canonical, bumps the version, changes the source hash, and the next view
  regenerates — there is **no** special un-mark path and **no** code path by which un-approved text reaches
  a reader.
- **Scenario 3 (honest marker):** WHEN a gap cannot be filled (corpus cannot supply, the answer was
  declined, the proposal was rejected, or the ask failed), THE SYSTEM SHALL render a `.rr-gap` callout =
  the `question` + **exactly one** fixed status string from the marker vocabulary (`cr-proposed` →
  "…proposed upstream, awaiting review"; `unfilled-cannot-supply` → "missing — upstream could not supply
  it"; `unfilled-declined` → "missing — a proposed detail was declined"; `unfilled-ask-failed` → "missing
  from the requirements"), the marker being **class-based only** (zero `id=`, zero `data-block-anchor`, the
  v2 DOM contract preserved) so carriage + survival gates stay green on a marked render; the checker grants
  gap amnesty (a surfaced gap is honest source-gap communication, not a comprehension defect).

### US22 — The phase-tab viewer renders render-class `.html` alongside `.md` (Priority: P1)

**As a** reader of a goal's phase tab, **I want to** see a render-class `.html` artifact embedded in the
viewer the same place I read its `.md` source, **so that** a rendered surface (refined-requirements today,
exploration tomorrow) is reachable without leaving the goal screen for the standalone `/render` page.

**Independent test:** A requirements phase tab whose goal directory holds both a `.collab.md` and a
`refined_requirements.html` renders the markdown in a `markdown-body` div AND embeds the html inside an
`<iframe srcdoc>` whose decoded content equals the file bytes verbatim; the html artifact shows **no** edit
button (render-class), and a tab with only `.md` artifacts emits no iframe (the md path is unchanged).

**Acceptance scenarios (EARS-style):**

- **Scenario 1 (dual render):** WHEN a phase tab collects a directory's artifacts, THE SYSTEM SHALL admit
  both `.md` and `.html`, tagging each artifact dict with a `kind` discriminator (`markdown` | `html`);
  `.md` is rendered to HTML as today, `.html` carries its **verbatim file bytes** (never
  `md.markdown()`-processed) so a full standalone document keeps its own `<head>`/`<style>`.
- **Scenario 2 (isolated embed):** WHEN a `kind="html"` artifact is rendered, THE SYSTEM SHALL embed it via
  `<iframe srcdoc>` in a **null-origin** sandbox (`allow-scripts allow-popups`, **never**
  `allow-same-origin`) so the document cannot read host cookies/DOM and its styles cannot collide with the
  host page; `allow-scripts` is present so the Phase 3b comment bridge can later run.
- **Scenario 3 (read-only, US4 reuse):** WHEN a `.html` artifact is surfaced, THE SYSTEM SHALL treat it as a
  **render-class** artifact (US4): read-only with **no** edit affordance (`authorship=None`) and exempt from
  the `.human`/`.ai`/`.collab` authorship-suffix convention — the **read** gate admits `.html`, the **edit**
  gate still rejects it, and the existing path-traversal guard applies to `.html` unchanged.
- **Scenario 4 (md path unchanged):** WHEN a phase tab holds only `.md` artifacts, THE SYSTEM SHALL render
  them exactly as before (the `kind="markdown"` default keeps every existing call site byte-identical) — no
  iframe, no regression.
- **Scenario 5 (consumer surface, US7 reuse):** WHEN the refined-requirements HTML exists on disk, THE
  SYSTEM SHALL surface it in the requirements phase tab as render **consumer #2** (exploration is consumer
  #1) **without** retiring the `/render` route; the rendered DOM keeps the US7 contract (selectable units,
  zero `id=`/`data-block-anchor`) so Phase 3b's verbatim-substring anchoring and the `anchor_space='render'`
  path keep working. **Out of scope here:** in-iframe commenting (Phase 3b) and the exploration render
  pipeline (Phase 4).

### US23 — Diecast-wide commenting on any served `.html` via the host bridge (Priority: P1)

> **In scope as of v10 (was deferred in v9).** Selecting text in ANY served `.html` artifact in the dual
> viewer and submitting persists a same-door render-space comment keyed to **that** artifact. The hard
> part is two boundary crossings, both reused-not-rebuilt: the null-origin srcdoc can't `fetch` the
> same-door API (→ a **host postMessage bridge** proxies the POST), and the server's render resolver was
> requirements-hardwired (→ it becomes **artifact-keyed** by `artifact_ref`). No new anchoring algorithm
> and **no** stable anchor-id scheme — US7 holds; relocation stays verbatim-substring.

**As a** reviewer of any rendered artifact (refined-requirements today, `exploration.html` tomorrow),
**I want to** select text in the embedded render and leave a comment, **so that** it lands in the existing
same-door comment store anchored to the artifact I was reading — with no artifact-specific code.

**Independent test:** a jsdom unit test drives the host bridge with a registered frame and asserts a
`cch:submit` fans out to one same-door POST per comment carrying `{quoted_text, section_hint, body,
artifact_ref, author_kind}` and replies `cch:submitted` to the originating frame only; a foreign window
sends nothing. A server-contract test asserts that proxied POST body creates a render-space comment whose
stored `artifact_ref` is the one supplied (and that omitting it defaults to `refined_requirements.html`,
byte-compatible with v9).

**Acceptance scenarios (EARS-style):**

- **Scenario 1 (artifact-keyed anchor):** WHEN a comment is created with an `artifact_ref`, THE SYSTEM
  SHALL resolve the render-space anchor against THAT goal-relative served `.html` (validated containment,
  `.html`-only) and store `artifact_ref` on the row; WHEN `artifact_ref` is absent, THE SYSTEM SHALL
  resolve against `refined_requirements.html` (the back-compatible default) and store NULL — the
  requirements path stays byte-identical.
- **Scenario 2 (injected bridge-mode layer):** WHEN a render-class `.html` is served into the viewer
  iframe, THE SYSTEM SHALL inject the cast-comment-html layer (the SAME assets the standalone tool serves)
  before `</body>` in **bridge mode**, so Submit `postMessage`s a `{type:"cch:submit", goal_slug,
  artifact_ref, comments[]}` batch to the host instead of a (blocked) null-origin `fetch`.
- **Scenario 3 (source-identity guard):** WHEN the host receives a `message`, THE SYSTEM SHALL accept it
  ONLY when `event.source` is a `contentWindow` in its `artifact_ref → contentWindow` registry — origin is
  `"null"` for srcdoc and SHALL NOT be checked; a foreign window or a malformed payload issues **no** POST.
- **Scenario 4 (per-comment fan-out, reply to originator):** WHEN a valid batch arrives, THE SYSTEM SHALL
  issue ONE same-door POST per comment (a failure on one SHALL NOT abort the others) and `postMessage` a
  `{type:"cch:submitted", ok, results[]}` reply to the **originating** frame only (`targetOrigin "*"`),
  surfacing per-comment success/failure as a visible toast — never silently dropped.
- **Scenario 5 (multi-iframe, US7/US8 preserved):** WHEN a tab embeds several commentable iframes (e.g.
  `exploration.html` + `refined_requirements.html`), THE SYSTEM SHALL route each frame's submit and reply
  independently by source identity; the comment is authored through the ONE same-door create handler (no
  parallel route, US8) and the render DOM keeps US7 (no ids, verbatim-substring placement).

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `GET /goals/{slug}/render` (page route in `routes/pages.py`) serves the self-contained read-only render and returns 200 for a goal with refined requirements | Mirrors the existing `preso_review` page route |
| FR-002 | The HTML is built by the pure `render_requirements(parsed, *, version=None) -> RenderResult` (`{html, warnings}` frozen) — no I/O, no timestamps, deterministic | Goldens depend on determinism; I/O lives in the service |
| FR-003 | `rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None) -> Path \| None` regenerates the `.html` only when the source `content_hash` differs from the embedded `source-hash`; a fresh hash returns the file byte-identical (no write) | Lazy, atomic (temp-file + `os.replace`). **v4:** this is now the **fallback/stub** regenerator (the happy path is the background maker job — US14/US15); the hash-cache envelope here is reused unchanged by both branches |
| FR-004 | A known goal with absent or stub requirements (`is_stub`, `STUB_WORD_THRESHOLD = 200`, imported from the Phase 1 parser package) returns 200 prompt-to-begin | Stub predicate never redefined here |
| FR-005 | An unknown slug returns 404 after a goals-DB validation that also kills path traversal; a render exception logs, preserves any existing `.html`, and returns a plain 500 | No stack trace to the reader |
| FR-006 | The generated `goals/{slug}/refined_requirements.html` opens with an `<!-- AUTO-GENERATED: ... -->` header and a `<!-- source-hash: <content_hash> -->` comment | Self-contained artifact |
| FR-007 | `refined_requirements.html` is a **render-class** artifact (write class of `tasks.md`/`goal.yaml`), read-only and exempt from `.human`/`.ai`/`.collab` authorship suffixes; the canonical `.collab.md` is read-only and never written by a render | Records (does not extend) `cast-init-conventions.collab.md` |
| FR-008 | `extract_zero_click_view(html: str) -> str` keeps the always-open surface + every `<summary>` and drops closed `<details>` bodies; `bin/cast-render-zero-click` exits 2 on unreadable input | Zero-click contract |
| FR-009 | `cast-requirements-checker` returns the canonical verdict object (bare JSON, no fences): `can_state_what`, `restated_job`, `restated_outcome`, `restated_scope{in,out}`, `missing`, `score`, `issues` | Four mandated fields: `can_state_what`, `restated_job`, `missing`, `score` |
| FR-010 | The checker PASS rule is binary and code-checkable: `can_state_what == true` AND no `missing[]` entry naming job/outcome/scope; the `score` float never decides the gate | The gate is the boolean |
| FR-011 | The checker runs subagent-mode, **outside** `cast-delegation-contract.collab.md` and the output-json contract: bare JSON, no `.output.json` envelope | Same carve-out as the Phase 2 classifier; recorded, not extended |
| FR-012 | Every rendered block is one semantic, contiguous, text-selectable `<section>`/`<li>` under a real `<h2>`/`<h3>` heading, with no span fragmentation and no `user-select` suppression | Phase 4 "selectable unit" |
| FR-013 | The render emits **no** element `id` attributes and **no** `data-block-anchor` attributes; Phase 4 stores the quote and re-derives placement from the nearest heading | Stable-element-IDs design was superseded; do not reintroduce |
| FR-014 | The comment API lives at prefix `/api/goals/{goal_slug}/requirements` (`cast_server/routes/api_requirements.py`); every handler validates the slug via `goal_service.get_goal` first (unknown → 404) | Same path-traversal rule as the render route |
| FR-015 | `POST …/comments` is the canonical same-door handler: ONE `create_comment` call, negotiated JSON `201` \| `thread_item.html`; the row is identical across paths modulo id/`author_kind`; `author_kind ∈ {human, agent}` is the only human/agent distinction | THE dual-assertion agent-parity handler (the same-door rule) |
| FR-016 | `GET …/comments` (`?state=`) is negotiated JSON list \| `tray.html`; each open comment in the JSON carries a derived `displaced: bool` | Displacement is read-time, never stored |
| FR-017 | Comment content validation: empty-after-strip or `>10 KB` `quoted_text`/`body` → `422`, nothing persisted | Route-layer Pydantic validation; service stays thin |
| FR-018 | The comment state machine — `resolve`/`reopen`/`relocate`/`orphan` — is negotiated; `resolve` on a resolved comment (and `reopen` on an open one) → `409` (`CommentStateError`); each accepted transition appends exactly one `comment_events` row in the same transaction | Append-only audit trail; one txn per transition |
| FR-019 | `POST …/comments/{id}/relocate` accepts `{new_quoted_text, new_section_hint?}` only when `new_quoted_text` is a verbatim substring of the current goal file, else `422` with no row change; the old quote is stored in the event `payload` | The deterministic anchor backstop |
| FR-020 | `comment_service` exposes flat house-DB functions (`create_comment`, `list_comments`, `get_comment`, `resolve_comment`, `reopen_comment`, `relocate_comment`, `orphan_comment`, `open_comment_count`, `get_comment_events`) with injectable `db_path`; `CommentNotFound` → 404, `CommentStateError` → 409 | Naming contract — Phase 5 cites these verbatim |
| FR-021 | `requirement_version_service.create_next(goal_slug, content, created_by, *, db_path=None) -> dict` returns `{version, convergence, open_comments, displaced_comment_ids}`, wrapping `create_snapshot` (hash idempotency + single-txn archive-flip + `BEGIN IMMEDIATE`); open comments carry forward by keeping their original `version` | Never refuses on open comments — they drive new versions |
| FR-022 | Convergence is derived, never stored: a goal is `unconverged` **iff** `open_comment_count(goal_slug) > 0`; `displaced_comment_ids` is the verbatim string-find of open comments not present in the new content (no LLM, no subprocess) | The one-sentence convergence rule |
| FR-023 | `POST …/versions` reads the current goal file (missing → `409`) and returns the `create_next` dict (JSON only); `GET …/versions` returns `{versions, convergence, open_comment_count}`; `GET …/versions/{n}` returns the row plus comments with as-of resolution state reconstructed from `comment_events`. **v4b:** the version surface gains the same-door narration route `POST …/versions/{head}/narration` (US20) — the server still reads, never writes, the goal file | The server reads, never writes, the goal file |
| FR-024 | `block_diff.diff_blocks(old, new) -> BlockDiff` + `summarize(diff) -> dict` are pure, deterministic, I/O-free; they hold the partition invariant (every block appears exactly once); a pure move lands in `unchanged`. `GET …/changes` returns `summarize()` JSON \| the `changes_panel.html` panel. **v4b re-scope:** the byte-for-byte guarantee is scoped to the `counts`/`items` keys; an LLM-authored `narration` sibling key (US20) rides alongside without perturbing them | The cross-phase contract Phase 5 imports — extend, never fork; `block_diff`/`diff_render` stay unmodified |
| FR-025 | `GET /goals/{slug}/render/diff?base=N&head=M` serves the `render_diff(...)` tracked-changes view **fresh** (never written to the goal folder); the diff view MAY use transient `id="diff-{n}"` anchors generated per render — the **only** sanctioned exception to the render's zero-`id` thin-spine rule, scoped to this view, never stored, never a comment anchor; `<2 versions` → 200 card, `base>=head` → 422, unknown slug → 404 | Transient-id exception (decision #8) |
| FR-026 | Only the current `refined_requirements.collab.md` ever lives in the goal folder; all prior versions are `requirement_versions` DB rows with their comments and as-of state intact; no Phase 4 operation mutates the canonical `.collab.md` | The folder invariant + the render read-only guarantee, both preserved |
| FR-027 | `cast-comment-reanchor` (`agents/cast-comment-reanchor/`) runs subagent-mode (`model: sonnet`, `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`, `timeout_minutes: 10`, `allowed_delegations: []`) and emits EXACTLY ONE bare JSON verdict object (`{verdicts:[{comment_id, verdict, new_quoted_text, new_section_hint, confidence, reasoning}]}`), **outside** the delegation + output-json contracts — the documented carve-out, not drift; it prefers `orphaned` over a low-confidence relocate. **v4b (contract v2):** a backward-compatible superset adds optional `change_set` + per-comment block context inputs, a `narration` output, and a third `resolved` verdict (US13 Scenario 4); legacy verdicts-only call sites stay byte-valid and the model tier is unchanged (`sonnet`) | `cast-refine-requirements` lists it in `allowed_delegations` (intent-documenting) |
| FR-028 | Phase 4 enhances the render progressively: the document loads `<script src="/static/htmx.min.js">` + `<script src="/static/requirements_comments.js" defer>` and a `data-goal-slug` on `<body>`; a bare `file://` open (scripts 404, no slug) no-ops and the render stays a fully readable read-only document — no content depends on JS. On a served render (slug present) `requirements_comments.js` additionally injects a visible `.comment-affordance` control + a `.comment-affordance__hint` that *states* the select-to-comment gesture (US6, the comment-API door, the affordance criterion) into the `.rr-controls` bar — clicking it surfaces/scrolls to the comment tray and pulses the hint; select-to-comment remains the only comment-creation path (decision #7) and a bare `file://` render carries **no** affordance (it is JS-injected behind the slug guard, never in the static artifact) | The deliberate relaxation of the Phase 3a "no external script src" property (paired harness update, cast-ui-testing US2); the affordance is the additive discoverability surface over the locked select→pill→composer flow |
| FR-029 | The happy-path render is produced by the `cast-requirements-what` → `cast-requirements-how` maker pipeline driven by `render_job_service`, through the named stages `run_what → gate_what → run_how → gate_html → publish`; each agent is a tool-free `claude -p` subagent (`dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`, `allowed_delegations: []`, `model: opus`) run with `--tools ""` + clean child env (`env -u CLAUDECODE`, job-dir cwd) | Named-stage seam — Phase 4a inserts `run_checker → decide_quality` before `publish` without a rewrite |
| FR-030 | The deterministic `render_requirements()` / `rerender_requirements_html` path is the **fallback branch**, served **only** on a literal no-output maker failure (crash / timeout / empty / structurally-unextractable); this supersedes the synchronous-regen *primacy* of US2 (the source-hash cache envelope is reused unchanged across both branches) | Happy-path inversion — the deterministic substrate is no longer the primary producer |
| FR-031 | On a stale or missing render, `GET /goals/{slug}/render` starts the idempotent single-flight background job and immediately serves a live generating state (the prior stale render + a regenerating banner when one exists, else the dedicated `generating.html.j2` page) that polls the status endpoint and swaps in on `ready`; cached views, stubs, 404s, and the comment API never start or wait on a job | The maker never blocks a page view and never pops a terminal — the tmux HTTP-dispatch path is wrong for a page render |
| FR-032 | `GET /goals/{slug}/render/status` returns JSON `{state, source_hash}` with `state ∈ ready \| generating \| failed`; `ready` is the **pure artifact-hash derivation** (the served file's embedded `source-hash` equals the current source hash — covering maker, flagged, AND fallback publishes alike) and `failed` is returned only when nothing servable exists for the current hash AND its latest `render_jobs` row is terminal-`failed` | Readiness is never derived from the job table — the artifact's embedded hash is the single source of truth |
| FR-033 | The canonical `US-NN`/`FR-NNN`/`SC-NNN` ids are assigned upstream by the deterministic parser and the maker emits each **verbatim exactly once** as a small visible anchor label (never invented, never renamed); the WHAT-doc `sections[].block_refs` mapping is the non-DOM structure the Phase 4b diff agent reads, and the US7 DOM contract (zero `id=`, zero `data-block-anchor`, quote anchoring) is **explicitly preserved** | Logical id backbone is metadata-as-labels, not DOM anchors — the superseded stable-IDs design stays superseded |
| FR-034 | The maker contract REQUIRES each requirement unit's anchorable text (its source body with inline markdown stripped via the single `strip_inline_markdown`) to appear **verbatim and contiguous** within one semantic container in the served DOM; `maker_gate.check_html` enforces it through the shared `container_text_index(html)` walker | The Phase 1 carry-forward — guards against silent `<mark>`-placement loss on a paraphrased DOM; 4b-1 imports the same walker (no copy) |
| FR-035 | On structural-gate exhaustion the server publishes the **best attempt** via `publish_maker_html(..., served_by="structural_violation")` with a `flagged` `render_jobs` status, the joined gate violations in `error`, and a reader-visible "needs review" badge injected on the `/render` response from the `served-by` stamp — it does **NOT** fall to the deterministic page; the deterministic fallback fires **only** on literal no-output | The structural-violation OWNER OVERRIDE — "surface, don't suppress"; 4a's flag columns + score layer on top of this status + stamp |
| FR-036 | The `render_jobs` table (`id, goal_slug, source_hash, status, attempts, error, started_at, finished_at, heartbeat_at`; `status ∈ running \| published \| fallback \| superseded \| failed \| flagged`) is the observability / status / failure-reason surface; the per-job thread writes `heartbeat_at` at every stage boundary and the lazy reaper marks ceiling-exceeded jobs `failed`; readiness is **never** derived from this table | Every terminal job is a row with a reason (zero silent failures); 4a-2 adds its four human-review flag columns on top |
| FR-037 | The happy-path render is gated by **one** agent, `cast-requirements-render-checker` (`agents/cast-requirements-render-checker/`, `model: opus`, `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`, `allowed_delegations: []`), grading comprehension **and** visual quality in a single pass and emitting ONE bare-JSON verdict (contract `cast-requirements-render-checker/v1`: `can_state_what`, `restated_job`, `restated_outcome`, `restated_scope{in,out}`, `missing`, `issues[]` each with `dimension`+`criterion`+`severity`+`description`+`evidence`, `score`, `rework_feedback[]`) — a strict **superset** of the v2 `cast-requirements-checker` shape, **outside** the delegation + output-json contracts (the same subagent bare-JSON carve-out as the classifier / re-anchor agents). The binary PASS is computed **code-side** by `checker_verdict.derive_pass` (`can_state_what == true` AND no `missing[]` entry naming job/outcome/scope AND zero `severity:"error"` issues in either dimension; warnings never block); the ranking score is `checker_verdict.canonical_score` recomputed from issue counts (`1.0 − 0.15·errors − 0.05·warnings`, floored at 0); the agent-emitted `score` float is advisory only. The checker is tool-free (`--tools ""`) so it physically cannot read the canonical source or the WHAT doc; the runner inlines only the rendered artifact + family label. Every `error` issue MUST contribute ≥1 `rework_feedback` string. Gap amnesty: a `.rr-gap` marker is honest source-gap communication, not a comprehension defect — the checker must not fail a render for a surfaced gap | One checker, no coordinator; the gate is the boolean, never the float — extended to the visual dimension and to best-attempt ranking. `checker_verdict.py` is pure, beside `maker_gate.py` |
| FR-038 | `render_job_service` runs the **quality-driven rework loop** as the named stages `run_checker → decide_quality` inserted between `gate_html` and `publish`. Each iteration `run_how → gate_html → run_checker`; a clean attempt (structurally valid AND `derive_pass`) publishes immediately; otherwise the failing verdict drives the next rework with **provenance-tagged** feedback (deterministic structural violations under a "required" heading; the checker's `rework_feedback` under a "guidance" heading) and a one-line score history. Three consecutive verdicts naming the same gated WHAT token escalate to a forced `run_what` re-gen (bounded by `QUALITY_MAX_WHAT_REWORKS`; a re-gen that fails `gate_what` is discarded and the prior good WHAT retained, budget still decremented). The loop is bounded **only** by `QUALITY_MAX_ATTEMPTS` (the owner-sanctioned **anti-infinite-loop ceiling, NOT a cost cap**) and `QUALITY_STRUCTURAL_STOP` (consecutive structural failures → early terminal); cost / latency / model tier are **never** loop constraints (owner decision, binding). Attempt + verdict artifacts (`attempt-N.html`, `attempt-N.verdict.json`) are written under `RENDER_JOBS_DIR` (`build/render-jobs/{slug}/{hash12}/`), never under `goals/{slug}/`. The `QUALITY_*` knobs live in `config.py`, disjoint from the `RENDER_*` and `GAPFILL_*` keys; the checker stage is registered in the stage-timeout list so the reaper ceiling extends with zero formula edits | The single structural retry of Phase 3 (US14 Scenario 3) is **subsumed** by this loop — a structural failure is just another rework |
| FR-039 | The two-branch degradation policy is the **OWNER OVERRIDE** (supersedes the v4 US17 structural-violation RATIFIED fork): the deterministic `render_requirements()` page is served **ONLY** on a **literal no-output** failure (crash / timeout / nothing produced or extractable across all attempts) — and is **never** LLM-gated (running the checker over the no-LLM path would re-introduce an LLM dependency on the crash escape hatch). A **structurally-broken-but-present** attempt is **scoreable and servable**, flagged `human_review=1` + `review_reason='structural_violation'` (`served-by: structural_violation`) — **never** the deterministic page. At non-convergence `decide_quality` applies **PREFER VALID, THEN SCORE**: serve the best-scoring structurally-VALID attempt (`served-by: maker`, `review_reason='non_convergent'`; `'checker_unavailable'` when every valid attempt is unscored; `'structural_degradation'` on the `QUALITY_STRUCTURAL_STOP` early terminal); fall to the best-scoring BROKEN attempt **only** when no valid attempt exists (a broken attempt can never outrank a valid one on score alone). Tie → latest attempt | *Surface, don't suppress* — the visible-degraded state with machine-readable context over the silent-safe swap. The plan's "zero structurally-valid attempts → deterministic fallback" row is **deleted** by this override |
| FR-040 | The `render_jobs` migration adds **only** four nullable/defaulted human-review flag columns — `human_review INTEGER NOT NULL DEFAULT 0`, `review_reason TEXT` (`non_convergent \| checker_unavailable \| structural_degradation \| structural_violation`), `published_attempt INTEGER`, `published_score REAL` (`heartbeat_at` already ships in Phase 3's CREATE TABLE; the `status` enum is unchanged — `published` covers flagged publishes). These columns are the **queryable observability copy** (Phase-5 sweep input, post-mortem), **not** the readiness path. The status JSON (`GET …/render/status`) exposes `human_review` **read from the served-artifact envelope stamp** (the single source of truth for the poll), never from a possibly-newer running row | Additive migration only (`db/schema.sql` + `tests/test_schema_migration.py`); the flagged-renders LIST that consumes these columns is **Phase 5d**, not built here |
| FR-041 | `check_comment_survival(html, parsed, comments) -> SurvivalReport` (pure, co-located in `maker_gate.py`, `comments` a plain sequence of `{id, quoted_text}`) walks the candidate HTML **once** via the shared `container_text_index` walker and precomputes each block's `strip_inline_markdown(body)` once per pass; it classifies each open comment **in-block** (quote ⊂ a block's anchorable text — MUST place in that block's container, a miss is a witnessed violation that flips `passed=False` and lands in `violations` + `unplaced`) vs **cross-boundary** (best-effort whole-document find, recorded in `unplaced` on a miss but **never** a violation, never flips `passed`); `SurvivalReport` is the frozen `{passed, violations, unplaced, placed}` shape | The Phase-1 silent-`<mark>`-loss guard turned into a publish-time gate; single-walk discipline (no copy of the walker, no second stripper) |
| FR-042 | `gate_html` fetches the open comments at stage entry — **re-read on every entry** (Decision #9; the 4a loop re-enters `gate_html` many times) — runs `check_comment_survival`, writes `survival.json` under `build/render-jobs/{slug}/{hash12}/`, and merges **only the in-block** survival `violations` into the **same** `state.html_report.violations` structural channel (frozen report ⇒ rebuilt, never mutated); under the **DECISION #10 OVERRIDE** a survival-failing in-block attempt is a **flagged, servable** structural state (served best-attempt + `structural_violation`), it does **not** add a blocking branch and does **not** trigger the deterministic fallback (literal no-output only) | The C3 merge seam — 4b widens the report `gate_html` produces; 4a's `run_checker → decide_quality` wraps "whatever `gate_html` reports" and absorbs it by construction |
| FR-043 | The `.comment-unplaced` tray badge is a **read-time, derived** marker: `requirements_comments.js` toggles it (and an injected `.comment-unplaced-badge`) on an open, non-displaced tray item whose `highlight()` returned `false`, covering **both** in-block and cross-boundary placement misses uniformly; nothing about the miss is stored, the save path is untouched, and the next render recomputes it | "Surface, don't suppress" at read time — the JS `highlight()→false` path already treats both miss classes the same |
| FR-044 | `cast-comment-reanchor` **contract v2** is a backward-compatible **superset**: inputs add optional `change_set` (a `summarize()` dict) and per-comment `block_ref`/`block_disposition`; output adds a top-level `narration` (`{overview, item_notes:[{change, heading_or_ref, note}]}`, emitted only when `change_set` is provided) and a third verdict value `resolved` (only on a demonstrable fix; bias `relocated > resolved > orphaned`-when-unsure — a wrong `resolved` is recoverable, a wrong relocate is not); `new_quoted_text` stays a verbatim substring of `new_content` and SHOULD avoid inline-markdown markers (anchor-pickability). The **trust boundary** is hard: `narration` describes ONLY `change_set.items` entries — never merged, added, or reworded keys. A legacy `{comments, old_content, new_content}` call is byte-identical to v1. **v3 (v8):** inputs add OPTIONAL render-space context (a comment's prior-render container text by `block_ref` + the candidate new-render container text); every new input optional → every v1/v2 call site stays byte-valid; the verdict vocabulary, safety machinery, and `sonnet` tier are untouched (US13 Scenario 5). In UPDATE mode the dispatch is the ONE publish-boundary call over the expected-miss set (the publish-boundary reanchor below) | The US3-S2 "re-anchor **or** resolve" half; the safety machinery (orphan-over-guess, 422 verbatim backstop) carries untouched; v3 adds render-space context as an additive superset |
| FR-045 | `version_diff_narrations` (`id, goal_slug, base_version, head_version, overview, item_notes JSON, created_by, created_at, UNIQUE(goal_slug, base_version, head_version)`) stores the diff narration; `requirement_version_service.save_narration`/`get_narration` are flat house-DB functions with injectable `db_path`. `POST …/versions/{head}/narration` (body `{base, overview, item_notes, created_by}`, JSON only) validates the slug via `goal_service.get_goal` (404), **recomputes** `summarize(diff_blocks(old, new))` server-side, and validates **every** `item_note` key to a deterministic item — ANY mismatch → **422 all-or-nothing** listing the offending keys (no silent note-dropping), unknown version/slug → 404; a re-post UPSERTS (a retried loop cycle replaces, never duplicates); size caps mirror the comment-content validation caps (`overview` ≤ 2 KB, each note ≤ 2 KB, ≤ 1 note per item); `created_by` (the dispatching parent's actor id) rides the body same-door | The narration is posted same-door by the parent that cut the version; the server never dispatches an LLM on the version path |
| FR-046 | `GET …/changes` gains a sibling `narration: {...} \| null` key while `counts`/`items` stay **byte-for-byte** `summarize()` (the byte-stable diff guarantee re-scoped to those keys); the `changes_panel.html` panel attaches each stored note to its deterministic item by `(change, heading_or_ref)` lookup and renders the LLM-authored text through the **autoescaped** Jinja template (never `innerHTML` / `\| safe`); a version cut with no narration shows the deterministic panel (the floor) | LLM text into HTML = escaped fragments rendered by attachment only — the UI structurally cannot show a change absent from `summarize()` |
| FR-047 | The WHAT doc's `gaps[]` field is **activated** (Phase 3's reserved seam): each entry is `{gap_id, section_title, block_refs[], question, why_it_matters}` with **no** proposed answer — the WHAT layer names what is missing, never supplies it. `maker_gate.check_what_doc` enforces: `gap_id`s unique + sequential, every `block_refs` member a real `Block.ref`, `question` non-empty, the doc NEVER contains an answer, and the count ≤ `GAPFILL_MAX_GAPS` (`config.py`, default 5, `CAST_GAPFILL_MAX_GAPS` override). The detection bar is US7's "would materially help the reader" (verbatim in the prompt) — a page is communication, not an audit; trivia-hunting is instructed against | The gate rejects `GAP-NN` as a canonical ref token; `gaps[]` empty ⇒ exactly Phase-3/4a behaviour |
| FR-048 | The HOW agent MAY emit an optional `<!-- GAPS-DETECTED … -->` trailer **AFTER** `<!-- END RENDER -->` (OUTSIDE the `BEGIN RENDER`→`END RENDER` window, so the strict first-`BEGIN`→first-`END` extraction and the no-output classification are byte-untouched); the trailer carries `section_title`/`question`/`why_it_matters` with **no** ids (the WHAT re-run assigns them). This is the "HOW asks WHAT" channel of the gap-fill story (US21) — the HOW layer asks rather than improvises | Sentinel extraction unchanged — never move the trailer inside the window |
| FR-049 | `cast-requirements-gapfill` (`agents/cast-requirements-gapfill/`, `model: opus` + `[USER-DEFERRED]` tier knob, `dispatch_mode: subagent`, `interactive: false`, `allowed_delegations: []`, `timeout_minutes: 15`, `--tools ""`) is a **net-new, tool-free, pure text-to-text** subagent (the `cast-requirements-what`/`-how` carve-out, **outside** the delegation + output-json contracts). It emits one YAML doc per gap between sentinels: `{gap_id, supplied: true, answer, evidence:{file, quote}, proposed_change:{kind: addition, section_hint, proposed_body}}` OR `{gap_id, supplied: false, reason}`. Hard prompt rule: supply **only** what the corpus literally supports, with a verbatim evidence quote; **when in doubt, REFUSE**. `kind` is gate-pinned to `addition` (a gap is MISSING content, never a rewrite); the SERVICE owns all I/O, corpus resolution, and evidence validation | The agent cannot read beyond what the runner inlines, cannot write anything — "never fabricates" is enforced server-side by `validate_evidence` (next), not promised by the agent |
| FR-050 | The grounding corpus is an **explicit allowlist** of the goal's OWN upstream artifacts only — `requirements.human.md`, `research_notes.human.md`, an `exploration/` summary if present — resolved by the runner inside the goal's own artifact tree (path-validated, the existing traversal rule) and inlined; the **wider repo is NEVER a requirements source**. "Upstream cannot supply" (US7 Scenario 2) means *these files don't contain it* — the honest answer the marker reports | The allowlist is the trust boundary on what "upstream" means |
| FR-051 | `render_job_service.validate_evidence` (deterministic, service-side) is the trust boundary: for each `supplied` gap it asserts `evidence.file` ∈ the corpus allowlist **and** `evidence.quote` **verbatim-locates** in that file via the **shared** `verbatim_locate` helper (whitespace/smart-quote tolerant; NOT a raw `str.find()` — the one locate, reused, never a second copy). A failure **demotes** the answer to `cannot-supply` and records `evidence-validation-failed` on the job row (zero silent failures); an ungrounded answer can **never** reach the CR door | The single-helper discipline — `validate_evidence` reuses `change_request_service.verbatim_locate` |
| FR-052 | The gap pipeline stages run **once per job, BEFORE** the 4a quality loop, in order: probe `run_how` (harvest the trailer — does **NOT** debit `QUALITY_MAX_ATTEMPTS`, C6) → `ask_what` (the bounded HOW-asks-WHAT re-run, its own `GAPFILL_ASK_ROUNDS` counter, default 1 — does **NOT** debit `QUALITY_MAX_WHAT_REWORKS`, A2) → `run_gapfill` → `validate_evidence` → `emit_change_requests`. All five stages are registered in `RENDER_STAGE_TIMEOUTS`, so the reaper ceiling + the stage-boundary heartbeats extend with **zero** formula edits; the gap set is a property of the source, not the attempt (US21's "before finalizing") | The stage seam (3c/4a) is honored — gap stages insert between `gate_what` and the FINAL `run_how`; the quality loop stays between `gate_html` and `publish` |
| FR-053 | `emit_change_requests` reconciles each validated gap through the v2 gate: gap CRs are `kind="addition"`, `target_quote=None`, `author="cast-requirements-gapfill"`, `author_type="agent"` (hard-coded at the emitter, no spoof surface), `origin_phase="render-gapfill"`, `origin_artifact_path="{what_doc_job_path}#gap=<fp12>"`, status from `gate_status(kind, target_quote, policy)` — under the goal's **GATE-ALL** policy (`config.py` default `WRITEBACK_GATE_POLICY="gate-all"`, `CAST_WRITEBACK_GATE_POLICY` override preserved) always `"proposed"`. A structural dedupe fingerprint `fp12 = sha256(sorted(block_refs)+" "+section_title)[:12]` (question folded through the named `_normalize_gap_question`) is matched substring-after-`goal_slug`-filter; an existing `proposed`/`applied`/`conflicted`/`rejected` row skips re-proposal (a `rejected` match → `unfilled-declined`). The service writes the closed-vocabulary `gaps-state.json` (`status ∈ cr-proposed \| cr-applied \| unfilled-cannot-supply \| unfilled-declined \| unfilled-ask-failed`) beside the agents' docs and renders the `.rr-gap` marker (question + the 1:1 fixed status string, **never** the `proposed_body`) — `change_request_service` (intake/gate/apply/outbox/relay) is consumed **byte-unchanged** | The reconcile-through-the-gate invariant (US21 Scenario 2) is **structural** — the answer's only destination is a CR through the same-door v2 intake; the v2 cache/version machinery does the un-mark, there is no un-mark path to get wrong |
| FR-054 | A **read-only flagged-renders list** (slug, `review_reason`, `published_score`, render link) is surfaced on an existing screen (`/runs`) from `render_job_service.list_flagged_renders()` — a query of the 4a recording-only `render_jobs` flag columns (`human_review=1`) with **no** new write path and **no** new column. It is the honest degraded-page signal the structural override makes load-bearing ("surface, don't suppress"); additive scope only — **no** queue/triage UI | Resolves the human-review-flag row's "the LIST is Phase 5d" pointer; the migration is unchanged (`git diff` shows no `render_jobs` schema change) |
| FR-055 | The render job decides CREATE vs UPDATE via the pure `render_job_service.decide_mode(...)`. UPDATE iff ALL hold: a prior render exists AND was a CLEAN maker publish (`served-by: maker`, no human-review — never UPDATE *from* a flagged/fallback render); the prior source is recoverable (prior job dir, else a `requirement_versions` content-hash match); the goal's `workflow_family` is unchanged; `changed_fraction <= RENDER_UPDATE_MAX_CHANGED_FRACTION` (config default 0.4); and `prior_render_bytes <= RENDER_UPDATE_MAX_PRIOR_BYTES` (config default 600 000, plan-review Decision #6). EVERY precondition failure degrades to CREATE with a job `_note` — **never a job error** (CREATE is always safe). `changed_fraction = (added+removed+modified)/max(old_blocks,new_blocks)` from the consumed `block_diff.diff_blocks` engine (the deterministic-diff extend-never-fork rule — consumed unchanged, not edited). The decided `mode` is stamped on the `render_jobs` row for observability | Every UPDATE precondition failure degrades to CREATE, noted, never errored — shared-context Owner Principle |
| FR-056 | UPDATE is the **deterministic splice** (Spike 1a verdict FAIL → splice, NOT gate-enforced LLM copy): the server keeps each unchanged unit container's bytes verbatim from the prior render and splices in HOW-rendered changed-block fragments via the `RR-FRAGMENT` sub-contract (HOW emits **only** changed blocks, never a full page). Byte-identity of unchanged containers is a **construction guarantee**. `check_update_fidelity(html, prior_html, unchanged_refs)` compares **NORMALIZED container TEXT** via the shared `container_text_index` walker (NOT raw bytes — a raw-byte gate on LLM output thrashes on serialization noise); a changed ref HOW emitted no fragment for is a structural violation taking the standard retry. UPDATE **reuses the prior gated WHAT doc** (no `run_what`); a WHAT-reuse miss degrades the whole job to CREATE. The published UPDATE artifact is therefore **server-assembled** (splice), not a single LLM emission | The splice-assembles-the-published-artifact architecture note; one walker, no copy |
| FR-057 | Comment anchoring lives in the **published-render snapshot** space. `requirement_comments` gains two additive columns: `block_ref TEXT NULL` (server-resolved canonical id of the enclosing labeled unit container; NULL = cross-boundary OR a ref-less render — both honest) and `anchor_space TEXT NOT NULL DEFAULT 'source'` (`'source' \| 'render'`). `block_ref` is resolved SERVER-SIDE from the served artifact by `comment_anchor.resolve_render_anchor` (the productionized 1b dry-run, reusing the single `container_text_index` walker) and is **NEVER accepted from the client** (a spoofed ref would mis-route a future change-request) — it stays out of the POST body schema. A ref-less-render NULL `block_ref` is a **placed-comment SUCCESS**, never an unplaced miss to retry/badge (plan-review Decision #1). `create_comment` / `list_comments` / `relocate` re-target to render space; `list_comments` picks the comparison space per `anchor_space`. Old rows keep the back-compatible `'source'` default (additive migration: `db/schema.sql` + `tests/test_schema_migration.py`). **v10:** the served-render resolver is now **artifact-keyed** — `_resolve_served_render_html` / `_resolve_render_compare_text` / `create_comment` / `relocate` take an optional `artifact_ref` and `list_comments` resolves the render compare-text **per `artifact_ref`** (cached keyed by it), so a goal's comments minted against different served `.html` documents never cross-anchor; absent `artifact_ref` resolves the requirements default (the same-door field + resolver are specified in the v10 rows below) | The crux move — comments anchor to the render, bridged back to source by a server-resolved ref; v10 keys that resolution to the specific artifact |
| FR-058 | UPDATE **SKIPS `emit_change_requests` entirely** and REUSES the prior `gaps-state.json` (plan-review Decision #2 — LOAD-BEARING, not an optimization): the gap-CR dedupe fingerprint rides `origin_artifact_path` keyed by the CURRENT `source_hash[:12]`; an UPDATE runs under a NEW hash, so re-emitting would write a DUPLICATE gap CR the dedupe pre-check cannot match. Any diff that would change the gap set has already flipped the job to CREATE (WHAT reuse fell back). The prior render's `.rr-gap` markers ride along in the unchanged containers the splice preserves | Gap-CR idempotency under UPDATE — guards the source-hash-keyed dedupe duplication risk (the gap-idempotency criterion below) |
| FR-059 | For an UPDATE's **expected-miss** comments (those on modified/removed blocks), the pipeline runs ONE `cast-comment-reanchor` v3 dispatch at the **publish boundary** (`_post_publish_reanchor`, after `_finalize` so it never affects the terminal row): a `relocated` verdict re-points the comment to a verbatim span of the new render, `resolved` resolves it, anything else (incl. crash / garbage / non-verbatim quote) leaves the comment **open + badged** — never silently dropped, never auto-resolved. An expected miss never flips survival `passed`; a comment on an unchanged block survives **structurally** (no dispatch) | US19-reoriented; surface, don't suppress |
| FR-060 | `maker_gate.check_html` gains an **empty-shell** check: a render whose body carries section scaffolding but no actual requirement content (an empty shell) is a structural violation, so a degenerate maker emission cannot publish as a clean page — the CREATE-mode floor that replaces the superseded blanket verbatim-carriage requirement (it pairs with US16 Scenario 2's CREATE supersession). The `cast-requirements-what` zero-ref contract (empty `block_refs` for a genuinely ref-less source) and the HOW zero-ref + empty-shell hardening pair with it | Hardens the `pilot_poc`/`random_idea` ref-less path against degenerate output |
| FR-061 | Two config knobs follow the `RENDER_*` env-overridable convention: `RENDER_UPDATE_MAX_CHANGED_FRACTION` (default 0.4, `CAST_RENDER_UPDATE_MAX_CHANGED_FRACTION`) and `RENDER_UPDATE_MAX_PRIOR_BYTES` (default 600 000, `CAST_RENDER_UPDATE_MAX_PRIOR_BYTES`). The legacy `RENDER_UPDATE_ENABLED` flag is **retired as a behaviour gate** (sp3b wired UPDATE live: an UPDATE fires whenever `decide_mode` lands `mode='update'`, `_is_update_active(state)`); it survives only as a harmless legacy constant | `RENDER_*`/`QUALITY_*` knob convention; the flag-gate is gone |
| FR-062 | The phase-tab artifact viewer is **dual md/html**: the per-directory and single-file artifact collection in `get_phase_tab` admits both `.md` and `.html`, every artifact dict carries a `kind ∈ {markdown, html}` discriminator, and the render macro dispatches on it — `markdown` → today's `markdown-body` div (the `kind="markdown"` default keeps every existing call site byte-identical), `html` → an `<iframe srcdoc>` carrying the file's **verbatim bytes** (never `md.markdown()`-processed) in a **null-origin** sandbox (`allow-scripts allow-popups`, **no** `allow-same-origin`). The `.html` collector (`_add_html_file`) sets `authorship=None` (render-class). `.html` is collected **after** `.md` per directory (md source first, render below) — the deterministic ordering Phase 4 relies on | Naming contract — Phase 3b/4 adopt `kind`, `_add_html_file`, the iframe sandbox verbatim; `allow-scripts` is mandatory so the Phase 3b comment bridge can run; `allow-same-origin` is **forbidden** (it would defeat the null-origin isolation) |
| FR-063 | The artifact **read** gate (`validate_artifact_path_read`) admits `.html` (a render-class artifact, US4 — read-only, no authorship suffix), while the **edit** gate (`validate_artifact_path`) stays `.md`-only; the existing `_validate_artifact_path_base` traversal guard (`resolve` + `is_relative_to` GOALS_DIR / `external_project_dir`) applies to `.html` unchanged (no new path surface). The refined-requirements HTML is added to the requirements phase's artifact set so it surfaces in-viewer as render **consumer #2** — a **lazy** surface that appears once a render has written the file, gracefully empty when absent — **without** removing the `/render` route; **exploration** is render **consumer #1** (Phase 4 produces `exploration/exploration.html`). US7 (zero `id=`/`data-block-anchor`, quote anchoring) is preserved on the embedded render so Phase 3b's verbatim-substring anchoring + the `anchor_space='render'` path keep working — **REUSED, not superseded** | US4/US7 (and the render-class read-only + zero-`id`/`data-block-anchor` DOM clauses they carry) are cited and unchanged; in-iframe commenting (Phase 3b) + the exploration render pipeline (Phase 4) are **out of scope** for this version |
| FR-064 | The same-door create endpoint gains **one** optional, defaulted `artifact_ref` field on `CreateCommentRequest` (the goal-relative served-`.html` the quote was minted against; `None` = `refined_requirements.html`, the requirements contract verbatim). It is **server-validated** as goal-relative (no `..` segment, not absolute) and `.html`-only — the same goal-relative / no-traversal / `.html` contract the read gate enforces; a malformed value is a `422` and persists nothing. It is passed into `comment_service.create_comment(..., artifact_ref=...)`; `block_ref`/`anchor_space` stay server-resolved (never client-trusted). **No new endpoint, no parallel route** — same-door (US8) is one new field on the one canonical handler | One optional field on the one door (US8 honored); the client-supplied edge is validated server-side, the anchor stays server-resolved |
| FR-065 | The served-render resolver is **artifact-keyed** (`comment_service._resolve_artifact_path`): `artifact_ref=None` → `refined_requirements.html` (back-compatible default); a value resolves a **validated, contained** goal-relative `.html` under the goal dir (`resolve()` + `is_relative_to` — a traversal/`.html` violation is a hard `ValueError`, never an off-tree read); a missing file degrades to `""` (the read-time detector never crashes, as today). `artifact_ref` is stored on the comment row (third additive nullable `requirement_comments` column; NULL = requirements) so displacement/relocate later resolve against the **same** artifact the quote was minted from. The default path (`artifact_ref` NULL) is **byte-identical** to v9 — regression-asserted | The load-bearing seam — without it, comments on `exploration.html` would silently anchor against the requirements render; default-None keeps requirements unchanged |
| FR-066 | The **host postMessage bridge** (`static/comment-bridge.js`) is the boundary crossing: the bridge-mode comment layer (the SAME cast-comment-html assets, injected before `</body>` of every served `.html` by `comment_layer_inject.inject_comment_layer`) `postMessage`s a `{type:"cch:submit", goal_slug, artifact_ref, comments[]}` batch to the host. The host validates the message on **SOURCE IDENTITY** — `event.source` must be a `contentWindow` in its `artifact_ref → contentWindow` registry (origin is `"null"` for srcdoc and is **never** checked); a foreign window or a payload failing the shape-check issues **no** POST. For each comment it issues ONE same-door create POST (`author_kind:"human"`, the artifact's `artifact_ref`); a per-comment failure does **not** abort the batch. It replies `{type:"cch:submitted", ok, results[]}` to the **originating** frame only (`targetOrigin "*"`), so the in-iframe layer toasts per-comment success/failure (surface, don't suppress). Multiple commentable iframes per tab are routed independently by source identity | Source-identity (not origin) is the only correct guard for null-origin srcdoc (1b browser-confirmed); reply-to-originator-only + per-comment fan-out keep the server contract single |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | An unfamiliar reader (the checker agent, as the agent-as-consumer demonstration) can restate a goal's job, primary outcome, and in/out scope from the Goal Card + headings | **Deterministic substrate:** `cast-requirements-checker` PASS via `tests/eval_render_checker.py` (`eval_`-prefixed, **unmodified**). **v5 — happy path:** the maker render's cold-reader criterion is now satisfied by `cast-requirements-render-checker` — the in-loop quality gate, a strict superset folding in the v2 cold-reader shape — verified by `tests/eval_quality_gate.py` |
| SC-002 | The deterministic **fallback substrate** is byte-stable: identical source ⇒ identical `.html` from `render_requirements()`, and the source-hash cache envelope returns the file unchanged with no write; the structural DOM contract (no ids/anchors, contiguous selectable units) holds for both the fallback and the maker render | Golden-HTML snapshot tests (fallback) run in default pytest CI. **v4:** the byte-stable guarantee is scoped to the deterministic fallback + cache envelope; the happy-path maker render is checked by `maker_gate` + the eval harness (not goldens), and the LLM-judged quality layer that replaces the structural happy-path gate is Phase 4a scope, not specified here |
| SC-003 | A render never mutates the canonical `.collab.md` and `bin/cast-spec-checker` stays green on the frozen fixture after a render | `cast-server/tests/test_fr007_readonly_guard.py` |
| SC-004 | The generated `.html` is unambiguously a render: AUTO-GENERATED header + `source-hash` present, no authorship suffix | Snapshot + service tests assert the header and `source-hash` line |
| SC-005 | Human and agent reach the comment store through one door: the negotiated `POST …/comments` produces the same row (modulo id/`author_kind`) for a JSON call and an HX call | `tests/test_requirements_comments_api.py` dual-assertion parity test |
| SC-006 | Versioning is transactional and carry-forward is by-omission: `create_next` snapshots + archives in one transaction, open comments keep their `version`, convergence flips on open-comment count, and `displaced_comment_ids` equals the verbatim string-find | `tests/test_requirement_versions.py` + `tests/test_archive_retrieval.py` |
| SC-007 | The block diff is deterministic and total: the partition invariant holds and `GET …/changes` JSON equals `summarize()` byte-for-byte | `tests/test_block_diff.py` (partition invariant) + `tests/test_diff_render.py` (`changes_json_matches_summarize`) |
| SC-008 | No Phase 4 operation mutates the canonical `.collab.md`, no second requirements file is ever created, and the diff view is never persisted; the canonical render stays zero-`id` even with the version toggle | `tests/test_fr007_readonly_guard.py` (Phase 4 sweep) + `test_archive_retrieval.py` folder-invariant assertion + `test_diff_render.py` not-written-to-disk + zero-`id`-with-toggle |
| SC-009 | The render-page comment flows are e2e-covered (affordance present + click reveals tray, select→pill→composer→`<mark>`, resolve, version toggle→diff, displaced→tray) targeting the named selectors (`.comment-affordance`, `.comment-pill`, `.comment-composer`, `mark.comment-mark`, `.comment-tray`, `.version-toggle`, **v4b:** `.comment-unplaced`, `.diff-narration`) | `cast-server/tests/ui/` requirements-render screen (runs in a browser-capable CI per cast-ui-testing US2) |
| SC-010 | Two real work-families render **visibly distinct**, family-appropriate pages through the maker pipeline: their section-heading sets differ and contain no `US`/`FR`/`SC` slot names, every canonical unit is mapped to its logical id (none invented), and each is a single self-contained file | The eval-harness two-family e2e sweep + `maker_gate.check_html` green on both (`eval_`-prefixed harness, excluded from default pytest); the side-by-side human eyeball is a non-blocking carry-forward |
| SC-011 | The maker never writes the canonical `.collab.md` — guaranteed **structurally** by `--tools ""` and verified by the read-only-guard maker sweep | `cast-server/tests/test_fr007_readonly_guard.py` (maker sweep) |
| SC-012 | The generating state converges: a changed source serves the generating state immediately and the finished render swaps in on `ready` without blocking the view | `cast-server/tests/test_render_route_and_service.py` (fake-runner route tests) + the status-poll hash derivation + a manual e2e pass |
| SC-013 | The two-branch degradation is surfaced, never silent: literal no-output serves the deterministic `fallback` page; structural-gate exhaustion serves the `flagged` best attempt with the `served-by: structural_violation` stamp + "needs review" badge — never the deterministic page | `cast-server/tests/test_render_job_service.py` (publish branch tests) + `cast-server/tests/test_render_route_and_service.py` (badge injection) |
| SC-014 | The LLM checker and the deterministic `maker_gate` measure **different** things: the committed `low_quality_attempt.html` PASSES `check_html` yet FAILS `checker_verdict.derive_pass`, and a `.rr-gap` page is **not** failed for a "missing outcome" (gap amnesty). Below the bar the first lever is the checker prompt, never the code-side gate (the eval-and-production share one gate by import) | `cast-server/tests/eval_quality_gate.py` (replay + `--live`, `eval_`-prefixed) pinned in CI by `cast-server/tests/test_eval_quality_gate.py`; the side-by-side `--live` discrimination + browser eyeball is a non-blocking human carry-forward |
| SC-015 | The terminal policy is the OWNER OVERRIDE, exhaustively: literal no-output → deterministic `fallback` (checker never invoked); ≥1 structurally-valid attempt → best valid served `human_review=1` (`non_convergent`/`checker_unavailable`/`structural_degradation`); zero valid but attempts exist → best broken served `structural_violation`; PREFER VALID beats a higher-scoring broken attempt; the deterministic page is **never** served when any attempt exists | `cast-server/tests/test_quality_loop.py` (every terminal branch via the injected fake runner, scratch goal + throwaway `db_path`) |
| SC-016 | The human-review flag is **recording-only** in 4a: the four `render_jobs` columns + the served-artifact envelope stamp + the status-JSON `human_review` (read from the envelope, surviving a fresh `running` regen row) are present. **v7 (Phase 5d):** the minimal **flagged-renders list** that consumes these columns now exists (read-only, on `/runs`; see the flagged-renders-list requirement + criterion below) — the migration still adds only the four nullable/defaulted columns with no row rewrite, and no `render_jobs` schema change ships with the list | `cast-server/tests/test_schema_migration.py` (additive columns) + `cast-server/tests/test_quality_loop.py::test_served_artifact_flag_survives_a_fresh_running_regen_row` |
| SC-017 | A maker regenerate leaves every open comment anchored with **zero new orphans** (the survival guarantee): a same-source regenerate makes **zero** DB changes of any kind (no new version, no displacement, no orphan — comment rows byte-identical before/after) and the survival gate is green with every in-block mark placing on the new DOM; a source-edit loop re-anchors a reworded+moved commented block (`relocated`, the 422 backstop not triggered), orphans only the genuinely-deleted block's comment (surfaced in the tray), never displaces the untouched comment, and republishes survival-green — an in-block placement miss surfaces (flagged + `.comment-unplaced` badge), a cross-boundary miss is badge-only, **never** silent | `cast-server/tests/eval_sc003_survival.py` (the `eval_`-prefixed real-pipeline sweep — same-source + source-edit blocks) + `cast-server/tests/test_comment_survival.py` (per-class gate units); the browser eyeball of the badge is a non-blocking carry-forward |
| SC-018 | The narration trust boundary holds: a posted narration is accepted **only** when every `item_note` keys to a server-recomputed `summarize()` item (any mismatch → `422` all-or-nothing), and the rendered "What changed" panel shows **no** change entry beyond `summarize()`'s items; `GET …/changes` keeps `counts`/`items` byte-for-byte with `narration` as a sibling, and the LLM text flows through the autoescaped template only | `cast-server/tests/eval_sc003_survival.py` (trust-boundary block: server-accepted == recomputed set) + `cast-server/tests/test_schema_migration.py` (`version_diff_narrations` coverage) + the narration-API tests |
| SC-019 | Gap-fill asks upstream, never fabricates (the goal's US7 ask-upstream / reconcile-through-the-gate stories realized): a gap-injection run either proposes the detail **only** as a `kind="addition"` CR through the unchanged v2 gate (canonical byte-identical until human approval; the page marks `.rr-gap` until regeneration from approved canonical) or marks the gap with a question + fixed status string; `validate_evidence` demotes any answer whose evidence quote does not verbatim-locate in the corpus allowlist (`evidence-validation-failed`); the page NEVER renders a `proposed_body`; a full gap-fill run leaves canonical byte-identical | `cast-server/tests/test_gap_reconciliation.py` (emit → dedupe → both convergence lanes incl. the gated reconcile lane + the gap-injection arm) + `cast-server/tests/test_fr007_readonly_guard.py` (full-gap-fill byte-identical extension); the live deleted-detail e2e is a non-blocking carry-forward |
| SC-020 | The nine LOCKED `WorkFamily` corpus docs render visibly-distinct, family-appropriate pages through the shipped pipeline (gap machinery live): each reaches terminal `published` (never the deterministic `fallback`, never `failed`/`superseded`), the section-heading sets are pairwise distinct with no `US`/`FR`/`SC` slot names, and the per-family `human_review` flag + checker score is the recorded quality signal — a flagged best-attempt is the **correct shipped degraded state** (surfaced via the flagged-renders list), not a sweep failure | `cast-server/tests/eval_family_sweep.py` (`eval_`-prefixed nine-family real-pipeline sweep) + `signoff/golden/` evidence; the side-by-side human eyeball is a non-blocking carry-forward |
| SC-021 | The minimal **flagged-renders list** exists (resolving the human-review-flag criterion's Phase-5d pointer): a read-only list (slug, reason, score, link) on `/runs` sourced from `render_job_service.list_flagged_renders()` over the `human_review=1` rows — no new write path, no new column, no queue/triage UI; it renders only when ≥1 render is flagged | `cast-server/tests/test_render_job_service.py::test_list_flagged_renders_returns_only_flagged_rows` + `::test_list_flagged_renders_empty_when_no_flags`; the rendered `/runs` section is a non-blocking browser carry-forward |
| SC-022 | The two-mode decision is correct + degrade-safe: `decide_mode` returns UPDATE only when every precondition holds and degrades to CREATE (with a note, never an error) on each individual failure (no/flagged/unrecoverable prior, family flip, massive `changed_fraction`, oversize prior); an UPDATE publishes `served_by=maker` keeping unchanged unit containers byte-identical and swapping only changed blocks; a ref-less / massive / family-changed / flagged-prior edit re-renders fresh in CREATE. **v8 (the validation target): the three previously-flagged families (`bug_fix`, `pilot_poc`, `random_idea`) re-render CLEAN (`served_by=maker`, `human_review=0`) and the nine-family aggregate is 9/9 published, 0 flagged — readability-first CREATE did not regress the six previously-clean families** | `tests/test_render_mode_decision.py` + `tests/test_render_job_service.py` (live UPDATE splice + degrade tests) + `tests/test_maker_gate_update_fidelity.py`; **the nine-family clean record: `tests/eval_family_sweep.py --golden` (9/9 clean) + `signoff/golden/` + `signoff/sp5-proof.md`** (supersedes the prior 6/9-clean nine-family record) |
| SC-023 | Comments anchor to the render snapshot with a server-resolved bridge: `create_comment` stores `anchor_space='render'` + a server-resolved `block_ref` (never client-supplied — no `block_ref` POST param); a ref-less render yields `block_ref=NULL` treated as SUCCESS; displacement + survival are computed in render space; a comment on an unchanged UPDATE block survives structurally, one on a modified block routes to the publish-boundary reanchor (relocate/resolve/orphan), never dropped, never auto-resolved | `tests/test_comment_service.py` + `tests/test_comment_anchor_render.py` + `tests/eval_sc003_survival.py` (render-anchor + UPDATE survival regressions a–f) |
| SC-024 | Gap CRs are idempotent under UPDATE: an UPDATE-mode re-render of a doc carrying an open gap emits **ZERO** new gap change-requests (reuse prior `gaps-state.json`, skip `emit_change_requests`) — the source-hash-keyed dedupe duplication risk is pinned by a regression so a future refactor cannot silently reintroduce it | `tests/eval_sc003_survival.py` (regression f) + `tests/test_gap_reconciliation.py` |
| SC-025 | The dual md/html viewer renders both classes without regressing the md path: a phase tab with a `.md` **and** a `.html` artifact shows the md in a `markdown-body` div and the html inside an `<iframe srcdoc>` whose decoded value equals the file bytes **byte-exact**, the html artifact has **no** edit button (render-class), the iframe sandbox **omits** `allow-same-origin`, and a `.md`-only tab emits **no** iframe; the read gate admits `.html` while the edit gate rejects it. An **adversarial** render-class doc (containing `</script>`, quotes/backtick, `&`, and a render-marker) round-trips byte-exact through `srcdoc` and parses to **exactly one** `<script>` (plan-review Decision #6) | `cast-server/tests/test_dual_viewer.py` (read/edit gate, dual-artifact render, sandbox-omits-same-origin, md-only regression, `kind="markdown"` default byte-identity, adversarial srcdoc round-trip + single-script); the in-viewer requirements eyeball is the 1b browser-validated carry-forward (`spike-1b-result.md`). **v10 note:** the **macro** still escapes whatever bytes it is handed byte-exact (the adversarial + default-param tests are unchanged); the **served** `.html` now additionally carries the injected bridge-mode comment layer appended before its own `</body>` (the host-bridge row below) — so the route-level srcdoc preserves the artifact's markup verbatim but is no longer byte-identical to the on-disk file |
| SC-026 | Diecast-wide commenting + the host bridge are proven **without a browser** (autonomous CI can't drive Chrome; 1b did the live validation): (a) a jsdom host-bridge unit test asserts foreign-window rejection, payload shape-check, per-comment POST fan-out with the exact same-door body incl. `artifact_ref`, the `cch:submit`→`cch:submitted` round-trip to the originating frame only, and multi-iframe source-identity routing; (b) a server-contract test asserts the proxied POST body creates a render-space comment whose stored `artifact_ref` matches, that **omitting** `artifact_ref` defaults to `refined_requirements.html` (byte-compatible), and that a traversal/`.html` violation is `422`; (c) the injector preserves artifact markup, is idempotent, and carries `{bridge, goal_slug, artifact_ref}` config | `agents/cast-comment-html/tests/test_comment_bridge.js` (jsdom, via `npm test`) + `cast-server/tests/test_html_comment_bridge_contract.py` + `cast-server/tests/test_comment_layer_inject.py`; the live in-iframe comment is the 1b browser-validated carry-forward (`spike-1b-result.md`) |

## Open Questions

- None blocking. All route, artifact-class, zero-click, checker-I/O, DOM, comment-API, versioning,
  diff-engine, and re-anchor contracts are resolved in the high-level plan, the Phase 4 plan, and
  `_shared_context.md`'s Naming Contract; this spec records them verbatim. The two deliberate
  exceptions — the diff-view transient-`id` (FR-025) and the `cast-comment-reanchor` bare-JSON
  carve-out (FR-027) — are recorded as intentional, not drift.
- **v4 (Phase 3 maker pipeline):** the happy-path inversion, the generating-state route, the logical
  non-DOM id backbone + the verbatim-carriage clause, the determinism-scope narrowing, and the
  structural-violation owner override are all resolved by the Phase 3 plan + `decisions-so-far.md` and
  recorded above (US14–US17, FR-029–FR-036, SC-010–SC-013). Two items were **explicit forward pointers,
  not open questions**: the LLM-judged quality gate that replaces the structural happy-path gate, and
  the four human-review flag columns that layer on the `flagged` status + `served-by` stamp — both were
  Phase 4a scope. The `gaps[]` WHAT-doc field + the optional `GAPS-DETECTED` HOW trailer are reserved
  Phase 5 seams with **zero Phase 3 behaviour**.
- **v5 (Phase 4a quality gate):** both v4 forward pointers are now **resolved and specified above** —
  the `cast-requirements-render-checker` LLM quality gate + the quality-driven rework loop
  (US18, FR-037–FR-038), the OWNER-OVERRIDE two-branch policy with PREFER-VALID-THEN-SCORE ranking
  (FR-039, superseding the v4 RATIFIED fork per `decisions-so-far.md` 104/107), and the four
  human-review flag columns + status-JSON exposure (FR-040), verified by SC-014–SC-016. The override
  rationale (**surface, don't suppress**; deterministic page only on literal no-output) is binding.
  **One deliberate deferral, not an open question:** the human-review **consumption** surface — the
  flagged-renders LIST (slug, reason, score, link) — is **Phase 5d** (owner-resolved 2026-06-12); 4a
  ships the flag **recording-only**. The model-tier tune-down for the checker (`[USER-DEFERRED]`) is a
  later review knob, not a 4a decision.
- **v6 (Phase 4b comment survival + diff narration):** nothing open. The comment/version layer is
  source-side, so a maker regenerate (same source, new HTML) cannot orphan a comment at the DB layer;
  the genuine exposure — silent `<mark>`-placement loss on a paraphrased DOM — is closed by the
  **comment-survival gate** (US19, FR-041–FR-042) riding the verbatim-carriage clause and reusing the
  single `container_text_index` walker (no copy). Per **DECISION #10 OVERRIDE** an in-block survival
  miss is **surfaced, not blocking** (served best-attempt + `structural_violation` flag + the read-time
  `.comment-unplaced` badge, FR-043), and the deterministic fallback still fires **only** on literal
  no-output — the v4 US17 "survival blocks publish" framing predates the override and is read through
  it. The diff-resolution agent extends **in place** to contract v2 (US13 S4, FR-044) and the diff
  narration is stored once per version cut, structurally validated against the deterministic change set
  (FR-045) and rendered by attachment only (US20, FR-046) — the FR-024 byte-for-byte guarantee is
  re-scoped to `counts`/`items` with `narration` a sibling. `block_diff`/`diff_render` and the
  canonical `.collab.md` read-only guarantee are unchanged; the maker never writes the source.
- **v7 (Phase 5 gap-fill + sign-off):** nothing open. The reserved v4 seams (`gaps[]`, the
  `GAPS-DETECTED` HOW trailer) are **activated** (US21, FR-047–FR-053): the maker fills genuine
  comprehension gaps by asking upstream through the tool-free `cast-requirements-gapfill` grounded-or-
  refuse subagent, the server-side `validate_evidence` (reusing the single `verbatim_locate`) makes
  "never fabricates" **enforced, not promised**, and every supplied detail rides the **unchanged** v2
  change-request gate under the goal's **GATE-ALL** policy (every gap CR human-gated) — the FR-016
  invariant is structural (no un-mark path, no code path by which un-approved text reaches a reader; the
  v2 cache/version machinery un-marks by regeneration). The `.rr-gap` page marker is class-based
  (question + one fixed status string, **never** the `proposed_body`), so the DOM contract + carriage +
  survival gates stay green on a marked render. SC-002's nine-family record is captured by
  `eval_family_sweep.py` (SC-020) and the **flagged-renders list** (FR-054, SC-021) is the minimal
  read-only consumption surface for the 4a flag columns — resolving SC-016's deferral. **Three
  deliberate deferrals, not open questions:** the `[USER-DEFERRED]` model-tier tune-down for the four
  pipeline agents (a post-e2e review knob); the human-review **queue/triage** UI (a future-goal owner
  call — the minimal list is the whole 5d surface); and the v2 human timed-read evaluation (out of
  scope under HOLD). **One principal post-sign-off follow-up** (owner-recorded in
  `decisions-so-far.md`): the HOW-layer CREATE/UPDATE-mode + readability-over-verbatim rework that the
  three flagged families (`bug_fix`/`pilot_poc`/`random_idea`) surface — to be detail-planned then
  executed as its own goal, not patched in 5d.
- **v8 (Phase-5 follow-up: HOW two-mode + render-snapshot anchoring):** nothing blocking — and the v7
  "principal post-sign-off follow-up" above is now **EXECUTED** (goal `refine-req-v3-how-update-mode`).
  The HOW maker's CREATE/UPDATE two-mode contract (FR-055/FR-056; **Spike 1a verdict FAIL →
  deterministic splice**, so the published UPDATE artifact is **server-assembled**, not a single LLM
  emission), the comment anchoring move to the render snapshot (FR-057; US8/US12 displacement + US19
  survival reoriented to render space, the `block_ref`/`anchor_space` columns, the server-resolved bridge,
  the ref-less-NULL-is-success rule), the US16 verbatim-carriage supersession (anchor labels +
  one-unit-one-container survive; CREATE leaf-text copy-exact dropped for readability, with FR-060's
  empty-shell gate as the new CREATE floor), the reanchor contract v3 (US13 Scenario 5 / FR-044), the
  gap-CR idempotency-under-UPDATE guarantee (FR-058), and the two `RENDER_UPDATE_*` knobs with the
  retired `RENDER_UPDATE_ENABLED` flag-gate (FR-061) are all resolved and recorded above, verified by
  SC-022–SC-024 (the nine-family sweep is now **9/9 clean**, superseding SC-020's 6/9 record). **One
  KNOWN LIMITATION (not an open question):** dropping CREATE leaf-text verbatim carriage for readability
  admits **paraphrase meaning-drift** — a dedicated paraphrase-meaning-fidelity checker is explicitly
  **OUT of scope** (HOLD); the `cast-requirements-render-checker` comprehension pass is the only guard,
  and a future review MAY add a fidelity dimension.
- **v9 (Phase 2b, exploration-pipeline-nxm: dual md/html viewer):** nothing blocking. The Diecast
  phase-tab viewer now renders render-class `.html` (via `<iframe srcdoc>`, null-origin sandbox) alongside
  `.md` (US22, FR-062–FR-063, SC-025); the refined-requirements HTML is reachable in-viewer as render
  **consumer #2** (exploration is **consumer #1**, produced by Phase 4) **without** retiring `/render`.
  US4 (render-class: read-only, no authorship suffix, atomic + `served-by` stamp) and US7 (selectable
  units, zero `id=`/`data-block-anchor` — the DOM contract Phase 3b's verbatim-substring anchoring + the
  `anchor_space='render'` path consume) are **REUSED, not superseded**, now applied to ALL render-class
  `.html` in the viewer. The 1b spike browser-validated the srcdoc embed + in-frame selection +
  postMessage source-identity guard (`spike-1b-result.md`); the `allow-scripts` (no `allow-same-origin`)
  sandbox is the forward-looking constraint that lets the Phase 3b bridge run. **Two deliberate
  out-of-scope items, not open questions:** in-iframe **commenting** (Phase 3b — this version ships the
  *viewer render* only) and the **exploration render pipeline** (Phase 4 produces
  `exploration/exploration.html`). Artifact ordering is md-source-first, render-after per directory
  (deterministic); Phase 4 MAY set its own ordering when it produces `exploration.html`.
