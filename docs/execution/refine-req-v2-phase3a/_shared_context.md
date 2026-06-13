# Shared Context: refine-req-v2-phase3a (Comprehension — HTML-First Render)

> Read this file at the start of **every** sub-phase session. It is not inlined into each
> sub-phase plan — read it on disk.

## Source Documents
- **Plan (authoritative):** `docs/plan/2026-06-11-refine-requirements-v2-phase3a-html-render.md`
- **Cross-phase decisions (adopt names verbatim):** `docs/plan/refine-requirements-v2-decisions-so-far.md`
- High-level plan: `goals/refine-requirements-v2/plan.collab.md`
- Playbook 05 (background; **superseded on stable-IDs** — see "Pre-Existing Decisions"):
  `goals/refine-requirements-v2/.cast/exploration/playbooks/05-html-first-render.ai.md`

## Project Background
Refinement gains a **read-only HTML render** as the primary human-consumption artifact. The render
leads with an above-the-fold **Goal Card** (classification pill + one-sentence job statement + 3–5
WHAT outcome/scope assertions, zero clicks), uses an L1/L2/L3 visual hierarchy lifted nearly
verbatim from the cast-preso toolkit, discloses depth via native `<details>`, quarantines HOW to a
muted bottom "Directional" section, and varies structure per work-family via Phase 2's
`FAMILY_RECIPES`. This is the goal's only measurable headline criterion (**SC-001**: an unfamiliar
reader states a goal's WHAT in ~2 minutes).

The key insight (Playbook 05): the 2-minute test is an **information-architecture problem, not a CSS
problem**. The block-recipe render engine over Phase 1's typed block model is the entire net-new
build; the visual foundation (tokens, fonts, `<details>` styling, pill idiom, the standalone-serve
loop) is already paid for by `static/style.css` and the cast-preso toolkit.

The key sub-deliverable is the **`cast-requirements-checker` agent** — the SC-001 gate. It opens the
rendered HTML as an *unfamiliar reader* and, from the Goal Card + headings alone, restates the job,
primary outcome, and in/out scope — failing the render if it can't. It doubles as the FR-013
"agent-as-consumer" demonstration. The human timed-read is **deferred for v2**.

## ⚠️ External Preconditions (fan-out planning — verify before starting)
Phases 1 and 2 are **planned but NOT yet executed**. This entire execution plan assumes their code
has landed. Before sp1, confirm these exist; if missing, those phases must be executed first.

| Precondition | Where | Provides |
|---|---|---|
| `cast_server.requirements_render` parser package | `cast-server/cast_server/requirements_render/` | `ParsedRequirements`, `Block`, `BlockKind`, `parse_requirements_file()` |
| `requirements_render/hashing.py` | same | `content_hash(text) -> str` |
| `is_stub(parsed) -> bool` + `STUB_WORD_THRESHOLD = 200` | Phase 1 `requirements_render` parser pkg (canonical home — plan-review #1) | Phase 3a **imports** it; never redefine |
| `BlockKind` **incl. `EVIDENCE` + `DECISION`** (Phase 2 Suggested Revision #1) | `requirements_render/blocks.py` | `bug_fix`/`pilot_poc` recipe sections; without them those blocks fall to `unrecognized_sections` |
| `requirement_version_service.get_current()` | Phase 1 services | Goal Card version chip (`v{n}`) |
| `WorkFamily`, `FAMILY_RECIPES`, `RecipeBlock`, `RECIPE_REALIZATION`, `FAMILY_PILL_LABELS`, `modulate()`, `validate_classification()` | Phase 2 `requirements_render/families.py` | recipe → ordered sections pipeline; pill labels; render-time classification read |
| `front_matter["classification"]` contract (`family` = `WorkFamily` value) | Phase 2 | The render reads the persisted mapping; **never re-classifies** |
| `tests/fixtures/family_docs/` (one minimal valid doc per family) | Phase 2 WP-D | Per-family render inputs + golden snapshots |
| Frozen fixture `tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | Phase 1 | Full-spec render fixture + FR-007 guard target |
| `tests/test_fr007_readonly_guard.py` (Phase 1 golden-file guard) | Phase 1 | Extended by sp5b |

**If Phase 1/2 land with drifted names, adopt the *landed* names and update references — do not fork
the vocabulary.**

## Codebase Conventions
- **Path mapping:** the plan writes `tests/...`; on disk these live under **`cast-server/tests/`**
  (e.g. `tests/test_requirements_renderer.py` → `cast-server/tests/test_requirements_renderer.py`).
  Likewise `requirements_render/...` → `cast-server/cast_server/requirements_render/...` and
  `services/...` → `cast-server/cast_server/services/...`, `routes/...` →
  `cast-server/cast_server/routes/...`, `static/...` → `cast-server/cast_server/static/...`.
- **Service DB pattern (canon):** flat module-level functions, `db_path: Path | None = None`
  injectable + `get_connection(db_path)`, modeled on `goal_service.py` / `task_service.py`
  (NOT `orchestration_service.py`). Phase 3a's `requirements_render_service` follows this.
- **Routes:** human surfaces (HTML pages) live in `routes/pages.py`; machine APIs under `/api`.
  The new render route is a **page**, mirroring the existing `preso_review` route.
- **Generated renders:** the server writing `refined_requirements.html` is the same write class as
  `_rerender_tasks_md` (`task_service.py:~389`) and `goal.yaml` — an AUTO-GENERATED render of
  canonical state, NOT an authored-artifact write. It carries an `<!-- AUTO-GENERATED: ... -->`
  header and never edits the canonical `.collab.md`.
- **Agents:** one directory under `agents/<name>/` with `<name>.md` + `config.yaml`. After creating
  or editing an agent, run `bin/generate-skills`. `bin/` scripts bootstrap `sys.path` then import the
  package (see `bin/cast-spec-checker`).
- **Pure-function discipline:** `render_requirements()` is a pure function over `ParsedRequirements`
  (no I/O, no DB, **no timestamps** — goldens depend on determinism). I/O lives in the service; HTTP
  lives in the route.

## Key File Paths
| File | Role |
|---|---|
| `cast-server/cast_server/routes/pages.py` | Existing `preso_review` route to clone for `GET /goals/{slug}/render` |
| `cast-server/cast_server/services/task_service.py` | `_rerender_tasks_md` precedent (AUTO-GENERATED header, atomic write) |
| `cast-server/cast_server/static/style.css` | `:root` design tokens (`:root` ≈ lines 2–48); `.phase-badge` (≈1979–1992) the pill idiom to clone |
| `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css` | `.slide-title/.l1-body/.l2-body/.source-citation/.callout/.question-annotation` (≈100–192) to lift verbatim |
| `agents/cast-preso-check-content/` | Agent shape + verdict-style precedent for the checker; rubric names `one-clear-takeaway`, `l1-l2-hierarchy` |
| `agents/cast-preso-check-content/config.yaml` | `model: sonnet`, `dispatch_mode: subagent`, `timeout_minutes: 10`, `context_mode`, `allowed_delegations` |
| `bin/cast-spec-checker` | `sys.path` bootstrap pattern for the `bin/cast-render-zero-click` wrapper; FR-007 checker |
| `cast-server/tests/conftest.py` | Test fixtures/config; goldens land under `cast-server/tests/golden/requirements_render/` |
| `docs/specs/_registry.md` | Spec registry (sp5b registers the new spec) |

## Data Schemas & Contracts (the Naming Contract — Phase 4 MUST adopt; copy verbatim)
- **Renderer:** `cast_server.requirements_render.renderer.render_requirements(parsed: ParsedRequirements, *, version: int | None = None) -> RenderResult`.
  `RenderResult` = frozen dataclass `{html: str, warnings: tuple[str, ...]}`. Pure, deterministic, no I/O.
- **Goal Card heuristics (own module):** `cast_server.requirements_render.goal_card` —
  `extract_job_statement(...)`, `derive_l2_assertions(...)`. Unit-tested in isolation; `renderer.py`
  *calls* them.
- **Stub predicate:** `is_stub(parsed) -> bool` + `STUB_WORD_THRESHOLD = 200` live in the **Phase 1**
  parser package; Phase 3a imports — never redefines.
- **Templates:** `cast_server/requirements_render/templates/` rendered through the package's own
  `jinja2.Environment(PackageLoader(...), autoescape=True)` (importable without FastAPI). Main:
  `document.html.j2`; inline-styles partial: `_theme.css.j2`.
- **Zero-click extractor:** `cast_server.requirements_render.zero_click.extract_zero_click_view(html: str) -> str`.
  Bin wrapper `bin/cast-render-zero-click` (exit 2 on unreadable input).
- **Service:** `cast_server.services.requirements_render_service.rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None) -> Path | None`.
- **Route:** `GET /goals/{slug}/render` in `routes/pages.py`.
- **Generated artifact:** `goals/{slug}/refined_requirements.html` — read-only, self-contained,
  headed by `<!-- AUTO-GENERATED: ... -->` + `<!-- source-hash: <content_hash> -->`.
- **Checker agent:** `agents/cast-requirements-checker/` (`cast-requirements-checker.md` +
  `config.yaml`: `model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `timeout_minutes: 10`).
- **Verdict schema (canonical, bare JSON, no fences):**
  `{can_state_what: bool, restated_job: str, restated_outcome: str, restated_scope: {in: [], out: []}, missing: [], score: float, issues: []}`.
  The four delegation-mandated fields are `can_state_what`, `restated_job`, `missing`, `score`.
  **PASS rule (binary, code-checkable):** `can_state_what == true` AND no `missing[]` entry naming
  job/outcome/scope. The gate is the boolean — never the `score` float.
- **DOM contract for Phase 4 ("selectable unit"):** every rendered block is one semantic
  `<section>`/`<li>` with **contiguous** text (no per-word/per-line span fragmentation, no
  `user-select` suppression), under a real heading (`<h2>`/`<h3>`). **NO element `id`s and NO
  `data-block-anchor` attributes** — Phase 4 stores the quote and re-derives placement.

## Pre-Existing Decisions (locked; do not re-open)
- **Operating mode: HOLD SCOPE.** No illustrations in v2. No stored anchors / no `id=`. No framework
  (vanilla). No extra render modes. Human timed-read deferred. HOW omitted (not padded) when a family
  makes it irrelevant.
- **⚠️ FR-008 superseded + Playbook 05 keystone overridden** (plan-review decision #1, thin spine):
  "stable element IDs / emit `id=fr-007`" were **deleted**. This render emits NO ids and NO
  `data-block-anchor`. A golden structural test asserts their absence. An implementer reading
  Playbook 05 must **not** re-add them. (The requirements doc still carries stale FR-008 — flagged to
  owner; the high-level plan governs.)
- **SC-001 gate split (owner decision, 2026-06-11):** deterministic **golden-HTML snapshots run in
  default pytest CI**; the **LLM checker runs via an eval-style harness** `tests/eval_render_checker.py`
  (excluded from default discovery by the `eval_` filename prefix) — on demand and as the phase gate.
- **Deviation from Playbook 05 Step 2:** classes are **inlined** into the generated document via
  `_theme.css.j2` (self-contained artifact), NOT appended to `static/style.css`. A **token-drift pin
  test** replaces the "single copy" property the playbook was buying.
- **Checker is outside `cast-delegation-contract.collab.md`** (subagent-mode, returns bare JSON,
  writes no `.output.json`) — same carve-out Phase 2 stated for its classifier. Restated in the
  sp5b spec so nobody "fixes" it into an output envelope.
- **Plan-review decisions (this phase):** #1 `is_stub` in Phase 1 pkg; #2 run `/cast-agent-compliance`
  on the checker after `bin/generate-skills`; #3 Goal Card heuristics in `goal_card.py`; #4 explicit
  rescue-path tests + goldens (missing/garbage classification, stub); #5 reuse one
  `markdown.Markdown()` instance with `.reset()` per section.

## Relevant Specs
- `docs/specs/cast-init-conventions.collab.md` — authorship suffixes / generated-render conventions.
  The generated `.html` is classified as a **render** (like `tasks.md`), not an authored artifact;
  sp5b's new spec records this rather than silently extending conventions.
- `docs/specs/cast-delegation-contract.collab.md` — output-file contract; "server never writes
  artifact files". No conflict: the checker is subagent-mode (outside the contract); the `.html`
  write is a generated render. Sub-phases modifying spec-linked files must read the spec first.
- *(planned, Phase 2 WP-F)* `cast-goal-classification.collab.md` — the `classification.*`
  front-matter + recipe semantics this render consumes (cite once it lands).
- *(new, created by sp5b)* `cast-requirements-render.collab.md` — route, artifact class, zero-click
  contract, checker I/O, Phase 4 DOM contract.

## Sub-Phase Dependency Summary
| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|---|---|---|---|---|
| sp1 Theme + document template (WP-A) | Sub-phase | External (Phase 1/2) | sp2 | — |
| sp2 Recipe render engine (WP-B) | Sub-phase | sp1 | sp3 | — |
| sp3 Goal Card + disclosure + WHAT/HOW (WP-C+D) | Sub-phase | sp2 | sp4 | — |
| sp4 Serve + regenerate (WP-E) | Sub-phase | sp3 | sp5a, sp5b | — |
| sp5a Checker + extractor + goldens + eval (WP-F) | Sub-phase | sp4 | — | sp5b |
| sp5b Spec lockstep + FR-007 guard (WP-G) | Sub-phase | sp4 | — | sp5a |

No decision gates: the plan's only genuine fork (how an LLM checker "runs in CI") was resolved
interactively (golden snapshots in default CI + eval harness). "Open Questions: None blocking."
