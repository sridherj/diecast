# Sub-phase 5: Spec capture + e2e smoke + close-out

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` and
> complete sp1-sp4 before starting.

## Outcome

New spec `docs/specs/cast-subagent-and-skill-capture.collab.md` documents
the contract; registered in `_registry.md`; `cast-spec-checker` lints
clean; an end-to-end manual smoke confirms a real Claude Code session
produces the expected tree + skill chips.

## Dependencies

- **Requires completed:** sub-phases 1-4 (spec reflects shipped
  behavior).
- **Assumed codebase state:** schema migration done, capture service
  + endpoints live, hooks installed, UI rendering chips on real data.

## Estimated effort

0.5 session.

## Scope

**In scope:**

- Author `docs/specs/cast-subagent-and-skill-capture.collab.md` via
  `/cast-update-spec` delegation.
- Lint via `/cast-spec-checker` delegation — must exit 0.
- Update `docs/specs/_registry.md` to add the new spec row.
- End-to-end manual smoke; capture screenshots into
  `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md`.
- Cross-spec back-reference in `cast-delegation-contract.collab.md`.
- Cross-spec back-reference in sibling slash-command spec
  (`cast-user-invocation-tracking.collab.md`) noting subagent rows ride
  the same `session_id` field but additionally carry `claude_agent_id`
  and use a different `source` discriminator.
- Update `cast-hooks.collab.md` (or note in new spec) covering
  per-event matcher contract.

**Out of scope (do NOT do):**

- Code changes (sp1-sp4 should have shipped everything).
- Removing the `system-ops` auto-seed contract from
  `cast-hooks.collab.md` if it's there (sibling owns).
- FR-013 from refined requirements is RESOLVED — do NOT include it as
  a TODO. Sibling already populates `agent_runs.session_id` correctly.

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `docs/specs/cast-subagent-and-skill-capture.collab.md` | Create | Via `/cast-update-spec create cast-subagent-and-skill-capture`. |
| `docs/specs/_registry.md` | Modify | Add new spec row. |
| `docs/specs/cast-delegation-contract.collab.md` | Modify | One-line back-reference noting session_id-based hook path with `claude_agent_id` closure. |
| `docs/specs/cast-user-invocation-tracking.collab.md` | Modify | One-line back-reference noting subagent rows additionally carry `claude_agent_id` and use a different `source` discriminator; constants live in `_invocation_sources.py`. |
| `docs/specs/cast-hooks.collab.md` | Modify (if needed) | Per-event matcher extension contract. |
| `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` | Create | E2E smoke screenshots + transcript. |

## Detailed Steps

### Step 5.1: Delegate `/cast-update-spec`

→ Delegate: `/cast-update-spec create cast-subagent-and-skill-capture`.

Provide context to the agent:

- This plan's path:
  `/data/workspace/diecast/docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`
- The requirements doc path (refined requirements under
  `goals/cast-subagent-and-skill-capture/`).
- FR-001..FR-013 verbatim from refined requirements **(refined
  requirements have been swept to match the post-Spike-A design — see
  Section "Spike A — empirical findings" in the source plan)**. Note
  that FR-013 is RESOLVED; should not be a TODO in the spec.
- FR-014 (`system-ops` auto-seed) verbatim.
- SC-001..SC-007 verbatim.
- The regex `^cast-[a-z0-9-]+$` (`AGENT_TYPE_PATTERN`).
- The parent-resolution rule: most-recent running cast-* row in
  `session_id` (`agent_name LIKE 'cast-%'` filter is contract).
- The closure rule: exact `claude_agent_id` match
  (`resolve_run_by_claude_agent_id`).
- The `_invocation_sources.py` constants and their use in `complete()`
  of the sibling user-invocation service. (Subagent service uses
  `claude_agent_id` exact match, so no source filter needed.)
- The `record_skill` "most-recent running cast-* row" attribution rule.
- The goal_slug inheritance rule (parent → inherited; orphan / NULL →
  `"system-ops"`).
- The `system-ops` auto-seed contract (already shipped in sibling).
- The SQLite 3.9+ floor.
- The `claude_agent_id` column-naming decision (avoids collision with
  `cast_server.models.agent_config.AgentConfig.agent_id`).
- The L2/L3 chip rules.
- The per-event matcher support contract for `install_hooks.py`.
- The fire-and-forget `_post()` semantics.
- The non-loopback `CAST_HOST` startup warning.
- The empirical payload-shapes notes file
  (`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`)
  — link as authoritative.

Verify spec output for:

- Spec maturity: Draft.
- `linked_files` lists all touched files including `_cast_name.py`,
  `_invocation_sources.py`, and `notes/payload-shapes.ai.md`.
- Behavior section covers all 8 user stories.
- Cross-references to `cast-delegation-contract.collab.md` and
  `cast-output-json-contract.collab.md` noting non-overlap.

### Step 5.2: Delegate `/cast-spec-checker`

→ Delegate:
`/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md`.

Must exit 0. If lint fails, fix the spec (or push back to
`/cast-update-spec`) and re-run.

### Step 5.3: Update `_registry.md`

Add the row (the update-spec skill should do this; if it doesn't,
append manually):

```
| `cast-subagent-and-skill-capture.collab.md` | cast-subagent-and-skill-capture | cast-server | Hook-driven capture of Task()-dispatched cast-* subagents and PreToolUse Skill events; session_id + claude_agent_id parent resolution / closure; goal_slug inheritance; system-ops auto-seed; per-event matcher support in cast-hook installer; fire-and-forget POST. Linked plan: `docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`. | Draft | 1 |
```

### Step 5.4: Cross-spec back-references

Edit `docs/specs/cast-delegation-contract.collab.md`:

- Add a one-line back-reference noting the new session_id-based hook
  path with exact `claude_agent_id` closure (does not modify any
  delegation-contract behavior; hook rows don't write delegation
  output files).

Edit `docs/specs/cast-user-invocation-tracking.collab.md` (sibling
spec):

- Add a one-line back-reference noting that subagent rows ride the
  same `session_id` field but additionally carry `claude_agent_id` and
  use a different `source` discriminator (`subagent-start` vs
  `user-prompt`). Source constants live in `_invocation_sources.py`.

Edit `docs/specs/cast-hooks.collab.md` (sibling spec) if needed:

- Note the per-event matcher extension to `install_hooks.py`. If the
  new spec covers it adequately and `cast-hooks.collab.md` has a
  "see also" section, a back-reference may suffice.

### Step 5.5: End-to-end manual smoke

In a fresh Claude Code session in this project (cast-hook installed
via `cast-hook install`):

1. Type `/cast-detailed-plan goals/<some-goal>` in Claude Code.
2. Open `http://127.0.0.1:8005/runs` in browser.
3. Watch the row tree:
   - User-invocation root row appears (sibling-managed).
   - When the slash-command harness dispatches `cast-detailed-plan`
     as a `Task()` subagent, that row appears as child via this
     plan's `SubagentStart` capture (parent_run_id resolved via
     `resolve_parent_for_subagent`).
   - `cast-detailed-plan`'s auto-trigger of `cast-plan-review`
     appears as grandchild (HTTP-dispatched, sibling-managed).
   - Skill chips appear on whichever cast-* row was
     most-recent-running when each Skill invocation happened.
   - `SubagentStop` flips each subagent row to `completed` via
     exact `claude_agent_id` match.
4. Capture screenshots into
   `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md`
   for the audit trail.

### Step 5.6: Uninstall round-trip

```bash
mkdir -p /tmp/cast-hook-uninstall-test-$$/.claude
cd /tmp/cast-hook-uninstall-test-$$
# Seed with a known third-party hook entry on SubagentStart and PreToolUse
cat > .claude/settings.json <<'EOF'
{
  "hooks": {
    "SubagentStart": [{"hooks":[{"type":"command","command":"third-party-hook x","timeout":3}]}],
    "PreToolUse":    [{"matcher":"Bash","hooks":[{"type":"command","command":"third-party-bash-watch","timeout":3}]}]
  }
}
EOF
cp .claude/settings.json /tmp/seed-$$.json

cast-hook install
cast-hook uninstall

diff <(jq -S . .claude/settings.json) <(jq -S . /tmp/seed-$$.json)
# Expected: no diff — all 5 cast-hook entries removed; third-party SubagentStart and PreToolUse(matcher=Bash) untouched.
```

## Verification

### Automated Tests (permanent)

- `bin/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md`
  exits 0.

### Manual Checks

- `_registry.md` shows the new row.
- E2E smoke (Step 5.5): user-invocation root → subagent child →
  grandchild visible in `/runs`; skill chips on appropriate rows;
  subagent rows flip to `completed` on `SubagentStop`.
- Uninstall round-trip (Step 5.6): all 5 hook entries removed; nothing
  else touched.

### Success Criteria

- [ ] `docs/specs/cast-subagent-and-skill-capture.collab.md` exists and
      lints clean.
- [ ] `_registry.md` shows the new row.
- [ ] Cross-spec back-references added to
      `cast-delegation-contract`, `cast-user-invocation-tracking`,
      and `cast-hooks` (where applicable).
- [ ] E2E smoke artifact (`e2e-smoke.ai.md`) captured with screenshots.
- [ ] `cast-hook uninstall` round-trip leaves no residue.
- [ ] FR-013 is reflected as RESOLVED in the spec, not as a TODO.

## Design Review

- **Spec creation post-implementation** is acceptable here because the
  contract was already locked in the refined requirements (which
  `cast-spec-checker` already linted clean) and the implementation is
  small. ✓
- **Naming:** spec slug matches goal slug. ✓
- **Architecture:** registers via canonical `_registry.md` row; no
  special handling. ✓

## Execution Notes

- **Skill/agent delegation is mandatory** for the spec author/lint
  loop. Don't hand-author the spec — let `/cast-update-spec` produce a
  template-conformant document and `/cast-spec-checker` lint it.
- **E2E smoke needs cast-server running** with the latest code from
  sp1-sp4; verify before starting Claude Code.
- **Screenshot discipline:** capture the L2 chip view AND the L3
  detail view for at least one row. Show the parent/child/grandchild
  tree expanded.
- **Don't auto-resolve open questions** during spec authoring. If
  `/cast-update-spec` flags a behavior the plan doesn't cover,
  surface to the user before committing.
- **Spike A authoritativeness:** if `/cast-update-spec` proposes
  language inconsistent with the empirical payload shapes (e.g.
  re-introducing `parent_session_id` or `tool_input.skill_name`),
  reject and force the agent to read
  `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`.
