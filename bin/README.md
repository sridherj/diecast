# `bin/`

**User-facing:** only `cast-server` (symlinked to `~/.local/bin/cast-server` by
`./setup`). All other entries are internal tooling — invoked by `setup`, CI, or
one-shot migrations. Post-install user surface lives in `/cast-*` slash commands
inside Claude Code.

## User-facing

- `cast-server` — the daemon; the only Diecast binary on your `$PATH`.

## Internal — invoked by `setup` or CI

- `cast-doctor` — diagnostic prerequisite checker. User surface: `/cast-doctor`
  slash command inside Claude Code; this script remains the shell fallback and
  the gate `setup`'s `step1_doctor` runs.
- `_lib.sh` — shared bash helpers (`log`, `warn`, `fail`, `backup_if_exists`,
  `prune_old_backups`). Sourced, not executed.
- `generate-skills` — produces `~/.claude/skills/cast-*/SKILL.md` from
  `agents/` and `skills/claude-code/`. Invoked by `step4_install_skills`.
- `set-proactive-defaults.py` — seeds per-agent `proactive` defaults in
  `agents/cast-*/config.yaml`. Invoked by setup's default-init step.
- `sweep-port-refs.py` — markdown-aware port/host sweep (one-shot; see sp1 of
  the cast-server-first-run-launch plan).

## Internal — CI lints

- `cast-spec-checker` — lints spec docs against
  `templates/cast-spec.template.md`. User surface:
  `/cast-spec-checker` slash command.
- `check-doc-links` — validates relative Markdown links across `README.md`
  and `docs/*.md`.
- `audit-interdependencies` — cross-reference audit over the cast-* agent and
  skill fleet.
- `lint-anonymization` — scans for upstream-private references that must not
  appear in public Diecast output.

## Internal — one-shot data migrations

These are obsolete after their matching deploy but kept for users on stale
databases:

- `migrate-legacy-estimates.py` — legacy estimate columns → Diecast US10
  T-shirt sizes.
- `migrate-next-steps-shape.py` — bulk-rewrite legacy `next_steps` lists to
  the typed shape (US14).

## Deprecated

- `run-migrations.py` — superseded by Alembic (`cast-server/alembic/`).
  Will be removed once all known DBs have been migrated. Do not invoke for
  new schema changes.
