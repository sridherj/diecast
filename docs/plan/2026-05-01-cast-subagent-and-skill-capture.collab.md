# Cast Subagent and Skill Capture: Capture Task() Subagents + Skills

## Overview

Closes the third leg of the runs-tree trilogy. Sibling plans have shipped: user-typed
`/cast-*` slash commands are captured as roots
(`cast-server/cast_server/services/user_invocation_service.py`) and the threaded tree
renders (`docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`). This plan adds the
remaining capture path: `Task()`-dispatched `cast-*` subagents and the skills they
invoke. **Spike A captured the live payload shapes** — see
`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` for verbatim
examples and a field summary table. Empirical reality differs from the original
design assumption: there is **no `parent_session_id` field**; instead, Claude Code
supplies an `agent_id` (unique per subagent) and reuses the parent main-loop's
`session_id` for every subagent in that session. Parent attribution therefore uses
"most-recent running cast-* row in `session_id`" — what the plan originally framed
as a fallback is now the primary path. The new `agent_id` column on `agent_runs`
keys SubagentStart ↔ SubagentStop closure exactly. `skills_used` is the second new
column. Skills are captured via `PreToolUse` matcher `"Skill"` (payload field
`tool_input.skill`, singular — NOT `skill_name`) and surfaced as compact chips at
L2 / detailed list at L3 in the runs UI.

## Operating Mode

**HOLD SCOPE** — Requirements are precise and locked, with explicit out-of-scope
deferrals to v2 (no MVP/spike/prototype signals; no 10x/explore/comprehensive
signals). Bulletproof every spec'd behavior, exhaustive edge-case mapping, no kitchen
sink. Sibling plan shipped during the review pass; this rewrite reflects current
codebase reality, not a forecast.

## Pre-existing Surface (read before planning)

Sibling work already on disk — this plan extends, never duplicates:

- `cast-server/cast_server/services/user_invocation_service.py` — `register()` writes
  rows with `input_params.source="user-prompt"`, `goal_slug="system-ops"`, and
  populates `agent_runs.session_id` with Claude's session id. `complete()` closes by
  `session_id` + JSON discriminator + 1-hour staleness window.
- `cast-server/cast_server/cli/hook_events.py` — **canonical** `(event, subcommand,
  handler)` registry. Comment on line 4: "Adding a new hook event = one line in this
  file." Both `install_hooks.py` and `hook.py` iterate from it.
- `cast-server/cast_server/cli/hook.py` — `cast-hook` console-script entry point.
- `cast-server/cast_server/cli/hook_handlers.py` — handler implementations; defines
  `PROMPT_PATTERN = re.compile(r"^\s*/(cast-[a-z0-9-]+)")` and `_post()` /
  `_read_payload()` helpers. Default port `CAST_PORT=8005`.
- `cast-server/cast_server/cli/install_hooks.py` — idempotent settings.json injector
  iterating `HOOK_EVENTS`; HOOK_MARKER `"cast-hook "`. Currently emits flat entries
  with no per-event `matcher` support.
- `cast-server/tests/test_install_hooks.py`, `test_cli_hook.py` — extend, don't fork.
- Endpoints live under `/api/agents/user-invocations` (POST start, POST `/complete`).
- `agent_runs.session_id` column exists and IS being populated. A composite
  `idx_agent_runs_session_status ON agent_runs(session_id, status)` already
  exists (`cast-server/cast_server/db/connection.py` `_run_migrations()`) and
  fully covers sp1's lookup pattern (`WHERE session_id = ? AND status =
  'running'`); sp1 does NOT need to add a single-column `idx_agent_runs_session_id`.
- **`system-ops` goal seed has been landed already** in `_run_migrations()` via
  a new `_seed_system_goals(conn)` helper (idempotent `INSERT OR IGNORE`).
  Live DB also has the row inserted out-of-band so the running server doesn't
  need a restart to begin honoring sibling's `register()`. sp1's auto-seed
  activity is therefore done; sp1 retains the verification test
  (`test_system_ops_seed_idempotent`) to lock the contract.

## Sub-phase 1: Foundation — payload spike + schema migration + system seeds

**Outcome:** `agent_runs` has a new `skills_used TEXT DEFAULT '[]'` column. Parent
resolution is fast via the pre-existing composite index
`idx_agent_runs_session_status ON agent_runs(session_id, status)` — no new index
needed. The `system-ops` goal is auto-seeded (already shipped in
`_seed_system_goals`) so sibling and this plan can write rows without FK
violations; sp1 keeps the idempotency test as the lock. SQLite 3.9+ is enforced at
startup so `record_skill` can rely on `json_insert(... '$[#]' ...)` without
fallback. The shared cast-name pattern AND the input-source discriminator
constants live in dedicated modules for downstream reuse. The actual
`SubagentStart`, `SubagentStop`, and `PreToolUse(Skill)` payload shapes are
empirically captured and pinned in this sub-phase's notes.

**Dependencies:** None.

**Estimated effort:** 1 session.

**Verification:**

- Fresh-DB test in `cast-server/tests/test_schema_migration.py`: schema has `skills_used` column; pre-existing composite `idx_agent_runs_session_status` is left intact (no new single-column index added).
- Live-DB test: copy `~/.cast/diecast.db` to a tmp path, restart cast-server pointing at it — migration is idempotent (no errors, no extra rows).
- `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` exists with verbatim live captures.
- `pytest cast-server/tests/test_cast_name_pattern.py` green; existing `test_cli_hook.py` tests still green after the import refactor.
- `pytest cast-server/tests/test_invocation_sources.py` green.
- **`test_system_ops_seed_idempotent`** green: fresh DB → goal exists; pre-existing DB without goal → goal added; pre-existing goal → no error, no duplicate.
- **`test_sqlite_version_check_rejects_old_versions`** green: monkeypatch `sqlite3.sqlite_version_info` to `(3, 8, 0)`, assert SystemExit at `get_connection()` call.

Key activities:

- **Spike A — DONE 2026-05-01.** Live payloads captured to
  `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`. Setup pattern
  for re-running: `/tmp/log-payload.sh` + entries in
  `.claude/settings.local.json` for `SubagentStart`, `SubagentStop`, and
  `PreToolUse` matchers `Skill` and `Task`. **Note:** `settings.local.json` is NOT
  re-read mid-session — restart Claude Code after editing.
  **Findings (decision-gate verdict: GATE HIT, design revised — see below):**
  (a) ❌ `parent_session_id` does **not exist** in any payload. Cross-checked
      against [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks);
      docs do not list this field.
  (b) ✅ `SubagentStop` carries `session_id` (parent main-loop's), `agent_id`
      (subagent's, matches `SubagentStart`), `agent_type`, `agent_transcript_path`,
      `last_assistant_message`. **No explicit error/exit field** — v1 status flips
      to `completed` regardless.
  (c) ✅ `PreToolUse(Skill)` carries `session_id` and `tool_input.skill`
      (singular). **NOT `tool_input.skill_name`** as originally assumed.
  (d) **Bonus finding:** `agent_id` is Claude Code's per-subagent unique
      identifier (per docs: "Present only when the hook fires inside a subagent
      call"). This is **better** than the planned `parent_session_id` design —
      `SubagentStart` ↔ `SubagentStop` close on `agent_id` exact match, no
      staleness window needed for the inner subagent.
  (e) `PreToolUse(Task)` matcher value `"Task"` works in settings; runtime
      `tool_name` reads as `"Agent"` though.
- **Schema migration.** Edit `cast-server/cast_server/db/schema.sql` — add **two** new columns to `agent_runs`:
  - `skills_used TEXT DEFAULT '[]'` (PreToolUse(Skill) capture)
  - `claude_agent_id TEXT` (Claude Code's runtime subagent id from SubagentStart payload). **Naming note:** named `claude_agent_id` not `agent_id` to avoid collision with `cast_server.models.agent_config.AgentConfig.agent_id` which is the agent CONFIG folder name (e.g. `cast-detailed-plan`).
  Add corresponding `ALTER TABLE … ADD COLUMN` blocks in `_run_migrations()` (`cast-server/cast_server/db/connection.py`) following the existing `try/except sqlite3.OperationalError` pattern.
  Add new index for the closure path: `CREATE INDEX IF NOT EXISTS idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL` — `SubagentStop` closes by exact `claude_agent_id` match, single-row lookup. **No other new indexes** — composite `idx_agent_runs_session_status` already covers session_id-keyed lookups. **No `claude_session_id` column** — `session_id` IS the Claude Code session id, populated by `user_invocation_service.register()` line 49.
- **System goals seed.** ✅ Already landed in `_run_migrations()._seed_system_goals(conn)` (`INSERT OR IGNORE` of `slug='system-ops'`, plus `folder_path='system-ops'` to satisfy the NOT NULL column). Live DB row also seeded out-of-band. Sp1 retains only the verification test `test_system_ops_seed_idempotent` (fresh DB → seeded; pre-existing DB without goal → seeded; pre-existing goal → no error, no duplicate).
- **SQLite 3.9+ startup check.** In `cast-server/cast_server/db/connection.py:get_connection()`, after the `PRAGMA` calls, assert `sqlite3.sqlite_version_info >= (3, 9, 0)` and `SystemExit` with a clear message: "cast-server requires SQLite 3.9+ for `record_skill`'s `json_insert(... '$[#]' ...)` semantics; got <ver>." 3.9 was 2015 — every reasonable system has it; we treat the floor as a contract, not a fallback dance.
- **Model update.** `cast-server/cast_server/models/agent_run.py:AgentRun` — add `skills_used: list[dict] = []` and `claude_agent_id: str | None = None`. Existing `session_id: str | None = None` (line 19) stays; document in docstring that it carries the Claude Code (parent main-loop) session id, and that `claude_agent_id` carries the Claude Code per-subagent runtime id.
- **DRY extraction — single source of cast-name truth.** Create `cast-server/cast_server/cli/_cast_name.py` exporting:

  ```python
  CAST_NAME_BODY = r"cast-[a-z0-9-]+"
  PROMPT_PATTERN = re.compile(rf"^\s*/({CAST_NAME_BODY})")        # slash-prefixed user prompts
  AGENT_TYPE_PATTERN = re.compile(rf"^{CAST_NAME_BODY}$")         # bare subagent_type names
  ```

  Update `hook_handlers.py` to import `PROMPT_PATTERN` from this module (delete the local definition). New `test_cast_name_pattern.py` covers both regexes (positive: `cast-foo`, `cast-foo-bar-baz`; negative: `Cast-foo`, `cast_foo`, `cast-`, `not-cast-foo`).
- **Invocation sources module.** Create `cast-server/cast_server/services/_invocation_sources.py`:

  ```python
  USER_PROMPT = "user-prompt"
  SUBAGENT_START = "subagent-start"

  def source_filter_clause() -> str:
      return "json_extract(input_params, '$.source') = ?"
  ```

  Both `user_invocation_service.py` and the new `subagent_invocation_service.py` import from here. Update sibling's `complete()` (line 86) to use `source_filter_clause()` + the `USER_PROMPT` constant. Tests in `test_invocation_sources.py` cover the constant values and the SQL clause shape; sibling's existing `complete()` tests must still pass after the refactor.
- **Service helpers (TWO).** Add to `cast-server/cast_server/services/agent_service.py`:
  - `resolve_parent_for_subagent(session_id: str) -> str | None` — returns the run_id of the most-recent running cast-* row in `session_id`. SQL: `SELECT id FROM agent_runs WHERE session_id = ? AND status = 'running' AND agent_name LIKE 'cast-%' ORDER BY started_at DESC LIMIT 1`. The `agent_name LIKE 'cast-%'` filter is critical — it scopes parent resolution to cast-* rows only, so a non-cast subagent (e.g., a user manually dispatching `Explore`) doesn't become a "parent" of a later cast-* subagent. **Note:** named `_for_subagent` rather than `_by_session_id` because session_id alone is shared by ALL subagents in a Claude Code session — the resolver returns the most-recent running CAST-* row, not "the row for this session_id". Tests: no row → None, no cast-* row but other rows exist → None, single running cast-* row → id, multiple running cast-* rows (parent + nested subagent) → most-recent wins.
  - `resolve_run_by_claude_agent_id(claude_agent_id: str) -> str | None` — returns the run_id whose `claude_agent_id` matches. SQL: `SELECT id FROM agent_runs WHERE claude_agent_id = ? LIMIT 1`. Used by `SubagentStop` to close the exact row. Tests: missing → None, present → id, two rows with same id (shouldn't happen but defend) → most-recent.

**Design review:**

- Naming: `skills_used` matches plural-noun convention (`artifacts`, `directories`, `rate_limit_pauses`). `_invocation_sources.py` follows the leading-underscore convention for "internal-but-importable" modules used elsewhere in `services/`. ✓
- Architecture: migration via `_run_migrations()` mirrors all eight existing examples in `connection.py`. The seed step is one new call at the end, not a new file. ✓
- Spec consistency: no impact on `cast-delegation-contract.collab.md` (file-based delegation outputs, unrelated to hook-tracking). No impact on `cast-output-json-contract.collab.md` (hook-created rows have no output.json). ✓
- DRY: PROMPT_PATTERN and AGENT_TYPE_PATTERN share `CAST_NAME_BODY` — single source of truth for "what counts as cast-*". Source discriminators share constants — typo-proof.
- Error & rescue: `resolve_parent_for_subagent` is the SOLE parent-resolution path (no `parent_session_id` to fall back on — it doesn't exist). Stale-parent guard is the `status='running'` filter; the `agent_name LIKE 'cast-%'` filter ensures non-cast subagents don't accidentally become parents. `resolve_run_by_claude_agent_id` is the SOLE closure path for `SubagentStop`. SQLite version check fails LOUD at startup (not at first `record_skill` call) so deployment surprises happen once, not per-skill.
- Index choice: composite `idx_agent_runs_session_status` (existing) covers parent-resolution (`session_id` + `status='running'` + `agent_name LIKE 'cast-%'` does the leftmost-prefix scan; `LIKE` is a SARG-able filter at the row level). New partial index `idx_agent_runs_claude_agent_id WHERE claude_agent_id IS NOT NULL` covers closure path — partial because user-invocation rows never have it.

## Sub-phase 2: Server — subagent capture service + endpoints

**Outcome:** Three new HTTP endpoints under `/api/agents/subagent-invocations/` accept
hook payloads (matching the empirical shapes in
`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`), server-side
filter to `cast-*` agents via the shared `AGENT_TYPE_PATTERN`, create rows with
correct `parent_run_id` (resolved via `resolve_parent_for_subagent` —
most-recent-running cast-* row in the session) AND inherited `goal_slug`,
persist `claude_agent_id` from the SubagentStart payload for closure,
transition them on `SubagentStop` via exact `claude_agent_id` match, and append
skill invocations to whichever cast-* row (user-invocation OR subagent) is the
most-recent running in that session. Every endpoint exits 200 even on misses
(hook scripts must never block).

**Dependencies:** Sub-phase 1.

**Estimated effort:** 1 session.

**Verification:**

- `pytest cast-server/tests/test_subagent_invocation_service.py` green:
  - `test_register_creates_running_row_for_cast_agent`
  - `test_register_returns_null_for_non_cast_agent_type`
  - `test_register_persists_claude_agent_id`
  - `test_register_resolves_parent_via_most_recent_running_cast_row` (renamed from "_via_session_id")
  - `test_register_returns_orphan_when_no_running_cast_row_in_session` (renamed; was "_when_parent_session_stale")
  - `test_register_ignores_non_cast_running_rows_when_resolving_parent` (new — `agent_name LIKE 'cast-%'` filter is contract)
  - `test_subagent_register_inherits_parent_goal_slug` (per review #3)
  - `test_subagent_register_falls_back_to_system_ops_when_orphan` (per review #3)
  - `test_complete_closes_only_the_subagent_with_matching_claude_agent_id` (renamed; was session-broad)
  - `test_complete_does_not_touch_user_invocation_rows` (closure now keys on claude_agent_id which user-invocation rows lack)
  - `test_complete_returns_zero_when_claude_agent_id_unknown`
  - `test_record_skill_attaches_to_user_invocation_when_no_subagent_running` (per review #1)
  - `test_record_skill_attaches_to_subagent_when_both_running` (per review #1, most-recent wins)
  - `test_record_skill_appends_in_invocation_order` (multiple skill calls)
- `pytest cast-server/tests/test_api_agents.py::test_subagent_invocation_endpoints` green: 3 endpoints return 200 + correct JSON shape (incl. `claude_agent_id` request/response field).
- `curl -X POST localhost:8005/api/agents/subagent-invocations -d '{"agent_type":"cast-foo","session_id":"S1","claude_agent_id":"a1"}'` returns `{"run_id": "<uuid>"}`. Second curl while the first is still `running` (same `session_id:"S1"`, different `claude_agent_id:"a2"`, `agent_type:"cast-bar"`) returns child whose `parent_run_id` matches the first run.
- `curl ... -d '{"agent_type":"Explore",...}'` returns `{"run_id": null}` and creates no row.
- `curl -X POST localhost:8005/api/agents/subagent-invocations/complete -d '{"claude_agent_id":"a2"}'` closes ONLY that row (verified via DB inspection).
- Sibling user-invocation `complete()` does NOT touch our subagent rows; our `complete()` does NOT touch user-invocation rows.

Key activities:

- **New service `cast-server/cast_server/services/subagent_invocation_service.py`** (parallel naming to `user_invocation_service.py`). Three functions, each thin:
  - `register(agent_type, session_id, claude_agent_id, transcript_path=None, prompt=None, db_path=None) -> str | None` —
    1. Apply `AGENT_TYPE_PATTERN.match(agent_type)`; if no match, return `None`.
    2. `parent_run_id = resolve_parent_for_subagent(session_id)` — most-recent running cast-* row in this session. May be `None` if no cast-* parent (orphan).
    3. **Inherit goal_slug from parent.** If `parent_run_id` is non-None, `goal_slug = SELECT goal_slug FROM agent_runs WHERE id = ?`; otherwise `goal_slug = "system-ops"` (orphan fallback).
    4. Call `agent_service.create_agent_run` with `agent_name=agent_type`, `goal_slug=goal_slug`, `session_id=session_id`, `claude_agent_id=claude_agent_id`, `status="running"`, `input_params={"source": SUBAGENT_START, "prompt": prompt, "transcript_path": transcript_path}`, `parent_run_id=parent_run_id`. (`create_agent_run` will need a `claude_agent_id` kwarg added — INSERT-time field.)
    5. `update_agent_run(run_id, started_at=now)` (mirrors sibling pattern, line 56).
    6. Return run_id.
  - `complete(claude_agent_id, db_path=None) -> int` — UPDATE the row where `claude_agent_id=?` AND `status='running'` to `status='completed'`, set `completed_at`. **Single-row exact match.** No staleness window needed — `claude_agent_id` is unique per subagent dispatch and Claude Code only emits SubagentStop once per subagent. Return rowcount (0 if unknown id, 1 on success).
  - `record_skill(session_id, skill_name, invoked_at=None, db_path=None) -> int` — **NO source filter** (per review #1). Append `{name, invoked_at}` to whichever cast-* row is most-recent running in this session. SQL:
    ```sql
    UPDATE agent_runs
       SET skills_used = json_insert(skills_used, '$[#]', json_object('name', ?, 'invoked_at', ?))
     WHERE id = (
       SELECT id FROM agent_runs
        WHERE session_id = ?
          AND status = 'running'
          AND agent_name LIKE 'cast-%'
        ORDER BY started_at DESC
        LIMIT 1
     )
    ```
    The `agent_name LIKE 'cast-%'` filter ensures we attach to a cast-* row (user-invocation OR subagent), never to an unrelated row that happens to share the session. The "most-recent" rule means a Task()-dispatched subagent supersedes its slash-command parent for skill attribution while running, then skills naturally flow back to the parent after the subagent's `complete()` flips its status to `completed`. Return rowcount.
- **Source discriminator scope.** Used by sibling `complete()` only (closes by `source = USER_PROMPT` + session_id). Our `complete()` keys on `claude_agent_id` (exact-match), so a source filter is unnecessary — user-invocation rows don't have `claude_agent_id` populated, so they can't accidentally match. Constants live in `_invocation_sources.py` from sp1.
- **Endpoints in `cast-server/cast_server/routes/api_agents.py`** (mirror sibling shape):
  - `POST /api/agents/subagent-invocations` — body `{agent_type, session_id, claude_agent_id, transcript_path?, prompt?}`. Returns `{"run_id": <uuid> | null}`.
  - `POST /api/agents/subagent-invocations/complete` — body `{claude_agent_id}`. Returns `{"closed": <int>}` (always 0 or 1).
  - `POST /api/agents/subagent-invocations/skill` — body `{session_id, skill, invoked_at?}` (note `skill` singular, matching `tool_input.skill`). Returns `{"appended": <int>}`. `invoked_at` defaults to `now_iso()` server-side if absent.
- **Pydantic request models** mirroring `UserInvocationOpenRequest` style (find the existing one in `routes/api_agents.py` and follow the same conventions).
- **Best-practices delegation.** → Delegate: `/cast-pytest-best-practices` over `test_subagent_invocation_service.py`. Verify: in-memory DB per test (mirror sibling fixtures), no time-mocking pitfalls in staleness tests, no leaking writes to `~/.cast/diecast.db`.

**Design review:**

- Architecture: service → route mirrors sibling layering exactly. ✓
- Naming: `subagent_invocation_service` reads as the subagent counterpart to `user_invocation_service`. ✓
- Concurrency: `record_skill` uses SQLite `json_insert(... '$[#]' ...)` — single UPDATE statement, no read-modify-write. SQLite 3.9+ is enforced at startup (sp1) so no fallback path exists. ✓
- Error & rescue: every endpoint's "no matching row" returns 200 with `{run_id: null}` or `{closed: 0}` or `{appended: 0}` rather than 404 — hook scripts MUST exit 0 (FR-010), and 4xx tempts a future hook author to retry.
- Spec consistency: terminal status is `completed | partial | failed` per `cast-delegation-contract`. We use `completed` only on `SubagentStop`; never `partial`. ✓
- Security: hook endpoints have NO auth. cast-server binds 127.0.0.1 by default but `CAST_HOST` is configurable. Add a startup warning when CAST_HOST is non-loopback ("hook endpoints are unauthenticated; do not expose cast-server publicly"). Document in spec.
- Skill-attribution rule (per review #1): the most-recent running cast-* row in a session wins. Test the dual-running case explicitly so the rule is contract, not coincidence.

## Sub-phase 3: Hook layer — extend HOOK_EVENTS + per-event matcher + fire-and-forget POST

**Outcome:** Three new entries in `HOOK_EVENTS`, three new handlers (with hook-side
cast-* scope filter), `install_hooks.py` learns to emit per-event `matcher` keys
(needed for `PreToolUse` matchers `"Skill"` and `"Task"`), and `_post()` is
refactored to fire-and-forget so hook subprocesses don't block on cast-server's
response body. `cast-hook install` writes 5 hook entries to
`.claude/settings.json` (UserPromptSubmit, Stop, SubagentStart, SubagentStop,
PreToolUse-with-matcher-Skill); `cast-hook uninstall` removes only ours, leaves
third-party untouched.

**Dependencies:** Sub-phases 1 and 2.

**Estimated effort:** 1 session.

**Verification:**

- `pytest cast-server/tests/test_cli_hook.py` green:
  - existing tests still pass after `_post()` refactor
  - `test_subagent_start_posts_for_cast_agent_type` (happy path; payload includes `claude_agent_id`)
  - `test_subagent_start_skips_non_cast_agent_type` (per review #2 — early-return, no POST)
  - `test_subagent_start_server_unreachable_exits_zero`
  - `test_subagent_stop_posts_claude_agent_id` (renamed from "_session_id" — closure now keyed on agent_id)
  - `test_subagent_stop_skips_when_claude_agent_id_missing` (defensive: malformed payload → exit 0, no POST)
  - `test_skill_invoke_skips_non_skill_tool_name`
  - `test_skill_invoke_extracts_skill_from_tool_input` (renamed; field is `tool_input.skill`, NOT `tool_input.skill_name`)
  - `test_post_does_not_block_on_response_body` (per review #9 — assert no `.read()` on the urlopen result)
- `pytest cast-server/tests/test_install_hooks.py` green:
  - `test_install_hooks_writes_pretooluse_with_skill_matcher` (per review #7)
  - `test_install_preserves_third_party_pretooluse_with_different_matcher`
  - `test_uninstall_removes_ours_regardless_of_matcher`
  - `test_round_trip_install_uninstall_byte_equivalent`
- Manual round-trip: `cast-hook install` in a tmp project → `.claude/settings.json` has 5 entries (UserPromptSubmit, Stop, SubagentStart, SubagentStop, PreToolUse with `matcher: "Skill"`). `cast-hook uninstall` → all 5 of ours gone, any seeded third-party entries untouched.
- Manual end-to-end with `CAST_PORT=8005` cast-server running: `echo '{"agent_type":"cast-foo","session_id":"S1","agent_id":"a1","transcript_path":"/tmp/x.jsonl"}' | cast-hook subagent-start` exits 0; row visible via `GET /api/agents/jobs/<run_id>`. Then `echo '{"agent_id":"a1","session_id":"S1"}' | cast-hook subagent-stop` flips it to `completed`.

Key activities:

- **`_post()` fire-and-forget refactor.** Modify `cli/hook_handlers.py:_post()` to NOT call `.read()` on the response — open the connection, send the request body, then return without waiting for the response body. The 2s urlopen timeout still bounds the worst case, but the typical path returns immediately after sending. Server logs any errors; client never sees them (and shouldn't — hook never blocks anyway). Apply to ALL handlers: sibling `user_prompt_start`/`user_prompt_stop` benefit from the same change. Add `test_post_does_not_block_on_response_body`: monkeypatch a slow response body, assert handler returns before the body would have arrived.
- **Extend `HOOK_EVENTS` in `cli/hook_events.py`** — three new tuples (4-tuple shape; see install_hooks change below):

  ```python
  ("SubagentStart", "subagent-start", _h.subagent_start, None),
  ("SubagentStop",  "subagent-stop",  _h.subagent_stop,  None),
  ("PreToolUse",    "skill-invoke",   _h.skill_invoke,   "Skill"),
  ```

  Per the file's canonical-extension comment, this single edit propagates to `install_hooks.py` (settings injection) and `hook.py` (runtime dispatch).
- **Three new handlers in `cli/hook_handlers.py`**. Reference payload shapes:
  `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`.
  - `subagent_start()` — read payload; extract `agent_type`, `session_id`,
    `agent_id` (rename to `claude_agent_id` when forwarding to cast-server, per
    plan's column-naming decision), `transcript_path`. The `prompt` field is
    NOT in `SubagentStart`; if a future caller wants it, capture from the
    PreToolUse(Task) `tool_input.prompt` correlated via `tool_use_id` (out of
    scope for v1).
    **Hook-side scope filter (per review #2):** import `AGENT_TYPE_PATTERN`
    from `cli/_cast_name.py` and early-return WITHOUT POST when `agent_type`
    doesn't match. Server keeps its filter as defense in depth. POST to
    `/subagent-invocations` with body `{agent_type, session_id,
    claude_agent_id, transcript_path}`.
  - `subagent_stop()` — read payload; extract `agent_id` (forward as
    `claude_agent_id`). If absent (malformed), early-return. POST to
    `/subagent-invocations/complete` with body `{claude_agent_id}`.
  - `skill_invoke()` — read payload; if `tool_name != "Skill"` → return early
    (defensive — install side already filters via matcher, but handler-side
    check is cheap insurance). Extract `session_id`, `tool_input.skill`
    (singular — empirical capture confirmed; was assumed `skill_name` in
    original plan). POST to `/subagent-invocations/skill` with body
    `{session_id, skill}`.
- **Per-event matcher support in `install_hooks.py`** — extend `HOOK_EVENTS` value type from `(event, subcommand, handler)` to `(event, subcommand, handler, matcher_or_none)` (already shown above). Update:
  - `install_hooks.install()` (line 97 onward): when iterating `HOOK_EVENTS`, write `{"matcher": matcher, "hooks": [...]}` when `matcher` is non-None, else `{"hooks": [...]}`.
  - `_entry_is_ours()` (line 69) and `uninstall()`: ignore the `matcher` key when matching ours-vs-not (the HOOK_MARKER on the inner `command` is the only ours-vs-theirs signal).
  - `DISPATCH` and `COMMAND_FOR_EVENT` derivations in `hook_events.py`: ignore the new tuple slot.
- **Idempotency under matcher.** A re-install must not duplicate the PreToolUse(matcher=Skill) entry, even if a third-party PreToolUse entry exists with a different matcher. The HOOK_MARKER (`"cast-hook "`) substring check handles this — the matcher key is irrelevant to identity. Document with a test (`test_install_preserves_third_party_pretooluse_with_different_matcher`).
- **Best-practices delegation.** → Delegate: `/cast-pytest-best-practices` over `test_install_hooks.py` AND `test_cli_hook.py`. Verify: tmp-dir cleanup, no leaking writes to dev's real `~/.claude/settings.json`, `subprocess`-free (mock urllib at the boundary).

**Design review:**

- Architecture: extends the canonical `HOOK_EVENTS` table per its comment; never forks. ✓
- DRY: matcher support added once in `install_hooks.py`; no new file. Hook-side scope filter shares `AGENT_TYPE_PATTERN` with the server filter — single regex, two enforcement points (defense in depth). ✓
- Naming: handler/subcommand names match Claude Code event naming where possible (`subagent-start`/`subagent-stop`/`skill-invoke`). ✓
- Performance: fire-and-forget `_post()` shaves the ~50-80% of hook latency that was blocking on response body. SC-003's <100ms p95 budget gets healthy headroom.
- Error & rescue: handlers exit 0 on any error (per FR-010); install/uninstall preserve existing pattern (atomic write, malformed-JSON refuses).
- Compatibility: the value-shape extension to 4-tuple is a breaking change to any external code importing `HOOK_EVENTS`. Quick grep — only `install_hooks.py` and `hook.py` import; both updated in same sp. No external consumers.

## Sub-phase 4: Surface — L2 chip-list + L3 detail in runs UI

**Outcome:** The `/runs` page renders skills used by each cast-* run as a compact chip
row at L2 (e.g. `"3 skills: detailed-plan, spec-checker, +1"`) and as a full list with
timestamps and invocation counts when expanded to L3. Empty `skills_used` hides the
chip row entirely.

**Dependencies:** Sub-phases 1-3 (data must be flowing for visual verification).

**Estimated effort:** 1 session.

**Verification:**

- `pytest cast-server/tests/ui/test_runs_skills_chips.py` green:
  - `test_skills_chip_row_renders_for_user_invocation_with_skills` (per review #1 — slash command shows chips even without Task() subagents)
  - `test_skills_chip_row_renders_for_subagent_with_skills`
  - `test_skills_chip_row_hidden_when_skills_used_empty`
  - `test_skills_chip_overflow_indicator_shows_plus_n_after_two_chips`
  - `test_l3_detail_aggregates_repeated_skill_invocations_into_count`
- Manual: in a session with ≥3 cast-* subagent dispatches each invoking ≥2 skills, visit `http://127.0.0.1:8005/runs`. Each cast-* row's L2 line shows the skill chip-row; expanding to L3 shows the full timestamped list with counts.
- Manual: a cast-* row with `skills_used=[]` shows no chip row at L2 (no "0 skills" placeholder).
- Visual check at 1280px confirms no layout overflow with 5 skills rendered.

Key activities:

- **Locate templates.** `find cast-server/cast_server/templates -name "*run*"` to find existing L1/L2/L3 partials. The threaded-tree plan should already define L2/L3 anatomy; mirror its conventions and slot ours appropriately.
- **L2 chip row partial.** New `cast-server/cast_server/templates/partials/run_skills_chips.html`: render `<div class="skills-chips">` with first 2 skill names as chips and a `+N` overflow badge if more. Wrap in `{% if skills_used %}…{% endif %}` so empty hides entirely.
- **L3 detail partial.** New `cast-server/cast_server/templates/partials/run_skills_detail.html`: `<table>` with columns `Skill`, `First invoked`, `Count`. Server-side aggregation: group `skills_used` JSON list by `name`, count occurrences, take min(`invoked_at`).
- **Route handler.** In the `/runs` handler (`cast-server/cast_server/routes/pages.py`), parse `skills_used` JSON when serializing each run and pass aggregated form to the template. Wrap parse in `try/except (json.JSONDecodeError, TypeError) → []` (defensive: a row with malformed JSON should render as "no skills", not crash the page).
- **CSS.** Add `.skills-chips` styles to the runs page CSS — match existing chip/pill pattern if one exists; otherwise small rounded rect with subtle border.
- **UI tests.** Create `test_runs_skills_chips.py` — seed three runs (5 skills, 1 skill, 0 skills); assert chip-row presence/absence and the `+N` overflow indicator at exactly the right threshold. Include a slash-command-only run with skills (no Task() subagent) to verify per review #1 that user-invocation rows get chips too.
- **Best-practices delegation.** → Delegate: `/cast-pytest-best-practices` over the new UI test. Verify: zero-residue (test runs leave no DB rows behind), no real-DB writes, deterministic skill ordering for assertions.

**Design review:**

- Architecture: mirrors existing partial → route → page pattern; no new layer. ✓
- Naming: `skills_used` consistent with `artifacts`, `directories`. `run_skills_chips` partial name follows existing `run_*` partial convention.
- Spec consistency: when `cast-runs-threaded-tree` ships, our chip-row insertion point must respect their L2 row anatomy. Cross-check at impl time.
- Error & rescue: malformed JSON in `skills_used` (shouldn't happen but possible if hand-edited) → empty list, no chip row.
- Security: skill names go straight to template via Jinja default autoescape; do not use `|safe`. Skill names are agent-controlled but never user-controlled.

## Sub-phase 5: Spec capture + e2e smoke + close-out

**Outcome:** New spec `docs/specs/cast-subagent-and-skill-capture.collab.md` documents
the contract; registered in `_registry.md`; `cast-spec-checker` lints clean; an
end-to-end manual smoke confirms a real Claude Code session produces the expected tree
+ skill chips.

**Dependencies:** Sub-phases 1-4.

**Estimated effort:** 0.5 session.

**Verification:**

- `bin/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md` exits 0.
- `_registry.md` shows the new row.
- E2E smoke: in a fresh Claude Code session in this project (cast-hook installed via `cast-hook install`), type `/cast-detailed-plan goals/<some-goal>`. Watch `/runs`: user-invocation root row appears (sibling-managed); when the slash-command harness dispatches `cast-detailed-plan` as a `Task()` subagent, that row appears as child via this plan's SubagentStart capture; cast-detailed-plan's auto-trigger of `cast-plan-review` appears as grandchild (HTTP-dispatched); skill chips appear on whichever cast-* row was most-recent-running when each Skill invocation happened.
- Run `cast-hook uninstall` in a tmp project; confirm all 5 hook entries removed; nothing else in settings.json touched.

Key activities:

- **→ Delegate: `/cast-update-spec create cast-subagent-and-skill-capture`**. Provide context: this plan's path; the requirements doc path; FR-001..FR-013 verbatim from refined requirements **(refined_requirements has been swept to match the post-Spike-A design — see Section "Spike A — empirical findings" below)**; SC-001..SC-007 verbatim; the regex `^cast-[a-z0-9-]+$`; the parent-resolution rule (most-recent running cast-* row in session_id; `agent_name LIKE 'cast-%'` filter); the closure rule (exact `claude_agent_id` match); the `_invocation_sources.py` constants and their use in `complete()` of sibling user-invocation service (subagent service uses `claude_agent_id` so no source filter needed); the `record_skill` "most-recent running cast-* row" attribution rule; the goal_slug inheritance rule; the `system-ops` auto-seed contract; the SQLite 3.9+ floor; the `claude_agent_id` column naming decision (avoids collision with `agent_config.agent_id`); the L2/L3 chip rules; the per-event matcher support contract for `install_hooks.py`; the fire-and-forget `_post()` semantics; the empirical payload-shapes notes file. Verify output for: spec maturity Draft; linked_files lists all touched files including `_cast_name.py`, `_invocation_sources.py`, and `notes/payload-shapes.ai.md`; behavior section covers all 8 user stories; cross-references to `cast-delegation-contract.collab.md` and `cast-output-json-contract.collab.md` noting non-overlap.
- **→ Delegate: `/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md`** — must exit 0.
- **Update `docs/specs/_registry.md`** to add the new row (the update-spec skill should do this; if it doesn't, append manually):

  ```
  | `cast-subagent-and-skill-capture.collab.md` | cast-subagent-and-skill-capture | cast-server | Hook-driven capture of Task()-dispatched cast-* subagents and PreToolUse Skill events; session_id-based parent resolution; goal_slug inheritance; system-ops auto-seed; per-event matcher support in cast-hook installer; fire-and-forget POST. Linked plan: `docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`. | Draft | 1 |
  ```

- **End-to-end manual smoke** following the Verification list above. Capture screenshots into `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` for the audit trail.
- **Cross-spec back-reference.** Add to `cast-delegation-contract.collab.md` a one-line back-reference noting the new session_id-based hook path (parent resolution = most-recent running cast-* row; closure = exact `claude_agent_id`). Likewise check the sibling slash-command spec — add a back-reference noting that subagent rows ride the same `session_id` field as user-invocation rows (parent main-loop session) but additionally carry `claude_agent_id` and use a different `source` discriminator; source constants live in `_invocation_sources.py`.

**Design review:**

- Spec creation post-implementation is acceptable here because the contract was already locked in the refined requirements (which `cast-spec-checker` already linted clean) and the implementation is small. ✓
- Naming: spec slug matches goal slug. ✓
- Architecture: registers via canonical `_registry.md` row; no special handling. ✓

## Build Order

```
sp1 (Foundation) ──► sp2 (Capture service) ──► sp3 (Hook layer) ──► sp4 (UI) ──► sp5 (Spec + E2E)
```

**Critical path:** sp1 → sp2 → sp3 → sp4 → sp5. No genuine parallelism — sub-sub-phases
within a single sp can run in any order, but the inter-sp dependency chain is linear.

## Design Review Flags

| Sub-phase | Flag | Action |
|-------|------|--------|
| sp1 | ~~Spike A failure (Claude Code doesn't actually surface `parent_session_id`) collapses parent attribution~~ **RESOLVED 2026-05-01.** Spike A confirmed `parent_session_id` does not exist; fallback design ("most-recent running cast-* row in session") is now the primary path. `claude_agent_id` provides exact closure. See Spike A findings inline in sp1. |
| sp1 | `system-ops` goal seed must be idempotent under both fresh and live DB | `INSERT OR IGNORE` + dedicated test (`test_system_ops_seed_idempotent`). |
| sp1 | SQLite 3.9+ requirement is a hard contract | Startup check fails LOUD with actionable message; tested. |
| sp2 | No auth on hook endpoints; `CAST_HOST` configurable to non-loopback | Add startup warning when CAST_HOST is non-loopback. Document in spec (sp5). |
| sp2 | Skill attribution rule: most-recent running cast-* row wins (across user-invocation + subagent in same session) | Dedicated tests for both the "no subagent" and "both running" cases; document as the primary skill-attribution invariant in the spec. |
| sp2 | Source discriminator scope shrunk to `complete()`-only | Cross-contamination between sibling and our `complete()` still prevented; `record_skill` no longer needs the discriminator since `LIKE 'cast-%'` + most-recent-running covers it. |
| sp3 | `install_hooks.py` value-shape goes from 3-tuple to 4-tuple; breaking change to importers | Confirmed only `install_hooks.py` and `hook.py` import HOOK_EVENTS; both updated in same sp. |
| sp3 | Idempotency under matcher key | Test that re-install with mixed matcher entries doesn't duplicate. |
| sp3 | Hook-side scope filter must share regex with server | Both import from `cli/_cast_name.py`. ✓ |
| sp3 | Fire-and-forget `_post()` swallows server-side errors | Acceptable: hook never blocks; cast-server logs errors itself. ✓ |
| sp4 | Layout overflow with many skills | `+N` overflow badge after 2 chips; verified in UI test at 1280px. |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ~~Claude Code's `SubagentStart` payload doesn't include `parent_session_id`~~ **RESOLVED 2026-05-01.** Spike A confirmed the field doesn't exist. New design uses (`session_id` + `claude_agent_id`); parent resolution is "most-recent running cast-* row in session." Empirical capture in `notes/payload-shapes.ai.md`. | n/a | Design adjusted; this risk no longer applies. |
| `PreToolUse` matcher `"Skill"` doesn't actually narrow to Skill-tool calls | Medium — every PreToolUse event POSTs, generating noise | sp3 handler-side defensive check (`if tool_name != "Skill": return`) before POST, in addition to settings.json matcher. Two-layer defense. |
| Hook subprocess spawn cost per Skill call adds noticeable interactive lag | Low (post fire-and-forget) | Per review #9: `_post()` no longer blocks on response body. ~50-80% latency reduction. SC-003's <100ms p95 budget has headroom. If still breached, batch via local file flush (out of scope for v1). |
| `_run_migrations` ALTER fails on a corrupt or partial DB | Low | Existing migrations have the same exposure; reuse `try/except sqlite3.OperationalError` pattern. |
| `skills_used` JSON column grows unbounded for very long-running cast-* sessions | Low | A run touching 100+ skills is unusual; if observed, add a `skill_invocation_count` column for fast aggregation and prune `skills_used` to the last N entries. v2 concern. |
| UI overflow at L2 on narrow viewports (<800px) | Low | Plan targets 1280px; sub-1024px gracefully wraps. Spec'd in sp4. |
| `record_skill` attaches a skill to the wrong cast-* row when both user-invocation and subagent are running concurrently | Medium — surprising attribution if "most-recent" rule misfires | The most-recent-running rule is correct for the steady-state (subagent supersedes parent during its lifetime, parent regains attribution after subagent's `complete()`). Test the dual-running case explicitly so behavior is contract, not coincidence. |
| Goal_slug inheritance returns NULL when parent row is in a goal that was deleted (FK cascade SET NULL) | Low | Inherited NULL flows to `agent_runs.goal_slug` which is NOT NULL — insert fails. Mitigation: `register()` falls back to `"system-ops"` if the SELECT returns NULL or no row. Add to test list. |

## Open Questions

- **[RESOLVED 2026-05-01] O1 — Live SubagentStart payload shape.** Resolved via Spike A. Actual shape: `{session_id, agent_id, agent_type, transcript_path, cwd, hook_event_name}`. `agent_type` is the key (capital first letter for built-ins like `Explore`, lowercase-hyphenated for custom like `cast-foo`). NO `parent_session_id`. NO `prompt` field on SubagentStart (prompt is on PreToolUse(Task) — not currently captured). Verbatim in `notes/payload-shapes.ai.md`.
- **[RESOLVED 2026-05-01] O2 — SubagentStop payload exit signaling.** Resolved via Spike A. No explicit `error`, `exit_code`, or `failed` field. v1 status flips to `completed` regardless. `last_assistant_message` is present and could feed v2 failure detection.
- **[USER-DEFERRED] O3 — L2 chip overflow threshold + click-through interactivity.** Reason: refined requirements pre-decided "first 2 chips + count, no click-through in v1". sp4 implements that; revisit if user feedback signals otherwise.
- **[USER-DEFERRED] O4 — Skill arguments capture.** Reason: refined requirements explicit punt to v2 with redaction; out of scope here.
- **[RESOLVED 2026-05-01] O5 — Most-recent-running disambiguation under nested/parallel subagents.** Original concern (that `parent_session_id` should equal the immediate parent's id) is moot — `parent_session_id` doesn't exist. The actual mechanism for disambiguating: `SubagentStart` fires synchronously before the new subagent's first action, so by the time it lands at cast-server, the parent (most-recent running cast-* row) is the immediate dispatcher. Parallel-sibling case: when parent dispatches A, then B; B's `SubagentStart` arrives after A's. If A then dispatches G, A is "running" and is the most-recent (because B hasn't started new work). The most-recent-running rule is correct UNLESS A and B both run quickly and overlap — in that edge case, attribution may go to whichever ran last. Acceptable for v1; if precision needed later, capture `PreToolUse(Task)` and use `tool_use_id` correlation.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-delegation-contract.collab.md` | Terminal Status Set, Atomic Write Contract, Cross-Phase Authorship | None — hook-created rows don't write delegation output files. Add back-reference noting the parallel parent-attribution path (session_id keyed) in sp5. |
| `cast-output-json-contract.collab.md` | Field-by-Field Schema | None — hook-created rows have no `output.json`. Spec'd as out-of-scope in refined requirements. |

## Decisions

- **2026-05-01T18:00:00Z — Should `record_skill` filter by `source='subagent-start'` or attach skills to the most-recent running cast-* row regardless of source?** — Decision: Drop the source filter; attach to the most-recent running cast-* row (user-invocation OR subagent) in the session. Rationale: every cast-* row should show what it invoked, regardless of dispatch surface; slash commands without Task() subagents would otherwise show no skill info anywhere.
- **2026-05-01T18:01:00Z — Where should the cast-* scope filter live: server-side only, hook-side only, or both?** — Decision: Both. Hook handler imports `AGENT_TYPE_PATTERN` and early-returns before POST; server keeps its filter as defense in depth. Rationale: avoids hundreds of pointless POSTs for non-cast `Task()` events; single regex sourced from `cli/_cast_name.py` so there is no duplication risk.
- **2026-05-01T18:02:00Z — What `goal_slug` should subagent rows use?** — Decision: Inherit from resolved parent_run; fall back to `"system-ops"` when orphan. Rationale: the threaded-tree UI groups under the right goal; matches the user mental model where `/cast-detailed-plan goals/foo/` produces rows under `goals/foo`.
- **2026-05-01T18:03:00Z — Where should the `system-ops` goal be created?** — Decision: Auto-create on cast-server startup as part of `_run_migrations()`, idempotent via `INSERT OR IGNORE`. Rationale: self-healing; sibling `user_invocation_service.register()` was silently broken without it (FK + NOT NULL on `agent_runs.goal_slug`); no user setup step required.
- **2026-05-01T18:04:00Z — How DRY should the input-source discriminator be?** — Decision: Extract source values + filter helper to `cast-server/cast_server/services/_invocation_sources.py` and refactor sibling `complete()` to use it. Rationale: single source of truth; typo-proof; future services adding a third source extend in one place; the strings ARE the contract.
- **2026-05-01T18:05:00Z — Should `record_skill` include a fallback path for SQLite versions older than 3.9?** — Decision: Hard-require SQLite 3.9+ via startup assertion; no fallback code. Rationale: 3.9 is from 2015; one code path; simpler tests; loud failure at startup beats silent slow path.
- **2026-05-01T18:06:00Z — Should the plan enumerate explicit test names for every new decision?** — Decision: Yes; verification lists in sp1/sp2/sp3/sp4 enumerate one named test per decision. Rationale: test list is source of truth; no decision can ship without coverage; catches the kind of stale verification that the original draft accumulated.
- **2026-05-01T18:07:00Z — Should the plan add a dedicated upgrade-from-partial-sibling-install test?** — Decision: No. Rationale: diecast is too new for a partial-sibling-install user to exist; the existing third-party-preservation test in sibling's `test_install_hooks.py` covers the relevant general behavior.
- **2026-05-01T18:08:00Z — Should hook `_post()` block on the response body?** — Decision: Drop the `.read()` call — fire-and-forget. Rationale: ~50-80% latency reduction with a one-line change; protects SC-003's <100ms p95 budget; hook never needs to see server errors (cast-server logs them itself); reverts cleanly if it ever causes issues.
- **2026-05-01T19:00:00Z — Spike A: empirical hook payload shapes.** — Decision: Replace `parent_session_id` design (didn't exist) with `(session_id + claude_agent_id)` design. Parent resolution = most-recent running cast-* row in session_id. Closure = exact `claude_agent_id` match. New column `claude_agent_id` on `agent_runs` (named to avoid collision with `agent_config.agent_id`). `tool_input.skill` (singular, not `skill_name`) for PreToolUse(Skill). Rationale: empirical capture (see `notes/payload-shapes.ai.md`) is authoritative; new design is strictly better than original (`claude_agent_id` enables exact closure, no staleness window for inner subagent). Cross-checked against [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) common-input-fields list.

## Cross-feature Impact (Spike A revision)

The Spike A redesign is a NEW-FIELD addition; no existing field changes meaning.
Specifically:

| Component | Affected? | How |
|-----------|-----------|-----|
| Sibling `user_invocation_service.py` | **No.** | Already uses `session_id` correctly (parent main-loop session). User-invocation rows don't carry `claude_agent_id` (it stays NULL); their `complete()` path is untouched. |
| Sibling `agent_runs.session_id` column | **No.** | Same column, same meaning ("parent main-loop session id"). Plan adds `claude_agent_id` as a NEW column for the subagent layer. |
| Threaded `/runs` page (sibling, shipped) | **No.** | Renders parent_run_id-based tree. parent_run_id is populated via the new `resolve_parent_for_subagent` for subagent rows; user-invocation rows stay as roots. |
| `cast-hooks.collab.md` spec | **No.** | Spec only references `SubagentStart` as a "preserve unrelated event" example for install/uninstall idempotency. Doesn't document its payload shape. Sp5 will add a back-reference to the new spec. |
| `cast-delegation-contract.collab.md` spec | **No.** | File-based delegation outputs; orthogonal to hook-based capture. Sp5 will add a one-line cross-spec back-reference. |
| Existing `cast_server.models.agent_config.AgentConfig.agent_id` | **No** (naming collision avoided). | Plan's new column is `claude_agent_id`. `AgentConfig.agent_id` stays as the agent CONFIG folder name (`cast-detailed-plan`, etc.). |
| Existing `agent_service.invoke_agent` (CLI dispatch) | **No.** | `claude_agent_id` is null for CLI-dispatched runs (no Claude Code SubagentStart event). `resolve_parent_for_subagent` is only called from the new subagent_invocation_service. |
| Existing tests in `test_user_invocation_service.py`, `test_cli_hook.py`, `test_install_hooks.py` | **Yes (compatible).** | After sp1's `_invocation_sources.py` extraction, sibling `complete()` SQL is refactored — sibling tests must still pass. After sp3's `_post()` fire-and-forget change, sibling tests must verify no new blocking behavior. |
| `tasks` table FK to goals | **No.** | Unaffected. |
| `agent_error_memories` table | **No.** | Unaffected. |

**Net cross-feature blast radius:** zero behavioral change to sibling features.
The only existing-code touches are surgical refactors covered by their own tests:

1. `user_invocation_service.complete()` → use `_invocation_sources.source_filter_clause()` instead of inline string (sp1).
2. `hook_handlers._post()` → drop `.read()` for fire-and-forget (sp3).
3. `hook_events.HOOK_EVENTS` → 3-tuple → 4-tuple (sp3); only `install_hooks.py` and `hook.py` import.

All three have explicit regression tests in the verification lists.

## Plan Review (cast-plan-review, 2026-05-01)

Reviewed the swept plan + the regenerated execution dir
(`docs/execution/cast-subagent-and-skill-capture/`) against engineering
preferences (DRY, well-tested, engineered-enough, edge cases, explicit). No
escalations; 4 auto-decisions applied inline. Decisions appended below.

- **2026-05-01T19:30:00Z — sp3 `subagent_start` handler missing the defensive early-return that `subagent_stop` has.** — Decision: Add the symmetric early-return — if `agent_type`, `session_id`, or `agent_id` is missing/empty in the SubagentStart payload, return without POST. Rationale: matches sibling guard, satisfies FR-010 (handlers never block on bad input). Patched in `sp3_hook_layer/plan.md` + two new tests `test_subagent_start_skips_when_agent_id_missing` and `test_subagent_start_skips_when_session_id_missing`.
- **2026-05-01T19:31:00Z — sp1 spawned 6 separate test files for the migration cluster (schema, system-ops seed, sqlite version).** — Decision: Consolidate the migration-cluster into `test_schema_migration.py`; keep `test_cast_name_pattern.py`, `test_invocation_sources.py`, and `test_agent_service.py` separate (one-file-per-source-module). Rationale: existing project convention; reduces fragmentation and tells the migration story in one place. Patched in `sp1_foundation/plan.md` Files table.
- **2026-05-01T19:32:00Z — sp2 had a single `test_subagent_invocation_endpoints` for 3 routes.** — Decision: Split into 3 named tests, one per endpoint (`test_subagent_invocation_open_endpoint`, `..._complete_endpoint`, `..._skill_endpoint`). Rationale: better failure attribution at test-runner output; matches existing test_api_agents.py granularity. Patched in `sp2_capture_service/plan.md` Files table.
- **2026-05-01T19:33:00Z — sp1 didn't reference existing `conftest.py` shared fixtures.** — Decision: Add an explicit "reuse, do NOT fork" row to the sp1 Files table calling out `isolated_db` and `ensure_goal` fixtures. Rationale: DRY; sibling tests already use them; new tests should not roll their own in-memory DB scaffolding. Patched in `sp1_foundation/plan.md` Files table.
