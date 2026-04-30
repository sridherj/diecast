# Sub-phase 2: `bin/cast-doctor` extended preflight (python3 ≥3.11, tmux)

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Extend the existing `bin/cast-doctor` RED-list with two cast-server prerequisites — Python 3.11+ and `tmux` — so a missing prerequisite aborts `setup` cleanly at `step1_doctor` instead of failing later inside the application. Per Decision #12, this replaces the original §D's parallel preflight (which would have duplicated cast-doctor) — single source of truth for prerequisite checks, consistent with the terminal-defaults plan's "extend cast-doctor; no new CLI" decision.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** `bin/cast-doctor` already exists with a RED-list machinery (bash, uv, git, claude, write-access). `step1_doctor` in `setup` already invokes it and aborts on non-zero exit. (Do not introduce a parallel preflight step.)

## Scope

**In scope:**
- Add `python3 ≥3.11` and `tmux` to cast-doctor's RED list.
- OS-aware install hints (macOS via `brew`; Linux via `/etc/os-release` sniff for apt/dnf; generic fallback).
- Header docstring left as-is — sp6 owns the docstring rewrite. **Do not** touch lines 8–12, 12, 57, 224, 241 here.

**Out of scope (do NOT do these):**
- Header docstring updates (sp6).
- The `--fix-terminal` flag presentation wording (sp6, Decision #19).
- Any new CLI binary or shell script that duplicates cast-doctor.
- Plumbing the JSON-shape contract — sp6 introduces `--json` and `/api/health`.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `bin/cast-doctor` | Modify (RED-list block only) | Currently checks bash, uv, git, claude, write-access. |

## Detailed Steps

### Step 2.1: Locate the RED-list block

Open `bin/cast-doctor` and find the existing pattern for RED checks (look for the bash check or uv check as a reference — the script likely uses helper functions like `check_red <name> <test>`).

### Step 2.2: Add `python3 ≥3.11` check

Use `python3 --version` and parse the output. Approximate shape:

```bash
check_python3() {
  if ! command -v python3 >/dev/null 2>&1; then
    red "python3 not found"
    install_hint_python3
    return 1
  fi
  local ver
  ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  local major minor
  IFS=. read -r major minor <<<"$ver"
  if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
    red "python3 ${ver} found; cast-server requires ≥3.11"
    install_hint_python3
    return 1
  fi
  green "python3 ${ver}"
}
```

Match the existing helper-function style — if the script uses a `RED_LIST` array of test commands rather than per-check functions, fold this into that pattern instead.

### Step 2.3: Add `tmux` check

```bash
check_tmux() {
  if ! command -v tmux >/dev/null 2>&1; then
    red "tmux not found (required by the dispatcher)"
    install_hint_tmux
    return 1
  fi
  green "tmux $(tmux -V | awk '{print $2}')"
}
```

### Step 2.4: OS-aware install hints

Add two helpers, modeled on whatever cast-doctor already does for bash:

```bash
install_hint_python3() {
  case "$(uname -s)" in
    Darwin) echo "  → brew install python@3.11" ;;
    Linux)
      if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        case "${ID:-}${ID_LIKE:-}" in
          *debian*|*ubuntu*) echo "  → sudo apt install python3.11" ;;
          *rhel*|*fedora*|*centos*) echo "  → sudo dnf install python3.11" ;;
          *arch*) echo "  → sudo pacman -S python" ;;
          *) echo "  → install python ≥3.11 via your package manager" ;;
        esac
      else
        echo "  → install python ≥3.11 via your package manager"
      fi
      ;;
    *) echo "  → install python ≥3.11 via your package manager" ;;
  esac
}

install_hint_tmux() {
  case "$(uname -s)" in
    Darwin) echo "  → brew install tmux" ;;
    Linux)
      if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        case "${ID:-}${ID_LIKE:-}" in
          *debian*|*ubuntu*) echo "  → sudo apt install tmux" ;;
          *rhel*|*fedora*|*centos*) echo "  → sudo dnf install tmux" ;;
          *arch*) echo "  → sudo pacman -S tmux" ;;
          *) echo "  → install tmux via your package manager" ;;
        esac
      else
        echo "  → install tmux via your package manager"
      fi
      ;;
    *) echo "  → install tmux via your package manager" ;;
  esac
}
```

If cast-doctor already centralizes its OS detection, reuse that helper — DRY trumps duplication.

### Step 2.5: Wire the new checks into the run order

Wherever the script invokes its current red-list checks, add `check_python3` and `check_tmux` to that sequence. Order: after `bash` and before `claude` (so the user sees missing-runtime errors before missing-IDE errors).

### Step 2.6: Confirm `step1_doctor` aborts on red exit

`setup:84–89` already calls `bin/cast-doctor` and `fail`s on non-zero exit. No `setup` edits needed in this sub-phase. **Do not** add or touch any setup function.

## Verification

### Automated Tests (permanent)

If `tests/test_cast_doctor.py` exists (the terminal-defaults plan introduced it), extend it with two subprocess-based cases:

```python
def test_cast_doctor_red_on_missing_tmux(tmp_path, monkeypatch):
    fake_path = tmp_path / "bin"
    fake_path.mkdir()
    # Stub everything except tmux into PATH
    monkeypatch.setenv("PATH", str(fake_path))
    result = subprocess.run(["bin/cast-doctor"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "tmux" in result.stdout + result.stderr
    assert "brew install tmux" in result.stdout + result.stderr or \
           "apt install tmux" in result.stdout + result.stderr or \
           "package manager" in result.stdout + result.stderr

def test_cast_doctor_red_on_old_python(tmp_path):
    # Inject a fake python3 that prints 3.10 then exits 0
    fake_python = tmp_path / "python3"
    fake_python.write_text("#!/bin/sh\necho 'Python 3.10.12'\n")
    fake_python.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    result = subprocess.run(["bin/cast-doctor"], capture_output=True, text=True, env=env)
    assert result.returncode != 0
    assert "3.11" in result.stdout + result.stderr
```

If `tests/test_cast_doctor.py` does not yet exist, create it with these two cases plus a green-path smoke test.

### Validation Scripts (temporary)

```bash
# 1. Strip tmux from PATH and confirm RED:
PATH="$(echo "$PATH" | tr ':' '\n' | grep -v 'tmux' | tr '\n' ':')" bin/cast-doctor; echo "exit: $?"

# 2. Force missing python3 (rename it temporarily) and confirm RED.

# 3. Confirm green path on a healthy host:
bin/cast-doctor; echo "exit: $?"   # expect 0
```

### Manual Checks
- On macOS without tmux installed, the failure message reads `→ brew install tmux`.
- On a Debian/Ubuntu image without tmux, the failure message reads `→ sudo apt install tmux`.
- On a Fedora image, the failure message reads `→ sudo dnf install tmux`.
- `step1_doctor` in `setup` propagates the failure verbatim and aborts before any writes to `~/.claude/` or `~/.local/bin/` (existing behavior — confirm by running `./setup --dry-run` on a host without tmux).

### Success Criteria
- [ ] `bin/cast-doctor` checks `python3 ≥ 3.11` and `tmux`.
- [ ] OS-aware install hints fire for macOS, Debian/Ubuntu, RHEL/Fedora, generic fallback.
- [ ] Existing checks (bash, uv, git, claude) still work.
- [ ] `step1_doctor` aborts on missing prereq (no new setup edits).
- [ ] `tests/test_cast_doctor.py` extended with two new cases (or created with three).

## Execution Notes

- Reuse cast-doctor's existing helper style. If it has a `RED_LIST` array, append to it; if it has per-check functions, follow that pattern. Do not introduce a third style.
- The `python3 -c 'import sys; ...'` invocation is intentional — it exercises the actual interpreter (catching broken installs) better than parsing `python3 --version`.
- If the host has no `python3` at all, the script must not crash — every check function returns non-zero and falls through.
- Coordinate with sp6: that sub-phase will edit other regions of `bin/cast-doctor`. Keep your edits scoped to the RED-list/check region; do not touch lines 8–12, 12, 57, 224, 241.

**Spec-linked files:** None — `bin/cast-doctor` is not currently linked by any spec in `docs/specs/`.
