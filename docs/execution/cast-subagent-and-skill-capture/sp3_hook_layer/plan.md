# Sub-phase 3: Hook layer — extend HOOK_EVENTS + per-event matcher + fire-and-forget POST

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` and
> complete sp1 + sp2 before starting.
>
> Re-read
> `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`
> before authoring handlers — payload field names there are authoritative.

## Outcome

Three new entries in `HOOK_EVENTS`, three new handlers (with hook-side
cast-* scope filter), `install_hooks.py` learns to emit per-event
`matcher` keys (needed for `PreToolUse` matcher `"Skill"`), and
`_post()` is refactored to fire-and-forget so hook subprocesses don't
block on cast-server's response body. `cast-hook install` writes 5 hook
entries to `.claude/settings.json` (UserPromptSubmit, Stop,
SubagentStart, SubagentStop, PreToolUse-with-matcher-Skill);
`cast-hook uninstall` removes only ours, leaves third-party untouched.

## Dependencies

- **Requires completed:** sub-phases 1 and 2.
- **Assumed codebase state:** `_cast_name.py::AGENT_TYPE_PATTERN`
  exists; the 3 new endpoints under `/api/agents/subagent-invocations/`
  are live and return 200; bodies key on `claude_agent_id` (start /
  complete) and `session_id + skill` (skill).

## Estimated effort

1 session.

## Scope

**In scope:**

- Refactor `cli/hook_handlers.py:_post()` to fire-and-forget (no
  `.read()` on response body).
- Extend `cli/hook_events.py::HOOK_EVENTS` value tuple from 3-tuple to
  4-tuple (new `matcher_or_none` slot); add 3 new entries.
- Add 3 new handlers in `cli/hook_handlers.py`: `subagent_start`,
  `subagent_stop`, `skill_invoke`. Handlers extract `claude_agent_id`
  from payload `agent_id` and skill name from `tool_input.skill`
  (singular).
- Per-event matcher support in `cli/install_hooks.py` (`install` writes
  `{"matcher": ...}` when non-None; `_entry_is_ours` and `uninstall`
  ignore matcher key — HOOK_MARKER on inner `command` is the only
  ours-vs-theirs signal).
- Update `DISPATCH` and `COMMAND_FOR_EVENT` derivations in
  `hook_events.py` to ignore the new tuple slot.
- Tests in `cast-server/tests/test_cli_hook.py` and
  `cast-server/tests/test_install_hooks.py`.

**Out of scope (do NOT do):**

- Service or endpoint changes (already done in sp2).
- UI work (sp4).
- Spec authoring (sp5).
- Adding a `claude_session_id` column or new index (sp1 already decided
  against a single-column session index; partial
  `idx_agent_runs_claude_agent_id` already exists from sp1).
- Any change to sibling user-prompt handlers' POST payloads (only the
  shared `_post()` body-reading semantics change).
- Capturing `PreToolUse(Task)` for nested attribution (deferred to v2).

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/cli/hook_handlers.py` | Modify | Refactor `_post()` to fire-and-forget; add 3 new handlers; import `AGENT_TYPE_PATTERN`. |
| `cast-server/cast_server/cli/hook_events.py` | Modify | Extend tuple shape to 4 elements; add 3 new entries; update `DISPATCH` and `COMMAND_FOR_EVENT` derivations. |
| `cast-server/cast_server/cli/install_hooks.py` | Modify | Per-event matcher support; idempotency under matcher. |
| `cast-server/tests/test_cli_hook.py` | Modify | 8 new named tests (see Step 3.6). |
| `cast-server/tests/test_install_hooks.py` | Modify | 4 new named tests (see Step 3.6). |

## Detailed Steps

### Step 3.1: `_post()` fire-and-forget refactor

Modify `cli/hook_handlers.py:_post()` to NOT call `.read()` on the
response — open the connection, send the request body, then return
without waiting for the response body. The 2s urlopen timeout still
bounds the worst case, but the typical path returns immediately after
sending.

Server logs any errors; client never sees them (and shouldn't — hook
never blocks anyway).

Apply to ALL handlers: sibling `user_prompt_start` /
`user_prompt_stop` benefit from the same change (same `_post()`
helper).

Add `test_post_does_not_block_on_response_body` (in `test_cli_hook.py`):
monkeypatch a slow response body, assert handler returns before the
body would have arrived.

### Step 3.2: Extend `HOOK_EVENTS` in `cli/hook_events.py`

Change tuple shape from `(event, subcommand, handler)` to `(event,
subcommand, handler, matcher_or_none)`. Update the existing 2 entries
to add `None` in the 4th slot. Add three new tuples:

```python
("SubagentStart", "subagent-start", _h.subagent_start, None),
("SubagentStop",  "subagent-stop",  _h.subagent_stop,  None),
("PreToolUse",    "skill-invoke",   _h.skill_invoke,   "Skill"),
```

Per the file's canonical-extension comment, this single edit propagates
to `install_hooks.py` (settings injection) and `hook.py` (runtime
dispatch).

Update derivations:

```python
DISPATCH = {sub: handler for _, sub, handler, _matcher in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"cast-hook {sub}" for evt, sub, _h, _m in HOOK_EVENTS}
```

### Step 3.3: Three new handlers in `cli/hook_handlers.py`

Reference payload shapes:
`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`.

#### `subagent_start()`

- Read payload via `_read_payload()`.
- Extract:
  - `agent_type` (e.g. `"cast-foo"` for cast subagents,
    `"Explore"` for built-ins);
  - `session_id`;
  - `agent_id` — **rename to `claude_agent_id` when forwarding** to
    cast-server, per the column-naming decision;
  - `transcript_path`.
  - The `prompt` field is NOT in the `SubagentStart` payload. Pass
    `None` for now. (If a future caller wants it, capture from
    `PreToolUse(Task).tool_input.prompt` correlated via `tool_use_id`
    — out of scope for v1.)
- **Defensive early-return on malformed payload (mirrors `subagent_stop`):**
  if `agent_type` OR `session_id` OR `agent_id` is missing/empty in the
  payload, return early WITHOUT POST. This matches `subagent_stop`'s
  symmetric guard and FR-010 (handlers never block on bad input).
- **Hook-side scope filter (per Decision #2):**
  `from cast_server.cli._cast_name import AGENT_TYPE_PATTERN`. If
  `not AGENT_TYPE_PATTERN.match(agent_type or "")`, return early
  WITHOUT POST. Server keeps its filter as defense in depth.
- POST to `/api/agents/subagent-invocations` with body:

  ```json
  {
    "agent_type": "<agent_type>",
    "session_id": "<session_id>",
    "claude_agent_id": "<agent_id from payload>",
    "transcript_path": "<transcript_path or null>"
  }
  ```

#### `subagent_stop()`

- Read payload; extract `agent_id`. If absent (malformed), early-return
  (do not POST).
- Forward as `claude_agent_id`.
- POST to `/api/agents/subagent-invocations/complete` with body:

  ```json
  {"claude_agent_id": "<agent_id from payload>"}
  ```

#### `skill_invoke()`

- Read payload.
- If `tool_name != "Skill"` → return early (defensive — install side
  already filters via matcher, but handler-side check is cheap
  insurance).
- Extract `session_id`, `tool_input.skill` (**singular** — empirical
  capture confirmed; was incorrectly assumed `skill_name` in original
  draft).
- POST to `/api/agents/subagent-invocations/skill` with body:

  ```json
  {"session_id": "<session_id>", "skill": "<tool_input.skill>"}
  ```

  Wire field is `skill` (singular).

All three handlers exit 0 on any error (mirror sibling pattern;
FR-010).

### Step 3.4: Per-event matcher support in `install_hooks.py`

Extend usage of `HOOK_EVENTS` to handle the new 4-tuple slot.

`install()` (line 97 onward): when iterating `HOOK_EVENTS`, write
`{"matcher": matcher, "hooks": [...]}` when `matcher` is non-None,
else `{"hooks": [...]}`.

`_entry_is_ours()` (line 69) and `uninstall()`: ignore the `matcher`
key when matching ours-vs-not. The HOOK_MARKER (`"cast-hook "`)
substring on the inner `command` is the only ours-vs-theirs signal.

### Step 3.5: Idempotency under matcher

A re-install must not duplicate the `PreToolUse` matcher=`"Skill"`
entry, even if a third-party `PreToolUse` entry exists with a
different matcher. The HOOK_MARKER substring check on the inner
`command` handles this — the matcher key is irrelevant to identity.

Document with a test
(`test_install_preserves_third_party_pretooluse_with_different_matcher`).

### Step 3.6: Tests

Add to `cast-server/tests/test_cli_hook.py`:

```python
def test_subagent_start_posts_for_cast_agent_type
    # happy path; payload includes claude_agent_id (renamed from payload's agent_id)
def test_subagent_start_skips_non_cast_agent_type
    # early-return, no POST (e.g. agent_type="Explore")
def test_subagent_start_skips_when_agent_id_missing
    # defensive: malformed payload (no agent_id) → exit 0, no POST
def test_subagent_start_skips_when_session_id_missing
    # defensive: malformed payload (no session_id) → exit 0, no POST
def test_subagent_start_server_unreachable_exits_zero
def test_subagent_stop_posts_claude_agent_id
    # claude_agent_id is the closure key (was "session_id" in original draft)
def test_subagent_stop_skips_when_claude_agent_id_missing
    # defensive: malformed payload (no agent_id) → exit 0, no POST
def test_skill_invoke_skips_non_skill_tool_name
def test_skill_invoke_extracts_skill_from_tool_input
    # field is `tool_input.skill` (singular), NOT `tool_input.skill_name`
def test_post_does_not_block_on_response_body
    # assert no .read() on the urlopen result
```

Existing tests in `test_cli_hook.py` must still pass after the
`_post()` refactor.

Add to `cast-server/tests/test_install_hooks.py`:

```python
def test_install_hooks_writes_pretooluse_with_skill_matcher
def test_install_preserves_third_party_pretooluse_with_different_matcher
def test_uninstall_removes_ours_regardless_of_matcher
def test_round_trip_install_uninstall_byte_equivalent
```

### Step 3.7: Best-practices delegation

→ Delegate: `/cast-pytest-best-practices` over `test_install_hooks.py`
AND `test_cli_hook.py`. Verify:

- tmp-dir cleanup,
- no leaking writes to dev's real `~/.claude/settings.json`,
- `subprocess`-free (mock urllib at the boundary).

### Step 3.8: Run the test suites

```bash
cd cast-server && uv run pytest \
  tests/test_cli_hook.py \
  tests/test_install_hooks.py \
  -v
```

All listed tests must pass (existing + new).

### Step 3.9: Manual round-trip

```bash
# In a tmp project directory:
mkdir -p /tmp/cast-hook-roundtrip-$$/.claude && cd /tmp/cast-hook-roundtrip-$$
echo '{}' > .claude/settings.json

cast-hook install
cat .claude/settings.json
# Expected: 5 entries — UserPromptSubmit, Stop, SubagentStart, SubagentStop,
#           PreToolUse with matcher: "Skill".

cast-hook uninstall
cat .claude/settings.json
# Expected: all 5 of ours gone; any seeded third-party entries untouched.
```

### Step 3.10: Manual end-to-end with running cast-server

```bash
# With CAST_PORT=8005 cast-server running:
echo '{"agent_type":"cast-foo","session_id":"S1","agent_id":"a1","transcript_path":"/tmp/x.jsonl"}' \
  | cast-hook subagent-start
echo $?    # 0

# Confirm row visible:
curl -s localhost:8005/api/agents/runs?status=running \
  | jq '.[] | select(.agent_name == "cast-foo")'

# Close the row by exact claude_agent_id match:
echo '{"agent_id":"a1","session_id":"S1"}' | cast-hook subagent-stop
echo $?    # 0

# Confirm flipped to completed:
curl -s localhost:8005/api/agents/runs \
  | jq '.[] | select(.claude_agent_id == "a1")'
# → status=completed

# Skill invocation appends to most-recent running cast-* row in S1:
echo '{"session_id":"S1","tool_name":"Skill","tool_input":{"skill":"landing-report"}}' \
  | cast-hook skill-invoke
echo $?    # 0
```

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/test_cli_hook.py` green:
  - existing tests still pass after `_post()` refactor
  - `test_subagent_start_posts_for_cast_agent_type` (happy path; payload
    includes `claude_agent_id`)
  - `test_subagent_start_skips_non_cast_agent_type` (early-return, no
    POST)
  - `test_subagent_start_server_unreachable_exits_zero`
  - `test_subagent_stop_posts_claude_agent_id`
  - `test_subagent_stop_skips_when_claude_agent_id_missing`
  - `test_skill_invoke_skips_non_skill_tool_name`
  - `test_skill_invoke_extracts_skill_from_tool_input`
  - `test_post_does_not_block_on_response_body`
- `pytest cast-server/tests/test_install_hooks.py` green:
  - `test_install_hooks_writes_pretooluse_with_skill_matcher`
  - `test_install_preserves_third_party_pretooluse_with_different_matcher`
  - `test_uninstall_removes_ours_regardless_of_matcher`
  - `test_round_trip_install_uninstall_byte_equivalent`

### Manual Checks

- Manual round-trip (Step 3.9): `cast-hook install` → 5 entries in
  `.claude/settings.json`; `cast-hook uninstall` → all 5 removed;
  third-party untouched.
- Manual end-to-end (Step 3.10) with `CAST_PORT=8005` cast-server
  running: handler subprocesses exit 0; rows created on
  `subagent-start`; flipped to `completed` on `subagent-stop` (by
  exact `claude_agent_id` match); skills appended to the most-recent
  running cast-* row by `skill-invoke`.

### Success Criteria

- [ ] `_post()` is fire-and-forget; existing tests still pass.
- [ ] `HOOK_EVENTS` is 4-tuple shape; 5 entries total (2 sibling + 3
      new).
- [ ] `DISPATCH` and `COMMAND_FOR_EVENT` derivations updated.
- [ ] 3 new handlers exist; hook-side scope filter via
      `AGENT_TYPE_PATTERN`.
- [ ] Handlers translate payload field names: `agent_id` →
      `claude_agent_id`; `tool_input.skill` → wire `skill`.
- [ ] `install_hooks.py` writes `matcher` key when non-None.
- [ ] `cast-hook install` writes 5 entries in tmp project.
- [ ] `cast-hook uninstall` removes all 5 of ours; third-party
      untouched.
- [ ] Re-install is idempotent even with mixed-matcher third-party
      entries.
- [ ] All sp3 tests pass.

## Design Review

- **Architecture:** extends the canonical `HOOK_EVENTS` table per its
  comment; never forks. ✓
- **DRY:** matcher support added once in `install_hooks.py`; no new
  file. Hook-side scope filter shares `AGENT_TYPE_PATTERN` with the
  server filter — single regex, two enforcement points (defense in
  depth). ✓
- **Naming:** handler/subcommand names match Claude Code event naming
  where possible (`subagent-start` / `subagent-stop` / `skill-invoke`).
  Wire field renames (`agent_id` → `claude_agent_id`,
  `tool_input.skill` → `skill`) are documented and tested. ✓
- **Performance:** fire-and-forget `_post()` shaves the ~50-80% of hook
  latency that was blocking on response body. SC-003's <100ms p95
  budget gets healthy headroom.
- **Error & rescue:** handlers exit 0 on any error (per FR-010);
  install / uninstall preserve existing pattern (atomic write,
  malformed-JSON refuses).
- **Compatibility:** the value-shape extension to 4-tuple is a
  breaking change to any external code importing `HOOK_EVENTS`. Quick
  grep — only `install_hooks.py` and `hook.py` import; both updated in
  same sp. No external consumers.

## Execution Notes

- **Spec-linked files:** the per-event matcher contract is a behavior
  change to `cast-hooks.collab.md` (sibling-authored). sp5 should
  ensure the new spec covers the matcher extension OR update sibling
  spec.
- **Defense in depth:** server keeps its `AGENT_TYPE_PATTERN` filter
  (sp2) even though the hook now filters too. Both layers matter —
  server is authoritative; hook avoids pointless POSTs for non-cast
  `Task()` events.
- **Live-settings.json caution:** all install / uninstall tests must
  run in tmp dirs. Verify with `git status` after running tests that
  `~/.claude/settings.json` is untouched.
- **Spike A payload reference:** before writing `subagent_start()`,
  re-read
  `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`
  to confirm the exact key names. The relevant facts:
  - `SubagentStart` carries `agent_id` (renamed
    `claude_agent_id` on the wire); NO `parent_session_id`.
  - `SubagentStop` carries `agent_id` (the closure key);
    NO error/exit field.
  - `PreToolUse(Skill)` carries `tool_input.skill` (singular).
