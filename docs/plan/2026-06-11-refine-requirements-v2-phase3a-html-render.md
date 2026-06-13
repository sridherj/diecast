# Refine Requirements v2: Phase 3a — Comprehension: HTML-First Render

## Overview

Refinement gains a **read-only HTML render** as the primary human-consumption artifact: an
above-the-fold **Goal Card** (classification pill + one-sentence job statement + 3–5 outcome/scope
assertions, all WHAT, zero clicks), an L1/L2/L3 visual hierarchy lifted nearly verbatim from the
cast-preso toolkit, progressive disclosure of depth via native `<details>`, HOW quarantined to a
muted bottom "Directional" section, and per-family structural variation driven by Phase 2's
`FAMILY_RECIPES` — **this is the headline thread and the goal's only measurable headline criterion
(SC-001).** The key insight from exploration (Playbook 05): the 2-minute test is an
*information-architecture* problem, not a CSS problem — the block-recipe render engine over Phase 1's
typed block model is the entire net-new build; the visual foundation (tokens, fonts, `<details>`
styling, pill idiom, the `/preso/review` serving loop) is already paid for.

The key sub-deliverable is the **`cast-requirements-checker` agent** — the SC-001 gate (plan-review
decision #5): it opens the rendered HTML as an *unfamiliar reader* and, from the Goal Card + headings
alone, restates the job, primary outcome, and in/out scope — failing the render if it can't. It
doubles as the FR-013 "agent-as-consumer" demonstration. The human timed-read is deferred for v2.

This plan covers ONLY Phase 3a of the high-level plan (`goals/refine-requirements-v2/plan.collab.md`)
and adopts all prior canon from `docs/plan/refine-requirements-v2-decisions-so-far.md`.

## Position in Overall Plan

```
Phase 1: Parser & Thin Spine ──► Phase 2: Classification ──┬──► Phase 3a: HTML Render (THIS PLAN)
   (ParsedRequirements,              (WorkFamily, FAMILY_RECIPES,  │      (headline, SC-001)
    BlockKind, content_hash,          RECIPE_REALIZATION,          └──► Phase 3b: Router (parallel)
    requirement_versions)             classification front-matter)
                                                                   Phase 3a ──► Phase 4: Annotation
                                                                     (selectable DOM is 4's substrate)
```

Phase 3a is ON the critical path: Phase 4's vanilla-JS comment layer captures selections from the
DOM this phase renders. Phase 3b is independent of this plan (it reads `classification.family` only).

## Depends On (from prior plans)

| Prior deliverable | Where | How Phase 3a consumes it |
|---|---|---|
| `ParsedRequirements` (title, front_matter, preamble, blocks, unrecognized_sections, source_text, content_hash) | Phase 1 `requirements_render/blocks.py` | The renderer's sole input — `parse_requirements_file()` → render |
| `BlockKind` enum **including the Phase 2-revised `EVIDENCE` + `DECISION` kinds** | Phase 1 `blocks.py` + Phase 2 Suggested Revision #1 | `RECIPE_REALIZATION` targets; the render pulls blocks by kind |
| `Block{kind, level, body, heading, ref, line_start, line_end}` — `ref` in-memory only, never a DOM anchor | Phase 1 `blocks.py` | Section ordering + body slices; **`ref` is NEVER emitted as an `id`** (thin-spine) |
| `content_hash(text)` | Phase 1 `hashing.py` | Staleness check for lazy regeneration (embedded source-hash vs file) |
| `requirement_version_service.get_current()` | Phase 1 services | Goal Card version chip (`v3`) |
| `WorkFamily`, `FAMILY_RECIPES`, `RECIPE_REALIZATION`, `FAMILY_PILL_LABELS`, `modulate()` | Phase 2 `requirements_render/families.py` | The recipe → ordered sections → HTML pipeline; pill label text + hover-reasoning rule |
| `validate_classification(raw) -> Classification` | Phase 2 `families.py` | Render-time read of `front_matter["classification"]` (defence in depth; never crash) |
| `classification.family` front-matter contract (persist once, consume twice) | Phase 2 | The render NEVER re-classifies — it reads the persisted mapping only |
| `tests/fixtures/family_docs/` — one minimal valid doc per family | Phase 2 WP-D | Reused as the render inputs for the per-family golden snapshots |
| CSS class convention `family-pill family-pill--{value}`; hover shows `reasoning` | Phase 2 Naming Contract | 3a owns the HTML/CSS realization |
| Frozen fixture `tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | Phase 1 | The full-spec render fixture + FR-007 guard target |

**Sequencing note:** this is fan-out planning — Phases 1/2 are planned, not yet executed. If their
implementations land with drifted names, adopt the *landed* names and update this plan's references;
do not fork the vocabulary.

## Operating Mode

**HOLD SCOPE** — every design fork was already closed at plan review (owner, 2026-06-11):
"Illustrations: none in v2", "there is **no** `data-block-anchor`/`id="fr-007"` to emit", "the
human timed-read … is deferred", "HOW … omitted entirely … never padded". This plan's job is
rigorous adherence to the locked surface: no illustrations, no stored anchors, no framework, no
extra render modes. Every activity below traces to a bullet in the Phase 3a section of
`plan.collab.md` or the delegation instructions.

## Decisions Made This Session (owner, 2026-06-11, interactive)

1. **SC-001 gate = split CI integration.** Deterministic **golden-HTML snapshot tests per family run
   in default pytest CI** (structural regressions caught cheaply, no API key/cost/flakiness). The
   **LLM `cast-requirements-checker` runs via an eval-style harness** (`tests/eval_render_checker.py`,
   mirroring Phase 2's `eval_classifier_corpus.py` — excluded from default discovery by the `eval_`
   filename) — on demand, and as the phase-gate before Phase 3a is declared done. This is the precise
   reading of "runs in CI per family with one golden HTML snapshot per family."

## Naming Contract (Phase 3a sets these; Phase 4 MUST adopt)

- **Renderer:** `cast_server.requirements_render.renderer` —
  `render_requirements(parsed: ParsedRequirements, *, version: int | None = None) -> RenderResult`
  where `RenderResult` is a frozen dataclass `{html: str, warnings: tuple[str, ...]}`. Pure function:
  no I/O, no DB, deterministic (no timestamps — goldens depend on this).
- **Templates:** package-local `cast_server/requirements_render/templates/` rendered through the
  package's own `jinja2.Environment(PackageLoader(...), autoescape=True)` — importable and testable
  without FastAPI. Main template `document.html.j2`; inline-styles partial `_theme.css.j2`.
- **Zero-click extractor:** `cast_server.requirements_render.zero_click.extract_zero_click_view(html: str) -> str`
  — the visible-without-clicking text surface (drops closed-`<details>` content, keeps `<summary>`
  text). Thin bin wrapper `bin/cast-render-zero-click` (sys.path bootstrap, same pattern as Phase 2's
  `bin/cast-classify-gate`).
- **Service:** `cast_server.services.requirements_render_service` — flat functions, house DB pattern:
  `rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None) -> Path | None`.
- **Route:** `GET /goals/{slug}/render` in `routes/pages.py` (human surface — pages, not `/api`).
- **Generated artifact:** `goals/{slug}/refined_requirements.html` — read-only, self-contained,
  headed by `<!-- AUTO-GENERATED: ... -->` + `<!-- source-hash: <content_hash> -->`.
- **Checker agent:** `agents/cast-requirements-checker/` (`cast-requirements-checker.md` +
  `config.yaml`: `model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `timeout_minutes: 10` — same shape as `cast-preso-check-content` and
  Phase 2's classifier, per plan-review D2 precedent).
- **Verdict schema (canonical):**
  `{can_state_what: bool, restated_job: str, restated_outcome: str, restated_scope: {in: [], out: []}, missing: [], score: float, issues: []}`
  — the four delegation-mandated fields (`can_state_what`, `restated_job`, `missing`, `score`) are
  load-bearing; the rest are extensions in the preso D1-verdict style.
- **DOM contract for Phase 4 (the "selectable unit"):** every rendered block is one semantic
  `<section>`/`<li>` whose text content is contiguous (no per-word/per-line span fragmentation, no
  `user-select` suppression), placed under a real heading element (`<h2>`/`<h3>`) so the comment
  layer can derive the nearest-heading **hint** from the DOM. **There are NO element `id`s and NO
  `data-block-anchor` attributes** — the thin-spine decision deleted stored anchors; Phase 4 stores
  the quote and re-derives placement by subagent.

## Sub-phase: Comprehension — HTML-First Render

**Outcome:** `GET /goals/{slug}/render` serves a self-contained, read-only HTML render of
`refined_requirements.collab.md`, regenerated lazily when the source hash changes. The render leads
with a zero-click Goal Card (pill + job statement + outcome/scope assertions), varies structure per
family via `FAMILY_RECIPES`, collapses only depth, quarantines HOW, renders stubs as a
prompt-to-begin, and never mutates the markdown (FR-007 guard extended and green). One golden HTML
snapshot per family passes in default CI; the `cast-requirements-checker` agent exists, returns the
canonical verdict, and passes `can_state_what: true` on every family's golden via the eval harness.

**Dependencies:** Phase 1 (parser/block model, hashing, version service) + Phase 2 (taxonomy, recipes,
realization map, pill labels, family fixtures).

**Estimated effort:** 3–5 sessions (A+B ≈ 1.5–2, C+D ≈ 1, E ≈ 0.5, F ≈ 1, G ≈ 0.5).

**Verification (phase gate):**
- `pytest tests/test_requirements_renderer.py` — renders every `tests/fixtures/family_docs/` fixture
  + the frozen full-spec fixture; golden-HTML comparison per family
  (`tests/golden/requirements_render/{family}.html`, regenerated via `UPDATE_GOLDENS=1`); structural
  assertions: Goal Card outside any `<details>`; pill present with `family-pill--{value}` class;
  scope compare renders open; **zero `id=` attributes and zero `data-block-anchor` on requirement
  sections**; zero hardcoded hex outside the `:root` token block; every block under a heading
  element with contiguous text.
- `pytest tests/test_zero_click_extractor.py` — extractor output contains Goal Card + headings +
  `<summary>` text, and contains NO text that lives inside a closed `<details>` body.
- `pytest tests/test_render_route_and_service.py` — `GET /goals/{slug}/render`: 200 + regenerated
  file on stale hash; no-op (byte-identical file, no rewrite) when fresh; 200 prompt-to-begin when
  the goal exists but no/stub requirements; 404 on unknown slug (which also kills path traversal).
- `pytest tests/test_fr007_readonly_guard.py` (extended) — fixture `.collab.md` bytes identical
  before/after `rerender_requirements_html()`; `bin/cast-spec-checker` exit 0.
- Token-drift pin test — the inline `_theme.css.j2` `:root` token values == `static/style.css`
  `:root` values (the byte-identical premise, made a CI invariant).
- Agent pin test — `cast-requirements-checker.md` contains the rubric names `one-clear-takeaway` and
  `l1-l2-hierarchy` and every canonical verdict key (precedent: `tests/test_b1_domain_search.py`).
- `tests/eval_render_checker.py` (manual/slow, excluded from default CI — owner decision #1 above):
  dispatch the checker on each family's golden render; **gate: `can_state_what == true` for every
  family** and `missing[]` empty for job/outcome/scope. This is the SC-001 sign-off artifact.
- **Rescue-path tests (plan-review #4):** explicit renderer tests + goldens for the error rescues
  this plan emphasizes — (a) missing `classification` front-matter and (b) unparseable/garbage
  classification both ⇒ `GENERIC` recipe + the distinct "Unclassified — re-run refinement" pill
  state + a render warning; (c) a stub doc ⇒ prompt-to-begin card. Each asserts the expected
  `RenderResult.warnings` entry, not just the HTML — the rescues must be regression-pinned, not only
  the happy-path per-family goldens.

### Work Package A — Visual theme + document template (the lifted toolkit)

The self-contained document shell everything else renders into. Build first.

- Create `requirements_render/templates/document.html.j2`: a standalone HTML5 document (NOT
  extending the app's `base.html`) — title, inline `<style>` from `_theme.css.j2`, the five-layer
  body skeleton (Goal Card → recipe sections → unmodeled sections → Directional), and a tiny inline
  "expand all" control (the ONE allowed inline script — toggles `open` on all `<details>`; no
  framework, no library).
- `_theme.css.j2`: copy the `:root` tokens (already byte-identical between
  `static/style.css:2–48` and the preso toolkit `theme.css:12–31`) + lift
  `.slide-title / .l1-body / .l2-body / .source-citation / .callout / .question-annotation` from
  `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css:100–192` **keeping the class
  names verbatim** (the checker rubric language transfers directly), adapted from reveal.js
  em-scaling to document rem-scaling; plus `<details>/<summary>` styling, the
  `.family-pill--{value}` tint idiom (clone `static/style.css:1979–1992` `.phase-badge`), the
  side-by-side scope grid, and `@media print { details > * { display: block } }` force-open.
- **HARD RULE (FR-012): never hardcode hex outside the `:root` token block — always
  `var(--color-*)`.** Enforced by a unit test scanning the emitted HTML for hex literals outside
  the token definitions (one-line OSS rebrand stays a one-line override).
- **Deviation from Playbook 05 Step 2 (documented):** the playbook said "append the classes to
  `style.css`". This plan instead inlines them into the generated document via `_theme.css.j2`,
  because (a) the artifact must be **self-contained** like the `/preso/review` precedent it clones
  (`pages.py:299–307` serves the file verbatim; it must also view sanely from the goal folder), and
  (b) document-scale typography rules must not leak into the app shell. The token-drift pin test
  replaces the "single copy" property the playbook was buying.
- L1/L2/L3 assignment is by **importance, not heading depth**: L1 = survives a 90% cut (job
  statement, `.l1-body`/`.slide-title`); L2 = survives a 50% cut (outcomes, scope assertions,
  `.l2-body` + `.callout` accent for decided WHAT); L3 = acceptance detail/EARS/rationale/tables
  (inside `<details>`); `.question-annotation` muted/italic = tentative HOW;
  `.source-citation` = provenance lines. L2 must never visually out-weigh L1.

### Work Package B — Block-recipe render engine (the net-new build)

- `requirements_render/renderer.py`: `render_requirements(parsed, *, version=None) -> RenderResult`.
  Pipeline: read `parsed.front_matter.get("classification")` → `validate_classification()` (Phase 2;
  never crash) → `recipe = modulate(FAMILY_RECIPES[family], **modifiers)` → for each `RecipeBlock`
  in order, pull the matching parser blocks via `RECIPE_REALIZATION` and render that section; then
  unmodeled sections; then Directional. **The render never re-classifies** — absent/unparseable
  classification ⇒ `GENERIC` recipe + a distinct "Unclassified — re-run refinement to classify"
  pill state (visually distinct from a model-selected `generic`; emits a render warning).
- **One canonical visual treatment per block** (the consulting-exhibit shape): assertion heading →
  bold-lead bullets → `.source-citation` line. Block bodies convert markdown → inline HTML via the
  installed `markdown` lib (tables, bold, links) — scoped inside each section, never a whole-document
  `md.markdown()` dump (the structure-blind path this phase exists to replace). **(plan-review #5)
  reuse a single configured `markdown.Markdown()` instance with `.reset()` between sections rather
  than calling module-level `markdown.markdown()` per block** — avoids re-initializing the parser +
  extension chain once per section on every render.
- **Stub → prompt-to-begin:** deterministic `is_stub(parsed) -> bool` (no blocks beyond `INTENT`
  AND source under `STUB_WORD_THRESHOLD = 200` words) — **defined once in the Phase 1
  `requirements_render` parser package (canonical home), imported here** (plan-review #1: the "stub"
  notion is shared with Phase 1b's reviewer-skip and Phase 2's classify-floor; a single predicate
  prevents three drifting 200-word thresholds) → render a prompt-to-begin card (what exists +
  "refine to build this out"), never an empty skeleton (Template-Enforcer guard at the render layer).
- **`unrecognized_sections` are never dropped** (the Phase 1 forward-flag this phase must consume):
  render each verbatim (per-section `md.markdown`) at the bottom before Directional, inside an L3
  `<details>` marked "unmodeled section", and emit a render warning naming it. Zero silent drops.
- **Density warnings, not failures** (Playbook pitfall #10): >50 words/block, >15 words/bullet,
  >6 elements/unit → entries in `RenderResult.warnings` (surfaced in the route log and the eval
  report; a too-dense block is an SC-001 regression caught at generation time).
- **Determinism:** no timestamps anywhere in the HTML; the only run-varying value is the
  `source-hash` comment (a pure function of input). Goldens depend on this.

### Work Package C — Goal Card + classification pill (the entire SC-001 surface)

- Above the fold, always open, **zero clicks**, outside any `<details>`: the family pill
  (`FAMILY_PILL_LABELS[family]` text, `class="family-pill family-pill--{value}"`,
  `title="{classification.reasoning}"` — the Phase 2 hover rule) + a version chip
  (`v{n}` from `requirement_version_service.get_current()`, omitted when no snapshot exists;
  open-comment count is `[PENDING Phase 4]` — leave a clearly-marked template slot, render nothing
  until Phase 4 wires it) + the **L1 job statement** + **3–5 L2 assertions**.
- **Job-statement extraction (deterministic, in `renderer.py`):** the bolded `**Job statement:**`
  lead inside the `INTENT` block when present (the refined template emits it); else the Intent's
  first sentence; if neither yields a sentence, emit a render warning ("no job statement — SC-001 at
  risk") and fall back to the H1 title. Assertion-format headings are the single
  highest-leverage SC-001 rule — the warning is the renderer's lever on authoring.
- **L2 assertion derivation (deterministic priority order, capped at 5, never padded):** SC rows
  (criterion text — the outcomes) → Out-of-Scope bullets (lead phrase, rendered as boundaries) →
  for families whose recipes carry neither (e.g. `bug_fix`, `random_idea`): the Intent's enumerated
  thread/numbered-list items. Fewer than 3 available ⇒ show what exists (a sparse card is honest;
  an invented assertion is a lie to the reader).
- **Scope renders open, side-by-side** (a comparison is never collapsed): left column = primary
  outcomes (SC criteria or Intent threads) in `.callout` accent; right column = Out-of-Scope bullets
  in muted treatment. Omit the grid entirely when the family's recipe has no `SCOPE` block.
- **Code organization (plan-review #3):** the deterministic Goal Card heuristics
  (`extract_job_statement`, `derive_l2_assertions`) live in a dedicated
  `requirements_render/goal_card.py`, unit-tested in isolation; `renderer.py` stays the thin
  recipe → ordered-sections → HTML pipeline that *calls* them. The IA logic is the SC-001 core and
  must be testable without rendering a full document. (`is_stub` lives in the Phase 1 package per
  plan-review #1, not here.)

### Work Package D — Disclosure boundary + WHAT-before-HOW

- **Only depth wraps in `<details>` (closed by default):** acceptance scenarios + EARS + independent
  tests inside each user story; the full FR and SC tables; constraint detail; evidence detail beyond
  its lead line; rationale. Each US renders heading + story sentence open (L2), depth collapsed (L3).
  **The WHAT is never behind a `<details>`** — Goal Card, section lead assertions, and the scope
  compare are always open. Any disclosure on the WHAT is a bug, testable structurally.
- A11y + print: every `<summary>` carries discernible visible text (the section's assertion
  heading); `@media print` forces all open (WP-A CSS); the "expand all" control (WP-A) covers deep
  review vs. the 2-minute skim.
- **WHAT-before-HOW (FR-001):** the `DIRECTIONAL` block renders last, in the `.question-annotation`
  muted/italic grammar, explicitly marked "non-binding — subject to change by exploration". When the
  family makes HOW irrelevant (`data_analysis`, `personal_non_eng` — Phase 2's omit-not-pad rule)
  AND no Directional block exists, the section is **omitted entirely, never padded**. If an author
  wrote genuine Directional content in such a family, render it (never hide authored content — the
  Phase 2 checker already WARNs on it; the render is not a second enforcement point).
- Tentative vs decided visual grammar (Playbook pitfall #4): `.callout` accent = decided WHAT;
  `.question-annotation` muted = open/tentative. Confidence is visible, not implied.

### Work Package E — Serve + regenerate (clone the preso loop)

- `services/requirements_render_service.py` → `rerender_requirements_html(goal_slug, *, goals_dir=None,
  db_path=None) -> Path | None`: read `goals/{slug}/refined_requirements.collab.md` (missing →
  `None`); parse; **lazy staleness check** — if the existing `.html`'s embedded `source-hash` equals
  `content_hash(source_text)`, return the path without rewriting; else render and **atomically
  write** (tmp + `os.replace`) `goals/{slug}/refined_requirements.html` with the
  `<!-- AUTO-GENERATED: Read-only render of refined_requirements.collab.md. Do not edit. -->` header
  (mirroring `_rerender_tasks_md`, `task_service.py:389`) + the `source-hash` comment. **Reads the
  `.collab.md` only — never writes it** (FR-007).
- `GET /goals/{slug}/render` in `routes/pages.py`, cloned from `preso_review` (`pages.py:299–307`):
  validate the slug via `goal_service.get_goal()` first — unknown goal → 404 (this is also the
  path-traversal kill, resolving Phase 1's forward-flag); goal exists → call
  `rerender_requirements_html()` (self-healing regen on every view) → `HTMLResponse(file text)`;
  goal exists but no/stub requirements → 200 with the prompt-to-begin render (a legitimate product
  state, not an error).
- Add a one-line "View render" link on the goal page near the requirements artifact (SC-003 needs
  humans to actually find the HTML; one template line, no new UI surface).
- **Markdown stays the edit + agent source; HTML is generated read-only** — the EasyMDE edit path
  and every downstream agent contract are untouched (FR-007/SC-004). The server writing
  `refined_requirements.html` is the same class of write as `tasks.md`/`goal.yaml` (an
  AUTO-GENERATED render of canonical state), NOT an authored-artifact write — the
  delegation-contract concern ("cast-server never writes artifact files") binds Phase 5's writes to
  the canonical `.collab.md`, which this phase never performs. Stated in the WP-G spec.

### Work Package F — `cast-requirements-checker` + zero-click extractor + golden gates

- `requirements_render/zero_click.py` → `extract_zero_click_view(html) -> str` (stdlib
  `html.parser`): the text a non-clicking reader sees — keeps Goal Card, headings, open content,
  `<summary>` lines; drops closed-`<details>` bodies and tags. This makes "zero clicks" a
  **structural property of the gate input**, not prompt discipline. Bin wrapper
  `bin/cast-render-zero-click <file>` (sys.path bootstrap; exit 2 on unreadable input).
- Create `agents/cast-requirements-checker/cast-requirements-checker.md` + `config.yaml` (shape per
  Naming Contract). Lineage: `cast-spec-checker` (deterministic cousin) + `cast-preso-check-*`
  (verdict style). **Input:** path to a rendered `refined_requirements.html`; the agent runs
  `bin/cast-render-zero-click` and judges ONLY that extracted surface — it never opens the markdown
  or the raw writeup (it must be the unfamiliar reader). **Output:** EXACTLY ONE bare JSON object —
  the canonical verdict schema (Naming Contract) — no prose, no fences (Phase 2 classifier
  precedent). **Rubric, reused from cast-preso:** `one-clear-takeaway`
  (`cast-preso-check-content.md:42` — single takeaway identifiable in <5s from the Goal Card) +
  `l1-l2-hierarchy` (`:41` — job statement dominates; assertions secondary), plus the restate test:
  state the job, the primary outcome, and what's in/out of scope. **PASS rule (binary, code-checkable):**
  `can_state_what == true` AND no `missing[]` entry naming job/outcome/scope; `score` follows the
  preso scoring guidance (start 1.0, −0.15/error, −0.05/warning) and tracks improvement only — the
  gate is the boolean, not the float (LLM-judge score variance must not flip the gate).
- The checker is subagent-mode and deliberately **outside `cast-delegation-contract.collab.md`**
  (returns bare JSON as final text, writes no `.output.json`) — same carve-out Phase 2 stated for
  the classifier; restated in the WP-G spec so nobody "fixes" it into an output envelope.
- **Golden snapshots (default CI):** `tests/test_requirements_renderer.py` renders each
  `tests/fixtures/family_docs/` fixture → byte-compare against
  `tests/golden/requirements_render/{family}.html`; regeneration via `UPDATE_GOLDENS=1` env flag.
  Plus the structural assertion battery (Verification list above).
- **Eval harness (the SC-001 sign-off — owner decision #1):** `tests/eval_render_checker.py`
  dispatches the checker per family golden, prints per-family verdicts + warnings; gate =
  `can_state_what` true across all families. Run on demand and before declaring this phase done;
  excluded from default discovery by the `eval_` filename (Phase 2 precedent).
- Run `bin/generate-skills` after creating the agent; **then run `/cast-agent-compliance` (consult
  `/cast-agent-design-guide`) to validate `config.yaml` fields + the subagent I/O contract against
  fleet canon** (plan-review #2 — the string pin-test below checks rubric/verdict keys, not config
  conformance: `dispatch_mode`, `context_mode`, `timeout_minutes`, the subagent-mode carve-out); add
  the agent pin test (Verification list).
- v2 ships the checker **standalone** — it is NOT wired into `cast-refine-requirements`' flow (the
  ~650-line prompt ceiling is already claimed by Phases 1b/2; on-demand + eval use satisfies the
  phase outcome). Wiring it as a post-refinement step is a later increment.

### Work Package G — Spec lockstep + FR-007 guard extension

- → Delegate: `/cast-update-spec` (create mode) — author `docs/specs/cast-requirements-render.collab.md`
  documenting the new user-facing contracts: the `GET /goals/{slug}/render` route semantics
  (lazy regen, prompt-to-begin state, 404 rule); the generated `refined_requirements.html` artifact
  class (AUTO-GENERATED header, `source-hash`, read-only, exempt from authorship suffixes — it is a
  render like `tasks.md`/`goal.yaml`, which `cast-init-conventions.collab.md` already treats as
  generated); the zero-click extractor contract; the checker agent I/O (canonical verdict schema +
  PASS rule + the outside-the-delegation-contract carve-out); and the **Phase 4 DOM contract**
  (selectable units, nearest-heading derivation, NO ids/anchors). Register in
  `docs/specs/_registry.md`. Review output: names must match this plan's Naming Contract exactly
  (Phase 4 will cite it).
- Extend `tests/test_fr007_readonly_guard.py` (Phase 1's golden-file guard): after
  `rerender_requirements_html()` on the frozen fixture, source bytes identical +
  `bin/cast-spec-checker` exit 0 — the FR-007/SC-004 lock, extended the day HTML generation lands.

**Design review:**
- **Spec consistency:** no loaded spec conflicts. `cast-init-conventions.collab.md` (authorship
  suffixes, date prefixes) — the generated `.html` is a render, not an authored artifact; the WP-G
  spec records this classification rather than silently extending the conventions.
  `cast-delegation-contract.collab.md` — the checker is subagent-mode, outside the contract
  (stated, Phase 2 precedent); the server's `.html` write is a generated render, not the Phase 5
  artifact-write the contract constrains. New user-facing behavior (route, artifact class, agent
  I/O) → `/cast-update-spec` in WP-G, per the registry rule.
- **⚠️ FR-008 is superseded, and Playbook 05's keystone is overridden:** `refined_requirements.collab.md`
  FR-008 ("requirement elements shall carry stable identifiers usable as anchors") and the
  playbook's "the render is the origin of stable element IDs / emit `id=fr-007`" were both
  **deleted by plan-review decision #1 (thin spine)**. This render emits NO ids and NO
  `data-block-anchor`. An implementer reading the playbook must not re-add them — the golden
  structural test asserts their absence, and the WP-G spec records the DOM contract. (The
  requirements doc itself still carries the stale FR-008 — flagged for the owner; the high-level
  plan governs.)
- **Naming:** route under `pages.py` (human surface) mirrors `/preso/review`; service follows the
  flat-function house pattern (`goal_service`/`task_service` model per Phase 1 plan-review #1);
  `family-pill--{value}` adopted from Phase 2 verbatim ✓.
- **Architecture:** renderer is a pure function over `ParsedRequirements` (no I/O/DB) — golden
  tests need no server; the service owns file/DB I/O; the route owns HTTP. Package-local Jinja
  `Environment` keeps `requirements_render` importable without FastAPI (deliberate, documented in
  the package docstring — the app's `Jinja2Templates` in `deps.py` stays request-bound).
- **Error & rescue:** missing `.collab.md` → prompt-to-begin (never a stack trace); absent/garbage
  classification → `GENERIC` recipe + "Unclassified" pill + warning (never crash, never
  re-classify); unrecognized sections rendered + warned (zero silent drops); render write is
  atomic (tmp + `os.replace` — a crashed render never leaves a truncated artifact); render
  exception on GET → 500 with a plain message, existing `.html` left intact.
- **Security:** slug validated against the goals DB before any path use (404 on unknown — kills
  traversal; resolves Phase 1's forward-flag). Note: the existing `/preso/review/{goal_slug}` route
  builds a path from the raw slug without DB validation — same exposure class; flagged as a
  follow-up housekeeping fix outside this phase's scope.
- **A11y/print:** discernible `<summary>` text, print-forces-open, WCAG-AA-equivalent sizing via
  the toolkit's density limits (render-time warnings).

## Build Order

```
A (theme + document template) ──► B (recipe render engine) ──┬──► C (Goal Card + pill) ──┐
                                                             └──► D (disclosure + WHAT/HOW) ─┴──► E (serve + regenerate)
                                                                                                   │
                                              F (checker + extractor + goldens + eval) ◄──────────┘
                                              G (spec + FR-007 guard) — parallel with F, after A–E interfaces settle
```

**Critical path:** A → B → C/D → E → F. C and D are parallel edits over the same template (small —
coordinate, don't serialize sessions). G is documentation lockstep.

## Design Review Flags

| Item | Flag | Action |
|---|---|---|
| FR-008 / Playbook 05 keystone | Stable element IDs were deleted by plan-review decision #1; playbook still preaches them | Golden test asserts NO `id`/`data-block-anchor`; DOM contract in WP-G spec; flag stale FR-008 to owner |
| Playbook 05 Step 2 | "Append classes to style.css" conflicts with the self-contained artifact requirement | Documented deviation: inline `_theme.css.j2`; token-drift pin test replaces the single-copy property |
| Server file write | `refined_requirements.html` written by cast-server | Generated-render class (tasks.md precedent), not an authored artifact — stated in WP-G spec |
| Path traversal | Raw slug → filesystem path | `get_goal()` validation before path use; existing `/preso/review` shares the exposure — follow-up housekeeping flagged |
| Spec creation | New route + artifact class + agent I/O are user-facing contracts | `/cast-update-spec` create mode in WP-G; register in `_registry.md` |
| LLM in CI | Checker is an LLM agent; default CI must stay deterministic | Owner decision this session: snapshots in CI, checker as `eval_*` harness |
| Phase 4 hook | Goal Card has a comment-count slot with nothing to fill | `[PENDING Phase 4]` template slot, renders nothing until wired |

## Suggested Revisions to Prior Sub-Phases

1. **Phase 2 (`validate_classification`, minor):** the render calls it on the **persisted
   front-matter mapping**, which carries keys the raw classifier output lacks (`confirmed_by`,
   `classified_at`, `taxonomy_version`). Confirm it ignores unknown keys without recording
   coercions — otherwise every render of a correctly-classified doc reports phantom coercion
   warnings. A one-line tolerance note in Phase 2's WP-A; no interface change.
2. **Phase 1/2 (restated dependency, not a change):** Phase 3a render **requires** Phase 2's
   Suggested Revision #1 to Phase 1 (the `EVIDENCE` + `DECISION` BlockKinds) to have landed —
   without them, `bug_fix`/`pilot_poc` recipe sections fall into `unrecognized_sections` and render
   unmodeled. Sequencing constraint for the execution orchestrator.
3. **Phase 1 (parser, plan-review #1):** house the canonical `is_stub(parsed) -> bool` predicate +
   `STUB_WORD_THRESHOLD = 200` in the `requirements_render` parser package (it owns
   `ParsedRequirements`). Phase 3a imports it for the prompt-to-begin gate; Phase 1b's
   reviewer-skip and Phase 2's classify-floor should consume the *same* predicate so the three
   ~200-word "stub" notions cannot drift. Additive, one shared module constant — no interface change
   to existing Phase 1 deliverables.

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **SC-001 fails despite good styling** — the L1 line isn't a self-contained job assertion (an authoring problem the renderer can't fix) | High | Deterministic job-statement extraction + a loud render warning when absent; the checker eval per family catches IA failures before any human reads; Phase 1b's authoring upgrades (evidence-quoting, decisions) raise source quality |
| Goal Card L2 derivation yields a weak card for sparse families (`random_idea`, `bug_fix`) | Medium | Honest degradation (show what exists, never pad — the Template-Enforcer guard); per-family golden + checker eval make weakness visible per family, not on average |
| Golden snapshots brittle to benign template tweaks | Medium | Render determinism (no timestamps); `UPDATE_GOLDENS=1` regeneration path; structural assertions carry the invariants so goldens can be regenerated freely |
| Checker verdict variance (LLM judge) flips the gate | Medium | Gate on the binary `can_state_what` + `missing[]`, never the score; eval harness reports per-family so a flaky verdict is visible and re-runnable |
| Inline theme copy drifts from the preso toolkit / style.css tokens | Low-Med | Token-drift pin test in default CI; class names kept verbatim |
| Phase 4's selection capture breaks on fragmented DOM | Medium | The "selectable unit" DOM contract is spec'd (WP-G) + structurally tested (contiguous text, heading-derivable) before Phase 4 builds on it |
| FR-007 regression when HTML generation lands | Medium | Phase 1's golden-file guard extended in WP-G on day one; the service never opens the `.collab.md` for writing |

## Open Questions

**None blocking.** The one genuine fork — how an LLM checker "runs in CI" — was resolved
interactively this session (owner, 2026-06-11): golden snapshots in default CI, checker as an
eval-style harness and the phase-gate. Two non-blocking items are recorded as flags, not questions:
the stale FR-008 text in `refined_requirements.collab.md` (superseded by plan-review decision #1 —
owner may annotate the requirements doc at leisure), and the `/preso/review` path-validation
housekeeping (outside this phase).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|---|---|---|
| `cast-init-conventions.collab.md` | Authorship suffixes, generated-render conventions | None — generated `.html` classified as a render (like `tasks.md`); recorded in the new WP-G spec rather than silently extending conventions |
| `cast-delegation-contract.collab.md` | Output-file contract scope; "server never writes artifact files" | None — checker is subagent-mode (outside the contract, Phase 2 precedent); the `.html` write is a generated render, not an authored-artifact write |
| *(planned, Phase 2 WP-F)* `cast-goal-classification.collab.md` | `classification.*` front-matter schema, `FAMILY_RECIPES`/`RECIPE_REALIZATION` semantics, pill-label rule | n/a — the contract this render consumes; cite once it lands |
| *(new)* `cast-requirements-render.collab.md` | Created by WP-G via `/cast-update-spec` | n/a — becomes the contract Phase 4 cites (route, artifact class, DOM contract, checker verdict) |

## Decisions

> Appended by `cast-plan-review` (2026-06-11). Buffered in memory across the review and written once
> (B2 single-Write contract). Re-running with the same answers is a no-op; a changed answer updates
> the matching entry in place. All five were the agent's recommended option — the owner directed
> "if the question has an obvious recommended answer, don't ask; just proceed," so Architecture #1/#2
> were confirmed interactively and Code Quality/Tests/Performance adopted the recommendation.

- **2026-06-11T17:47:52Z — Architecture #1: where should the stub predicate live, given three phases define a ~200-word stub independently?** — Decision: Define the canonical `is_stub` + `STUB_WORD_THRESHOLD` once in the Phase 1 `requirements_render` parser package; Phase 3a imports it; recorded as Suggested Revision #3 to Phase 1. Rationale: DRY single source of truth; prevents three drifting 200-word thresholds across Phase 1b reviewer-skip, Phase 2 classify-floor, and Phase 3a prompt-to-begin.
- **2026-06-11T17:47:52Z — Architecture #2: should WP-F add a conformance gate for the net-new `cast-requirements-checker` agent?** — Decision: Yes — after `bin/generate-skills`, run `/cast-agent-compliance` (consult `/cast-agent-design-guide`) to validate `config.yaml` fields + the subagent I/O contract. Rationale: the string pin-test checks rubric/verdict keys only, never config conformance (`dispatch_mode`/`context_mode`/`timeout_minutes`); matches the plan's own pattern of delegating to fleet skills.
- **2026-06-11T17:47:52Z — Code Quality #3: should the Goal Card extraction heuristics be factored out of `renderer.py`?** — Decision: Yes — `extract_job_statement` + `derive_l2_assertions` move to a dedicated `requirements_render/goal_card.py`, unit-tested in isolation; `renderer.py` stays the thin recipe→sections→HTML pipeline. Rationale: the IA logic is the SC-001 core and must be testable without rendering a full document; explicit over a monolithic renderer.
- **2026-06-11T17:47:52Z — Tests #4: are the error-rescue paths covered by the verification battery?** — Decision: Add explicit renderer tests + goldens for (a) missing classification, (b) garbage classification → `GENERIC` + "Unclassified" pill + warning, (c) stub → prompt-to-begin, each asserting the `RenderResult.warnings` entry. Rationale: the plan emphasizes these rescues but the goldens only covered happy-path valid family docs; untested failure modes must be regression-pinned. More edge cases, not fewer.
- **2026-06-11T17:47:52Z — Performance #5: how should per-section markdown→HTML conversion be done?** — Decision: Reuse a single configured `markdown.Markdown()` instance with `.reset()` between sections instead of calling module-level `markdown.markdown()` per block. Rationale: avoids re-initializing the parser + extension chain once per section on every render; cheap, idiomatic, no behavior change.
