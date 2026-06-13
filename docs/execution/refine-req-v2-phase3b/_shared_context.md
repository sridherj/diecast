# Shared Context: Refine Requirements v2 — Phase 3b (Routing: Phase-Agnostic Workflow Router)

> **Read this file at the start of every sub-phase session.** It is the cross-cutting
> reference — names, contracts, conventions, and decisions — that every `spN_*/plan.md`
> assumes. It is NOT inlined into each sub-phase; read it once, then open your sub-phase file.

## Source Documents
- **Plan:** `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md` (the authoritative spec for this work — read the Work Package that maps to your sub-phase)
- **Cross-phase decisions:** `docs/plan/refine-requirements-v2-decisions-so-far.md` (canonical names/interfaces all phases adopt verbatim — see the Phase 3b section)
- **High-level plan:** `goals/refine-requirements-v2/plan.collab.md` (Phase 3b is one of six phases)

## Project Background

Refine Requirements v2 makes requirement documents **workflow-aware** and **HTML-first**. Phase 3b
is the **routing** layer: once a goal has been classified into a `WorkFamily` (Phase 2), it resolves
to a family-specific downstream-workflow **handle** — a named **stub** for every not-yet-built
pipeline. The decision is recorded on the goal (DB columns that auto-render to `goal.yaml`), and the
resolver is invokable from **any phase** without re-running refinement.

The load-bearing design insight (exploration Playbook 06): **phase-agnosticism (FR-016) is not a
feature you build — it is a property you fail to destroy.** The resolver is a pure, total function of
the *persisted* family; it never re-classifies, so any caller in any phase gets the same answer for
free. v2 ships the **seam + stubs, not the pipelines** (FR-015): every registry value stays
`status="stub"`; flipping one to `"implemented"` later is a registry-only diff with no seam change.

**Operating mode: HOLD SCOPE.** The build boundary is explicit and repeated: "ship the door, not the
future callers." In v2, `cast-refine-requirements` is the **only** caller of the router — do not wire
planners/executors or any other phase. No rules engine, no `goal_routing` history table, no UI
routing panel (see each plan's Out of Scope). All five plan-review decisions are final and recorded
in the source plan's `## Decisions` section.

## Hard Prerequisite: Phase 2 Must Be Landed First

Phase 3b consumes Phase 2's taxonomy. Before executing **any** Phase 3b sub-phase, confirm Phase 2's
Work Packages A (taxonomy) and B/E (classifier + Step 0 in the refine prompt) have landed:

```bash
ls cast-server/cast_server/requirements_render/families.py    # must exist: WorkFamily (9 values)
python -c "from cast_server.requirements_render.families import WorkFamily; print([f.value for f in WorkFamily])"
grep -n "Step 0" agents/cast-refine-requirements/cast-refine-requirements.md   # Phase 2 WP-E classify step
```

Phase 3b is **off the critical path** of the whole goal (Phase 4 depends on Phase 3a, not 3b) and
depends **only** on Phase 2 — it does not need Phase 2's checker or corpus-eval work. It runs in
parallel with Phase 3a.

## Codebase Conventions

| Convention | Rule |
|---|---|
| **Service DB pattern (canon for the write path)** | Flat functions, `db_path: Path \| None = None` injectable + `get_connection(db_path)`, try/finally close; modeled on `goal_service.py` / `task_service.py`, **NOT** `orchestration_service.py` (which is file/manifest-based — owner Decision Opt A demotes it as DB canon). `workflow_router_service.py` uses this for its one write path. |
| **Service STRUCTURE precedent** | `orchestration_service.py` is the precedent for *module shape only*: pure logic, no LLM/subprocess/tmux, frozen dataclass result, `if __name__ == "__main__"` CLI hook. `workflow_router_service.py` mirrors this shape — **structure from orchestration_service, persistence from goal_service.** |
| **Schema** | Edit the **canonical** `cast-server/cast_server/db/schema.sql` (the root `db/schema.sql` is legacy/diverged — do NOT edit it) AND mirror an idempotent `ALTER TABLE … ADD COLUMN` try/except in `_run_migrations()` in `db/connection.py`. Precedent: the `gstack_dir`/`external_project_dir` loop at `connection.py:100-104`. |
| **`goal.yaml` mirror** | `goal_service._update_goal_yaml_fields()` merges arbitrary keys (recording works day one); conditional includes in `_write_goal_yaml()` (like `gstack_dir`) make a full re-render preserve the fields. The yaml mirror is **best-effort** — a missing file is logged, not raised (DB is authoritative). |
| **Routes** | `/api/goals/{slug}/<verb>` is agent-facing JSON (precedent: `api_agents.py`); `/goals/{slug}/<verb>` in `routes/pages.py` is the human HTMX surface. Route follows the `/status`, `/phase` precedent in `api_goals.py`. |
| **Agents** | Live in `agents/<name>/<name>.md` + `config.yaml`. After creating/editing an agent, run `bin/generate-skills` and verify the generated skill appears. |
| **Specs** | `docs/specs/*.collab.md`, registered in `docs/specs/_registry.md`; authored/edited via `/cast-update-spec`; linted by `bin/cast-spec-checker`. |
| **Prompt ceiling** | `agents/cast-refine-requirements/cast-refine-requirements.md` has a **~650-line ceiling** shared with Phases 1b/2. Phase 3b's WP-E addition is ~15 lines appended to Phase 2's "Step 0 — Classify". |
| **Python / pytest quality** | Apply `/cast-python-best-practices` + `/cast-pytest-best-practices` when writing code/tests. |

## Key File Paths

| Path | Role | State at Phase 3b start |
|---|---|---|
| `cast-server/cast_server/config.py` | `STARTER_TASKS` (line ~77); **`WORKFLOW_REGISTRY` added beside it (sp1a)** | Exists; no `WORKFLOW_REGISTRY` yet — config stays the import-free bottom layer |
| `cast-server/cast_server/requirements_render/families.py` | `WorkFamily` (9 values) — Phase 2 keystone | From Phase 2 — imported by tests ONLY (the registry/enum pin test) |
| `cast-server/cast_server/services/workflow_router_service.py` | **NEW (sp2)** — pure resolver + one recorder | Does not exist |
| `cast-server/cast_server/services/orchestration_service.py` | STRUCTURE precedent (dataclass result + CLI hook) | Exists — read for shape, do NOT modify |
| `cast-server/cast_server/services/goal_service.py` | DB pattern + `_resolve_goal_dir`/`_update_goal_yaml_fields`/`_write_goal_yaml`; **modified (sp1b)** for the 3-field render | Exists; `gstack_dir` conditional-include precedent at `_write_goal_yaml` |
| `cast-server/cast_server/db/schema.sql` | **CANONICAL** goals table; **modified (sp1b)** | Exists; `gstack_dir` at line ~12 |
| `cast-server/cast_server/db/connection.py` | `_run_migrations()`; **modified (sp1b)** | Exists; `gstack_dir` ALTER loop at lines 100-104 |
| `cast-server/cast_server/models/goal.py` | `Goal`, `GoalUpdate`; **modified (sp1b)** | Exists |
| `cast-server/cast_server/routes/api_goals.py` | `/status` (l.101), `/phase` (l.144); **`POST /{slug}/route` added (sp3)** | Exists |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | The only v2 caller — **modified (sp4a)** | Exists; Phase 2 WP-E "Step 0 — Classify" is the anchor |
| `agents/cast-router/` | **NEW (sp4a, optional)** — thin read-only resolve-and-show skill | Does not exist |
| `docs/specs/cast-workflow-routing.collab.md` | **NEW (sp4b)** — the contract future pipeline goals cite | Does not exist |
| `docs/specs/cast-goal-classification.collab.md` | Phase 2 WP-F spec — routing **cites** the family vocabulary, never redefines | From Phase 2 |

## Data Schemas & Contracts (copy verbatim — the Phase 3b Naming Contract)

**Registry — `cast-server/cast_server/config.py` (sp1a), beside `STARTER_TASKS`:**

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

- Every value `status="stub"` in v2 (FR-015). `bug_fix`'s steps are **spec-mandated**
  (`logs→RCA→confirm→fix/test`); all other step wordings are owner-editable copy, not contracts.
- `generic` gets a *named* stub like every other family — it is model-selected (Phase 2 Decision #2:
  `GENERIC` is never a coercion target), so routing it to a named stub is an **announced** decision,
  not a silent fallback. The *forbidden* fallback is an unknown/unclassified case quietly resolving.

**Resolver interfaces — `cast-server/cast_server/services/workflow_router_service.py` (sp2). Phases 4/5 and future pipeline goals MUST adopt these:**

```python
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

**`resolve` totality (PURE + TOTAL — no DB, no LLM, takes the family as an argument):**
- `None` → `WorkflowHandle(None, "needs-classification", message="Goal not yet classified — run /cast-refine-requirements first; the router never guesses.")`
- unknown string → `WorkflowHandle(family, "unmatched", message=f"No pipeline registered for '{family}' — registry knows: {sorted(WORKFLOW_FAMILIES)}.")` — a Special Case that *announces itself*, never a silent Null Object.
- hit → `WorkflowHandle(family, entry["status"], steps=tuple(entry["steps"]), message=...)`.

**`record_routing_decision` (the ONLY writer, house DB pattern):**
- Guard: `family in WORKFLOW_FAMILIES` **and** `handle.status in ("stub", "implemented")` — else raise
  `ValueError`. Callers must never persist `unmatched`/`needs-classification`.
- Read current row; if `workflow_family == family and routing_handle == f"{family}:{handle.status}"`
  → **no-op** (`{"recorded": False, "changed": False, ...}`; `routed_at` untouched).
- Else `UPDATE goals SET workflow_family=?, routing_handle=?, routed_at=?` (ISO-8601 UTC) and mirror
  to `goal.yaml` via `goal_service._update_goal_yaml_fields(_resolve_goal_dir(...), ...)` (best-effort
  — a missing file is logged, not raised; DB is authoritative).
- Return `{"recorded": True, "changed": <prior family differed>, "previous_family": ...}`.

**Stored handle format:** `goals.routing_handle = f"{family}:{status}"` (e.g. `bug_fix:stub`).
- A point-in-time **STAMP, not derived-on-read** (plan-review Decision #1): it can lag the registry —
  when a family graduates `stub→implemented`, every already-routed goal keeps its old `{family}:stub`
  handle until re-routed (re-route IS the refresh). Accepted, documented contract — preserves the
  SC-005 byte-stability test and the human-visible `goal.yaml` stamp.
- `goals.workflow_family` is the **AUTHORITATIVE** routing record and single writer-of-record
  (plan-review Decision #2); front-matter `classification.family` is the document's self-description,
  reconciled to the column on the next refine (Step 0 re-writes both). Do NOT "fix" the divergence by
  making front-matter authoritative — that re-introduces a parser read into the FR-016 pure-DB path.

**Recording rule:** only valid `WorkFamily` values are ever persisted. `unmatched` and
`needs-classification` handles are *returned and announced*, never recorded (no garbage in `goal.yaml`).

**HTTP surface — `POST /api/goals/{slug}/route` (sp3, JSON in/out):**
- *With* body `{"family": "<WorkFamily value>"}` (the refinement path): resolve + record.
- *Without* body (the FR-016 path — any future phase/agent): read `goal["workflow_family"]` from the
  DB, resolve, re-record idempotently (a no-op when unchanged — `routed_at` NOT touched).
- **200** handle + recording metadata:
  `{"family", "status", "steps", "pipeline_ref", "message", "recorded", "changed", "previous_family", "routing_handle", "routed_at"}`.
- **404** unknown slug. Unknown family string in body → **200** with the `unmatched` handle +
  `recorded: false` (totality ⇒ the API never 500s on content). `None` persisted + no body → **200**
  with `needs-classification`, `recorded: false`.
- The handler calls **only** `goal_service.get_goal` + `workflow_router_service.resolve` /
  `record_routing_decision` — no agent dispatch, no LLM, nothing that could re-classify.

**Goal columns (sp1b):** `workflow_family TEXT`, `routing_handle TEXT`, `routed_at TEXT` on `goals`.
`GoalUpdate` gains `workflow_family` and `routing_handle` (NOT `routed_at` — server-set).
`taxonomy_version` front-matter field (Phase 2) is recorded alongside so a future family-set bump is
detectable.

## Pre-Existing Decisions (binding — adopt verbatim)

**Plan-review decisions (2026-06-11, appended by `cast-plan-review`, all five final):**
- **D1 — `routing_handle` is STORED, not derived-on-read.** It is a point-in-time stamp that can lag
  the registry until re-route; documented staleness, not a bug. Preserves the SC-005 byte-stability
  test and the `goal.yaml` stamp. (Interfaces — Stored handle format; spec in sp4b.)
- **D2 — `goals.workflow_family` is the AUTHORITATIVE routing record / single writer-of-record.**
  Front-matter `classification.family` reconciles to the column on the next refine. (sp4a; Design
  Review — dual persistence.)
- **D3 — Single canonical add-a-family checklist.** The sp4b spec does NOT restate a separate
  add-a-family list; it appends the routing homes (`WORKFLOW_REGISTRY` entry) and the
  graduate-a-family steps (flip `status`, set `pipeline_ref`) as a labeled extension of the ONE
  canonical `cast-goal-classification.collab.md` checklist. (sp4b.)
- **D4 — No-reclassify guarantee is an automated source-pin test, not manual inspection.** A test
  asserts the `workflow_router_service` module AND the `/route` handler module source contain no
  agent-dispatch/subprocess/classifier imports — mirroring the no-`STARTER_TASKS` pin. This REPLACES
  the SC-005 "assert by code inspection" step. (sp2; sp3; Verification SC-005 trace.)
- **D5 — Missing-`goal.yaml` recording is pinned best-effort.** A test records against a goal whose
  `goal.yaml` is absent → the DB row IS written and the call does NOT raise; a recorder docstring line
  states the yaml mirror is best-effort (DB authoritative). (sp2.)

**Autonomous-run defaults recorded this session (delegation = PROCEED FULLY AUTONOMOUSLY):**
- **`/cast-router` skill — SHIP it** (sp4a). The high-level plan says "optionally ship"; the source
  plan's default is "ship" (near-zero cost, completes the FR-013 surface). It is the designated
  cuttable item if the 1–2 session budget runs short — if cut, flag it in the run summary, never
  silently skip.
- **Stub `steps` wording — adopt the WP-A strings verbatim** (except `bug_fix`, spec-mandated). They
  are owner-editable copy at execution time (they render into `goal.yaml` + the refinement summary);
  editing them changes data only, not the plan.

## Relevant Specs

| Spec | Overlap | Note |
|---|---|---|
| `docs/specs/cast-delegation-contract.collab.md` | Agent dispatch + output-file contract | **None** — `/route` is a plain JSON API, not agent dispatch; no output-envelope semantics apply. UNTOUCHED. |
| `docs/specs/cast-output-json-contract.collab.md` | Contract-v2 envelope | **None** — no new artifact types; refinement's existing envelope unchanged. |
| `docs/specs/cast-goal-classification.collab.md` *(Phase 2 WP-F)* | `WorkFamily` vocabulary, front-matter schema | Routing **cites** the vocabulary, never redefines it. sp4b cross-references it and appends the routing/graduate steps (D3). |
| *(new)* `docs/specs/cast-workflow-routing.collab.md` | Created by sp4b | Becomes the contract future pipeline goals cite. |

Do NOT paste spec Behaviors here — read the spec on-demand only when your sub-phase modifies
spec-linked files.

## Sub-Phase Dependency Summary

| Sub-phase | Source WP | Type | Depends On | Blocks | Can Parallel With |
|---|---|---|---|---|---|
| sp1a_family_registry | A | Sub-phase | — (Phase 2 landed) | sp2, sp4b | sp1b |
| sp1b_recording_columns | C | Sub-phase | — (Phase 2 landed) | sp2, sp3 | sp1a |
| sp2_resolver_service | B | Sub-phase | sp1a, sp1b | sp3, sp4a, sp4b | — |
| sp3_route_endpoint | D | Sub-phase | sp2 | sp4a, sp4b | — |
| sp4a_refine_wiring | E | Sub-phase | sp3 | — | sp4b |
| sp4b_routing_spec | F | Sub-phase | sp1a, sp2, sp3 (interfaces) | — | sp4a |

No decision gates (HOLD SCOPE — all five plan-review decisions resolved at plan review).

**Critical path:** sp1a → sp2 → sp3 → sp4a. sp1b runs parallel with sp1a (both feed sp2). sp4b
(spec/docs) runs parallel with sp4a once the sp1a–sp3 interfaces have settled.

## Phase Gate (SC-005 — the whole-phase acceptance bar)

- `pytest` green on `cast-server/tests/test_workflow_router_service.py` and `test_api_goals_route.py`.
- **Totality:** `resolve` returns a real `WorkflowHandle` for all 9 families + `None` + an unknown
  string — 0 exceptions, 0 `None` returns; the three edge handles carry the right `status` + a
  non-empty `message`.
- **Stub discipline (FR-015):** every registry value `status="stub"` with non-empty `steps`; a pin
  test asserts the `workflow_router_service` source has no `STARTER_TASKS` reference.
- **Registry/enum pin:** `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}` — drift fails CI.
- **Idempotency:** same family twice → no-op (`routed_at` unchanged, `recorded: false`); different
  family → updated row + `changed: true` + `previous_family`.
- **No-reclassify source pin (D4):** router module AND `/route` handler contain no
  subprocess/agent-dispatch/classifier imports.
- **End-to-end (SC-005 trace):** seed 5 goals (`bug_fix`, `new_initiative`, `data_analysis`,
  `random_idea`, `testing_qa`) → `POST /route` each → correct handle AND `workflow_family`/
  `routing_handle` in both the DB row and the rendered `goal.yaml`. Flip one goal's `phase` →
  `POST /route` with no body → **byte-identical** handle JSON, no classifier in the path.
- `bin/cast-spec-checker` green on the new spec (sp4b).
