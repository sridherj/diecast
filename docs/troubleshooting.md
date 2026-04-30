# Troubleshooting

Recipes for the most common Diecast install / runtime hiccups. Each entry
describes the symptom, the recovery, and the underlying mechanism so that
you can adapt the recovery if your situation differs.

If your problem is not covered here, run `bin/cast-doctor` for a structured
prerequisite check, and file an issue with its output attached.

## `setup` failed mid-run — recovery from `.cast-bak-*`

**Symptom.** `./setup` aborted partway through (network error during
`uv run`, killed by `Ctrl+C`, disk full, etc.). Some files at
`~/.claude/agents/cast-*` or `~/.local/bin/cast-server` may have been
overwritten before the failure; the originals are safe in
`~/.claude/.cast-bak-<UTC-timestamp>/`.

**Recovery.**

1. Find the most recent backup directory:

   ```bash
   ls -1d ~/.claude/.cast-bak-* | sort | tail -n 1
   ```

2. Restore it on top of `~/.claude/`:

   ```bash
   latest="$(ls -1d ~/.claude/.cast-bak-* | sort | tail -n 1)"
   cp -R "${latest}"/* ~/.claude/
   ```

3. Resolve the underlying cause (network, disk, permissions), then re-run
   `./setup`. The next run will create a fresh `.cast-bak-<ts>/` and the
   retention pass keeps the 5 newest by lex sort.

**Mechanism.** `bin/_lib.sh::backup_if_exists` moves any pre-existing target
into `${HOME}/.claude/.cast-bak-${RUN_TIMESTAMP}/` before `./setup` writes
its replacement. All moves in one run share a directory, so the entire
prior install state is recoverable as a unit.

## `/cast-upgrade` restart killed an in-flight run

**Symptom.** You ran `/cast-upgrade` while a cast-\* agent was mid-run.
The upgrade restarted `cast-server` and the in-flight run's status went
from `running` to a terminal failure with no output JSON written.

**Why this happens.** `/cast-upgrade` always restarts `cast-server` after
`./setup --upgrade` completes (so the new code is actually loaded). At
runtime, the skill detects active runs via `GET
http://localhost:8005/api/agents/runs?status=running` and surfaces a
2-option confirm prompt before restarting. If you bypass the prompt by
picking **Restart anyway**, expect run-state loss.

**Recovery.**

1. Re-trigger the lost run via the recheck endpoint:

   ```bash
   curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/<run_id>/recheck
   ```

   The run picks up from its last persisted state. If the child wrote a
   partial output JSON to `<goal_dir>/.agent-run_<RUN_ID>.output.json`
   before being killed, recheck reads it; otherwise the run restarts.

2. If the run had no persisted state (e.g. the child died before any
   write), re-dispatch via the parent agent's normal trigger path. The
   parent's `cast-child-delegation` polling logic surfaces the failure
   and offers a rerun next-step automatically.

**Prevention.** Pick **Cancel** in the active-runs confirm prompt when
there are runs in flight. Wait for them to drain, then re-run
`/cast-upgrade`. The cache (1-hour TTL on `last_upgrade_check_at` in
`~/.cast/config.yaml`) keeps the recheck cheap.

## `/cast-upgrade` failed and left local edits in `stash@{0}`

**Symptom.** `/cast-upgrade` printed:

> Auto-upgrade failed and your local repo edits are still in `stash@{0}`;
> resolve manually with `git stash pop` after fixing.

**Why this happens.** Per Decision #9, the upgrade skill always tries to
restore `~/.claude/` from the most recent `.cast-bak-*` directory and
then `git stash pop` the repo stash it created at the start of the
upgrade. If `git stash pop` reports merge conflicts (because the
upstream pull touched the same files your local edits did), it leaves
your edits in `stash@{0}` so nothing is lost.

**Recovery.**

1. Resolve the underlying issue that caused the upgrade to fail
   (network, disk, broken local commit, etc.).

2. In the repo directory:

   ```bash
   git stash pop
   # Resolve the merge conflicts in any reported files, then:
   git add <fixed-files>
   ```

3. Re-run `/cast-upgrade` to retry with a clean working tree. If you do
   not need your local edits any more, drop the stash instead of
   popping:

   ```bash
   git stash drop
   ```

**Mechanism.** The skill captures the stash ref from `git stash list`
right after creating it, and passes that ref to `git stash pop` on the
failure path. The stash is never cleared by the skill on a conflict, so
your edits are recoverable until you choose to drop them.

## `/cast-upgrade` says "Snoozed until …" and exits

**Symptom.** You ran `/cast-upgrade` and saw `Snoozed until <ISO
timestamp> — run /cast-upgrade --force to override.` instead of an
upgrade prompt.

**Why this happens.** A previous invocation picked **Not now** at the
4-option prompt. The skill set `upgrade_snooze_until` in
`~/.cast/config.yaml` to `now + 24h` (or 48h, or 168h depending on the
streak count) so it would not nag. The streak caps at 3 (1 week).

**Recovery.**

- **One-shot override:** `/cast-upgrade --force` skips the snooze gate
  for this invocation **without** clearing the snooze state. Your
  preference survives an override.
- **Permanent clear:** edit `~/.cast/config.yaml` and set
  `upgrade_snooze_until: null` and `upgrade_snooze_streak: 0`. A
  dedicated `/cast-upgrade --reset` flag is deferred to v1.1.

A successful upgrade (via **Yes, upgrade now** or `auto_upgrade: true`)
resets the streak and clears the until-timestamp automatically.

## Unsupported terminal — see `docs/terminals.md`

**Symptom.** `cast-spawn-child` or `bin/cast-doctor` printed a YELLOW
warning along the lines of:

> Warning: `$CAST_TERMINAL=<value>` not supported; falling back to
> `<picked>`. See `docs/terminals.md` to add support.

**Why this happens.** `$CAST_TERMINAL` is set to a value that
`agents/_shared/terminal.py::resolve_terminal()` does not recognise. Per
Decision #3, Diecast does **not** hard-fail in this situation; it
soft-falls-back to the first supported terminal on `PATH` (preference
order matches the table in [`docs/terminals.md`](terminals.md)).

**Recovery (pick one).**

1. **Set a supported value.** Edit `~/.cast/config.yaml::terminal` (or
   export `$CAST_TERMINAL`) to one of: `ptyxis`, `gnome-terminal`,
   `kitty`, `alacritty`, `wezterm`, `iterm2`. The full table with launch
   recipes lives at [`docs/terminals.md`](terminals.md). Re-run
   `bin/cast-doctor` to confirm the warning clears.
2. **Install a supported terminal.** If none of the supported names are
   on your `PATH`, install one (e.g. `apt install kitty`,
   `brew install wezterm`).
3. **Add support for your terminal.** See the "Adding support for a new
   terminal" section in [`docs/terminals.md`](terminals.md). PRs welcome.

**Mechanism.** The supported list is the single source of truth in
`agents/_shared/terminal.py::SUPPORTED_TERMINALS`, mirrored in
`bin/cast-doctor`'s `SUPPORTED_TERMINALS` array and in the table at
[`docs/terminals.md`](terminals.md). All three update together when a new
terminal lands.

## Migration failure during `./setup --upgrade`

**Symptom.** `./setup --upgrade` (called by `/cast-upgrade` after
`git pull`) aborted partway through with a Python traceback originating
in `bin/run-migrations.py` or in a migration module under
`migrations/`. The failed migration filename was **not** appended to
`~/.cast/migrations.applied`, so the next run will retry it.

**Why this happens.** `bin/run-migrations.py` runs in Step 2.5 of
`./setup --upgrade` — between `bin/generate-skills` and the agent /
skill / cast-server install steps. A migration's `up(config)` raised an
exception (bug in the migration, schema drift, environment mismatch).

**Recovery.**

1. **Restore the previous install state** from the most recent backup,
   following the same recipe as "`setup` failed mid-run — recovery from
   `.cast-bak-*`" above:

   ```bash
   latest="$(ls -1d ~/.claude/.cast-bak-* | sort | tail -n 1)"
   cp -R "${latest}"/* ~/.claude/
   ```

2. **Recover any local repo edits** — `/cast-upgrade` stashed them
   before invoking `./setup --upgrade`. If `git stash pop` succeeded
   silently, your edits are already back; if not, see "`/cast-upgrade`
   failed and left local edits in `stash@{0}`" above.

3. **Diagnose and fix the migration**. Re-read the traceback; the
   migration filename is in the `[run-migrations] applying <name>…`
   line immediately above the traceback. Check the migration's
   `up(config)` implementation for the asserted invariant.

4. **Retry**. Re-run `/cast-upgrade` (or `./setup --upgrade` directly).
   Already-applied migrations are skipped via
   `~/.cast/migrations.applied`; the previously-failed one is retried.

**Mechanism.** `bin/run-migrations.py` raises on the first failure,
which propagates up through `./setup --upgrade`'s `set -e` and triggers
the `/cast-upgrade` rollback path (Decision #9). Migrations are expected
to be idempotent (re-running `up()` on an already-migrated state is a
no-op) — see [`migrations/README.md`](../migrations/README.md). At v1
zero migrations ship, so this entry is forward-looking.

## Skill list in `CLAUDE.md` is stale after `/cast-upgrade`

**Symptom.** You ran `/cast-upgrade` and gained one or more new `cast-*`
skills, but the "Skills available" section in your project-local
`CLAUDE.md` still lists the old set.

**Recovery.** Re-run `/cast-init` from the project root and pick
**"Overwrite CLAUDE.md only"** at the 4-option prompt. The skill enumerates
`~/.claude/skills/cast-*/SKILL.md` at template-render time and writes the
fresh list. Your previous `CLAUDE.md` is preserved in
`~/.claude/.cast-bak-<UTC-timestamp>/CLAUDE.md` if you need to recover the
"About this project" section you had hand-edited.

**Mechanism.** The skill list is a snapshot taken when `/cast-init` writes
`CLAUDE.md`; there is no live binding. A dedicated `--refresh-claude-md`
flag is held for v1.1 — until then, the four-option re-run is the
documented workaround. The conventions block itself is **not** affected by
this staleness: it points at the spec by URL, so updates to the spec
propagate without rewriting `CLAUDE.md`.
