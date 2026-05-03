---
feature: cast-hooks
module: cast-server
linked_files:
  - docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md
  - cast-server/cast_server/cli/install_hooks.py
  - cast-server/cast_server/cli/hook_events.py
  - cast-server/cast_server/cli/hook.py
  - cast-server/cast_server/cli/hook_handlers.py
  - pyproject.toml
  - skills/claude-code/cast-init/SKILL.md
  - cast-server/tests/test_install_hooks.py
last_verified: "2026-05-01"
---

# Cast Hook Install / Uninstall — Spec

> **Spec maturity:** draft
> **Version:** 2
> **Updated:** 2026-05-01
> **Status:** Draft

## Intent

Cast-server installs Claude Code hooks via the `cast-hook install` command.
The installer is a *polite citizen* in the user's `.claude/settings.json` —
it is one listener among potentially many. It NEVER replaces or breaks
third-party or pre-existing user hooks; it only appends its own entries
(idempotent) and surgically removes them on `cast-hook uninstall`. All
writes are atomic; malformed JSON refuses to overwrite; permission errors
surface a readable message instead of a traceback.

The lifecycle that these hooks drive — capturing user-typed `/cast-*`
slash commands as top-level `agent_run` rows — is the subject of
[`cast-user-invocation-tracking.collab.md`](./cast-user-invocation-tracking.collab.md).
This spec is exclusively about the install surface, the on-disk safety
properties, and the third-party-preservation guarantees that make
`cast-hook install` safe to run against any pre-existing
`.claude/settings.json`.

This is a **critical user-safety contract**. A buggy installer that wipes
or corrupts a user's `settings.json` destroys their Claude Code hook
configuration silently — including hooks they wrote themselves or
installed from other tools. The polite-citizen framing is load-bearing.

The canonical install entry point in a fresh Diecast project is
`/cast-init` Step 4 (see
[`skills/claude-code/cast-init/SKILL.md`](../../skills/claude-code/cast-init/SKILL.md)).
That step is **default ON** (opt out with `--no-hooks`) and delegates to
the same `cast-hook install` console script described here.

## User Stories

### US1 — Coexists with third-party `UserPromptSubmit` hooks (Priority: P1)

**As a** user with an existing third-party `UserPromptSubmit` hook (e.g., a
linter, a logger, another agent framework), **I want** `cast-hook install`
to leave that entry verbatim and add ours alongside it, **so that** both
hooks fire on every prompt and my prior tooling continues to work.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_preserves_third_party_user_prompt_submit`
seeds a `settings.json` with a third-party `UserPromptSubmit` entry,
runs `install(...)`, and asserts the third-party entry survives byte-for-byte
and our entry is appended to the same array.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `install(...)` runs against a `settings.json` whose
  `hooks.UserPromptSubmit` array already contains a third-party entry, THE
  SYSTEM SHALL leave that entry's command, timeout, and shape untouched and
  append our `{"type":"command","command":"cast-hook user-prompt-start","timeout":3}`
  entry to the same array.
- **Scenario 2:** WHEN both hooks are installed, THE SYSTEM SHALL emit a
  `settings.json` whose `hooks.UserPromptSubmit` length is exactly the
  third-party count + 1.

### US2 — Coexists with third-party `Stop` hooks (Priority: P1)

**As a** user with an existing third-party `Stop` hook, **I want** the same
preservation guarantee for `Stop` as for `UserPromptSubmit`, **so that**
turn-end tooling I rely on keeps working.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_preserves_third_party_stop`
seeds a third-party `Stop` entry and asserts the same coexistence shape.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `install(...)` runs against a `settings.json` with a
  third-party `Stop` entry, THE SYSTEM SHALL preserve that entry verbatim
  and append our `{"type":"command","command":"cast-hook user-prompt-stop","timeout":3}`
  entry to the same array.

### US3 — Preserves all unrelated events (Priority: P1)

**As a** user with hooks on events we don't touch (`PostToolUse`,
`SubagentStart`, `SessionEnd`, `PreCompact`, etc.), **I want** those events
to be untouched by both install and uninstall, **so that** the installer's
blast radius is exactly `UserPromptSubmit` + `Stop` and nothing else.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_preserves_unrelated_events`
seeds entries on `PostToolUse`, `SubagentStart`, etc., runs install,
runs uninstall, and asserts the unrelated events are byte-for-byte
preserved across both operations.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `install(...)` or `uninstall(...)` runs against a
  `settings.json` containing entries on any event other than the two in
  `HOOK_EVENTS` (`UserPromptSubmit`, `Stop`), THE SYSTEM SHALL leave those
  entries untouched.
- **Scenario 2:** WHEN `install(...)` runs, THE SYSTEM SHALL preserve every
  top-level key in `settings.json` other than `hooks` byte-for-byte (e.g.,
  `permissions`, `theme`, `model`, custom user keys).

### US4 — Idempotent install (Priority: P1)

**As a** user re-running `cast-hook install` (or `/cast-init`), **I want** the
second run to be a no-op, **so that** my `settings.json` does not accumulate
duplicate hook entries.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_install_is_idempotent`
runs `install(...)` twice and asserts the second run leaves
`hooks.UserPromptSubmit` and `hooks.Stop` at length 1 each (with a
`already installed` log line on the second pass).

**Acceptance scenarios:**

- **Scenario 1:** WHEN `install(...)` finds a bucket that already contains
  an entry whose any `hooks[*].command` starts with the marker
  `cast-hook ` (trailing space), THE SYSTEM SHALL skip appending and treat
  the bucket as up-to-date.
- **Scenario 2:** WHEN both buckets are already up-to-date, THE SYSTEM SHALL
  still atomically rewrite the file (round-trip safe) and exit 0 with a
  human-readable `already installed` message per event.

### US5 — Surgical uninstall (Priority: P1)

**As a** user uninstalling cast-hooks, **I want** ONLY our entries removed —
nothing else — **so that** uninstall is reversible without collateral
damage.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_uninstall_is_surgical`
seeds a `settings.json` containing our entries, third-party entries on the
same events, and entries on unrelated events, runs `uninstall(...)`, and
asserts (a) only our entries are gone, (b) the third-party entries are
byte-for-byte preserved, (c) unrelated events are untouched, (d) buckets
that become empty are dropped, and (e) if `hooks` becomes empty the key
itself is dropped.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `uninstall(...)` runs, THE SYSTEM SHALL remove ONLY
  entries whose `hooks[*].command` starts with `HOOK_MARKER = "cast-hook "`
  (trailing space). All other entries on the same event MUST survive.
- **Scenario 2:** WHEN removing our entries makes an event's array empty,
  THE SYSTEM SHALL drop the event key from `hooks`.
- **Scenario 3:** WHEN removing event keys makes the `hooks` block empty,
  THE SYSTEM SHALL drop the `hooks` key from the top-level settings.

### US6 — Refuses to corrupt malformed settings (Priority: P1)

**As a** user with a malformed `.claude/settings.json` (e.g., a stray comma,
a half-edited file), **I want** `cast-hook install` to refuse rather than
overwrite, **so that** my partially-edited file is not destroyed by a
"helpful" rewrite.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_install_refuses_malformed_json`
writes invalid JSON to `settings.json`, runs `install(...)`, and asserts
the call raises `SystemExit` with a readable message and the file is
byte-for-byte unchanged on disk.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `_load(path)` cannot parse the existing
  `settings.json` as JSON, THE SYSTEM SHALL raise `SystemExit` with the
  message `cast-hook: refusing to overwrite malformed settings.json at
  <path>: <error>. Fix or remove the file and retry.` and exit non-zero.
- **Scenario 2:** WHEN install aborts on malformed JSON, THE SYSTEM SHALL
  perform NO writes — the original file is untouched and no `.tmp` file
  is left behind.

### US7 — Survives filesystem failures gracefully (Priority: P1)

**As a** user on a read-only filesystem, with a full disk, or with locked
parent directories, **I want** the installer to surface a readable error
instead of a Python traceback, **so that** I know what to do (typically
`--user`).

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_install_handles_oserror`
patches `os.replace` (or `tempfile.mkstemp`) to raise `OSError` /
`PermissionError`, runs `install(...)`, and asserts (a) `SystemExit` with
a readable message naming `--user` as the workaround, (b) any `.tmp` file
created during the attempt is cleaned up, (c) the original `settings.json`
is untouched.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `_atomic_write` raises `OSError` or
  `PermissionError`, THE SYSTEM SHALL clean up the `.tmp` file (best-effort
  via `Path.unlink(missing_ok=True)`) and raise `SystemExit` with the
  message `cast-hook: cannot write <path>: <error>. Try \`cast-hook
  install --user\` to write to ~/.claude/settings.json instead.`.
- **Scenario 2:** WHEN any other `BaseException` interrupts the write
  (e.g., `KeyboardInterrupt`), THE SYSTEM SHALL still clean up the `.tmp`
  file before re-raising.

### US8 — Atomic on disk (Priority: P1)

**As a** user, **I want** partial writes to never reach the live
`settings.json`, **so that** an interrupt mid-write cannot corrupt my
configuration.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_atomic_write_uses_replace`
patches `tempfile.mkstemp` and `os.replace` and asserts the write goes
through `mkstemp` → write → `os.replace`, never directly to the final
path.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `_atomic_write` runs, THE SYSTEM SHALL create a
  temp file via `tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)`,
  write the JSON payload to it, fsync via the file handle close, and call
  `os.replace(tmp, path)` to swap into place.
- **Scenario 2:** WHEN the swap completes, THE SYSTEM SHALL never leave a
  `.tmp` file alongside the final `settings.json` on the success path.

### US9 — Project-aware install scope (Priority: P1)

**As a** user installing from a project root, **I want** the default to
write to `<project_root>/.claude/settings.json`, **so that** the hooks are
scoped to the project I'm working on. **As a** user passing `--user`, **I
want** to install to `~/.claude/settings.json` instead.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_settings_path_resolution`
asserts `_settings_path(user_scope=False, project_root=...)` returns
`<project_root>/.claude/settings.json` and `_settings_path(user_scope=True,
...)` returns `~/.claude/settings.json`. A second case asserts that
running with `user_scope=False` from a directory missing all of
`.git`/`.cast`/`pyproject.toml`/`package.json` emits a stderr warning but
does not block the install.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `install(project_root=p, user_scope=False)` runs,
  THE SYSTEM SHALL resolve the target as `p / ".claude" / "settings.json"`
  and create `.claude/` if missing.
- **Scenario 2:** WHEN `install(project_root=p, user_scope=True)` runs,
  THE SYSTEM SHALL resolve the target as `~/.claude/settings.json`
  regardless of `p`.
- **Scenario 3:** WHEN `user_scope=False` and `project_root` lacks all of
  `(.git, .cast, pyproject.toml, package.json)`, THE SYSTEM SHALL emit a
  stderr warning `does not look like a project root` and proceed with the
  install (warn, do not block).

### US10 — Single source of truth for hook events (Priority: P1)

**As a** maintainer, **I want** `(event, subcommand, handler)` tuples
defined in exactly one module, **so that** install-side and runtime-side
cannot drift.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_uses_hook_events_module`
imports `cli.hook_events` and asserts (a) `HOOK_EVENTS` is the canonical
list of `(event, subcommand, handler)` tuples, (b) `DISPATCH` is derived
from it (mapping subcommand → handler), and (c) `COMMAND_FOR_EVENT` is
derived from it (mapping event → `f"cast-hook {sub}"`). A second case
asserts `install(...)` writes a `command` field that exactly matches
`COMMAND_FOR_EVENT[event]`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `install(...)` builds the entry to append, THE
  SYSTEM SHALL read the command string from `COMMAND_FOR_EVENT[event]` —
  not from a hardcoded literal.
- **Scenario 2:** WHEN `cast-hook <sub>` dispatches at runtime, THE SYSTEM
  SHALL look the handler up via `DISPATCH[sub]` — not from a hardcoded
  if/elif chain.
- **Scenario 3:** WHEN a new event/subcommand pair is added, THE SYSTEM
  SHALL require exactly one edit (to `HOOK_EVENTS` in
  `cli/hook_events.py`); install-side and runtime-side pick up the change
  with no further coordination.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `HOOK_MARKER = f"{CAST_HOOK_BIN} "` (the absolute path to the cast-hook wrapper, trailing space). Any settings.json `hooks[*].hooks[*].command` whose value starts with this string is "ours" for install dedup and uninstall removal. The literal value of `CAST_HOOK_BIN` is `{Path.home()}/.claude/skills/diecast/bin/cast-hook` resolved at install time. | Single literal source; defined in `cli/install_hooks.py` via `cli/hook_events.CAST_HOOK_BIN`. |
| FR-002 | Hook command shape MUST be `<absolute_path>/cast-hook <subcommand>` where `<absolute_path>` is `~/.claude/skills/diecast/bin/cast-hook` resolved through the diecast skill-root symlink that `./setup` creates. PATH-based resolution is FORBIDDEN: Claude Code fires hooks with a restricted shell PATH that does not reliably include `~/.local/bin/` or `<repo>/.venv/bin/`, so bare command names misfire silently. The installer MUST refuse to write entries when `CAST_HOOK_BIN` is missing on disk (fails with a "run ./setup --upgrade" message). | Reliable hook firing across all shell environments. The command string is per-machine (different `$HOME`); `settings.json` is per-machine anyway. |
| FR-003 | The atomic write contract is `tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)` → write → `os.replace(tmp, path)`. The tmp file MUST be cleaned up on every exception path (including `OSError`, `PermissionError`, `KeyboardInterrupt`, and any other `BaseException`). | `cli/install_hooks.py::_atomic_write`. |
| FR-004 | Malformed JSON in the target settings file MUST raise `SystemExit` with a readable message. The original file MUST NOT be overwritten and no `.tmp` file is left behind. | `_load(path)` enforces this. |
| FR-005 | `OSError` / `PermissionError` during `_atomic_write` MUST raise `SystemExit` with a readable message that names `cast-hook install --user` as the workaround. | Read-only fs, full disk, locked file. |
| FR-006 | Settings file missing on `uninstall(...)` MUST print `cast-hook: nothing to do — <path> does not exist.` and return 0. | Uninstall is unconditionally safe. |
| FR-007 | The marker for "ours" is `command.startswith(HOOK_MARKER)`. Idempotency dedup and surgical uninstall both key off this marker — no other identifier (no GUID, no comment, no separate file). | The marker constant is the only matcher. |
| FR-008 | Non-list values found at `hooks.<event>` (e.g., a foreign tool wrote a dict there) MUST raise `SystemExit` with `settings.json hooks.<event> is not a list (got <type>); refusing to modify.` rather than silently coerce. | Defends against schema drift. |
| FR-009 | The hook command's `timeout` field MUST be `3` seconds. The hook handler is required to be sub-second; the timeout is the user-protection ceiling. | `HOOK_TIMEOUT_SECONDS = 3` in `cli/install_hooks.py`. |
| FR-010 | Project-root detection markers are `(.git, .cast, pyproject.toml, package.json)`. Missing all four when installing at project scope produces a stderr warning but does NOT block the install. | Warn-don't-block keeps the installer usable from non-conventional layouts. |
| FR-011 | The canonical `(event, subcommand, handler)` mapping lives in `cli/hook_events.py`. `install_hooks.py` (write side) and `hook.py` (runtime dispatch) MUST import from this module. Drift between install and dispatch is structurally impossible. | Decision #10 of the source plan. |
| FR-012 | Concurrency on `settings.json` is NOT handled. Two `cast-hook install` processes racing each other on the same path is an unsupported scenario; the last writer wins. | Documented limitation. Matches gstack's stance. |
| FR-013 | `cast-hook` is registered as a console script in `pyproject.toml` `[project.scripts]` so `uv run cast-hook` resolves correctly inside the project venv. End-users do NOT invoke the bare console script. They invoke the bash wrapper at `<repo>/bin/cast-hook` (which `exec`s `uv run --project <repo> -- cast-hook "$@"`), which is reachable as `~/.claude/skills/diecast/bin/cast-hook` through the umbrella symlink installed by `./setup`. | Decision #6 of the source plan; updated for the gstack-pattern install seam. |
| FR-014 | `./setup` (and `./setup --upgrade`) MUST create `~/.claude/skills/diecast` as a symlink to the repo root. Idempotent: removes any existing symlink and backs up any pre-existing real path under `~/.claude/.cast-bak-<ts>/` before re-linking. The symlink is the single source of truth for resolving cast-hook + cast-server from outside the repo. | `cast_server.bootstrap.common.install_diecast_skill_root`, `setup_flow::step5a_install_diecast_skill_root`. |
| FR-015 | `./setup --upgrade` MUST remove any pre-existing `~/.local/bin/cast-server` shim (backed up under `~/.claude/.cast-bak-<ts>/`). The PATH-based shim from earlier Diecast versions is no longer maintained. | `setup::step5_remove_legacy_shim`. Decision: clean-cut migration, no backward-compat for the old shim location. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Installing into a `settings.json` with third-party `UserPromptSubmit` and `Stop` entries leaves both verbatim and appends ours alongside. | `tests/test_install_hooks.py::test_preserves_third_party_*`. |
| SC-002 | Installing into a `settings.json` with entries on unrelated events (`PostToolUse`, `SubagentStart`, etc.) and unrelated top-level keys (`permissions`, `theme`) preserves them byte-for-byte across install and uninstall. | `tests/test_install_hooks.py::test_preserves_unrelated_events`. |
| SC-003 | Re-running `install(...)` is a no-op: bucket lengths stay at "third-party + 1" and a `already installed` log line is emitted per event. | `tests/test_install_hooks.py::test_install_is_idempotent`. |
| SC-004 | Uninstall removes ONLY entries whose `command` starts with `HOOK_MARKER`. Empty buckets are dropped, and a fully-empty `hooks` block is also dropped. | `tests/test_install_hooks.py::test_uninstall_is_surgical`. |
| SC-005 | Installing against malformed JSON raises `SystemExit` and never overwrites the file or leaves a `.tmp` artifact. | `tests/test_install_hooks.py::test_install_refuses_malformed_json`. |
| SC-006 | A simulated `OSError` during write surfaces a readable error naming `--user` and cleans up the `.tmp` file. | `tests/test_install_hooks.py::test_install_handles_oserror`. |
| SC-007 | The on-disk write goes through `tempfile.mkstemp` → `os.replace` and never opens the final path directly for write. | `tests/test_install_hooks.py::test_atomic_write_uses_replace`. |
| SC-008 | Adding a new `(event, subcommand, handler)` tuple requires exactly one edit (to `HOOK_EVENTS`) — install-side, dispatch-side, and the test that asserts coverage of every entry update without further coordination. | `tests/test_install_hooks.py::test_uses_hook_events_module` + dispatch coverage assertion. |

## Verification

Live coverage for this spec is asserted by:

- `cast-server/tests/test_install_hooks.py` — the gating test suite for
  every behavior locked above. The plan calls this out as a critical
  user-safety surface; the test suite is the gate.

**Module-level autouse isolation fixture (non-negotiable safety property):**
the test suite MUST use a module-level autouse fixture that redirects
`HOME` and the project-root path used by every test into a per-test
`tmp_path`. Without this fixture, a single misbehaving test would write
into the developer's real `~/.claude/settings.json`. Decision #8 of the
source plan: this fixture is non-negotiable and reviewers MUST reject any
test in this file that bypasses it. The fixture lives at the top of
`tests/test_install_hooks.py`.

This spec does not enumerate test cases inline; it cites where the live
coverage lives. The plan
(`docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`) is the
rationale archive — read it for the "why" behind the locked decisions
referenced above. The canonical reference pattern (atomic settings.json
injection in another tool) is
`<GSTACK_ROOT>/bin/gstack-settings-hook`.

## Out of scope

The following items are explicitly NOT covered by this spec; they are
deferred to future sub-phases.

- **File locking on `settings.json`.** Concurrent `cast-hook install`
  invocations on the same path are an unsupported scenario in v1. Matches
  gstack's stance.
- **Auto-uninstall on package removal.** Removing the `cast-server`
  package does NOT remove its hook entries from `settings.json`; the user
  runs `cast-hook uninstall` explicitly.
- **Multi-machine routing.** v1 writes to one settings file at a time
  (project or user scope, never both). Cross-machine sync of
  `settings.json` (e.g., via dotfiles repos) is the user's concern.
- **Adding more events** (`PostToolUse`, `SessionStart`, `PreCompact`,
  etc.). The contract supports it via the single source of truth in
  `cli/hook_events.py`, but no other event is registered in v1.
- **Detecting and removing legacy / pre-marker cast-hook entries.** The
  marker is the only identity check; if a prior version of cast-hook ever
  shipped a different command shape, manual cleanup is required.

## Cross-references

- User-invocation lifecycle that uses these hooks: see
  [`cast-user-invocation-tracking.collab.md`](./cast-user-invocation-tracking.collab.md).
- Task()-dispatched subagent + Skill-event capture path. Extends the
  install contract with a per-event `matcher` slot in `HOOK_EVENTS`
  (4-tuple shape) — `cli/install_hooks.py` emits
  `{"matcher": ..., "hooks": [...]}` when the matcher is non-`None`,
  matcher-aware idempotency keeps third-party `PreToolUse(matcher="Bash")`
  entries safe under our `PreToolUse(matcher="Skill")` install/uninstall.
  See
  [`cast-subagent-and-skill-capture.collab.md`](./cast-subagent-and-skill-capture.collab.md).
- Install entry point in a fresh project (default ON; opt out with
  `--no-hooks`): `/cast-init` Step 4 in
  [`skills/claude-code/cast-init/SKILL.md`](../../skills/claude-code/cast-init/SKILL.md).
- Reference pattern for atomic `settings.json` injection:
  `<GSTACK_ROOT>/bin/gstack-settings-hook`.

## Open Questions

- **[USER-DEFERRED]** Whether to add a comment marker to our hook entries
  for human-readability when the user opens `settings.json` manually.
  Reason: deferred because the JSON spec does not allow comments, and a
  sidecar field (e.g., `"_origin": "cast-hook"`) bloats the file without
  adding behavior — the existing `command` prefix is sufficient
  identity.
- **[USER-DEFERRED]** Whether to detect and migrate legacy cast-hook entry
  shapes if the command marker ever changes. Reason: deferred until the
  first time we ship a marker change; v1 has only one marker and there is
  no legacy to migrate.
