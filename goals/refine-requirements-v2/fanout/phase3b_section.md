## Phase 3b: Routing — Phase-Agnostic Workflow Router (parallel with Phase 3a)
**Outcome:** A classified goal resolves to a family-specific downstream-workflow **handle** (a named
**stub** for unbuilt pipelines), the decision is recorded on the goal, and the resolver is invokable
from **any phase** without re-running refinement. v2 ships the seam + stubs, not the pipelines.
**Dependencies:** Phase 2 (classification produces the family the resolver consumes).
**Estimated effort:** 1-2 sessions
**Verification:** Seed 5 goals (one per family) → `resolve` returns the correct handle/stub and
persists `workflow_family`/`routing_handle` (SC-005). Flip a goal's `phase`, call `resolve` again →
**byte-identical** handle, **no** re-classification. Assert no unimplemented family ever resolves to
`STARTER_TASKS` or a generic bucket (0 silent fallbacks; every stub names its steps).

Key activities:
- **Add the family registry to `config.py`** beside `STARTER_TASKS`: a closed `WORKFLOW_FAMILIES` set
  and a **total** `WORKFLOW_REGISTRY` map, every value `status="stub"` with enumerated `steps`
  (bug-fix: `logs→RCA→confirm→fix/test`; etc.). Flipping a family to `"implemented"` later is a
  registry-only diff — no seam change (FR-015).
- **Build the pure resolver `workflow_router_service.py`** modeled on `orchestration_service.py` (no
  LLM, no subprocess, `db_path=` injectable, CLI hook). `resolve(family)` is **total** — defined for
  every family + `None` (→ `needs-classification`) + unknown (→ `unmatched`, a Special Case that
  *announces itself*, never a silent Null Object). The resolver **never re-classifies** — it is a pure
  consumer of the persisted family (this is how FR-016 phase-agnosticism is preserved, not built).
- **Add recording columns to `goals`** (`workflow_family`, `routing_handle`, `routed_at`) via the
  `ALTER TABLE … ADD COLUMN` migration pattern; thread through `GoalUpdate`; they auto-render to
  `goal.yaml` for free. **Not** `tags` (flat, collides).
- **Write `record_routing_decision(slug, family, handle)`** — the only part that writes; idempotent
  (re-recording the same family is a no-op). Keep it separate from the pure `resolve`.
- **Expose `POST /api/goals/{slug}/route`** — the phase-agnostic surface a future planning/execution
  agent hits to re-resolve from persisted state (FR-016).
- **Have `cast-refine-requirements` call the `cast-goal-classifier` agent** (built in Phase 2), then
  write `workflow_family` to the goal and call `record_routing_decision`. Refinement is the **only** v2
  caller of the classifier and the router — do not wire other phases. Handle reclassification updates
  surfacing the changed downstream workflow (US6 Scenario 4). Optionally ship a `/cast-router` skill.
  Net seam: **classifier agent + resolver service, both phase-agnostic, both single-caller in v2.**

