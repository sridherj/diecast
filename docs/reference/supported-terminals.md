# Supported Terminals

Diecast spawns child agent sessions in a new terminal tab. The terminal binary is **never hardcoded**: every dispatcher resolves it through `agents/_shared/terminal.py:resolve_terminal()`. This document lists the supported terminals, the env-var contract that selects one, and the per-terminal quirks contributors need to know.

## Resolution order

`resolve_terminal()` walks four sources in order and returns the first non-empty value:

1. **`$CAST_TERMINAL`** — preferred. Project-scoped; setting this in the shell that runs Diecast (or in a `.envrc`) keeps a per-project terminal choice independent of the user's POSIX default.
2. **`$TERMINAL`** — POSIX convention. Many users already export this for non-Diecast tools; respecting it avoids forcing a second variable.
3. **`~/.cast/config.yaml:terminal_default`** — written by `/cast-setup` (Phase 4) on first run. Survives shell restarts and removes the need for env-var plumbing in graphical launchers.
4. **`ResolutionError`** — raised when all three sources are empty. The error message names all three sources and links here. There is **no silent fallback** to `xterm` or any "safe default": a wrong terminal is worse than a clear error pointing at the fix.

`resolve_terminal()` returns a `ResolvedTerminal(command, args, flags)`. `command` is the executable; `args` carries any additional tokens parsed from the env-var/config string via `shlex.split` (e.g., `CAST_TERMINAL="kitty --single-instance"` → `command="kitty"`, `args=["--single-instance"]`). `flags` is a per-terminal preset pulled from the `_SUPPORTED` table inside `terminal.py`.

> **Security:** the resolved command MUST be passed as `args=[command, *args, ...]` to `subprocess.Popen`. NEVER use `shell=True`. Both env vars and the config file are user-writable, and `shell=True` would expand them through the shell.

## Supported terminals

| Terminal | Platform | Install (typical) | Recommended setting | Notes |
|----------|----------|-------------------|---------------------|-------|
| `ptyxis` | Linux (GNOME 46+) | `flatpak install app.devsuite.Ptyxis` or distro package | `export CAST_TERMINAL=ptyxis` | Default on modern GNOME; uses `--new-window`, `--working-directory=DIR` | <!-- diecast-lint: ignore-line -->
| `gnome-terminal` | Linux (GNOME) | distro package | `export CAST_TERMINAL=gnome-terminal` | Uses `--tab` (not `--new-window`); `--working-directory=DIR` |
| `kitty` | Linux, macOS | distro package or `brew install kitty` | `export CAST_TERMINAL=kitty` | New tabs go through the remote-control protocol (`@launch --type=tab`); cwd flag is `--directory=` (no second `working-`) |
| `alacritty` | Linux, macOS, Windows | distro package or `brew install alacritty` | `export CAST_TERMINAL=alacritty` | No tabbed mode — each child opens a new window; cwd flag is `--working-directory DIR` (space-separated, NOT `=`); the `-e` separator must terminate the alacritty argv before the child command |
| `iterm` | macOS | App Store / `brew install --cask iterm2` | `export CAST_TERMINAL=iterm` | Tab spawn requires AppleScript (`osascript`) — flags table is empty; the dispatcher uses a Mac-specific path |
| `terminal` | macOS | preinstalled | `export CAST_TERMINAL=terminal` | macOS Terminal.app, also via `osascript`; flags table empty |

The `_SUPPORTED` table in `agents/_shared/terminal.py` mirrors this list and is the single source of truth that callers consult for per-terminal flags. Any binary whose `Path(cmd).name` does not appear in the table still resolves cleanly — `flags` is simply an empty dict, and the dispatcher falls back to "spawn the binary with the cwd preset off". This keeps unknown terminals usable for advanced users while ensuring first-class support for the listed ones.

## Adding a new terminal

1. Add an entry to `_SUPPORTED` in `agents/_shared/terminal.py`. Use the binary's basename as the key. Required keys: `new_tab_flag` (string, may be empty if no tabbed mode), `cwd_flag` (string, including the trailing `=` if applicable).
2. Document the terminal in the table above. Include the install command and any quirks.
3. Add a row to the parametrized `test_supported_table_drives_resolution` in `tests/test_b6_terminal_resolution.py` so the resolver is exercised against the new entry.
4. Run `bin/lint-anonymization` before committing — it runs in CI and will block any non-public reference.

## Quirks

- **kitty's `--directory` flag** has no `working-` prefix. This is intentional in the kitty CLI; do not "normalize" it to match the others.
- **alacritty's `-e` separator** ends alacritty's argv list. Anything after `-e` is the child command, so the resolver returns flags **without** an explicit `-e`; the dispatcher inserts `-e` immediately before the child command.
- **alacritty has no native tabs** — each spawn is a new window. The `new_tab_flag` is intentionally empty.
- **ptyxis vs gnome-terminal** look like one tool but have different flags. ptyxis prefers `--new-window` (separate window per child); gnome-terminal prefers `--tab` (all children share one window). Do not collapse these into a shared entry. <!-- diecast-lint: ignore-line -->
- **macOS Terminal.app and iTerm** have no useful CLI for tab spawn. The dispatcher invokes `osascript` with a tiny AppleScript snippet to open the new tab and `cd` into the goal dir. The `_SUPPORTED` entry is intentionally empty for these — the dispatcher branches on `cmd in {"iterm", "terminal"}` rather than on the flag preset.

## First-run setup

`needs_first_run_setup(config_path=...)` returns `True` only when **all** of the following hold:

- `$CAST_TERMINAL` is unset.
- `$TERMINAL` is unset.
- `~/.cast/config.yaml` lacks a non-empty `terminal_default` value (file may be absent entirely).

The `/cast-setup` slash command (shipping in Phase 4) calls this helper at the start of every run. When it returns `True`, `/cast-setup` prompts the user to pick a terminal from the supported list above and writes `terminal_default` into `~/.cast/config.yaml`. Subsequent runs see the config value and skip the prompt.

**This sub-phase ships only the prompt-trigger helper.** The interactive prompt itself, the config-write logic, and the shell snippet that exports `$CAST_TERMINAL` for the rest of the session all land in Phase 4's `/cast-setup` script.

## Why no `xterm` fallback?

Silent fallbacks to `xterm` were considered and rejected. Two reasons:

1. **`xterm` is rarely the user's preferred terminal.** Spawning into `xterm` when the user expected ptyxis or kitty produces a confusing UX — the new tab opens "somewhere else", and the user wastes time hunting for it. <!-- diecast-lint: ignore-line -->
2. **A clear error is recoverable; a silent fallback is not.** `ResolutionError` names all three resolution sources and links here. The user fixes it in seconds. A silent `xterm` spawn produces no error and no log entry that points at the cause.

If a user genuinely wants `xterm`, `export CAST_TERMINAL=xterm` is one keystroke shorter than discovering the silent fallback exists.
