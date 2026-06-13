# sp4a_refine_wiring — Output

**Status:** ✅ Complete. All 5 success criteria met. `/cast-router` shipped (NOT cut). Refine prompt at 632 lines (≲ 650). 39 tests green (4 new wiring pins + 35 sp2/sp3 contract).

## What was done

### 1. Routing tail appended to Step 0 (`agents/cast-refine-requirements/cast-refine-requirements.md`)
Added point **9** at the tail of Phase 2's "Step 0 — Classify", after the `merge_front_matter` step. ~28 lines (slightly over the ~15 target but every line maps to a mandated success criterion; prompt stays under ceiling at 632/650). Covers all four 4a sub-steps:

- **4a.1 — Route call:** ONE `curl -s -X POST http://localhost:8005/api/goals/{slug}/route -d '{"family":"<family>"}'` through the single door. This both writes `workflow_family` to the goal AND records the routing decision — the agent **never** writes the columns directly (single-writer discipline). Includes the **D2 authority note**: `goals.workflow_family` is authoritative; front-matter `classification.family` is the document's self-description, reconciled on each refine; do NOT make front-matter authoritative.
- **4a.2 — Honest surfacing:** summary renders the `status` (e.g. `bug_fix (stub) — steps: logs → RCA → confirm → fix/test`).
- **4a.3 — Reclassification (US6 S4):** on `changed: true`, surface old `previous_family` → new `family` (with new `steps`) **inside the existing classification confirm** — no new `AskUserQuestion` slot; headless extends the Step 0 point-5 Open Questions note.
- **4a.4 — Fail-soft:** server down / non-200 → append an Open Questions line (*"…routing not recorded — re-run /cast-router or POST /route"*) and continue; classification and routing are decoupled failure domains.

### 2. `/cast-router` shipped (`agents/cast-router/`) — recorded default, NOT cut
- `config.yaml`: `dispatch_mode: subagent`, `model: haiku`, `interactive: false`, **no `allowed_delegations`** (read-only by contract).
- `cast-router.md`: thin resolve-and-show skill. Takes a goal slug → `POST /route` with **no body** (re-resolve from persisted `workflow_family`; no-op on an already-routed goal, `needs-classification` on an un-routed one) → presents the handle (family, status, steps, message) legibly; shows the self-announcing `message` verbatim on `needs-classification`/`unmatched`/404. Header documents that it sits OUTSIDE the delegation/output-json envelope contracts (subagent-mode returns text) and never originates a routing decision.

### 3. Skills regenerated + ceiling check
`bin/generate-skills` ran clean; both `~/.claude/skills/cast-router/SKILL.md` and `~/.claude/skills/cast-refine-requirements/SKILL.md` present; `cast-router` appears in the generated skills list. `wc -l` refine prompt = **632** (≲ 650).

### 4. Wiring-pin test added (`cast-server/tests/test_refine_routing_wiring.py`)
Modeled on the `test_goal_classifier_prompt.py` prompt-pin precedent. 4 pins: (a) prompt cites `/api/goals/{slug}/route`; (b) the routing call appears **after** `merge_front_matter`; (c) prompt has **no** direct DB write (`UPDATE goals|workflow_family =|sqlite`); (d) `/cast-router` ships subagent-mode with no `allowed_delegations`. This is the optional grep-pin the plan allows (a prompt-pin precedent exists); behavioral guarantees remain covered by sp3's E2E route tests.

## Verification
```
grep "/api/goals/{slug}/route" refine prompt              → line 168 (after merge_front_matter @165)
no direct DB write in prompt                              → correct
agents/cast-router/config.yaml: dispatch_mode: subagent, no allowed_delegations
bin/generate-skills                                       → cast-router + cast-refine-requirements present
wc -l refine prompt                                       → 632 (≲ 650)
uv run pytest test_refine_routing_wiring.py test_workflow_router_service.py test_api_goals_route.py
                                                          → 39 passed
```

## Success criteria
- [x] Step 0 tail POSTs to `/route` with `{"family": ...}` after classify-confirm; agent never writes columns directly.
- [x] Summary surfaces routed workflow with honest `status`; reclassification surfaces old→new (interactive) / Open Questions note (headless), no extra question slot.
- [x] Fail-soft: dead server → Open Questions note, not a refinement abort.
- [x] `/cast-router` shipped (`dispatch_mode: subagent`, read-only, no delegations) — **not cut**.
- [x] `bin/generate-skills` run; both skills present; refine prompt ≲ 650 (632).

## Notes for dependents / phase gate
- This is the last sub-phase on the critical path (sp1a → sp2 → sp3 → sp4a). The seam is now closed: the door (sp3) has its single intended v2 caller (`cast-refine-requirements`); no other phase is wired (HOLD SCOPE).
- sp4b (parallel) authors `cast-workflow-routing.collab.md` with the single-caller-in-v2 note — independent of this file.
- The refine prompt addition is ~13 lines above the ~15 ideal but well under the 650 ceiling; if a future Phase 1b/2 edit needs the headroom, the D2 authority paragraph is the most compressible part.
