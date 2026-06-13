# Sub-phase 2: Pure resolver `workflow_router_service.py`

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package B of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Create `cast-server/cast_server/services/workflow_router_service.py` — the heart of the phase. It holds
the `WorkflowHandle` frozen dataclass, the **PURE + TOTAL** `resolve(family)` function (no DB, no LLM,
no re-classification), and `record_routing_decision(...)` — the **single** idempotent writer of the
goal routing columns. The module mirrors `orchestration_service.py`'s *structure* (docstring contract,
dataclass result, CLI hook) while using `goal_service.py`'s *DB pattern* for its one write path. This
is where FR-016 (phase-agnosticism) and SC-005 (byte-stability) are *preserved* — `resolve` takes the
family as an argument and never touches a classifier, so any caller in any phase gets the same answer.

## Dependencies
- **Requires completed:**
  - **sp1a** — `WORKFLOW_REGISTRY` / `WORKFLOW_FAMILIES` in `config.py` (the data `resolve` indexes).
  - **sp1b** — the `workflow_family`/`routing_handle`/`routed_at` columns on `goals` (the recorder's
    idempotency / change-path / `goal.yaml` round-trip / missing-yaml tests need them to be green).
- **Assumed codebase state:** `config.WORKFLOW_REGISTRY` + `config.WORKFLOW_FAMILIES` exist; `goals`
  has the three routing columns; `goal_service.py` exposes `get_goal`, `_resolve_goal_dir`,
  `_update_goal_yaml_fields`; `db/connection.py` exposes `get_connection(db_path)`. Read
  `orchestration_service.py` for the module shape to mirror (structure only — NOT its file persistence).

## Scope

**In scope:**
- `WorkflowHandle` frozen dataclass (per the Interfaces contract; `steps` is a `tuple`).
- `resolve(family: str | None) -> WorkflowHandle` — total, ~5 lines of branching, no DB/LLM.
- `record_routing_decision(slug, family, handle, goals_dir=None, db_path=None) -> dict` — the one
  writer, house DB pattern, idempotent, best-effort `goal.yaml` mirror.
- CLI hook (`if __name__ == "__main__"`) mirroring `orchestration_service.py`'s.
- The full test module `cast-server/tests/test_workflow_router_service.py`, **including the
  registry↔`WorkFamily` key-set pin test** (co-located here per the source plan; the one place Phase 3b
  imports `families.py`, in tests only) and the **no-reclassify / no-`STARTER_TASKS` source pins** (D4).

**Out of scope (do NOT do these):**
- The HTTP route (sp3) — this module is service-layer only; no FastAPI imports.
- Wiring `cast-refine-requirements` (sp4a). The spec (sp4b).
- Re-defining the registry (it lives in `config.py`, sp1a) or the columns (sp1b).
- ANY agent dispatch / subprocess / LLM client import in this module — that would fail the D4 source
  pin and break FR-016 by construction. The resolver is a pure consumer of the persisted family.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/workflow_router_service.py` | Create | Does not exist |
| `cast-server/tests/test_workflow_router_service.py` | Create | Does not exist |

## Detailed Steps

### Step 2.1: Module skeleton + `WorkflowHandle`

Module docstring states the contract up front, mirroring `orchestration_service.py`'s:
*"Workflow router — pure resolution logic + one idempotent recorder. No LLM, no subprocess, no
re-classification."* Add a one-line note that **the `goal.yaml` mirror is best-effort (DB is
authoritative)** — Decision D5.

```python
@dataclass(frozen=True)
class WorkflowHandle:
    family: str | None
    status: str                    # "implemented" | "stub" | "unmatched" | "needs-classification"
    steps: tuple[str, ...] = ()
    pipeline_ref: str | None = None
    message: str = ""
```

### Step 2.2: `resolve(family)` — PURE + TOTAL

```python
def resolve(family: str | None) -> WorkflowHandle:
    if family is None:
        return WorkflowHandle(None, "needs-classification",
            message="Goal not yet classified — run /cast-refine-requirements first; the router never guesses.")
    entry = WORKFLOW_REGISTRY.get(family)
    if entry is None:
        return WorkflowHandle(family, "unmatched",
            message=f"No pipeline registered for '{family}' — registry knows: {sorted(WORKFLOW_FAMILIES)}.")
    return WorkflowHandle(family, entry["status"], steps=tuple(entry["steps"]),
        message=f"Routed to the {family} workflow ({entry['status']}).")
```

- **No `db_path` parameter on `resolve`** — its absence is a tested API invariant (purity by shape).
- `unmatched` is a Special Case that *announces itself*, never a silent Null Object.

### Step 2.3: `record_routing_decision(...)` — the ONLY writer (house DB pattern)

Use `goal_service.py`'s pattern: flat function, `get_connection(db_path)`, try/finally close — **NOT**
`orchestration_service.py`'s file-based persistence.

```python
def record_routing_decision(slug, family, handle, goals_dir=None, db_path=None) -> dict:
    if family not in WORKFLOW_FAMILIES or handle.status not in ("stub", "implemented"):
        raise ValueError(f"Refusing to record non-routable handle: family={family!r} status={handle.status!r}")
    new_handle = f"{family}:{handle.status}"
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT workflow_family, routing_handle FROM goals WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown goal slug: {slug!r}")
        prior_family = row["workflow_family"]
        if prior_family == family and row["routing_handle"] == new_handle:
            return {"recorded": False, "changed": False, "previous_family": prior_family,
                    "routing_handle": new_handle}
        routed_at = _utc_now_iso()
        conn.execute("UPDATE goals SET workflow_family=?, routing_handle=?, routed_at=? WHERE slug=?",
                     (family, new_handle, routed_at, slug))
        conn.commit()
    finally:
        conn.close()
    # best-effort goal.yaml mirror (DB is authoritative — a missing file is logged, not raised; D5)
    _mirror_to_goal_yaml(slug, family, new_handle, routed_at, goals_dir)
    return {"recorded": True, "changed": prior_family is not None and prior_family != family,
            "previous_family": prior_family, "routing_handle": new_handle, "routed_at": routed_at}
```

- The `goal.yaml` mirror calls `goal_service._update_goal_yaml_fields(_resolve_goal_dir(...), {...})`
  — the **same resolve-dir path** `update_status` uses, so externally-routed goals render correctly.
  Wrap it so a missing file logs-and-returns (matching `update_status`/`_update_goal_yaml_fields`).
- Confirm the exact column accessor style (`row["workflow_family"]` vs index) matches `goal_service`'s
  `get_connection` row factory — read `goal_service.py` and follow it.
- `changed` is `true` only when a **prior** family existed and differed (first-ever routing →
  `changed: false`, `previous_family: None`).

### Step 2.4: CLI hook

Mirror `orchestration_service.py`'s `if __name__ == "__main__"`:
- `python -m cast_server.services.workflow_router_service resolve <family>` → prints handle JSON.
- `... route <slug> [family]` → resolve-from-DB; record when `family` given.

A server-down escape hatch / test aid; agents use the HTTP door (sp3).

### Step 2.5: Test module — `cast-server/tests/test_workflow_router_service.py`

This is where ~30–40% of the effort goes. Required cases:
- **Totality (table-driven, 9 + 2 cases):** all 9 families → `status` from the registry, non-empty
  `steps`, non-empty `message`; `None` → `needs-classification`; unknown string `"nonsense"` →
  `unmatched`. 0 exceptions, 0 `None` returns. The three edge handles carry the right `status` + a
  non-empty `message`.
- **`resolve` purity:** assert `resolve` has **no `db_path` parameter**
  (`inspect.signature(resolve).parameters` excludes `db_path`) — purity-by-shape.
- **Registry↔enum pin (the WP-A pin, co-located here):**
  `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}` — this is the ONE place Phase 3b imports
  `families.py`. Drift fails CI (Phase 2 Decision #5 mirror discipline).
- **Stub discipline (FR-015):** every registry value `status="stub"` with non-empty `steps`.
- **No-`STARTER_TASKS` source pin:** read this module's own source (`inspect.getsource` or read the
  file) → assert it contains no `STARTER_TASKS` reference (the silent generic fallback is structurally
  unreachable).
- **No-reclassify source pin (D4):** assert the `workflow_router_service` module source contains no
  `subprocess`, no Agent/`/trigger` dispatch, no `cast_goal_classifier`, no LLM client import. Same
  mechanism as the `STARTER_TASKS` pin. (sp3 extends this same assertion to the `/route` handler.)
- **Record idempotency:** record `bug_fix` → `recorded: true, changed: false`; record `bug_fix` again
  → `recorded: false, changed: false`, and **`routed_at` unchanged** between the two DB rows.
- **Record change-path:** record `bug_fix` then `data_analysis` → second call `recorded: true,
  changed: true, previous_family: "bug_fix"`; row updated.
- **ValueError guards:** `record_routing_decision` with an `unmatched`/`needs-classification` handle
  (status not in `{stub, implemented}`) raises; with a family not in `WORKFLOW_FAMILIES` raises;
  unknown slug raises.
- **`goal.yaml` round-trip:** tmp goals-dir fixture (precedent: `test_goal_service_ext_routing.py`) →
  record → assert `goal.yaml` carries `workflow_family` + `routing_handle`.
- **Missing-`goal.yaml` recording (D5):** record against a goal whose `goal.yaml` is absent → the DB
  row IS written and the call does NOT raise (pins the yaml mirror as best-effort).

→ **Delegate:** apply `/cast-python-best-practices` over the service and `/cast-pytest-best-practices`
over the test module while writing. Review output for compliance.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_workflow_router_service.py`
All cases in Step 2.5. Headline gate assertions (SC-005): totality, stub discipline, registry/enum
pin, idempotency, no-reclassify + no-`STARTER_TASKS` source pins, missing-yaml best-effort.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_workflow_router_service.py -v
python -m cast_server.services.workflow_router_service resolve bug_fix
python -m cast_server.services.workflow_router_service resolve nonsense   # → unmatched handle JSON
# Source pins, eyeballed:
grep -nE "subprocess|cast_goal_classifier|STARTER_TASKS|/trigger" cast-server/cast_server/services/workflow_router_service.py && echo "PIN VIOLATION" || echo "source clean"
```

### Manual Checks
- `resolve` signature has no `db_path`.
- The module imports only `config` (registry), `goal_service`/`connection` (DB pattern), stdlib —
  nothing that classifies.
- `record_routing_decision` is the only function that executes an `UPDATE`/`INSERT`.

### Success Criteria
- [ ] `WorkflowHandle`, `resolve`, `record_routing_decision`, CLI hook present; module docstring states
      the no-LLM/no-subprocess/no-reclassify contract + the best-effort-yaml note.
- [ ] `resolve` is total over 9 families + `None` + unknown string; 0 exceptions, 0 `None`.
- [ ] Registry↔`WorkFamily` key-set pin green; no-`STARTER_TASKS` + no-reclassify source pins green.
- [ ] Recording is idempotent (no-op leaves `routed_at` untouched) and reports `changed`/`previous_family`.
- [ ] ValueError guards reject `unmatched`/`needs-classification`/unknown-family/unknown-slug.
- [ ] Missing-`goal.yaml` record writes the DB row without raising.
- [ ] `pytest cast-server/tests/test_workflow_router_service.py` green.

## Execution Notes
- **Mirror structure, not persistence.** `orchestration_service.py` is the shape template (dataclass
  result + CLI hook), but it persists to files/manifests — do NOT copy that. The write path is the
  `goal_service` DB pattern. The `_shared_context.md` calls this "structure from one precedent,
  persistence from the other" — thread the needle deliberately.
- The recorder writes `routing_handle = f"{family}:{status}"` — a point-in-time STAMP (D1). It can lag
  the registry after a family graduates; the SC-005 byte-stability test depends on this being stored,
  not derived. Do not "simplify" by deriving the handle on read.
- The `changed: true` + `previous_family` return is what sp4a surfaces as US6 S4 (downstream workflow
  changed on reclassification) — keep the return shape exactly as specified.

**Spec-linked files:** No spec covers `workflow_router_service.py` yet — sp4b authors it. No SAV
behaviors to preserve here; the source pins ARE the load-bearing invariants (in CI, not the spec).
