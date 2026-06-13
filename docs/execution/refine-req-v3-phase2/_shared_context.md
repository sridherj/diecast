# Shared Context: refine-req-v3-phase2 (Discoverable Commenting & an Honest Fallback)

## Source Documents
- Plan: `docs/plan/2026-06-12-refine-requirements-v3-phase2-commenting-fallback.md`
- Reconciliation (cross-phase edges): `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- Goal plan: `docs/goal/refine-requirements-better-rendering-v3/plan.collab.md`

## Project Background

Phase 2 of the six-phase "Refine Requirements — Better Rendering (v3)" effort. It **ships
independently, ahead of the rest of v3** and shares no files with Phase 1. It does two
unrelated jobs:

1. **Discoverable commenting (US6 / FR-014 / SC-006).** A first-time reader of a *served*
   render currently has to guess the hidden select-text gesture. This phase adds a visible
   affordance + a hint that *states the gesture*, so an unprompted reader can comment.

2. **Honest deterministic fallback (FR-006).** v3 keeps the deterministic renderer in the
   codebase as the true no-output-crash fallback. Two dogfooding defects make that fallback
   look broken: (a) raw inline markdown (`**bold**`, `` `code` ``) leaks as literal characters
   onto the Goal Card; (b) the sentence splitter truncates the job statement on abbreviations
   (`vs.`, `e.g.`, `30 min.`). This phase hardens the substrate so the page v3 later falls
   back to is itself clean.

The key code-reading insight: the leak is confined to the Goal Card *text* paths — all of
which inject via `escape()`, **not** the markdown pipeline the recipe sections already use —
so the fix is a small **pure helper**, not a renderer redesign.

## Operating Mode

**HOLD SCOPE** (`scope_mode: hold`). Rigorous adherence to the four work items only. No card
redesign, no comment-UX rework beyond the additive affordance, no new renderer capabilities.

## Codebase Conventions

- **`goal_card.py` purity rule (load-bearing).** Its module docstring forbids "markdown
  rendering"; functions are pure functions of `ParsedRequirements` — no I/O, no DB, no
  timestamps. The `strip_inline_markdown` helper is a *pure text transform* (stripping markers),
  **not** rendering — keep it that way and amend the docstring so the rule and code can't drift.
- **Dependency direction:** `renderer.py` → `goal_card.py`, **never** the reverse. 2a's helper
  lives in `goal_card.py` and `renderer.py` imports it (it already imports that module).
- **Naming:** module uses `_snake` private helpers + exported-verb public functions
  (`extract_job_statement`, `derive_l2_assertions`). New names follow suit:
  `strip_inline_markdown`, `_split_first_sentence`, `_ABBREVIATIONS`.
- **Comment CSS lives in `_theme.css.j2`** next to the `.comment-*` rules. **Class selectors
  only — no `id=`** anywhere in render output (DOM contract).
- **Comment family uses `.comment-*` BEM-ish selectors** (`.comment-pill`,
  `.comment-tray-host`, `.comment-composer__*`). New affordance follows: `.comment-affordance`,
  `.comment-affordance__hint`.
- **Tests:** follow `/cast-pytest-best-practices`; data-driven where natural
  (`pytest.mark.parametrize`). Pin regressions to the *actual dogfooding strings*.

## Key File Paths

| File | Role | Phase-2 touch |
|------|------|---------------|
| `cast-server/cast_server/requirements_render/goal_card.py` | IA-core: `extract_job_statement`, `derive_l2_assertions`, `_first_sentence`, `_table_cell`, `_enumerated_items`, `_strip_leading_marker` | **2a** — add `strip_inline_markdown`, `_split_first_sentence`, `_ABBREVIATIONS`; apply strip at card-text production points |
| `cast-server/cast_server/requirements_render/renderer.py` | Owns HTML; `_render_scope_grid` (`_row_description` outcomes, `_strip_leading_marker` out-of-scope) | **2a** — strip scope-grid items before `_ul`/`escape` (import helper from `goal_card.py`) |
| `cast-server/cast_server/static/requirements_comments.js` | Served-render comment JS; `init()` runs only when `data-goal-slug` present | **2b** — inject `.comment-affordance` into `.rr-controls` |
| `cast-server/cast_server/requirements_render/templates/_theme.css.j2` | Theme CSS, home of `.comment-*` rules | **2b** — style `.comment-affordance` / `.comment-affordance__hint` |
| `cast-server/tests/test_goal_card.py` | 7 existing goal_card unit tests | **2a** — add strip + abbreviation tests |
| `cast-server/tests/test_requirements_renderer.py` | Golden byte-compare; `UPDATE_GOLDENS=1` regen path | **2c** — regen goldens once |
| `cast-server/tests/golden/requirements_render/*.html` | 13 golden families (regression net) | **2c** — regenerate + per-family diff review |
| `cast-server/tests/ui/` (requirements-render screen, `cast-ui-test-requirements-render`) | Browser-capable UI assertions | **2b** — add affordance-present + click-reveals-tray assertions |
| `cast-server/tests/test_fr007_readonly_guard.py` | Read-only / DOM-contract structural guard | **2c** — re-run as part of green gate |
| `docs/specs/cast-requirements-render.collab.md` | Render + commenting spec (FR-028, SC-009 selectors, US7/FR-013 DOM contract) | **2b** — `/cast-update-spec` records additive affordance + new selector |

## Data Schemas & Contracts (preserved — do NOT violate)

- **v2 DOM contract:** quote/verbatim-substring anchoring; **no `id=`, no `data-block-anchor`**
  anywhere in canonical render (`cast-requirements-render.collab.md` FR-013/US7). Everything
  added here honors it — `.comment-affordance` is class-only.
- **v2 commenting naming contract:** `static/requirements_comments.js`; same-door comment API
  at `/api/goals/{slug}/requirements/comments`; `.comment-pill` / `.comment-composer` /
  `.comment-tray-host` selectors; **FR-028 progressive enhancement** — bare `file://` open ⇒
  scripts 404 ⇒ fully readable read-only document (so the JS-injected affordance must NOT
  appear on `file://`).
- **Fallback policy (binding seed decision):** the deterministic renderer stays as the true
  no-output-crash fallback. These fixes *harden* it; nothing here removes it or weakens its
  determinism / byte-stability.
- **Golden machinery:** `tests/test_requirements_renderer.py` byte-compares against
  `tests/golden/requirements_render/*.html`; `UPDATE_GOLDENS=1` is the documented
  intentional-change path. This phase changes golden bytes (card text + theme CSS) and must
  leave the suite green via that path — **regen happens exactly once, in 2c**.

## Pre-Existing Decisions (autonomous forks from the plan — already settled, do not relitigate)

1. **Strip, don't convert, inline markdown on the Goal Card** — strip-to-plain-text preserves
   purity, keeps card text contiguous escaped plain text (zero new DOM surface under no-`id=`).
2. **Strip at each production point, not inside `_first_sentence`** — explicit call sites (job
   statement, assertions, scope grid); the scope-grid path doesn't flow through `_first_sentence`.
3. **Abbreviation handling via a token-set candidate scan** over `finditer`, not lookbehind.
   Over-long-on-genuine-`etc.` accepted as the honest failure mode.
4. **Affordance is JS-injected into `.rr-controls`**, not template-rendered (FR-028 + golden
   cleanliness + mirrors the convergence-chip pattern). CSS still lives in `_theme.css.j2`.
5. **Affordance = teach + surface, not a new creation path.** Click reveals the tray + pulses
   the gesture hint; creation stays select→pill→composer through the same-door API.
6. **One golden regeneration, gated and reviewed (2c)** — not per-sub-phase regens.

Plan-review hardening decisions folded into 2a/2b verification (CQ2, CQ3, T1, T2, T3, P1) —
see each sub-phase's Verification section.

## Relevant Specs

- **`docs/specs/cast-requirements-render.collab.md` (Draft v2)** — covers `goal_card.py` and
  `renderer.py` (touched by 2a) and the commenting UX / SC-009 selector list (touched by 2b).
  - **2a:** the spec does not specify card-text formatting at this granularity → **no spec
    conflict, no `/cast-update-spec` for 2a.**
  - **2b:** the visible affordance extends the recorded commenting UX (locked decision #7:
    select → pill → composer) and the SC-009 named-selector list → **`/cast-update-spec` is
    mandatory in 2b** (additive clause + add `.comment-affordance` to SC-009; DOM contract
    US7/FR-013 and decision #7 flow stay verbatim).
  - Sub-phase agents read the spec on-demand only when modifying spec-linked files.
- `docs/specs/cast-goal-classification.collab.md` (Draft v1) — `FAMILY_RECIPES` consumed by the
  renderer (context only; recipe machinery untouched).

## Cross-Phase Hard Edge (from reconciliation — non-negotiable)

**2a → 3b (HARD).** `strip_inline_markdown` must be a **pure, import-stable, module-level public
helper in `goal_card.py`** because Phase 3's `maker_gate.py` (`check_html` verbatim-carriage
check) later imports it. Phase 2 ships ahead, but 2a specifically sits on Phase 3's critical
path. Do not bury it, rename it, or make it depend on render state. Naming, signature, and
import location are a contract for downstream phases.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp2a (honest fallback — card text) | Sub-phase | None | sp2c | sp2b |
| sp2b (discoverable commenting affordance) | Sub-phase | None | sp2c | sp2a |
| sp2c (green gate — golden regen) | Sub-phase | sp2a, sp2b | — | — |

**No decision gates in Phase 2.** 2a and 2b touch disjoint files (Python card paths vs.
JS/CSS/spec/UI tests) — verified safe to run in parallel. Both perturb golden bytes, so golden
regeneration is consolidated into 2c after both land.
