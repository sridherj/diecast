# Rate-Limit Auto-Restart — Implementation Map & Test Recipe

Reference material for `cast-server/tests/test_rate_limit_recovery.py` and any
future change to the rate-limit recovery path. Authored 2026-04-30 as part of
Phase 3b sp6 (per Q#18 / T1 lock — mock at the narrowest boundary, not at
`subprocess.Popen`).

## Implementation map

The dispatcher's auto-restart path is a polling loop that reads tmux pane
content, detects a rate-limit message, parses a reset time, waits, and sends
`Enter` to the still-running Claude CLI session. **No subprocess re-spawn is
required:** the same Claude tmux pane resumes on `Enter` after the API limit
clears. This is significant for tests — the canonical mock boundary is the
state-detection function, not the spawn pipeline.

### Detection

| Stage | File | Key symbol | Notes |
|-------|------|------------|-------|
| Pane regex match | `cast_server/infra/state_detection.py` | `RATE_LIMIT_PRIMARY` (`hit your limit`, `you've hit your`) and `detect_agent_state` | Returns `AgentState.RATE_LIMITED` when any primary pattern matches captured pane lines. The reset-time regex (`RATE_LIMIT_RESET`) is **not** load-bearing for detection — a primary match alone is sufficient. |
| Reset-time parsing | `cast_server/infra/rate_limit_parser.py` | `parse_rate_limit_reset(pane_text)` | Extracts a resume datetime from the captured pane text. Recognises `resets at Xpm` / `resets at X:YYpm` and `try again in N min`. Falls back to `now() + 15min` (`FALLBACK_COOLDOWN_MINUTES`) when neither pattern matches. Both successful matches add `BUFFER_MINUTES = 2`. |

### Trigger condition

`cast_server.services.agent_service._check_all_agents` (currently at
`agent_service.py:1753`) runs every `AGENT_MONITOR_INTERVAL` seconds, captures
the last 15 lines of each agent's tmux pane, and calls `detect_agent_state`.
When the result is `AgentState.RATE_LIMITED`, the state-transition handler
fires.

### Auto-restart fires here

`cast_server.services.agent_service._handle_state_transition` —
the `state == AgentState.RATE_LIMITED` branch (currently at
`agent_service.py:1857`).

Branching on the run's *current* persisted status:

* **First detection** (`run["status"] != "rate_limited"`):
  1. Capture 30 lines of pane content.
  2. Call `parse_rate_limit_reset(pane_text)`.
  3. Set in-memory `_cooldown_until[run_id] = resume_at`.
  4. `update_agent_run(run_id, status="rate_limited")`.
  5. Seed `_current_pause[run_id]` with `started_at` + `reset_time_parsed`.
* **Subsequent ticks while still RATE_LIMITED** (`run["status"] == "rate_limited"`):
  1. Read `_cooldown_until[run_id]`. If `datetime.now() >= resume_at`:
  2. `tmux.send_enter("agent-{run_id}")` — wakes the same Claude pane.
  3. `update_agent_run(run_id, status="running")`.
  4. Stamp `_current_pause[run_id]` with `ended_at` + `duration_seconds`,
     append it to the JSON array stored in `agent_runs.rate_limit_pauses`.
  5. Increment `_total_paused[run_id]` (used to back out paused time from
     `active_execution_seconds`) and clear cooldown bookkeeping.

### State touched

| State | Where | Lifecycle |
|-------|-------|-----------|
| `_cooldown_until[run_id]` | module-level dict in `agent_service.py` | seeded at first detection, cleared on resume |
| `_current_pause[run_id]` | module-level dict | seeded with `started_at` / `reset_time_parsed`, sealed with `ended_at` / `duration_seconds` on resume |
| `_total_paused[run_id]` | module-level dict | accumulates pause durations across multiple rate limits |
| `agent_runs.status` | SQLite via `update_agent_run` | flips `running → rate_limited → running` |
| `agent_runs.rate_limit_pauses` | SQLite (TEXT, JSON array) | new pause appended on each resume |

### Spawn re-entry

There is **no second-attempt subprocess**. The Claude CLI process inside the
tmux pane stays alive while it shows the rate-limit message; the dispatcher
simply sends a literal `Enter` keystroke
(`tmux send-keys -t agent-{run_id} Enter`) once the cooldown elapses, which
Claude consumes as "retry the last action." The single live primitive is
therefore `TmuxSessionManager.send_enter`.

### Default backoff

`FALLBACK_COOLDOWN_MINUTES = 15` in
`cast_server/infra/rate_limit_parser.py`. When `parse_rate_limit_reset` cannot
extract a reset time, it returns `datetime.now() + timedelta(minutes=15)`
(no extra buffer). The dispatcher writes that value straight into
`_cooldown_until[run_id]`, so `now + 15min` is also the dispatcher's
effective default.

`BUFFER_MINUTES = 2` is added when either reset-time pattern *does* match;
the buffer is **not** applied to the fallback.

## Mock boundary chosen for the regression test

Pane → `detect_agent_state` → `parse_rate_limit_reset` → `_cooldown_until` →
`tmux.send_enter`.

The test in `cast-server/tests/test_rate_limit_recovery.py` mocks at the
state-detection boundary: it patches
`cast_server.services.agent_service.detect_agent_state` to return a scripted
sequence of `AgentState` values and patches
`cast_server.services.agent_service._get_tmux` to return a `MagicMock`
session manager. `parse_rate_limit_reset` is **not** mocked in the
positive-path test — feeding it real "you've hit your limit … try again in
1 min" text exercises the parser end-to-end and lets the dispatcher write a
parser-derived value into `_cooldown_until`, which the test then asserts on.
The negative-case test calls `parse_rate_limit_reset` directly with an
unparseable message to confirm the 15-minute fallback contract still holds.

This mock boundary is strictly narrower than `subprocess.Popen` (per Q#18)
and avoids the temptation to re-implement the dispatcher in the test.

## Manual pre-launch verification

The integration test only proves the recovery path is correctly wired in
isolation. Before any release that changes the rate-limit code, run the
manual recipe below against a real Claude CLI to confirm end-to-end behaviour.

### Trigger a real rate limit

1. Make sure your Anthropic account is on a tier where you can deliberately
   exhaust the limit (low-tier dev key or a saturated higher-tier account).
2. Start `cast-server` locally (`bin/cast-server`).
3. Trigger a long-running agent that issues many model requests in tight
   succession — e.g. dispatch a `cast-orchestrate` run on a goal with several
   children, or post repeatedly to `POST /api/agents/{name}/trigger` until
   Claude returns the rate-limit banner in the tmux pane.

### Expected dispatcher behaviour

* Server log records `Agent <name> (<run_id>) rate limited. Resume at HH:MM`
  (the `logger.info` call inside the RATE_LIMITED branch).
* `GET /api/agents/jobs/{run_id}` reports `status = rate_limited`.
* No new tmux session is created for the rate-limited run.
* When the parsed reset time elapses, the next monitor tick logs
  `Agent <name> (<run_id>) resumed after rate limit`, the status flips back
  to `running`, and the same tmux pane resumes Claude output (the agent
  continues from where it paused, not from a fresh prompt).
* `agent_runs.rate_limit_pauses` (visible via `cast-server` UI or a direct
  `sqlite3` query) gains one entry with `started_at`, `ended_at`,
  `duration_seconds`, and `reset_time_parsed`.

### How to confirm the auto-restart fired

Pick any one of the following — all three are independent corroboration:

* `tmux capture-pane -p -t agent-<run_id>` — Claude output continues past the
  rate-limit banner.
* SQLite: `SELECT status, rate_limit_pauses FROM agent_runs WHERE id = '<run_id>'`
  — status is back to `running`, JSON array has one or more pauses.
* Server log — pair of `rate limited … Resume at HH:MM` and `resumed after
  rate limit` lines for the same run id.

If any of those is missing, treat the rate-limit recovery as broken even when
the integration test passes — the fast pytest-level mock cannot cover real
tmux pane decoding, real Claude CLI banner formatting, or real-world clock
drift around the parsed reset time.

## See also

* `cast_server/services/agent_service.py` — `_handle_state_transition`
* `cast_server/infra/state_detection.py` — `detect_agent_state`
* `cast_server/infra/rate_limit_parser.py` — `parse_rate_limit_reset`
* `cast_server/infra/tmux_manager.py` — `TmuxSessionManager.send_enter`
* `cast-server/tests/test_rate_limit_recovery.py` — regression test
* `cast-server/tests/conftest.py` — shared fixtures (extended in sp6_5)
