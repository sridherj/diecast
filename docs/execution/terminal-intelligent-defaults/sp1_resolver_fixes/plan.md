# Sub-phase 1: Resolver Fixes — Key Alias, De-Vendor, Loud Failure

> **Pre-requisite:** Read `docs/execution/terminal-intelligent-defaults/_shared_context.md` before starting this sub-phase.

## Objective

Make terminal resolution honest: accept the `terminal:` config-key alias for back-compat (the bug that caused the original 30s timeout), de-vendor the duplicate resolver in `cast-server`, improve `ResolutionError`'s message to point at the new `--fix-terminal` flow, and stop silently swallowing `ResolutionError` in the tmux manager so dispatch fails immediately with a structured error instead of after a 30s readiness timeout. This is commit 1 of the planned 2-commit PR — fully self-contained and unit-testable on its own.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** `agents/_shared/terminal.py` (lines 26-106) and `cast-server/cast_server/infra/terminal.py` (lines 30-82) are duplicate copies; `cast-server/cast_server/infra/tmux_manager.py:78-92` swallows `ResolutionError` into a `WARNING` log; `cast-server/cast_server/services/agent_service.py:1674` and `:1716` call `tmux.open_terminal(...)` and do not currently catch `ResolutionError`; `tests/test_b6_terminal_resolution.py` is 100 lines covering the resolution chain.

## Scope

**In scope:**

- Update `_config_default()` in `agents/_shared/terminal.py` to accept both `terminal_default` (canonical, preferred) and `terminal` (alias, back-compat). `terminal_default` wins when both are present.
- Improve `ResolutionError`'s message in place (no new exception class) to point at `bin/cast-doctor --fix-terminal` and to show all three resolution sources.
- Add an `_autodetect()` helper to `agents/_shared/terminal.py` that probes platform-appropriate terminals. **Used only by the first-run setup flow in sp2** — `resolve_terminal()` does NOT call `_autodetect()`. (Adding the helper here keeps the canonical resolver as the single source of truth for terminal probing logic.)
- Decide whether to add `foot` and/or `konsole` to `_SUPPORTED` (see Open Question #1 in `_review_summary.md` — must be resolved before this sub-phase starts).
- De-vendor `cast-server/cast_server/infra/terminal.py` — replace its body with a thin re-export shim from `agents._shared.terminal`. Ensure `agents/` is importable from cast-server's runtime (verify, fix `sys.path` only if needed).
- In `cast-server/cast_server/infra/tmux_manager.py`, change `_resolved_terminal()` to **re-raise** `ResolutionError` (with the same exception object) rather than log a warning and return `None`. The `shutil.which()` PATH-not-found check stays — but it should also raise `ResolutionError` with a clear message instead of silently disabling visible terminals.
- In `cast-server/cast_server/services/agent_service.py`, wrap `tmux.open_terminal(...)` in a `try`/`except ResolutionError` at both call sites (child run path ~line 1674, top-level path ~line 1716). On error: kill the tmux session via `tmux.kill_session(session_name)`, log the structured message, and raise `TmuxError` (or fail the run with the structured message — match existing failure mechanics in the surrounding code).
- Extend `tests/test_b6_terminal_resolution.py` in place: tests for `_autodetect()` probe order on Linux per `XDG_CURRENT_DESKTOP`, macOS `iterm`/`terminal` key emission, the `terminal:` alias, the canonical-wins-over-alias precedence, the improved `ResolutionError` message, and updated `test_first_run_prompt_*` tests if their semantics changed.

**Out of scope (do NOT do these):**

- `bin/cast-doctor` modifications (`--fix-terminal` flag, hardcoded-fallback list, parity test) — sp2.
- `docs/reference/supported-terminals.md` updates — sp2.
- `tests/test_cast_doctor.py` — sp2.
- Real headless dispatch (`kick_winch`, `--print` exploration). Out of scope for the entire PR per plan §0.
- Changes to `config.headless` / `config.interactive` semantics. Today's warning at `agent_service.py:1704-1708` keeps describing today's behavior.
- A new typed `TerminalNotFound` exception class — explicitly rejected in plan Decision 2026-04-30T20:50:00Z.
- `wezterm` support — separate PR per Decision in plan Out-of-Scope.
- Any change to `agents/_shared/terminal.py:resolve_terminal()` that calls `_autodetect()` during dispatch. Auto-detect runs only at first-run setup.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/_shared/terminal.py` | Modify | Canonical resolver, 107 lines. `_config_default` reads only `terminal_default`. No `_autodetect`. |
| `cast-server/cast_server/infra/terminal.py` | Modify (shrink to shim) | Vendored copy, 82 lines duplicating `agents/_shared/terminal.py`. |
| `cast-server/cast_server/infra/tmux_manager.py` | Modify | `_resolved_terminal()` swallows `ResolutionError` and PATH-miss into warnings (lines 78-92). |
| `cast-server/cast_server/services/agent_service.py` | Modify | Calls `tmux.open_terminal(...)` at ~lines 1674 and ~1716; does not catch `ResolutionError`. |
| `tests/test_b6_terminal_resolution.py` | Modify (extend) | 100 lines covering the resolution chain. |

## Detailed Steps

### Step 1.1: Decide `_SUPPORTED` additions

Before touching code, confirm Open Question #1 in `_review_summary.md` is resolved. If `foot` and/or `konsole` are added, draft their entries:

```python
# Plausible defaults — verify against each terminal's CLI before committing:
"foot":     {"new_tab_flag": "",                       "cwd_flag": "--working-directory="},
"konsole":  {"new_tab_flag": "--new-tab",              "cwd_flag": "--workdir "},
```

Validate by running `foot --help` / `konsole --help` on a Linux box (or reading the upstream docs) and adjust the flag strings to match. If neither candidate is approved, skip this step — `_SUPPORTED` retains its current 6 entries.

### Step 1.2: `agents/_shared/terminal.py` — accept `terminal:` alias

Update `_config_default()` to read both keys. `terminal_default` wins when both are present:

```python
def _config_default(config_path: Optional[Path] = None) -> Optional[str]:
    path = config_path or Path.home() / ".cast" / "config.yaml"
    if not path.exists():
        return None
    try:
        cfg = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(cfg, dict):
        return None
    # Accept both keys for back-compat. `terminal_default` is canonical and wins
    # when both are present; `terminal:` is the alias originally written by
    # `cast init` / docs (see plan §1 for history).
    for key in ("terminal_default", "terminal"):
        value = cfg.get(key)
        if isinstance(value, str) and value:
            return value
    return None
```

Note: `test_malformed_config_yields_error_not_crash` expects `ResolutionError` for a malformed YAML, but the current implementation returns `None` from `_config_default()` and lets `resolve_terminal()` raise. That's still fine — leave the existing flow alone.

### Step 1.3: `agents/_shared/terminal.py` — improve `ResolutionError` message

Update `resolve_terminal()` to build a message that names every source actually checked and points at `bin/cast-doctor --fix-terminal`:

```python
def resolve_terminal(config_path: Optional[Path] = None) -> ResolvedTerminal:
    cast_term = os.environ.get("CAST_TERMINAL")
    sys_term  = os.environ.get("TERMINAL")
    cfg_term  = _config_default(config_path)

    raw = cast_term or sys_term or cfg_term
    if not raw:
        cfg_path = config_path or Path.home() / ".cast" / "config.yaml"
        msg = (
            "no terminal configured.\n"
            f"  tried: $CAST_TERMINAL ({'set: ' + cast_term if cast_term else 'unset'}), "
            f"$TERMINAL ({'set: ' + sys_term if sys_term else 'unset'}),\n"
            f"         {cfg_path} "
            f"({'no terminal_default/terminal key' if cfg_path.exists() else 'file missing'}).\n"
            "  fix:   run `bin/cast-doctor --fix-terminal` to auto-detect and configure,\n"
            "         or set $CAST_TERMINAL=<your-terminal> manually.\n"
            "         See docs/reference/supported-terminals.md."
        )
        raise ResolutionError(msg)
    parts = shlex.split(raw)
    cmd, *args = parts
    flags = dict(_SUPPORTED.get(Path(cmd).name, {}))
    return ResolvedTerminal(command=cmd, args=args, flags=flags)
```

The exact wording can vary, but the message MUST contain:
- The literal strings `$CAST_TERMINAL`, `$TERMINAL`, and `terminal_default` (existing tests in `test_unset_raises_with_docs_link` assert these).
- The literal string `bin/cast-doctor --fix-terminal`.
- The literal string `supported-terminals.md`.

### Step 1.4: `agents/_shared/terminal.py` — add `_autodetect()` helper

Append a new private helper. **`resolve_terminal()` must NOT call this** — it is consumed exclusively by `bin/cast-doctor --fix-terminal` (in sp2) and by the new tests added in this sub-phase.

```python
import platform
import shutil
from typing import Iterable

# Linux probe order — favors GNOME stack, then misc tabbed terminals.
# Re-ordered at probe time per $XDG_CURRENT_DESKTOP.
_LINUX_PROBE_ORDER: tuple[str, ...] = tuple(
    k for k in _SUPPORTED if k not in ("iterm", "terminal")
)


def _autodetect(
    *,
    system: Optional[str] = None,
    desktop: Optional[str] = None,
    iterm_app_path: Path = Path("/Applications/iTerm.app"),
    which: callable = shutil.which,
) -> list[str]:
    """Return ordered candidates from `_SUPPORTED.keys()` available on this host.

    Args:
        system: Override `platform.system()`. Tests inject "Darwin" / "Linux".
        desktop: Override `$XDG_CURRENT_DESKTOP`. Tests inject "GNOME" / "KDE".
        iterm_app_path: Override iTerm.app probe path (macOS only).
        which: Override `shutil.which`. Tests inject a fake.

    Returns:
        Ordered candidate keys from `_SUPPORTED`. Empty list when nothing matches.
        First entry is the recommended default; caller (cast-doctor) decides
        whether to confirm-and-write (single candidate) or prompt (multiple).
    """
    sys_name = system or platform.system()
    if sys_name == "Darwin":
        candidates: list[str] = []
        if iterm_app_path.exists():
            candidates.append("iterm")
        candidates.append("terminal")  # always present on macOS
        return candidates

    # Linux (and BSD, WSL — anything non-Darwin).
    desktop = desktop if desktop is not None else os.environ.get("XDG_CURRENT_DESKTOP", "")
    desktop = desktop.upper()
    order: list[str] = list(_LINUX_PROBE_ORDER)
    if "GNOME" in desktop:
        # ptyxis already first; gnome-terminal already second — keep as-is.
        pass
    elif "KDE" in desktop and "konsole" in _SUPPORTED:
        # konsole bumps to front when KDE detected (only if konsole approved for _SUPPORTED).
        order.remove("konsole")
        order.insert(0, "konsole")
    return [name for name in order if which(name) is not None]
```

If `foot` / `konsole` were not added to `_SUPPORTED` in Step 1.1, drop the `konsole` branch from the body (the `which` filter still drops anything not on PATH — so leaving the branch is harmless, just dead).

### Step 1.5: De-vendor `cast-server/cast_server/infra/terminal.py`

Replace the body with a thin re-export shim:

```python
"""Re-export shim — single source of truth is agents/_shared/terminal.py.

Earlier revisions vendored the resolver here because cast-server could not rely
on agents/ being importable. That gap is now closed (see ensure-importable
note below). All resolver logic lives in agents/_shared/terminal.py.
"""
from __future__ import annotations

# When cast-server is installed as an editable package (uv pip install -e .),
# the agents/ tree must already be on sys.path. Verify in a fresh checkout
# before relying on this; if missing, add `sys.path.insert(0, REPO_ROOT)` to
# cast-server's package __init__.py — but prefer the import-path fix to a
# vendored copy.
from agents._shared.terminal import (  # noqa: F401
    _SUPPORTED,
    ResolutionError,
    ResolvedTerminal,
    _autodetect,
    _config_default,
    needs_first_run_setup,
    resolve_terminal,
)
```

Verify the import works in cast-server's runtime context:

```bash
cd <DIECAST_ROOT>
uv run --package cast-server python -c "from cast_server.infra.terminal import resolve_terminal, _SUPPORTED; print(sorted(_SUPPORTED))"
```

If the import fails with `ModuleNotFoundError: agents`, fix `sys.path` once at the top of `cast-server/cast_server/__init__.py` (or equivalent) by inserting the repo root. Do this with the smallest possible change — e.g.:

```python
# cast_server/__init__.py — ensure shared agent code is importable
import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
```

Prefer this one-time path fix over leaving the duplicated module in place.

### Step 1.6: `cast-server/cast_server/infra/tmux_manager.py` — re-raise `ResolutionError`

Replace `_resolved_terminal()` (lines 78-92) so it lets `ResolutionError` propagate, and so a PATH-miss raises an instructive `ResolutionError` instead of silently disabling visible terminals:

```python
def _resolved_terminal(self) -> ResolvedTerminal:
    """Resolve $CAST_TERMINAL once and cache.

    Raises:
        ResolutionError: when no terminal is configured, or when the configured
            command is not on PATH. Callers (agent_service) catch this and fail
            the run with the structured message — no more 30s readiness timeout.
    """
    if isinstance(self._terminal, ResolvedTerminal):
        return self._terminal
    resolved = resolve_terminal()
    if shutil.which(resolved.command) is None:
        raise ResolutionError(
            f"configured terminal '{resolved.command}' is not on PATH. "
            f"fix: install {resolved.command} or run `bin/cast-doctor --fix-terminal` "
            f"to pick a different one. See docs/reference/supported-terminals.md."
        )
    self._terminal = resolved
    return self._terminal
```

Adjust `open_terminal()` to drop the `if resolved is None: return` guard now that `_resolved_terminal()` either returns a value or raises. Audit for any other internal callers of `_resolved_terminal()` — there should not be any beyond `open_terminal()`, but `grep` to be sure.

Inspect the cache-state field type and rename if needed — today `self._terminal` can be `False` (PATH-miss memo) or a `ResolvedTerminal`. Since both error paths now raise, `False` as a sentinel goes away; either drop the memo entirely (resolution is cheap) or memoize only the resolved value. Prefer the simpler "resolve every time" option unless profiling shows it matters.

### Step 1.7: `cast-server/cast_server/services/agent_service.py` — catch and fail the run

At both call sites (~line 1674 child path, ~line 1716 top-level path), wrap `tmux.open_terminal(...)` in a `try`/`except ResolutionError`. On error: kill the tmux session and re-raise as `TmuxError` (or whatever the surrounding code uses to fail the run). Example for the child path:

```python
tmux.create_session(session_name, cmd, working_dir)
try:
    tmux.open_terminal(session_name, title=child_title)
except ResolutionError as exc:
    tmux.kill_session(session_name)
    logger.error(
        "Child agent %s could not start: %s",
        run_id, exc,
    )
    raise TmuxError(
        f"Child agent {run_id} could not start: {exc}"
    ) from exc
```

Mirror the same pattern at the top-level call site. Make sure the `ResolutionError` import is added at the top of the module (it is exported from the de-vendored `cast_server.infra.terminal`).

### Step 1.8: Extend `tests/test_b6_terminal_resolution.py`

Add the following tests (preserve every existing test). Use the existing `clean_env` fixture for any test that touches env vars.

```python
# --- New: terminal_default vs terminal alias ----------------------------------

def test_config_alias_terminal_key_accepted(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal": "ptyxis"}))  # diecast-lint: ignore-line
    assert resolve_terminal(cfg).command == "ptyxis"  # diecast-lint: ignore-line


def test_config_canonical_wins_over_alias(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({
        "terminal_default": "kitty",
        "terminal": "ptyxis",  # diecast-lint: ignore-line
    }))
    assert resolve_terminal(cfg).command == "kitty"


# --- New: improved ResolutionError message ------------------------------------

def test_resolution_error_points_at_fix_terminal(clean_env, tmp_path):
    with pytest.raises(ResolutionError) as exc:
        resolve_terminal(tmp_path / "missing.yaml")
    msg = str(exc.value)
    assert "bin/cast-doctor --fix-terminal" in msg
    assert "supported-terminals.md" in msg
    # Existing assertions still hold:
    assert "$CAST_TERMINAL" in msg
    assert "$TERMINAL" in msg
    assert "terminal_default" in msg


# --- New: _autodetect probe order ---------------------------------------------

from agents._shared.terminal import _autodetect


def test_autodetect_macos_with_iterm(clean_env, tmp_path):
    fake_iterm = tmp_path / "iTerm.app"
    fake_iterm.mkdir()
    candidates = _autodetect(
        system="Darwin",
        iterm_app_path=fake_iterm,
        which=lambda _name: "/usr/bin/anything",
    )
    assert candidates == ["iterm", "terminal"]


def test_autodetect_macos_without_iterm(clean_env, tmp_path):
    candidates = _autodetect(
        system="Darwin",
        iterm_app_path=tmp_path / "missing.app",
        which=lambda _name: "/usr/bin/anything",
    )
    assert candidates == ["terminal"]


def test_autodetect_linux_gnome_prefers_gnome_stack(clean_env, monkeypatch):
    fake_path = {"ptyxis": "/usr/bin/ptyxis", "gnome-terminal": "/usr/bin/gnome-terminal"}  # diecast-lint: ignore-line
    candidates = _autodetect(
        system="Linux",
        desktop="GNOME",
        which=lambda name: fake_path.get(name),
    )
    # ptyxis first (GNOME-native), gnome-terminal second.
    assert candidates[:2] == ["ptyxis", "gnome-terminal"]  # diecast-lint: ignore-line


def test_autodetect_linux_no_terminals_returns_empty(clean_env):
    assert _autodetect(system="Linux", desktop="", which=lambda _n: None) == []


# --- Optional: KDE preference if konsole was added to _SUPPORTED --------------

@pytest.mark.skipif("konsole" not in _SUPPORTED, reason="konsole not in _SUPPORTED")
def test_autodetect_linux_kde_prefers_konsole(clean_env):
    fake_path = {"konsole": "/usr/bin/konsole", "alacritty": "/usr/bin/alacritty"}
    candidates = _autodetect(
        system="Linux",
        desktop="KDE",
        which=lambda name: fake_path.get(name),
    )
    assert candidates[0] == "konsole"
```

The existing `test_first_run_prompt_*` trio still works because `needs_first_run_setup()` did not change. If Step 1.4 changed any behavior visible to those tests, update them; otherwise leave alone.

### Step 1.9: Run the full test suite locally

```bash
cd <DIECAST_ROOT>
uv run pytest tests/test_b6_terminal_resolution.py -v
uv run pytest tests/ -k "tmux or agent_service or terminal" -v   # broader sanity sweep
```

Fix any failures. Do not skip or @xfail — every test in the broader sweep should pass. If you hit an unrelated pre-existing failure, document it in `_review_summary.md` Open Questions and ask the maintainer before proceeding.

## Verification

### Automated Tests (permanent)

- `tests/test_b6_terminal_resolution.py::test_config_alias_terminal_key_accepted`
- `tests/test_b6_terminal_resolution.py::test_config_canonical_wins_over_alias`
- `tests/test_b6_terminal_resolution.py::test_resolution_error_points_at_fix_terminal`
- `tests/test_b6_terminal_resolution.py::test_autodetect_macos_with_iterm`
- `tests/test_b6_terminal_resolution.py::test_autodetect_macos_without_iterm`
- `tests/test_b6_terminal_resolution.py::test_autodetect_linux_gnome_prefers_gnome_stack`
- `tests/test_b6_terminal_resolution.py::test_autodetect_linux_no_terminals_returns_empty`
- `tests/test_b6_terminal_resolution.py::test_autodetect_linux_kde_prefers_konsole` (only if `konsole` added)
- All pre-existing tests in the file still pass (parametrized `test_supported_table_drives_resolution` for any new entries).

### Validation Scripts (temporary)

- Confirm `cast-server` imports the de-vendored module correctly:
  ```bash
  cd <DIECAST_ROOT>
  uv run --package cast-server python -c \
    "from cast_server.infra.terminal import resolve_terminal, ResolutionError, _SUPPORTED; \
     assert hasattr(resolve_terminal, '__call__'); print('OK', sorted(_SUPPORTED))"
  ```
- Reproduce the original failure scenario in a tmp HOME:
  ```bash
  TMPHOME=$(mktemp -d)
  mkdir -p "$TMPHOME/.cast"
  printf 'terminal: ptyxis\n' > "$TMPHOME/.cast/config.yaml"  # diecast-lint: ignore-line
  HOME="$TMPHOME" CAST_TERMINAL= TERMINAL= uv run python -c \
    "from agents._shared.terminal import resolve_terminal; print(resolve_terminal())"
  rm -rf "$TMPHOME"
  ```
  Expected: prints a `ResolvedTerminal(command='ptyxis', ...)` (alias accepted).  # diecast-lint: ignore-line

### Manual Checks

- Run `grep -n "swallow\|warning(.*resolution failed\|warning(.*not on PATH" cast-server/cast_server/infra/tmux_manager.py` and confirm no matches remain — the silent-fallback log lines are gone.
- Run `grep -n "ResolutionError" cast-server/cast_server/services/agent_service.py` and confirm the import + try/except blocks are present at both call sites.
- `wc -l cast-server/cast_server/infra/terminal.py` should drop from ~82 to ~20-30 lines (shim only).

### Success Criteria

- [ ] `_config_default()` accepts both `terminal_default` and `terminal` keys, with `terminal_default` winning.
- [ ] `ResolutionError`'s message contains `$CAST_TERMINAL`, `$TERMINAL`, `terminal_default`, `bin/cast-doctor --fix-terminal`, and `supported-terminals.md`.
- [ ] `_autodetect()` exists in `agents/_shared/terminal.py` with the signature documented above; `resolve_terminal()` does NOT call it.
- [ ] If Open Question #1 resolved yes for `foot`/`konsole`: those keys are present in `_SUPPORTED` with valid `new_tab_flag`/`cwd_flag` strings.
- [ ] `cast-server/cast_server/infra/terminal.py` is a thin re-export shim of `agents/_shared/terminal.py`. The duplicate logic is gone.
- [ ] `cast_server.infra.terminal` imports cleanly from cast-server's runtime (validation script passes).
- [ ] `tmux_manager._resolved_terminal()` raises `ResolutionError` (both for unconfigured-terminal and PATH-miss); never returns `None`.
- [ ] `agent_service` catches `ResolutionError` at both call sites, kills the tmux session, and fails the run with a structured message.
- [ ] All new tests pass; all pre-existing tests in `test_b6_terminal_resolution.py` still pass.
- [ ] Broader pytest sweep (`-k "tmux or agent_service or terminal"`) is green.
- [ ] `bin/lint-anonymization` passes (run before commit — required by repo convention).

## Execution Notes

- **Spec-linked files:** None. The three specs in `docs/specs/` do not cover terminal resolver, tmux manager, or agent service.
- **Anonymization linter:** Any test or doc string that mentions `ptyxis` requires `# diecast-lint: ignore-line` on the same line. Check existing usages in `terminal.py` and `test_b6_terminal_resolution.py` for the pattern.
- **Cache-state cleanup:** Today `TmuxManager._terminal` can be `False` as a sentinel for "tried and failed; do not retry". With re-raise semantics, that sentinel is dead. Either drop the memo (simpler) or only cache the success case — do not keep the `False` branch.
- **Symmetry between child and top-level call sites:** Both `agent_service.py:1674` and `:1716` need the same `try`/`except ResolutionError` pattern. Easy to fix one and miss the other — grep for `tmux.open_terminal` and confirm both sites are covered.
- **Do not change the message wording test asserts on.** The existing `test_unset_raises_with_docs_link` asserts on `$CAST_TERMINAL`, `$TERMINAL`, `terminal_default`, `supported-terminals.md`. Step 1.3's new test adds `bin/cast-doctor --fix-terminal`. Both must pass.
- **Commit message hint:** `terminal: accept terminal: alias, de-vendor, and fail loudly on unresolved terminal` — captures the three coupled changes for commit 1.
