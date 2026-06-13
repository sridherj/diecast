# Execution Manifest: Refine Requirements v2 — Phase 2 (Classification)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in the Diecast repo root.
2. Tell Claude: "Read `docs/execution/refine-req-v2-phase2/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase2/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Each sub-phase corresponds to a **Work Package** (A–G) from the source plan
(`docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`), preserving the plan's own
Build Order. The whole phase ships as 2–3 sessions of work (the plan's estimate).

> **⚠️ Hard prerequisite (read `_shared_context.md` → "Hard Prerequisite"):** Phase 1's
> `cast-server/cast_server/requirements_render/` package must be landed before **any** Phase 2
> sub-phase. sp1 includes a conditional 10-line follow-up to add the `EVIDENCE`/`DECISION` BlockKinds
> if Phase 1 shipped without them.

## Sub-Phase Overview

| #    | Sub-phase                                          | Directory/File                      | Source WP | Depends On            | Status      | Notes |
|------|----------------------------------------------------|-------------------------------------|-----------|-----------------------|-------------|-------|
| 1    | Taxonomy module (`families.py`) — the keystone     | `sp1_taxonomy_module/`              | A         | — (Phase 1 landed)    | Not Started | Enums, recipes, realization, profiles, pill labels, gate constants + `validate_classification`/`merge_front_matter`/`gate`/`modulate`. Build first. |
| 2a   | `cast-goal-classifier` agent (classify seam)       | `sp2a_classifier_agent/`            | B         | 1                     | Not Started | Subagent, `model: sonnet`. Parallel with 2b, 2c. Runs `bin/generate-skills`. |
| 2b   | `bin/cast-classify-gate` (code decides)            | `sp2b_gate_bin/`                    | C         | 1                     | Not Started | Thin wrapper, imports `families.py`. Parallel with 2a, 2c. |
| 2c   | Two-level family-aware checker                     | `sp2c_two_level_checker/`           | D         | 1                     | Not Started | `--family` flag; mirrors (not imports) `REQUIRED_SECTIONS_BY_FAMILY`. Parallel with 2a, 2b. Runs `bin/generate-skills`. |
| 3a   | `cast-refine-requirements` integration (sole caller)| `sp3a_refine_integration/`         | E         | 2a, 2b, 2c            | Not Started | Step 0 — Classify (~60 lines). Parallel with 3b. Critical path. |
| 3b   | Spec + template lockstep                           | `sp3b_spec_template/`               | F         | 1, 2a, 2b, 2c         | Not Started | New `cast-goal-classification.collab.md` + `## Evidence` template stub. Parallel with 3a. |
| 4    | Corpus eval + Template-Enforcer audit              | `sp4_corpus_eval/`                  | G         | 3a                    | Not Started | ≥85% top-1; zero-padding audit. **Human action:** corpus labeling + privacy call. |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision gates.** Operating mode is HOLD SCOPE — all nine plan-review decisions are resolved and
recorded in the source plan's `## Decisions` section; there is nothing to pause for.

## Dependency Graph

```
                  ┌──▶ sp2a_classifier_agent ──┐
                  │                            │
sp1_taxonomy ─────┼──▶ sp2b_gate_bin ──────────┼──▶ sp3a_refine_integration ──▶ sp4_corpus_eval
   (families.py)  │                            │            (only v2 caller)        (eval + audit)
                  └──▶ sp2c_two_level_checker ──┘
                  │                                    sp3b_spec_template
                  └────────────────────────────────▶  (parallel with sp3a)
```

**Critical path:** sp1 → {sp2a, sp2b, sp2c} → sp3a → sp4.
sp3b (spec/docs) runs parallel with sp3a once the sp1–sp2c interfaces have settled.

## Execution Order

### Sequential Group 1
1. **sp1_taxonomy_module** (WP A) — the keystone everything imports. `families.py` + its full unit
   suite. Independently verifiable: `pytest cast-server/tests/test_families.py` green proves the recipe
   invariants, gate boundaries, coercion safety, `merge_front_matter` round-trip, no-duplicate-H2, and
   the no-reclassify read path — with no agent/bin/checker work present.

### Parallel Group 2 (after sp1 — independent files, except a shared `generate-skills`)
2a. **sp2a_classifier_agent** (WP B) — `agents/cast-goal-classifier/*` + prompt pin test. Runs
    `bin/generate-skills`.
2b. **sp2b_gate_bin** (WP C) — `bin/cast-classify-gate` + golden tests. Does NOT run `generate-skills`.
2c. **sp2c_two_level_checker** (WP D) — edits `bin/cast-spec-checker` + `agents/cast-spec-checker/*` +
    fixtures/pin test. Runs `bin/generate-skills`.

> **Parallel-safety:** 2a, 2b, 2c modify disjoint source files. The only shared *action* is
> `bin/generate-skills` (2a and 2c) — it is idempotent and regenerates the full skills tree from
> `agents/`, so either order converges; re-run it if a concurrent race leaves a partial tree. See
> "Files Touched by More Than One Sub-Phase" below.

### Parallel Group 3 (after Group 2 — independent files)
3a. **sp3a_refine_integration** (WP E) — `agents/cast-refine-requirements/*`. Step 0 wiring + E2E.
    Critical path. Runs `bin/generate-skills`.
3b. **sp3b_spec_template** (WP F) — `docs/specs/cast-goal-classification.collab.md` + `_registry.md` +
    `templates/cast-spec.template.md`. Documentation lockstep; no code change.

### Sequential Group 4 (after sp3a)
4. **sp4_corpus_eval** (WP G) — corpus assembly, `tests/eval_classifier_corpus.py`, zero-padding audit.
   Terminal sub-phase; carries the one genuine human-in-the-loop dependency.

## Files Touched by More Than One Sub-Phase

| File / Action | Sub-phases | Conflict resolution |
|---|---|---|
| `bin/generate-skills` (action, not a file) | sp2a, sp2c, sp3a | Idempotent; regenerates the whole skills tree from `agents/`. Each sub-phase runs it and commits its generated output; re-run if a partial tree appears. No source-file overlap. |
| `templates/cast-spec.template.md` | sp3b **(this plan)** + **Phase 1b** (`## Decisions` edit, different phase) | Whichever lands second rebases over the other's section — do not clobber. Within *this* plan only sp3b touches it. |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | sp3a **(this plan)** + **Phase 1b** (different phase) | sp3a rebases Step 0 around Phase 1b's edits; never duplicates 1b's `## Decisions`/scope-mode content; only sequences the shared question budget. Within *this* plan only sp3a touches it. |

All other files are written by exactly one sub-phase. The parallel groups (2a/2b/2c and 3a/3b) modify
disjoint source files — verified during analysis.

## Cross-Phase Interface Contract (Phases 3a/3b adopt verbatim)

sp1 sets the names the rest of Refine-Requirements-v2 consumes — do not rename after sp2a starts:
- `WorkFamily` (9 values), `RecipeBlock` (6 values), `FAMILY_RECIPES`, `RECIPE_REALIZATION`,
  `REQUIRED_SECTIONS_BY_FAMILY`, `FAMILY_PILL_LABELS`, `GATE_SILENT`/`GATE_CONFIRM`.
- Front-matter key `classification.family` is the ONE field the Phase 3b router reads.
- Persist once (`merge_front_matter`), consume twice (Phase 3a pill, Phase 3b routing) — never re-classify.

## Progress Log

_(Update after each sub-phase: date, sub-phase, status, commit, notes.)_

- _Not started._
