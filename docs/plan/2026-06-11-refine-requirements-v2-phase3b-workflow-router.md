# Refine Requirements v2: Phase 3b — Routing: Phase-Agnostic Workflow Router

## Overview

A classified goal resolves to a family-specific downstream-workflow **handle** — a named **stub**
for every not-yet-built pipeline — the decision is recorded on the goal (DB columns that
auto-render to `goal.yaml`), and the resolver is invokable from **any phase** without re-running
refinement. The key insight from exploration (Playbook 06): **phase-agnosticism (FR-016) is not a
feature you build — it is a property you fail to destroy.** The resolver is a pure, total function
of the *persisted* family; it never re-classifies, so any caller in any phase gets the same answer
for free. v2 ships the seam + stubs, not the pipelines (FR-015).

This plan covers ONLY Phase 3b of the high-level plan (`goals/refine-requirements-v2/plan.collab.md`),
runs parallel with Phase 3a, and adopts all locked names from
`docs/plan/refine-requirements-v2-decisions-so-far.md` and the Phase 2 Naming Contract.

## Operating Mode

**HOLD SCOPE** — the build boundary is explicit and repeated: "v2 ships the seam + stubs, not the
pipelines", "Refinement is the **only** v2 caller of the classifier and the router — do not wire
other phases", "ship the door, not the future callers". No expansion (no rules engine, no
`goal_routing` history table, no UI routing panel — see Out of Scope below), no reduction (all six
delegated activity clusters are required).

## Position in Overall Plan

```
Phase 1: Parser & Thin Spine ──► Phase 2: Classification ──┬──► Phase 3a: HTML Render (SC-001)
                                  (WorkFamily, classifier,  └──► Phase 3b: Router (THIS PLAN, SC-005)
                                   classification.family)              │
                                                                       ▼
                                                            Phase 4: Annotation & Versioning
```

Phase 3b is **off the critical path** (Phase 4 depends on 3a, not 3b) and depends only on Phase 2
(the classifier produces the `WorkFamily` the resolver consumes). It can start the moment Phase 2's
Work Packages A (taxonomy) and B (classifier agent) land — it does not need Phase 2's checker or
corpus-eval work.

## Depends On (from prior plans)

| Prior deliverable | Where | How Phase 3b consumes it |
|---|---|---|
| `WorkFamily(str, Enum)` — 9 LOCKED values (`new_initiative, pilot_poc, bug_fix, data_analysis, random_idea, testing_qa, refactor_migration, personal_non_eng, generic`) | Phase 2 WP-A, `cast-server/cast_server/requirements_render/families.py` | `WORKFLOW_REGISTRY` keys are exactly these string values (one vocabulary, two homes); a pin test enforces key-set equality |
| `classification.family` front-matter contract | Phase 2 Naming Contract | The value `cast-refine-requirements` passes to `POST /api/goals/{slug}/route` at classify time; the goal column is the routing-side record of it |
| `cast-goal-classifier` agent (subagent dispatch, validated output, gate in code) | Phase 2 WP-B/C | Refinement's Step 0 produces the confirmed family; Phase 3b's WP-E wiring runs immediately after it |
| Phase 2 WP-E "Step 0 — Classify" in `cast-refine-requirements.md` (+ headless policy, question budget) | Phase 2 WP-E | WP-E here appends the routing call to that step; reuses its headless `fallback` policy verbatim |
| Service DB pattern: flat functions, `db_path: Path \| None = None` injectable, `get_connection(db_path)` | Phase 1 decision (canon = `goal_service.py` / `task_service.py`, **NOT** `orchestration_service.py`'s file-based pattern — owner Decision Opt A) | `workflow_router_service.py` uses this pattern for its one write path |
| `orchestration_service.py` STRUCTURE precedent: pure logic, no LLM/subprocess/tmux, dataclasses, `if __name__ == "__main__"` CLI hook | existing `cast_server/services/orchestration_service.py` | `workflow_router_service.py` mirrors the module shape (docstring contract, dataclass result, CLI hook) — structure only, not its file/manifest persistence |
| `ALTER TABLE … ADD COLUMN` try/except migration pattern + canonical `cast-server/cast_server/db/schema.sql` (root `db/schema.sql` is legacy — do NOT edit) | Phase 1 decision; existing `db/connection.py:100-104` (`gstack_dir` precedent) | WP-C adds the three goal columns in both places |
| `_update_goal_yaml_fields()` merge + `_write_goal_yaml()` full render | existing `goal_service.py` | Recording auto-renders to `goal.yaml`; `_write_goal_yaml` gains conditional includes like `gstack_dir` |
| `taxonomy_version` front-matter field | Phase 2 Naming Contract | Recorded alongside the routing decision so a future family-set bump is detectable |

## Interfaces This Phase Sets (Phases 4/5 and future pipeline goals MUST adopt)

```python
# cast_server/services/workflow_router_service.py
@dataclass(frozen=True)
class WorkflowHandle:
    family: str | None
    status: str                    # "implemented" | "stub" | "unmatched" | "needs-classification"
    steps: tuple[str, ...] = ()
    pipeline_ref: str | None = None   # future: agent/orchestration target when a family graduates
    message: str = ""

def resolve(family: str | None) -> WorkflowHandle: ...        # PURE + TOTAL, no DB, no LLM
def record_routing_decision(slug: str, family: str, handle: WorkflowHandle,
                            goals_dir: Path | None = None,
                            db_path: Path | None = None) -> dict: ...   # the ONLY writer; idempotent
```

- **Stored handle format:** `goals.routing_handle = f"{family}:{status}"` (e.g. `bug_fix:stub`).
  Carries stub-ness into `goal.yaml` for human visibility; stays byte-identical across phase flips
  (registry unchanged ⇒ handle unchanged, SC-005); a family graduating to `implemented` produces a
  *visibly different* handle on the next re-route — which is exactly the US6 S4 surfacing trigger.
  **The stored handle is a point-in-time STAMP, not derived-on-read (plan-review Decision #1):** it can
  lag the registry — when a family graduates `stub→implemented`, every already-routed goal keeps its
  old `{family}:stub` handle in the DB row and `goal.yaml` until that goal is re-routed (re-route IS
  the refresh mechanism). This staleness is an accepted, documented contract (spec'd in WP-F), not a
  bug; deriving the handle live was rejected to preserve the SC-005 byte-stability test and the
  human-visible `goal.yaml` stamp.
- **HTTP surface:** `POST /api/goals/{slug}/route` (JSON in/out — see WP-D contract).
- **Recording rule:** only valid `WorkFamily` values are ever persisted. `unmatched` and
  `needs-classification` handles are *returned and announced*, never recorded (no garbage in
  `goal.yaml`; the Special Case announces itself instead of leaving a residue).

## Sub-phase: Routing — Phase-Agnostic Workflow Router

**Outcome:** A classified goal resolves to a family-specific downstream-workflow handle (named stub
for unbuilt pipelines); the decision is recorded as `workflow_family`/`routing_handle`/`routed_at`
on the goal and visible in `goal.yaml`; `POST /api/goals/{slug}/route` re-resolves from persisted
state from any phase with no re-classification; `cast-refine-requirements` is the only v2 caller
and surfaces a changed downstream workflow on reclassification (US6 S4).

**Dependencies:** Phase 2 WP-A (`WorkFamily`) + WP-B/E (classifier + Step 0 in the refine prompt).

**Estimated effort:** 1-2 sessions (A+B ≈ ½ session, C+D ≈ ½-1, E+F ≈ ½-1).

**Verification (phase gate — SC-005):**
- `pytest` green on `cast-server/tests/test_workflow_router_service.py` and
  `test_api_goals_route.py` (enumerated per work package below). Headline assertions:
  - **Totality:** `resolve` returns a real `WorkflowHandle` for all 9 families + `None` +
    an unknown string — 0 exceptions, 0 `None` returns; the three edge handles carry the right
    `status` and a non-empty `message`.
  - **Stub discipline (FR-015):** every registry value has `status="stub"` and non-empty `steps`;
    a pin test asserts the `workflow_router_service` module source contains no reference to
    `STARTER_TASKS` (the silent generic fallback is structurally unreachable).
  - **Pin test:** `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}` — registry/enum drift
    fails CI (the Phase 2 Decision #5 mirror-discipline precedent).
  - **Idempotency:** recording the same family twice → second call is a no-op (`routed_at`
    unchanged, `recorded: false`); recording a different family → updated row + `changed: true` +
    `previous_family`.
- **End-to-end (SC-005 trace):** seed 5 goals (one per family: `bug_fix`, `new_initiative`,
  `data_analysis`, `random_idea`, `testing_qa`) → `POST /route` with each family → assert correct
  handle returned AND `workflow_family`/`routing_handle` present in both the DB row and the
  rendered `goal.yaml`. Then flip one goal's `phase` via the existing phase endpoint →
  `POST /route` with no body → **byte-identical** handle JSON, no classifier invocation anywhere
  in the path (the route handler imports no agent/LLM machinery — asserted by an automated
  **no-reclassify source-pin test** (WP-B), NOT by manual code inspection; plan-review Decision #4).
- `bin/cast-spec-checker` stays green on this plan's new spec file (WP-F).

### Work Package A — Family registry in `config.py`

The registry IS the router. Build first; everything else reads it.

- Add to `cast-server/cast_server/config.py`, directly beside `STARTER_TASKS` (it reads as the
  family-keyed generalization of the phase-keyed tables already there):

  ```python
  # Workflow routing registry (Phase 3b). Keys are WorkFamily string values —
  # one vocabulary, two homes; kept as strings so config.py stays the
  # dependency-free bottom layer (no requirements_render import). A pin test
  # asserts key-set equality with families.WorkFamily.
  WORKFLOW_REGISTRY: dict[str, dict] = {
      "new_initiative":     {"status": "stub", "steps": ["PRD", "architecture", "phased plan", "execute"]},
      "pilot_poc":          {"status": "stub", "steps": ["one-screen WHAT", "spike", "demo", "learnings"]},
      "bug_fix":            {"status": "stub", "steps": ["logs", "RCA", "confirm", "fix/test"]},
      "data_analysis":      {"status": "stub", "steps": ["question", "sources", "analysis", "writeup"]},
      "random_idea":        {"status": "stub", "steps": ["capture", "incubate", "promote-or-archive"]},
      "testing_qa":         {"status": "stub", "steps": ["inventory", "coverage gaps", "test plan", "implement"]},
      "refactor_migration": {"status": "stub", "steps": ["map current", "target design", "migration steps", "verify parity"]},
      "personal_non_eng":   {"status": "stub", "steps": ["clarify outcome", "plan", "do", "reflect"]},
      "generic":            {"status": "stub", "steps": ["refine", "explore", "plan", "execute"]},
  }
  WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)   # the closed set, derived — cannot drift from the map
  ```

- Every value `status="stub"` in v2. Flipping a family to `"implemented"` later (and populating
  `pipeline_ref`) is a **registry-only diff** — no seam change (FR-015). Step wordings are
  owner-editable copy, not contracts; only `bug_fix`'s steps are spec-mandated
  (`logs→RCA→confirm→fix/test`).
- `generic` gets a *named* stub like every other family — it is a model-selected family
  (Phase 2 Decision #2: `GENERIC` is never a coercion target), so routing it to a named
  refine→explore→plan→execute stub is an announced decision, not a silent fallback. The
  *forbidden* fallback is an unknown/unclassified case quietly resolving to anything.
- Tests (in WP-B's test module): pin test (key set == `WorkFamily` values — this is the ONE place
  Phase 3b imports `families.py`, in tests only); every entry has non-empty `steps` and
  `status ∈ {"stub", "implemented"}`.
- → Apply `/cast-python-best-practices` while writing; review output for compliance.

### Work Package B — Pure resolver `workflow_router_service.py`

- Create `cast-server/cast_server/services/workflow_router_service.py`. Module docstring states
  the contract up front, mirroring `orchestration_service.py`'s: *"Workflow router — pure
  resolution logic + one idempotent recorder. No LLM, no subprocess, no re-classification."*
- `WorkflowHandle` frozen dataclass per the Interfaces section. `steps` is a tuple (immutability
  matches frozen).
- `resolve(family: str | None) -> WorkflowHandle` — **TOTAL**, ~5 lines of branching:
  - `None` → `WorkflowHandle(None, "needs-classification", message="Goal not yet classified — run /cast-refine-requirements first; the router never guesses.")`
  - unknown string → `WorkflowHandle(family, "unmatched", message=f"No pipeline registered for '{family}' — registry knows: {sorted(WORKFLOW_FAMILIES)}.")`
    — a Special Case that *announces itself*, never a silent Null Object.
  - hit → `WorkflowHandle(family, entry["status"], steps=tuple(entry["steps"]), message=...)`.
  - The resolver **never re-classifies** — it is a pure consumer of the persisted family. No DB
    access in `resolve` at all (it takes the family as an argument); this is how FR-016 is
    *preserved*, not built.
- `record_routing_decision(slug, family, handle, goals_dir=None, db_path=None) -> dict` — the
  ONLY writer, using the **goal_service DB pattern** (flat function, `get_connection(db_path)`,
  try/finally close — NOT orchestration_service's file-based persistence):
  - Guard: `family in WORKFLOW_FAMILIES` and `handle.status in ("stub", "implemented")` — else
    raise `ValueError` (callers must never persist `unmatched`/`needs-classification`).
  - Read current row; if `workflow_family == family and routing_handle == f"{family}:{handle.status}"`
    → **no-op** (return `{"recorded": False, "changed": False, ...}`; `routed_at` untouched).
  - Else `UPDATE goals SET workflow_family=?, routing_handle=?, routed_at=?` (ISO-8601 UTC) and
    mirror to `goal.yaml` via `goal_service._update_goal_yaml_fields(_resolve_goal_dir(...), ...)`
    — the same resolve-dir path `update_status` uses, so externally-routed goals render correctly.
    The recorder's docstring states the `goal.yaml` mirror is **best-effort** (a missing file is
    logged, not raised — the DB row is authoritative; plan-review Decision #5).
  - Return `{"recorded": True, "changed": <prior family differed>, "previous_family": ...}` — the
    data WP-D/WP-E use to surface US6 S4.
- CLI hook (`if __name__ == "__main__"`), mirroring orchestration_service's: 
  `python -m cast_server.services.workflow_router_service resolve <family>` → handle JSON;
  `... route <slug> [family]` → resolve-from-DB (+record when family given). Useful for tests and
  for a server-down escape hatch; agents use the HTTP door.
- Tests `cast-server/tests/test_workflow_router_service.py`: table-driven totality (9+2 cases);
  edge-handle messages non-empty; `resolve` purity (no `db_path` parameter exists on it — API
  shape is the test); record idempotency / change-path / ValueError guards; `goal.yaml` round-trip
  (tmp goals dir fixture, precedent: `test_goal_service_ext_routing.py`); the no-`STARTER_TASKS`
  source pin. **No-reclassify source pin (plan-review Decision #4):** a test asserting the
  `workflow_router_service` module **and the `/route` handler module** source contain no
  agent-dispatch/subprocess/classifier imports (no `subprocess`, no Agent/`/trigger` dispatch, no
  `cast_goal_classifier`, no LLM client) — same mechanism as the no-`STARTER_TASKS` pin, applied to
  the plan's #1 named risk; this REPLACES the SC-005 "assert by code inspection" step (Phase 2
  Decision #6 precedent: load-bearing invariants live in CI, not manual grep).
  **Missing-`goal.yaml` recording test (plan-review Decision #5):** record against a goal whose
  `goal.yaml` is absent → the DB row IS written and the call does NOT raise (pins the yaml mirror as
  best-effort, matching `update_status`/`_update_goal_yaml_fields`, which logs-and-returns on a
  missing file). → Apply `/cast-pytest-best-practices`; review output.

### Work Package C — Recording columns on `goals` + model threading

- **Canonical schema** `cast-server/cast_server/db/schema.sql` (NOT the legacy root
  `db/schema.sql`): add `workflow_family TEXT`, `routing_handle TEXT`, `routed_at TEXT` to
  `CREATE TABLE goals`.
- **Migration mirror** in `db/connection.py::_run_migrations()` — the exact `gstack_dir`
  precedent (`connection.py:100-104`):

  ```python
  for col in ["workflow_family", "routing_handle", "routed_at"]:
      try:
          conn.execute(f"ALTER TABLE goals ADD COLUMN {col} TEXT")
      except sqlite3.OperationalError:
          pass  # column already exists
  ```

- **Models** (`models/goal.py`): add the three optional fields to `Goal`; add
  `workflow_family: str | None = None` and `routing_handle: str | None = None` to `GoalUpdate`
  (`routed_at` is server-set, never client-supplied). Note: `GoalUpdate` currently has no
  consumers in the codebase — threading is additive contract-completeness; the actual write path
  is `record_routing_decision` (single-writer discipline).
- **`goal.yaml` render:** `_update_goal_yaml_fields` already merges arbitrary keys (recording
  works day one); also add conditional includes to `_write_goal_yaml` (like `gstack_dir`) so a
  full re-render of a routed goal preserves the three fields.
- **NOT `tags`** (flat, unstructured, collides with real tags — rejected per playbook + plan).
- **Deferred (HOLD SCOPE):** a `goal_routing` history table. US6 S4 needs only
  current-vs-previous, which the `record_routing_decision` return value carries transiently and
  the version-controlled `goal.yaml` diff preserves durably enough for v2.
- Tests: fresh-DB `init_db` exposes the columns; legacy-DB (pre-column file fixture) migration
  adds them idempotently (run `_run_migrations` twice).

### Work Package D — `POST /api/goals/{slug}/route` (the phase-agnostic surface)

- Add to `routes/api_goals.py` (keeps the `/api/goals` prefix + service-call style; returns
  **JSON**, not an HTMX fragment — this is an agent-facing API like `api_agents.py`, and no UI
  consumes it in v2):
  - **Request:** optional JSON body `{"family": "<WorkFamily value>"}`.
    - *With* `family` (the refinement path, right after classification): resolve + record.
    - *Without* body (the FR-016 path — any future phase/agent): read `goal["workflow_family"]`
      from the DB, resolve, and re-record idempotently (a no-op when nothing changed — `routed_at`
      is NOT touched, keeping the handle byte-stable for SC-005).
  - **Response 200:** the handle + recording metadata:
    `{"family", "status", "steps", "pipeline_ref", "message", "recorded", "changed",
    "previous_family", "routing_handle", "routed_at"}`.
  - **404** unknown slug. **Unknown family string in body** → 200 with the `unmatched` handle and
    `recorded: false` (totality means the API never 500s on content; the Special Case announces
    itself in-band). **`None` persisted + no body** → 200 with `needs-classification`,
    `recorded: false`.
- The handler calls only `goal_service.get_goal` + `workflow_router_service.resolve` /
  `record_routing_decision` — no agent dispatch, no LLM, nothing that could re-classify
  (FR-016/SC-005 by construction).
- Tests `cast-server/tests/test_api_goals_route.py` (FastAPI TestClient precedent:
  `test_api_agents.py`): the 5-family seed trace; phase-flip → byte-identical response body
  (SC-005); 404; unmatched-not-recorded; needs-classification path; idempotent re-POST.

### Work Package E — Wire the single v2 caller (`cast-refine-requirements`) + optional `/cast-router` skill

All prompt edits to `agents/cast-refine-requirements/cast-refine-requirements.md` — coordinate
with Phase 2's WP-E (this lands as the tail of its "Step 0 — Classify"; keep the addition ~15
lines, respecting the ~650-line ceiling shared with Phases 1b/2).

- **After classification is confirmed** (auto/confirm/choose path resolved, front-matter merged
  via `merge_front_matter`): call
  `curl -s -X POST http://localhost:8005/api/goals/{slug}/route -H 'Content-Type: application/json' -d '{"family": "<family>"}'`
  — one call performs "write `workflow_family` to the goal" AND "call `record_routing_decision`"
  through the single door. The agent never writes the goal columns directly (single-writer:
  the service owns the write; the agent owns the trigger). **Authority (plan-review Decision #2):**
  `goals.workflow_family` is the authoritative routing record; the front-matter `classification.family`
  written in the same Step 0 is the document's self-description, reconciled to the column on each
  refine — a hand-edited front-matter family takes effect only by re-running refinement, which
  re-routes and overwrites the column (see Design Review → dual persistence).
- **Surface the routed workflow** in the refinement summary: "Routed downstream workflow:
  `bug_fix` (stub) — steps: logs → RCA → confirm → fix/test" (render `status` honestly — the user
  should see it's a stub).
- **Reclassification (US6 S4):** on a re-run where the classifier returns a different family, the
  route response carries `changed: true` + `previous_family`. Interactive → tell the user the
  downstream workflow changed (old → new, with the new steps) as part of the classification
  confirm flow; headless → append the Phase 2 WP-E Open Questions note, extended with the routing
  change. No extra `AskUserQuestion` slot — the surfacing rides the existing classification
  confirm (question-budget contract with Phases 1b/2 holds).
- **Fail-soft:** route call fails (server down, non-200) → refinement does NOT die; append an
  Open Questions line ("classification recorded in front-matter; routing not recorded — re-run
  `/cast-router` or POST /route") and continue. Classification (front-matter) and routing (goal
  columns) are deliberately decoupled failure domains.
- **Do NOT wire any other phase.** The endpoint is the door; planners/executors get wired in
  later per-family pipeline goals.
- **Optional — ship `/cast-router`** (included; near-zero cost and completes the FR-013 surface):
  a thin skill+agent (`agents/cast-router/`) whose entire job is "resolve and show the routed
  workflow for a goal slug" via `POST /route` (no body), for humans and future agents alike.
  `dispatch_mode: subagent`, read-only, no `allowed_delegations`. If session budget runs short,
  this is the one cuttable item — flag in the run summary rather than silently skipping.
- Re-run `bin/generate-skills` after agent edits; verify the refine prompt stays under the
  ~650-line ceiling.
- Review output: confirm the refine prompt's routing addition cites the endpoint, not direct DB
  access.

### Work Package F — Spec lockstep

- → Delegate: `/cast-update-spec` (create mode) — author `docs/specs/cast-workflow-routing.collab.md`
  documenting the new user-facing contracts: the three `goals` columns (+ `goal.yaml` render), the
  `routing_handle` format (`{family}:{status}`), the `WorkflowHandle` JSON shape + status set, the
  `POST /api/goals/{slug}/route` request/response contract (including the recording rule:
  `unmatched`/`needs-classification` never persist), and `WORKFLOW_REGISTRY` semantics,
  and the single-caller-in-v2 note. Register in `docs/specs/_registry.md`. Cross-reference
  `cast-goal-classification.collab.md` (Phase 2 WP-F) for the family vocabulary — routing cites,
  never redefines it. **Single canonical add-a-family checklist (plan-review Decision #3):** do NOT
  restate a separate add-a-family list in this spec; instead append the routing homes (the
  `WORKFLOW_REGISTRY` entry) and the graduate-a-family steps (flip `status`, set `pipeline_ref` —
  registry-only diff, FR-015) as a labeled *extension* of the Phase 2
  `cast-goal-classification.collab.md` add-a-family checklist, so a maintainer follows ONE list
  end-to-end (the registry/enum key-set pin test remains the CI backstop against a forgotten entry).
  Review output: names must match `config.py`/`workflow_router_service.py` exactly.

**Design review:**
- **Spec consistency:** no loaded spec conflicts. `cast-delegation-contract.collab.md` is
  untouched — `/route` is a plain JSON API, not agent dispatch; no output-envelope semantics
  apply. New user-facing behavior (columns, endpoint, registry) gets its own spec via
  `/cast-update-spec` in WP-F (this is the high-level plan's own Spec References instruction for
  Phase 3b). ✓
- **Naming:** `workflow_family` stores `WorkFamily` string values exactly (one vocabulary, two
  homes — pin-tested); snake_case columns mirror `gstack_dir`/`external_project_dir`; the
  endpoint follows the `/api/goals/{slug}/<verb>` precedent (`/status`, `/phase`). `routing_handle`
  format `{family}:{status}` is new — defined once in the Interfaces section and spec'd in WP-F. ✓
- **Architecture:** resolver = pure service mirroring `orchestration_service.py`'s *structure*
  while using the `goal_service` *DB pattern* — the decisions-so-far file explicitly demotes
  orchestration_service as DB canon (owner Decision Opt A), and this plan threads that needle
  deliberately: structure from one precedent, persistence from the other. Registry in `config.py`
  stays string-keyed so config remains the import-free bottom layer; enum coupling lives in one
  pin test. Single-writer: `record_routing_decision` is the only goal-column writer; the agent
  triggers via HTTP, never writes directly. ⚠️ One deliberate dual-persistence:
  `classification.family` (front-matter, document-side) and `goals.workflow_family` (DB,
  routing-side) are written in the same Step 0 breath by the same agent; the router reads ONLY the
  column. Divergence is possible if a human hand-edits front-matter without re-refining —
  accepted for v2 (the column is the recorded *decision*, front-matter is the document's
  *self-description*); noted in the WP-F spec. **Authority made explicit (plan-review Decision #2):**
  `goals.workflow_family` is the authoritative routing record and the single writer-of-record;
  front-matter `classification.family` is reconciled to the column on the next refine (Step 0 always
  re-writes both), so the two stores are never co-equal — a future maintainer must not "fix" the
  divergence by making the front-matter authoritative (that would re-introduce a parser read into the
  FR-016 pure-DB routing path).
- **Error & rescue:** `resolve` is total — there is no undefined input, so there is nothing for a
  caller to silently default on (FR-015 as a structural property). Absent family →
  `needs-classification` (never guess); unknown → self-announcing `unmatched`; neither persists.
  Refinement survives a dead server (fail-soft + Open Questions note). Idempotent recording makes
  re-invocation from any phase safe by default. Zero silent failures in the routing decision itself:
  every degraded *resolution* path returns a message and `recorded: false`. The one best-effort path
  is the `goal.yaml` mirror — a missing file is logged, not raised (DB is authoritative); this is
  pinned by a test and stated in the recorder docstring (plan-review Decision #5), not left implicit.
- **Security:** `slug` is path data into a parameterized query (house pattern); family body value
  is whitelist-checked against `WORKFLOW_FAMILIES` before any write; file I/O is confined to the
  existing `_update_goal_yaml_fields`/`_resolve_goal_dir` helpers (no new path construction from
  user input); the registry is code, not user input. No new attack surface beyond one read-mostly
  endpoint. ✓

## Build Order

```
WP-A (registry) ──► WP-B (resolver service) ──┬──► WP-D (HTTP route) ──► WP-E (refine wiring + /cast-router)
WP-C (schema + models) ───────────────────────┘         WP-F (spec) — after A-D interfaces settle, parallel with E
```

**Critical path:** A → B → D → E. C is independent of A/B (parallel from the start; D needs both).
F is documentation lockstep, parallel with E. All of Phase 3b parallels Phase 3a.

## Design Review Flags

| Item | Flag | Action |
|---|---|---|
| Registry placement | `config.py` (locked by delegation) vs `WorkFamily` enum in `families.py` — duplication risk | String-keyed registry + derived `WORKFLOW_FAMILIES` + pin test against the enum (Phase 2 Decision #5 mirror discipline); config.py imports nothing new |
| Dual persistence | `classification.family` (front-matter) vs `goals.workflow_family` (column) could diverge on hand-edits | Router reads ONLY the column; both written by the same Step 0; divergence accepted for v2 and documented in the WP-F spec |
| `generic` family routing | Could be mistaken for the forbidden silent fallback | `generic` is model-selected (never a coercion target) and gets a *named* stub; the forbidden case is unknown/unclassified resolving silently — both are non-persisting Special Cases |
| `STARTER_TASKS` adjacency | `_create_starter_tasks` is literally the family-blind generic seed FR-015 abolishes | Resolver module has no `STARTER_TASKS` reference — enforced by a source pin test, not convention |
| `GoalUpdate` threading | Model currently has zero consumers; threading alone changes nothing | Done for contract completeness; the real write path is `record_routing_decision`; stated in WP-C so nobody "finishes" a second write path |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Router silently re-classifies (the playbook's #1 pitfall) | High | `resolve` takes the family as an argument and has no LLM/agent imports; the endpoint handler touches only goal_service + router service; SC-005 phase-flip test pins byte-identical output |
| Registry drifts from the `WorkFamily` enum (add-a-family forgets one home) | Medium | Pin test fails CI on key-set inequality; the WP-F spec's graduate/add checklists name both homes |
| Recording garbage on classifier misbehavior | Medium | Whitelist guard in `record_routing_decision` + endpoint recording rule: only valid families persist; `unmatched` announces and returns |
| Refinement dies when cast-server is down at route time | Medium | Fail-soft: front-matter classification still persists; Open Questions note + `/cast-router` re-run path; decoupled failure domains |
| Stub path untested ("flag-off" neglect) | Medium | The stub IS the v2 path — every family's stub handle is a first-class table-driven test case, incl. `bug_fix`'s exact spec-mandated steps |
| `routed_at` churn breaks byte-stability across phases | Low | Idempotent no-op leaves `routed_at` untouched; the SC-005 test asserts the full response body, not just the handle fields |

## Open Questions

- **Stub `steps` wording per family** (except `bug_fix`, which is spec-mandated): the WP-A strings
  are proposed copy. Owner can edit them at execution time — they render into `goal.yaml` and the
  refinement summary, so wording is user-facing. Decision changes only data, not the plan.
- **`/cast-router` skill — ship or cut:** included per the high-level plan's "optionally ship";
  it is the designated cuttable item if the 1-2 session budget runs short. Default: ship.

## Out of Scope (HOLD SCOPE fence)

- The family pipelines themselves (every registry value stays `stub`).
- Wiring any phase other than requirements (planners/executors come in later per-family goals).
- A `goal_routing` history/audit table (current-vs-previous suffices for US6 S4 in v2).
- A goal-page UI routing panel (playbook Step 7's UI half) — no v2 requirement consumes it;
  `goal.yaml` + the refinement summary are the v2 surfaces.
- Rules engine / DB-backed registry / plugin loader (EIP "configurable rules engine" — deferred
  by the rule of three).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|---|---|---|
| `cast-delegation-contract.collab.md` | Scope (agent dispatch + output files) | None — `/route` is a plain JSON API outside this contract |
| `cast-output-json-contract.collab.md` | Contract-v2 envelope | None — no new artifact types; refinement's existing envelope unchanged |
| *(new, Phase 2 WP-F)* `cast-goal-classification.collab.md` | `WorkFamily` vocabulary, front-matter schema | None — routing cites the vocabulary, never redefines it |
| *(new, this plan WP-F)* `cast-workflow-routing.collab.md` | Created via `/cast-update-spec` | n/a — becomes the contract future pipeline goals cite |

## Suggested Revisions to Prior Sub-Phases

None required. One wording clarification for the record (no plan change): Phase 2's Naming
Contract calls `classification.family` "the ONE field the router consumes" — precisely, it is the
one *classification* field the routing flow consumes *at refinement time*; the phase-agnostic
re-resolve path (FR-016) thereafter reads the recorded `goals.workflow_family` column, not the
front-matter. Same value, two read sites, one writer moment — stated here and in the WP-F spec so
the two phrasings aren't read as a conflict.

## Decisions

> Appended by `cast-plan-review` (2026-06-11). BIG-CHANGE pass over all four sections; 5 issues,
> all resolved. Architecture 2, Code Quality 1, Tests 2, Performance 0 (clean — pure functions +
> one PK-keyed single-row UPDATE, no N+1/loops/LLM in the request path; the per-refine classifier
> dispatch was already accepted in Phase 2's review). Body of the Interfaces section, WP-B, WP-E,
> WP-F, and the Design Review patched inline above to match these decisions.

- **2026-06-11T17:55:00Z — Should `routing_handle` be a stored column or derived-on-read, given it is fully derivable from `workflow_family` + the registry and goes stale when a family graduates `stub→implemented`?** — Decision: Keep it stored, but document the staleness explicitly. The handle is a point-in-time STAMP that can lag the registry until the goal is re-routed (re-route is the refresh mechanism); this is an accepted, spec-documented contract, not a bug. Rationale: the stored value is wanted for human visibility in `goal.yaml` and for the SC-005 byte-stability test; deriving live would remove both. Making the staleness a documented contract beats a latent surprise. (Interfaces — Stored handle format; WP-F spec)
- **2026-06-11T17:56:00Z — The family is persisted in two places (front-matter `classification.family` and the `goals.workflow_family` column) with no named authority or reconciliation rule; how is the "which one wins" ambiguity closed?** — Decision: Declare `goals.workflow_family` the authoritative routing record and single writer-of-record; front-matter is the document's self-description, reconciled to the column on the next refine (Step 0 re-writes both). A hand-edited front-matter family takes effect only by re-running refinement, which re-routes and overwrites the column. Rationale: names one authority without new code, prevents a future maintainer from "fixing" the divergence by making front-matter authoritative (which would re-introduce a parser read into the FR-016 pure-DB routing path). (WP-E; Design Review — dual persistence)
- **2026-06-11T17:57:00Z — "Add-a-family" now spans two checklists in two specs (Phase 2 classification + this plan's routing) that can drift; how is the procedure kept coherent?** — Decision: The WP-F spec does NOT restate a separate add-a-family list; it appends the routing homes (the `WORKFLOW_REGISTRY` entry) and the graduate-a-family steps (flip `status`, set `pipeline_ref`) as a labeled extension of the ONE canonical `cast-goal-classification.collab.md` checklist. Rationale: DRY — one list a maintainer follows end-to-end; near-zero extra work since WP-F already cross-references that spec; the registry/enum key-set pin test remains the CI backstop. (WP-F)
- **2026-06-11T17:58:00Z — The "router never re-classifies" guarantee (FR-016/SC-005, the plan's #1 risk) is asserted by manual code inspection; should it be an automated test?** — Decision: Yes — add a source-pin test asserting the `workflow_router_service` module AND the `/route` handler module source contain no agent-dispatch/subprocess/classifier imports, mirroring the existing no-`STARTER_TASKS` pin; this replaces the SC-005 "assert by code inspection" step. Rationale: load-bearing invariants belong in CI, not a manual grep — directly consistent with Phase 2 Decision #6, and the pin harness already exists. (WP-B; Verification SC-005 trace)
- **2026-06-11T17:59:00Z — `record_routing_decision` writes the DB row but `_update_goal_yaml_fields` silently logs-and-returns on a missing `goal.yaml`, contradicting the plan's "zero silent failures" claim; how is this handled?** — Decision: Add a test pinning the missing-`goal.yaml` behavior (DB row written, no raise) and a one-line recorder docstring stating the yaml mirror is best-effort (DB is authoritative); qualify the Design Review "zero silent failures" wording to scope it to the routing decision, with the yaml mirror named as the one best-effort path. Rationale: matches the established `update_status` pattern (no behavior change) while turning an undocumented silent path into a pinned, intentional contract. (WP-B; WP-C; Design Review — Error & rescue)
