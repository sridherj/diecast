# Sub-phase 8: End-to-End Smoke Test

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Validate the full lifecycle in a real Claude Code session against a tmp project that
already had unrelated hooks before install. Cover happy path, non-cast prompts, orphan
self-heal (within and beyond the staleness window), uninstall, and failure-mode probes
(read-only settings, malformed settings).

## Dependencies

- **Requires completed:** sp1–sp7. Everything must be shipped, including specs.
- **Assumed codebase state:** `cast-server` builds and runs. `cast-hook` is on PATH.
  All unit/integration tests pass.

## Scope

**In scope:**
- End-to-end smoke walking through every behavior promised by the plan.
- Failure-mode probes against a tmp project.
- A documented run log (output written to the sub-phase's `output.md` on completion).

**Out of scope (do NOT do these):**
- Adding more unit/integration tests — those should already exist from sp1–sp5.
- Fixing bugs found during smoke (escalate as a separate fix sub-phase if anything
  fails).

## Files to Create/Modify

None — this sub-phase only **uses** the system. Output: a run log written to
`docs/execution/capture-user-invocations-as-runs/sp8_e2e_smoke/output.md`.

## Detailed Steps

### Step 8.1: Pre-install state capture

```bash
# Pick (or create) a tmp project that already has unrelated hooks.
TMP=$(mktemp -d -p ~)            # Claude Code needs a real path it can spawn into
cd $TMP
git init                          # marker
mkdir -p .claude
cat > .claude/settings.json <<EOF
{
  "hooks": {
    "PreCompact": [
      {"hooks": [{"type": "command", "command": "echo unrelated-precompact", "timeout": 5}]}
    ],
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "echo third-party-prompt", "timeout": 5}]}
    ]
  }
}
EOF

# Snapshot pre-install state for byte-for-byte comparison later.
cp .claude/settings.json /tmp/cast-e2e-pre-install.json
```

Record `cat .claude/settings.json` output in the run log.

### Step 8.2: Install + verify additive merge

```bash
cast-hook install
cat .claude/settings.json
```

**Expect:**
- `PreCompact` array: byte-for-byte identical to pre-install snapshot.
- `UserPromptSubmit` array: contains the original third-party entry **plus** our
  cast-hook entry (in either order — appended).
- `Stop` array: contains only our cast-hook entry.

Diff snapshot:

```bash
diff /tmp/cast-e2e-pre-install.json .claude/settings.json
# Expect: PreCompact unchanged; UserPromptSubmit gains our entry; Stop is new.
```

Record the diff in the run log.

### Step 8.3: Lifecycle smoke — happy path

Restart Claude Code in this tmp project (so the hooks load). Make sure `bin/cast-server`
is running.

In Claude Code, type:

```
/cast-plan-review just smoke-testing the hook lifecycle, please ignore
```

Within 1 second, query the DB:

```bash
sqlite3 <agent_runs.db path> \
  "SELECT id, agent_name, status, json_extract(input_params,'$.source'), session_id, parent_run_id, started_at, completed_at FROM agent_runs ORDER BY started_at DESC LIMIT 1"
```

**Expect:**
- `agent_name = "cast-plan-review"`
- `status = "running"`
- `input_params.source = "user-prompt"`
- `session_id` populated (non-null, non-empty)
- `parent_run_id = NULL`
- `started_at` set, `completed_at` NULL

After Claude finishes the turn:

```bash
sqlite3 ... "SELECT status, completed_at FROM agent_runs WHERE id=?"
```

**Expect:**
- `status = "completed"`
- `completed_at` set.

### Step 8.4: Negative path — non-cast prompt

In Claude Code, type a freeform prompt: `What time is it?`

After the turn ends, query for new rows:

```bash
sqlite3 ... \
  "SELECT count(*) FROM agent_runs WHERE json_extract(input_params,'$.source')='user-prompt' AND started_at > <prior-row.started_at>"
```

**Expect:** 0. Freeform prompts produce no rows.

### Step 8.5: Orphan self-heal — within window

Manually insert a stale `running` row simulating a prior crashed turn:

```bash
SESSION=<the current session_id from step 8.3>
NOW_MINUS_30=<ISO8601 UTC, 30 minutes ago>

sqlite3 ... <<EOF
INSERT INTO agent_runs (id, agent_name, goal_slug, input_params, session_id, status, parent_run_id, started_at)
VALUES ('orphan-30', 'cast-plan-review', 'system-ops',
        json('{"source":"user-prompt","prompt":"crashed turn"}'),
        '$SESSION', 'running', NULL, '$NOW_MINUS_30');
EOF
```

In Claude Code, type `/cast-plan-review another smoke check`. After the turn ends:

```bash
sqlite3 ... \
  "SELECT id, status FROM agent_runs WHERE session_id='$SESSION' ORDER BY started_at"
```

**Expect:** both the orphan AND the new row are `completed`.

### Step 8.6: Orphan self-heal — beyond window (staleness boundary)

```bash
SESSION=<a fresh session_id, or restart Claude Code first>
NOW_MINUS_90=<ISO8601 UTC, 90 minutes ago>

sqlite3 ... <<EOF
INSERT INTO agent_runs (id, agent_name, goal_slug, input_params, session_id, status, parent_run_id, started_at)
VALUES ('orphan-90', 'cast-plan-review', 'system-ops',
        json('{"source":"user-prompt","prompt":"ancient crashed turn"}'),
        '$SESSION', 'running', NULL, '$NOW_MINUS_90');
EOF
```

Type `/cast-plan-review` in this session. After the turn:

```bash
sqlite3 ... "SELECT id, status FROM agent_runs WHERE session_id='$SESSION' ORDER BY started_at"
```

**Expect:** the new row is `completed`; the 90-minute orphan is **still `running`**.
Decision #5 staleness window verified.

### Step 8.7: Uninstall + verify surgical removal

```bash
cast-hook uninstall
cat .claude/settings.json
```

**Expect:**
- `UserPromptSubmit` array: contains only the original third-party entry (our entry
  removed).
- `Stop` array: deleted (was only ours; sp5 deletes empty arrays).
- `PreCompact` array: unchanged.

```bash
diff /tmp/cast-e2e-pre-install.json .claude/settings.json
# Expect: byte-for-byte equivalent (modulo JSON formatting if any).
```

Restart Claude Code in this tmp project. Type `/cast-plan-review`. Verify **no row is
created** — hooks gone.

### Step 8.8: Failure-mode probes

#### Permission denied

```bash
cast-hook install                              # re-install for this probe
chmod 0o444 .claude/settings.json
cast-hook install
# Expect: SystemExit, non-zero, readable message naming --user as workaround.
# Verify .tmp files do NOT linger:
ls .claude/settings.json.tmp* 2>/dev/null      # must be empty
chmod 0o644 .claude/settings.json
```

#### Malformed JSON

```bash
echo '{not json' > .claude/settings.json
cast-hook install
# Expect: SystemExit, non-zero, readable JSON parse error.
# Original file untouched:
cat .claude/settings.json
# Expect: still '{not json'.
```

Restore by uninstalling/reinstalling cleanly or by pasting back the snapshot.

### Step 8.9: Document the run

Write `docs/execution/capture-user-invocations-as-runs/sp8_e2e_smoke/output.md` with:

- Pre-install snapshot
- Post-install diff
- DB row dumps from each step
- Pass/fail status for each behavior under test
- Any anomalies — including hook payload shape (Risks #1: confirm `UserPromptSubmit`
  payload contains `prompt` and `Stop` payload contains `session_id`. If either is
  missing, that's a blocker — escalate.)

## Verification

### Automated Tests (permanent)

None. This sub-phase is manual smoke.

### Validation Scripts (temporary)

The full sequence in Steps 8.1–8.8.

### Manual Checks

Walk through each step, confirm expected outcomes match observed.

### Success Criteria

- [ ] Pre-existing third-party hooks survive install byte-for-byte.
- [ ] `/cast-plan-review` creates a row with the correct shape.
- [ ] Stop transitions the row to `completed`.
- [ ] Non-cast prompts create no rows.
- [ ] Within-window orphan (30 min) is auto-closed alongside the current row.
- [ ] Beyond-window orphan (90 min) is **NOT** auto-closed.
- [ ] Uninstall removes only our entries; third-party entries survive byte-for-byte.
- [ ] Empty event arrays / empty `hooks` dict are dropped after uninstall.
- [ ] Permission-denied probe surfaces a readable message.
- [ ] Malformed-JSON probe surfaces a readable message and leaves the file untouched.
- [ ] Hook payloads contain the fields we depend on (`prompt`, `session_id`).
- [ ] Run log written to `sp8_e2e_smoke/output.md`.

## Execution Notes

- This sub-phase requires a real Claude Code session — it cannot be fully automated.
  Plan the time accordingly.
- The orphan-insert SQL relies on knowing the schema columns. If `agent_runs` has
  required columns the plan didn't enumerate (e.g., `goal_id`), look at an existing row
  and mirror its shape.
- **Risks #1 is the load-bearing assumption:** if Claude Code's `Stop` payload doesn't
  include `session_id`, the close path silently no-ops. The fallback design (marker
  file) is documented in the plan but parked. If you discover this gap during smoke,
  STOP and escalate — do not silently fall back.
- **PATH risk (Risks #3):** if `cast-hook` isn't on PATH at hook-fire time, the hook
  silently no-ops. Verify `which cast-hook` from inside the same shell environment
  Claude Code spawns.
- **Spec-linked files:** `cast-user-invocation-tracking.collab.md`,
  `cast-hooks.collab.md`. If any behavior here diverges from those specs, that's a bug
  somewhere — STOP and reconcile.
- After a successful smoke, this is the moment to close the goal: update the plan's
  status from "Reviewed via /cast-plan-review BIG; ready for execution" to "Shipped."
