# Execution Manifest: refine-req-v3-phase2 (Discoverable Commenting & an Honest Fallback)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase2/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase2/spN_name/plan.md`".
3. After completion, update the Status column below.

**No decision gates in this phase.** 2a and 2b touch disjoint files and may run in parallel;
2c runs after both. At 1–2 sessions total, executing 2a then 2b sequentially in one branch is
the practical default; the parallel split exists if two executors pick it up.

## Sub-Phase Overview

| # | Sub-phase | Directory | Depends On | Status | Notes |
|---|-----------|-----------|-----------|--------|-------|
| 2a | Honest Fallback — clean, untruncated card text | `sp2a_honest_fallback/` | — | Done | Parallel with 2b. Hard edge: `strip_inline_markdown` is a Phase-3 (3b) import contract |
| 2b | Discoverable Commenting — visible affordance | `sp2b_discoverable_commenting/` | — | Done | Parallel with 2a. Includes `/cast-update-spec` |
| 2c | Green Gate — golden regen, full suite green | `sp2c_green_gate/` | 2a, 2b | Done* | Single, reviewed golden regen for the whole phase |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp2a (card text fixes) ──┐
                         ├──► sp2c (golden regen + green gate)
sp2b (affordance) ───────┘
```

**Critical path:** 2a → 2c (2a and 2b independent; both touch golden bytes — 2a via card text,
2b via theme CSS — so golden regeneration happens exactly once, in 2c, after both).

**File-collision check (verified):** 2a touches Python card paths (`goal_card.py`,
`renderer.py`, `test_goal_card.py`); 2b touches JS/CSS/spec/UI-test (`requirements_comments.js`,
`_theme.css.j2`, `cast-requirements-render.collab.md`, `tests/ui/`). **No shared file → safe to
parallelize.** 2c regenerates `tests/golden/requirements_render/*.html`, which neither 2a nor 2b
writes directly.

**Cross-phase hard edge:** `2a → 3b` — `strip_inline_markdown` must be a pure, import-stable,
module-level public helper in `goal_card.py` because Phase 3's `maker_gate.py` imports it. Phase
2 ships ahead at the phase level, but 2a sits on Phase 3's critical path.

## Execution Order

### Parallel Group 1 (independent — run simultaneously or 2a-then-2b in one branch)
- 2a: Honest Fallback — `sp2a_honest_fallback/`
- 2b: Discoverable Commenting — `sp2b_discoverable_commenting/`

### Sequential Group 2 (after both of Group 1)
- 2c: Green Gate — `sp2c_green_gate/`

## Progress Log

<!-- User updates this after each sub-phase -->
- (not started)
