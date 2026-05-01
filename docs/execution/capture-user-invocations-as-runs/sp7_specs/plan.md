# Sub-phase 7: Spec Capture (Two Specs)

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Author two new specs that lock the contracts shipped in sp1–sp6:

1. `docs/specs/cast-user-invocation-tracking.collab.md` — the user-invocation lifecycle
   contract (HTTP endpoints, row shape, close-by-session semantics, staleness window).
2. `docs/specs/cast-hooks.collab.md` — the polite-citizen hook install/uninstall
   contract. **Critical user-safety spec.** Lead with the polite-citizen framing.

Update `docs/specs/_registry.md` with rows for both. Add a back-reference from
`docs/specs/cast-delegation-contract.collab.md` noting that user-invocation rows are now
a recognized top-level kind.

## Dependencies

- **Requires completed:** sp1–sp6. Specs reflect actual shipped behavior, not aspiration.
- **Assumed codebase state:** Spec template exists at `templates/cast-spec.template.md`.
  `docs/specs/_registry.md` exists with rows in markdown table format.

## Scope

**In scope:**
- Two new spec files at `docs/specs/cast-user-invocation-tracking.collab.md` and
  `docs/specs/cast-hooks.collab.md`.
- Two new rows in `docs/specs/_registry.md`.
- Back-reference in `docs/specs/cast-delegation-contract.collab.md`.
- Run `/cast-spec-checker` against each new spec; address findings.

**Out of scope (do NOT do these):**
- Modifying any code module (sp1–sp6 already shipped them).
- Adding behaviors not implemented in sp1–sp6.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-user-invocation-tracking.collab.md` | Create | Does not exist |
| `docs/specs/cast-hooks.collab.md` | Create | Does not exist |
| `docs/specs/_registry.md` | Modify | Has registry table |
| `docs/specs/cast-delegation-contract.collab.md` | Modify (1 line) | Existing spec |

## Detailed Steps

### Step 7.1: Read the spec template + registry conventions

```bash
cat templates/cast-spec.template.md
cat docs/specs/_registry.md | head -30
ls docs/specs/
```

Match the template's section ordering, frontmatter, and behavior-table conventions
exactly. Read one or two existing specs (e.g., `cast-delegation-contract.collab.md`) to
calibrate voice and format.

### Step 7.2: Author Spec A — `cast-user-invocation-tracking.collab.md`

**Delegate: `/cast-update-spec create cast-user-invocation-tracking`** (this is the
canonical invocation per the plan's Spec capture section). Pass it the following content
spine:

**Intent (one paragraph):**

> Cast-server captures every user-typed `/cast-*` slash command as a top-level
> `agent_run` row whose `agent_name` matches the slash command. Lifecycle is bracketed
> by Claude Code's `UserPromptSubmit` and `Stop` hooks. The Stop endpoint closes by
> `session_id` with a 1-hour staleness window — self-healing for orphans without
> ghost-running rows. Children of in-turn dispatches are NOT auto-linked to the
> user-invocation row in v1.

**Linked files:**
- This plan: `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`
- `cast-server/cast_server/services/user_invocation_service.py`
- `cast-server/cast_server/cli/hook_handlers.py`
- `cast-server/cast_server/routes/api_agents.py` (the two new endpoints)
- `cast-server/cast_server/db/connection.py` (the new index)

**User Stories:**
- **US1:** Slash-command invocation creates a row. `/cast-plan-review` →
  `agent_name="cast-plan-review"`, `status="running"`, `input_params.source="user-prompt"`,
  `session_id` set, `parent_run_id=null`.
- **US2:** Lifecycle closes — Stop transitions the row to `status="completed"`,
  `completed_at` set.
- **US3:** Non-cast prompts are ignored. Freeform prompts and non-cast slash commands
  produce no rows.
- **US4:** Crashed-session orphans self-heal. Stop in a session containing a stale
  `running` row from a prior crashed turn cleans it up alongside the current row, **only
  if started within the past hour**.
- **US5:** Multiple invocations per session work. Many `/cast-*` invocations in one
  Claude Code session each get their own row, sequentially opened and closed.
- **US6:** Children stay top-level. Agent dispatches that occur during a `/cast-*` turn
  are NOT auto-linked as children; correlation is by `session_id` + timestamps only.

**Behavior contract:**
- `agent_name` convention: slash command name without the leading slash.
- Discriminator: `input_params.source == "user-prompt"`. No new column.
- Detection regex (hook-side only): `^\s*/(cast-[a-z0-9-]+)`. Server is agnostic to
  prefix.
- Close-by-session query (Decision #4):
  ```
  UPDATE agent_runs SET status='completed', completed_at=?
   WHERE session_id=?
     AND status='running'
     AND json_extract(input_params,'$.source')='user-prompt'
     AND started_at > <now − 1h>
  ```
- Index: `idx_agent_runs_session_status ON agent_runs(session_id, status)`.
- Stop semantics: `completed` always; v1 does not detect cancellation.
- Endpoint failure semantics: `/complete` with missing/empty `session_id` → `{closed: 0}`,
  not an error.

**Verification:** cite `tests/test_user_invocation_service.py`, `tests/test_api_agents.py`
(the new cases), `tests/test_cli_hook.py`.

**Out of scope:** mirror the plan's Out-of-scope list.

**Cross-reference:** "Hook installation contract: see `cast-hooks.collab.md`."

### Step 7.3: Author Spec B — `cast-hooks.collab.md` (CRITICAL USER-SAFETY SPEC)

**Delegate: `/cast-update-spec create cast-hooks`**

Lead with the polite-citizen framing.

**Intent (one paragraph):**

> Cast-server installs Claude Code hooks via the `cast-hook install` command. The
> installer is a *polite citizen* in the user's `.claude/settings.json` — it is one
> listener among potentially many. It NEVER replaces or breaks third-party or
> pre-existing user hooks; it only appends its own entries (idempotent) and surgically
> removes them on `cast-hook uninstall`. All writes are atomic; malformed JSON refuses to
> overwrite; permission errors surface a readable message instead of a traceback.

**Linked files:**
- This plan: `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`
- `cast-server/cast_server/cli/install_hooks.py`
- `cast-server/cast_server/cli/hook_events.py`
- `cast-server/cast_server/cli/hook.py`
- `pyproject.toml` (`[project.scripts]` entry)
- Reference: `~/workspace/reference_repos/gstack/bin/gstack-settings-hook` (canonical pattern)

**User Stories (10):**
- **US1:** Coexists with third-party `UserPromptSubmit` hooks — installing into a
  settings.json that already has a third-party `UserPromptSubmit` entry leaves that
  entry verbatim; our entry coexists in the same array; both fire on every prompt.
- **US2:** Coexists with third-party `Stop` hooks — symmetric to US1.
- **US3:** Preserves all unrelated events — `PostToolUse`, `SubagentStart`,
  `SessionEnd`, `PreCompact`, etc. are untouched.
- **US4:** Idempotent install — re-running `cast-hook install` is a no-op.
- **US5:** Surgical uninstall — removes ONLY entries whose `command` starts with
  `cast-hook ` (the marker). Other entries, other events, and the rest of `settings.json`
  are byte-for-byte preserved. Newly-empty event arrays dropped; if `hooks` is empty,
  that key is dropped too.
- **US6:** Refuses to corrupt malformed settings — installer aborts with readable error
  if `.claude/settings.json` is invalid JSON. Does NOT write.
- **US7:** Survives filesystem failures gracefully — `OSError`/`PermissionError`
  (read-only fs, disk full, locked file) surfaces a readable message; the `.tmp` file is
  cleaned up; original settings file untouched.
- **US8:** Atomic on disk — partial writes never reach the live `settings.json`.
  mkstemp + write + `os.replace`.
- **US9:** Project-aware — installs to `<project_root>/.claude/settings.json` by default.
  `--user` writes to `~/.claude/settings.json`. Warns (does not block) if cwd lacks
  `.git`/`.cast`/`pyproject.toml`/`package.json` markers.
- **US10:** Single source of truth for hook events — `cli/hook_events.py` is the only
  place that knows {event, subcommand, handler}; install-side and runtime-side cannot
  drift.

**Behavior contract:**
- `HOOK_MARKER = "cast-hook "` (trailing space). Any settings.json
  `hooks[*].hooks[*].command` starting with this prefix is "ours".
- Hook command shape: `cast-hook <subcommand>`. PATH-resolved. No hardcoded filesystem
  paths in any user's settings.json.
- Atomic write: `tempfile.mkstemp` + write + `os.replace`. tmp file cleaned on exception
  (success or failure).
- Failure semantics:
  - Malformed JSON in target → `SystemExit` with readable message; exit non-zero;
    no write.
  - `OSError`/`PermissionError` → `SystemExit` with readable message naming `--user`
    as the workaround; exit non-zero.
  - Settings file missing on uninstall → `print "nothing to do"`; exit 0.
- Idempotency marker: any `command` starting with `HOOK_MARKER` is ours.
- Concurrency: not handled. Documented limitation.

**Verification:** cite `tests/test_install_hooks.py` (gating coverage). Spec calls out
the **module-level autouse isolation fixture** (Decision #8) as a non-negotiable safety
property of the test suite.

**Out of scope:**
- File locking on settings.json (matches gstack stance).
- Auto-uninstall on package removal.
- Multi-machine routing.

**Cross-reference:** "User-invocation lifecycle uses these hooks: see
`cast-user-invocation-tracking.collab.md`."

### Step 7.4: Update `_registry.md`

Append two rows:

```
| `cast-user-invocation-tracking.collab.md` | cast-user-invocation-tracking | cast-server | User-typed /cast-* slash commands captured as top-level agent_run rows; close-by-session_id with 1h staleness window. Linked plan: `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`. Hook install: see `cast-hooks.collab.md`. | Draft | 1 |
| `cast-hooks.collab.md`                    | cast-hooks                    | cast-server | Polite-citizen install/uninstall contract for Claude Code settings.json. Additive merge, atomic write, idempotent dedup, surgical uninstall, third-party preservation. Reference pattern: gstack-settings-hook. | Draft | 1 |
```

Confirm column alignment matches the rest of the table.

### Step 7.5: Add back-reference in `cast-delegation-contract.collab.md`

Locate the section that enumerates run kinds (top-level vs subprocess) and add:

> **Note:** User-invocation rows (created by user-typed `/cast-*` slash commands) are now
> a recognized top-level kind. They are distinguished by
> `input_params.source == "user-prompt"`. See `cast-user-invocation-tracking.collab.md`
> for the lifecycle contract.

If no obvious section exists, add a short cross-references block at the end.

### Step 7.6: Lint specs

For each new spec:

```bash
# Delegate to spec-checker
```

> Delegate: `/cast-spec-checker` against `docs/specs/cast-user-invocation-tracking.collab.md`
> Delegate: `/cast-spec-checker` against `docs/specs/cast-hooks.collab.md`

Address any findings.

## Verification

### Automated Tests (permanent)

None added in this sub-phase. The specs reference tests already authored in sp1–sp6.

### Validation Scripts (temporary)

```bash
# Confirm both new specs exist
ls -la docs/specs/cast-user-invocation-tracking.collab.md docs/specs/cast-hooks.collab.md

# Confirm registry has both rows
grep -c "cast-user-invocation-tracking\|cast-hooks" docs/specs/_registry.md
# Should be at least 2

# Confirm cross-references
grep -n "cast-hooks.collab.md" docs/specs/cast-user-invocation-tracking.collab.md
grep -n "cast-user-invocation-tracking" docs/specs/cast-hooks.collab.md
grep -n "cast-user-invocation-tracking" docs/specs/cast-delegation-contract.collab.md
```

### Manual Checks

- Spec A's User Stories enumerate exactly 6 stories matching the plan's spec section.
- Spec B's User Stories enumerate exactly 10 stories matching the plan's spec section.
- Spec B leads with the polite-citizen framing in its Intent.
- `_registry.md` rows are in correct column order with `Draft | 1` versioning.
- `/cast-spec-checker` passes on both specs.

### Success Criteria

- [ ] `cast-user-invocation-tracking.collab.md` exists, follows template, has 6 user
      stories.
- [ ] `cast-hooks.collab.md` exists, follows template, has 10 user stories, leads with
      polite-citizen framing.
- [ ] `_registry.md` has both new rows.
- [ ] `cast-delegation-contract.collab.md` has the back-reference.
- [ ] `/cast-spec-checker` passes on both new specs.
- [ ] Each spec's "Verification" section cites the actual test files shipped in
      sp1–sp6.
- [ ] No code under `cast-server/` was modified in this sub-phase.

## Execution Notes

- **Decision #11 + plan's "Spec capture" section:** the two-spec split is deliberate.
  Hook install is critical user-safety surface that deserves its own contract independent
  of any one feature using it. **Do not merge these into one spec.**
- **Skill/agent delegation:** `/cast-update-spec create <name>` is the canonical
  authoring path. `/cast-spec-checker` is the canonical lint path. Use both — manual
  authoring should only fill gaps the skills can't cover.
- The plan calls out the autouse isolation fixture (sp5) as a "non-negotiable safety
  property" — Spec B should reflect that explicitly in its Verification or Behavior
  section.
- If `templates/cast-spec.template.md` doesn't exist, fall back to copying an existing
  spec's structure (e.g., `cast-delegation-contract.collab.md`).
