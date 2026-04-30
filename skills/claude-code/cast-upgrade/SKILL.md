---
name: cast-upgrade
model: sonnet
description: >
  Upgrade Diecast: pull latest upstream, preserve local skill modifications via
  `git stash` + `.cast-bak-<ts>/`, restart `cast-server`. Supports auto-upgrade,
  snooze backoff (24h / 48h / 1 week), and silent skip when the user has opted
  out. On any-step failure, restores `~/.claude/` from the latest `.cast-bak-*`
  directory and pops the repo stash so the user is never left worse-off than
  before the upgrade ran.
trigger_phrases:
  - /cast-upgrade
  - upgrade Diecast
  - update cast
  - is there a new version
  - upgrade cast
license: Apache-2.0
metadata:
  spec: docs/specs/cast-delegation-contract.collab.md
  version: "1.0"
---

# /cast-upgrade

Upgrade an installed Diecast to the latest published `main`, preserve any
local edits the user has made under `~/.claude/skills/cast-*/`, and restart
`cast-server` if it was running. The skill is the lifecycle counterpart to
`./setup`: same install seam, same backup primitive (`.cast-bak-<ts>/`),
same anonymization gate. The only operation it adds on top of `./setup` is
**`git pull --ff-only`** in the repo and **stash discipline** for any local
repo edits the user has made.

## Delegation pattern

`/cast-upgrade` delegates **two** interactive prompts to
[`cast-interactive-questions`](../cast-interactive-questions/SKILL.md):

1. The 4-option upgrade prompt (Step 7 below).
2. The active-runs confirm prompt (Step 8 below).

Both follow the protocol in
[`docs/specs/cast-delegation-contract.collab.md`](../../../docs/specs/cast-delegation-contract.collab.md):
one question at a time, lettered options, recommendation first. Do **not**
ask either question with plain conversational text — always go through
`cast-interactive-questions`.

## Configuration keys consumed

Read from `~/.cast/config.yaml` (canonical schema in
[`docs/config.md`](../../../docs/config.md)):

| Key                      | Effect                                                                           |
| ------------------------ | -------------------------------------------------------------------------------- |
| `auto_upgrade`           | If `true`, skip Step 7's prompt and go straight to the upgrade procedure.        |
| `upgrade_snooze_until`   | If set and in the future, exit silently with a snooze-active message.            |
| `upgrade_snooze_streak`  | 0 / 1 / 2+ → next snooze duration (24h / 48h / 168h). Capped at 3.               |
| `upgrade_never_ask`      | If `true`, exit silently with no prompt and no upgrade.                          |
| `last_upgrade_check_at`  | ISO-8601 cache of the last `git ls-remote` call. 1-hour TTL.                     |

If a key is missing from `~/.cast/config.yaml`, treat it as the default in
the schema. The skill only **writes** keys it actually changes — it never
overwrites unrelated keys.

## Procedure

The repo path is fixed: `<repo>` is the directory `./setup` was run from.
The skill discovers it by walking up from `~/.claude/skills/cast-upgrade/`
to find the nearest ancestor that is a git work-tree, falling back to the
location stored in `~/.cast/config.yaml::repo_path` if recorded there. If
neither resolves, abort with: `Cannot locate the Diecast repo. Run ./setup
from a fresh clone first.`

The `--force` flag (documented at the bottom of this file) skips Step 3's
snooze gate. It does **not** clear the snooze state.

### Step 1: Acquire the concurrent-invocation lock

```bash
LOCK_FILE="$HOME/.cast/upgrade.lock"
mkdir -p "$(dirname "$LOCK_FILE")"
if ! ( set -o noclobber; : > "$LOCK_FILE" ) 2>/dev/null; then
  echo "[cast] Another upgrade is in progress (lock at $LOCK_FILE)."
  echo "[cast] If you are sure no other upgrade is running, remove the lock and retry."
  exit 0
fi
trap 'rm -f "$LOCK_FILE"' EXIT
```

The `noclobber` redirect is the bash-portable equivalent of `O_EXCL`. The
`trap EXIT` ensures the lock is released on every code path, including the
failure path in Step 12.

### Step 2: Cache check (1h TTL)

Read `~/.cast/config.yaml::last_upgrade_check_at`. If it is a valid
ISO-8601 timestamp less than one hour in the past **and** the cached
result was "up to date", exit silently with `[cast] Already up to date
(cached).`. Otherwise fall through to the network check; do not skip the
check just because the cache is fresh — only skip when the cache says
there was nothing to do.

### Step 3: Snooze gate

```bash
SNOOZE_UNTIL=$(yq '.upgrade_snooze_until // ""' ~/.cast/config.yaml)
if [[ -n "$SNOOZE_UNTIL" && "$SNOOZE_UNTIL" != "null" ]]; then
  if [[ "$(date -u +%Y-%m-%dT%H:%M:%SZ)" < "$SNOOZE_UNTIL" ]]; then
    if [[ "${FORCE:-0}" != "1" ]]; then
      echo "[cast] Snoozed until $SNOOZE_UNTIL — run /cast-upgrade --force to override."
      exit 0
    fi
  fi
fi
```

`--force` skips the gate but does **not** clear `upgrade_snooze_until` or
`upgrade_snooze_streak`. The user's snooze preference survives an
override so the next un-forced invocation honors it again.

### Step 4: Never-ask gate

```bash
NEVER=$(yq '.upgrade_never_ask // false' ~/.cast/config.yaml)
if [[ "$NEVER" == "true" ]]; then
  exit 0
fi
```

To re-enable upgrade prompts, the user edits `~/.cast/config.yaml` and
sets `upgrade_never_ask: false`. (A `/cast-upgrade --reset` flag is
deferred to v1.1.)

### Step 5: Upgrade-available detection

```bash
LOCAL_SHA=$(git -C "$REPO" rev-parse HEAD)
REMOTE_SHA=$(git -C "$REPO" ls-remote origin main | awk '{print $1}')

# Always update the cache timestamp, regardless of result.
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
yq -i ".last_upgrade_check_at = \"$NOW\"" ~/.cast/config.yaml

if [[ "$LOCAL_SHA" == "$REMOTE_SHA" ]]; then
  echo "[cast] Already up to date (commit $LOCAL_SHA)."
  exit 0
fi
```

If `git ls-remote` fails (offline, GitHub down, etc.), surface the error
and exit non-zero. Do **not** retry silently.

### Step 6: Auto-upgrade skip

```bash
AUTO=$(yq '.auto_upgrade // false' ~/.cast/config.yaml)
if [[ "$AUTO" == "true" ]]; then
  echo "[cast] Auto-upgrading $LOCAL_SHA → $REMOTE_SHA…"
  # Skip Step 7; jump to Step 8.
fi
```

### Step 7: 4-option AskUserQuestion (delegated)

→ **Delegate to** [`cast-interactive-questions`](../cast-interactive-questions/SKILL.md).
Surface the question with these **verbatim** option labels:

> Diecast `<remote_short_sha>` is available (you're on `<local_short_sha>`). Upgrade now?
>
> A. Yes, upgrade now
> B. Always keep me up to date
> C. Not now
> D. Never ask again

Recommendation: **A**, unless the user is mid-task with a long-running
agent (Step 8 will catch this anyway), in which case **C**.

| Option                       | Effect                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------ |
| A. Yes, upgrade now          | Proceed to Step 8.                                                                               |
| B. Always keep me up to date | `yq -i '.auto_upgrade = true' ~/.cast/config.yaml`, then proceed to Step 8.                      |
| C. Not now                   | Apply the snooze backoff state machine (Step 9), then exit 0 with `[]` next_steps (US14 OK).     |
| D. Never ask again           | `yq -i '.upgrade_never_ask = true' ~/.cast/config.yaml`, then exit 0.                            |

Do **not** reword the option labels. Diecast users coming from sibling
ecosystems will recognise the surface; consistency reduces friction.

### Step 8: Active-runs check

```bash
SERVER_PID=$(pgrep -f cast-server || true)
if [[ -n "$SERVER_PID" ]]; then
  RUNS=$(curl -s --max-time 2 'http://localhost:8000/api/agents/runs?status=running' || echo '[]')
  ACTIVE_COUNT=$(echo "$RUNS" | jq 'length' 2>/dev/null || echo 0)
  if [[ "$ACTIVE_COUNT" -gt 0 ]]; then
    # Delegate to cast-interactive-questions:
    #   Q: "There are $ACTIVE_COUNT active run(s) in flight. The cast-server
    #        restart at the end of /cast-upgrade will kill them. Restart anyway?"
    #   A: "Restart anyway" → continue.
    #   B: "Cancel"          → release lock, exit 0 with no changes.
    #   Recommendation: B (Cancel) unless the user explicitly wants to interrupt.
    :
  fi
fi
```

If `curl` fails (server not running, connection refused), there are no
active runs to worry about — proceed without a prompt. The same
`pgrep -f cast-server` check drives the restart decision in Step 10.

### Step 9: Snooze backoff state machine

Triggered only when the user picks **C. Not now** in Step 7.

```python
# Pseudocode — actual implementation lives in the skill body.
DURATIONS_HOURS = [24, 48, 168]   # streak 0 → 24h, 1 → 48h, 2+ → 168h
streak = config.get("upgrade_snooze_streak", 0)
duration = DURATIONS_HOURS[min(streak, 2)]
next_until = datetime.now(UTC) + timedelta(hours=duration)
config["upgrade_snooze_until"] = next_until.isoformat()
config["upgrade_snooze_streak"] = min(streak + 1, 3)   # cap at 3
```

In bash:

```bash
STREAK=$(yq '.upgrade_snooze_streak // 0' ~/.cast/config.yaml)
case $(( STREAK < 2 ? STREAK : 2 )) in
  0) HOURS=24 ;;
  1) HOURS=48 ;;
  2) HOURS=168 ;;
esac
NEXT=$(date -u -d "+${HOURS} hours" +%Y-%m-%dT%H:%M:%SZ)
NEW_STREAK=$(( STREAK + 1 < 3 ? STREAK + 1 : 3 ))
yq -i ".upgrade_snooze_until = \"$NEXT\" | .upgrade_snooze_streak = $NEW_STREAK" ~/.cast/config.yaml
echo "[cast] Snoozed. Next reminder after $NEXT (in ${HOURS}h)."
exit 0
```

When the user later picks **A. Yes, upgrade now** or `auto_upgrade`
succeeds, reset `upgrade_snooze_streak = 0` and
`upgrade_snooze_until = null` so the next "Not now" starts the 24-hour
backoff fresh.

### Step 10: Upgrade procedure

```bash
SERVER_WAS_RUNNING=0
if pgrep -f cast-server >/dev/null 2>&1; then
  SERVER_WAS_RUNNING=1
fi

cd "$REPO"

# Stash any local edits.
STASH_REF=""
if [[ -n "$(git status --porcelain)" ]]; then
  STASH_MSG="cast-upgrade $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git stash push -u -m "$STASH_MSG"
  STASH_REF=$(git stash list | awk -F: -v m="$STASH_MSG" '$0 ~ m {print $1; exit}')
fi

# Fast-forward only — never auto-rebase, never auto-merge.
if ! git pull --ff-only origin main; then
  echo "[cast] git pull --ff-only failed."
  echo "[cast] Your repo has local commits ahead of origin/main."
  echo "[cast] Push or rebase manually before re-running /cast-upgrade."
  echo "[cast] /cast-upgrade does not auto-rebase to avoid data loss."
  # Pop the stash we just made so the user gets back what they had.
  [[ -n "$STASH_REF" ]] && git stash pop "$STASH_REF" || true
  exit 1
fi

# TODO(sp3): Migrations runner hook. Between `git pull` and
# `./setup --upgrade`, scan `migrations/` for un-applied migrations against
# `~/.cast/migrations.applied` and run them in order. sp3 owns the runner;
# sp2b leaves this seam clearly marked. Do not implement the runner here.

# Run the install seam — same path as ./setup, just sets UPGRADE_MODE=1.
UPGRADE_MODE=1 ./setup --upgrade

# Reset snooze state on a successful upgrade.
yq -i '.upgrade_snooze_until = null | .upgrade_snooze_streak = 0' ~/.cast/config.yaml

# Restart cast-server with nohup so it survives the parent shell.
if [[ "$SERVER_WAS_RUNNING" == "1" ]]; then
  pkill -f cast-server || true
  sleep 1
  nohup "$HOME/.local/bin/cast-server" >> "$HOME/.cast/cast-server.log" 2>&1 &
  disown
fi
```

`nohup` is critical — without it, killing the parent shell kills the
restarted server. The `disown` keeps the background job out of the shell's
job table so it does not get reaped on shell exit.

### Step 11: Success path

```text
[cast] Upgrade complete. Local repo changes (if any) are stashed; run
       `git stash pop` in <repo> to restore them.
```

Emit typed `next_steps` per the
[US14 contract](../../../tests/fixtures/next_steps.schema.json) (1–3 items,
each with `command`, `rationale`, `artifact_anchor`):

```json
[
  {
    "command": "/cast-runs",
    "rationale": "Inspect cast-server runs after the restart to confirm everything came back up.",
    "artifact_anchor": null
  },
  {
    "command": "Read CHANGELOG.md",
    "rationale": "See what changed in the upgrade you just installed.",
    "artifact_anchor": "CHANGELOG.md"
  },
  {
    "command": "Restart Claude Code if a skill change is not reflected",
    "rationale": "Claude Code caches skill content per session; a restart picks up the new SKILL.md files.",
    "artifact_anchor": null
  }
]
```

After the **Not now** branch in Step 7, emit `next_steps: []`. US14
allows the empty array as a documented exception.

### Step 12: Failure path (Decision #9)

If any step in 10 fails after the install seam started:

```bash
# Restore ~/.claude/ from the most recent .cast-bak-* directory.
LATEST_BAK=$(ls -1d "$HOME/.claude/.cast-bak-"* 2>/dev/null | sort | tail -n 1 || true)
if [[ -n "$LATEST_BAK" ]]; then
  cp -R "$LATEST_BAK"/* "$HOME/.claude/"
fi

# Pop the local-repo stash so the user gets back their working-tree edits.
POP_RC=0
if [[ -n "$STASH_REF" ]]; then
  git -C "$REPO" stash pop "$STASH_REF" || POP_RC=$?
fi

if [[ "$POP_RC" == "0" ]]; then
  echo "[cast] Auto-upgrade failed — restored previous version including your local repo edits."
else
  echo "[cast] Auto-upgrade failed and your local repo edits are still in stash@{0};"
  echo "[cast] resolve manually with \`git stash pop\` in $REPO after fixing the underlying issue."
fi
```

Emit typed `next_steps`:

```json
[
  {
    "command": "/cast-upgrade",
    "rationale": "Retry the upgrade after fixing the underlying issue (network, disk, conflicting local edits, etc.).",
    "artifact_anchor": null
  }
]
```

The `trap EXIT` from Step 1 fires regardless and removes
`~/.cast/upgrade.lock`.

## `--force` flag

```bash
/cast-upgrade --force
```

Skips Step 3's snooze gate. Does **not** clear `upgrade_snooze_until` or
`upgrade_snooze_streak` — the user's snooze preference is preserved
across the override so the next un-forced invocation honors it again.

## v1 limitations (deferred to v1.1)

- **`upgrade_branch:` config key.** v1 tracks `origin/main` only. v1.1 will
  add per-clone branch tracking.
- **`/cast-upgrade --reset` flag.** v1 expects the user to clear
  `upgrade_snooze_*` and `upgrade_never_ask` by hand-editing
  `~/.cast/config.yaml`.
- **Auto-graceful-shutdown of in-flight runs.** v1 uses a blocking confirm
  prompt (Step 8). v1.1 may add `--gracefully-stop-runs` to drain them.
- **Real Claude Code in CI.** v1 uses `tests/fixtures/fake-claude` only.

## Spec cross-references

- **Delegation pattern:**
  [`docs/specs/cast-delegation-contract.collab.md`](../../../docs/specs/cast-delegation-contract.collab.md)
  governs every `cast-interactive-questions` invocation in this skill.
- **Output JSON shape:**
  [`docs/specs/cast-output-json-contract.collab.md`](../../../docs/specs/cast-output-json-contract.collab.md)
  governs the typed `next_steps` array.
- **Recovery handoff:**
  [`docs/troubleshooting.md`](../../../docs/troubleshooting.md) under
  `## /cast-upgrade restart killed an in-flight run`.
