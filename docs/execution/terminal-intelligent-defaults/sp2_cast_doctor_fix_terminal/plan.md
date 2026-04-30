# Sub-phase 2: `bin/cast-doctor --fix-terminal` + Docs + Parity Test

> **Pre-requisite:** Read `docs/execution/terminal-intelligent-defaults/_shared_context.md` before starting this sub-phase.
> **Pre-requisite:** Sub-phase 1 must be complete and committed. This sub-phase's `--fix-terminal` flag reads `_SUPPORTED.keys()` from the resolver established in sp1, and its parity test asserts the bash hardcoded fallback list matches `_SUPPORTED` after any sp1 additions (e.g., `foot`/`konsole`).

## Objective

Ship the user-facing first-run setup flow: extend `bin/cast-doctor` with a `--fix-terminal` flag that probes installed terminals on PATH, prompts the user when there's ambiguity, writes `terminal_default` to `~/.cast/config.yaml`, and tells the user to verify with `cast-doctor`. Update `docs/reference/supported-terminals.md` to document the new flow and the dual-key alias. Add `tests/test_cast_doctor.py` with subprocess-level tests of the interactive flow plus a parity assertion that cast-doctor's hardcoded fallback list matches `_SUPPORTED.keys()`. This is commit 2 of the planned 2-commit PR.

## Dependencies

- **Requires completed:** sp1 (`agents/_shared/terminal.py` exposes `_SUPPORTED` with the final entry list and `_autodetect()`; `cast-server/cast_server/infra/terminal.py` is a re-export shim; `tmux_manager._resolved_terminal()` re-raises; `agent_service` catches and fails the run).
- **Assumed codebase state:** `bin/cast-doctor` is the current 265-line Bash diagnostic with `check_terminal()` at lines 181-208 and `SUPPORTED_TERMINALS=(ptyxis gnome-terminal kitty alacritty wezterm iterm2 terminal)` at line 37 — note: the existing array drifts from `_SUPPORTED` (`wezterm` and `iterm2` vs canonical `iterm`). Fixing this drift is part of this sub-phase.

## Scope

**In scope:**

- Add `--fix-terminal` parsing to the `while (($#))` flag loop. When set, run the new `fix_terminal()` function and exit immediately (do NOT run the rest of the prerequisite checks).
- Implement the interactive `fix_terminal()` Bash function with: PATH probe, zero/one/multiple-candidate handling, write to `~/.cast/config.yaml`, idempotent re-runs.
- Read the canonical supported list from `_SUPPORTED.keys()` via `python3 -c '...'`. Fall back to a hardcoded array (`# KEEP IN SYNC WITH _SUPPORTED`) when Python or the import fails (e.g., during install-time gating, before deps are installed).
- Update the existing `SUPPORTED_TERMINALS=(...)` literal at line 37 to match `_SUPPORTED.keys()` exactly (drop `wezterm`/`iterm2`; use canonical `iterm`; add `foot`/`konsole` if sp1 added them). Add the `# KEEP IN SYNC WITH _SUPPORTED` comment.
- Update `check_terminal()` to point at `bin/cast-doctor --fix-terminal` as the actionable fix when no terminal is configured.
- Update `docs/reference/supported-terminals.md` to (a) document `bin/cast-doctor --fix-terminal`, (b) document the `terminal:` alias accepted alongside `terminal_default:`, (c) reaffirm "no silent fallback during dispatch", (d) update the resolution-order list (item 3) to mention both keys, (e) update the "First-run setup" section to describe the new flow (the existing text references a `/cast-setup` slash command that is being superseded by `bin/cast-doctor --fix-terminal`).
- Create `tests/test_cast_doctor.py` with: parity test (Python and Bash fallback lists match), zero-candidate test, single-candidate confirm test, multiple-candidate disambiguation test, idempotency test (re-run does not duplicate / corrupt config), and a yaml-round-trip test that the written file is readable by `_config_default()`.

**Out of scope (do NOT do these):**

- Resolver behavior changes (alias acceptance, message text, `_autodetect()`) — sp1.
- Tmux manager / agent service changes — sp1.
- Adding `wezterm` to `_SUPPORTED` (separate PR per plan Out-of-Scope).
- A new Python CLI for `cast doctor` (explicitly rejected; we extend the existing Bash script).
- Any change to `bin/cast-doctor`'s existing `check_bash`/`check_uv`/`check_git`/`check_claude`/`check_writable` checks.
- Migration tooling that rewrites old `terminal:` configs to `terminal_default:` (sp1's alias preserves them as-is).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `bin/cast-doctor` | Modify | 265 lines, no `--fix-terminal` flag; hardcoded `SUPPORTED_TERMINALS` array drifts from `_SUPPORTED`. |
| `docs/reference/supported-terminals.md` | Modify | 65 lines documenting today's resolution chain and the `/cast-setup` placeholder. |
| `tests/test_cast_doctor.py` | Create | Does not exist. |

## Detailed Steps

### Step 2.1: `bin/cast-doctor` — `--fix-terminal` flag wiring

In the `while (($#))` flag-parsing loop (currently lines 68-76), add a new branch:

```bash
FIX_TERMINAL=0

while (($#)); do
  case "$1" in
    --json)         JSON_OUTPUT=1 ;;
    --quiet)        QUIET=1 ;;
    --fix-terminal) FIX_TERMINAL=1 ;;
    -h|--help)      print_help; exit 0 ;;
    *)              fail "Unknown flag: $1 (try --help)" ;;
  esac
  shift
done

if [[ "${FIX_TERMINAL}" -eq 1 ]]; then
  fix_terminal
  exit 0
fi
```

Update `print_help` to document `--fix-terminal`. Add a one-line description in the file-header docblock comment.

### Step 2.2: `bin/cast-doctor` — sync `SUPPORTED_TERMINALS` to `_SUPPORTED.keys()`

Replace line 37:

```bash
# KEEP IN SYNC WITH _SUPPORTED in agents/_shared/terminal.py.
# CI parity test (tests/test_cast_doctor.py) asserts equality.
SUPPORTED_TERMINALS_FALLBACK=(ptyxis gnome-terminal kitty alacritty iterm terminal)  # diecast-lint: ignore-line
# Add foot / konsole here if sp1 added them to _SUPPORTED.
```

Drop `wezterm` and `iterm2` (the canonical key is `iterm`, not `iterm2`; `wezterm` is not in `_SUPPORTED` and is explicitly out of scope per plan).

Add a helper that prefers Python for the live read, falling back to the bash array:

```bash
get_supported_terminals() {
  # Echo space-separated supported terminal keys. Prefer the canonical Python
  # source of truth; fall back to the hardcoded array when python3 / agents
  # aren't importable (e.g., install-time gate before deps are installed).
  if command -v python3 >/dev/null 2>&1; then
    local out
    out=$(python3 -c '
import sys
sys.path.insert(0, "'"${SCRIPT_DIR}"'/..")
try:
    from agents._shared.terminal import _SUPPORTED
    print(" ".join(sorted(_SUPPORTED)))
except Exception:
    sys.exit(2)
' 2>/dev/null) && [[ -n "$out" ]] && { echo "$out"; return; }
  fi
  echo "${SUPPORTED_TERMINALS_FALLBACK[*]}"
}
```

`SCRIPT_DIR` is set at the top of `bin/cast-doctor`; the import path assumes `bin/` sits under the repo root (verify with `ls "${SCRIPT_DIR}/../agents/_shared/terminal.py"` once before relying on it).

### Step 2.3: `bin/cast-doctor` — implement `fix_terminal()`

```bash
fix_terminal() {
  local sys_name
  sys_name=$(uname -s)
  printf '[cast-doctor] Probing supported terminals on PATH...\n'

  local -a candidates=()
  local supported_str
  supported_str=$(get_supported_terminals)

  if [[ "$sys_name" == "Darwin" ]]; then
    if [[ -d "/Applications/iTerm.app" ]]; then
      candidates+=(iterm)
      printf '  found: iterm (/Applications/iTerm.app)\n'
    fi
    candidates+=(terminal)  # always present on macOS
    printf '  found: terminal (built-in)\n'
  else
    # Linux / BSD / WSL — probe via command -v in _SUPPORTED-table order.
    # Move konsole to front if KDE detected; ptyxis/gnome-terminal already lead.
    local desktop="${XDG_CURRENT_DESKTOP^^}"
    local order_str="$supported_str"
    if [[ "$desktop" == *KDE* && " $supported_str " == *" konsole "* ]]; then
      order_str="konsole $(echo "$supported_str" | tr ' ' '\n' | grep -v '^konsole$' | tr '\n' ' ')"
    fi
    local t path
    for t in $order_str; do
      # Skip macOS-only keys.
      [[ "$t" == "iterm" || "$t" == "terminal" ]] && continue
      if path=$(command -v "$t" 2>/dev/null) && [[ -n "$path" ]]; then
        candidates+=("$t")
        printf '  found: %s (%s)\n' "$t" "$path"
      fi
    done
  fi

  if [[ ${#candidates[@]} -eq 0 ]]; then
    printf '\n[cast-doctor] No supported terminal found on PATH.\n'
    if [[ "$sys_name" == "Darwin" ]]; then
      printf '  install iTerm2: brew install --cask iterm2\n'
    else
      printf '  install one of: %s\n' "$supported_str"
      printf '  e.g. on Debian/Ubuntu: sudo apt install gnome-terminal\n'
    fi
    return 1
  fi

  local choice
  if [[ ${#candidates[@]} -eq 1 ]]; then
    printf '\n[cast-doctor] One candidate found: %s\n' "${candidates[0]}"
    printf 'Write ~/.cast/config.yaml with terminal_default: %s? [Y/n] ' "${candidates[0]}"
    read -r choice
    case "${choice:-y}" in
      [yY]|[yY][eE][sS]) choice="${candidates[0]}" ;;
      *) printf '[cast-doctor] Aborted, no changes written.\n'; return 1 ;;
    esac
  else
    printf '\nMultiple candidates. Pick one:\n'
    local i=1
    for c in "${candidates[@]}"; do
      printf '  %d) %s\n' "$i" "$c"
      i=$((i + 1))
    done
    printf '\nChoice [1]: '
    read -r choice
    choice="${choice:-1}"
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#candidates[@]} )); then
      printf '[cast-doctor] Invalid choice: %s\n' "$choice"
      return 1
    fi
    choice="${candidates[$((choice - 1))]}"
  fi

  local cfg_dir="${HOME}/.cast"
  local cfg_file="${cfg_dir}/config.yaml"
  mkdir -p "$cfg_dir"

  # Idempotent write: if the file exists, replace just the terminal_default key.
  # We rewrite the whole file via python3 to avoid hand-rolling YAML in bash.
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$cfg_file" "$choice" <<'PY'
import sys, yaml
from pathlib import Path
path, choice = Path(sys.argv[1]), sys.argv[2]
data = {}
if path.exists():
    try:
        loaded = yaml.safe_load(path.read_text()) or {}
        if isinstance(loaded, dict):
            data = loaded
    except yaml.YAMLError:
        pass
data["terminal_default"] = choice
path.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=True))
PY
  else
    # Minimal fallback when python3 is missing: overwrite single-key config.
    printf 'terminal_default: %s\n' "$choice" > "$cfg_file"
  fi

  printf '\n[cast-doctor] Wrote %s: terminal_default: %s\n' "$cfg_file" "$choice"
  printf '[cast-doctor] Done. Verify with: cast-doctor\n'
}
```

**Notes on the implementation:**

- The idempotent write preserves any other keys already in `~/.cast/config.yaml` and overwrites only `terminal_default`. Re-running `--fix-terminal` overwrites cleanly.
- The fallback python-less branch handles the install-time edge case where pyyaml may not yet be installed; it writes a minimal one-line file. Existing keys would be lost, but that path only fires before the user's first dep install — acceptable.
- `read -r choice` blocks on stdin. Tests pass input via `subprocess.run(..., input=..., text=True)`.
- Default selection on bare Enter in the multi-candidate prompt is `1` (top of list). Default on bare Enter in the single-candidate prompt is `Y`.

### Step 2.4: `bin/cast-doctor` — update `check_terminal()` to point at `--fix-terminal`

In `check_terminal()` (current lines 181-208), update the two `note_yellow` calls so they point at `bin/cast-doctor --fix-terminal` instead of (or in addition to) the `./setup` reference.

```bash
note_yellow "No supported terminal found. Run \`bin/cast-doctor --fix-terminal\` to probe and configure interactively, or set \$CAST_TERMINAL manually. (Supported: $(get_supported_terminals))"
```

The "supported list" string should come from `get_supported_terminals` so it stays in sync with `_SUPPORTED`. The yellow message about `$CAST_TERMINAL=...` being "not a supported terminal" can either keep its current wording or also point at `--fix-terminal` — minor; pick one.

### Step 2.5: `docs/reference/supported-terminals.md` — document the new flow

Edits:

1. **Resolution order list (lines 7-12):** update item 3 to mention both keys:
   ```
   3. **`~/.cast/config.yaml:terminal_default`** — written by `bin/cast-doctor --fix-terminal` on first run. The legacy key `terminal:` is also accepted for back-compat with configs written by older versions of `cast init` (`terminal_default:` wins when both are present). Survives shell restarts and removes the need for env-var plumbing in graphical launchers.
   ```

2. **First-run setup section (lines 46-56):** rewrite to describe `bin/cast-doctor --fix-terminal`:
   ```markdown
   ## First-run setup

   `needs_first_run_setup(config_path=...)` returns `True` only when **all** of the following hold:

   - `$CAST_TERMINAL` is unset.
   - `$TERMINAL` is unset.
   - `~/.cast/config.yaml` lacks a non-empty `terminal_default` (or alias `terminal`) value.

   When that's the case, run `bin/cast-doctor --fix-terminal`. The script:

   1. Probes installed terminals on `PATH` from the canonical `_SUPPORTED` list.
   2. With one candidate, asks the user to confirm before writing.
   3. With multiple, presents a numbered prompt (default: first).
   4. With none, prints platform-appropriate install instructions and exits 1.
   5. Writes the chosen terminal as `terminal_default` to `~/.cast/config.yaml`. Idempotent — re-running `--fix-terminal` replaces the value cleanly.

   Auto-detect runs **only** at first-run setup. During dispatch, `resolve_terminal()` keeps its loud-failure semantics: a misconfigured or unset terminal raises `ResolutionError` with a structured message pointing back at `bin/cast-doctor --fix-terminal` — there is no silent fallback.
   ```

3. **"Why no `xterm` fallback?" section:** keep as-is. The principle still applies — auto-detect is at *setup time*, not *dispatch time*, so the documented rule survives.

4. **"Adding a new terminal" section:** add a step to update `bin/cast-doctor`'s `SUPPORTED_TERMINALS_FALLBACK` array (with the `# KEEP IN SYNC WITH _SUPPORTED` comment) and run the parity test in `tests/test_cast_doctor.py`.

### Step 2.6: Create `tests/test_cast_doctor.py`

```python
"""Subprocess tests for `bin/cast-doctor --fix-terminal`.

Covers the interactive flow (zero/one/multiple candidates), idempotent re-runs,
yaml-round-trip with the canonical resolver, and a parity check between the
bash hardcoded fallback list and `_SUPPORTED.keys()`.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

from agents._shared.terminal import (
    _SUPPORTED,
    _config_default,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CAST_DOCTOR = REPO_ROOT / "bin" / "cast-doctor"


def _make_fake_bin(dir_: Path, names: list[str]) -> Path:
    """Create empty executable shims for each name; return the dir path."""
    dir_.mkdir(parents=True, exist_ok=True)
    for name in names:
        shim = dir_ / name
        shim.write_text("#!/bin/sh\nexit 0\n")
        shim.chmod(0o755)
    return dir_


def _run(home: Path, fake_bin: Path, stdin: str = "") -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "CAST_TERMINAL": "",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
        "LANG": "C.UTF-8",
    }
    return subprocess.run(
        [str(CAST_DOCTOR), "--fix-terminal"],
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )


# --- Parity test --------------------------------------------------------------

def test_fallback_list_matches_supported():
    """Bash hardcoded fallback list is in sync with _SUPPORTED.keys().

    This is the CI guard against drift — fail fast when someone adds a key to
    _SUPPORTED but forgets to update bin/cast-doctor.
    """
    text = CAST_DOCTOR.read_text()
    match = re.search(
        r"SUPPORTED_TERMINALS_FALLBACK=\(([^)]*)\)",
        text,
    )
    assert match, "SUPPORTED_TERMINALS_FALLBACK array not found in bin/cast-doctor"
    bash_keys = set(match.group(1).split())
    py_keys = set(_SUPPORTED)
    assert bash_keys == py_keys, (
        f"bin/cast-doctor fallback list drifted from _SUPPORTED.\n"
        f"  bash only: {sorted(bash_keys - py_keys)}\n"
        f"  python only: {sorted(py_keys - bash_keys)}"
    )


# --- Interactive-flow tests ---------------------------------------------------

@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_zero_candidates_exits_nonzero(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=[])  # nothing on PATH
    # Force non-Darwin probe path even on macOS test runners — uname can't be
    # cleanly mocked through env, so we run only on Linux.
    if os.uname().sysname != "Linux":
        pytest.skip("zero-candidate test runs only on Linux probe path")
    res = _run(home, fake_bin)
    assert res.returncode != 0
    assert "No supported terminal" in (res.stdout + res.stderr)
    assert not (home / ".cast" / "config.yaml").exists()


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_single_candidate_confirm_writes_config(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    res = _run(home, fake_bin, stdin="y\n")
    assert res.returncode == 0, res.stderr
    cfg_path = home / ".cast" / "config.yaml"
    assert cfg_path.exists()
    assert _config_default(cfg_path) == "alacritty"


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_single_candidate_decline_does_not_write(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    res = _run(home, fake_bin, stdin="n\n")
    assert res.returncode != 0
    assert not (home / ".cast" / "config.yaml").exists()


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_multiple_candidates_pick_second(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(
        tmp_path / "bin",
        names=["ptyxis", "gnome-terminal", "kitty"],  # diecast-lint: ignore-line
    )
    res = _run(home, fake_bin, stdin="2\n")
    assert res.returncode == 0, res.stderr
    cfg_path = home / ".cast" / "config.yaml"
    assert _config_default(cfg_path) == "gnome-terminal"


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_idempotent_rerun(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    _run(home, fake_bin, stdin="y\n")
    _run(home, fake_bin, stdin="y\n")
    cfg_path = home / ".cast" / "config.yaml"
    cfg_text = cfg_path.read_text()
    parsed = yaml.safe_load(cfg_text)
    assert parsed == {"terminal_default": "alacritty"}
    # No duplicated keys, no garbled re-write.
    assert cfg_text.count("terminal_default") == 1


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_preserves_unrelated_config_keys(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    (home / ".cast").mkdir(parents=True)
    (home / ".cast" / "config.yaml").write_text(
        yaml.safe_dump({"some_other_key": "value", "terminal_default": "old"})
    )
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    _run(home, fake_bin, stdin="y\n")
    parsed = yaml.safe_load((home / ".cast" / "config.yaml").read_text())
    assert parsed == {
        "some_other_key": "value",
        "terminal_default": "alacritty",
    }
```

**Notes on the test design:**

- Linux-only probe-path tests because `uname` cannot be cleanly faked through env vars. macOS-specific behavior is exercised through the `_autodetect()` unit tests in sp1's `test_b6_terminal_resolution.py`, which can inject `system="Darwin"`.
- Empty stub binaries on a controlled `PATH` make the probe deterministic and safe — they're never executed by `--fix-terminal`, only `command -v`'d.
- `_config_default()` from sp1 is used to round-trip the written config — confirms end-to-end correctness against the resolver.
- The parity test runs unconditionally (no skipif); CI will catch drift even on platforms where the interactive tests skip.

### Step 2.7: Run the full test suite locally

```bash
cd /data/workspace/diecast
uv run pytest tests/test_cast_doctor.py -v
uv run pytest tests/test_b6_terminal_resolution.py tests/test_cast_doctor.py -v   # combined
uv run pytest tests/ -k "doctor or terminal" -v   # broader
```

Manually exercise the script in a tmp HOME to sanity-check the UX:

```bash
TMPHOME=$(mktemp -d)
HOME="$TMPHOME" CAST_TERMINAL= TERMINAL= bin/cast-doctor --fix-terminal
cat "$TMPHOME/.cast/config.yaml"
rm -rf "$TMPHOME"
```

Re-run with no terminals on `PATH` to confirm the "install one of" branch:

```bash
TMPHOME=$(mktemp -d) FAKEBIN=$(mktemp -d)
HOME="$TMPHOME" PATH="$FAKEBIN:/usr/bin:/bin" CAST_TERMINAL= TERMINAL= \
  bin/cast-doctor --fix-terminal
rm -rf "$TMPHOME" "$FAKEBIN"
```

## Verification

### Automated Tests (permanent)

- `tests/test_cast_doctor.py::test_fallback_list_matches_supported` (parity, runs always)
- `tests/test_cast_doctor.py::test_zero_candidates_exits_nonzero`
- `tests/test_cast_doctor.py::test_single_candidate_confirm_writes_config`
- `tests/test_cast_doctor.py::test_single_candidate_decline_does_not_write`
- `tests/test_cast_doctor.py::test_multiple_candidates_pick_second`
- `tests/test_cast_doctor.py::test_idempotent_rerun`
- `tests/test_cast_doctor.py::test_preserves_unrelated_config_keys`
- All sp1 tests still pass (regression guard).

### Validation Scripts (temporary)

- Live demo on the dev box (skip if no GUI available):
  ```bash
  TMPHOME=$(mktemp -d)
  HOME="$TMPHOME" CAST_TERMINAL= TERMINAL= bin/cast-doctor --fix-terminal
  bin/cast-doctor --quiet     # confirm no YELLOW for terminal anymore
  rm -rf "$TMPHOME"
  ```
- Confirm `--help` text mentions `--fix-terminal`:
  ```bash
  bin/cast-doctor --help | grep -- --fix-terminal
  ```

### Manual Checks

- Read `docs/reference/supported-terminals.md` end-to-end and verify:
  - Resolution-order list mentions both `terminal_default` and the `terminal:` alias.
  - First-run setup section describes `bin/cast-doctor --fix-terminal` (not `/cast-setup`).
  - "Adding a new terminal" steps now require updating `SUPPORTED_TERMINALS_FALLBACK` and the parity test.
- Manually run `bin/cast-doctor --fix-terminal` on the dev box; verify the prompt UX and the resulting `~/.cast/config.yaml`.
- Run `bin/lint-anonymization` — required by repo convention before commit.

### Success Criteria

- [ ] `bin/cast-doctor --fix-terminal` runs end-to-end and writes a correct `~/.cast/config.yaml`.
- [ ] Zero / single / multiple candidate code paths all work.
- [ ] Re-running `--fix-terminal` does not duplicate or garble config; preserves other keys.
- [ ] `SUPPORTED_TERMINALS_FALLBACK` matches `_SUPPORTED.keys()` exactly (parity test green).
- [ ] `check_terminal()` yellow message points at `bin/cast-doctor --fix-terminal`.
- [ ] `bin/cast-doctor --help` lists the new flag.
- [ ] `docs/reference/supported-terminals.md` documents the new flow, the alias, and the "no silent fallback during dispatch" guarantee.
- [ ] All seven new tests pass; sp1 tests still pass.
- [ ] `bin/lint-anonymization` passes.
- [ ] Combined sweep (`tests/ -k "doctor or terminal"`) is green.

## Execution Notes

- **Spec-linked files:** None — see `_shared_context.md`.
- **Bash quoting:** the heredoc embedded in `fix_terminal()` for the idempotent yaml write uses `<<'PY'` (quoted delimiter) to suppress bash expansion inside the Python block. Do not unquote it.
- **`read -r` portability:** GNU `bash >= 4.0` is already a hard requirement enforced by `check_bash` (`bin/cast-doctor:14`). `read -r` works in 3.x too — no concern.
- **`uname -s` fallback:** macOS / Linux only is fine for v1. WSL reports `Linux` from `uname -s` and goes through the Linux probe path — correct per plan.
- **Test platform skips:** the interactive subprocess tests skip on non-Linux because `uname` cannot be mocked from inside the bash script easily. The unit-level `_autodetect()` tests in sp1 cover Darwin via the injected `system=` parameter — together they give full coverage.
- **`# diecast-lint: ignore-line`:** any line in `bin/cast-doctor`, `tests/test_cast_doctor.py`, or `docs/reference/supported-terminals.md` that names `ptyxis` needs the inline pragma. Test fixtures that put `ptyxis` on PATH need it.  # diecast-lint: ignore-line
- **Commit message hint:** `cast-doctor: add --fix-terminal interactive setup + parity test + docs` — captures the three coupled changes for commit 2.
- **Do NOT depend on a `/cast-setup` slash command.** The plan supersedes that placeholder. The first-run path is `bin/cast-doctor --fix-terminal`; references to `/cast-setup` in docs should be removed or rewritten.
