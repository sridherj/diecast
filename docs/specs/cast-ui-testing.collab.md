# Cast UI Testing

> **Spec maturity:** draft
> **Version:** 2
> **Updated:** 2026-05-01 — added `docs/specs/cast-runs-screen.collab.md` cross-reference under "Linked files" so the harness spec points at the per-screen contract for the threaded `/runs` page.
> **Linked files:**
> - `docs/plan/2026-05-01-cast-ui-e2e-test-harness.collab.md` (canonical plan)
> - `cast-server/tests/ui/` (harness)
> - `cast-server/tests/ui/agents/cast-ui-test-*/` (test agents)
> - `cast-server/cast_server/templates/pages/` (UI surface under test)
> - `cast-server/cast_server/routes/api_*.py` (HTTP routes under test)
> - `docs/specs/cast-runs-screen.collab.md` — per-screen contract for the threaded `/runs` page; the harness asserts US1–US7 of this spec via `cast-server/tests/ui/agents/cast-ui-test-runs/`.

## Intent

Every screen of the cast-server UI is covered by an end-to-end test harness that
exercises real flows in a real browser against a real (but isolated) cast-server.
Whenever a meaningful UI change ships, a corresponding test update is mandatory.
The harness is re-runnable anytime, leaves no residue, and never pollutes the dev
environment.

## User Stories

### US1 — Every screen and tab is exercised end-to-end (Priority: P1)

**As a** Diecast developer, **I want** the e2e harness at `cast-server/tests/ui/`
to cover every screen (dashboard, agents, runs, scratchpad, goal-detail, focus,
about) with smoke + functional + CRUD assertions, **so that** I catch both
load-level regressions and silent flow breakage in one shot.

**Independent test:** `pytest cast-server/tests/ui/test_full_sweep.py::test_ui_e2e`
exits 0 against a clean checkout.

**Acceptance scenarios:**

- **Scenario 1:** WHEN any screen at `http://127.0.0.1:8006/` loads, THE SYSTEM
  SHALL return HTTP 200 with no `level==error` or `level==pageerror` browser
  console messages.
- **Scenario 2:** WHEN a tab/filter on any screen is clicked, THE SYSTEM SHALL
  HTMX-swap or filter the relevant content within 5s.
- **Scenario 3:** WHEN a CRUD round-trip (create / status-cycle / delete) is
  performed on goals, tasks, scratchpad entries, or artifacts, THE SYSTEM SHALL
  reflect the change in the UI within 5s.

### US2 — UI changes mandate test updates (Priority: P1)

**As a** Diecast developer, **I want** any meaningful UI change to be paired
with a corresponding harness update, **so that** UI coverage never drifts behind
shipped behavior.

**Independent test:** A code-review checklist (or pre-merge gate) flags PRs that
modify `cast-server/cast_server/templates/pages/*.html`,
`cast-server/cast_server/routes/api_*.py`, or
`cast-server/cast_server/templates/fragments/*.html` without a matching diff in
`cast-server/tests/ui/`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a new page is added under `templates/pages/`, THE SYSTEM
  SHALL block merge until the change includes a new `cast-ui-test-<screen>`
  agent and a new entry in the orchestrator's child list.
- **Scenario 2:** WHEN a new route is added under `cast_server/routes/api_*.py`
  that surfaces in the UI (form, button, link, htmx target), THE SYSTEM SHALL
  block merge until the change includes a new assertion exercising that route
  in the relevant per-screen child.
- **Scenario 3:** WHEN a new tab, form, or CRUD flow is added on an existing
  screen, THE SYSTEM SHALL block merge until the change includes a new EARS
  scenario or assertion in the corresponding per-screen child's
  `_assert_<screen>(page, ctx)` function in `cast-server/tests/ui/runner.py`.

### US3 — Harness leaves zero residue across runs (Priority: P1)

**As a** Diecast developer, **I want to** run the harness three times in a row
and have each run be independent, **so that** flake debugging is reliable and
local dev state is never polluted.

**Independent test:** `for i in 1 2 3; do pytest cast-server/tests/ui/; done`
followed by a residue scan (no `goals/ui-test-*`, no `/tmp/diecast-uitest-*.db`,
no `agent-*` tmux sessions, no orphan Chromium processes with the
`diecast-uitest` user-data-dir marker, no `ui-test-*` rows in the dev DB at
`~/.cast/diecast.db`).

**Acceptance scenarios:**

- **Scenario 1:** WHEN a test session ends (pass or fail), THE TEARDOWN fixture
  SHALL kill the test cast-server process group, delete
  `/tmp/diecast-uitest-<pid>.db`, remove `goals/ui-test-*`, kill any `agent-*`
  tmux session created during the session, and pkill any `diecast-uitest`
  Chromium process.
- **Scenario 2:** IF `:8006` is occupied at session start, THEN THE SYSTEM
  SHALL fail fast with an actionable error naming the conflict — never silently
  pick a different port.

### US4 — Test agents are invisible in dev environment (Priority: P1)

**As a** Diecast developer, **I want** test agents (`cast-ui-test-*`) to be
visible only when the test harness is running, **so that** the dev `/agents`
registry stays signal-rich and I never accidentally invoke a test agent.

**Independent test:** `GET http://127.0.0.1:8005/api/agents` (dev server, no
test env) returns zero entries with `name` matching `cast-ui-test-*`. The same
GET on `:8006` during a test run returns all 9.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the dev cast-server is running without
  `CAST_TEST_AGENTS_DIR` set, THE SYSTEM SHALL exclude `cast-ui-test-*` agents
  from the `/agents` page and from `GET /api/agents`.
- **Scenario 2:** WHEN the test cast-server is running with
  `CAST_TEST_AGENTS_DIR` set to `cast-server/tests/ui/agents/`, THE SYSTEM
  SHALL include `cast-ui-test-*` agents in the registry and in dispatch
  validation paths (`load_agent_config` and `get_all_agents`).

### US5 — Single-command invocation (Priority: P2)

**As a** Diecast developer, **I want to** run the entire harness via one
command, **so that** running tests is friction-free.

**Independent test:** `pytest cast-server/tests/ui/` is the only command
required, after a one-time `uv pip install -r pyproject.toml --extra test` and
`playwright install chromium` (or system Chrome via `channel="chrome"`).

**Acceptance scenarios:**

- **Scenario 1:** WHEN the developer runs `pytest cast-server/tests/ui/`, THE
  SYSTEM SHALL boot a second cast-server on `:8006` against a temp DB, dispatch
  the orchestrator, poll to terminal, surface per-child failures, and tear down
  cleanly.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Harness lives exclusively at `cast-server/tests/ui/`. | One canonical location. No fragmentation. |
| FR-002 | Test cast-server runs on `:8006` against `/tmp/diecast-uitest-<pid>.db` with `start_new_session=True`. | Session-scoped fixture in `conftest.py`. |
| FR-003 | Test agents live exclusively at `cast-server/tests/ui/agents/cast-ui-test-{orchestrator,dashboard,agents,runs,scratchpad,goal-detail,focus,about,noop}/`. | Production `agents/` directory MUST NEVER contain `cast-ui-test-*`. |
| FR-004 | `CAST_TEST_AGENTS_DIR` env var is the sole gate for test-agent visibility. Both `get_all_agents()` (listing) and `load_agent_config()` (dispatch validation) honor it. | Without this env var, behavior is bit-identical to the production registry path. |
| FR-005 | Teardown sweeps process group + temp DB + `goals/ui-test-*` + `agent-*` tmux sessions created during the run + `pkill -f diecast-uitest` Chromium. | Runs in `finally`/autouse so SIGINT-safe. |
| FR-006 | Any change to `cast-server/cast_server/templates/pages/*.html`, `cast-server/cast_server/routes/api_*.py`, or `cast-server/cast_server/templates/fragments/*.html` MUST be paired with a corresponding diff in `cast-server/tests/ui/`. | Enforced via code review; future enhancement: pre-merge gate. |
| FR-007 | Single command: `pytest cast-server/tests/ui/`. No environment activation, no extra flags required for the default case. | `KEEP_UITEST_ARTIFACTS=1` is an opt-in debug flag. |
| FR-008 | Playwright browser uses the `chrome` channel by default (system Chrome), with env-var overrides `CAST_UITEST_BROWSER_CHANNEL` and `CAST_UITEST_BROWSER_EXECUTABLE`. | Workaround for Ubuntu 26.04 Playwright support gap (microsoft/playwright#40117). |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Adding a new screen takes <50 LOC: one new agent dir + one `_assert_<screen>` function + one entry in the orchestrator's child list. | Code review when the next screen lands. |
| SC-002 | Three back-to-back runs leave zero residue. | Post-run shell check + autouse teardown assertion. |
| SC-003 | `cast-ui-test-*` agents are absent from `GET http://127.0.0.1:8005/api/agents` and present from `GET http://127.0.0.1:8006/api/agents` during a test run. | Meta-test `test_registry_visibility.py`. |
| SC-004 | A meaningful UI change without a paired test update is caught at code review. | Reviewer checklist; future: CI gate. |
| SC-005 | A fresh-clone developer can run the harness with one install command and one test command, no other setup. | Documented in `cast-server/tests/ui/README.md`. |

## Open Questions

- **[NEEDS CLARIFICATION: pre-merge gate for FR-006]** — should we add a
  CI/pre-commit check that parses the diff and asserts test-side coverage, or
  rely on reviewer discipline alone? Owner: maintainer.
