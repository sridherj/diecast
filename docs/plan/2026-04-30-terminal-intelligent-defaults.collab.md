# Plan: Terminal handling — intelligent defaults at first-run setup

## Context

A run failed with "Claude did not become ready within 30s" because terminal resolution silently fell off the bottom of the chain. Investigation revealed three coupled problems that hurt every diecast user, not just this machine:

1. **Config key drift.** `cast init` / docs write `terminal:`, but `resolve_terminal()` at `agents/_shared/terminal.py` (and its vendored copy `cast-server/cast_server/infra/terminal.py:61`) reads `terminal_default:`. The mismatch means a freshly-installed user with a real working terminal still hits the same failure.
2. **Silent fallback masks the cause.** `tmux_manager.py:83-86` swallows `ResolutionError` into a `WARNING` log and disables visible terminals. The user sees a misleading "ready timeout" 30s later instead of "no terminal configured."
3. **The GUI terminal is load-bearing for readiness, not cosmetic.** Per the comment at `agent_service.py:1668-1669`, Claude only finishes rendering its TUI prompt after a real client attaches — confirmed empirically (see §0 below). So "no GUI terminal" is *currently* equivalent to "agent never starts," and a SIGWINCH-only synthetic kick is not enough to make it render. Genuine headless dispatch is therefore out of scope for this PR — see §0.

**Goal of this plan:** make diecast Just Work for any user on Linux or macOS who has a terminal installed, with explicit auto-detect at first-run setup (not at dispatch) and loud failures during dispatch. No more 30s misleading timeouts. SSH/CI users keep the existing experience until a real headless story is designed.

## Pre-flight: §0 — empirical verification result (FAILED)

The original plan included a §3 "real headless mode" that synthesized SIGWINCH via `tmux resize-window` to make Claude render in a detached pane without a GUI client. **That smoke test ran and failed.**

```bash
SESSION=smoketest-$(date +%s)
tmux new-session -d -s "$SESSION" -x 200 -y 50 \
  'claude --dangerously-skip-permissions --model claude-haiku-4-5-20251001'
sleep 10                            # extended past the original 5s
tmux resize-window -t "$SESSION" -x 199 -y 50
tmux resize-window -t "$SESSION" -x 200 -y 50
sleep 5
tmux capture-pane -t "$SESSION" -p -J -S - -E -    # alt-screen-aware capture
# → pane is empty before AND after kick. Process is alive (10 worker threads,
#   pty /dev/pts/N, dimensions 200x50) but writes nothing until a real client
#   attaches.
```

**Why it fails:** Claude Code is a full Ink/React TUI app on the alternate screen buffer. SIGWINCH is necessary but not sufficient — Claude evidently waits for an actually-attached client before painting. Every public orchestration project surveyed ([Claude Code Agent Farm](https://github.com/Dicklesworthstone/claude_code_agent_farm), [amux](https://github.com/mixpeek/amux), [claude-tmux](https://github.com/nielsgroen/claude-tmux)) keeps real clients attached to tmux panes. None dispatch into detached sessions and rely on synthetic SIGWINCH. Anthropic's own [agent-teams docs](https://code.claude.com/docs/en/agent-teams) describe interactive orchestration only.

**Consequence:** §3 (`kick_winch`, headless dispatch path, the `config.headless`/`interactive` truth-table behavior) is removed from this PR. SSH/CI/no-display users will continue to hit Issue #2's loud failure (the *correct* error, no longer the misleading 30s timeout). Real headless dispatch becomes a follow-up effort exploring one of: a Claude CLI flag for non-TUI mode, `claude --print` one-shot invocations, or a permanently-attached phantom client (e.g., backgrounded `tmux attach` via `script`/`unbuffer`).

## Design

Three fixes that ship together.

### 1. Intelligent terminal auto-detection at first-run setup

The documented principle in `docs/reference/supported-terminals.md:11` — "no silent fallback to xterm or any safe default: a wrong terminal is worse than a clear error pointing at the fix" — is preserved. **Auto-detect runs at first-run setup only, never during dispatch.** During dispatch, `resolve_terminal()` keeps its loud-failure semantics.

**Resolution chain during dispatch** (unchanged from today):

```
1. $CAST_TERMINAL                  (explicit override)
2. $TERMINAL                       (POSIX convention)
3. ~/.cast/config.yaml             (accept either `terminal_default:` OR `terminal:` for back-compat)
4. ResolutionError (loud)          (no silent fallback)
```

**First-run setup flow** (new path, hooks into existing `needs_first_run_setup()`):

When `needs_first_run_setup()` returns `True` (no env vars, no config), `bin/cast-doctor --fix-terminal` runs interactively:

1. Probe candidates per platform (see below). Exclude any not on PATH.
2. **If exactly one candidate is found:** show what we picked, ask the user to confirm (Y/n), then write `~/.cast/config.yaml:terminal_default`.
3. **If multiple candidates are found:** present a numbered list; user picks one; write to config.
4. **If zero candidates are found:** print install instructions for the platform's most common terminal; exit 1.

No silent persistence: every config write is explicitly confirmed. This satisfies the "explicit over clever" engineering preference and keeps the documented principle intact.

**Probe candidates** (read from `_SUPPORTED.keys()` in `agents/_shared/terminal.py` — single source of truth, see Issue #6):

- **macOS** (`uname -s` = Darwin): `iterm` (if `/Applications/iTerm.app` exists), `terminal` (always present).
  - Note: these are *config keys*, not binaries. The dispatcher's existing `cmd in {"iterm", "terminal"}` branch (`supported-terminals.md:27-28`) handles `osascript`/AppleScript spawn — auto-detect just writes the key.
- **Linux**: `ptyxis`, `gnome-terminal`, `kitty`, `alacritty`, `foot` (add to `_SUPPORTED` if approved), `konsole` (add to `_SUPPORTED` if approved), `xterm`. Validated via `command -v`.
  - Probe order: if `$XDG_CURRENT_DESKTOP` contains `GNOME`, prefer `ptyxis`/`gnome-terminal`. If `KDE`, prefer `konsole`. Otherwise iterate the table order.

**Back-compat:** `_config_default()` accepts both `terminal_default:` (canonical) and `terminal:` (alias). Existing user configs keep working with no migration.

### 2. Loud, useful failures during dispatch

Stop swallowing `ResolutionError` into a 30s readiness timeout. In `TmuxManager._resolved_terminal()`, re-raise `ResolutionError` with an improved message instead of returning `None`:

```
ResolutionError: no terminal configured.
  tried: $CAST_TERMINAL (unset), $TERMINAL (unset),
         ~/.cast/config.yaml (key 'terminal_default' missing).
  fix:   run `bin/cast-doctor --fix-terminal` to auto-detect and configure,
         or set $CAST_TERMINAL=<your-terminal> manually.
         See docs/reference/supported-terminals.md.
```

The dispatcher (`agent_service.py`) catches the raise, kills the tmux session, and fails the run with the structured message — no more silent 30s timeout.

**No new exception class.** Improve `ResolutionError`'s message in place. (Per review Issue #8: a typed structured exception was overkill for a single raise site.)

**Note on `config.headless`:** the existing `config.interactive` / `config.headless` flags (`agent_service.py:1704`) stay as-is. Until a real headless mechanism is built (post-§0 verification failure), `config.headless=True` continues to take the existing interactive path; the warning at `agent_service.py:1704-1708` keeps describing today's behavior accurately.

### 3. `bin/cast-doctor --fix-terminal` (extend existing script)

`bin/cast-doctor` already exists as a Bash diagnostic with a `check_terminal()` function (`bin/cast-doctor:181-208`). **Extend it** with a `--fix-terminal` flag rather than creating a parallel Python CLI. (Per review Issue #3.)

Behavior:

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

`bin/cast-doctor` reads the canonical supported list from `agents/_shared/terminal.py:_SUPPORTED.keys()` via `python3 -c '...'`. If Python isn't installed yet (cast-doctor runs as the install-time gate), fall back to a hardcoded list with a `# KEEP IN SYNC WITH _SUPPORTED` comment plus a CI lint at `tests/test_cast_doctor.py` that asserts the two lists match. (Per review Issue #6.)

The existing `check_terminal()` keeps reporting yellow when nothing is configured but auto-detect would succeed — and now points at `bin/cast-doctor --fix-terminal` as the fix.

## Critical Files To Change

| File | Change |
|------|--------|
| `agents/_shared/terminal.py` | Canonical resolver. Update `_config_default()` to accept both `terminal:` and `terminal_default:` keys. Add `_autodetect()` (platform-aware probe; **called only by `needs_first_run_setup` flow**, NOT by `resolve_terminal`). Improve `ResolutionError` message. Add `foot`/`konsole` to `_SUPPORTED` if we want them auto-detected (decide). |
| `cast-server/cast_server/infra/terminal.py` | **De-vendor.** Replace contents with `from agents._shared.terminal import *  # re-export` (thin shim). Add `agents/` to cast-server's `sys.path` at startup if not already importable. Delete the duplicated logic. (Per review Issue #2.) |
| `cast-server/cast_server/infra/tmux_manager.py` | `_resolved_terminal()` re-raises `ResolutionError` instead of swallowing it (was lines 83-86). |
| `cast-server/cast_server/services/agent_service.py` | Catch `ResolutionError` raised from `open_terminal()` and fail the run with the structured message; kill the tmux session before raising (no more silent 30s timeout). |
| `bin/cast-doctor` | Add `--fix-terminal` flag with interactive auto-detect + persist flow. Update `check_terminal()` to point at `--fix-terminal` as the fix. Read supported list from `_SUPPORTED.keys()` via `python3 -c` (with hardcoded fallback + CI parity test). |
| `docs/reference/supported-terminals.md` | Document `--fix-terminal`, the first-run-setup flow, and the dual-key alias for back-compat. Reaffirm "no silent fallback during dispatch." |
| `tests/test_b6_terminal_resolution.py` | **Extend in place.** Add tests for: (a) `_autodetect()` probe order on Linux per `XDG_CURRENT_DESKTOP`, (b) macOS `iterm`/`terminal` key emission, (c) updated `needs_first_run_setup()` semantics, (d) `terminal:` key alias acceptance. Update existing `test_first_run_prompt_*` tests for the new flow. (Per review Issue #9.) |
| `tests/test_cast_doctor.py` | **New.** `subprocess.run(['bin/cast-doctor', '--fix-terminal'], env={'HOME': tmp_path}, input=...)` test. Mocks PATH to control the candidate set: zero / one / multiple. Asserts `~/.cast/config.yaml` contents. Includes the parity assertion that cast-doctor's hardcoded fallback list matches `_SUPPORTED.keys()`. (Per review Issue #11.) |

## Reuse / Existing Code

- `_SUPPORTED` table at `agents/_shared/terminal.py:30-37` is the single source of truth for terminal keys (per Issue #6). cast-doctor reads it; auto-detect probes from it; tests parametrize over it.
- `needs_first_run_setup()` at `agents/_shared/terminal.py:97` already exists. The new `--fix-terminal` flow plugs into the existing first-run UX hook rather than inventing a new one.
- The dispatcher's existing `cmd in {"iterm", "terminal"}` branch (per `supported-terminals.md:27-28`) handles macOS AppleScript spawn — auto-detect emits keys that this branch already handles. No new spawn code on macOS.

## Verification

After implementation:

1. **Fresh user on GNOME, no env vars, no config:** `bin/cast-doctor` reports yellow → user runs `--fix-terminal` → script picks ptyxis (or prompts to choose if multiple) → writes config → next dispatch succeeds.
2. **Fresh user on macOS, no env vars:** `--fix-terminal` picks `iterm` if iTerm.app exists else `terminal` → existing osascript spawn path opens the window.
3. **Existing user with `terminal: ptyxis`** (today's broken config): alias accepted, no migration prompt, works.
4. **Misconfigured `$CAST_TERMINAL=nope`:** `ResolutionError` raised with full chain in message; run fails fast (not at 30s).
5. **`bin/cast-doctor --fix-terminal`** auto-detects, prompts for confirmation/disambiguation, persists, and is idempotent across re-runs.
6. **`tests/test_b6_terminal_resolution.py`, `test_cast_doctor.py`** all pass; CI parity check between cast-doctor's hardcoded list and `_SUPPORTED` passes.
7. **The original failing run scenario** (env vars unset, config has wrong key): `terminal:` alias accepted by the resolver, run reaches "ready". (No re-probe needed — alias makes the existing config valid.)

## Out of Scope

- Replacing tmux as the underlying multiplexer.
- Windows / WSL native terminal support (separate problem; WSL users today get the Linux path).
- Live web-UI streaming of agent output as an alternative to GUI terminals.
- Adding `wezterm` to `_SUPPORTED` (cast-doctor mentions it but the resolver doesn't support it). Decide separately whether diecast officially supports wezterm; if yes, that's a follow-up PR with proper flag entries.
- AppleScript automation for fancier macOS window/tab management — existing `osascript` path is enough for v1.
- Auto-detect during dispatch (explicitly rejected per Issue #1).
- **Real headless dispatch** (synthetic SIGWINCH via `tmux resize-window` proven empirically insufficient — Claude Code requires an actually-attached client to render its TUI; see §0). A separate effort can explore: a Claude CLI non-TUI flag, `claude --print` one-shot invocations, or a permanently-attached phantom client wrapped in `script`/`unbuffer`.

## Roll-out

Two commits in one PR:

1. **Resolver fixes + key alias + de-vendor + loud failure** (`agents/_shared/terminal.py`, `cast-server/cast_server/infra/terminal.py` shim, `tmux_manager.py`, `agent_service.py`). Self-contained, fully unit-testable. Includes `test_b6_terminal_resolution.py` updates.
2. **`bin/cast-doctor --fix-terminal` + docs update + parity test** (`bin/cast-doctor`, `docs/reference/supported-terminals.md`, `test_cast_doctor.py`).

No DB migration. No config migration (back-compat alias preserves existing user configs).

---

## Decisions

- **2026-04-30T20:30:00Z — Reconcile silent auto-detect with documented "no silent fallback" principle?** — Decision: Auto-detect ONLY at first-run setup, never during dispatch. Rationale: Honors the documented principle in `supported-terminals.md:11`; uses the existing `needs_first_run_setup()` hook; explicit > clever.
- **2026-04-30T20:32:00Z — How to handle the two terminal.py copies (canonical `agents/_shared/` + vendored `cast-server/`)?** — Decision: De-duplicate. cast-server re-exports from `agents/_shared/terminal.py` via a thin shim. Rationale: Single source of truth; all future fixes land once; vendoring justification (import path) is solvable with sys.path setup.
- **2026-04-30T20:34:00Z — Plan invented a new Python `cast doctor` CLI, but `bin/cast-doctor` already exists. Resolution?** — Decision: Extend `bin/cast-doctor` with `--fix-terminal` flag; no new Python CLI. Rationale: Single doctor surface; matches existing UX; no new entrypoint to discover; `cast-doctor:60` already declares it intentionally usable post-install.
- **2026-04-30T20:38:00Z — `kick_winch()` SIGWINCH theory is unverified and load-bearing for §3. Approach?** — Decision: Run a 5-minute smoke test first; gate §3 on it passing. Rationale: §3 is the only part of the PR creating new product value (SSH/CI support) AND the only part built on an untested technical claim.
- **2026-04-30T20:42:00Z — Plan's macOS auto-detect uses `open -a` but `_SUPPORTED` table uses `osascript` keys. Fix?** — Decision: Auto-detect writes canonical keys (`iterm`/`terminal`) to config; existing osascript dispatcher path handles spawn. Rationale: Reuses production-tested macOS code path; decouples "name a terminal" from "prescribe how to spawn it"; zero new spawn code.
- **2026-04-30T20:45:00Z — Drift between `bin/cast-doctor:37` supported list and `_SUPPORTED` table (wezterm/iterm2 vs iterm; `_SUPPORTED` missing wezterm). Resolution?** — Decision: Make `_SUPPORTED` (Python) the single source of truth; cast-doctor reads from it via `python3 -c`, with hardcoded fallback + CI parity test. Rationale: Prevents future drift; canonical list lives where dispatcher consumes it.
- **2026-04-30T20:48:00Z — Should headless dispatch decision use env probe or config flags?** — Decision: ~~Use both — env-detection default + config flag override.~~ **SUPERSEDED** by 2026-04-30T20:55:00Z below.
- **2026-04-30T20:50:00Z — Shape of new `TerminalNotFound` exception?** — Decision: No new class. Keep `ResolutionError`; just improve its message. Rationale: Single raise site today; structured exception is overkill; simpler.
- **2026-04-30T20:55:00Z — REVISED: Should headless dispatch decision use env probe or config flags?** — Decision: Drop $DISPLAY/$WAYLAND_DISPLAY detection entirely; use `config.interactive` / `config.headless` flags only. Rationale: Explicit > clever; collapses 8-cell test matrix to 3 cases; matches "explicit over clever" engineering preference. Note: superseded in practice by 2026-04-30T21:30:00Z (§3 removal) — `config.headless` semantics revert to today's behavior.
- **2026-04-30T20:58:00Z — How to organize new test surface against existing `test_b6_terminal_resolution.py`?** — Decision: Extend in-place; update tests broken by Issue #1's auto-detect refactor. Rationale: Keeps related tests in one file; reuses existing fixtures (clean_env, monkeypatch, tmp_path); easier full-coverage review.
- **2026-04-30T21:00:00Z — How to test the new `bin/cast-doctor --fix-terminal` flag?** — Decision: Pytest test with `subprocess.run(['bin/cast-doctor', '--fix-terminal'], env=..., input=...)` and a tmp HOME. Rationale: Integrates with existing pytest CI; easy to mock PATH scenarios; failure messages land in same test report.
- **2026-04-30T21:03:00Z — Optimize `kick_winch()`'s ~100ms-per-dispatch cost under fan-out orchestration?** — Decision: ~~Always call `kick_winch()`; tolerate the cost.~~ **MOOT** — `kick_winch()` removed entirely per 2026-04-30T21:30:00Z below.
- **2026-04-30T21:30:00Z — §0 smoke test result and §3 fate?** — Decision: §0 FAILED. `tmux resize-window` synthesizes SIGWINCH but Claude Code requires an actually-attached client to render its TUI (Ink/React on alt-screen). Verified by re-test with longer wait (10s) and alt-screen-aware capture (`-S - -E -`); pane stays empty before and after kick. Web-search of public Claude Code orchestration projects (Agent Farm, amux, claude-tmux) confirms all keep real clients attached — none rely on synthetic SIGWINCH. Drop §3 entirely from this PR. Ship §1 + §2 + §4 (renumbered to §3) only. SSH/CI users keep today's experience but now hit a clear loud failure instead of a misleading 30s timeout. Rationale: ship what works, fail loudly when it doesn't, leave headless dispatch for a follow-up that explores `claude --print` / phantom-attached client / a CLI non-TUI flag.
