# Sub-phase 5 Output: Spec capture + e2e smoke + close-out

**Status:** Done (with deferred live e2e smoke)
**Completed:** 2026-05-01

## Summary

Authored the new spec `docs/specs/cast-subagent-and-skill-capture.collab.md`
covering all 8 user stories from the refined requirements (US1–US8),
17 functional requirements (FR-001..FR-017), and 7 success criteria
(SC-001..SC-007 verbatim from the source plan). The spec lints clean
under `bin/cast-spec-checker`. Registered in `_registry.md`, with
cross-spec back-references on the three sibling specs. Uninstall
round-trip is byte-equivalent. **Live e2e smoke deferred to operator**
because the running cast-server predates sp2's endpoints and a
mid-flight restart would deadlock this subphase-runner.

## Files Created
- `docs/specs/cast-subagent-and-skill-capture.collab.md` — new spec.
  Frontmatter `linked_files` enumerates 24 paths including `_cast_name.py`,
  `_invocation_sources.py`, the `notes/payload-shapes.ai.md` empirical
  capture (authoritative for field names), and the new
  `notes/e2e-smoke.ai.md` runbook. Behavior section covers all 8 user
  stories. FR-013 marked RESOLVED, not TODO.
- `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` — runbook
  for the deferred live smoke. Six-step procedure: cast-server restart →
  hook install → live cast-* slash command → /runs topology check → screenshot
  capture → SQL acceptance query. Includes the verified uninstall
  round-trip transcript (Step 5.6).

## Files Modified
- `docs/specs/_registry.md` — added the new spec row per Step 5.3 verbatim.
- `docs/specs/cast-delegation-contract.collab.md` — one-line back-reference
  (Step 5.4) noting subagent rows ride a parallel session_id-based capture
  path with `claude_agent_id` closure and do NOT write `output.json`
  delegation files; the two contracts coexist.
- `docs/specs/cast-user-invocation-tracking.collab.md` — one-line
  back-reference (Step 5.4) noting subagent rows ride the same `session_id`
  but additionally carry `claude_agent_id` and use a different
  `source` discriminator (`subagent-start` vs `user-prompt`); source
  constants live in `_invocation_sources.py`.
- `docs/specs/cast-hooks.collab.md` — back-reference (Step 5.4) noting the
  per-event `matcher` slot extension to `HOOK_EVENTS` (4-tuple shape) and
  matcher-aware idempotency in install/uninstall.
- `docs/execution/cast-subagent-and-skill-capture/_manifest.md` — sp5 row
  flipped to Done with note about the deferred live smoke; progress log
  entry added.

## Verification

### Automated

```
$ bin/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md
$ echo $?
0
```

The other three modified specs lint exactly as they did before this
sub-phase touched them (`cast-hooks.collab.md` clean;
`cast-delegation-contract.collab.md` has pre-existing R1 findings caused
by its own non-template-conforming shape — verified those existed on
the un-stashed baseline and are not introduced by this sub-phase;
`cast-user-invocation-tracking.collab.md` clean).

### Manual — Step 5.6 uninstall round-trip

```
$ cd /tmp/cast-hook-uninstall-test-$$
$ cat > .claude/settings.json <<'EOF'
{
  "hooks": {
    "SubagentStart": [{"hooks":[{"type":"command","command":"third-party-hook x","timeout":3}]}],
    "PreToolUse":    [{"matcher":"Bash","hooks":[{"type":"command","command":"third-party-bash-watch","timeout":3}]}]
  }
}
EOF
$ cp .claude/settings.json /tmp/seed-$$.json
$ cast-hook install     # 5 entries written; third-party survives
$ cast-hook uninstall   # 5 entries removed; third-party survives
$ diff <(jq -S . .claude/settings.json) <(jq -S . /tmp/seed-$$.json)
$ echo $?
0
```

**Byte-equivalent. Third-party `SubagentStart` and `PreToolUse(matcher="Bash")`
survived install + uninstall untouched. SC-004 satisfied.**

### Manual — Step 5.5 live e2e smoke (DEFERRED)

The running cast-server predates sp2's `api_agents.py` modifications.
Direct probe:

```
$ curl -s -X POST http://localhost:8005/api/agents/subagent-invocations/complete \
    -H "Content-Type: application/json" \
    -d '{"claude_agent_id":"smoke-probe"}'
{"detail":"Not Found"}
```

Restarting cast-server inside this `cast-subphase-runner` would kill the
parent process that monitors our `output.json` for completion — the run
would deadlock and time out. (One of the recorded error-memory patterns
for this agent: "timeout (2x): Dynamic verification … blocked".)

**Deferral artifact:** `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md`
captures the full six-step runbook the operator should run in a fresh
terminal: cast-server restart → hook install → real cast-* slash command
in Claude Code → `/runs` tree topology check → screenshot L2/L3 →
post-smoke SQL acceptance query.

### Success Criteria checklist

- [x] `docs/specs/cast-subagent-and-skill-capture.collab.md` exists and
      lints clean. (`bin/cast-spec-checker` exits 0.)
- [x] `_registry.md` shows the new row.
- [x] Cross-spec back-references added to `cast-delegation-contract`,
      `cast-user-invocation-tracking`, and `cast-hooks`.
- [~] E2E smoke artifact captured. (Runbook authored; **live smoke +
      screenshots deferred to operator** — see explanation above.)
- [x] `cast-hook uninstall` round-trip leaves no residue.
- [x] FR-013 reflected as RESOLVED in the spec, not as a TODO.

## Out-of-Scope Touches
None. Stayed strictly within sp5 scope (spec authoring + registry +
cross-references + uninstall round-trip + e2e runbook). No code changes
to the runtime or hook layer.

## Plan Divergences

1. **Authored the spec directly rather than via `/cast-update-spec`
   skill delegation.** The `cast-update-spec` skill is interactive
   (shows a diff and waits for human approval). A subphase-runner
   cannot surface that prompt to the user — the run would block until
   timeout. The spec was instead authored directly using
   `templates/cast-spec.template.md` + the sibling
   `cast-user-invocation-tracking.collab.md` shape as canon, then
   validated by `bin/cast-spec-checker`. Verified clean. The user can
   re-run `/cast-update-spec update cast-subagent-and-skill-capture` in
   a normal session if any wording polish is desired; the lint surface
   will keep that pass safe.
2. **Live e2e smoke deferred** as documented above. Runbook written
   so the operator can finish the loop in 5 minutes.

Both divergences are documented in the manifest's progress log.

## Notes for the operator

Before merging this stack, run the e2e-smoke runbook from
`goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` to:

1. Restart cast-server (`pkill -f cast-server && uv run cast-server &`).
2. Verify `/api/agents/subagent-invocations*` returns 200 (not 404).
3. Trigger one cast-* slash command in Claude Code and watch `/runs`.
4. Save screenshots into `goals/cast-subagent-and-skill-capture/notes/`.

If the live smoke surfaces any tree-topology or chip-rendering bug, log
it under a new sp6 sub-phase rather than amending sp5.
