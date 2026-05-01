# Sub-phase 3 — Hook layer — output

**Status:** Done
**Run:** `run_20260501_121251_faade6`
**Completed:** 2026-05-01T12:20:17+00:00

## Summary

Extended the canonical hook registry from a 3-tuple to a 4-tuple shape (added
optional `matcher` slot), added three new hook handlers (`subagent_start`,
`subagent_stop`, `skill_invoke`), refactored `_post()` to fire-and-forget,
taught `install_hooks.py` to emit per-event `matcher` keys, and added 13
named tests across two files. `cast-hook install` now writes 5 entries into
`.claude/settings.json` (UserPromptSubmit, Stop, SubagentStart, SubagentStop,
PreToolUse with `matcher: "Skill"`); `cast-hook uninstall` removes only ours.

## What changed

### Code

- **`cast-server/cast_server/cli/hook_handlers.py`**
  - `_post()` is now fire-and-forget — returns the `urlopen` result without
    calling `.read()` on it. Same `(URLError, TimeoutError, OSError)` swallow
    semantics. Sibling `user_prompt_*` handlers benefit from the same change.
  - New `subagent_start()`. Imports `AGENT_TYPE_PATTERN` from
    `_cast_name`. Defensive early-returns when `agent_type` /
    `session_id` / `agent_id` is missing OR when `agent_type` is not a
    cast-* name (defense in depth alongside server-side filter). Forwards
    `agent_id` → `claude_agent_id` on the wire.
  - New `subagent_stop()`. Reads `agent_id` from payload (matches
    `SubagentStop` empirical shape). Early-returns on missing key. Forwards
    `agent_id` → `claude_agent_id`.
  - New `skill_invoke()`. Defensive `tool_name == "Skill"` check (insurance
    on top of settings.json matcher). Reads
    `tool_input.skill` (**singular**, per Spike A). Forwards as wire field
    `skill` (singular).

- **`cast-server/cast_server/cli/hook_events.py`**
  - `HOOK_EVENTS` value tuple extended from 3 → 4 elements (added
    `matcher_or_none` slot). Existing 2 entries carry `None` in slot 4.
  - 3 new entries: `SubagentStart` / `SubagentStop` (matcher `None`) and
    `PreToolUse` (matcher `"Skill"`).
  - `DISPATCH` and `COMMAND_FOR_EVENT` derivations updated to ignore the new
    slot.

- **`cast-server/cast_server/cli/install_hooks.py`**
  - Iterates `HOOK_EVENTS` 4-tuple shape; emits `{"matcher": ..., "hooks":
    [...]}` when `matcher is not None`, else flat `{"hooks": [...]}`.
  - Builds `cmd` from `f"{CAST_HOOK_BIN} {sub}"` directly per-tuple
    (decoupled from `COMMAND_FOR_EVENT[event]` so two PreToolUse entries
    with different matchers could coexist in the future).
  - Status messages now key on `sub` (subcommand name) rather than `event`
    so the per-handler granularity is visible.
  - `uninstall()` unpacks the 4-tuple too (the `matcher` is irrelevant for
    ours-vs-theirs identity — only HOOK_MARKER substring on inner `command`
    matters).

- **`cast-server/cast_server/cli/hook.py`**
  - Help text mentions the 3 new subcommands.

### Tests

- **`cast-server/tests/test_cli_hook.py`** — 11 new tests:
  - `test_subagent_start_posts_for_cast_agent_type` (happy path; renames
    `agent_id` → `claude_agent_id`)
  - `test_subagent_start_skips_non_cast_agent_type`
  - `test_subagent_start_skips_when_agent_id_missing`
  - `test_subagent_start_skips_when_session_id_missing`
  - `test_subagent_start_server_unreachable_exits_zero`
  - `test_subagent_stop_posts_claude_agent_id`
  - `test_subagent_stop_skips_when_claude_agent_id_missing`
  - `test_skill_invoke_skips_non_skill_tool_name`
  - `test_skill_invoke_extracts_skill_from_tool_input`
  - `test_post_does_not_block_on_response_body` — monkeypatches `urlopen`
    to return a stub whose `.read()` raises; `_post` must complete without
    calling it.

- **`cast-server/tests/test_install_hooks.py`** — 4 new tests:
  - `test_install_hooks_writes_pretooluse_with_skill_matcher` — verifies
    the `matcher: "Skill"` key on the new PreToolUse entry, and that
    sibling entries do NOT carry a `matcher` key.
  - `test_install_preserves_third_party_pretooluse_with_different_matcher`
    — third-party `matcher: "Bash"` survives install + re-install
    (idempotency under matcher; `_entry_is_ours` ignores matcher).
  - `test_uninstall_removes_ours_regardless_of_matcher` — uninstall
    removes ours by HOOK_MARKER substring, leaves third-party untouched.
  - `test_round_trip_install_uninstall_byte_equivalent` — install +
    uninstall on a 6-event seed restores byte-for-byte equality.

## Verification

### Automated tests — `cast-server/tests/test_cli_hook.py` + `test_install_hooks.py`

```
============================== 46 passed in 0.78s ==============================
```

All 46 tests green (existing 33 + 13 new). No real-network or real-FS
leakage; `~/.claude/settings.json` mtime unchanged through the test run
(09:44 mod time predates any test execution).

### Manual round-trip (Step 3.9)

```
$ cast-hook install
cast-hook: installed entries for user-prompt-start, user-prompt-stop,
  subagent-start, subagent-stop, skill-invoke
```

`.claude/settings.json` after install — 5 entries, PreToolUse carries
`matcher: "Skill"`, every other event carries no matcher key.

```
$ cast-hook uninstall
cast-hook: removed entries for UserPromptSubmit, Stop, SubagentStart,
  SubagentStop, PreToolUse
```

`.claude/settings.json` after uninstall — `{}`.

### Manual end-to-end (Step 3.10) — DEFERRED

The currently-running `cast-server` (PID 1996403, started ~17:23 IST)
predates sp2's `api_agents.py` modifications (mtime 17:28 IST), so its
in-memory FastAPI app does NOT yet expose
`/api/agents/subagent-invocations*`. A direct curl confirms `404 {"detail":
"Not Found"}`.

The hook handlers themselves correctly exited 0 in this state — fire-and-
forget contract holds:

```
$ echo '{"agent_type":"cast-foo",...,"agent_id":"a-sp3-..."}' | cast-hook subagent-start
$ echo $?
0
```

End-to-end DB-row creation against a freshly-restarted cast-server is part
of sp5's close-out smoke. sp3's verifiable surface (handlers compute
correct payload bodies, fire-and-forget POST, settings.json shape, install
/ uninstall round-trip) is fully covered by the automated suite + manual
round-trip.

## Pytest best practices delegation

`/cast-pytest-best-practices` audited both test files against the guide:

- No subprocess; HTTP mocked at the urllib / module-level `_post` boundary
  (test_cli_hook.py).
- Tmp-dir cleanup via pytest's `tmp_path` / `tmp_path_factory`
  (test_install_hooks.py); autouse `_isolate_settings_filesystem` fixture
  rebinds `Path.home` to a tmp dir for every test (Decision #8 paranoid
  isolation).
- AAA pattern present in all new tests.
- `~/.claude/settings.json` mtime unchanged across the full test run —
  zero leakage to dev's real config.

## Files changed

- `cast-server/cast_server/cli/hook_events.py` (modified)
- `cast-server/cast_server/cli/hook_handlers.py` (modified)
- `cast-server/cast_server/cli/install_hooks.py` (modified)
- `cast-server/cast_server/cli/hook.py` (modified — help text only)
- `cast-server/tests/test_cli_hook.py` (modified — 11 new tests)
- `cast-server/tests/test_install_hooks.py` (modified — 4 new tests)
- `docs/execution/cast-subagent-and-skill-capture/_manifest.md` (sp3 row → Done)
- `docs/execution/cast-subagent-and-skill-capture/sp3_hook_layer/output.md` (this file)

## Next steps

- sp4 — `/runs` UI surface: chip-list partial at L2, skills detail at L3,
  `/runs` route parses `skills_used` JSON.
- sp5 — spec capture + e2e smoke. The end-to-end Step 3.10 verification
  belongs in sp5's close-out (after the user restarts cast-server to pick
  up sp2's endpoints).
