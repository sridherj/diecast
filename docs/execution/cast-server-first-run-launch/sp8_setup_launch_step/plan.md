# Sub-phase 8: `setup` — step 8 launch + browser + alembic + PATH check + `print_next_steps` rewrite

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Wire the new `step8_launch_and_open_browser` into `setup` so a fresh `./setup` ends with cast-server already running and the dashboard open in a browser. Wire in the boot-time alembic upgrade between step 5 and step 8. Add the post-install PATH check. Rewrite `print_next_steps` with two branches (running vs deferred). Renumber Step X/7 → Step X/8 across 8 sed targets. This is the final user-visible payoff sub-phase.

## Dependencies

- **Requires completed:**
  - sp1 (port seam) — uses `8005` default; `step6_write_config` `DEFAULTS` already has `host`/`port`.
  - sp2 (doctor preflight) — `step1_doctor` calls extended `bin/cast-doctor`.
  - sp3 (alembic) — `alembic upgrade head` is callable from `cast-server/`.
  - sp4 (log rotation) — `RotatingFileHandler` owns `server.log`; `nohup` redirect goes to `bootstrap.log` (Decision #13).
  - sp6 (`/cast-doctor` skill) — mental-model coherence; `print_next_steps` references `/cast-runs` (already existed) and the auto-launch flow.
- **Assumed codebase state:**
  - `setup` is at HEAD with sp1's `DEFAULTS` `host`/`port` additions.
  - `bin/cast-doctor --fix-terminal` exists (already shipped in commit `28db472`).
  - `cast-server` binary on `~/.local/bin` after `step5_install_cast_server`.
  - `bin/_lib.sh` provides `log` / `warn` / `fail`.

## Scope

**In scope:**
- Renumber Step X/7 → Step X/8 across 8 sed targets at `setup:85, 93, 120, 130, 149, 170, 196, 296`.
- Insert `alembic upgrade head` invocation between `step5_install_cast_server` and the new `step8_*` (after step 5, before step 8 — i.e., effectively between step 5 and step 6 if we keep numbering, but the plan §E item 4 says "between step 5 and step 8" which means: any time before step 8 starts and after step 5 finishes — pick the cleanest insertion point in the dispatcher).
- New `step8_launch_and_open_browser` function:
  - Skip-condition gate (UPGRADE_MODE / DRY_RUN / NO_PROMPT / CI / already-running).
  - Port pre-flight probe (cast-server vs other-process vs free).
  - `mkdir -p ~/.cache/diecast` (happy path only — Decision #11).
  - Detached background launch via `( nohup ... >bootstrap.log 2>&1 & ) >/dev/null 2>&1` (Decision #4 + #13).
  - Readiness poll: 30 × 0.5s = 15s max via `bash /dev/tcp/${host}/${port}` (Decision #10).
  - Terminal wire-up: `bin/cast-doctor --fix-terminal` (interactive only).
  - Browser open: macOS `open`, Linux `xdg-open` (with display detect).
  - Post-install PATH check.
- Rewrite `print_next_steps` with two branches keyed on `LAUNCHED=0/1`.
- Wire `step8_launch_and_open_browser` into `main` after `prune_old_backups` and before `print_next_steps` (`setup:345–346`).

**Out of scope (do NOT do these):**
- The launch step's underlying primitives — port seam (sp1), cast-doctor (sp2), alembic (sp3), log rotation (sp4), `/cast-doctor` skill (sp6). All assumed complete.
- Auto-detect/auto-kill old `:8000` daemon — Decision #1 says don't.
- Auto-edit user shell rc — Decision #1 says warn only.
- New automated tests for the launch step — Decision #8 says rely on manual matrix.
- `/cast-init` parity — explicit out-of-scope.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `setup` | Modify | 7-step driver. `print_next_steps` at `:325–334`. Step counter X/7 at 8 sites. Dispatch order ends at `prune_old_backups` → `print_next_steps`. |

## Detailed Steps

### Step 8.1: Step counter renumber Step X/7 → Step X/8

Find every occurrence and renumber. Targets per the plan: `setup:85, 93, 120, 130, 149, 170, 196, 296`.

```bash
sed -i 's|Step 1/7|Step 1/8|; s|Step 2/7|Step 2/8|; s|Step 3/7|Step 3/8|; \
        s|Step 4/7|Step 4/8|; s|Step 5/7|Step 5/8|; s|Step 6/7|Step 6/8|; \
        s|Step 7/7|Step 7/8|' setup
```

After running, confirm `grep -n "Step .*/7" setup` returns nothing and `grep -n "Step .*/8" setup` returns 7 (one per existing step) plus the new step 8 once it's added.

### Step 8.2: Insert `alembic upgrade head` between step 5 and step 8

Per plan §E item 4: "after step 5 (`step5_install_cast_server`) and before step 8 (launch)". The cleanest pattern is a tiny new function `step5b_run_migrations` (or fold into the existing dispatch order without renumbering). Suggested implementation: add a new function and call it right after `step5_install_cast_server` in `main`:

```bash
step5b_run_migrations() {
  log "Step 5b/8: running database migrations"
  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "  (dry-run — would run: uv run alembic upgrade head)"
    return 0
  fi
  ( cd "${REPO_DIR}/cast-server" && uv run alembic upgrade head ) || \
    fail "alembic upgrade head failed; refusing to launch with possibly-broken DB"
}
```

(Note the X/8 numbering. If you'd rather not introduce sub-step numbering, the call can be a private helper invoked at the top of `step6_write_config` or at the end of `step5_install_cast_server`. Pick whichever matches existing conventions — but **do** make sure failure aborts setup verbatim per plan §E item 4.)

### Step 8.3: Author `step8_launch_and_open_browser`

Insert this function definition above `print_next_steps` in `setup`:

```bash
step8_launch_and_open_browser() {
  log "Step 8/8: launch cast-server + open dashboard"

  local host="${CAST_HOST:-localhost}"
  local port="${CAST_PORT:-8005}"
  local url="http://${host}:${port}/"

  # Skip conditions (any one short-circuits this step).
  if [ "${UPGRADE_MODE:-0}" -eq 1 ]; then
    log "  skipping launch: --upgrade mode"
    LAUNCHED=0; return 0
  fi
  if [ "${DRY_RUN:-0}" -eq 1 ]; then
    log "  skipping launch: --dry-run"
    LAUNCHED=0; return 0
  fi
  if [ "${NO_PROMPT:-0}" -eq 1 ] || [ -n "${CI:-}" ]; then
    log "  skipping launch: non-interactive (--no-prompt or CI)"
    LAUNCHED=0; return 0
  fi

  # Port pre-flight probe.
  if exec 3<>"/dev/tcp/${host}/${port}" 2>/dev/null; then
    exec 3<&-; exec 3>&-
    # Something is already bound. Determine whether it is our cast-server.
    if curl -s --max-time 1 "${url}api/agents/runs?status=running" >/dev/null 2>&1; then
      log "  cast-server already running on ${host}:${port}; opening browser only"
      LAUNCHED=1
      _open_browser "${url}"
      return 0
    fi
    # Bound by something else.
    local pid cmd
    pid=$(lsof -ti ":${port}" 2>/dev/null | head -1)
    cmd=$(ps -p "${pid:-0}" -o comm= 2>/dev/null || echo "?")
    warn "port ${port} in use by PID ${pid:-?} (${cmd})."
    warn "       set CAST_PORT=<n> ./setup, or stop the process and re-run."
    warn "       (skipping launch — install otherwise complete)"
    LAUNCHED=0
    return 0
  fi

  # Happy path: nothing on the port. Touch the cache dir only here (Decision #11).
  mkdir -p "${HOME}/.cache/diecast"

  # Detached background launch (Decision #4 — drop disown; Decision #13 — bootstrap.log).
  ( nohup "${HOME}/.local/bin/cast-server" \
        >"${HOME}/.cache/diecast/bootstrap.log" 2>&1 & ) >/dev/null 2>&1

  # Readiness poll: 30 × 0.5s = 15s (Decision #10).
  local i
  for i in $(seq 1 30); do
    if exec 3<>"/dev/tcp/${host}/${port}" 2>/dev/null; then
      exec 3<&-; exec 3>&-
      LAUNCHED=1
      break
    fi
    sleep 0.5
  done

  if [ "${LAUNCHED:-0}" -ne 1 ]; then
    warn "cast-server did not become ready within 15s."
    warn "       check ${HOME}/.cache/diecast/bootstrap.log for startup errors."
    LAUNCHED=0
    return 0   # never fail setup over the launch step
  fi

  # Terminal wire-up (Decision §B step 5). Skipped on --no-prompt / CI (already filtered above).
  if [ -x "${REPO_DIR}/bin/cast-doctor" ]; then
    "${REPO_DIR}/bin/cast-doctor" --fix-terminal || \
      warn "  bin/cast-doctor --fix-terminal returned non-zero (continuing)"
  fi

  _open_browser "${url}"

  # Post-install PATH check.
  case ":${PATH}:" in
    *":${HOME}/.local/bin:"*) : ;;
    *) warn "cast-server installed to ~/.local/bin, which is not on your \$PATH.
           Add this to your shell rc (e.g. ~/.zshrc, ~/.bashrc):
             export PATH=\"\$HOME/.local/bin:\$PATH\"
           Then restart your shell or: source ~/.zshrc" ;;
  esac
}

_open_browser() {
  local url="$1"
  case "$(uname -s)" in
    Darwin) open "${url}" 2>/dev/null || true ;;
    Linux)
      if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${url}" >/dev/null 2>&1 &
      else
        log "  no display detected — visit ${url} manually"
      fi
      ;;
    *) log "  unsupported OS for browser open — visit ${url} manually" ;;
  esac
}
```

Notes:
- The "is it our cast-server already running?" probe uses curl against `/api/agents/runs?status=running`. The plan's health-check at the prompt's bottom is exactly this URL: `curl -s http://localhost:8000/api/agents/runs?status=running | head -1`. Reuse the same convention.
- Decision #18 introduces `/api/health`; sp6 ships it. Once that's available, this probe could optionally upgrade to `/api/health` for stronger ready-signaling. Plan §B step 4 explicitly specifies TCP-only; keep TCP-only here unless you want to also coordinate sp6's endpoint. Deferred.
- `lsof` may not be installed on minimal containers — fall through gracefully if `pid` is empty.

### Step 8.4: Wire `step8_launch_and_open_browser` into `main`

Find the dispatcher near `setup:345–346` (after `prune_old_backups`, before `print_next_steps`):

```bash
prune_old_backups
step8_launch_and_open_browser   # NEW
print_next_steps
```

Initialize `LAUNCHED=0` at the top of `main` so the variable is always defined before `print_next_steps` reads it:

```bash
LAUNCHED=0
```

Place this near the other env-var initializations (`DRY_RUN=${DRY_RUN:-0}`, etc.).

### Step 8.5: Rewrite `print_next_steps`

Replace the current single-branch implementation at `setup:325–334` with two branches:

```bash
print_next_steps() {
  local host="${CAST_HOST:-localhost}"
  local port="${CAST_PORT:-8005}"
  local url="http://${host}:${port}"

  if [ "${LAUNCHED:-0}" -eq 1 ]; then
    cat <<EOF

[cast] Install complete. cast-server is running at ${url}
       (logs: ~/.cache/diecast/server.log; bootstrap: bootstrap.log)

To restart it later (e.g. after reboot):
  cast-server                            # background-friendly defaults
  CAST_PORT=8080 cast-server             # custom port
  CAST_BIND_HOST=0.0.0.0 cast-server     # bind for LAN access (server side)
  CAST_HOST=cast.example.com cast-server # connect target (client side; future cloud)

Next steps:
  1. /cast-init   — scaffold a new project (writes CLAUDE.md + cast-* dirs)
  2. /cast-runs   — open the dashboard you just launched

Docs: docs/config.md (config keys) · docs/troubleshooting.md (recovery & FAQ)
EOF
  else
    cat <<EOF

[cast] Install complete. To start the server: cast-server

Next steps:
  1. /cast-init   — scaffold a new project (writes CLAUDE.md + cast-* dirs)
  2. /cast-runs   — open the dashboard once cast-server is up

Docs: docs/config.md (config keys) · docs/troubleshooting.md (recovery & FAQ)
EOF
  fi
}
```

### Step 8.6: Sanity-check the dispatch order

After all edits, the `main` function should look like:

```bash
main() {
  LAUNCHED=0
  # ... existing flag parsing ...
  step1_doctor
  step2_*
  step3_install_agents
  step4_install_skills
  step5_install_cast_server
  step5b_run_migrations           # NEW (sp8 step 8.2)
  step6_write_config
  step7_*
  prune_old_backups
  step8_launch_and_open_browser   # NEW (sp8 step 8.4)
  print_next_steps                # REWRITTEN (sp8 step 8.5)
}
```

(Adjust to match actual function names. The 7th step in the existing setup is whatever currently runs before `prune_old_backups`. Don't reorder existing steps.)

## Verification

### Automated Tests (permanent)
- No new tests (Decision #8). The launch step is bash glue around well-tested primitives.
- `uv run pytest` — full suite remains green.

### Validation Scripts (temporary)

Run the plan's full manual-verification matrix (items 1–7, 13–24, 31–32 from the plan §Verification list) — selectively:

```bash
# 1. Fresh-install path:
rm -rf ~/.claude/agents/cast-* ~/.local/bin/cast-server ~/.cache/diecast
./setup
# Expect: server bound on :8005, browser opens to http://localhost:8005,
#         "Install complete. cast-server is running at …" message.

# 2. Port-config seam:
CAST_PORT=8090 CAST_BIND_HOST=0.0.0.0 ./setup
# Expect: server binds on 0.0.0.0:8090, dashboard URL reflects override.

# 4. Upgrade path:
./setup --upgrade
# Expect: NO relaunch. "To start the server: cast-server" message.

# 5. CI/headless path:
CI=1 ./setup --no-prompt
# Expect: no launch, no browser, no ~/.cache/diecast/ created.

# 6. Already-running path:
cast-server &
./setup
# Expect: skip launch, still open browser, "running at …" message.

# 7. No-display Linux path:
unset DISPLAY WAYLAND_DISPLAY
./setup
# Expect: server launches; "visit … manually" log.

# 15. Port-conflict path:
python3 -m http.server 8005 &
./setup
# Expect: "port 8005 in use by PID <x> (python3) — set CAST_PORT=…",
#         LAUNCHED=0, deferred branch.
kill %1

# 22. PATH check:
PATH="$(echo "$PATH" | tr ':' '\n' | grep -v '/.local/bin' | tr '\n' ':')" ./setup
# Expect: warning with the export line.

# 23. Terminal wire-up:
# On a fresh box where needs_first_run_setup() returns True, ./setup invokes
# bin/cast-doctor --fix-terminal. With --no-prompt, the call is skipped.
```

### Manual Checks
- Step counter shows X/8 in every log line during a fresh install.
- `print_next_steps` "running" branch fires when `LAUNCHED=1`; "deferred" when `LAUNCHED=0`.
- `~/.cache/diecast/bootstrap.log` exists after a happy-path install; `~/.cache/diecast/server.log` accumulates (sp4's RotatingFileHandler).
- `lsof ~/.cache/diecast/bootstrap.log` shows the nohup-redirect handle (decision #13 test).
- `lsof ~/.cache/diecast/server.log` shows only the cast-server Python process (decision #13 test).

### Success Criteria
- [ ] Step counter renumbered Step X/7 → Step X/8 across all 8 sites.
- [ ] `step5b_run_migrations` (or equivalent) runs `alembic upgrade head` before `step8`.
- [ ] `step8_launch_and_open_browser` exists and is wired into `main` between `prune_old_backups` and `print_next_steps`.
- [ ] All five skip-conditions short-circuit cleanly (UPGRADE_MODE, DRY_RUN, NO_PROMPT, CI, already-running).
- [ ] Port pre-flight handles three cases: free / our cast-server / other process.
- [ ] `mkdir -p ~/.cache/diecast` only executes on the happy path (after all skip checks).
- [ ] Detached launch: `( nohup ... & ) >/dev/null 2>&1`; writes to `bootstrap.log` (not `server.log`).
- [ ] Readiness poll: 30 × 0.5s = 15s.
- [ ] `bin/cast-doctor --fix-terminal` invoked when interactive (not `--no-prompt`/CI).
- [ ] Browser open: macOS `open`; Linux `xdg-open` with display detect; otherwise log+continue.
- [ ] PATH check fires the warning when `~/.local/bin` is missing.
- [ ] `print_next_steps` two-branch rewrite keys on `LAUNCHED`.
- [ ] All plan §Verification items 1–7, 13–24, 31–32 pass on a real fresh-install run.

## Execution Notes

- **Never fail setup over the launch step.** Every error path emits a warning and continues. The launch step is convenience; the install is the contract.
- **Step counter sed targets shift after sp1.** sp1's `DEFAULTS` edits at `setup:218–227` may have shifted line numbers slightly. Use `grep -n 'Step .*/7' setup` to find the current locations rather than trusting hardcoded line numbers.
- **`step5b` vs renumbering everything to 9 steps:** the simpler approach (and what the plan implies) is to keep the renumber to /8 and call alembic from a sub-step. Avoid renumbering to /9 — the plan and the printout text both say `/8`.
- **The `lsof -ti :${port}` probe** doesn't work without `lsof` installed. On minimal containers (Alpine, etc.) without lsof, the probe falls through gracefully (empty `pid`, `cmd=?`). Don't `fail` over a missing `lsof`.
- **Terminal wire-up requires `bin/cast-doctor --fix-terminal` to be a no-op when configured.** That's the contract from the terminal-defaults plan (already shipped). Do not re-implement.
- **Coordinate with sp6:** sp6 may further edit `bin/cast-doctor` (lines 12, 57, 224, 241 wording). The `--fix-terminal` flag mechanism is unchanged; only the user-discovery wording moves. sp8's invocation is unaffected.
- **Backward-compat reminder:** Decision #1 says don't auto-detect old `:8000` daemons. Users with an old daemon kill it manually before re-running setup; CHANGELOG entry covers this. Do not add detection logic here.

**Spec-linked files:** None (`setup` is not currently linked by any spec).
