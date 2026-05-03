# Plan: First-run setup hardening — auto-launch, port seam, preflight, migrations, README

## Context

Three friction points surfaced in the same session, plus a hardening pass over the surrounding setup machinery (Alembic migrations, log rotation, preflight, PATH check, port-conflict handling, terminal wire-up, shellcheck CI). The hardening items are folded into this plan rather than spawning a separate doc — they all share the "fresh `./setup` Just Works end-to-end" outcome.

Original three:

1. **README has no "how to start the server" section.** It mentions `cast-server` as a thing on `$PATH` and says "if you do run cast-server, you get…" — but never tells the reader the actual command. Confirmed via grep: `cast-server` appears only in the install blurb (`README.md:55`), the feature list (`:93–98`), and the directory tree (`:204`, `:207`). No quick-start invocation.

2. **`./setup` finishes installing but doesn't launch anything.** The user has to learn there's a server, learn the command, and run it manually before `/cast-runs` (which `print_next_steps` already advertises) becomes meaningful. The user wants zero extra steps on first install.

3. **Port `8000` is a high-collision dev port and is hardcoded in 30+ places.** `bin/cast-server:19` reads `${CAST_PORT:-8000}` correctly, but `skills/claude-code/cast-*/`, `agents/cast-*/`, and `cast-server/cast_server/services/agent_service.py` docstrings hardcode `http://localhost:8000`. The user wants a single seam (host + port) that future cloud deployments can also flip — same env vars, different values, no skill edits.

The user also clarified the scoping model in conversation: **one goal = one repo.** The schema already supports this — `goals` has `folder_path`, `gstack_dir`, and `external_project_dir` columns (`cast-server/cast_server/db/schema.sql:1–14`). The "infer-or-prompt for project dir on first command invocation" gap is a separate, narrower behavior change scoped to the goal lifecycle, not a multi-tenant rework. **Explicitly out of scope for this plan** (see Out of scope).

cast-server architectural confirmation: single user-level daemon. DB at `~/.cast/diecast.db` (`config.py:16`), wrapper script pinned to `--project ${REPO_DIR}` regardless of cwd (`setup:179–183`), single bind. Setup-launches-once-and-leaves-it-running is the correct semantics; no per-project lifecycle.

**Naming convention (post-review, Decision #3):** This plan uses `CAST_HOST` for the *client-side connect target* (default `localhost`, used by skills/agents calling the server) and `CAST_BIND_HOST` for the *server-side bind address* (default `127.0.0.1`, used by uvicorn). The pre-existing `CAST_HOST` env var (server bind) was renamed to `CAST_BIND_HOST`; the new client-side var takes the former name to match conventional curl-style usage. `CAST_PORT` is shared by both sides.

**Backward compatibility (Decision #1):** This plan does not preserve any pre-change runtime state. Anyone with an old cast-server still running on :8000 from before this change will need to kill it manually (`lsof -ti:8000 | xargs kill`) before re-running `./setup`. CHANGELOG entry covers this; no auto-detect/auto-kill logic in setup.

## Recommended approach

Eight coordinated edits. Order below = order of execution.

---

### A. Establish the `CAST_HOST` / `CAST_PORT` seam (default port → 8005)

**Why first:** A and B (auto-launch) both need to agree on the new default. Doing the port shift first means the launch step in B uses the new value and the README in C documents one consistent number.

**Mechanical changes:**

1. **`bin/cast-server:19`** — change `${CAST_PORT:-8000}` to `${CAST_PORT:-8005}` and `${CAST_HOST:-127.0.0.1}` to `${CAST_BIND_HOST:-127.0.0.1}` (rename per Decision #3 — server-bind side becomes `CAST_BIND_HOST`).

2. **`cast-server/cast_server/config.py`** — add three constants:
   ```python
   DEFAULT_CAST_PORT = int(os.environ.get("CAST_PORT", "8005"))
   DEFAULT_CAST_HOST = os.environ.get("CAST_HOST", "localhost")            # client-side default
   DEFAULT_CAST_BIND_HOST = os.environ.get("CAST_BIND_HOST", "127.0.0.1")  # server-side bind default
   ```
   These are read by §A.4 (server-emitted curl) and §F (log path resolution).

3. **Markdown-aware sweep across the 30+ hardcoded sites** (Decision #5: bash blocks vs prose).

   A naive single-pass sed will mangle narrative prose where the bash substitution `${CAST_HOST:-localhost}:${CAST_PORT:-8005}` is meaningless. Implementation: a small Python script (`bin/sweep-port-refs.py`, ~30 lines) walks markdown files, identifies fenced bash blocks, and applies the right substitution per region:
   - **Inside ```bash / ```sh / inline `code` containing `curl` or `http://`:** replace `http://localhost:8000` → `http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}` (and same for `127.0.0.1`).
   - **Narrative prose elsewhere:** replace with the literal `http://localhost:8005` (and `http://127.0.0.1:8005`).

   Pre-flight `grep -rn '\(localhost\|127\.0\.0\.1\):8000' <DIECAST_ROOT>/` to enumerate the actual hits and verify ~30 matches.

   Targets (Decision #6: add cast-server/README.md, exclude tests/):
   - `<DIECAST_ROOT>/skills/claude-code/cast-*/**/*.md` (~13 hits in cast-child-delegation alone)
   - `<DIECAST_ROOT>/agents/cast-*/**/*.md`
   - `<DIECAST_ROOT>/cast-server/README.md` *(added per Decision #6 — env-var table at :23 + intro at :4)*
   - `<DIECAST_ROOT>/README.md`
   - `<DIECAST_ROOT>/docs/**/*.md`

   **Exclude:** `tests/` — `tests/test_cast_upgrade.sh:298` literal `localhost:8000` is intentional (mock-curl payload, not a real URL); changing it would alter test semantics.

   Setup reinstalls skills/agents into `~/.claude/` on every run (`step3_install_agents`, `step4_install_skills` at `setup:128–166`), so the in-repo edit propagates on next `./setup`.

4. **`cast_server/services/agent_service.py` — server-emitted curl** (Decision #2).

   Lines 889/915 emit curl as runtime prompt content sent to child agents — not just docstrings. Lines 992/1005 are docstring API references. The server knows its own bind, so emit literal URLs (no bash-substitution pattern needed):
   ```python
   from cast_server.config import DEFAULT_CAST_HOST, DEFAULT_CAST_PORT
   server_url = f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"
   # then use {server_url}/api/agents/... in the f-string
   ```
   *Why no bash-substitution pattern here:* skills/agents are user-configurable (the user might have `CAST_HOST=cloud.example.com` exported), but server-emitted prompts are *server-state-aware* — the server is *telling* the child where to call back, not asking the child to discover it. Two different patterns, each correct for its context.

5. **`~/.cast/config.yaml` schema** — add two keys to the `DEFAULTS` dict in `step6_write_config` at `setup:218–227` (Decision #7: host + port only, skip bind_host):
   ```python
   "host": "localhost",
   "port": 8005,
   ```
   Document in `docs/config.md`. The `bind_host` knob is intentionally omitted from config.yaml — it's an advanced override (env-var only via `CAST_BIND_HOST`); default loopback is right for ~99% of users. Existing values are preserved (the merger at `setup:236–252` already handles this).

**What this buys us:** every skill/agent now resolves `http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}` at bash-execution time. To run against a cloud server later: `export CAST_HOST=cast.example.com CAST_PORT=443` and every skill works unchanged. Same seam swap is the cloud-deploy story.

**Risk:** anyone with a private skill copy that hardcodes `:8000` won't be auto-updated. Mitigation: `setup` overwrites `~/.claude/skills/cast-*/` from the repo source; the existing `backup_if_exists` at `setup:159` preserves the prior copy under `~/.claude/.cast-bak-<ts>/` so the user can diff if they had local edits.

---

### B. `setup` — Step 8: launch server + open browser on first install

Insertion point: between `prune_old_backups` and `print_next_steps` at `setup:345–346`. Renames the run-counter from `Step X/7` → `Step X/8` everywhere (mechanical: 7 sed replacements across `setup:85, 93, 120, 130, 149, 170, 196, 296`).

**Skip conditions** (any one short-circuits the step, log "skipping launch: <reason>"):
- `--upgrade` (existing flag, `UPGRADE_MODE=1`) — upgrades shouldn't restart user processes
- `--dry-run` (existing, `DRY_RUN=1`)
- `--no-prompt` (existing, `NO_PROMPT=1`) — CI / non-interactive contract
- `${CI:-}` non-empty — defensive against shells that don't pass `--no-prompt`
- A server already responding on `${host}:${port}` — open browser only, don't double-launch

**Happy-path behavior** (after all skip checks evaluate, per Decision #11 — filesystem touched only on the happy path):

1. **Port pre-flight probe.** Before launch, check whether `${host}:${port}` is already bound:
   - If a cast-server is responding (per the existing already-running short-circuit): skip launch, set `LAUNCHED=1`, fall through to browser open.
   - If something else holds the port (`lsof -ti :${port}` returns a PID that isn't our `cast-server` cmd): abort the launch step with
     ```
     [cast] port ${port} in use by PID <pid> (<cmd>).
            set CAST_PORT=<n> ./setup, or stop the process and re-run.
            (skipping launch — install otherwise complete)
     ```
     `LAUNCHED=0`; setup still completes, `print_next_steps` takes the deferred branch.
   - If nothing answers: continue.
2. `mkdir -p ~/.cache/diecast` — *only on the happy path* (Decision #11); skip-path never touches the cache dir.
3. Detached background launch (Decision #4 — drop the no-op `disown`; Decision #13 — write to `bootstrap.log`, not `server.log`, so RotatingFileHandler in §F can own `server.log` without write-conflict):
   ```bash
   ( nohup "${HOME}/.local/bin/cast-server" >"${HOME}/.cache/diecast/bootstrap.log" 2>&1 & ) >/dev/null 2>&1
   ```
4. Poll readiness via bash `/dev/tcp/${host}/${port}`, **30× at 0.5s = 15s max** (Decision #10 — bumped from 5s; cold uvicorn import realistically takes 3–8s on slow disks). No curl dependency, native to bash.
5. **Terminal wire-up.** If `--no-prompt`/CI is *not* set, invoke `bin/cast-doctor --fix-terminal` (introduced by the terminal-defaults plan). This calls into `needs_first_run_setup()` and is a no-op when the user already has a configured terminal. Without this, a fresh box auto-launches the server but the first agent dispatch still fails on `ResolutionError`.
6. Open the browser to `http://${host}:${port}/`:
   - macOS: `open "${url}"`
   - Linux with `${DISPLAY:-}${WAYLAND_DISPLAY:-}` set and `xdg-open` available: `xdg-open "${url}" &`
   - Otherwise: log "no display detected — visit ${url} manually" and proceed
7. If the readiness poll never succeeds, log a warning with the path to `~/.cache/diecast/bootstrap.log` and continue — never fail setup over the launch step.

**Post-install PATH check** (runs unconditionally at end of step 8, before `print_next_steps`):

```bash
case ":${PATH}:" in
  *":${HOME}/.local/bin:"*) : ;;
  *) warn "cast-server installed to ~/.local/bin, which is not on your \$PATH.
           Add this to your shell rc (e.g. ~/.zshrc, ~/.bashrc):
             export PATH=\"\$HOME/.local/bin:\$PATH\"
           Then restart your shell or: source ~/.zshrc" ;;
esac
```

No automatic dotfile edits — user keeps control of their shell rc.

**`print_next_steps` rewrite** (`setup:325–334`). Two branches: "running" vs "deferred":

When launch succeeded:
```
[cast] Install complete. cast-server is running at http://localhost:8005
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
```

When launch was skipped:
```
[cast] Install complete. To start the server: cast-server

Next steps:
  1. /cast-init   — scaffold a new project (writes CLAUDE.md + cast-* dirs)
  2. /cast-runs   — open the dashboard once cast-server is up

Docs: docs/config.md (config keys) · docs/troubleshooting.md (recovery & FAQ)
```

The branch is selected by a single `LAUNCHED=0/1` shell var set inside `step8_launch_and_open_browser`.

---

### C. `README.md` — add a "Run the server" subsection

Insertion point: directly after the Quick Start fence at `README.md:62–64` ("That's the chain…"), before the `---` and `## What you get` heading at `:66–68`.

New content (~14 lines):

```markdown
### Run the server

`./setup` starts cast-server in the background and opens the dashboard on first
install. To start it again after a reboot or shell restart:

​```bash
cast-server                            # http://localhost:8005, on $PATH after ./setup
./bin/cast-server                      # equivalent, from a fresh clone
CAST_PORT=8080 cast-server             # custom port (8005 is the default)
CAST_BIND_HOST=0.0.0.0 cast-server     # server-side bind for LAN access
CAST_HOST=cast.example.com cast-server # client-side connect target (future cloud)
​```

cast-server is a single user-level daemon — one instance per machine, shared
across every project you cd into. State lives in `~/.cast/diecast.db`; logs at
`~/.cache/diecast/server.log` (bootstrap output at `bootstrap.log`).
`CAST_HOST` / `CAST_PORT` are the *client-side* connect target (used by skills
calling the server); `CAST_BIND_HOST` controls the *server-side* bind. Each
goal binds to one repo via its `external_project_dir` column.
```

Also update `README:55` install blurb to clarify "drops cast-* skills + agents into ~/.claude/, puts cast-server on your PATH, **and starts it on first install**."

---

### D. Extend `bin/cast-doctor` with the missing prerequisite checks

**Decision #12:** The original §D introduced a parallel "Step 0 preflight" that duplicated `bin/cast-doctor`'s existing checks (bash, uv, git, claude, write access). `setup:84–89` already invokes cast-doctor as `step1_doctor`. Adding a second preflight contradicts the cross-plan pattern set by the terminal-defaults plan's Decision `2026-04-30T20:34:00Z` ("extend `bin/cast-doctor`; no new Python CLI").

**Mechanical changes:**

1. Add to cast-doctor's RED list:
   - `python3` ≥ 3.11 (cast-server runtime requirement; check via `python3 --version`).
   - `tmux` (terminal multiplexer required by the dispatcher).
2. Add OS-aware install hints in the failure messages (cast-doctor already partially does this for bash):
   - macOS (`uname -s` = Darwin): `brew install python@3.11` / `brew install tmux`.
   - Linux: sniff `/etc/os-release` for `ID=` / `ID_LIKE=` to pick `apt install python3.11 tmux` vs `dnf install python3.11 tmux`. Generic fallback: "install <tool> using your package manager".
3. `step1_doctor` (existing in setup) continues to invoke cast-doctor — no new step needed.

The aborts-before-any-writes property (no partial-install state on missing-prereq) is preserved by `step1_doctor`'s existing `fail` on cast-doctor exit ≠ 0.

---

### E. Database migrations via Alembic

`~/.cast/diecast.db` persists across versions. Today there's no migration story — a release with schema drift fails at first DB access on upgrade.

**Mechanical changes:**

1. Add `alembic` to cast-server's dependencies in `pyproject.toml`.
2. Create `cast-server/alembic/` and `cast-server/alembic.ini` via `uv run alembic init alembic`. Configure `alembic.ini`'s `sqlalchemy.url` to read from `cast_server.config` (same DB path as the runtime).
3. **Hand-author the baseline migration** (Decision #14 — *not* `--autogenerate`). cast-server is SQL-first (zero SQLAlchemy ORM models, 106-line `schema.sql` with 6 tables + 14 indexes). Autogenerate would silently miss any non-trivial constructs (CHECK constraints, partial indexes, triggers) and isn't applicable without ORM models to introspect anyway. Baseline migration's `upgrade()` reads `cast-server/cast_server/db/schema.sql` and runs `op.execute()` on each statement — byte-exact match with what cast-server has shipped:
   ```python
   def upgrade():
       schema_sql = Path(__file__).parent.parent.parent / "cast_server" / "db" / "schema.sql"
       for stmt in schema_sql.read_text().split(";"):
           if stmt.strip():
               op.execute(stmt)

   def downgrade():
       # Baseline has no downgrade — drop the DB to undo.
       raise NotImplementedError("baseline cannot be downgraded; rm ~/.cast/diecast.db")
   ```
   Future migrations are hand-authored `op.execute()` calls (or autogen if ORM models are introduced later — see Out of scope).
4. **Run on `./setup`**, after step 5 (`step5_install_cast_server`) and before step 8 (launch):
   ```bash
   ( cd "${REPO_DIR}/cast-server" && uv run alembic upgrade head )
   ```
   On failure: abort setup with the alembic error verbatim. Migration failure must not be silently swallowed — broken DB state is worse than a halted install.
5. **Boot-time skip-if-stamped check** (Decision #15 — most boots are no-ops; only actual schema drift triggers the lock-holding upgrade). In `cast-server/cast_server/main.py`:
   ```python
   from alembic import command
   from alembic.config import Config
   from alembic.script import ScriptDirectory
   from alembic.runtime.migration import MigrationContext

   def _ensure_db_at_head():
       cfg = Config(str(CAST_ROOT / "alembic.ini"))
       script = ScriptDirectory.from_config(cfg)
       head = script.get_current_head()
       with engine.connect() as conn:
           current = MigrationContext.configure(conn).get_current_revision()
       if current != head:
           command.upgrade(cfg, "head")
   ```
   Called once at startup, before the FastAPI app accepts requests. Eliminates the always-paying-for-rare-case cost; bounds the SQLite write-lock acquisition to actual migrations. Race window between two concurrent starts is bounded — second one sees current=head and skips.

**Risk:** users who hand-edited `~/.cast/diecast.db` with `sqlite3` might have schema that conflicts with the baseline. Mitigation: the first release with Alembic also stamps existing DBs at the baseline revision via a one-time `alembic stamp head` if the `alembic_version` table is missing — wrapped in a try/except so missing-DB or empty-DB cases also work.

---

### F. Server log rotation

`nohup` redirect in §B writes to `~/.cache/diecast/bootstrap.log` (per Decision #13). Without rotation, a long-running auto-launched daemon hits multi-GB logs in weeks. RotatingFileHandler owns `~/.cache/diecast/server.log` for app/framework logs.

**Mechanical changes:**

1. In `cast-server/cast_server/config.py` (or wherever logging is initialized), configure Python's `logging` module with a `RotatingFileHandler`:
   ```python
   from logging.handlers import RotatingFileHandler

   LOG_DIR = Path.home() / ".cache" / "diecast"
   LOG_DIR.mkdir(parents=True, exist_ok=True)
   handler = RotatingFileHandler(
       LOG_DIR / "server.log",
       maxBytes=10 * 1024 * 1024,  # 10MB
       backupCount=5,
   )
   ```
2. Apply the handler to both the root logger and uvicorn's `uvicorn.error` / `uvicorn.access` loggers so framework logs also rotate.
3. **File ownership separation** (Decision #13 — eliminates the rotation-vs-file-redirect conflict from the original plan):
   - `bootstrap.log` — owned by `nohup` redirect in §B step 3. Captures uvicorn's pre-logging stdout/stderr (process-start errors before Python logging is configured).
   - `server.log` — owned by RotatingFileHandler. Captures all structured app + framework logs. Rotates without breakage because no other writer holds the file.

   Two distinct files for two distinct phases. Cross-platform identical behavior on macOS and Linux.

---

### G. Shellcheck in CI for `setup` and `bin/` bash scripts

The new launch step, port pre-flight probe, cast-doctor wire-up, PATH check, and existing renumber-the-step-counter sed are all bash with zero coverage.

**Mechanical changes:**

1. Add a `.github/workflows/shellcheck.yml` (or extend the existing CI workflow) with a **shebang-aware sweep** of `bin/*` (Decision #17):
   ```bash
   for f in setup bin/*; do
     [ -f "$f" ] || continue
     head -1 "$f" | grep -q 'bash' && shellcheck "$f"
   done
   ```
   Catches every current and future bash script in `bin/` without needing CI updates when new scripts land. Shellcheck is preinstalled on `ubuntu-latest` runners — zero install cost.
2. Fix the inevitable initial shellcheck violations in the affected scripts (likely a handful of `SC2086` unquoted-var and `SC2155` declare-and-assign). One-shot cleanup commit.

No bats, no integration smoke test of `./setup --dry-run`. The 20-scenario verification list remains the human gate at release time.

---

### H. Tighten user-facing surface — `cast-server` is the only CLI; everything else is `/cast-*`

**Decision #18:** During review the user asked "except for cast-server, there should be no other CLI commands; everything else including doctor should be /cast-doctor types." The codebase is already 90% there — `setup:170–190` (`step5_install_cast_server`) symlinks *only* `cast-server` into `~/.local/bin/`. The 12 other `bin/` scripts (`cast-doctor`, `cast-spec-checker`, `audit-interdependencies`, `check-doc-links`, `generate-skills`, `lint-anonymization`, `migrate-*.py`, `run-migrations.py`, `set-proactive-defaults.py`) are internal tooling that users never PATH-invoke. The one wart: `bin/cast-doctor:8–12` documents itself as user-runnable ("Run this … any time post-install to diagnose installation issues"), creating a half-position. §H closes the half-position by making `bin/cast-doctor` purely internal and adding `/cast-doctor` as the user-facing diagnostic surface.

**Mental model after §H:**
- **`cast-server`** — the only user-facing CLI binary; the daemon. On `$PATH`.
- **`/cast-*`** — every user-facing operation (init, runs, doctor, goals, tasks, spec-checker, etc.) is a Claude Code slash command/skill.
- **`bin/*` (excluding `cast-server`)** — internal tooling: setup-time helpers, CI/lint scripts, one-shot migrations. Not on `$PATH`. Documented as such.

**Mechanical changes:**

1. **`bin/cast-doctor:8–12`** — update header docstring. Remove the "Run this before ./setup, or any time post-install to diagnose installation issues" line. Replace with: "Internal: invoked by `setup`'s `step1_doctor` and CI. Post-install diagnosis happens via `/cast-doctor` from inside Claude Code." Keep the script fully functional — `step1_doctor` still calls it, and `/cast-doctor` shells out to it.

2. **`/cast-doctor` skill — new.** Scaffold at `agents/cast-doctor/cast-doctor.md` (canonical agent source) with `bin/generate-skills` producing `skills/claude-code/cast-doctor/SKILL.md` on next setup. Behavior:
   - **Primary path:** GET `http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/health` (new endpoint — see step 3 below). If the server is up, render its structured JSON output as a Claude-Code-friendly markdown summary.
   - **Fallback:** if the server is down or unreachable, the skill instructs Claude to shell out to `${REPO_DIR}/bin/cast-doctor --json` via the Bash tool and renders that output instead.
   - **Action surfacing:** if `cast-doctor` reports a configurable issue (no terminal, missing prereq with install hint), surface it via `cast-interactive-questions` so the user can fix it inline rather than copy-pasting commands.

3. **`/api/health` endpoint on cast-server — new.** Add a route at `cast-server/cast_server/routes/api_health.py` returning the same shape as `bin/cast-doctor --json`: `{"red": [...], "yellow": [...], "green": [...]}`. The handler reuses the prereq checks from cast-doctor wherever possible (a shared Python module if the cost is low, or a `subprocess.run(["bin/cast-doctor", "--json"])` for v1). This endpoint is also useful for §B step 4's readiness poll — a `/api/health` 200 is a stronger ready-signal than a TCP-only probe (see Out of scope's `/healthz` rejection — this supersedes it).

4. **Audit other `bin/` scripts for half-positions.** For each of the 12 internal scripts, verify the header docstring explicitly says "Internal use; not on user PATH" so future readers don't get confused:
   - `bin/cast-spec-checker` — there's already a `cast-spec-checker` agent in `agents/`; bin script becomes internal. If anyone today runs it from the repo, mark the docstring and point them at the slash command.
   - `bin/check-doc-links`, `bin/audit-interdependencies`, `bin/lint-anonymization` — internal CI; ensure docstrings say so.
   - `bin/generate-skills` — internal (called by setup); ensure docstring says so.
   - `bin/migrate-legacy-estimates.py`, `bin/migrate-next-steps-shape.py`, `bin/run-migrations.py` — internal one-shot data migrations; ensure docstrings say so. (Note: `bin/run-migrations.py` will likely be obsoleted by §E's Alembic — fold the deprecation note into its docstring.)
   - `bin/set-proactive-defaults.py` — internal; same.
   - `bin/_lib.sh` — sourced helper; not directly invoked. Already clear.

5. **`bin/README.md` — update.** Already exists; rewrite to make the user/internal split explicit. Top of file: "**User-facing:** only `cast-server` (symlinked to `~/.local/bin/cast-server` by `./setup`). All other entries are internal tooling — invoked by `setup`, CI, or one-shot migrations. Post-install user surface lives in `/cast-*` slash commands inside Claude Code."

6. **`README.md` — add the mental model.** In the "Run the server" subsection (§C), add a one-line postscript: "Only `cast-server` is on your `$PATH`. Every other Diecast operation is a `/cast-*` slash command inside Claude Code (run `/cast-doctor` to diagnose, `/cast-init` to scaffold, `/cast-runs` for the dashboard, etc.)."

**What this buys us:**
- Single mental model: cast-server (daemon) + /cast-* (slash commands).
- No drift between bin/cast-doctor and /cast-doctor (the slash command wraps the bin script via the new `/api/health` endpoint with a Bash-fallback).
- Discoverability via Claude Code's `/` autocomplete (already 50+ cast-* skills).
- Bootstrap chicken/egg solved: `bin/cast-doctor` *must* stay as a script because `step1_doctor` runs *before* Claude Code is verified working — but it's no longer documented as a user surface.
- Future ops are slash commands by default; no temptation to add another `bin/cast-thing` script.

**Risk:** users who today rely on `cd <DIECAST_ROOT> && bin/cast-doctor` from a shell will need to switch to `/cast-doctor` inside Claude Code. The bin script still works (we don't delete it), so the worst case is a confused user reading old docs. Mitigation: CHANGELOG entry plus the bin/README.md split.

**Why this beats a unified `cast` CLI:** ~6 file touches vs ~50–80 for the unified CLI. No PATH rename. Plays to Claude Code's strengths (rich .md docs, autocomplete, AskUserQuestion). The unified CLI remains a possible future direction if the slash-command surface ever grows unwieldy.

7. **Override the in-flight terminal-defaults plan's user-facing presentation** (Decision #19). Commit `28db472` already landed `bin/cast-doctor --fix-terminal` plus four sites that present it as the *primary user surface*. §H makes `/cast-doctor` the front door instead. The `--fix-terminal` flag itself stays — `setup` step 8 step 5 invokes it directly, and the `/cast-doctor` skill shells out to it via Bash when an unconfigured terminal is detected. Only the *discovery presentation* changes:

   - **`bin/cast-doctor:12`** (`--help` listing) — change the `--fix-terminal` line from "interactive first-run setup" to "internal: invoked by `setup` and the `/cast-doctor` skill; users should run `/cast-doctor` from inside Claude Code."
   - **`bin/cast-doctor:57`** (usage block within `print_help()`) — same wording shift.
   - **`bin/cast-doctor:224`** (yellow message for unsupported `$CAST_TERMINAL`) — change "Run `bin/cast-doctor --fix-terminal` to probe and configure interactively" to "Run `/cast-doctor` from inside Claude Code to probe and configure (or `bin/cast-doctor --fix-terminal` from a shell as fallback)".
   - **`bin/cast-doctor:241`** (yellow message for "no supported terminal found") — same wording shift.
   - **Terminal-defaults plan §2's `ResolutionError` improved-message text** (per `agents/_shared/terminal.py` and the terminal-defaults plan, lines 78–83) — change "fix: run `bin/cast-doctor --fix-terminal` to auto-detect and configure" to "fix: run `/cast-doctor` from inside Claude Code to auto-detect and configure". The terminal-defaults plan already shipped commit `28db472` for the alias/de-vendor/loud-failure work; the message text is part of the same workstream — overriding here keeps user-facing wording aligned with §H instead of letting the in-flight plan ship a now-obsolete primary surface.

   **What does NOT change in terminal-defaults:** §1 (intelligent auto-detect implementation), §3 (the `--fix-terminal` flag mechanism itself), `tests/test_cast_doctor.py` (still valid — tests an internal helper that setup uses), Verification #5 (`--fix-terminal` still auto-detects and persists; the test is shape-correct even though the user discovery path moved). The `agents/_shared/terminal.py` `_autodetect()` function and the `_config_default()` dual-key alias are unchanged.

---

## Files to modify

- `<DIECAST_ROOT>/bin/cast-server` — port default 8005; rename `${CAST_HOST:-127.0.0.1}` → `${CAST_BIND_HOST:-127.0.0.1}` (Decision #3)
- `<DIECAST_ROOT>/cast-server/cast_server/config.py` — add `DEFAULT_CAST_PORT` / `DEFAULT_CAST_HOST` / `DEFAULT_CAST_BIND_HOST` constants; configure `RotatingFileHandler` writing to `server.log` (§F)
- `<DIECAST_ROOT>/cast-server/cast_server/main.py` — `_ensure_db_at_head()` skip-if-stamped check (Decision #15); call before FastAPI accepts requests (§E)
- `<DIECAST_ROOT>/cast-server/cast_server/services/agent_service.py` — replace hardcoded `http://localhost:8000` at lines 889/915 (runtime prompt content) and 992/1005 (docstrings) with `f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"` from config constants (Decision #2)
- `<DIECAST_ROOT>/cast-server/cast_server/db/schema.sql` — read by the baseline migration (no edits to schema.sql itself; it remains source of truth)
- `<DIECAST_ROOT>/cast-server/pyproject.toml` — add `alembic` dependency (§E)
- `<DIECAST_ROOT>/cast-server/alembic/`, `cast-server/alembic.ini` — new migration tree with hand-authored baseline that `op.execute()`s `schema.sql` (§E, Decision #14)
- `<DIECAST_ROOT>/cast-server/README.md` — env-var table at :23 (CAST_HOST → CAST_BIND_HOST + new CAST_HOST entry; CAST_PORT default → 8005), intro at :4 (Decision #6)
- `<DIECAST_ROOT>/bin/cast-doctor` — add `python3 ≥3.11` and `tmux` to RED list with OS-aware install hints (Decision #12, §D)
- `<DIECAST_ROOT>/bin/sweep-port-refs.py` (new) — markdown-aware Python script that walks fenced bash blocks vs prose and applies the right substitution (Decision #5)
- `<DIECAST_ROOT>/setup` — port defaults in `step6_write_config`; new `step8_launch_and_open_browser` (port pre-flight + cast-doctor wire-up + PATH check, mkdir on happy path only); `alembic upgrade head` between step 5 and step 8; rewrite `print_next_steps`; renumber Step X/7 → X/8
- `<DIECAST_ROOT>/skills/claude-code/cast-*/**/*.md` — markdown-aware sweep (bash blocks → env-var pattern; prose → literal `localhost:8005`)
- `<DIECAST_ROOT>/agents/cast-*/**/*.md` — same sweep
- `<DIECAST_ROOT>/README.md` — add "Run the server" subsection, tweak install blurb
- `<DIECAST_ROOT>/docs/config.md` — add `host` / `port` keys to schema reference; document `CAST_HOST` (client) vs `CAST_BIND_HOST` (server) env-var asymmetry
- `<DIECAST_ROOT>/docs/**/*.md` — sweep narrative prose (delegation-pattern.md, troubleshooting.md, etc.)
- `<DIECAST_ROOT>/tests/test_migrations.py` (new) — round-trip test (`alembic upgrade head` from empty DB ↔ schema.sql) + idempotency test (re-running upgrade is a no-op) (Decision #16)
- `<DIECAST_ROOT>/.github/workflows/shellcheck.yml` (new) — shebang-aware sweep over `bin/*` (Decision #17, §G)
- `<DIECAST_ROOT>/bin/cast-doctor` — header docstring update at lines 8–12 (mark internal-only, point post-install diagnosis at `/cast-doctor`, Decision #18, §H step 1); presentation-shift at lines 12, 57, 224, 241 (point users at `/cast-doctor` rather than `bin/cast-doctor --fix-terminal`, Decision #19, §H step 7). Also gets the python3/tmux additions per Decision #12, §D.
- `<DIECAST_ROOT>/agents/_shared/terminal.py` — `ResolutionError` improved-message text shifts from "run `bin/cast-doctor --fix-terminal`" to "run `/cast-doctor` from inside Claude Code" (Decision #19, §H step 7). Overrides part of the in-flight terminal-defaults plan's §2.
- `<DIECAST_ROOT>/agents/cast-doctor/cast-doctor.md` (new) — canonical agent source for the `/cast-doctor` skill; bin/generate-skills produces the SKILL.md (Decision #18, §H step 2)
- `<DIECAST_ROOT>/cast-server/cast_server/routes/api_health.py` (new) — `/api/health` endpoint returning `{"red","yellow","green"}` shape; reuses cast-doctor's prereq checks (Decision #18, §H step 3). Also serves §B step 4's readiness probe.
- `<DIECAST_ROOT>/cast-server/cast_server/app.py` — register the new `api_health` router
- `<DIECAST_ROOT>/bin/cast-spec-checker`, `bin/check-doc-links`, `bin/audit-interdependencies`, `bin/lint-anonymization`, `bin/generate-skills`, `bin/migrate-legacy-estimates.py`, `bin/migrate-next-steps-shape.py`, `bin/run-migrations.py`, `bin/set-proactive-defaults.py` — header docstrings updated to "Internal use; not on user PATH" (Decision #18, §H step 4). `bin/run-migrations.py` also gets a deprecation note pointing at §E's Alembic.
- `<DIECAST_ROOT>/bin/README.md` — rewrite top section to split user-facing (`cast-server` only) vs internal (everything else) (Decision #18, §H step 5)
- `<DIECAST_ROOT>/README.md` — also gets the §H mental-model postscript in the "Run the server" subsection (Decision #18, §H step 6)
- `<DIECAST_ROOT>/CHANGELOG.md` — note the 8000 → 8005 default port shift, the env-var rename, the Alembic introduction, and the `/cast-doctor` slash command (with the bin/cast-doctor docstring change)

**Exclusions:**
- `tests/test_cast_upgrade.sh:298` — literal `:8000` is intentional (mock-curl payload, not a real URL); changing it would alter test semantics (Decision #6).

## Existing helpers to reuse

- `log` / `warn` / `fail` from `bin/_lib.sh:19–21` — use these for all printout, not raw `printf`/`echo`.
- `DRY_RUN` / `UPGRADE_MODE` / `NO_PROMPT` env vars are already exported at `setup:65`.
- `step1_doctor` (`setup:84–89`) already invokes `bin/cast-doctor`; §D extends cast-doctor in place rather than adding a parallel step.
- `step5_install_cast_server` (`setup:168–190`) already puts `cast-server` on `$PATH` — no new install path needed for the launch step.
- `step6_write_config` merger (`setup:236–252`) already handles "preserve user value, fill default for missing key" — extend its `DEFAULTS` dict, no new merger logic.
- `backup_if_exists` (`bin/_lib.sh:26–46`) already protects user customizations of `~/.claude/skills/cast-*/` files during the sweep-driven re-install.
- `needs_first_run_setup()` and `bin/cast-doctor --fix-terminal` from the terminal-defaults plan — §B step 5 calls `--fix-terminal` directly.

## Verification

1. **Fresh-install path:** in a throwaway dir, `rm -rf ~/.claude/agents/cast-* ~/.local/bin/cast-server ~/.cache/diecast`, then `./setup`. Expect: server bound on `:8005`, browser opens to `http://localhost:8005`, terminal returns to prompt with the new "Install complete. cast-server is running at …" message.
2. **Port-config seam:** `CAST_PORT=8090 CAST_BIND_HOST=0.0.0.0 ./setup` — server binds on `0.0.0.0:8090`, dashboard URL in printout reflects the override.
3. **Client-side override:** `CAST_HOST=cast.example.com cast-server` (manually invoked) — printout reflects the connect-target override.
4. **Upgrade path:** `./setup --upgrade` — must NOT relaunch the server; printed message says "To start the server: cast-server" with no "running at …" claim.
5. **CI/headless path:** `CI=1 ./setup --no-prompt` — no launch, no browser, no `~/.cache/diecast/` created.
6. **Already-running path:** start the server manually on `:8005`, then run `./setup`. Expect: skip launch, still open the browser, message reflects "running at …".
7. **No-display Linux path:** `unset DISPLAY WAYLAND_DISPLAY; ./setup` — server launches, browser open is skipped with a one-line "visit … manually" log.
8. **Hardcoded-port sweep verification:** after the sweep, `grep -rn '\(localhost\|127\.0\.0\.1\):8000' <DIECAST_ROOT>/ --include='*.md' --include='*.py' --include='*.sh' --exclude-dir=tests` should return zero hits (or only intentional CHANGELOG entries documenting the shift).
9. **Skill runtime resolution:** invoke a cast-* skill that hits the server (e.g. `/cast-runs`) — confirm the curl resolves `${CAST_HOST:-localhost}:${CAST_PORT:-8005}` correctly via bash and reaches the server.
10. **Sweep prose-vs-bash correctness:** spot-check `README.md:95` ("A local web UI at `http://localhost:8005`" — literal, not `${CAST_HOST:-...}`) and `cast-child-delegation/SKILL.md:30` (curl with the bash env-var pattern). Confirms the markdown-aware sweep applied the right substitution per region.
11. **Test suite:** `uv run pytest` continues to pass (109/109 baseline + 2 new `test_migrations.py` tests). The new step has no Python surface area; the existing `test_us14_next_steps_typed.py` checks shape, not literal text.
12. **README rendering:** open the file on github.com after push — confirm the new subsection lands between Quick Start and "What you get" without breaking the surrounding `---` rules.
13. **cast-doctor extended preflight (§D):** in a container without `tmux`, `bin/cast-doctor` reports RED on `tmux` with the OS-aware install hint; setup `step1_doctor` propagates the failure and aborts before any writes to `~/.claude/` or `~/.local/bin/`.
14. **cast-doctor python3 version (§D):** with `python3 --version` < 3.11, cast-doctor reports RED with a version-specific error.
15. **Port-conflict path (§B step 1):** `python3 -m http.server 8005 &` then `./setup` — launch step prints "port 8005 in use by PID <x> (python3) — set CAST_PORT=…", `LAUNCHED=0`, `print_next_steps` takes the deferred branch, install otherwise completes.
16. **Alembic baseline (§E):** with no `~/.cast/diecast.db`, `./setup` runs `alembic upgrade head`, DB is created at the baseline revision, `alembic_version` table populated. Re-run is idempotent (skip-if-stamped per Decision #15).
17. **Alembic upgrade-from-stamped (§E):** stamp an existing pre-Alembic DB to baseline manually, then run `./setup` — no migration ops, no errors. Simulates the first-release-with-Alembic case for existing users.
18. **Boot-time skip-if-stamped (§E, Decision #15):** start `cast-server` directly against a head-revision DB, observe in logs that `_ensure_db_at_head()` returns without calling `command.upgrade` (current == head). Then delete `alembic_version` from a healthy DB and restart — server detects missing version table, runs `upgrade head`, accepts requests.
19. **Migration tests (Decision #16):** `uv run pytest tests/test_migrations.py` — both round-trip and idempotency cases pass. Round-trip asserts byte-equivalent schema between alembic-built and schema.sql-built DBs (compare `sqlite3 .schema` output).
20. **Log rotation (§F):** generate >10MB of log output (e.g. tight loop hitting an endpoint) and confirm `~/.cache/diecast/server.log` rotates to `.1` through `.5`, then truncates oldest. Total disk footprint stays bounded. `bootstrap.log` is untouched (separate file, separate writer).
21. **Log file separation (Decision #13):** confirm `lsof ~/.cache/diecast/server.log` shows only the cast-server Python process; `lsof ~/.cache/diecast/bootstrap.log` shows the nohup redirect handle. Two writers, two files, no conflict.
22. **PATH check (§B post-install):** in a shell with `PATH` not containing `~/.local/bin`, `./setup` prints the warning with the exact `export` line; with `~/.local/bin` already on `PATH`, no warning.
23. **Terminal wire-up (§B step 5):** on a fresh box where `needs_first_run_setup()` returns True, `./setup` (interactive) invokes `bin/cast-doctor --fix-terminal`; with `--no-prompt`, the call is skipped. Subsequent `/cast-runs` dispatch reaches "ready" without a terminal `ResolutionError`.
24. **Shellcheck CI (§G):** the shebang-aware sweep `for f in setup bin/*; do head -1 "$f" | grep -q 'bash' && shellcheck "$f"; done` exits 0 on the merged branch; intentionally introduce an unquoted-var bug and confirm CI fails on it.
25. **`/cast-doctor` skill (§H):** with cast-server up, run `/cast-doctor` from inside Claude Code — confirm it hits `/api/health`, gets the structured response, and renders red/yellow/green findings as markdown. Confirm `cast-interactive-questions` fires for any actionable findings (e.g. unconfigured terminal → suggests `--fix-terminal`).
26. **`/cast-doctor` fallback (§H):** stop cast-server, run `/cast-doctor` again — confirm it falls back to shelling out to `${REPO_DIR}/bin/cast-doctor --json` and renders the same shape. The bin script is invoked but never advertised to the user.
27. **`bin/cast-doctor` doc-string update (§H step 1):** `head -15 bin/cast-doctor` shows the "Internal: invoked by `setup`'s `step1_doctor` and CI" wording; the old "Run this … any time post-install" line is gone.
28. **bin/ docstring sweep (§H step 4):** `for f in bin/cast-spec-checker bin/check-doc-links bin/audit-interdependencies bin/lint-anonymization bin/generate-skills bin/migrate-*.py bin/run-migrations.py bin/set-proactive-defaults.py; do head -10 "$f" | grep -q "Internal use" || echo "missing internal-use marker: $f"; done` returns no output.
29. **`bin/README.md` split (§H step 5):** opens with the "User-facing: only cast-server" framing; lists internal scripts in a separate subsection. Renders cleanly on github.com.
30. **`/api/health` endpoint (§H step 3):** `curl -s http://localhost:8005/api/health | jq` returns the cast-doctor JSON shape. The endpoint also satisfies §B step 4's readiness probe (a 200 response is a stronger ready-signal than a TCP-only probe).
31. **Terminal-defaults override — yellow-message wording (§H step 7):** trigger the unsupported-`$CAST_TERMINAL` path (`CAST_TERMINAL=nope bin/cast-doctor`) and confirm the yellow message points at `/cast-doctor`, not `bin/cast-doctor --fix-terminal`. Same for the no-supported-terminal path.
32. **Terminal-defaults override — `ResolutionError` message (§H step 7):** trigger the resolver with no env vars / no config, confirm the raised error's `fix:` line points at `/cast-doctor`. The terminal-defaults plan's `tests/test_b6_terminal_resolution.py` may have an assertion against the old wording — update that test to match the new text in the same PR (call out as a coordinated change in the PR description).

## Out of scope (deferred to dedicated plans)

- **Goal-to-project-dir prompt-or-infer behavior on first command invocation.** The schema already has `external_project_dir`; the gap is the lifecycle wiring (UI prompt, CLI infer + confirm, where to store the prompt-skip preference). Worth its own plan because it touches goal-creation flow, every cast-* skill that operates on a goal, and the dashboard.
- **Multi-tenant project routing.** Per the user's clarification (one goal = one repo), this isn't needed. Single global DB + per-goal project_dir is the model.
- **Cloud-server actual deployment.** This plan establishes the `CAST_HOST` / `CAST_PORT` seam; actual cloud deployment (auth, TLS, multi-user) is a separate effort.
- **Process supervision / auto-restart on crash** (systemd/launchd) — the user asked for "simple"; surviving a manual `kill -9` is not the goal.
- **A `cast-server stop` command or PID-file shutdown** — `lsof -ti:8005 | xargs kill` is fine for now.
- **Touching `/cast-init` to run the same launch+browser flow** — setup-only is what was requested.
- **Detection / auto-kill of an old cast-server still running on :8000.** Per Decision #1 (don't worry about backward compat), users with a pre-change daemon kill it manually before re-running setup. CHANGELOG entry covers this.
- **`/healthz` HTTP readiness endpoint.** Considered for §B step 4 (TCP probe could miss a bound-but-500-ing server). Rejected: a bound-but-broken cast-server is rare on first install; TCP-only is sufficient. Revisit if real users hit it.
- **Bats / integration smoke tests for `setup`** (running `./setup --dry-run --no-prompt` and asserting log lines). Rejected: shellcheck (§G) plus the manual verification list catches the realistic class of bugs at near-zero maintenance cost.
- **Auto-appending `export PATH=~/.local/bin:$PATH` to the user's shell rc.** Rejected: writing to dotfiles without explicit consent is intrusive and surprises users with managed dotfiles (chezmoi, stow, nix). The §B PATH-check warning gives the user a copy-pasteable line instead.
- **Unified `cast` CLI (`cast server`, `cast doctor`, `cast init`, etc.).** User considered this during review and chose §H's slash-command-only approach instead — fewer file touches (~6 vs ~50–80), no PATH rename, leverages existing `/cast-*` skill surface and Claude Code's autocomplete. The unified CLI remains a possible future direction if the slash-command surface ever grows unwieldy or if standalone-shell usage outside Claude Code becomes a real need. **Superseded by §H for now.**
- **Moving internal `bin/` scripts to `scripts/`.** Considered alongside §H. Rejected for v1: the `bin/` location is fine *with* the docstring updates from §H step 4 making the internal/external split explicit. Moving them would break every `setup`/CI invocation that already references `bin/...`. Revisit if `bin/` ever grows past ~20 entries.
- **SQLAlchemy ORM models for cast-server's data layer.** Considered for #14's alembic baseline approach. Not needed; SQL-first codebase, schema.sql is simple and readable. Adopting ORM would be a larger refactor with no immediate payoff.
- **Pre-1.0 setup-time notice for the 8000 → 8005 port shift** (auto-preserve old port via config merge). Rejected: pre-1.0, no users to migrate beyond the CHANGELOG note.

---

## Decisions

- **2026-04-30T21:30:00Z — On the upgrade race (old :8000 daemon + new :8005 daemon sharing one DB), what should the launch step do?** — Decision: Do nothing; document in CHANGELOG telling users to kill any old daemon. Rationale: User directive 'don't worry about backward compatibility' makes auto-kill detection over-engineering.
- **2026-04-30T21:31:00Z — How should agent_service.py:889/915 (curl emitted as runtime prompt content) handle the URL?** — Decision: Server emits literal URL from its own DEFAULT_CAST_HOST/DEFAULT_CAST_PORT constants; skills keep bash env-var substitution pattern. Rationale: Server is telling the child where to call back, not asking it to discover; user-configurable bash pattern only makes sense in user-facing skill markdown.
- **2026-04-30T21:32:00Z — How to name the client-side connect target env var vs the server-side bind env var?** — Decision: Rename existing CAST_HOST → CAST_BIND_HOST (server bind); use CAST_HOST for the new client-side var. Rationale: CAST_HOST matches conventional curl-style usage; CAST_BIND_HOST is unambiguous about server-side semantics.
- **2026-04-30T21:33:00Z — How to detach the background-launched cast-server in step 8?** — Decision: `( nohup ... & ) >/dev/null 2>&1` — drop the disown. Rationale: disown is a no-op inside a dying subshell; nohup + & inside the subshell already detaches correctly. Removing dead code clarifies intent.
- **2026-04-30T21:34:00Z — How to scope the sed sweep so it doesn't mangle narrative prose with bash substitution syntax?** — Decision: Two-pass markdown-aware sweep via a small Python script (`bin/sweep-port-refs.py`); bash blocks get env-var pattern, prose gets literal `http://localhost:8005`. Rationale: `${CAST_HOST:-localhost}:${CAST_PORT:-8005}` in prose is meaningless; the sweep needs to be context-aware.
- **2026-04-30T21:35:00Z — Targets to add to the sweep / exclude from the sweep?** — Decision: Add `cast-server/README.md` (was missing); exclude `tests/` entirely (`test_cast_upgrade.sh:298` literal is intentional mock payload). Rationale: cast-server/README.md documents the env vars and default port — must reflect new values; tests/ has different correctness semantics.
- **2026-04-30T21:36:00Z — Which keys should ~/.cast/config.yaml expose for the new host/port settings?** — Decision: `host` + `port` only; skip `bind_host`. Rationale: bind_host is an advanced override needed by ~1% of users; keeping it env-var-only avoids config bloat.
- **2026-04-30T21:37:00Z — Add automated tests for the new step8_launch_and_open_browser behavior?** — Decision: No new tests; rely on the plan's manual verification matrix. Rationale: launch step is bash glue around well-tested primitives; full coverage isn't worth the test infra cost for a one-time setup-time path.
- **2026-04-30T21:38:00Z — Add a round-trip test for the new config.yaml keys?** — Decision: No. Rationale: Consistent with the launch-step decision — defer to manual verification.
- **2026-04-30T21:39:00Z — Increase the readiness-poll timeout?** — Decision: Bump from 10×0.5s = 5s to 30×0.5s = 15s. Rationale: cold uvicorn import realistically takes 3–8s on slow disks; 5s would time out for some users on first install.
- **2026-04-30T21:40:00Z — Where to put the `mkdir -p ~/.cache/diecast` call relative to skip checks?** — Decision: Inside the happy path, after all skip conditions evaluate. Rationale: prevents headless/CI machines from accumulating empty cache dirs they never use.
- **2026-04-30T21:41:00Z — §D added a parallel preflight that duplicates `bin/cast-doctor`. Resolution?** — Decision: Drop §D; extend `bin/cast-doctor` with python3 ≥ 3.11 and tmux checks plus OS-aware install hints. Rationale: cast-doctor already exists and is invoked at step1_doctor; cross-plan consistency with terminal-defaults plan's Decision `2026-04-30T20:34:00Z` ("extend cast-doctor; no new CLI"); single source of truth for prerequisite checks.
- **2026-04-30T21:42:00Z — Log file conflict: §B nohup writes to server.log AND §F RotatingFileHandler writes to server.log. Two writers on one file. Fix?** — Decision: nohup writes to `bootstrap.log` (uvicorn pre-logging stdout/stderr); RotatingFileHandler owns `server.log` (structured app + framework logs). Two distinct files, two distinct phases, no rotation breakage.
- **2026-04-30T21:43:00Z — Alembic baseline approach: autogenerate vs hand-author from schema.sql?** — Decision: Hand-author baseline as `op.execute()` of `schema.sql` contents. Rationale: cast-server is SQL-first (zero SQLAlchemy ORM models); autogenerate is inapplicable without models and would silently miss non-trivial constructs even if a placeholder model layer were added. schema.sql is already simple and readable; preserving it as source of truth eliminates drift risk.
- **2026-04-30T21:44:00Z — Boot-time alembic upgrade is synchronous on every cast-server start. Optimize?** — Decision: Skip-if-stamped — read alembic_version, only call `command.upgrade` if revision != head. Rationale: most boots are no-ops (DB at head); the SELECT is cheap; only actual schema drift triggers the lock-holding upgrade. Bounds the concurrent-start race to "second one sees head, skips".
- **2026-04-30T21:45:00Z — Add automated migration tests?** — Decision: Add `tests/test_migrations.py` with round-trip and idempotency cases. Rationale: schema drift is silent — a missing column in a migration won't surface until someone hits the broken endpoint; ~50 lines of pytest catches the silent-drift class of regressions for the entire life of the project.
- **2026-04-30T21:46:00Z — Shellcheck CI target list — explicit names or sweep?** — Decision: Shebang-aware sweep over `bin/*` (`for f in setup bin/*; do head -1 "$f" | grep -q 'bash' && shellcheck "$f"; done`). Rationale: future-proof against new bash scripts in `bin/`; zero CI maintenance when scripts are added/removed; flat surface coverage.
- **2026-04-30T21:50:00Z — Should we replace the multi-`bin/` surface with a unified `cast` CLI, or tighten the user-facing surface to "only `cast-server` is on PATH; everything else is `/cast-*` slash commands"?** — Decision: §H — slash-command-only. `cast-server` stays as the sole user-facing binary; `bin/cast-doctor` becomes internal-only with a new `/cast-doctor` skill as the user surface (backed by a new `/api/health` endpoint with a Bash-fallback to the bin script for when the server is down); all other `bin/` scripts get docstring updates explicitly marking them internal. Rationale: codebase is already 90% there (only `cast-server` is symlinked into `~/.local/bin/`); ~6 file touches vs ~50–80 for a unified CLI; no PATH rename headache; plays to Claude Code's strengths (rich .md docs, autocomplete, AskUserQuestion); bootstrap chicken/egg solved by keeping `bin/cast-doctor` callable from `step1_doctor` before any Claude session exists. Unified `cast` CLI remains a possible future direction; superseded for v1.
- **2026-04-30T21:55:00Z — Conflict with the in-flight terminal-defaults plan (commit `28db472` already landed): that plan presents `bin/cast-doctor --fix-terminal` as the primary user surface for terminal mis-configuration. §H wants `/cast-doctor` to be the front door. Override?** — Decision: Yes, override. Add §H step 7 to this plan that explicitly retargets the four user-facing presentation sites in `bin/cast-doctor` (lines 12, 57, 224, 241) plus the `ResolutionError` improved-message text in `agents/_shared/terminal.py` from "`bin/cast-doctor --fix-terminal`" → "`/cast-doctor` from inside Claude Code". The flag itself stays — `setup` step 8 step 5 calls it; the `/cast-doctor` skill shells out to it via Bash. Only the *discovery* surface moves. Rationale: user explicitly authorized the override ("totally okay to override that change right away"); cleanest mental model = single front door; `--fix-terminal` becomes an internal helper that happens to be testable from a shell; terminal-defaults plan's auto-detect implementation (§1), flag mechanism (§3), and tests are unaffected — only its user-discovery wording shifts. Coordinated change: terminal-defaults' `tests/test_b6_terminal_resolution.py` may pin the old `ResolutionError` text and need updating in the same PR.
