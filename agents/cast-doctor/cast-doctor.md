---
name: cast-doctor
description: >
  Diagnose Diecast installation health. Hits the cast-server /api/health
  endpoint when the server is up; falls back to running bin/cast-doctor --json
  directly when it isn't. Surfaces actionable findings via
  cast-interactive-questions.
  Trigger phrases: "doctor", "cast-doctor", "diagnose", "health check",
  "what's wrong".
memory: user
effort: small
---

# /cast-doctor — Diagnose Diecast installation

Post-install diagnostic surface for Diecast. Reports prerequisite status as
`{red, yellow, green}` findings, with actionable hints for each red/yellow item.

## Behavior

1. **Primary path:** hit the running cast-server.

   ```bash
   curl -fs "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/health"
   ```

   - On HTTP 200: parse JSON `{"red": [...], "yellow": [...], "green": [...]}`
     and render the markdown summary below.
   - On connection refused, non-200, or empty body: fall through to fallback.

2. **Fallback path (server down):** run the local script directly.

   ```bash
   "${REPO_DIR:-$PWD}/bin/cast-doctor" --json
   ```

   Same JSON shape; same renderer. Tell the user the server is down so they
   know why the diagnosis path differs.

3. **Action surfacing:** for each red/yellow finding with a configurable fix
   (e.g. unsupported `$CAST_TERMINAL`, missing prereq, "no supported terminal
   found"), surface the action via `cast-interactive-questions` so the user
   can apply it inline. Configurable fixes today:

   - **Unsupported / unset terminal** → offer to run `bin/cast-doctor
     --fix-terminal` from the user's shell.
   - **Missing prereq with an `install:` hint** → echo the hint verbatim; do
     not run installers automatically.

> **ERROR HANDLING:** If both the curl and the bash fallback fail (e.g.
> `bin/cast-doctor` not found on the resolved path), STOP and tell the user:
> "Human intervention required: cast-doctor unavailable — could not reach
> cast-server and bin/cast-doctor is missing."

## Output format

```markdown
## /cast-doctor

**Source:** `/api/health` (cast-server up)   ← or "fallback: bin/cast-doctor --json" when server is down

### Red — must fix
- python3 3.9.6 found (need >= 3.11). Install: brew install python@3.11
- tmux not found (required by the dispatcher). Install: brew install tmux

### Yellow — recommended
- $CAST_TERMINAL=xterm is not a supported terminal. → /cast-doctor (or `bin/cast-doctor --fix-terminal`).

### Green — OK
- bash 5.2.21
- uv 0.4.18
- git 2.43.0
- claude on PATH (/usr/local/bin/claude)
- ~/.claude writable
- ~/.cast writable
```

If `red` is empty, lead with **"All required prerequisites satisfied."**

## Notes

- This skill is the canonical user surface. `bin/cast-doctor` remains
  callable from a shell as a fallback (and is what `setup`'s `step1_doctor`
  invokes) but the recommended user-facing entry point is `/cast-doctor`
  inside Claude Code.
- The endpoint shells out to `bin/cast-doctor --json` server-side (v1); the
  shape is stable and contract-tested.
- Trigger phrases include "doctor" and "cast-doctor" so `/<` autocomplete
  surfaces the skill on partial matches.
