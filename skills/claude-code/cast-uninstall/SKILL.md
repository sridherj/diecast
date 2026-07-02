---
name: cast-uninstall
model: sonnet
description: >
  Remove an installed Diecast: back up (never hard-delete) and remove
  `cast-*` skills, `cast-*` agents, the `~/.claude/skills/diecast` symlink,
  cast-hook settings.json entries, and optionally `~/.cast/` (config + the
  run database) and `~/.cache/diecast/` (logs), based on a scope the user
  picks. The lifecycle counterpart to `./setup` / `/cast-upgrade` — same
  install seam, same `.cast-bak-<ts>/` backup primitive, so every removal
  is reversible until backups are pruned. Never touches non-`cast-*`
  skills/agents (e.g. any sibling ecosystem installed alongside Diecast) or
  the diecast git repository itself.
trigger_phrases:
  - /cast-uninstall
  - uninstall Diecast
  - uninstall cast
  - remove Diecast
  - remove cast skills
  - teardown Diecast
license: Apache-2.0
metadata:
  spec: docs/specs/cast-delegation-contract.collab.md
  version: "1.0"
---

# /cast-uninstall

Remove an installed Diecast from this machine. The skill is the lifecycle
counterpart to `./setup` and `/cast-upgrade`: same install seam, same
`.cast-bak-<ts>/` backup primitive (`cast_server.bootstrap.common.backup_if_exists`
moves a path into the backup root rather than deleting it), same
anonymization-aware `cast-*` naming convention. Nothing this skill removes is
gone for good until `prune_old_backups()` (5-newest-kept, shared with
`./setup`) ages the backup out.

**Only `cast-*`-prefixed skills and agents are ever touched.** Any sibling
ecosystem installed on the same machine under a different prefix is out of
scope and MUST NOT be listed, backed up, or removed by this skill.

**The diecast git repository (the clone `./setup` was run from) is never
touched.** This skill only removes things `./setup` wrote outside the repo:
`~/.claude/agents/cast-*`, `~/.claude/skills/cast-*`, the
`~/.claude/skills/diecast` symlink, cast-hook `settings.json` entries, and
(opt-in) `~/.cast/` and `~/.cache/diecast/`. If the user also wants the
source checkout gone, tell them to `rm -rf` it themselves — that is
explicitly not this skill's job.

## Delegation pattern

`/cast-uninstall` delegates **two** interactive prompts to
[`cast-interactive-questions`](../cast-interactive-questions/SKILL.md),
per [`docs/specs/cast-delegation-contract.collab.md`](../../../docs/specs/cast-delegation-contract.collab.md):
one question at a time, lettered options, recommendation first. Do **not**
ask either question with plain conversational text.

1. The 3-option scope prompt (Step 3 below).
2. The active-runs confirm prompt (Step 4 below) — only when `cast-server`
   is running with active runs.

## Procedure

### Step 1: Locate the repo (best-effort; not required)

Uninstall does not need the repo to succeed — everything it removes lives
under `~/.claude`, `~/.cast`, `~/.cache/diecast`. But `bin/cast-hook` (used
in Step 6) is resolved via the `~/.claude/skills/diecast` symlink, so no
repo lookup is actually required either. Skip repo discovery entirely;
resolve `cast-hook` as `~/.claude/skills/diecast/bin/cast-hook`.

### Step 2: Enumerate what's installed

```bash
HOME_CLAUDE="$HOME/.claude"
AGENTS=$(find "$HOME_CLAUDE/agents" -maxdepth 1 -type d -name 'cast-*' 2>/dev/null | sort)
SKILLS=$(find "$HOME_CLAUDE/skills" -maxdepth 1 -type d -name 'cast-*' 2>/dev/null | sort)
SYMLINK_PRESENT=0
[[ -L "$HOME_CLAUDE/skills/diecast" ]] && SYMLINK_PRESENT=1
LEGACY_SHIM_PRESENT=0
[[ -e "$HOME/.local/bin/cast-server" ]] && LEGACY_SHIM_PRESENT=1

HOOK_PROJECT=0
[[ -f "$(pwd)/.claude/settings.json" ]] && grep -qF "$HOME_CLAUDE/skills/diecast/bin/cast-hook " "$(pwd)/.claude/settings.json" 2>/dev/null && HOOK_PROJECT=1
HOOK_USER=0
[[ -f "$HOME_CLAUDE/settings.json" ]] && grep -qF "$HOME_CLAUDE/skills/diecast/bin/cast-hook " "$HOME_CLAUDE/settings.json" 2>/dev/null && HOOK_USER=1

CAST_DIR_PRESENT=0
[[ -d "$HOME/.cast" ]] && CAST_DIR_PRESENT=1
CACHE_DIR_PRESENT=0
[[ -d "$HOME/.cache/diecast" ]] && CACHE_DIR_PRESENT=1

SERVER_PID=$(pgrep -f cast-server || true)
```

Print a short summary before asking anything, e.g.:

```text
[cast] Found: 62 agents, 58 skills, diecast symlink, cast-hook entries
       (project + user), ~/.cast/ (config + run database), ~/.cache/diecast/
       (logs), cast-server running (pid 41213).
```

If **nothing** `cast-*`-prefixed is found under `~/.claude/{agents,skills}`
and no `~/.cast/` directory exists, exit early:

```text
[cast] Nothing to uninstall — no cast-* skills, agents, or ~/.cast/ found.
```

### Step 3: Scope prompt (delegated)

→ **Delegate to** [`cast-interactive-questions`](../cast-interactive-questions/SKILL.md).
Surface with these **verbatim** option labels (substitute the counts from
Step 2):

> Remove Diecast. What should go?
>
> A. Skills & agents only — <N> agents, <M> skills, the diecast symlink.
>    Keeps `~/.cast/config.yaml`, your run database, and cast-hook entries.
>    A future `./setup` restores instantly.
> B. Skills, agents & hooks — everything in A, plus cast-hook entries
>    removed from project and user `settings.json`. Diecast stops capturing
>    runs. Config and database are kept.
> C. Full wipe — everything in B, plus `~/.cast/` (config + run database)
>    and `~/.cache/diecast/` (logs). Nothing of Diecast left on this
>    machine except the git repo you cloned.

Recommendation: **A**, unless the user says they're done with Diecast
entirely (then **C**). Everything each option removes is moved into
`~/.claude/.cast-bak-<ts>/`, not deleted — say so if the user hesitates
over B or C.

| Option | Removes |
| ------ | ------- |
| A. Skills & agents only | `~/.claude/agents/cast-*`, `~/.claude/skills/cast-*`, `~/.claude/skills/diecast` symlink |
| B. + hooks | A, plus `cast-hook uninstall` (project scope) and `cast-hook uninstall --user` |
| C. Full wipe | B, plus `~/.cast/` and `~/.cache/diecast/`, plus the legacy `~/.local/bin/cast-server` shim if still present |

### Step 4: Active-runs check (delegated, conditional)

Only when `SERVER_PID` from Step 2 is non-empty:

```bash
RUNS=$(curl -s --max-time 2 "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/runs?status=running" || echo '[]')
ACTIVE_COUNT=$(echo "$RUNS" | jq 'length' 2>/dev/null || echo 0)
```

If `ACTIVE_COUNT` > 0, delegate to `cast-interactive-questions`:

> There are `<ACTIVE_COUNT>` active run(s) in flight. Uninstalling stops
> `cast-server`, which kills them. Continue?
>
> A. Stop cast-server and continue
> B. Cancel

Recommendation: **B** unless the user explicitly wants to interrupt. If
`curl` fails (server not actually reachable despite the pgrep match), treat
as zero active runs and proceed without a prompt.

### Step 5: Stop cast-server

```bash
if [[ -n "$SERVER_PID" ]]; then
  kill "$SERVER_PID" 2>/dev/null || true
  for _ in $(seq 1 10); do
    kill -0 "$SERVER_PID" 2>/dev/null || break
    sleep 0.5
  done
  kill -0 "$SERVER_PID" 2>/dev/null && kill -9 "$SERVER_PID" 2>/dev/null || true
fi
```

SIGTERM first, escalate to SIGKILL only if it's still alive after ~5s —
same graceful-then-force pattern as the port-kill discipline used elsewhere
in Diecast tooling. Skip entirely if `SERVER_PID` was empty in Step 2.

### Step 6: Remove, by scope

All removal uses `backup_if_exists()` (`cast_server.bootstrap.common`) — a
**move**, not a delete — into the shared `~/.claude/.cast-bak-<ts>/` root
(same primitive `./setup` and `/cast-upgrade` use). Freeze one timestamp for
the whole run.

**Scope A, B, and C (always):**

```bash
for d in $AGENTS; do backup_if_exists "$d"; done   # ~/.claude/agents/cast-*
for d in $SKILLS; do backup_if_exists "$d"; done   # ~/.claude/skills/cast-*

# The symlink itself is not backed up (it only points at the repo, which
# is untouched) — just unlink it.
[[ -L "$HOME_CLAUDE/skills/diecast" ]] && rm "$HOME_CLAUDE/skills/diecast"
```

**Scope B and C (add):**

```bash
CAST_HOOK="$HOME_CLAUDE/skills/diecast/bin/cast-hook"
# Resolve cast-hook BEFORE the symlink removal above breaks the path —
# reorder: run this block first if scope includes hooks, or cache the
# resolved binary's realpath before Step 6's symlink removal runs.
[[ -x "$CAST_HOOK" ]] && "$CAST_HOOK" uninstall
[[ -x "$CAST_HOOK" ]] && "$CAST_HOOK" uninstall --user
```

`cast-hook uninstall` only strips entries whose `command` starts with the
`cast-hook` marker — third-party hooks in the same `settings.json` are left
byte-for-byte untouched (same polite-citizen guarantee `install`/`uninstall`
share). If the symlink was already removed by the always-block above,
resolve `cast-hook` first via `readlink` before unlinking, or simply run
this block **before** the symlink removal when scope is B or C.

**Scope C only (add):**

```bash
backup_if_exists "$HOME/.cast"              # config.yaml + diecast.db + upgrade.lock
backup_if_exists "$HOME/.cache/diecast"     # bootstrap.log, server.log
[[ -e "$HOME/.local/bin/cast-server" ]] && backup_if_exists "$HOME/.local/bin/cast-server"
```

`~/.cast/diecast.db` is the run/goal/task database — flag this explicitly
before scope C proceeds if the user hasn't already been told (Step 3's
option C description covers it, but re-confirm in plain language if the
count of runs/goals is nonzero and easily checkable).

### Step 7: Prune old backups

```bash
prune_old_backups(keep=5)   # cast_server.bootstrap.common — shared policy with ./setup
```

Uninstall backups and install backups live in the same `.cast-bak-*`
namespace and age out together under the same 5-newest-kept retention. No
separate uninstall-specific retention policy.

### Step 8: Summary + next steps

```text
[cast] Uninstall complete (scope: <A|B|C>).
       Backed up to ~/.claude/.cast-bak-<ts>/ — nothing was deleted.
```

Emit typed `next_steps` per the
[US14 contract](../../../tests/fixtures/next_steps.schema.json):

```json
[
  {
    "command": "./setup",
    "rationale": "Reinstall Diecast from this clone — instant if backups weren't pruned, since config/hooks were left in place for scope A/B.",
    "artifact_anchor": null
  },
  {
    "command": "ls ~/.claude/.cast-bak-<ts>/",
    "rationale": "Inspect exactly what was removed before it ages out of the 5-newest-kept backup retention.",
    "artifact_anchor": null
  }
]
```

For scope C, add a third entry noting the repo checkout itself is
untouched and can be removed manually if the user wants Diecast fully gone.

### Step 9: Failure path

Because every removal in Step 6 is a **move**, a mid-run failure never
destroys data — it just leaves some `cast-*` paths already moved into
`~/.claude/.cast-bak-<ts>/` and others not yet touched. On any step
failure:

```text
[cast] Uninstall stopped partway (scope: <A|B|C>) after: <last completed sub-step>.
       Nothing was lost — everything moved so far is under
       ~/.claude/.cast-bak-<ts>/. Re-run /cast-uninstall to finish, or
       restore manually with: cp -R ~/.claude/.cast-bak-<ts>/* ~/
```

No stash/pop dance is needed here (unlike `/cast-upgrade`'s Step 12) —
uninstall never touches the git repo, so there is no repo-side state to
restore.

## Flags

```bash
/cast-uninstall --dry-run          # print the action plan (per Step 2's enumeration + chosen scope); touch nothing
/cast-uninstall --scope=agents-skills   # non-interactive: skip Step 3, use scope A
/cast-uninstall --scope=hooks           # non-interactive: skip Step 3, use scope B
/cast-uninstall --scope=full            # non-interactive: skip Step 3, use scope C
/cast-uninstall --force            # skip Step 4's active-runs confirm; still stops cast-server
```

`--scope=...` and `--force` exist for CI / non-interactive teardown (mirrors
`./setup --no-prompt`); everyday interactive use should go through Step 3's
prompt rather than a flag.

## Spec cross-references

- **Delegation pattern:**
  [`docs/specs/cast-delegation-contract.collab.md`](../../../docs/specs/cast-delegation-contract.collab.md)
  governs every `cast-interactive-questions` invocation in this skill.
- **Output JSON shape:**
  [`docs/specs/cast-output-json-contract.collab.md`](../../../docs/specs/cast-output-json-contract.collab.md)
  governs the typed `next_steps` array.
- **Backup primitive:** `cast_server.bootstrap.common.backup_if_exists` /
  `backup_root` / `prune_old_backups` — the same functions `./setup`'s
  `step3_install_agents` / `step4_install_skills` and `/cast-upgrade`'s
  failure-path restore use. This skill introduces no new backup mechanism.
- **cast-hook uninstall:** `cast-server/cast_server/cli/install_hooks.py::uninstall` —
  the polite-citizen settings.json entry remover this skill calls in
  scope B/C, unchanged.
