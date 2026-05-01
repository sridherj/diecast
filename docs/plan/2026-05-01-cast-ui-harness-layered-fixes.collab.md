---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 0
questions_asked: 0
---

# Plan: Cast-UI Harness Layered Fixes (A → B → C)

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:**
> - `docs/specs/cast-ui-testing.collab.md` (governing spec)
> - `docs/plan/2026-05-01-cast-ui-e2e-test-harness.collab.md` (original harness plan)
> - `cast-server/tests/ui/test_full_sweep.py` (pytest entry)
> - `cast-server/tests/ui/conftest.py` (fixtures)
> - `cast-server/tests/ui/runner.py` (Playwright helper)
> - `cast-server/tests/ui/agents/cast-ui-test-*/` (per-screen agents)
> - `docs/specs/cast-output-json-contract.collab.md` (output filename contract)

## Intent

The `cast-ui-test-harness` plan landed and the harness boots, dispatches, polls, and
tears down cleanly. But running it produces 1/7 children passing — and most of the
6 failures are NOT real UI bugs. They're harness-layer or test-assertion bugs that
mask whatever real issues exist.

This plan removes the failure modes in dependency order so the test's red list becomes
trustworthy. Three layers, executed strictly in order:

- **Layer A — test infrastructure:** the harness must report honestly. Fixed first.
- **Layer B — test assertions:** the children's assumptions about API/UI must match the
  actual implementation. Fixed second, after A surfaces real signal.
- **Layer C — real bugs:** whatever's still red after A+B is genuinely broken in
  cast-server. Investigated last, with proper diagnostics in place.

**Why this order:** A1 unmasks the orchestrator's true status; A2 makes server-side
500s diagnosable; A3 eliminates the networkidle false-positive that's hiding 4 of the
6 current failures. Without A, fixing B is guessing; without A+B, the C list isn't
trustworthy.

## User Stories

### US1 — Honest test reporting (Layer A) (Priority: P1)

**As a** Diecast developer, **I want** `pytest cast-server/tests/ui/` to surface the
orchestrator's true terminal status (currently buried by a wrong filename lookup), the
test cast-server's stdout/stderr on failure (currently captured to PIPE and never read),
and the actual page-load completion (currently masked by `networkidle` timeouts on
HTMX-polling pages), **so that** the failure list reflects reality, not harness blind
spots.

**Independent test:** `pytest cast-server/tests/ui/test_full_sweep.py::test_ui_e2e`
runs against the current code and the failure message contains: (1) the orchestrator's
`status='partial'` (not a stray child's `'completed'`); (2) the test cast-server's
last 200 lines of stdout; (3) zero `networkidle` timeouts in any child's errors.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the e2e test queries the orchestrator's terminal job record,
  THE SYSTEM SHALL read the orchestrator's output JSON from
  `<goal_dir>/.agent-run_<orchestrator_run_id>.output.json` (per
  `cast-output-json-contract.collab.md`), not from a flat `<goal_dir>/output.json`.
- **Scenario 2:** WHEN the e2e test fails for any reason, THE SYSTEM SHALL dump the
  last 200 lines of the test cast-server's combined stdout/stderr to pytest's failure
  output, prefixed with `[test-cast-server stdout]:`.
- **Scenario 3:** WHEN any per-screen child runs `runner.py` against any HTMX-driven
  page, THE SYSTEM SHALL use `wait_until='domcontentloaded'` for `page.goto`, not
  `networkidle`. Per-screen overrides are allowed only if a specific screen genuinely
  requires `load` (none expected today).

### US2 — Test assertions match the real implementation (Layer B) (Priority: P1)

**As a** Diecast developer, **I want** every assertion in the per-screen children to
target a selector or endpoint that actually exists in the implementation, **so that**
test failures point at real product bugs, not at fictional API shapes.

**Independent test:** After Layer A is in place, re-run the harness and inspect each
remaining red child. Each `assertions_failed[]` entry must reference a concrete element
that exists in `templates/pages/<screen>.html`, `templates/fragments/*.html`, or a
route that exists in `cast_server/routes/api_*.py`. No assertion may rely on an
endpoint that returns 404 by design (e.g., a JSON `/api/agents` that doesn't exist).

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-ui-test-agents` asserts agent visibility, THE SYSTEM SHALL
  query a real endpoint (either an HTML fragment route under `/api/agents/*` or the
  page DOM at `/agents`), NOT a non-existent JSON endpoint.
- **Scenario 2:** WHEN `cast-ui-test-scratchpad` asserts the delete flow, THE SYSTEM
  SHALL use a selector that matches the actual delete control rendered by
  `templates/pages/scratchpad.html` (or its fragments).
- **Scenario 3:** WHEN any other child's assertion fails on a "selector not found"
  or "endpoint 404" error after Layer A is fixed, THE SYSTEM SHALL be patched to
  reference the real selector/route, OR the assertion SHALL be removed if the feature
  it tests doesn't exist.

### US3 — Real bugs surface as the only remaining red (Layer C) (Priority: P1)

**As a** Diecast developer, **I want** the post-A+B red list to consist only of
real server/UI bugs, **so that** every remaining failure is actionable as a product
fix rather than a test fix.

**Independent test:** After Layer A and Layer B are in place, re-run the harness.
Every remaining `assertions_failed[]` or `errors[]` entry MUST be reproducible by
manually clicking through the same flow on the dev server at `:8005` (or
`:8006`-test). Anything that's NOT reproducible is a test bug, not a product bug.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a Layer C bug is identified (e.g., `POST /api/goals` returning
  500), THE SYSTEM SHALL be debugged using the test cast-server logs (now surfaced by
  Layer A2) AND a manual reproduction in a browser; THE FIX SHALL be made in the
  product code (`cast_server/routes/`, `cast_server/services/`, etc.), not in the test.
- **Scenario 2:** WHEN the harness eventually reaches `1 passed, 0 failed`, THE
  ORCHESTRATOR'S `output.json` SHALL show `status='completed'` and `summary={"total":7,
  "completed":7,"failed":0,"skipped":0}`.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `_read_orchestrator_output()` in `test_full_sweep.py` reads `<goal_dir>/.agent-run_<orchestrator_run_id>.output.json` (canonical per `cast-output-json-contract.collab.md:35`). The orchestrator's `run_id` is known from the trigger response; the path is constructed deterministically. NEVER read flat `<goal_dir>/output.json`, and NEVER fall back to scanning. If the canonical path is missing, fail loudly — that's a real bug, not a path-resolution problem. | Layer A1. Plan-review #1 resolved: drop the scan fallback. |
| FR-002 | `conftest.py` `test_server` fixture writes the cast-server subprocess's stdout to a tempfile (e.g., `/tmp/diecast-uitest-server-<pid>.log`). The session-scoped autouse `_teardown` fixture, on test failure (detected via `pytest_runtest_makereport` hook), prints the last 200 lines of that log under a clear `[test-cast-server stdout]:` header. The log is deleted on session-clean exit. | Layer A2. Use `pytest_runtest_makereport` to detect failures within the autouse teardown. |
| FR-003 | `runner.py`'s `_run_screen` calls `page.goto(url, wait_until="domcontentloaded")` (was `networkidle`). Per-screen `_assert_<screen>` functions remain free to use `expect(page.locator(...)).to_be_visible(timeout=30_000)` for content-readiness, which auto-waits without depending on networkidle. | Layer A3. Idiomatic Playwright pattern for HTMX/SPA-style apps. |
| FR-004 | After Layers A1–A3 are merged, re-run `pytest cast-server/tests/ui/`. For each child still in `assertions_failed[]`, open `templates/pages/<screen>.html` and `cast_server/routes/api_*.py`, identify the real selector/route, and patch the child's `_assert_<screen>` (in `runner.py`) accordingly. | Layer B. Per-child fix; not a single sweep. |
| FR-005 | After Layers A and B are merged, the remaining red list constitutes the Layer C bug backlog. Each item MUST be tagged with: (a) the failing assertion's name, (b) a manual reproduction recipe, (c) a hypothesis about root cause. Filed as **Diecast tasks** on the existing `comprehensive-ui-test` goal (status='suggested' or 'todo'), one task per bug. | Layer C. Plan-review #2 resolved: tasks (not separate plans) — appropriate for well-scoped, route-level fixes that don't need a design discussion. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | After Layer A: pytest's failure output for `test_ui_e2e` contains the orchestrator's true `status` (`partial` or `completed` or `failed`), NOT a stray child's status. | Inspect pytest output. |
| SC-002 | After Layer A: pytest's failure output contains the test cast-server's last 200 stdout lines under a clear header. | Inspect pytest output on a deliberately-failing run (e.g., kill the server mid-poll). |
| SC-003 | After Layer A: zero `assertions_failed[]` entries reference `Page.goto` `networkidle` timeouts across all children. | Inspect snapshot artifacts at `/tmp/diecast-uitest-debug-*/`. |
| SC-004 | After Layer B: every remaining `assertions_failed[]` entry references a selector or endpoint that exists in the codebase. | Manual walk-through of each child's failures against the templates/routes. |
| SC-005 | After Layer C is enumerated: each Layer C item has a manual reproduction recipe AND lives as a tracked task or sub-plan. | Inspect the resulting tasks/plans. |

## Constraints

- **Layered execution.** Do not skip ahead. Layer A MUST be in place before Layer B
  is touched. Layer B MUST be complete before Layer C investigation begins.
- **No new abstractions.** Each fix is a targeted edit to the file named in its FR.
  No new helper modules, no new test classes, no extracted utilities unless
  duplication is already 3+ identical lines across files.
- **No assertion deletion to make tests green.** If a Layer B assertion is wrong,
  patch it to assert the right thing — don't delete it. The only acceptable deletion
  is if the feature being tested doesn't actually exist (Scenario B3).
- **No silent retries hiding flake.** Don't add `pytest-rerunfailures` to mask
  intermittent issues; flake is a Layer A bug.
- **Plan stays scoped to harness fixes.** Layer C product bugs (e.g., `POST /api/goals`
  500) are enumerated here but fixed in separate plans/tasks.

## Out of Scope

- **Fixing Layer C product bugs.** This plan fixes the harness so the bugs surface
  cleanly; product fixes are downstream work.
- **Adding new test agents or screens.** This plan is repair, not coverage extension.
- **Replacing Playwright or pytest.** Tooling stays as-is.
- **CI integration.** Already out of scope per the parent plan.
- **Adding seed data beyond what each child creates inline.** Already out of scope per
  the parent plan.

## Open Questions

None. All choices in this plan are mechanical / pre-decided.

## Decisions

Plan-review pass (2026-05-01, focused fix-pass, 2 issues across all sections):

- **2026-05-01T00:00:00Z — FR-001 fallback strategy: scan vs deterministic path?** — Decision: deterministic only. Rationale: `cast-output-json-contract.collab.md:35` mandates `<goal_dir>/.agent-run_<RUN_ID>.output.json` as canonical; the orchestrator's run_id is known at trigger time; a scan fallback masks real path-contract bugs.
- **2026-05-01T00:00:00Z — Layer C bug filing: tasks vs plan docs vs umbrella?** — Decision: tasks under `comprehensive-ui-test` goal, one per bug (status='suggested' or 'todo'). Rationale: Layer C bugs are well-scoped route-level fixes; plan docs are too heavy for the per-bug overhead; umbrella plan would mix unrelated concerns.
