# Sub-phase 1: Port Seam — `CAST_HOST` / `CAST_PORT` / `CAST_BIND_HOST`

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Establish a single env-var seam (`CAST_HOST` client / `CAST_BIND_HOST` server / shared `CAST_PORT`) that future cloud deployments flip with no skill edits, and shift the in-repo default port from the high-collision `8000` to `8005`. Everything downstream (auto-launch, README, cast-doctor preflight) assumes this seam exists, so this sub-phase runs first.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** Pre-change tree at HEAD. `bin/cast-server:19` reads `${CAST_PORT:-8000}` and `${CAST_HOST:-127.0.0.1}`; ~30 markdown files hardcode `localhost:8000` / `127.0.0.1:8000`.

## Scope

**In scope:**
- `bin/cast-server`: rename env var, change default port.
- `cast-server/cast_server/config.py`: add three `DEFAULT_*` constants.
- `cast-server/cast_server/services/agent_service.py`: replace four hardcoded URLs (lines 889/915/992/1005) with f-strings using the new constants (Decision #2).
- New `bin/sweep-port-refs.py`: ~30-line markdown-aware Python walker.
- Run the sweep across the targets listed below (Decision #6).
- `setup`'s `step6_write_config` `DEFAULTS` dict: add `host` / `port` keys (Decision #7).
- `docs/config.md`: document the new keys + env-var asymmetry.
- `cast-server/README.md`: env-var table at `:23` and intro at `:4` (already covered by the sweep).
- `CHANGELOG.md`: record port shift + env-var rename.

**Out of scope (do NOT do these):**
- Server-launch logic, port pre-flight probe, browser open — sp8.
- `RotatingFileHandler` config in `config.py` — sp4.
- README "Run the server" subsection — sp7.
- Any `bin/cast-doctor` edit — sp2 / sp6.
- Alembic anything — sp3.
- Editing `tests/test_cast_upgrade.sh:298` — explicitly excluded.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `bin/cast-server` | Modify | Line 19 reads `${CAST_PORT:-8000}` and `${CAST_HOST:-127.0.0.1}`. |
| `cast-server/cast_server/config.py` | Modify | No `DEFAULT_CAST_*` constants exist. |
| `cast-server/cast_server/services/agent_service.py` | Modify | Hardcoded `http://localhost:8000` at 889/915 (runtime prompts) and 992/1005 (docstrings). |
| `bin/sweep-port-refs.py` | Create | New Python walker. |
| `setup` | Modify (DEFAULTS only) | `step6_write_config` at `setup:218–227` lacks `host`/`port` keys. |
| `docs/config.md` | Modify | No host/port entries. |
| `cast-server/README.md` | Modify (via sweep) | `:4` intro + `:23` env-var table reflect old port. |
| Sweep targets (markdown) | Modify (via sweep) | See "Sweep targets" below. |
| `CHANGELOG.md` | Modify | No entry yet. |

## Detailed Steps

### Step 1.1: Edit `bin/cast-server` line 19

Change:

```bash
exec uvicorn cast_server.main:app --host "${CAST_HOST:-127.0.0.1}" --port "${CAST_PORT:-8000}"
```

to:

```bash
exec uvicorn cast_server.main:app --host "${CAST_BIND_HOST:-127.0.0.1}" --port "${CAST_PORT:-8005}"
```

Per Decision #3 — server-bind side becomes `CAST_BIND_HOST`; the freed `CAST_HOST` name is now client-side only.

### Step 1.2: Add constants to `cast-server/cast_server/config.py`

Find a sensible location near other env-driven settings and insert:

```python
DEFAULT_CAST_PORT = int(os.environ.get("CAST_PORT", "8005"))
DEFAULT_CAST_HOST = os.environ.get("CAST_HOST", "localhost")            # client-side default
DEFAULT_CAST_BIND_HOST = os.environ.get("CAST_BIND_HOST", "127.0.0.1")  # server-side bind default
```

These are read by step 1.3 and by sp4's RotatingFileHandler path resolution (don't preempt sp4's edits — only the constants here).

### Step 1.3: Replace hardcoded URLs in `cast-server/cast_server/services/agent_service.py`

Lines 889/915 are runtime prompt content; 992/1005 are docstrings. **Both** use literal URLs (Decision #2 — server is *telling* the child where to call back, no env-var indirection). At the top of the file, add the import; at each of the four sites, replace `http://localhost:8000` with `{server_url}` derived once:

```python
from cast_server.config import DEFAULT_CAST_HOST, DEFAULT_CAST_PORT
server_url = f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"
# ... use {server_url}/api/agents/... in the surrounding f-strings
```

If `agent_service.py` already imports from `cast_server.config`, extend the import — don't duplicate.

**Spec check:** `docs/specs/cast-delegation-contract.collab.md` lists `agent_service.py` in `linked_files`. Read that spec; verify SAV behaviors that mention "child agents must reach `/api/agents/...`" are unchanged. The URL substitution is functionally equivalent — only the constant source moves.

### Step 1.4: Author `bin/sweep-port-refs.py`

A ~30-line Python script. Behavior:

- Argparse: `bin/sweep-port-refs.py [--check | --apply] PATH...`
- For each markdown file, parse line-by-line, tracking fenced-block state (entered on ```` ```bash ```` / ```` ```sh ```` / ```` ```shell ````, exited on ```` ``` ````).
- **Inside a bash block, OR inside an inline backtick span containing `curl` or `http://`:**
  - `http://localhost:8000` → `http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}`
  - `http://127.0.0.1:8000` → `http://${CAST_BIND_HOST:-127.0.0.1}:${CAST_PORT:-8005}`
- **Otherwise (narrative prose):**
  - `http://localhost:8000` → `http://localhost:8005`
  - `http://127.0.0.1:8000` → `http://127.0.0.1:8005`
- `--check` exits non-zero if any change would be made (CI-friendly); `--apply` writes in place.
- Report files modified to stdout.

Header docstring should say "Internal use; not on user PATH. Markdown-aware sweep for port/host literals." (Aligns with sp6's bin/ docstring sweep — sp1 sets the precedent.)

### Step 1.5: Pre-flight `grep` to enumerate hits

```bash
grep -rn '\(localhost\|127\.0\.0\.1\):8000' <DIECAST_ROOT>/ \
  --include='*.md' --include='*.py' --include='*.sh' \
  --exclude-dir=tests --exclude-dir=.git --exclude-dir=node_modules
```

Verify ~30 hits and that `tests/test_cast_upgrade.sh:298` is excluded by `--exclude-dir=tests`.

### Step 1.6: Run the sweep

Targets (Decision #6):

```bash
python3 bin/sweep-port-refs.py --apply \
  <DIECAST_ROOT>/skills/claude-code/cast-* \
  <DIECAST_ROOT>/agents/cast-* \
  <DIECAST_ROOT>/cast-server/README.md \
  <DIECAST_ROOT>/README.md \
  <DIECAST_ROOT>/docs/
```

Exclusions:
- `<DIECAST_ROOT>/tests/` — `tests/test_cast_upgrade.sh:298` literal `:8000` is intentional mock payload.
- The "Run the server" content sp7 will add to `README.md` — sp7 hasn't run yet, so README only needs the *existing* sites updated; sp7 will write the new subsection with the right values from the start.

After the sweep, re-run the grep from step 1.5 — should return zero hits.

### Step 1.7: Add `host` / `port` to `setup`'s `DEFAULTS` (Decision #7)

In `step6_write_config` at `setup:218–227`, the existing `DEFAULTS` shell associative array (or python heredoc) gets two new entries:

```python
"host": "localhost",
"port": 8005,
```

`bind_host` is **deliberately omitted** — env-var-only via `CAST_BIND_HOST` (advanced override; default loopback is right for ~99% of users). The merger at `setup:236–252` already handles "preserve user value, fill default for missing key" — no merger logic changes.

### Step 1.8: Document in `docs/config.md`

Add an entry for `host` / `port` to the schema reference. Document the env-var asymmetry explicitly:

> `CAST_HOST` is the *client-side* connect target (used by skills calling the server, default `localhost`).
> `CAST_BIND_HOST` is the *server-side* uvicorn bind (default `127.0.0.1`, env-var-only — not in `config.yaml`).
> `CAST_PORT` is shared by both sides (default `8005`).

### Step 1.9: CHANGELOG entry

Add a single entry under the next-version heading:

```
- Default cast-server port shifted from `8000` to `8005`.
- New env-var `CAST_HOST` (client-side connect target, default `localhost`).
- The pre-existing `CAST_HOST` (server bind) is renamed to `CAST_BIND_HOST` (default `127.0.0.1`).
- If you have an old cast-server still running on `:8000`, kill it manually
  (`lsof -ti:8000 | xargs kill`) before re-running `./setup`. No automatic detection.
```

## Verification

### Automated Tests (permanent)
- `uv run pytest` continues to pass (109/109 baseline). No new tests in this sub-phase — the sweep is verifiable by grep + spot-check.

### Validation Scripts (temporary)

```bash
# 1. Zero hits remaining (excluding tests/, CHANGELOG entries):
grep -rn '\(localhost\|127\.0\.0\.1\):8000' <DIECAST_ROOT>/ \
  --include='*.md' --include='*.py' --include='*.sh' \
  --exclude-dir=tests --exclude-dir=.git \
  | grep -v CHANGELOG

# 2. Bash-block pattern is correct:
grep -n 'CAST_HOST:-localhost' <DIECAST_ROOT>/skills/claude-code/cast-child-delegation/SKILL.md
# Expect: a curl line using ${CAST_HOST:-localhost}:${CAST_PORT:-8005}

# 3. Prose pattern is correct:
grep -n 'localhost:8005' <DIECAST_ROOT>/README.md
# Expect: e.g. "A local web UI at http://localhost:8005" (literal, not env-substitution)

# 4. agent_service.py uses constants:
grep -n 'DEFAULT_CAST_HOST\|DEFAULT_CAST_PORT' \
  <DIECAST_ROOT>/cast-server/cast_server/services/agent_service.py
# Expect: import + usage in the f-string at the four old hardcode sites.

# 5. config.py constants exist:
grep -n 'DEFAULT_CAST_PORT\|DEFAULT_CAST_HOST\|DEFAULT_CAST_BIND_HOST' \
  <DIECAST_ROOT>/cast-server/cast_server/config.py
# Expect: three lines.

# 6. bin/cast-server uses CAST_BIND_HOST:
grep -n 'CAST_BIND_HOST\|CAST_PORT' <DIECAST_ROOT>/bin/cast-server
# Expect: line 19 references both.
```

### Manual Checks
- Eyeball-diff `README.md` line 95 (existing "A local web UI at …" text) — confirm it became `:8005` literal, NOT env-var-substitution (this is prose, not a bash block).
- Eyeball-diff `skills/claude-code/cast-child-delegation/SKILL.md:30` — confirm it became env-var-substitution (this is inside a curl example block).
- Run the server manually: `CAST_PORT=9999 ./bin/cast-server` should bind on `:9999`. `CAST_BIND_HOST=0.0.0.0 ./bin/cast-server` should bind on `0.0.0.0:8005`.

### Success Criteria
- [ ] `grep` for `:8000` returns zero non-CHANGELOG hits.
- [ ] `bin/cast-server` references `CAST_BIND_HOST` and `8005`.
- [ ] `config.py` has all three `DEFAULT_CAST_*` constants.
- [ ] `agent_service.py` lines 889/915/992/1005 use the new constants.
- [ ] `bin/sweep-port-refs.py` exists and `--check` exits 0 on the post-sweep tree.
- [ ] `setup` `DEFAULTS` includes `host` and `port`.
- [ ] `docs/config.md` documents the asymmetry.
- [ ] `cast-server/README.md` (`:4`, `:23`) reflects the new defaults.
- [ ] CHANGELOG entry written.
- [ ] `uv run pytest` still 109/109.

## Execution Notes

- The sweep script is the riskiest part — bugs in markdown-fence detection cause silent corruption. Test the script on a small sample (one file with mixed prose + bash) first.
- Respect existing import ordering in `agent_service.py`. If it already pulls from `cast_server.config`, fold into that line rather than duplicating an import.
- Preserve trailing newlines in modified files; some markdown linters care.
- `setup`'s `DEFAULTS` literal is Python embedded in a heredoc — match the surrounding indentation exactly.

**Spec-linked files:** This sub-phase modifies `cast_server/services/agent_service.py`, which is linked by `docs/specs/cast-delegation-contract.collab.md`. Read that spec and verify SAV behaviors mentioning child-agent callback URLs survive the change (they should — the URL is functionally identical, only the constant source moves).
