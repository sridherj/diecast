# Refine Requirements v2 — Decisions So Far (cumulative, fan-out planning)

> Maintained by `cast-fanout-detailed-plan`. Later sub-phases MUST adopt these names/interfaces
> unless they document a deviation under "Suggested Revisions to Prior Sub-Phases".

## Phase 1 — Foundation: Spec-Kit Parser & Thin Sidecar Spine  ✅ planned
Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1-foundation.md`

**Parser package (the core deliverable):** `cast_server.requirements_render`
(`cast-server/cast_server/requirements_render/`).
- `parser.py`: `parse_requirements(text: str) -> ParsedRequirements`,
  `parse_requirements_file(path: Path) -> ParsedRequirements` (read-only; never writes the file).
- `spec_grammar.py`: importlib bridge that **re-exports `bin/cast-spec-checker` regexes**
  (`US_HEADING_RE`, `FR_ID_RE`, `SC_ID_RE`, `EARS_SCENARIO_RE`, `SECTION_HEADING_RE`, `_section_spans`).
  The checker is NEVER modified — parser & FR-007 contract can't drift.
- `hashing.py`: `content_hash(text: str) -> str` (sha256 hex of UTF-8).

**Typed block model (consumed by render Phase 3a):**
- `BlockKind(str, Enum)` values: `intent, user_story, fr, sc, constraint, scope, directional, open_question`.
- `Block` (frozen dataclass): `kind, level (1=section / 2=element), body (byte-faithful slice),
  heading, ref ("US1"|"FR-007"|...), line_start, line_end`. **`ref` is in-memory ONLY** — never a DB
  column, never a comment anchor (thin-spine: stored anchors deleted).
- `ParsedRequirements`: `title, front_matter (dict), preamble, blocks (tuple), unrecognized_sections
  (never silent), source_text, content_hash`.

**Thin DB spine** — edit the CANONICAL `cast-server/cast_server/db/schema.sql` (the root `db/schema.sql`
is legacy/diverged — do NOT edit it) AND mirror identical `CREATE TABLE IF NOT EXISTS` in
`_run_migrations()` in `db/connection.py`. Three tables:
- `requirement_versions` (goal_slug, version, content, content_hash, status, created_at, ...).
- `requirement_comments` (id, goal_slug, version, **quoted_text**, section_hint, body,
  state ∈ open|resolved|orphaned, author, **author_kind ∈ human|agent** — the ONLY human/agent
  distinction (FR-013), created_at, updated_at). **No anchor/ref column** (thin spine).
- `comment_events` (append-only: created|resolved|reopened|orphaned|relocated).

**Service DB pattern (canon for ALL later service code):** flat functions, `db_path: Path | None = None`
injectable + `get_connection(db_path)`, modeled on `goal_service.py` / `task_service.py`
(**NOT** `orchestration_service.py`, which is file/manifest-based — owner Decision Opt A). Phase 4's
`comment_service` inherits this exact pattern.

**Design note:** `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md`
(files-canonical + thin spine; no per-element IDs; no anchoring engine — the "do not re-inherit ULIDs" marker).

## Phase 1b — Refinement Brain Upgrades (gbrain imports)  ✅ planned
Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1b-refinement-brain.md`
- **Prompt-only phase** — all edits target `agents/cast-refine-requirements/cast-refine-requirements.md`.
  Touches NO cast-server code.
- **Lands 3 of 6 gbrain imports** as new builds: dated `## Decisions` section (Chose/Over/Because),
  evidence-quoting mandate for confidence scores, scope-mode detection from signal words.
  (Stage-adaptive framework + exit-conditions already exist → verify-and-sharpen.)
- **Adversarial meta-pass CUT** (Decision #3) — the fresh-context reviewer subagent subsumes it.
- **Two owner-confirmed optional ports:** (a) `/spec` HARD GATE — **interactive-only; headless /
  HTTP-delegated runs auto-persist after the reviewer and record `auto-persisted: non-interactive run`**
  (owner override Opt A, 2026-06-11); (b) `/office-hours`-style **adversarial reviewer subagent** —
  a Claude Code **Agent-tool** subagent (fresh context, fail-soft), NOT an HTTP-registered child;
  runs before the HARD GATE; skips <200-word stubs.
- **Lockstep edits:** add `## Decisions` to `templates/cast-spec.template.md`; re-run `bin/generate-skills`
  after edits; `tests/test_b1_domain_search.py` pins the "Domain Web Search" section; ~650-line prompt ceiling.
- **Cross-phase → Phase 2:** the scope-mode confirm claims one `AskUserQuestion` slot in the worst case —
  Phase 2's classifier question budget should account for it. Dated `## Decisions` rows become per-version
  provenance feeding Phase 4 versioning.

---
### ⚠️ Cross-phase interface note for Phase 2 (resolve in the Phase 2 plan)
Phase 1's parser `BlockKind` (intent/user_story/fr/sc/constraint/scope/directional/open_question) is the
**spec-kit element** vocabulary. Phase 2's high-level plan introduces a SEPARATE **6-block document model**
(`problem, evidence, decision, scope, question, open`) for `FAMILY_RECIPES`. These are two distinct layers —
Phase 2 should state the mapping from parser `BlockKind`s → the recipe's 6 document blocks explicitly, and
reuse `ParsedRequirements.front_matter` as the persistence site for `classification.family`.

## Phase 2 — Classification: Family Detection & Block Recipes  ✅ planned
Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`
- **`WorkFamily(str, Enum)`** (LOCKED ~8 + fallback): `new_initiative, pilot_poc, bug_fix,
  data_analysis, random_idea (DEFAULT/floor), testing_qa, refactor_migration, personal_non_eng,
  generic (unmatched fallback)`. spike = within-family modifier; stub = render-state — neither is a family.
- **`RecipeBlock(str, Enum)`** (6-block document model): `problem, evidence, decision, scope, question, open`.
- **`FAMILY_RECIPES: dict[WorkFamily, tuple[RecipeBlock,...]]`** in `families.py` — ordered render skeleton;
  `RANDOM_IDEA == (PROBLEM,)` (the floor, nothing to pad). `FAMILY_PILL_LABELS: dict[WorkFamily,str]` (Phase 3a pill data).
- **`RECIPE_REALIZATION`** maps the 6 RecipeBlocks → Phase 1 parser `BlockKind`s (two distinct layers:
  recipe = semantic doc roles; BlockKind = concrete spec-kit grammar). Phase 3a render consumes this.
- **Front-matter contract:** persist under `front_matter["classification"]` with `family:` = the WorkFamily
  value (the ONE field Phase 3b router reads); `classification.family` is the cross-phase key.
  **`merge_front_matter(existing_text, classification) -> str`** in `requirements_render` (stdlib, deterministic)
  preserves all non-classification keys + body byte-for-byte — NOT LLM-regenerated. Persist once, consume twice; CI test asserts no re-classify on read.
- **`cast-goal-classifier` agent** = the classify seam (extracted, phase-agnostic; v2 sole caller = cast-refine-requirements).
  Strict tool-call `classify_work_family` → `{family, confidence, reasoning, uncertainty_factors, alt_family}`;
  ALL safety coercions → `RANDOM_IDEA` (GENERIC is only ever model-selected). Confidence gate in code: ≥0.9 silent / 0.5–0.9 confirm / <0.5 top-2 + escape.
- **RECORDED owner decisions this session (provenance being confirmed):** (D1) checker = ONE deterministic
  `bin/cast-spec-checker` with TWO levels (generic + family-specific via `--family` CLI flag), not per-family
  checker agents; `REQUIRED_SECTIONS_BY_FAMILY` mirrored in the checker (portable stdlib) + imported in the gate bin, pin-tested.
  (D2) `cast-goal-classifier` dispatch_mode = `subagent`.

## Phase 3a — Comprehension: HTML-First Render  ✅ planned
Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase3a-html-render.md`
- **Renderer:** `cast_server.requirements_render.renderer` (block-recipe engine over Phase 1 ParsedRequirements + Phase 2 FAMILY_RECIPES/RECIPE_REALIZATION).
- **Templates:** `cast_server/requirements_render/templates/` — `document.html.j2` + inline `_theme.css.j2` (token values pinned == `static/style.css` `:root`; never hardcode hex).
- **Zero-click extractor:** `cast_server.requirements_render.zero_click.extract_zero_click_view(html) -> str`.
- **Service:** `cast_server.services.requirements_render_service` (flat functions, house DB pattern).
- **Route:** `GET /goals/{slug}/render` in `routes/pages.py` (human surface, NOT /api); regen via `_rerender_requirements_html()` (mirrors `_rerender_tasks_md()`, AUTO-GENERATED header; HTML read-only).
- **`cast-requirements-checker` agent** (`agents/cast-requirements-checker/`): SC-001 gate, dispatch_mode=subagent; returns `{can_state_what, restated_job, missing[], score}`; rubric names `one-clear-takeaway` + `l1-l2-hierarchy`; eval harness `tests/eval_render_checker.py`; one golden HTML snapshot per family `tests/golden/requirements_render/{family}.html`.
- **DOM contract for Phase 4:** every rendered requirement block = ONE semantic, text-selectable unit; **zero `id=` and zero `data-block-anchor`** (thin spine — Phase 4 captures quote + nearest heading at selection time). Illustrations: NONE.

## Phase 3b — Routing: Phase-Agnostic Workflow Router  ✅ planned
Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`
- **`config.py`:** `WORKFLOW_REGISTRY: dict[str,dict]` (keys == WorkFamily string values; every value `status="stub"` + non-empty `steps`); `WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)` (derived, can't drift).
- **`workflow_router_service.py`:** `resolve(family: str|None) -> WorkflowHandle` (PURE + TOTAL, no DB/LLM/subprocess; None→needs-classification, unknown→self-announcing unmatched, never STARTER_TASKS); `record_routing_decision(slug, family, handle, ...)` = the one write path (house DB pattern). Mirrors `orchestration_service.py` STRUCTURE only (dataclass result + CLI hook), not its file persistence.
- **Stored handle:** `goals.routing_handle = f"{family}:{status}"` (e.g. `bug_fix:stub`) — STORED + documented staleness (review D1); **column `workflow_family` is the AUTHORITATIVE routing record** (review D2); front-matter `classification.family` reconciles to it on next refine.
- **goals columns** (ALTER TABLE migration, thread `GoalUpdate`, render to goal.yaml): `workflow_family, routing_handle, routed_at`. **HTTP:** `POST /api/goals/{slug}/route` (JSON; FR-016 pure re-resolve from persisted state).
- **Pins (review D4):** `set(WORKFLOW_REGISTRY)==WorkFamily values`; no-`STARTER_TASKS` + **no-LLM/no-subprocess/no-classifier-import source pin** on the router module; idempotent record; missing-`goal.yaml` degraded behavior pinned (review D5).
- **Single add-a-family checklist** (review D3): the Phase 2 classification spec is canonical; routing spec appends its registry step by cross-reference.
