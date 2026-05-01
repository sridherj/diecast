# Shared Context: Cast-UI E2E Test Harness

## Source Documents
- Plan: `/home/sridherj/workspace/diecast/docs/plan/2026-05-01-cast-ui-e2e-test-harness.collab.md`
- Writeup: (none — plan is self-contained)
- Canonical delegation contract: `/home/sridherj/workspace/diecast/skills/claude-code/cast-child-delegation/SKILL.md`

## Project Background

The user wants a single command — `pytest cast-server/tests/ui/` — that exercises every
screen and tab of the Diecast UI end-to-end against a real Chromium browser, while
simultaneously validating the agent delegation infrastructure (`/api/agents/{name}/trigger`
→ `parent_run_id` → child completion polling) by **using it as the test driver**.

The architecture is dual-purpose:
1. **UI smoke + functional sweep.** Every page loads, every tab swaps, every CRUD-style
   flow round-trips (create goal → see on dashboard → open detail → switch phase tabs →
   trigger an agent → see run → cleanup).
2. **Delegation validation by use.** A single orchestrator agent (`cast-ui-test-orchestrator`)
   fans out to 7 per-screen worker agents, each running Playwright-Python against its
   assigned screen. The orchestrator + children follow the canonical
   `cast-child-delegation` skill verbatim — drift in the production delegation contract
   gets caught here.

A separate `noop` test agent supports the goal_detail trigger-flow assertion and the
runs-page cancel-flow assertion (with `--sleep=Ns`).

The harness boots a **second cast-server process on `127.0.0.1:8006`** against a temp
SQLite DB (`/tmp/diecast-uitest-<pid>.db`) with `CAST_TEST_AGENTS_DIR` pointed at
`cast-server/tests/ui/agents/`. The dev server on `:8000` MUST NOT be touched. After
the run, every test artifact evaporates: the test server is killed (process group),
the temp DB is deleted, `goals/ui-test-*` are removed, and orphan Chromium processes
are swept by a port-scoped pattern. Test agent definitions persist on disk.

## Codebase Conventions

- **Repo root:** `/home/sridherj/workspace/diecast/`
- **Server package:** `cast-server/cast_server/` (Python). Routes under `routes/`, services under `services/`, templates under `templates/pages/`.
- **Test package:** `cast-server/tests/` (existing pytest harness, will get a new `ui/` subdir).
- **Server entrypoint:** `bin/cast-server` (a shell script that launches uvicorn). Tests should `Popen` this directly with `start_new_session=True`.
- **Health probe:** `GET /api/health` (defined at `cast-server/cast_server/routes/api_health.py:18`). The plan's `_healthz_` references were corrected to `/api/health`.
- **Agent registry:** definitions live in directories under a configurable root. Each agent dir contains a `<name>.md` instructions file and a `config.yaml`.
- **Delegation contract:** the canonical pattern is in `skills/claude-code/cast-child-delegation/SKILL.md`. Test agents reference this skill verbatim — they do NOT re-implement curl-based delegation inline.
- **Goal artifacts directory:** `goals/<slug>/` at repo root. The teardown fixture removes `goals/ui-test-*`.

## Key File Paths

| File | Role |
|------|------|
| `cast-server/cast_server/services/agent_service.py` | Registry loader. `_load_agent_registry` at :1148, `get_all_agents` at :1191. |
| `cast-server/cast_server/routes/api_agents.py` | HTTP trigger surface: `POST /api/agents/{name}/trigger`, `GET /api/agents/jobs/<run_id>`, `POST /api/agents/runs/<id>/cancel`. |
| `cast-server/cast_server/routes/api_health.py` | Readiness probe at `/api/health` (line :18). |
| `cast-server/cast_server/templates/pages/dashboard.html` | Screen for `cast-ui-test-dashboard`. |
| `cast-server/cast_server/templates/pages/agents.html` | Screen for `cast-ui-test-agents`. |
| `cast-server/cast_server/templates/pages/runs.html` | Screen for `cast-ui-test-runs`. |
| `cast-server/cast_server/templates/pages/scratchpad.html` | Screen for `cast-ui-test-scratchpad`. |
| `cast-server/cast_server/templates/pages/goal_detail.html` | Screen for `cast-ui-test-goal-detail`. |
| `cast-server/cast_server/templates/pages/focus.html` | Screen for `cast-ui-test-focus`. |
| `cast-server/cast_server/templates/pages/about.html` | Screen for `cast-ui-test-about`. |
| `cast-server/cast_server/templates/components/goal_card.html` | Has the accept button (`hx-vals={"status":"accepted"}` at :42). |
| `cast-server/cast_server/templates/components/run_row.html` | Cancel button at :219 (`hx-post="/api/agents/runs/<id>/cancel"`). |
| `bin/cast-server` | Server entrypoint (shell wrapper around uvicorn). |
| `skills/claude-code/cast-child-delegation/SKILL.md` | Canonical delegation contract — read this BEFORE writing any test agent. |
| `cast-server/pyproject.toml` | Where `playwright` is added under `[project.optional-dependencies] test`. |
| `cast-server/tests/conftest.py` | Existing test conftest — DO NOT MODIFY. The new fixtures live in `cast-server/tests/ui/conftest.py`. |

## Data Schemas & Contracts

### `runner.py` CLI contract
```
python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" \
    --screen=<name> \
    --base-url=http://127.0.0.1:8006 \
    --goal-slug=<slug> \
    --output=<absolute-path-to-output.json>
```
- `--screen` is one of: `dashboard`, `agents`, `runs`, `scratchpad`, `goal-detail`, `focus`, `about`.
- `--base-url` defaults to `http://127.0.0.1:8006` if not provided.
- `--goal-slug` is the shared `ui-test-<unix_ts>-<rand4>` slug.
- `--output` is an absolute path the runner writes to (idempotent overwrite).
- Exit code: `0` on green, `1` on any failed assertion. (Output JSON is the source of truth either way.)

### Per-child `output.json` schema
```json
{
  "screen": "dashboard",
  "status": "completed" | "failed" | "skipped",
  "assertions_passed": ["string description", ...],
  "assertions_failed": [{"name": "...", "error": "..."}, ...],
  "console_errors": ["...", ...],
  "console_warnings": ["...", ...],
  "screenshots": ["/abs/path/to/screenshot.png", ...],
  "started_at": "ISO8601",
  "finished_at": "ISO8601"
}
```
Console filter: ONLY `level=='error'` or `level=='pageerror'` count as failures.
`warning`/`info`/`debug` go into `console_warnings[]` without failing.

### Orchestrator `output.json` schema
```json
{
  "status": "completed" | "partial" | "failed",
  "children": {
    "cast-ui-test-dashboard": {"run_id": "...", "status": "completed", "output_path": "..."},
    "cast-ui-test-agents":    {...},
    ...
  },
  "summary": {"total": 7, "completed": 7, "failed": 0, "skipped": 0}
}
```
- `completed`: all children completed cleanly.
- `partial`: at least one child failed but others succeeded.
- `failed`: orchestrator itself errored (could not even dispatch).

### Per-child polling cap: 90s. Total run cap: 120s (SC-001).

## Pre-Existing Decisions (from plan-review pass 2026-05-01)

- **#1 Probe is `/api/health`**, not `/healthz`.
- **#2 Registry merge happens at `get_all_agents` call site**, not inside `_load_agent_registry`. Two roots, two independent mtime caches. Production path is bit-identical when env var unset.
- **#3 Test agents reference canonical `cast-child-delegation` skill verbatim** — no inline curl pattern.
- **#4 Process-group launch (`start_new_session=True`)** + finally-blocks in runner.py + post-teardown sweep with port-scoped pattern. Sweep pattern MUST NOT match dev-session browsers.
- **#5 Direct script-path invocation:** `python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py"`, NOT `python -m`.
- **#6 Severity-only console filter:** fail on `error`/`pageerror`, capture warnings separately. No allowlist.
- **#7 Goal creation owned by dashboard child:** orchestrator dispatches dashboard first, polls to completion, then triggers the rest in parallel. Slug shared via `test_goal_slug` fixture (passed to children via context).
- **#10 SC-004 dropped** (manual fault-injection only).
- **#11 Flake handling:** Playwright auto-wait + 30s per-assertion timeout + opt-in `pytest-rerunfailures` ONLY for `@pytest.mark.flaky`-tagged tests. Default zero retries.
- **#12 Per-child polling cap is 90s**, not 240s. Matches SC-001 budget.
- **#13 No parallelism throttle:** 7 Chromium instances in parallel. Acceptable on dev hardware.
- **#15 Task CRUD owned by goal_detail child** — full create/status-cycle/delete/accept-suggestion in one agent.
- **#16 Goal lifecycle ops:** focus/unfocus + idea→accepted in goal_detail child; separate `ui-test-delete-<ts>` throwaway in dashboard child for delete-button flow.
- **#17 Run cancellation:** `cast-ui-test-noop --sleep=20`, runs child cancels via UI button.
- **#18 Artifact CRUD owned by goal_detail child** — open editor, edit, save (PUT `/api/artifacts/save`), assert clean re-render.

## Relevant Specs

No specs in `docs/specs/` cover the files in this plan. (The plan itself was scaffolded
from `cast-spec.template.md` and lives under `docs/plan/`, not `docs/specs/`.)

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1_registry_extension | Sub-phase | -- | sp5 | sp2, sp3 |
| sp2_test_infra_fixtures | Sub-phase | -- | sp5 | sp1, sp3 |
| sp3_runner_helper | Sub-phase | -- | sp4a, sp4b, sp5 | sp1, sp2 |
| sp4a_test_agents_orchestrator_noop | Sub-phase | sp3 | sp5 | sp4b |
| sp4b_test_agents_screens | Sub-phase | sp3 | sp5 | sp4a |
| sp5_e2e_test_and_readme | Sub-phase | sp1, sp2, sp3, sp4a, sp4b | -- | -- |

No decision gates. Full execution is mechanical once sp1-sp4 land.
