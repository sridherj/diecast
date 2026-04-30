# Shared Context: Terminal Intelligent Defaults

## Source Documents
- Plan: `docs/plan/2026-04-30-terminal-intelligent-defaults.collab.md`
- Writeup: (none — plan is self-contained, see "Context" and "Pre-flight §0" sections of the plan)

## Project Background

A child run failed with the misleading error `Claude did not become ready within 30s`. Root cause was a silent fallback in terminal resolution: `cast init` and the docs write the config key `terminal:`, while the resolver reads `terminal_default:`. The resolver raised `ResolutionError`, the tmux manager swallowed it into a warning log, and the dispatcher waited 30s for a Claude TUI that was never going to render.

Three coupled fixes ship together:

1. **Intelligent first-run setup** — when no env var and no config exist, `bin/cast-doctor --fix-terminal` interactively probes the platform's installed terminals and writes the user's choice to `~/.cast/config.yaml`. Auto-detect runs **only at first-run setup**, never during dispatch — preserving the documented "no silent fallback during dispatch" principle (`docs/reference/supported-terminals.md:11`).
2. **Loud failures during dispatch** — `tmux_manager._resolved_terminal()` re-raises `ResolutionError` instead of swallowing it; `agent_service` catches the raise, kills the session, and fails the run with the structured message immediately (no more 30s timeout).
3. **De-duplication** — the vendored copy at `cast-server/cast_server/infra/terminal.py` is replaced by a thin re-export shim of `agents/_shared/terminal.py` so future fixes land once.

A pre-flight smoke test (§0 of the plan) proved that synthesizing `SIGWINCH` via `tmux resize-window` is **not** sufficient to make Claude Code render in a detached pane — Claude requires an actually-attached client to paint its Ink/React TUI. As a result, real headless dispatch is **out of scope** for this PR; SSH/CI users will continue to hit the (now loud, no longer misleading) failure path.

## Codebase Conventions

- Python source for shared library code lives at `agents/_shared/`.
- Server code lives under `cast-server/cast_server/`. Vendored copies of `agents/_shared/` modules in `cast-server/cast_server/infra/` exist where the server cannot rely on `agents/` being on `sys.path`.
- All terminal-related production code passes argv as a list to `subprocess.Popen` — `shell=True` is forbidden because `$CAST_TERMINAL` and `~/.cast/config.yaml` are user-writable.
- Tests live under `tests/` (root-level, single tests/ tree). Pytest fixtures `clean_env`, `monkeypatch`, and `tmp_path` are the standard scaffolding used throughout `test_b6_terminal_resolution.py`.
- Bash scripts in `bin/` source `bin/_lib.sh`, use `set -euo pipefail`, and respect `--json`/`--quiet`/`--help` flag conventions.
- `# diecast-lint: ignore-line` is the inline pragma that suppresses the anonymization linter (`bin/lint-anonymization`) — required wherever `ptyxis` or non-public references appear.

## Key File Paths

| File | Role |
|------|------|
| `agents/_shared/terminal.py` | Canonical resolver, `_SUPPORTED` table, `ResolutionError`, `needs_first_run_setup()`. |
| `cast-server/cast_server/infra/terminal.py` | **Vendored copy today.** To be replaced by a thin re-export shim of `agents/_shared/terminal.py`. |
| `cast-server/cast_server/infra/tmux_manager.py` | `_resolved_terminal()` (lines 78-92) and `open_terminal()` (lines 98+). Today swallows `ResolutionError`; will re-raise. |
| `cast-server/cast_server/services/agent_service.py` | Calls `tmux.open_terminal(...)` at lines 1674 (child) and 1716 (top-level). Will catch `ResolutionError`, kill the tmux session, and fail the run. |
| `bin/cast-doctor` | Existing Bash diagnostic; `check_terminal()` at lines 181-208. To be extended with `--fix-terminal` flag. |
| `docs/reference/supported-terminals.md` | Resolution-order doc and supported-terminal table. To document new flow. |
| `tests/test_b6_terminal_resolution.py` | Existing 100-line pytest module. Extended with new auto-detect, alias, and updated first-run tests. |
| `tests/test_cast_doctor.py` | **New.** Subprocess-level tests for `bin/cast-doctor --fix-terminal` + parity check between bash hardcoded list and `_SUPPORTED.keys()`. |

## Data Schemas & Contracts

### `_SUPPORTED` (in `agents/_shared/terminal.py`)

```python
_SUPPORTED: dict[str, dict[str, str]] = {
    "ptyxis":         {"new_tab_flag": "--new-window",      "cwd_flag": "--working-directory="},  # diecast-lint: ignore-line
    "gnome-terminal": {"new_tab_flag": "--tab",              "cwd_flag": "--working-directory="},
    "kitty":          {"new_tab_flag": "@launch --type=tab", "cwd_flag": "--directory="},
    "alacritty":      {"new_tab_flag": "",                   "cwd_flag": "--working-directory"},
    "iterm":          {"new_tab_flag": "",                   "cwd_flag": ""},
    "terminal":       {"new_tab_flag": "",                   "cwd_flag": ""},
}
```

The plan asks (open question) whether to add `foot` and `konsole` for auto-detect — see `_review_summary.md` Open Question #1.

### Resolution chain (during dispatch — unchanged)

```
1. $CAST_TERMINAL
2. $TERMINAL
3. ~/.cast/config.yaml: terminal_default OR terminal     (alias accepted, terminal_default canonical)
4. ResolutionError (loud, structured message)
```

### `ResolutionError` improved message (target text)

```
ResolutionError: no terminal configured.
  tried: $CAST_TERMINAL (unset), $TERMINAL (unset),
         ~/.cast/config.yaml (key 'terminal_default' missing).
  fix:   run `bin/cast-doctor --fix-terminal` to auto-detect and configure,
         or set $CAST_TERMINAL=<your-terminal> manually.
         See docs/reference/supported-terminals.md.
```

The exact rendering of "(unset)" / "(missing)" can vary based on which sources were checked, but the message MUST name all three sources and point at `bin/cast-doctor --fix-terminal`.

### `bin/cast-doctor --fix-terminal` interactive flow

```
$ bin/cast-doctor --fix-terminal
[cast-doctor] Probing supported terminals on PATH...
  found: ptyxis (/usr/bin/ptyxis)
  found: gnome-terminal (/usr/bin/gnome-terminal)

Multiple candidates. Pick one:
  1) ptyxis
  2) gnome-terminal

Choice [1]: 1

Writing ~/.cast/config.yaml: terminal_default: ptyxis
[cast-doctor] Done. Verify with: cast-doctor
```

Special cases:
- **Zero candidates:** print install hint for the platform; exit 1.
- **Single candidate:** show what we picked, ask `Y/n` to confirm, then write.
- **Multiple candidates:** numbered prompt as shown.
- **macOS:** probe is `/Applications/iTerm.app` existence (→ `iterm`) plus the always-present `terminal`; write canonical config keys, not binary paths.
- **Linux:** probe via `command -v`. If `$XDG_CURRENT_DESKTOP` contains `GNOME`, prefer `ptyxis`/`gnome-terminal`; if `KDE`, prefer `konsole` (only if added to `_SUPPORTED`); otherwise iterate the `_SUPPORTED` order.

## Pre-Existing Decisions

From the plan's Decisions section (verbatim, see plan for timestamps):

- **Auto-detect ONLY at first-run setup, never during dispatch.** Honors documented "no silent fallback" principle.
- **De-duplicate `terminal.py`.** cast-server re-exports from `agents/_shared/terminal.py` via a thin shim. Single source of truth.
- **Extend `bin/cast-doctor` rather than create a new Python CLI.** `--fix-terminal` flag.
- **§3 (real headless dispatch) is dropped from this PR** — pre-flight verification proved synthetic SIGWINCH insufficient. SSH/CI users get the loud-failure path.
- **No new exception class.** Improve `ResolutionError`'s message in place.
- **`config.headless` / `config.interactive` flags** stay as-is. Their warning at `agent_service.py:1704-1708` continues to describe today's behavior accurately.
- **Auto-detect writes canonical keys** (`iterm`/`terminal`), not binary paths. Existing osascript dispatcher branch handles spawn.
- **`_SUPPORTED` is the single source of truth.** `bin/cast-doctor` reads it via `python3 -c`, with hardcoded fallback + CI parity test.
- **Back-compat alias.** `_config_default()` accepts both `terminal_default` (canonical) and `terminal` (alias). No migration prompt.
- **Test surface.** Extend `tests/test_b6_terminal_resolution.py` in place; add new `tests/test_cast_doctor.py` for the bash flow. Use `subprocess.run` with mocked `HOME` and `PATH`.

## Relevant Specs

No specs in `docs/specs/` cover files in this plan. The three existing specs (`cast-delegation-contract`, `cast-init-conventions`, `cast-output-json-contract`) are about agent delegation contracts, init conventions, and output-JSON shape — none of them link to `agents/_shared/terminal.py`, `cast-server/cast_server/infra/`, `bin/cast-doctor`, or the supported-terminals doc.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With | Commit boundary |
|-----------|------|------------|--------|-------------------|------|
| sp1_resolver_fixes | Sub-phase | — | sp2 | — | Commit 1 of the PR |
| sp2_cast_doctor_fix_terminal | Sub-phase | sp1 | — | — | Commit 2 of the PR |

Both sub-phases ship in the same PR but as two distinct commits, matching the plan's "Roll-out" section. sp2 depends on sp1 because:
- sp2's `bin/cast-doctor --fix-terminal` reads `_SUPPORTED.keys()` from the resolver — sp1 establishes that interface.
- sp2's docs update describes `--fix-terminal` and the alias behavior delivered in sp1.
- sp2's parity test asserts the bash hardcoded list matches `_SUPPORTED` — and `_SUPPORTED` may have new entries (`foot`/`konsole`) added in sp1 if the open question resolves yes.
