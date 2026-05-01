# Review Summary: Cast-UI E2E Test Harness

The plan was already lint-clean against `cast-spec.template.md` and shipped with a full
plan-review pass (18 issues resolved on 2026-05-01). The split into sub-phases surfaced a
small number of concrete gaps and assumptions the executing contexts will need to confirm.
None are blocking; all are tactical.

## Open Questions

1. **Cast-server env-var contract.** The plan asserts `bin/cast-server` accepts overrides for
   the listening host, port, and SQLite DB path, but does not name the exact env vars.
   sp2's fixture currently assumes `CAST_HOST`, `CAST_PORT`, `CAST_DB_PATH`. If the entry
   script uses different names (e.g., `DIECAST_*`, or relies on CLI flags), sp2 must adapt.
   *Action:* sp2 reads `bin/cast-server` first and confirms; if the entrypoint lacks env-var
   overrides for any of host/port/db, sp2 either adds them in-script or switches to CLI flags.

2. **`AgentDefinition` shape and `config.yaml` schema.** sp1's collision test wants to assert
   the production entry "wins" but it's unclear whether `AgentDefinition` exposes a stable
   `source_path`/`directory` field. sp4a/sp4b's `config.yaml` examples are best-guess; the
   actual schema (required keys, type validation) lives in the agent loader.
   *Action:* sp1 inspects the dataclass; sp4a/sp4b mirror an existing production agent's
   `config.yaml` exactly.

3. **`${DIECAST_ROOT}` in agent subprocesses.** FR-005 invokes runner.py via
   `python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" ...`. It's not stated whether the
   cast-server agent runtime sets this env var when executing children. If not, sp4b's
   instructions need a fallback (absolute path to repo root, or `pwd`-based discovery).
   *Action:* sp4b inspects an existing production agent that shells out to a script; mirrors
   its convention.

4. **Job-poll response shape.** sp5's `_poll_to_terminal` and `_read_orchestrator_output`
   guess the response keys (`run_id`, `id`, `output_path`, `output_json_path`, `goal_slug`,
   `slug`). The actual `GET /api/agents/jobs/<run_id>` schema is not enumerated in the plan.
   *Action:* sp5 hits the endpoint once during development and adapts the keys.

5. **Cancel-button selector stability.** US4 Scenario 7b cancels a run via the button at
   `run_row.html:219`. Line numbers drift; selector identity is what survives. The plan
   references `hx-post="/api/agents/runs/<id>/cancel"` which is a usable attribute selector,
   but the runner needs to assert post-cancel UI state. The plan does not specify whether
   the cancel produces a `cancelled` row visible in the `failed` tab or in a dedicated
   `cancelled` tab.
   *Action:* sp3 verifies the post-cancel UI behavior live during runner.py implementation.

6. **Artifact CRUD round-trip details.** Scenario 5e specifies `GET /api/artifacts/edit` to
   open the editor and `PUT /api/artifacts/save` to save, but the plan does not document the
   request payloads or whether the editor is a modal vs. a page. Selector strategy will
   depend on which.
   *Action:* sp3 inspects `cast_server/routes/api_artifacts.py` and `artifact_editor.html`
   during runner.py implementation.

## Review Notes by Sub-Phase

### sp1_registry_extension
- The collision-test contract leaves the production-wins assertion soft (logged warning
  only) when `AgentDefinition` doesn't expose a source path. This is acceptable —
  production-wins is enforced by the `merged[name] = prod_entry` line, and the warning is
  the observable symptom.
- The third meta-test is conditionally skippable when the prod registry happens to be
  empty. Document the skip path.

### sp2_test_infra_fixtures
- The `pkill -f diecast-uitest` sweep substring is shared with sp3's `USER_DATA_DIR_PREFIX`.
  If either sub-phase changes the substring, both must move in lockstep — flagged in both
  sub-phase docs.
- `REPO_ROOT = Path(__file__).resolve().parents[3]` depends on the test file's depth; sp2
  should add a `print` once during development to verify the count is right.

### sp3_runner_helper
- The runner is the single largest deliverable and the place where flake comes from. The
  sub-phase plan emphasizes selector verification (Step 3.6) and per-assertion 30s timeouts
  to mitigate.
- `launch_persistent_context` was chosen so the user-data-dir is a deterministic substring;
  if the implementation switches to `launch_browser` the sweep pattern in sp2 must also
  change.

### sp4a_test_agents_orchestrator_noop
- Decision #3 (canonical skill, not inline curl) is restated in the sub-phase plan and in
  the success criteria. Tempting to inline a curl example "for clarity" — don't; that's
  exactly the drift the decision was designed to prevent.
- `visible: true` is required so US4 Scenario 6 (assert at least one `cast-ui-test-*` card
  visible) is observable. Without `CAST_TEST_AGENTS_DIR`, the agents don't load at all, so
  visibility doesn't leak into dev.

### sp4b_test_agents_screens
- 7 near-identical files; the sub-phase plan recommends authoring one template, then mass-
  producing. Re-validate that the resulting files are not so identical that they could be
  generated from a single source — if so, generation is fine, but check in the materialized
  files (the agent loader walks a directory tree, not a generator).

### sp5_e2e_test_and_readme
- The pytest-side outer timeout (240s) is comfortably above the orchestrator-side per-child
  cap (90s × parallel = ~90s + dashboard 90s = 180s worst case). Tightening 240s to ~210s
  would surface latent slow paths sooner; leaving it 240s is the safer first-week setting.
- The manual fault-injection smoke (Step 5.5) is a one-time check, not a permanent test.
  Decision #10 explicitly accepted manual coverage; do NOT promote this to a CI-tracked test.

## Default Choices Made

The split was straightforward; only a handful of design defaults needed to be picked:

- **Sub-phase boundaries.** Six sub-phases (5 + a parallel pair). Could have been four
  if sp4a+sp4b merged, but keeping them split lets two contexts work in parallel and
  keeps each context smaller.
- **No decision gates.** The plan is mechanical post-review — no human judgment points
  remain. Every fork was resolved during plan review.
- **Parallel groups in execution.** sp1, sp2, sp3 are independent (disjoint files).
  sp4a, sp4b are independent (disjoint agent directories). sp5 is the funnel.
- **Per-screen agent dir naming.** Followed the plan's `cast-ui-test-<screen>` naming
  exactly, including the dash in `goal-detail` (runner.py normalizes the dash internally).
- **Verification weight.** Each sub-phase plan dedicates ~30-40% of its body to verification
  (per the create-execution-plan canon); the e2e sub-phase (sp5) leans heavier on manual
  validation since the suite IS its own verification.
- **No new sub-phase for "wire up CI."** The plan explicitly puts CI integration out of
  scope; honored.

## Concerns / Gaps to Flag to the User

These are not blockers but warrant a heads-up.

1. **Selector fragility in `goal_detail` is concentrated.** The most assertion-dense screen
   has 8 distinct flows (5 tabs + accept/focus/task-CRUD/artifact-CRUD/trigger). If the UI
   refactors any of those, the goal_detail child becomes a single noisy failure. Consider
   splitting goal_detail into per-tab children later if churn is high — but doing so now
   would violate the "one agent owns the screen" decision (#15/#16/#18).

2. **240s polling cap vs. SC-001 120s wall-clock.** The pytest-side cap (240s in the test
   file) is loose relative to the SC-001 budget (120s). On a healthy run, 120s holds; on
   a borderline run, the test will pass but exceed SC-001 silently. Recommend adding a
   wall-clock assertion to `test_ui_e2e` if SC-001 is a hard requirement (it would catch
   slow regressions). Not adding by default to avoid environmental flake on slow dev
   machines.

3. **Browser-binary install is documented as manual** (Decision/FR-008). If a developer
   skips `playwright install chromium`, the failure mode is a Python exception inside
   runner.py during a child run — surfaced via the orchestrator's per-child failure but
   somewhat indirect. The README troubleshooting section names this; consider also adding
   a friendlier preflight in `conftest.py` that imports playwright and checks for the
   browser binary, raising a clear error before the test server even boots. Cheap to add
   in sp2 if desired.

4. **Test-server health is `/api/health`, but is the response shape stable?** The plan only
   asserts HTTP 200. If `/api/health` ever returns 200 with a body that contains
   `{"status": "degraded"}`, the suite will run against a half-broken server. Consider
   asserting body content too. Marginal; not worth blocking on.

5. **`pkill -f diecast-uitest` runs as the test user.** If the user has a dev tool that
   happens to include the substring `diecast-uitest` in its argv (extremely unlikely but
   possible), the sweep will kill it. The substring is specific enough that this is not
   a real-world concern — flagging only because the sweep is unconditional.

6. **No coverage of the cast-server "first run launch" flow** that the in-flight branch
   `wip: cast-server first-run-launch + terminal-intelligent-defaults` introduces. If
   that flow ships before this harness, the test server's first boot may include a
   "terminal intelligent defaults" prompt that blocks waiting on stdin. Worth confirming
   that `bin/cast-server` is non-interactive when CAST_PORT/CAST_DB_PATH are pre-set.
