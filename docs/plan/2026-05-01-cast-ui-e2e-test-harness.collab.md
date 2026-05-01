---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 0
questions_asked: 6
---

# Plan: Cast-UI E2E test harness (pytest + Playwright + delegating test agents)

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:**
> - `cast-server/cast_server/services/agent_service.py` (registry loader at :1148, `get_all_agents` at :1191)
> - `cast-server/cast_server/routes/api_agents.py` (HTTP trigger surface)
> - `cast-server/cast_server/routes/api_health.py` (readiness probe at `/api/health`)
> - `cast-server/cast_server/templates/pages/{dashboard,agents,runs,scratchpad,goal_detail,focus,about}.html`
> - `skills/claude-code/cast-child-delegation/SKILL.md` (canonical delegation contract — test agents follow this)

## Intent

**Job statement.** When the user has changed UI code (or just wants confidence that
nothing has rotted), they want to invoke a single command that exercises every screen and
every tab of the Diecast UI end-to-end against a real browser, exercises the agent
delegation path while doing so, and leaves no trace afterwards — no goal rows, no run
rows, no files in `goals/`, no DB pollution. Test agent definitions persist; everything
else evaporates.

**Two things are being verified at once:**

1. Every screen at `http://127.0.0.1:8006/` (the test server) loads cleanly, every
   tab/filter responds, and the core CRUD-style flows actually round-trip
   (create goal → see it on dashboard → open detail → switch phase tabs → trigger an
   agent → see the run on the runs page → cleanup).
2. The agent delegation infrastructure (`/api/agents/{name}/trigger` →
   `parent_run_id` → child completion polling) works, by *using* it as the test driver:
   one orchestrator agent fans out to per-screen worker agents, each of which runs
   Playwright-Python against its assigned screen.

**Why this dual-purpose shape rather than a plain pytest harness:** the user explicitly
asked for "test agents with delegation capability, like in `~/workspace/second-brain`."
A pytest-only harness would skip the agent layer the user wants validated by use. The
chosen architecture mirrors `test-parent-delegator` / `test-child-worker` but pointed at
real UI assertions.

## User Stories

### US1 — Single-command UI smoke + functional sweep (Priority: P1)

**As a** Diecast developer, **I want to** run `pytest cast-server/tests/ui/` and have
every screen + tab + core flow exercised against a real browser, **so that** I catch
both load-level regressions and silent flow breakage (e.g., button works but POST 500s)
in one shot, anytime, without affecting my running dev server.

**Independent test:** running `pytest cast-server/tests/ui/` on a fresh checkout
(with the dev server running on `:8000` doing real work) starts a second cast-server
process on `:8006` against a temp SQLite DB, runs all screen tests, exits with `0`
on green, and afterwards: dev server is untouched, temp DB file is gone, no `goals/ui-test-*`
directory exists, no rows for `ui-test-*` slugs in the dev DB.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the developer runs `pytest cast-server/tests/ui/` from the repo
  root, THE SYSTEM SHALL boot a second cast-server process on `127.0.0.1:8006` bound to
  a temp SQLite DB at `/tmp/diecast-uitest-<pid>.db`, with `CAST_TEST_AGENTS_DIR`
  pointed at `cast-server/tests/ui/agents/`, AND poll `GET /api/health` until it
  returns 200 (max 30s) before triggering any agent.
- **Scenario 2:** WHEN the test server is up, THE SYSTEM SHALL POST to
  `http://127.0.0.1:8006/api/agents/cast-ui-test-orchestrator/trigger` with
  `goal_slug=ui-test-<timestamp>`, then poll `/api/agents/jobs/<run_id>` every 5s up
  to 240s for terminal status.
- **Scenario 3:** WHEN the orchestrator returns terminal status, THE SYSTEM SHALL parse
  its `output.json`, assert `status == "completed"` and that every per-screen child
  reached `status == "completed"` with no errors[], and surface per-screen pass/fail
  to pytest.
- **Scenario 4:** WHEN the test run finishes (pass OR fail), THE SYSTEM SHALL kill the
  test server process, delete `/tmp/diecast-uitest-<pid>.db`, `rm -rf goals/ui-test-*`
  in the test repo working tree, and assert teardown cleanliness in a final teardown
  fixture. IF teardown fails, THEN THE SYSTEM SHALL emit a loud pytest warning naming
  the orphaned resource (process, file, dir).
- **Scenario 5:** IF the dev server is running on `:8000`, THEN THE SYSTEM SHALL NOT
  modify it in any way (no requests against it, no DB writes, no file writes outside
  `/tmp` and `cast-server/tests/ui/`'s own working tree).

### US2 — Per-screen worker agents with smoke + functional coverage (Priority: P1)

**As a** developer reading a test failure, **I want** each screen's pass/fail isolated
to its own child agent run, **so that** when `goal_detail` breaks I see exactly that —
not a single red light hiding three orthogonal failures.

**Independent test:** force a known break in one screen (e.g., return 500 from
`/api/goals/{slug}/tab/refinement`). The corresponding child agent (`cast-ui-test-goal-detail`)
fails with a precise error message in its `output.json`; all other children still complete
green; the orchestrator reports `status: partial` and pytest fails with one screen named.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-ui-test-orchestrator` runs, THE SYSTEM SHALL POST to
  `/api/agents/{child}/trigger` for each of these 7 children, in parallel, with
  `parent_run_id` set: `cast-ui-test-dashboard`, `cast-ui-test-agents`,
  `cast-ui-test-runs`, `cast-ui-test-scratchpad`, `cast-ui-test-goal-detail`,
  `cast-ui-test-focus`, `cast-ui-test-about`.
- **Scenario 2:** WHEN a child agent runs, THE SYSTEM SHALL launch a Playwright-Python
  Chromium instance, navigate to its assigned screen, perform smoke assertions
  (HTTP 200, only `level=='error'` or `level=='pageerror'` console messages count
  as failures — `warning`/`info`/`debug` are captured to `console_warnings[]` but
  do not fail the assertion) AND functional assertions (defined per screen below),
  and write `output.json` with structured results including `screen`,
  `assertions_passed[]`, `assertions_failed[]`, `console_errors[]`,
  `console_warnings[]`, `screenshots[]` (only on failure, written into the child's
  goal-dir scratch space which gets cleaned up with the goal).
- **Scenario 3:** WHEN every child has reached a terminal state, THE SYSTEM SHALL
  aggregate into the orchestrator's `output.json` with `status: completed` if all
  children completed cleanly, `status: partial` if any child failed but others
  succeeded, `status: failed` if the orchestrator itself errored.
- **Scenario 4:** IF a child times out (>90s), THEN the orchestrator SHALL mark that
  child as `failed` with a timeout error and continue rather than blocking on it.
  (90s per-child cap keeps total run within the 120s SC-001 budget.)

### US3 — Test agents invisible in dev environment (Priority: P1)

**As a** developer browsing `/agents` in my normal dev session, **I want to** see only
real production agents — not the `cast-ui-test-*` family — **so that** the registry
stays signal-rich and I never accidentally invoke a test agent.

**Independent test:** with the dev server running on `:8000` (without `CAST_TEST_AGENTS_DIR`
set), GET `/api/agents` returns zero entries with `name` matching `cast-ui-test-*`.
With the test server running on `:8006` (with `CAST_TEST_AGENTS_DIR` set), GET
`/api/agents` on `:8006` returns 8 such entries.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `get_all_agents()` (`agent_service.py:1191`) is invoked, IF the
  env var `CAST_TEST_AGENTS_DIR` is set, THE SYSTEM SHALL call `_load_agent_registry()`
  for the production root AND `_load_agent_registry(test_dir)` for the test root,
  merge the two dicts, and return the combined registry. The two roots maintain
  independent caches keyed on their own mtimes; `_load_agent_registry` itself is
  unchanged in shape (still one root, one cache).
- **Scenario 2:** WHEN `CAST_TEST_AGENTS_DIR` is NOT set, THE SYSTEM SHALL behave
  exactly as it does today (no behavior change to the production path —
  `_load_agent_registry` is called once on the prod root, no extra walks, no env
  var read inside the cache hot path).
- **Scenario 3:** WHEN both production and test agents define the same name, THE
  SYSTEM SHALL log a warning and prefer the production entry (defensive — should
  never happen in practice since test names are namespaced `cast-ui-test-*`).

### US4 — Functional flow assertions, not just smoke (Priority: P1)

**As a** developer, **I want** the test to actually create a goal, navigate to it,
trigger an agent, and verify state transitions, **so that** silently broken POSTs
get caught.

**Independent test:** introduce a regression where the "Create Goal" form button
visually works but the backing `POST /api/goals` returns 422. The
`cast-ui-test-dashboard` child SHALL fail with an assertion that the new goal did
not appear in the active-tab list within 5s.

**Acceptance scenarios:**

- **Scenario 1 (dashboard):** WHEN `cast-ui-test-dashboard` loads `/` and clicks each
  of the three tabs (active, inactive, completed), THE SYSTEM SHALL HTMX-swap the goal
  list for each tab without JS console errors.
- **Scenario 2 (dashboard create-goal flow):** WHEN the dashboard child submits the
  "Create Goal" form with slug `ui-test-<timestamp>`, THE SYSTEM SHALL render the new
  goal in the active-tab list within 5s and route a click on it to `/goals/<slug>`.
- **Scenario 2b (dashboard delete-goal flow):** WHEN the dashboard child creates a
  separate throwaway goal `ui-test-delete-<ts>` AND clicks the delete button on its
  card, THE SYSTEM SHALL remove it from the active-tab list within 5s. (Separate
  throwaway so the main test goal remains intact for goal_detail child.)
- **Scenario 3 (goal_detail tabs):** WHEN `cast-ui-test-goal-detail` opens the test
  goal, THE SYSTEM SHALL render 5 tabs (overview + 4 phase tabs), and WHEN each phase
  tab is clicked, THE SYSTEM SHALL HTMX-load and render that phase's content.
- **Scenario 4 (goal_detail trigger flow):** WHEN the goal_detail child triggers
  `cast-ui-test-noop` from the goal page, THE SYSTEM SHALL show a corresponding run
  entry on `/runs` within 5s.
- **Scenario 5 (goal_detail phase advance):** WHEN the test goal status is `accepted`
  AND the goal_detail child clicks a phase-advance button, THE SYSTEM SHALL transition
  to the next phase. IF status is not `accepted`, THEN the child SHALL skip this
  assertion and report it as `skipped` rather than `failed`.
- **Scenario 5b (goal_detail status transition):** WHEN the test goal status is `idea`
  AND the goal_detail child clicks the "accept" button (`hx-vals={"status":"accepted"}`,
  `goal_card.html:42`), THE SYSTEM SHALL transition status to `accepted` and reveal
  the phase controls within 5s.
- **Scenario 5c (goal_detail focus toggle):** WHEN the goal_detail child clicks
  "focus" on the test goal, THE SYSTEM SHALL mark it as focused; WHEN the child then
  clicks "unfocus", THE SYSTEM SHALL clear the focus state within 5s.
- **Scenario 5d (goal_detail task CRUD):** WHEN the goal_detail child opens a phase
  tab AND submits the "create task" form with title `test-task-<ts>`, THE SYSTEM
  SHALL render the new task in that phase within 5s. WHEN the child clicks the
  status-cycle control (todo → in_progress → done), THE SYSTEM SHALL persist each
  transition. WHEN the child clicks delete on the task, THE SYSTEM SHALL remove it
  from the phase within 5s. IF any suggested tasks are present, THEN the child
  SHALL accept exactly one and assert it migrates from `suggested` to `todo`.
- **Scenario 5e (goal_detail artifact CRUD):** WHEN the goal_detail child opens the
  artifact editor for an existing artifact (GET `/api/artifacts/edit`), edits its
  content, AND submits save (PUT `/api/artifacts/save`), THE SYSTEM SHALL persist
  the change AND re-render the artifact in its phase-tab section with the new
  content visible within 5s.
- **Scenario 6 (agents page):** WHEN `cast-ui-test-agents` loads `/agents`, THE SYSTEM
  SHALL return ≥1 entry from `/api/agents`, AND at least one visible card SHALL be a
  `cast-ui-test-*` agent (proves the registry merge worked); WHEN a filter button is
  clicked, THE SYSTEM SHALL toggle card visibility; WHEN a card's details expander is
  clicked, THE SYSTEM SHALL show details.
- **Scenario 7 (runs page):** WHEN `cast-ui-test-runs` loads `/runs` during the test
  session, THE SYSTEM SHALL show the orchestrator's own run in the `running` tab
  while it is executing and in the `completed` tab afterwards; WHEN each of the 4
  status tabs is clicked, THE SYSTEM SHALL filter the run list accordingly; WHEN a
  run row is clicked, THE SYSTEM SHALL show its detail.
- **Scenario 7b (runs page cancel flow):** WHEN the runs child triggers
  `cast-ui-test-noop --sleep=20` AND clicks the cancel button on its row
  (`run_row.html:219`, `hx-post="/api/agents/runs/<id>/cancel"`), THE SYSTEM SHALL
  transition the run to `cancelled` status and surface it in the `failed` (or
  `cancelled`) status tab within 5s.
- **Scenario 8 (scratchpad):** WHEN `cast-ui-test-scratchpad` submits a new entry
  via the form, THE SYSTEM SHALL render that entry in the list; WHEN the child
  deletes the entry, THE SYSTEM SHALL remove it from the list.
- **Scenario 9 (focus):** WHEN `cast-ui-test-focus` loads `/focus`, THE SYSTEM SHALL
  render without JS errors; IF a goal is focused, THEN the focused-goal details SHALL
  render; IF no goal is focused, THEN the "no focus" empty-state SHALL render.
- **Scenario 10 (about):** WHEN `cast-ui-test-about` loads `/about`, THE SYSTEM SHALL
  render the static content with no JS console errors.

### US5 — Re-runnable anytime, idempotent (Priority: P2)

**As a** developer, **I want to** run the suite three times in a row (or 30) and have
each run be independent, **so that** flake debugging is reliable and CI doesn't
accumulate state.

**Independent test:** `for i in 1 2 3; do pytest cast-server/tests/ui/; done` —
all three runs pass independently; no leftover `goals/ui-test-*` after each;
`/tmp/diecast-uitest-*.db` files do not accumulate; ports `:8006` are released
cleanly between runs.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a test run starts, IF `:8006` is occupied (e.g., by a hung
  prior run), THEN THE SYSTEM SHALL fail fast with a clear error naming the conflict
  rather than silently using a different port — surfacing leaks instead of hiding them.
- **Scenario 2:** WHEN a test run is interrupted (SIGINT mid-run), THE SYSTEM SHALL
  still execute teardown via pytest's session-scoped finalizer.
- **Scenario 3:** Each test run SHALL use a unique goal slug (`ui-test-<unix_ts>-<rand4>`)
  and a unique DB path (`/tmp/diecast-uitest-<pid>.db`) to avoid cross-run collisions
  even if teardown failed previously.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `get_all_agents()` (`agent_service.py:1191`) is extended: when `CAST_TEST_AGENTS_DIR` env var is set, it ALSO calls `_load_agent_registry(test_dir)` and merges that result into the production registry before returning. `_load_agent_registry` itself is unchanged (one root, one mtime-keyed cache). The two roots maintain independent caches. | Plan-review Issue #2 resolved: merge happens at the call-site wrapper, not inside `_load_agent_registry`, to keep the production path bit-identical when the env var is unset (no extra walks, no env var read in the cache hot path). |
| FR-002 | `cast-server/tests/ui/conftest.py` provides session-scoped fixtures: `test_server` (boots `:8006` subprocess via `subprocess.Popen([Path(repo_root)/"bin"/"cast-server"], ...)` with `start_new_session=True` so the entire test process tree lives in its own process group; polls `GET http://127.0.0.1:8006/api/health` until 200, max 30s), `test_db_path` (temp file at `/tmp/diecast-uitest-<pid>.db`), `test_goal_slug` (unique per run, format `ui-test-<unix_ts>-<rand4>`). | Plan-review Issue #1 resolved: probe is `/api/health` (the existing endpoint at `api_health.py:18`), not the non-existent `/healthz`. Plan-review Issue #4: process-group launch enables clean teardown sweep. |
| FR-003 | `cast-server/tests/ui/test_full_sweep.py::test_ui_e2e` is the single test entry. It triggers `cast-ui-test-orchestrator`, polls, asserts. | One test = one orchestrator dispatch. Per-screen failures surface via the orchestrator's structured `output.json` rendered as subtests or assertion-message details. |
| FR-004 | 9 test agent definitions live under `cast-server/tests/ui/agents/cast-ui-test-{orchestrator,dashboard,agents,runs,scratchpad,goal-detail,focus,about,noop}/`. Each has a `cast-ui-test-*.md` instructions file and `config.yaml`. The `noop` agent accepts an optional `--sleep=Ns` arg (default 0) and writes output.json with status=completed after sleeping; used both by goal_detail (no sleep) and runs (sleep=20, for the cancel-flow test). All test agents follow the canonical delegation contract from `skills/claude-code/cast-child-delegation/SKILL.md` (orchestrator AND children invoke that skill verbatim). | Plan-review Issue #3 resolved: test agents reference the canonical skill rather than re-implementing the second-brain inline curl pattern, so any drift in the production delegation contract is caught by the tests. |
| FR-005 | Each per-screen child agent invokes the shared Python helper via `python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" --screen=<name> --base-url=http://127.0.0.1:8006 --goal-slug=<slug> --output=<path>`. The `runner.py` is self-contained (no `-m` invocation, no PYTHONPATH plumbing). It captures console messages and FAILS on `level=='error'` or `level=='pageerror'` only; `level=='warning'/'info'/'debug'` are recorded to `console_warnings[]` but do not fail. Each screen has a `_assert_<screen>(page, ctx)` function. | Plan-review Issue #5 resolved: direct script-path invocation eliminates module-import ambiguity from agent subprocess working dirs. Plan-review Issue #6 resolved: severity-only filter (no allowlist) prevents day-1 flake on benign warnings. |
| FR-006 | Teardown fixture (session-scoped, `autouse=True`, `try/finally`-style, SIGINT-safe): (1) sends SIGTERM to the test-server process group, waits 5s, escalates to SIGKILL if needed; (2) deletes `/tmp/diecast-uitest-<pid>.db`; (3) `rm -rf goals/ui-test-*`; (4) post-teardown sweep: `pkill -f 'chromium.*--remote-debugging-port=<test-port-range>'` against a clearly-scoped pattern that cannot match dev-session browsers; (5) asserts no orphaned resources, surfaces warnings naming any swept process/file/dir. | Plan-review Issue #4 resolved: process-group + post-sweep covers SIGINT-killed children whose `finally: browser.close()` didn't run; sweep pattern is namespace-scoped to test ports only. |
| FR-007 | `cast-server/tests/ui/README.md` documents: how to run, what it does, where the agent definitions live, how to add a new screen. | One screen test should be ≤30 lines to add. |
| FR-008 | Playwright Python is added as a dev dependency in `pyproject.toml` under `[project.optional-dependencies] test`. Browser binaries fetched via `playwright install chromium` (documented in README, not auto-run). | Don't auto-install browsers — keep CI/dev opt-in. |
| FR-009 | `cast-server/tests/ui/test_registry_visibility.py` is a fast meta-test (<1s, no browser): asserts `_load_agent_registry()` with default args returns ZERO `cast-ui-test-*` keys, and `get_all_agents()` with `CAST_TEST_AGENTS_DIR` set to the test dir returns ALL 9 test-agent names. Backstops the registry-visibility success criterion. | Plan-review Issue #9: independent gate on the registry-merge logic, separate from the slow E2E test. |
| FR-010 | Flake resilience: Playwright's auto-wait + per-assertion 30s timeout (overridable per-screen). `pytest-rerunfailures` configured with `--reruns=2` ONLY for tests tagged `@pytest.mark.flaky` — never blanket. Default behavior: zero retries, flake is surfaced not hidden. | Plan-review Issue #11: opt-in retries keep the suite honest while accepting that real-world UI tests have legitimately racy moments. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | `pytest cast-server/tests/ui/` exits 0 on a clean checkout in <120s wall-clock (90s per-child polling cap + ~20s harness setup/teardown ≈ 110s budget). | Time the run; assert `< 120s` in CI. |
| SC-002 | After 3 consecutive runs, no `ui-test-*` rows in dev DB, no `/tmp/diecast-uitest-*` files, no `goals/ui-test-*` dirs, no listening processes on `:8006`. | Post-run shell check; assertion in teardown fixture. |
| SC-003 | Test agents are absent from `GET http://127.0.0.1:8000/api/agents` (dev server, no env var) and present on `GET http://127.0.0.1:8006/api/agents` during test run. | `test_registry_visibility.py` meta-test. |
| SC-005 | Adding a new screen requires <50 LOC: one new agent dir + one `_assert_<screen>` function + one entry in the orchestrator's child list. | Code review when the next screen lands. |

## Constraints

- **No mutation of dev state.** The test harness MUST NOT touch the dev server on
  `:8000`, the dev DB at `~/.cast/diecast.db`, or the production `agents/` directory.
- **No new languages.** Python only. Playwright Python (not Node Playwright Test).
- **No browser auto-install.** `playwright install chromium` is a documented manual
  step, not a side-effect of `pytest`.
- **Single-process server.** The test server is one `cast-server` subprocess; no
  Docker, no compose, no migration ceremony beyond what `cast-server` does on first
  start against a fresh DB.
- **Determinism over speed.** If a 5s wait makes a flaky assertion solid, take the
  5s. Target run time is <120s but not at the cost of flakiness.
- **No screenshot-diff baselines.** Screenshots only captured on failure for
  postmortem; not used for regression comparison (deferred — see Out of Scope).
- **Plan lives outside `goals/`.** This plan is `docs/plan/2026-05-01-cast-ui-e2e-test-harness.collab.md`,
  not a Diecast goal — explicit user instruction.

## Out of Scope

- **Visual regression / screenshot diffing.** Considered in Q1 and rejected; revisit
  if smoke+functional misses real UI breakage in practice.
- **Cross-browser coverage.** Chromium only. Firefox/WebKit deferred until smoke
  assertions are stable on Chromium for ≥2 weeks.
- **Mobile viewport / responsive testing.** Desktop-width only.
- **Accessibility audits (axe-core, lighthouse).** Separate workstream.
- **Performance budgets.** No latency/payload-size assertions beyond "page loads in
  <10s timeout."
- **CI integration.** Out of scope for this plan; runs on developer machine. Adding to
  GitHub Actions is a follow-up once stable locally.
- **Test data factories beyond what each screen needs.** No fixture seed-data spread
  across the suite — each child creates and verifies its own scoped data.
- **Wiring the test harness into `setup`.** Setup remains a production install path;
  the test harness is a developer tool only.
- **Replacing existing pytest tests.** This is additive; existing `cast-server/tests/`
  unaffected.

## Open Questions

None. Both prior open items resolved in-conversation per US13:

- **Q#5 (Playwright execution location):** Resolved — Playwright runs inside each child
  agent's subprocess (current plan shape). Each child shells out to
  `python -m tests.ui.runner --screen=<name>`. Trade-off acknowledged: 7 parallel
  browser launches is heavier than a single pytest-driven browser, but the user
  explicitly preferred true "test agent does the work" semantics over harness
  simplicity.
- **Q#6 (goal_detail trigger target):** Resolved — adding `cast-ui-test-noop` as the
  9th test agent (see FR-004). Used exclusively by the `cast-ui-test-goal-detail`
  child to assert the trigger → runs-page flow. Smallest possible surface for the
  assertion; lives in the test-only agents dir so invisible in dev.

## Decisions

Plan-review pass (2026-05-01, BIG mode, 18 issues across 4 sections + coverage gaps):

- **2026-05-01T00:00:00Z — #1 Wrong readiness probe (`/healthz` doesn't exist)** — Decision: Fix to `/api/health`. Rationale: endpoint already exists at `api_health.py:18`; pure spec correction.
- **2026-05-01T00:00:00Z — #2 Cache invalidation when CAST_TEST_AGENTS_DIR is set** — Decision: Merge at the `get_all_agents` call site, keep `_load_agent_registry` pure (one root, one cache). Rationale: production path stays bit-identical when env var unset; two roots get independent mtime caches.
- **2026-05-01T00:00:00Z — #3 Test agents bespoke pattern vs canonical skill** — Decision: Test agents reference `cast-child-delegation` skill verbatim. Rationale: tests catch drift between the canonical contract and inline patterns; aligns with US3 "test agents merge into the same registry."
- **2026-05-01T00:00:00Z — #4 Orphan Chromium processes across many runs** — Decision: process group launch (`start_new_session=True`) + finally-blocks in runner.py + post-teardown sweep with port-scoped pattern. Rationale: belt-and-suspenders covers SIGINT case where finally bypassed.
- **2026-05-01T00:00:00Z — #5 Runner invocation path** — Decision: direct script path (`python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" ...`) not `python -m`. Rationale: agent subprocess working dirs make `-m` resolution ambiguous; direct path is explicit.
- **2026-05-01T00:00:00Z — #6 Console-error allowlist vs severity filter** — Decision: severity-only filter (fail on `error`/`pageerror`, capture warnings to a separate field). Rationale: allowlists drift and start hiding real bugs; severity is a stable signal.
- **2026-05-01T00:00:00Z — #7 Test data ownership (auto-buffered)** — Decision: dashboard child creates the goal first; orchestrator dispatches dashboard, polls to completion, then triggers the rest in parallel. Goal slug shared via `test_goal_slug` fixture. Rationale: avoids race; centralizes goal creation.
- **2026-05-01T00:00:00Z — #8 Subprocess termination of bash wrapper (auto-buffered)** — Decision: `start_new_session=True` + SIGTERM-to-PGID + 5s grace + SIGKILL escalation. Rationale: bash `exec uvicorn` makes signals propagate, group-kill catches grandchildren.
- **2026-05-01T00:00:00Z — #9 SC-003 meta-test (auto-buffered)** — Decision: add `test_registry_visibility.py` (<1s, no browser) as FR-009. Rationale: fast independent gate on the registry merge logic.
- **2026-05-01T00:00:00Z — #10 Regression-injection mechanism for SC-004** — Decision: drop SC-004 entirely (manual smoke only). Rationale: user explicitly accepted manual coverage for fault-injection rather than carry monkey-patch or middleware backdoor.
- **2026-05-01T00:00:00Z — #11 Flake resilience (auto-buffered)** — Decision: Playwright auto-wait + 30s per-assertion timeout + opt-in `pytest-rerunfailures` only for tests tagged `@pytest.mark.flaky` (FR-010). Rationale: surface flake, don't hide it; explicit opt-in for known-racy cases.
- **2026-05-01T00:00:00Z — #12 240s polling cap vs 120s SC-001 budget (auto-buffered)** — Decision: per-child cap reduced to 90s. Rationale: matches SC-001 budget arithmetic; if a child takes >90s something is genuinely wrong.
- **2026-05-01T00:00:00Z — #13 Parallelism throttle for 7 Chromium instances** — Decision: no throttle, 7 in parallel. Rationale: ~1.4GB peak RAM is acceptable on developer hardware; throttling triples wall-clock and breaks SC-001.
- **2026-05-01T00:00:00Z — #14 LLM call cost (info-only, auto-buffered)** — Decision: 8 LLM calls per run (1 orchestrator + 7 children) accepted as the cost of the architecture chosen in Q#2. Rationale: documented; not actionable.
- **2026-05-01T00:00:00Z — #15 Task CRUD coverage gap** — Decision: full task CRUD (create/status-cycle/delete/accept-suggestion) added inside goal_detail child (US4 Scenario 5d). Rationale: tasks live within phase tabs; one agent owns the screen and its task ops atomically.
- **2026-05-01T00:00:00Z — #16 Goal lifecycle ops (auto-buffered)** — Decision: focus/unfocus + idea→accepted transition added to goal_detail child (Scenarios 5b, 5c); separate `ui-test-delete-<ts>` throwaway in dashboard child for delete-button flow (Scenario 2b). Rationale: matches user's "all operations on screen" requirement; throwaway preserves the main test goal.
- **2026-05-01T00:00:00Z — #17 Run cancellation flow (auto-buffered)** — Decision: extend `cast-ui-test-noop` with `--sleep=Ns` arg; runs child triggers `noop --sleep=20`, cancels via UI button, asserts `cancelled` status (Scenario 7b). Rationale: cancel button exists at `run_row.html:219`; minimal surface change to noop agent.
- **2026-05-01T00:00:00Z — #18 Artifact CRUD coverage gap** — Decision: artifact editor flow added to goal_detail child (Scenario 5e): open editor, edit, save (PUT `/api/artifacts/save`), assert clean re-render. Rationale: artifacts are a real surface (`api_artifacts.py`, `artifact_editor.html`); user explicitly requested coverage.
