# Diecast Migrations

> **Status: zero migrations at v1.** Framework hook only.

This directory ships in v1 with the framework documented but **no migrations
applied to user installs**. The framework hook exists so v1.1+ can ship
schema-migration scripts without a follow-up infra change.

## Filename convention

`<NNN>-<descriptive-slug>.py` — `NNN` is a zero-padded sequence (`001-`,
`002-`, …). Sequence is monotonic and **never reused** even if a migration
is rolled back. New migrations always take the next number.

Examples:

```
001-add-config-snooze-fields.py
002-rename-runs-table-status-column.py
```

## Module shape

Each migration is a Python module exposing two functions:

```python
def up(config: dict) -> None:
    """Apply the migration. config is the parsed ~/.cast/config.yaml."""

def down(config: dict) -> None:
    """Roll the migration back. config is the parsed ~/.cast/config.yaml."""
```

Migrations should be **idempotent** — re-running `up()` against an
already-migrated state must be a no-op. The runner does its best to skip
already-applied migrations via `~/.cast/migrations.applied`, but a botched
apply file or manual edit can lead to a re-run. Code defensively.

## When migrations run

`bin/run-migrations.py` is invoked by `./setup --upgrade` **after** `git pull`
and **before** the skill / agent install steps. The seam lives in
`./setup` (not in `/cast-upgrade`) so `./setup` remains the single source of
truth for "what runs in what order" during install / upgrade.

The order is:

1. `git pull` (handled by `/cast-upgrade` before invoking `./setup --upgrade`).
2. `./setup --upgrade` Step 1 — `cast-doctor` prereq check.
3. `./setup --upgrade` Step 2 — `bin/generate-skills` regenerates
   `skills/claude-code/cast-*/SKILL.md`.
4. **`./setup --upgrade` Step 2.5 — `bin/run-migrations.py`** (this
   directory's runner).
5. `./setup --upgrade` Steps 3-7 — install agents, install skills, install
   `~/.local/bin/cast-server`, write `~/.cast/config.yaml` if absent,
   `$CAST_TERMINAL` prompt.

Rationale: the schema must match the new code by the time skills /
agents / the server are copied into place.

## Tracking

Applied migrations are recorded **one filename per line** in
`~/.cast/migrations.applied`. The runner reads this file at startup,
computes the diff against on-disk migration filenames (sorted lexically),
and runs `up()` for each un-applied migration in order.

Per-branch tracking (the `upgrade_branch:` field in
`~/.cast/config.yaml`) is **deferred to v1.1** — v1 assumes one branch
per install.

## Rollback

On migration failure:

1. The runner raises and exits non-zero.
2. `./setup --upgrade` (the caller) catches the failure and restores
   `~/.claude/` from the most recent `.cast-bak-<UTC-timestamp>/`.
3. `/cast-upgrade` (the outer wrapper) `git stash pop`s any local repo
   edits so they are recoverable.
4. The failed migration is **not** marked applied — the next run will
   retry it.

For the user-facing recovery recipe, see
[`docs/troubleshooting.md`](../docs/troubleshooting.md) entry "Migration
failure during `./setup --upgrade`".

## Testing the runner without polluting the user state

A trivial test migration lives at `tests/migrations-fixtures/test_001_noop.py`.
The end-to-end Docker test (`tests/e2e-test.sh`) invokes the runner with:

```bash
bin/run-migrations.py \
  --migrations-dir tests/migrations-fixtures \
  --applied-file /tmp/migrations.applied
```

This exercises the runner code path without writing to
`~/.cast/migrations.applied` on the host. The fixture migrations live
**outside** the published `migrations/` set and never apply to user
installs.

## v1 status

- **Zero migrations under `migrations/`** (only `README.md` and
  `.gitkeep`).
- The runner ships and is wired into `./setup --upgrade`.
- The runner is exercised by the e2e test against a fixture migration.

When v1.1 ships its first real migration, drop a `001-<slug>.py` file
into this directory and the existing runner picks it up on the next
`./setup --upgrade` cycle.
