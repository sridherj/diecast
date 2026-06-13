# Execution Manifest: refine-req-v2-phase3a (Comprehension — HTML-First Render)

Splits `docs/plan/2026-06-11-refine-requirements-v2-phase3a-html-render.md` (Work Packages A–G) into
6 independently executable sub-phases. Phase 3a is the goal's **headline** thread (SC-001).

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase3a/spN_name/plan.md`".
3. After completion, update the Status column below.

> **⚠️ External precondition:** Phases 1 & 2 are *planned but not yet executed* (fan-out planning).
> sp1 assumes the `cast_server.requirements_render` parser package + Phase 2 `families.py` already
> exist. Verify (or execute those phases) before starting. See `_shared_context.md` → "External
> Preconditions". In particular, `BlockKind` must already include `EVIDENCE` + `DECISION`
> (Phase 2 Suggested Revision #1) or `bug_fix`/`pilot_poc` sections render unmodeled.

## Sub-Phase Overview

| # | Sub-phase | Directory | WP | Depends On | Status | Notes |
|---|-----------|-----------|----|------------|--------|-------|
| 1 | Visual theme + document template | `sp1_theme_and_template/` | A | External (Phase 1/2) | Not Started | Lifted toolkit; token-drift pin test |
| 2 | Block-recipe render engine | `sp2_recipe_render_engine/` | B | 1 | Not Started | The net-new build; pure `render_requirements()` |
| 3 | Goal Card + pill + disclosure + WHAT/HOW | `sp3_goal_card_and_disclosure/` | C+D | 2 | Not Started | The SC-001 surface; `goal_card.py` IA core |
| 4 | Serve + regenerate | `sp4_serve_and_regenerate/` | E | 3 | Not Started | Service + `GET /goals/{slug}/render` route |
| 5a | Checker + extractor + goldens + eval | `sp5a_checker_and_gates/` | F | 4 | Not Started | SC-001 gate; parallel with 5b |
| 5b | Spec lockstep + FR-007 guard | `sp5b_spec_and_guard/` | G | 4 | Not Started | Parallel with 5a; distinct files |

Status: Not Started → In Progress → Done → Verified → Skipped

No decision gates: the plan's only genuine fork (how an LLM checker "runs in CI") was resolved
interactively (golden snapshots in default CI + `eval_` harness). "Open Questions: None blocking."

## Dependency Graph

```
[External: Phase 1 parser pkg + Phase 2 families.py + EVIDENCE/DECISION BlockKinds]
        │
        ▼
   sp1 (A: theme + template)
        │
        ▼
   sp2 (B: recipe render engine)
        │
        ▼
   sp3 (C+D: Goal Card + disclosure + WHAT/HOW)   ← C & D merged: same template/renderer files
        │
        ▼
   sp4 (E: serve + regenerate)
        │
        ├──────────────┐
        ▼              ▼
   sp5a (F:         sp5b (G:
   checker +        spec +
   goldens +        FR-007
   eval)            guard)
        └──── parallel ────┘   (distinct files — no conflict)
```

**Critical path:** sp1 → sp2 → sp3 → sp4 → sp5a. sp5b runs in parallel with sp5a after sp4.
(Per the plan's Build Order: A → B → C/D → E → F; G is documentation lockstep parallel with F.)

## Parallel-Safety Audit (files touched)
- **sp5a** writes: `requirements_render/zero_click.py`, `bin/cast-render-zero-click`,
  `agents/cast-requirements-checker/*`, `tests/test_zero_click_extractor.py`,
  `tests/test_requirements_renderer.py` (golden/structural additions),
  `tests/golden/requirements_render/*`, `tests/eval_render_checker.py`,
  `tests/test_requirements_checker_agent.py`.
- **sp5b** writes: `docs/specs/cast-requirements-render.collab.md`, `docs/specs/_registry.md`,
  `tests/test_fr007_readonly_guard.py`.
- **No overlap** → sp5a ∥ sp5b is safe. (C+D were *merged* precisely because they would overlap on
  `document.html.j2` + `renderer.py`.)

## Execution Order

### Group 1
1. sp1 — Visual theme + document template (WP-A)

### Group 2 (after sp1)
2. sp2 — Block-recipe render engine (WP-B)

### Group 3 (after sp2)
3. sp3 — Goal Card + pill + disclosure + WHAT/HOW (WP-C+D)

### Group 4 (after sp3)
4. sp4 — Serve + regenerate (WP-E)

### Parallel Group 5 (after sp4 — run simultaneously)
5a. sp5a — Checker + extractor + goldens + eval (WP-F)
5b. sp5b — Spec lockstep + FR-007 guard (WP-G)

## Phase Gate (declare Phase 3a done only when all pass)
- `cd cast-server && pytest tests/test_requirements_renderer.py tests/test_goal_card.py
  tests/test_zero_click_extractor.py tests/test_render_route_and_service.py
  tests/test_fr007_readonly_guard.py tests/test_theme_token_drift.py
  tests/test_requirements_checker_agent.py` — all green (default CI battery).
- `python tests/eval_render_checker.py` — **`can_state_what: true` for every family** (the SC-001
  sign-off, owner decision #1).
- `bin/cast-spec-checker` exit 0 on the frozen fixture; `cast-requirements-render.collab.md`
  registered and lints clean.

## Progress Log
- 2026-06-11 — Execution plan created by `cast-create-execution-plan` (autonomous fan-out run).
