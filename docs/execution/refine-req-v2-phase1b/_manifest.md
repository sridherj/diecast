# Execution Manifest: refine-req-v2-phase1b (Refinement Brain Upgrades)

## How to Execute

The source plan is **one session of internal edits** to a single agent prompt. It is split here
into 5 sub-phases so each runs in a **separate Claude context** with a focused, verifiable scope.
For each sub-phase:

1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase1b/spN_<name>/plan.md`."
3. After completion, update the Status column below.

**All edits land in the `/home/sridherj/workspace/diecast` checkout** (the external project
checkout per goal config). sp1–sp3 mutate the same agent-prompt file, so they MUST run in order.

## Sub-Phase Overview

| # | Sub-phase | Directory | Depends On | Status | Notes |
|---|-----------|-----------|-----------|--------|-------|
| 1 | Detection Brain (verify stage+exit; add scope-mode) | `sp1_detection_brain/` | — | Not Started | Activities 1, 2, 4. Adds `scope_mode` front-matter. Prompt only. |
| 2 | Evidence-Quoting + Dated Decisions | `sp2_evidence_and_decisions/` | 1 | Not Started | Activities 6, 3. Prompt + `templates/cast-spec.template.md` + spec-checker doc note. |
| 3 | Reviewer Subagent + HARD GATE | `sp3_reviewer_and_gate/` | 2 | Not Started | Activities 8, 7. Reviewer runs BEFORE the gate (Decision #2). Prompt only. |
| 4 | Regen + Prompt-Pinning Tests | `sp4_regen_and_pins/` | 3 | Not Started | Activity 9. `bin/generate-skills`; new `tests/test_phase1b_prompt_pins.py`; keep `test_b1` green. |
| 5 | Verification Re-Refinements | `sp5_verification_refinements/` | 4 | Not Started | The plan's 8 Verification assertions over 3 real writeups (live agent runs). |

Status: Not Started → In Progress → Done → Verified → Skipped

No gate rows — the plan's Open Questions are "None blocking" and it defines no Decision Gates.

## Dependency Graph

```
sp1_detection_brain
        │  (prompt: Step 1.3 scope-mode table, Step 2.4 zero-silent-failure, scope_mode front-matter)
        ▼
sp2_evidence_and_decisions
        │  (prompt: Step 1.5/2.1 evidence quotes, ## Decisions in output template;
        │   + templates/cast-spec.template.md, + cast-spec-checker.md note)
        ▼
sp3_reviewer_and_gate
        │  (prompt: reviewer subagent rubric + HARD GATE; reviewer ordered BEFORE the gate)
        ▼
sp4_regen_and_pins
        │  (bin/generate-skills; tests/test_phase1b_prompt_pins.py; test_b1 stays green)
        ▼
sp5_verification_refinements
           (re-refine 3 writeups; assert all 8 verification items; cast-spec-checker exits 0)
```

Strictly sequential. No parallelism — sp1–sp3 edit the same prompt file; sp4 pins the anchors
sp1–sp3 created; sp5 exercises the finished prompt against real inputs.

## Execution Order

### Sequential Group 1
1. **sp1_detection_brain** — `agents/cast-refine-requirements/cast-refine-requirements.md`
   (Step 1.3 verify + scope-mode table; Step 2.1 mode statement; Step 2.4 zero-silent-failure;
   `scope_mode` front-matter).

### Sequential Group 2 (after 1)
2. **sp2_evidence_and_decisions** — agent prompt (Step 1.5/2.1 evidence-quoting; `## Decisions`
   in the Step 3.1 output template) + `templates/cast-spec.template.md` + one-line note in
   `agents/cast-spec-checker/cast-spec-checker.md`.

### Sequential Group 3 (after 2)
3. **sp3_reviewer_and_gate** — agent prompt (inline ~40-line reviewer rubric run before the
   draft presentation; HARD-GATE sentence + interactive-only / headless-auto-persist behavior).

### Sequential Group 4 (after 3)
4. **sp4_regen_and_pins** — `bin/generate-skills`; new `tests/test_phase1b_prompt_pins.py`;
   prove `tests/test_b1_domain_search.py` still passes.

### Sequential Group 5 (after 4)
5. **sp5_verification_refinements** — live re-refinements of 3 real writeups; assert the plan's 8
   verification items; `bin/cast-spec-checker` exits 0 on all outputs + one pre-existing spec.

## Prompt-Size Budget (carry across sub-phases)

Start: 434 lines. Plan estimate after the meta-pass cut: ~555 lines (additions ~90–120). **Hard
stop at ~650 lines** — if any sub-phase would push past it, trim before adding. Each sub-phase
should `wc -l` the prompt and record the new count in its Progress Log entry.

## Progress Log

<!-- Update after each sub-phase completes; note the prompt's new line count -->
