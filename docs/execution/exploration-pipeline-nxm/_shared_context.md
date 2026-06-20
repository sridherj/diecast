# Shared Context: Exploration Pipeline — N×M Workflow + 90/10 Hat + Diecast HTML Surface

**Goal:** `exploration-pipeline-nxm-claude-workflow-9010-angle` · **Family:** new_initiative
**Branch:** `feat/exploration-nxm-workflow` · **Repo:** /data/workspace/diecast

## Authoritative documents (read before executing any sub-phase)
- Spec: `goals/exploration-pipeline-nxm-claude-workflow-9010-angle/refined_requirements.collab.md`
- High-level plan: `goals/exploration-pipeline-nxm-claude-workflow-9010-angle/plan.collab.md`
- Decisions ledger (cross-sub-phase interfaces/naming): `docs/plan/exploration-pipeline-nxm-decisions-so-far.md`
- Reconciliation (verdict COHESIVE): `docs/plan/2026-06-20-exploration-pipeline-nxm-reconciliation.md`
- Each sub-phase's detailed plan: `docs/plan/2026-06-20-exploration-pipeline-nxm-<sfx>.md` — INCLUDING its
  binding `## Plan Review Decisions (2026-06-20)` section.

## Non-negotiable principles (do not dilute)
- Exploration angles are GENERATIVE "thinking hats" (idea-surfacing), NEVER review/score/gate lenses.
- gstack contributes TECHNIQUES only (specificity ladder, anti-sycophancy phrasing, [EUREKA]); never its
  "boil-the-ocean"/review principles.
- md artifacts stay the machine substrate (cast-high-level-planner consumes them); HTML is additive
  visualization. Per-step synthesis is UNCHANGED. Workflow ships PARALLEL to cast-explore (no migration).

## Pinned cross-sub-phase contracts (from the ledger)
- Single-hat agent: `cast-hat-researcher`, `(step, hat_id, goal_context) → one note` at
  `exploration/research/{NN}-{step-slug}-{hat-id}.ai.md`. always-on hats: `contrarian, first-principles, 90-10`.
- Workflow: `agents/cast-explore-workflow/workflow.py`; arg `hat-matrix = {goal_slug, goal_context, steps:[{nn,slug,name,hats:[hat_id…]}]}`.
- Dual viewer: artifact-dict `kind` discriminator; `<iframe srcdoc sandbox="allow-scripts allow-popups">` (no allow-same-origin).
- Commenting: postMessage-to-host bridge; new `artifact_ref` field on the same-door comment path; `anchor_space='render'`; verbatim-substring relocation.
- Render: parallel `cast_server/services/exploration_render_service.py` + `render_common/` shared core (decision #2A: stage-loop + decide_quality + verdict base extracted there); agents `cast-exploration-{what,how,render-checker}`; output `goals/{slug}/exploration/exploration.html`.

## Verification bar
- `bin/cast-spec-checker` clean on any spec change; pytest green; `/cast-update-spec` on `cast-requirements-render` (sp2b).
- The plan-review decisions (DRY dedup, jsdom bridge test, adversarial srcdoc fixture, degraded-step test, cost-at-gate, glob∩hat_id) are binding.

## G1 spike outcomes (binding — read before Group 3)
- **1a VIABLE (Option A):** entrypoint = a MAIN-AGENT skill/command that authors+launches the engine
  via the Workflow tool. **CORRECTION: the engine is a JavaScript Workflow script, NOT `workflow.py`.**
  `agent()/parallel()/pipeline()` are the script API; cells call `cast-hat-researcher`; synthesis is the
  script's final stage. Concurrency `min(16,cores−2)`. See `exploration/spike-1a-result.md`.
- **1b VIABLE:** in-viewer commenting via `<iframe srcdoc sandbox="allow-scripts">` + postMessage bridge;
  guard on SOURCE IDENTITY (origin is "null"); reply `targetOrigin="*"`. See `exploration/spike-1b-result.md`.
