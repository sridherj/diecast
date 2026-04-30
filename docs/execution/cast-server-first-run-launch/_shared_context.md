# Shared Context: Cast-Server First-Run Launch

## Source Documents
- Plan: `/data/workspace/diecast/docs/plan/2026-04-30-cast-server-first-run-launch.collab.md`
- Writeup: (none — plan is self-contained, with full Decisions block)

## Project Background

A fresh `./setup` for Diecast finishes installing but never tells the user the server exists or starts it. Three friction points surfaced together:

1. **README has no "how to start the server" section** — the binary `cast-server` is mentioned but never invoked.
2. **`./setup` doesn't launch anything** — user must learn the daemon exists, the command, and run it manually before `/cast-runs` works.
3. **Port `8000` is hardcoded in 30+ places** and collides with every other dev tool.

This plan also folds in five hardening items that share the same "fresh `./setup` Just Works end-to-end" outcome: Alembic migrations, log rotation, an extended `bin/cast-doctor` preflight, a port-conflict pre-flight, terminal wire-up, shellcheck CI, and tightening the user-facing surface so `cast-server` is the only CLI on `$PATH` (everything else is a `/cast-*` slash command, including a new `/cast-doctor`).

## Codebase Conventions

- **`bin/_lib.sh`** provides `log` / `warn` / `fail` / `backup_if_exists` / `prune_old_backups` (lines 19–46). Always use these, never raw `printf`/`echo`.
- **`setup`** is a numbered-step bash driver (`step1_doctor` → `step7_print_next_steps`); each step is a function, dispatched by `main` at the bottom. New steps must respect existing flag conventions: `DRY_RUN`, `UPGRADE_MODE`, `NO_PROMPT`, `${CI:-}`.
- **Skills/agents are reinstalled into `~/.claude/`** on every `./setup` run (`step3_install_agents`, `step4_install_skills` at `setup:128–166`). In-repo source-of-truth edits propagate on next setup. `backup_if_exists` (`bin/_lib.sh:26–46`) snapshots prior copies under `~/.claude/.cast-bak-<ts>/`.
- **`cast-server`** is a single user-level daemon — one instance per machine, shared across every project. State at `~/.cast/diecast.db`. Wrapper at `bin/cast-server` (line 19 reads `CAST_PORT` / `CAST_BIND_HOST`).
- **Schema-first DB**: zero SQLAlchemy ORM models. `cast-server/cast_server/db/schema.sql` (~106 lines, 6 tables, 14 indexes) is the source of truth. Alembic baseline runs `op.execute()` over `schema.sql` rather than autogenerate.
- **`agents/<name>/<name>.md`** is canonical agent source; `bin/generate-skills` produces matching `skills/claude-code/<name>/SKILL.md` on each setup run. Edit the agent `.md`, never the SKILL.md directly.
- **`docs/specs/`** holds Spec-Aligned Verification (SAV) docs. Sub-phases that touch `linked_files` from a spec must verify that spec's behaviors are preserved; see "Relevant Specs" below.

## Key File Paths

| File | Role |
|------|------|
| `bin/cast-server` | Wrapper script symlinked into `~/.local/bin`; reads `CAST_PORT` / `CAST_BIND_HOST` env vars. |
| `bin/cast-doctor` | Pre-install + post-install diagnostics; invoked by `setup`'s `step1_doctor`. After §H, becomes internal-only with `/cast-doctor` skill as the user front door. |
| `bin/_lib.sh` | Shared bash helpers: `log` / `warn` / `fail` / `backup_if_exists` / `prune_old_backups`. |
| `setup` | Top-level installer; numbered steps; calls all `bin/*` helpers. |
| `cast-server/cast_server/config.py` | Runtime config + path constants. New: `DEFAULT_CAST_HOST` / `DEFAULT_CAST_PORT` / `DEFAULT_CAST_BIND_HOST`; `RotatingFileHandler` for `server.log`. |
| `cast-server/cast_server/main.py` | FastAPI app entry; new: `_ensure_db_at_head()` boot-time migration check. |
| `cast-server/cast_server/services/agent_service.py` | Lines 889/915 emit curl as runtime prompt content (server-side); 992/1005 are docstrings. Both replaced with `f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"`. |
| `cast-server/cast_server/db/schema.sql` | SQL source of truth. Read verbatim by Alembic baseline migration; never edited. |
| `cast-server/alembic/`, `cast-server/alembic.ini` | New (sp3). Migration tree with hand-authored baseline. |
| `cast-server/pyproject.toml` | New `alembic` dependency (sp3). |
| `cast-server/cast_server/routes/api_health.py` | New (sp6). `/api/health` endpoint returning `{"red","yellow","green"}`. |
| `cast-server/cast_server/app.py` | Registers route modules; gets the new `api_health` router (sp6). |
| `cast-server/README.md` | Env-var table at `:23`, intro at `:4`. Swept for port/host literals (sp1). |
| `agents/_shared/terminal.py` | `ResolutionError.improved_message()` text shifts to `/cast-doctor` (sp6). |
| `agents/cast-doctor/cast-doctor.md` | New (sp6). Canonical agent source for the `/cast-doctor` skill. |
| `bin/sweep-port-refs.py` | New (sp1). Markdown-aware Python script that distinguishes fenced bash blocks from prose. |
| `tests/test_migrations.py` | New (sp3). Round-trip + idempotency tests. |
| `tests/test_cast_upgrade.sh:298` | EXCLUDED from sweep — literal `:8000` is intentional mock-curl payload. |
| `.github/workflows/shellcheck.yml` | New (sp5). Shebang-aware sweep over `setup` + `bin/*`. |

## Data Schemas & Contracts

### Env-Var Naming (Decision #3 — final)

| Var | Side | Default | Used by |
|-----|------|---------|---------|
| `CAST_HOST` | client (connect target) | `localhost` | skills, agents, server-emitted prompt URLs |
| `CAST_BIND_HOST` | server (uvicorn bind) | `127.0.0.1` | `bin/cast-server`, uvicorn |
| `CAST_PORT` | both sides | `8005` | everywhere |

The pre-existing `CAST_HOST` (server bind) is **renamed** to `CAST_BIND_HOST`. The new client-side var takes the freed name.

### Markdown Sweep Rules (Decision #5)

The `bin/sweep-port-refs.py` walker distinguishes:

- **Inside fenced bash/sh blocks or inline `code` containing `curl`/`http://`:**
  - `http://localhost:8000` → `http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}`
  - `http://127.0.0.1:8000` → `http://${CAST_BIND_HOST:-127.0.0.1}:${CAST_PORT:-8005}`
- **Narrative prose elsewhere:**
  - `http://localhost:8000` → `http://localhost:8005` (literal)
  - `http://127.0.0.1:8000` → `http://127.0.0.1:8005` (literal)

### Server-Emitted Prompt URLs (Decision #2)

`cast_server/services/agent_service.py:889/915/992/1005` use literal URLs from `DEFAULT_CAST_HOST` / `DEFAULT_CAST_PORT` constants — *not* the bash-substitution pattern. The server is *telling* the child where to call back; no env-var indirection needed.

### Alembic Baseline (Decision #14)

```python
def upgrade():
    schema_sql = Path(__file__).parent.parent.parent / "cast_server" / "db" / "schema.sql"
    for stmt in schema_sql.read_text().split(";"):
        if stmt.strip():
            op.execute(stmt)

def downgrade():
    raise NotImplementedError("baseline cannot be downgraded; rm ~/.cast/diecast.db")
```

Not autogenerated — there are no ORM models to introspect.

### Boot-Time Migration Check (Decision #15)

```python
def _ensure_db_at_head():
    cfg = Config(str(CAST_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    with engine.connect() as conn:
        current = MigrationContext.configure(conn).get_current_revision()
    if current != head:
        command.upgrade(cfg, "head")
```

Called once at startup, before FastAPI accepts requests. Skip-if-stamped is the common case; only schema drift triggers the lock.

### Log File Ownership (Decision #13)

| File | Owner | Format | Rotation |
|------|-------|--------|----------|
| `~/.cache/diecast/bootstrap.log` | `nohup` redirect (sp8 step 3) | raw stdout/stderr | none |
| `~/.cache/diecast/server.log` | `RotatingFileHandler` (sp4) | structured Python logging | 10 MB × 5 backups |

Two distinct files for two distinct phases. No write-conflict.

### `~/.cast/config.yaml` New Keys (Decision #7)

```yaml
host: localhost   # client-side connect target
port: 8005        # shared
# bind_host is deliberately omitted — env-var-only via CAST_BIND_HOST
```

## Pre-Existing Decisions

(Verbatim from the plan's Decisions block, dated 2026-04-30T21:30Z–21:55Z. Read the source plan for full rationale; sub-phases reference these by `Decision #N`.)

1. **#1** — Don't auto-detect/auto-kill an old `:8000` daemon; CHANGELOG note covers it.
2. **#2** — `agent_service.py` server-emitted URLs use literal `f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"`; user-facing skill markdown keeps the bash env-var pattern.
3. **#3** — Rename existing `CAST_HOST` → `CAST_BIND_HOST` (server); new `CAST_HOST` is client-side.
4. **#4** — Drop the no-op `disown`; `( nohup … & ) >/dev/null 2>&1` already detaches.
5. **#5** — Two-pass markdown-aware sweep via `bin/sweep-port-refs.py`.
6. **#6** — Add `cast-server/README.md` to sweep targets; exclude `tests/`.
7. **#7** — `host` + `port` only in config.yaml; skip `bind_host`.
8. **#8 / #9** — No new automated tests for the launch step or config.yaml round-trip; rely on manual verification matrix.
9. **#10** — Bump readiness poll from 10×0.5s = 5s to **30×0.5s = 15s**.
10. **#11** — `mkdir -p ~/.cache/diecast` only on the happy path, after all skip checks.
11. **#12** — Drop the original §D's parallel preflight; extend `bin/cast-doctor` instead (cross-plan consistency with terminal-defaults' Decision `2026-04-30T20:34:00Z`).
12. **#13** — `bootstrap.log` (nohup) vs `server.log` (RotatingFileHandler). Two files, two writers.
13. **#14** — Alembic baseline is hand-authored `op.execute()` of `schema.sql`; not autogen.
14. **#15** — `_ensure_db_at_head()` skip-if-stamped check at boot.
15. **#16** — Add `tests/test_migrations.py` (round-trip + idempotency).
16. **#17** — Shebang-aware shellcheck sweep over `setup` + `bin/*`.
17. **#18** — `cast-server` is the only user-facing CLI; `/cast-*` covers everything else; new `/cast-doctor` skill backed by `/api/health` with Bash-fallback to `bin/cast-doctor --json`.
18. **#19** — Override the in-flight terminal-defaults plan's user-facing presentation: four sites in `bin/cast-doctor` + `ResolutionError` text now point at `/cast-doctor` instead of `bin/cast-doctor --fix-terminal`. The flag itself stays.

## Relevant Specs

Spec coverage check for files modified by this plan:

| Spec | Linked files overlap | Sub-phase(s) |
|------|---------------------|---------------|
| `docs/specs/cast-delegation-contract.collab.md` | `cast_server/services/agent_service.py` (lines 889/915 emit dispatch prompts) | sp1 |
| (other specs) | None of the targeted files appear in another spec's `linked_files`. |

If a sub-phase modifies `agent_service.py`, read `docs/specs/cast-delegation-contract.collab.md` and verify that the URL change preserves SAV behaviors (specifically: child agents must still receive a callable HTTP base for `/api/agents/...`). The change is functionally equivalent — only the constant source moves from a hardcoded literal to `DEFAULT_CAST_HOST`/`DEFAULT_CAST_PORT`.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 — Port seam (§A) | Sub-phase | — | sp4, sp6, sp7, sp8 | sp2, sp3, sp5 |
| sp2 — Doctor preflight (§D) | Sub-phase | — | sp6, sp8 | sp1, sp3, sp5 |
| sp3 — Alembic migrations (§E) | Sub-phase | — | sp8 | sp1, sp2, sp5 |
| sp4 — Log rotation (§F) | Sub-phase | sp1 | sp8 | sp6, sp7 |
| sp5 — Shellcheck CI (§G) | Sub-phase | — | (none) | sp1, sp2, sp3, sp4, sp6, sp7, sp8 |
| sp6 — `/cast-doctor` skill + bin docstrings (§H) | Sub-phase | sp1, sp2 | sp8 | sp4, sp7 |
| sp7 — README run-the-server (§C + §H step 6) | Sub-phase | sp1 | (none) | sp4, sp6 |
| sp8 — Setup launch step (§B) | Sub-phase | sp1, sp2, sp3, sp4, sp6 | (none) | sp5, sp7 |

No gates. No skip-conditional sub-phases.
