# E2E Smoke Runbook — cast-subagent-and-skill-capture

> **Status:** Runbook authored 2026-05-01. Live e2e smoke deferred to
> operator (see "Why this is deferred" below).

## Why this is deferred

The sub-phase 5 plan calls for a live end-to-end smoke that requires a
**freshly-restarted cast-server** to pick up sp2's `api_agents.py`
modifications (the three new endpoints under
`/api/agents/subagent-invocations/`).

The currently-running cast-server process predates sp2's changes — a
direct `curl` confirms `/api/agents/subagent-invocations` returns
`{"detail":"Not Found"}`. sp3's output.md flagged the same gap.

The sp5 work was executed by `cast-subphase-runner`, which itself is a
child run of the live cast-server. Restarting cast-server from inside
the runner would kill the parent that monitors the agent-run
`output.json` for completion — the run would deadlock and time out (one
of the recorded error-memory patterns for this agent).

The hook-side payloads, the installer round-trip, and every code path
that does not hit the new endpoints are fully covered by the automated
suite landed in sp1–sp4. What remains is a **runtime integration check**
that the freshly-restarted server, the installed hooks, and a real
Claude Code session compose correctly into the threaded `/runs` tree.

## What sp5 verified before deferral

- The new spec `docs/specs/cast-subagent-and-skill-capture.collab.md`
  passes `bin/cast-spec-checker` with zero error findings (Step 5.2 — done).
- `_registry.md` shows the new spec row (Step 5.3 — done).
- Cross-spec back-references are in place on
  `cast-delegation-contract.collab.md`,
  `cast-user-invocation-tracking.collab.md`, and
  `cast-hooks.collab.md` (Step 5.4 — done).
- Uninstall round-trip on a settings.json seeded with third-party
  `SubagentStart` and `PreToolUse(matcher="Bash")` entries is
  byte-equivalent (Step 5.6 — done; transcript below).
- Hook handlers themselves exit 0 even against the stale server —
  fire-and-forget contract holds (sp3 verified this).

## How to run the deferred live smoke

The operator should run the following in **a fresh terminal session
that is not a cast-subphase-runner child**.

### Step 1 — Restart cast-server to pick up sp2 endpoints

```bash
# Kill the running cast-server (releases :8005 — see "kill before port
# bind" memory note).
pkill -f 'cast-server' || true
sleep 1
# Start fresh (cast-server reads schema.sql + applies migrations on boot).
uv run --project /data/workspace/diecast cast-server &
# Wait for boot.
until curl -s http://localhost:8005/api/agents/runs?status=running >/dev/null 2>&1; do sleep 1; done
# Verify the new endpoints exist.
curl -s -X POST http://localhost:8005/api/agents/subagent-invocations/complete \
  -H "Content-Type: application/json" \
  -d '{"claude_agent_id":"smoke-test-nonexistent"}'
# Expect: {"closed":0}   (HTTP 200, never 404)
```

### Step 2 — Install hooks for this project

```bash
cd /data/workspace/diecast
cast-hook install
# Expect: 5 entries written to .claude/settings.json
#   - UserPromptSubmit  → user-prompt-start
#   - Stop              → user-prompt-stop
#   - SubagentStart     → subagent-start
#   - SubagentStop      → subagent-stop
#   - PreToolUse        → skill-invoke   (matcher="Skill")
jq '.hooks | keys' .claude/settings.json
```

### Step 3 — Trigger a real cast-* slash command in Claude Code

In a new Claude Code session at `/data/workspace/diecast`, type at the
prompt:

```
/cast-detailed-plan goals/<some-goal>
```

(any goal slug that exists in `goals/` works — it doesn't matter whether
the plan completes; the run just needs to fire `Task()` for
`cast-detailed-plan`, which will then fire `Task()` again or a
`PreToolUse(Skill)` for downstream cast-* skills.)

### Step 4 — Watch the threaded `/runs` page

Open `http://127.0.0.1:8005/runs` in a browser. Within ~5 seconds of
the slash command:

| Expected row | Source | Owner |
|---|---|---|
| L1: `cast-detailed-plan` (user-invocation) | sibling `user_invocation_service` | `UserPromptSubmit` |
| L2: `cast-detailed-plan` (subagent) | this plan's `subagent_invocation_service` via `SubagentStart` | parent_run_id resolved via `resolve_parent_for_subagent` |
| L3: any HTTP-dispatched grandchild (e.g., `cast-plan-review`) | sibling delegation-contract path | parent set by HTTP dispatcher |
| Skill chips on the L2 subagent row (or L1 if subagent has not yet started) | `record_skill` via `PreToolUse(Skill)` | most-recent running cast-* row |
| L2 row flips `running → completed` | `subagent_invocation_service.complete` via `SubagentStop` exact-match on `claude_agent_id` | — |

### Step 5 — Capture screenshots

Take screenshots of:

1. **L2 chip view** — runs tree showing the user-invocation root, its
   subagent child, the grandchild, and the skill chip-row on whichever
   cast-* row is showing chips.
2. **L3 detail view** — the same run expanded to show the
   `.skills-detail` table with each distinct skill, count, and earliest
   `invoked_at`.

Save the screenshots into this `notes/` directory next to this file:

```
goals/cast-subagent-and-skill-capture/notes/
├── e2e-smoke.ai.md                 (this file)
├── e2e-smoke-l2.png                (L2 chip view)
└── e2e-smoke-l3.png                (L3 detail view)
```

### Step 6 — Post-smoke acceptance check

```sql
-- Verify subagent rows captured.
SELECT id, agent_name, status, session_id, claude_agent_id, parent_run_id,
       json_array_length(skills_used) AS skill_count
  FROM agent_runs
 WHERE agent_name LIKE 'cast-%'
   AND input_params LIKE '%"source":"subagent-start"%'
 ORDER BY started_at DESC
 LIMIT 10;
```

Expected:

- ≥1 row per cast-* `Task()` dispatch.
- Each row's `claude_agent_id` is non-NULL (the renamed `agent_id` from
  the SubagentStart payload).
- Each row's `parent_run_id` either points at the user-invocation root
  for that session, or at the most-recent-started cast-* subagent in
  the session — never at a non-cast row, never at a row in a different
  session.
- Each row's `status` is `"completed"` after the slash command turn
  finishes; `completed_at` is non-NULL.
- `skill_count` is non-zero on rows that invoked Skills.

## Transcript: uninstall round-trip (Step 5.6) — verified

Captured 2026-05-01 by the sp5 subphase-runner. Uses `cast-hook` from
the gstack-pattern install seam: `~/.claude/skills/diecast/bin/cast-hook`.

```
$ TESTDIR=/tmp/cast-hook-uninstall-test-$$
$ mkdir -p "$TESTDIR/.claude" && cd "$TESTDIR"
$ cat > .claude/settings.json <<'EOF'
{
  "hooks": {
    "SubagentStart": [{"hooks":[{"type":"command","command":"third-party-hook x","timeout":3}]}],
    "PreToolUse":    [{"matcher":"Bash","hooks":[{"type":"command","command":"third-party-bash-watch","timeout":3}]}]
  }
}
EOF
$ cp .claude/settings.json /tmp/seed-$$.json

$ cast-hook install
cast-hook: installed entries for user-prompt-start, user-prompt-stop,
  subagent-start, subagent-stop, skill-invoke

# After install: 5 cast entries co-exist alongside the third-party ones.
# Third-party SubagentStart entry survived byte-for-byte; PreToolUse
# matcher="Bash" survived too. Our PreToolUse entry carries
# matcher="Skill" — no clash.

$ cast-hook uninstall
cast-hook: removed entries for UserPromptSubmit, Stop, SubagentStart,
  SubagentStop, PreToolUse

$ diff <(jq -S . .claude/settings.json) <(jq -S . /tmp/seed-$$.json)
$ echo $?
0   # byte-equivalent
```

All 5 cast-hook entries removed; third-party `SubagentStart` and
`PreToolUse(matcher="Bash")` entries untouched. SC-004 satisfied.

## Acceptance criteria for closing the loop

This runbook is considered fully executed when the operator has:

- [ ] Restarted cast-server and confirmed `/api/agents/subagent-invocations`
      returns 200 (not 404).
- [ ] Installed hooks via `cast-hook install` and confirmed 5 settings.json
      entries.
- [ ] Triggered ≥1 cast-* slash command in a fresh Claude Code session.
- [ ] Observed the user-invocation root, subagent child, and grandchild
      in `/runs` with the correct topology.
- [ ] Observed skill chips on whichever cast-* row was most-recent-running
      at Skill-invocation time.
- [ ] Confirmed the subagent row flipped `running → completed` on
      `SubagentStop`.
- [ ] Saved L2 and L3 screenshots into this `notes/` directory.
- [ ] Run the SQL acceptance check from Step 6 and confirmed the row
      shape.

If any of those fail, the failure mode is captured in
`docs/execution/cast-subagent-and-skill-capture/sp5_spec_and_e2e/output.md`
with reproduction steps for triage in a follow-up sub-phase.
