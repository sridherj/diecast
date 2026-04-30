# Sub-phase 6: `/cast-doctor` skill + `/api/health` + bin docstring sweep

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Tighten the user-facing surface so `cast-server` is the only CLI on `$PATH`, and every other Diecast operation is a `/cast-*` slash command (Decision #18). Introduce a new `/cast-doctor` skill backed by a new `/api/health` endpoint with a Bash-fallback to `bin/cast-doctor --json` for when the server is down. Mark every other `bin/*` script as internal-only via header docstrings. Override the in-flight terminal-defaults plan's user-discovery wording in 4 sites + `ResolutionError` (Decision #19).

## Dependencies

- **Requires completed:**
  - sp1 (port seam) — `/api/health` URL uses `DEFAULT_CAST_HOST`/`DEFAULT_CAST_PORT`; skill markdown uses the bash env-var pattern.
  - sp2 (doctor preflight) — `/api/health` reuses the cast-doctor RED-list shape, including the new python3/tmux entries.
- **Assumed codebase state:** sp1 has shifted port to 8005 and added env-var seam. sp2 has extended `bin/cast-doctor` with python3/tmux RED checks. `bin/cast-doctor` exists with `--fix-terminal` flag (already shipped in commit `28db472` per terminal-defaults plan). `agents/_shared/terminal.py` has the `ResolutionError` class with an `improved_message`.

## Scope

**In scope:**
- New `agents/cast-doctor/cast-doctor.md` — canonical agent source for the `/cast-doctor` skill.
- `bin/generate-skills` produces `skills/claude-code/cast-doctor/SKILL.md` on next setup (no manual edit).
- New `cast-server/cast_server/routes/api_health.py` — `/api/health` endpoint returning `{"red","yellow","green"}` shape.
- `cast-server/cast_server/app.py` — register the new `api_health` router.
- `bin/cast-doctor`:
  - Header docstring rewrite (lines 8–12) per §H step 1 (Decision #18).
  - User-discovery wording shift at lines 12, 57, 224, 241 per §H step 7 (Decision #19).
  - Add `--json` flag that emits the structured shape `/api/health` consumes.
- `agents/_shared/terminal.py` — `ResolutionError` improved-message text shifts to `/cast-doctor` (Decision #19).
- Internal-use docstrings for: `bin/cast-spec-checker`, `bin/check-doc-links`, `bin/audit-interdependencies`, `bin/lint-anonymization`, `bin/generate-skills`, `bin/migrate-legacy-estimates.py`, `bin/migrate-next-steps-shape.py`, `bin/run-migrations.py` (with extra deprecation note pointing at sp3's Alembic), `bin/set-proactive-defaults.py`.
- `bin/README.md` rewrite — User-facing-only-cast-server framing.
- Terminal-defaults' `tests/test_b6_terminal_resolution.py` — update assertion against new `ResolutionError` text.

**Out of scope (do NOT do these):**
- README.md "Run the server" subsection — sp7 owns README.md edits, including the §H step 6 mental-model postscript.
- The `--fix-terminal` flag mechanism itself — already shipped in `28db472`; this sub-phase only changes user-facing presentation.
- The `step1_doctor` or any `setup` step — sp8 owns setup edits.
- Removing `bin/run-migrations.py` — only mark deprecated; full removal is out-of-plan.
- Adding python3/tmux checks — sp2 owns those.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `agents/cast-doctor/cast-doctor.md` | Create | Does not exist. |
| `cast-server/cast_server/routes/api_health.py` | Create | Does not exist. |
| `cast-server/cast_server/app.py` | Modify | Has other route registrations; no `api_health`. |
| `bin/cast-doctor` | Modify | Lines 8–12 docstring, line 12 `--fix-terminal` help, line 57 usage block, line 224 yellow message, line 241 yellow message, plus a new `--json` flag. (sp2 already added python3/tmux to RED list.) |
| `agents/_shared/terminal.py` | Modify | `ResolutionError.improved_message` text. |
| `bin/cast-spec-checker`, `bin/check-doc-links`, `bin/audit-interdependencies`, `bin/lint-anonymization`, `bin/generate-skills`, `bin/migrate-legacy-estimates.py`, `bin/migrate-next-steps-shape.py`, `bin/run-migrations.py`, `bin/set-proactive-defaults.py` | Modify | Headers do not say "Internal use; not on user PATH". |
| `bin/README.md` | Rewrite | Existing; outdated framing. |
| `tests/test_b6_terminal_resolution.py` | Modify | (If it exists per the terminal-defaults plan) — pinned old `ResolutionError` text needs updating. |

## Detailed Steps

### Step 6.1: Author `agents/cast-doctor/cast-doctor.md`

Use the canonical agent template (look at `agents/cast-runs/cast-runs.md` or another existing `/cast-*` agent for the convention). Structure:

```markdown
---
name: cast-doctor
description: Diagnose Diecast installation health. Hits the cast-server /api/health
  endpoint when the server is up; falls back to running bin/cast-doctor --json directly
  when it isn't. Surfaces actionable findings via cast-interactive-questions.
trigger phrases: ["doctor", "cast-doctor", "diagnose", "health check", "what's wrong"]
---

# /cast-doctor — Diagnose Diecast installation

## Behavior

1. **Primary path:** `curl -s http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/health`.
   - On 200: parse JSON `{"red": [...], "yellow": [...], "green": [...]}` and render
     a Claude-Code-friendly markdown summary.
   - On connection refused or non-200: fall through to fallback.

2. **Fallback path:** Bash tool: `${REPO_DIR}/bin/cast-doctor --json` and render the same shape.

3. **Action surfacing:** for each red/yellow finding with a configurable fix
   (e.g. `terminal_unsupported`, `prereq_missing`, `--fix-terminal`-eligible state),
   surface via `cast-interactive-questions` so the user can apply inline.

## Output format

(Markdown summary with three sections: Red, Yellow, Green. Each red/yellow item
includes the action hint, e.g. "→ brew install tmux".)
```

Match the SKILL.md style of other cast-* skills. Make sure the trigger phrases include "doctor" and "cast-doctor" so Claude Code's slash-command autocomplete surfaces it.

### Step 6.2: Author `cast-server/cast_server/routes/api_health.py`

```python
"""GET /api/health — cast-doctor parity (red/yellow/green)."""
import json
import subprocess
from pathlib import Path

from fastapi import APIRouter

from cast_server.config import REPO_ROOT  # or whatever points at the repo

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("")
def health() -> dict:
    """Returns the cast-doctor JSON shape: {"red": [...], "yellow": [...], "green": [...]}."""
    bin_path = REPO_ROOT / "bin" / "cast-doctor"
    proc = subprocess.run(
        [str(bin_path), "--json"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    # cast-doctor exits non-zero on red findings; that's expected, not an error here.
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "red": [{"name": "cast-doctor-shell", "msg": "could not parse output", "stderr": proc.stderr}],
            "yellow": [],
            "green": [],
        }
```

For v1, shelling out to `bin/cast-doctor --json` is acceptable per the plan ("a shared Python module if the cost is low, or a `subprocess.run` for v1"). A future iteration can extract a shared module if needed.

If `REPO_ROOT` isn't already exposed by `cast_server.config`, add it: `REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent` (adjust depth to match actual layout).

### Step 6.3: Register the router in `cast-server/cast_server/app.py`

Find where existing routers are imported and registered (e.g., `app.include_router(api_agents.router)`); add an analogous line for `api_health`. Keep alphabetical or original ordering.

### Step 6.4: Add `--json` flag to `bin/cast-doctor`

Today cast-doctor emits human-readable RED/YELLOW/GREEN to stdout. Add a `--json` flag that emits the same shape as `/api/health` returns. The implementation can collect findings into bash arrays during the existing checks and emit JSON at the end:

```bash
JSON_OUTPUT=0
case "${1:-}" in
  --json) JSON_OUTPUT=1; shift ;;
esac

# during checks, append to arrays:
RED_FINDINGS=()
YELLOW_FINDINGS=()
GREEN_FINDINGS=()

# helper:
append_finding() {
  local color="$1" name="$2" msg="$3" hint="${4:-}"
  if [ "$JSON_OUTPUT" -eq 1 ]; then
    # accumulate; final emit at end
    eval "${color^^}_FINDINGS+=('{\"name\":\"$name\",\"msg\":\"$msg\",\"hint\":\"$hint\"}')"
  else
    case "$color" in
      red)    red    "$msg"; [ -n "$hint" ] && echo "  → $hint" ;;
      yellow) yellow "$msg"; [ -n "$hint" ] && echo "  → $hint" ;;
      green)  green  "$msg" ;;
    esac
  fi
}

# at end:
if [ "$JSON_OUTPUT" -eq 1 ]; then
  printf '{"red":[%s],"yellow":[%s],"green":[%s]}\n' \
    "$(IFS=,; echo "${RED_FINDINGS[*]}")" \
    "$(IFS=,; echo "${YELLOW_FINDINGS[*]}")" \
    "$(IFS=,; echo "${GREEN_FINDINGS[*]}")"
fi
```

JSON-escape string contents (msg/hint may contain quotes). A small helper:

```bash
json_escape() { printf '%s' "$1" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read())[1:-1])'; }
```

If implementation in pure bash gets gnarly, defer JSON emission to a one-liner Python sub-call at the end — the script already requires python3 (sp2). Keep the implementation small.

### Step 6.5: Header docstring rewrite at `bin/cast-doctor` lines 8–12 (§H step 1)

Replace the existing "Run this … any time post-install" line with:

```bash
# Internal: invoked by `setup`'s `step1_doctor` and CI. Post-install diagnosis
# happens via `/cast-doctor` from inside Claude Code.
```

Keep the script fully functional.

### Step 6.6: Presentation-shift wording (§H step 7, Decision #19)

Four sites in `bin/cast-doctor`:

- **Line 12** (`--fix-terminal` listing in `--help`): change "interactive first-run setup" → "internal: invoked by `setup` and the `/cast-doctor` skill; users should run `/cast-doctor` from inside Claude Code."
- **Line 57** (usage block within `print_help()`): same wording shift.
- **Line 224** (yellow message for unsupported `$CAST_TERMINAL`): change "Run `bin/cast-doctor --fix-terminal` to probe and configure interactively" → "Run `/cast-doctor` from inside Claude Code to probe and configure (or `bin/cast-doctor --fix-terminal` from a shell as fallback)".
- **Line 241** (yellow message for "no supported terminal found"): same wording shift.

Verify line numbers — they may have shifted slightly after sp2's RED-list additions. Find the four sites by their distinctive content, not by line number.

### Step 6.7: `agents/_shared/terminal.py` — `ResolutionError` text (Decision #19)

Per terminal-defaults plan §2 lines 78–83, change:

```
fix: run `bin/cast-doctor --fix-terminal` to auto-detect and configure
```

to:

```
fix: run `/cast-doctor` from inside Claude Code to auto-detect and configure
```

Search for the exact string in `agents/_shared/terminal.py` to locate the message-builder.

### Step 6.8: Update `tests/test_b6_terminal_resolution.py` (terminal-defaults coordination)

If this test file exists, it likely asserts on the old `ResolutionError` text. Update the expected string to match step 6.7. If the file doesn't exist, skip; the coordinated change becomes moot.

```python
# Before:
# assert "bin/cast-doctor --fix-terminal" in str(exc.value)
# After:
assert "/cast-doctor" in str(exc.value)
```

Call out this coordinated edit in the PR description.

### Step 6.9: Internal-use docstrings (§H step 4)

For each script in the list below, add or update the header docstring to include a line like `# Internal use; not on user PATH. Invoked by <X>.`:

- `bin/cast-spec-checker` — invoked by `cast-spec-checker` agent / CI. Post-install user surface is `/cast-spec-checker` skill.
- `bin/check-doc-links` — invoked by CI doc-link audits.
- `bin/audit-interdependencies` — invoked by CI dependency audits.
- `bin/lint-anonymization` — invoked by CI anonymization linter.
- `bin/generate-skills` — invoked by `setup`'s `step4_install_skills`.
- `bin/migrate-legacy-estimates.py` — one-shot data migration; obsolete after the matching deploy.
- `bin/migrate-next-steps-shape.py` — same.
- `bin/run-migrations.py` — **deprecation note**: "Deprecated by Alembic (sp3). Will be removed once all known DBs have been migrated. Do not invoke for new schema changes."
- `bin/set-proactive-defaults.py` — invoked by `setup`'s default-init step.

`bin/_lib.sh` — sourced helper, not directly invoked. Already clear; optional one-line clarification.

### Step 6.10: Rewrite `bin/README.md` (§H step 5)

Top of file (replace whatever's there):

```markdown
# `bin/`

**User-facing:** only `cast-server` (symlinked to `~/.local/bin/cast-server` by
`./setup`). All other entries are internal tooling — invoked by `setup`, CI, or
one-shot migrations. Post-install user surface lives in `/cast-*` slash commands
inside Claude Code.

## User-facing
- `cast-server` — the daemon; the only Diecast binary on your `$PATH`.

## Internal — invoked by `setup` or CI
- `cast-doctor` — diagnostic checks. User surface: `/cast-doctor` slash command
  inside Claude Code.
- `_lib.sh` — shared bash helpers (`log`, `warn`, `fail`, `backup_if_exists`).
- `generate-skills` — produces `skills/claude-code/cast-*/SKILL.md` from `agents/`.
- `sweep-port-refs.py` — markdown-aware port/host sweep (one-shot; see sp1).
- (etc. — list all bin/* scripts with one-line role descriptions.)

## Internal — CI lints
- `check-doc-links`, `audit-interdependencies`, `lint-anonymization`, `cast-spec-checker`.

## Internal — one-shot data migrations
- `migrate-legacy-estimates.py`, `migrate-next-steps-shape.py`,
  `set-proactive-defaults.py`. These are obsolete after their matching deploy
  but kept for users on stale databases.

## Deprecated
- `run-migrations.py` — superseded by Alembic (`cast-server/alembic/`).
  Will be removed in a future release.
```

Adjust the script lists to reflect the actual contents of `bin/`.

## Verification

### Automated Tests (permanent)

- `tests/test_b6_terminal_resolution.py` — extended/updated for the new `ResolutionError` wording (step 6.8).
- New: `tests/test_api_health.py` (optional — small smoke test):

```python
def test_api_health_returns_red_yellow_green_shape(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"red", "yellow", "green"}
```

If the project doesn't have a `client` fixture, skip and rely on manual verification.

### Validation Scripts (temporary)

```bash
# 1. /api/health endpoint:
curl -s http://localhost:8005/api/health | jq
# Expect: {"red":[...],"yellow":[...],"green":[...]}

# 2. /cast-doctor skill resolves and renders:
# (Inside Claude Code) /cast-doctor → markdown summary

# 3. bin/cast-doctor --json output:
bin/cast-doctor --json | jq
# Expect: same JSON shape

# 4. Header docstring update:
head -15 bin/cast-doctor | grep -q "Internal: invoked by \`setup\`'s \`step1_doctor\` and CI"

# 5. bin/* internal-use markers present:
for f in bin/cast-spec-checker bin/check-doc-links bin/audit-interdependencies \
         bin/lint-anonymization bin/generate-skills bin/migrate-legacy-estimates.py \
         bin/migrate-next-steps-shape.py bin/run-migrations.py bin/set-proactive-defaults.py; do
  head -10 "$f" | grep -q "Internal use" || echo "MISSING marker: $f"
done
# Expect: no output

# 6. Yellow-message override:
CAST_TERMINAL=nope bin/cast-doctor 2>&1 | grep -F "/cast-doctor"
# Expect: a hit; the old "bin/cast-doctor --fix-terminal" wording is gone (or only present as fallback hint).

# 7. ResolutionError text:
python3 -c "from agents._shared.terminal import ResolutionError; \
            try: raise ResolutionError(); \
            except ResolutionError as e: print(e.improved_message())" \
  | grep -F "/cast-doctor"
```

### Manual Checks
- Run `/cast-doctor` inside Claude Code with cast-server up — confirm `/api/health` is hit and findings render as markdown.
- Stop cast-server, run `/cast-doctor` again — confirm the fallback shells out to `bin/cast-doctor --json`.
- Open `bin/README.md` on github.com — confirms the new framing renders cleanly.

### Success Criteria
- [ ] `agents/cast-doctor/cast-doctor.md` exists with correct frontmatter and behavior description.
- [ ] `cast-server/cast_server/routes/api_health.py` exists; router registered in `app.py`.
- [ ] `/api/health` returns the `{red, yellow, green}` shape.
- [ ] `bin/cast-doctor --json` emits the same shape.
- [ ] `bin/cast-doctor` lines 8–12 docstring updated; presentation wording at lines 12, 57, 224, 241 shifted to `/cast-doctor`.
- [ ] `agents/_shared/terminal.py` `ResolutionError` text updated.
- [ ] `tests/test_b6_terminal_resolution.py` updated (if it exists) and passing.
- [ ] All 9 internal `bin/*` scripts have "Internal use" markers.
- [ ] `bin/README.md` rewritten with user-facing/internal split.
- [ ] `bin/run-migrations.py` includes the Alembic-deprecation note.
- [ ] `uv run pytest` green.

## Execution Notes

- **Coordinate with sp2:** sp2 may have moved the line-numbers cited in step 6.6 by inserting python3/tmux RED-list checks. Find the four wording sites by content, not by hardcoded line numbers.
- **Don't break the bootstrap chicken-and-egg:** `bin/cast-doctor` MUST stay callable from `step1_doctor` because it runs *before* Claude Code is verified. `/cast-doctor` is a thin layer over the bin script — both must work.
- **`ResolutionError` test coordination:** the terminal-defaults plan (already partly merged in `28db472`) may have a test asserting the old `ResolutionError` text. Update that assertion in this same PR; reference the cross-plan dependency in the PR body.
- **JSON emission from bash:** if hand-rolling JSON in bash gets brittle, deferring to `python3 -c '...'` at the very end is acceptable — cast-doctor already requires python3 (sp2).
- **Don't edit README.md** here — sp7 owns it. The §H step 6 mental-model postscript is sp7's responsibility, not this sub-phase's.

**Spec-linked files:** None of the modified files are currently linked by a spec in `docs/specs/`. If a future spec covers `bin/cast-doctor` or `/api/health`, the SAV behaviors should preserve the JSON shape contract documented above.
