<!-- AUTO-GENERATED: Read-only render of DB state. Do not edit directly. -->
<!-- Changes: use /cast-tasks agent or task_service API. -->
# Tasks — Refine Requirements Better Rendering V3

## Requirements
- [ ] **Finish brainstorming/initial requirements**
      Tip: Dump everything, messy is fine
- [ ] **Refine requirements writeup** [agent: cast-refine-requirements]
      Tip: AI-assisted refinement of your initial requirements

## Exploration
- [ ] **Run starter exploration** [agent: cast-explore]
      Tip: Deep 7-angle research on the goal
- [ ] **Go through starter research output**
      Tip: Leverage research, form your POV
- [ ] **Add research notes**
      Tip: Dump notes from starter research + own research

## Plan
- [-] **Finalize high level phasing plan** [agent: cast-high-level-planner]
      Tip: City map — directionally right, progressively detailed
      Artifacts: ../../docs/goal/refine-requirements-better-rendering-v3/plan.collab.md
- [ ] **Create detailed execution plan** [agent: cast-detailed-plan]
      Tip: Spec-aware planning with inline design review

## Execution
- [-] **Orchestrate detailed plan execution and execution using the correct agents.** [agent: cast-orchestrate]
      Artifacts: ../../docs/execution/refine-req-v3-phase1/_manifest.md, ../../docs/goal/refine-requirements-better-rendering-v3/spikes/PHASE1-GATE.md, ../../docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md, ../../docs/goal/refine-requirements-better-rendering-v3/spikes/1b/spike-results.md, ../../docs/execution/refine-req-v3-phase1/
- [ ] **Harden cast-requirements-how for verbatim carriage of lead units**: The bug_fix family (and others) renders through the real maker with check_html green — no lead-unit paraphrase — so the structural-violation override fires only on genuine edge cases, not predictably. → Strengthen agents/cast-requirements-how/cast-requirements-how.md to REQUIRE verbatim carriage of each requirement unit lead/anchorable source text (esp. the first FR/SC per family); re-run tests/eval_maker_pipeline_e2e.py to confirm bug_fix passes check_html. [agent: cast-requirements-how]
      Tip: Reproducible: the production cast-requirements-how maker paraphrased bug_fix lead FR-001/SC-001 in 2/2 real runs, tripping verbatim-carriage gate FR-034. Non-blocking — the structural-violation override absorbs it safely until fixed. Surfaced in sub-phase 3e.
      Artifacts: docs/execution/refine-req-v3-phase3/sp3e_spec_e2e_gate/evidence/SWEEP-RECORD.md
      Type: refactor | Est: S | Energy: medium
      Assigned: ai
