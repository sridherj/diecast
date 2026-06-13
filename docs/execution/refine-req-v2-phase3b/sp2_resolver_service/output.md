# sp2_resolver_service — Output

**Status:** ✅ Completed. `pytest` green (26/26), ruff clean, all SC-005 pins satisfied.

## What was built

### `cast-server/cast_server/services/workflow_router_service.py` (NEW)
The pure resolver + single idempotent recorder. Module shape mirrors
`orchestration_service.py` (docstring contract, frozen dataclass result, CLI hook);
the write path uses `goal_service.py`'s DB pattern (`get_connection(db_path)` +
try/finally close) — *structure from one precedent, persistence from the other*.

- **`WorkflowHandle`** — frozen dataclass: `family: str | None`, `status: str`,
  `steps: tuple[str, ...] = ()`, `pipeline_ref: str | None = None`, `message: str = ""`.
- **`resolve(family) -> WorkflowHandle`** — PURE + TOTAL, no DB / no LLM / no `db_path`
  parameter (purity-by-shape). `None → needs-classification`, unknown string →
  `unmatched` (a self-announcing Special Case), hit → registry status + `tuple(steps)`.
- **`record_routing_decision(slug, family, handle, goals_dir=None, db_path=None) -> dict`**
  — the ONLY writer. Guards non-routable handles + unknown slug with `ValueError`;
  idempotent (same `{family}:{status}` → `{recorded: False}`, `routed_at` untouched);
  writes `workflow_family`/`routing_handle`/`routed_at` and mirrors to `goal.yaml`
  **best-effort** (DB authoritative; missing yaml logged, not raised — D5). Returns
  `{recorded, changed, previous_family, routing_handle[, routed_at]}` where `changed`
  is True only when a *prior* family existed and differed.
- **CLI hook** — `resolve <family>` and `route <slug> [family]` (server-down escape
  hatch / test aid; agents use the sp3 HTTP door).

The stored `routing_handle = f"{family}:{status}"` is a point-in-time STAMP (D1), not
derived-on-read — preserves SC-005 byte-stability and the human-visible `goal.yaml`.

### `cast-server/tests/test_workflow_router_service.py` (NEW)
26 tests, all green:
- **Totality** (parametrized 9 families + `None` + unknown) — registry status,
  non-empty steps/message; 0 exceptions, 0 `None`.
- **`resolve` purity** — `inspect.signature` excludes `db_path` (params == `["family"]`).
- **Registry↔`WorkFamily` key-set pin** — the ONE place Phase 3b imports `families.py`.
- **Stub discipline (FR-015)** — every entry `status="stub"` with non-empty steps.
- **Source pins (D4)** — no `STARTER_TASKS`; no `import subprocess`/`cast_goal_classifier`/
  `/trigger`/LLM-client imports. *(Pin scoped to import-form tokens so it can't
  false-positive on the module's own no-reclassify docstring prose.)*
- **Recorder** — idempotency (`routed_at` unchanged), change-path (`changed: true` +
  `previous_family`), `goal.yaml` round-trip, missing-`goal.yaml` best-effort (D5).
- **Guards** — `unmatched`/`needs-classification`/unknown-family/unknown-slug all raise.

## Verification run
```
uv run --project cast-server pytest cast-server/tests/test_workflow_router_service.py -q  → 26 passed
uv run --project cast-server ruff check <service> <test>                                  → All checks passed!
python -m cast_server.services.workflow_router_service resolve bug_fix                     → stub handle JSON
python -m cast_server.services.workflow_router_service resolve nonsense                    → unmatched handle JSON
grep -nE "import subprocess|cast_goal_classifier|STARTER_TASKS|/trigger|import anthropic|import openai" <service>  → source clean
broader suite (test_goal_routing_columns + test_goal_service_ext_routing + this)           → 47 passed
```

## Notes for dependent sub-phases
- **sp3** (`POST /api/goals/{slug}/route`): the handler must call ONLY
  `goal_service.get_goal` + `workflow_router_service.resolve`/`record_routing_decision`.
  Extend the D4 no-reclassify source pin to the `/route` handler module (same mechanism;
  scope the `subprocess` token to import-form as done here). Return shape from
  `record_routing_decision` already carries `recorded`/`changed`/`previous_family`/
  `routing_handle`/`routed_at`; merge with the handle fields for the 200 body.
- **sp4a**: surfaces `changed: true` + `previous_family` as US6 S4 — return shape is final.
- `pipeline_ref` is plumbed through `resolve` (reads `entry.get("pipeline_ref")`) so a
  future graduated family needs only a registry edit, no resolver change.
