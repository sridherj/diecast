# Sub-phase 5: settings.json Installer + Tests (User-Safety Critical)

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Replace the placeholder `cli/install_hooks.py` from sp4 with the real **idempotent,
polite-citizen** settings.json injector. Author the gating test suite — including the
**module-level autouse isolation fixture** (Decision #8) that structurally prevents a
runaway test from corrupting the developer's real `~/.claude/settings.json`.

This is the user-safety surface of the project. The installer is one listener among
potentially many; it MUST NEVER override or replace third-party hooks. The tests are the
gating bar.

## Dependencies

- **Requires completed:** sp4 (the `cli/` package, `hook_events.py` constants).
- **Assumed codebase state:** `hook_events.HOOK_EVENTS` and `COMMAND_FOR_EVENT` are
  importable. `cast-hook` console_script is registered. The placeholder `install_hooks.py`
  exists.

## Scope

**In scope:**
- Rewrite `cast-server/cast_server/cli/install_hooks.py` with the full idempotent
  injector + uninstaller from the plan ("New file: install_hooks.py"). ~120 lines.
- New file `cast-server/tests/test_install_hooks.py` with the 18 tests enumerated in the
  plan, including the module-level autouse isolation fixture.
- **Delegate: `/cast-pytest-best-practices`** before considering done (Decision #8 +
  plan's Step 5).

**Out of scope (do NOT do these):**
- Modifying the `cli/` runtime modules (handler, hook.py) — sp4 is done.
- Wiring into `/cast-init` (sp6).
- File locking on settings.json (matches gstack stance — Decision in Risks #6 — locked
  out of v1).
- Writing to the *real* repo's `.claude/settings.json` during testing — the autouse
  isolation fixture is the safety net.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/cli/install_hooks.py` | Rewrite | Placeholder from sp4 |
| `cast-server/tests/test_install_hooks.py` | Create | Does not exist |

## Detailed Steps

### Step 5.1: Rewrite `install_hooks.py`

Use the body verbatim from the plan ("New file: install_hooks.py"). Critical properties to
preserve:

- `HOOK_MARKER = "cast-hook "` (trailing space — important: any command starting with this
  is "ours", and `"cast-hookout-of-band"` would NOT match if such a thing existed).
- `HOOK_TIMEOUT_SECONDS = 3` — written into the settings.json entry.
- `PROJECT_MARKERS = (".git", ".cast", "pyproject.toml", "package.json")`.
- `_settings_path(user_scope, project_root)`: returns
  `Path.home() / ".claude" / "settings.json"` if `user_scope`, else
  `project_root / ".claude" / "settings.json"`.
- `_looks_like_project_root(p)`: returns True if any marker exists at `p`.
- `_load(path)`: missing file → `{}`. Malformed JSON → `SystemExit` with readable message
  including the parse error verbatim.
- `_atomic_write(path, data)`:
  - mkdir parents (`exist_ok=True`).
  - `tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))`.
  - Write JSON with `indent=2` + trailing newline.
  - `os.replace(tmp, path)`.
  - On `OSError`/`PermissionError`: try to unlink `tmp`, then `SystemExit` with a readable
    message naming `--user` as the workaround.
  - **Always cleans up the `.tmp` on exception** — including non-OSError exceptions
    raised between mkstemp and replace. Use a `try`/`except` around the whole body, and
    `tmp.unlink(missing_ok=True)` in the cleanup.
- `install(project_root, user_scope=False)`:
  - If not `user_scope` and `not _looks_like_project_root(project_root)`: print warning
    to stderr (do not block).
  - Load settings, ensure `settings["hooks"]` exists.
  - For each `(event, _, _)` in `HOOK_EVENTS`:
    - Get the existing list at `settings["hooks"][event]` (or empty list, then attach).
    - Detect if **any** of our entries (a hook with `command` starting with
      `HOOK_MARKER`) already exists in this event's array. If yes, skip.
    - Else append `{"hooks": [{"type": "command", "command": cmd, "timeout": HOOK_TIMEOUT_SECONDS}]}`.
  - Atomic write.
  - Print summary (which events received our entry, or "already installed").
  - Return 0.
- `uninstall(project_root, user_scope=False)`:
  - If file missing: print "nothing to do", return 0.
  - For each event in `HOOK_EVENTS`:
    - Filter out entries whose any nested hook starts with `HOOK_MARKER`.
    - If the filtered list is empty, delete the key from `hooks` entirely.
  - If `hooks` is now `{}`, delete that key from settings.
  - Atomic write.
  - Print summary.
  - Return 0.

### Step 5.2: Author `test_install_hooks.py`

The test file MUST start with the autouse isolation fixture before any other code:

```python
import json
from pathlib import Path
import pytest
from cast_server.cli import install_hooks

@pytest.fixture(autouse=True)
def _isolate_settings_filesystem(tmp_path_factory, monkeypatch):
    """SAFETY: structurally prevent any test from touching the dev's real
    ~/.claude/settings.json. Decision #8."""
    tmp_home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(Path, "home", lambda: tmp_home)
    yield
```

Belt-and-suspenders: optionally add a custom `pytest_collection_modifyitems` or a
`conftest.py`-level assertion that `install_hooks._settings_path(user_scope=True, ...)`
resolves under `tmp_path_factory.getbasetemp()`. This assertion is documented in the spec
(sp7).

Then 18 tests (mirror the plan exactly):

```python
def test_install_creates_settings_file_when_missing(tmp_project_root)
def test_install_preserves_existing_unrelated_hooks(tmp_project_root)
def test_install_appends_alongside_existing_user_prompt_submit(tmp_project_root)
def test_install_appends_alongside_existing_stop(tmp_project_root)
def test_install_is_idempotent(tmp_project_root)
def test_install_aborts_on_malformed_json(tmp_project_root)
def test_install_handles_permission_error_readable_message(tmp_project_root)
def test_install_atomic_write_no_partial_on_exception(tmp_project_root, monkeypatch)
def test_install_warns_when_no_project_markers(tmp_dir_no_markers, capsys)
def test_install_no_warning_when_project_markers_present(tmp_project_root, capsys)
def test_install_user_scope_writes_to_home_settings(tmp_project_root)
def test_uninstall_removes_only_cast_hook_entries(tmp_project_root)
def test_uninstall_preserves_third_party_user_prompt_submit_entry(tmp_project_root)
def test_uninstall_preserves_third_party_stop_entry(tmp_project_root)
def test_uninstall_deletes_empty_event_arrays(tmp_project_root)
def test_uninstall_deletes_empty_hooks_dict(tmp_project_root)
def test_uninstall_noop_when_settings_file_missing(tmp_project_root)
def test_round_trip_install_then_uninstall_restores_original_shape(tmp_project_root)
```

Fixtures to add (in this test file or `conftest.py`):

- `tmp_project_root`: returns a tmp dir with a marker file (e.g., `.git/`) created so
  `_looks_like_project_root` returns True. Has a `.claude/` subdir for clarity.
- `tmp_dir_no_markers`: returns a tmp dir with no markers — used to verify the warning.

#### Test bodies — key cases

- `test_install_preserves_existing_unrelated_hooks`:
  Seed `.claude/settings.json` with `{"hooks": {"PostToolUse": [...], "SessionStart": [...]}}`.
  Run `install`. Re-read; assert `PostToolUse` and `SessionStart` arrays are
  byte-for-byte identical to what was seeded (same shape, same keys, same order). Assert
  `UserPromptSubmit` and `Stop` arrays now contain our entry.

- `test_install_appends_alongside_existing_user_prompt_submit`:
  Seed `hooks.UserPromptSubmit` with a single third-party entry. Run `install`. Assert
  the third-party entry is unchanged AND our entry is appended (not prepended; not
  replacing).

- `test_install_appends_alongside_existing_stop`: symmetric to above (Decision #9).

- `test_install_is_idempotent`: run `install` twice. Assert exactly **one** of our
  entries per event.

- `test_install_aborts_on_malformed_json`:
  Write `{not json` to `.claude/settings.json`. Run `install` — must raise `SystemExit`
  with non-zero code. Re-read the file: must be byte-for-byte unchanged from the
  malformed seed.

- `test_install_handles_permission_error_readable_message`:
  Seed a valid file, then `chmod 0o444` on the file (and possibly the parent if needed
  on your OS). Run `install` — `SystemExit` with a message that mentions `--user` (the
  documented workaround). Verify `.tmp` files in the parent dir do not leak (cleanup
  happened).

- `test_install_atomic_write_no_partial_on_exception`:
  Seed a valid file. Monkeypatch `json.dumps` to raise. Run `install` — exception
  propagates (or `SystemExit`); the original file is byte-for-byte preserved; no `.tmp`
  files leak.

- `test_install_warns_when_no_project_markers`: `tmp_dir_no_markers` fixture; assert the
  warning text appears in `capsys.readouterr().err` and the install still proceeds.

- `test_install_no_warning_when_project_markers_present`: assert the warning text does
  NOT appear.

- `test_install_user_scope_writes_to_home_settings`: invoke
  `install(project_root=tmp_project_root, user_scope=True)`. Assert the file written is
  `Path.home() / ".claude/settings.json"` (which the autouse fixture has already pointed
  to a tmp dir).

- `test_uninstall_removes_only_cast_hook_entries`: install then uninstall. Verify our
  entries are gone and the rest of the file is untouched.

- `test_uninstall_preserves_third_party_*`: seed with third-party entry, install ours,
  uninstall ours, verify the third-party entry survives byte-for-byte.

- `test_uninstall_deletes_empty_event_arrays`: install then uninstall in a file that had
  ONLY our entries; assert the `UserPromptSubmit` and `Stop` keys are deleted.

- `test_uninstall_deletes_empty_hooks_dict`: same but assert `hooks` itself is deleted
  from the top-level settings dict.

- `test_uninstall_noop_when_settings_file_missing`: invoke uninstall with no file
  present; assert exit 0 and no exception, no file created.

- `test_round_trip_install_then_uninstall_restores_original_shape`:
  Seed a valid third-party-only settings file. Install, then uninstall. Re-read.
  Compare via `json.loads(seed) == json.loads(written)` (semantic equivalence — order of
  keys may differ after a JSON round-trip, but content must match).

### Step 5.3: Run the suite

```bash
cd cast-server && uv run pytest tests/test_install_hooks.py -v
```

All 18 tests must pass. **Then delegate:**

> Delegate: `/cast-pytest-best-practices` against `cast-server/tests/test_install_hooks.py`
> and act on findings.

Review the skill's output for: fixture scope appropriateness, missing edge cases,
isolation of side effects. Apply changes; re-run.

### Step 5.4: Manual end-to-end

```bash
# Create a tmp project
TMP=$(mktemp -d)
cd $TMP
git init   # marker
mkdir -p .claude
cat > .claude/settings.json <<EOF
{
  "hooks": {
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "echo third-party", "timeout": 5}]}
    ],
    "PostToolUse": [
      {"hooks": [{"type": "command", "command": "echo also-not-ours", "timeout": 5}]}
    ]
  }
}
EOF

cast-hook install
# Read back; expect:
#   - UserPromptSubmit: original entry + our cast-hook entry
#   - Stop: our entry alone
#   - PostToolUse: untouched

cast-hook install
# Idempotent: should report "already installed".

cast-hook uninstall
# Read back; expect:
#   - UserPromptSubmit: only the third-party entry
#   - Stop: deleted (was only ours)
#   - PostToolUse: untouched
```

## Verification

### Automated Tests (permanent)

`cast-server/tests/test_install_hooks.py` — 18 tests with the autouse isolation fixture.

### Validation Scripts (temporary)

The Step 5.4 manual end-to-end against a tmp project.

### Manual Checks

```bash
# Confirm only intended files changed
git status cast-server/cast_server/cli/install_hooks.py cast-server/tests/

# Confirm no test ever wrote to the real ~/.claude
ls ~/.claude/settings.json.tmp* 2>/dev/null   # must be empty
git status ~/.claude/settings.json 2>/dev/null

# Confirm the autouse fixture is in place
grep -n "_isolate_settings_filesystem\|autouse=True" cast-server/tests/test_install_hooks.py
```

### Success Criteria

- [ ] `install_hooks.py` matches the plan body, with `HOOK_MARKER`, atomic write, and
      surgical uninstall.
- [ ] All 18 tests pass.
- [ ] `_isolate_settings_filesystem` autouse fixture is the FIRST fixture in the file.
- [ ] Round-trip install → uninstall restores the seeded settings byte-for-byte
      (or JSON-equivalent).
- [ ] Permission errors and malformed JSON both surface `SystemExit` with readable
      messages; original file untouched.
- [ ] `.tmp` files are cleaned up on every exception path.
- [ ] `/cast-pytest-best-practices` has been invoked and findings addressed.
- [ ] Manual end-to-end against tmp project confirms third-party preservation.

## Execution Notes

- The autouse fixture is **the** load-bearing safety property of this test suite. If it's
  not in place or scoped wrong, a runaway test could corrupt the developer's real
  `~/.claude/settings.json`. Guard it carefully — make it the first thing in the file.
- `Path.home()` monkeypatch must be visible to `install_hooks._settings_path`. Since the
  module imports `Path` at module scope, monkeypatching the `Path` class itself (which is
  what `monkeypatch.setattr(Path, "home", ...)` does) does work. Verify with one
  paranoid test: write a tiny test that calls `install_hooks._settings_path(user_scope=True, project_root=tmp)`
  and asserts the result is under `tmp_path_factory.getbasetemp()`.
- The plan's `_atomic_write` uses `tempfile.mkstemp` which creates the file with mode
  0o600 — fine for our use, but be aware on Windows/CI. We're targeting Linux here per
  the working directory.
- **Spec-linked files:** `docs/specs/cast-hooks.collab.md` (authored in sp7) — this
  installer IS the contract that spec locks in. Every behavior here will be cited as
  spec verification.
- **Skill/agent delegation:** `/cast-pytest-best-practices` is a hard requirement before
  declaring sp5 done. Document the findings in the sub-phase output (or comment in the
  test file).
- The `gstack-settings-hook` reference at `<GSTACK_ROOT>/bin/gstack-settings-hook`
  is the canonical pattern. Worth diffing your final output against to catch missed
  edge cases.
