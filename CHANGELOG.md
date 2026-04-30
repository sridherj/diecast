# Changelog

All notable changes to Diecast are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

- Repo bootstrap: Apache-2.0 license, OSS staple files, canonical directory
  layout, and `setup` scaffold landed. No agents harvested yet.
- `/cast-upgrade` skill (Phase 4 sp2b): pulls `origin/main`, preserves local
  skill edits via `git stash` + `.cast-bak-<ts>/`, restarts `cast-server`,
  and auto-restores from the latest `.cast-bak-*` on failure. Honors
  `auto_upgrade`, `upgrade_snooze_until`, `upgrade_snooze_streak`,
  `upgrade_never_ask`, and `last_upgrade_check_at` (1h TTL) in
  `~/.cast/config.yaml`. Concurrent invocations are blocked by
  `~/.cast/upgrade.lock`.

  **v1 limitation:** `/cast-upgrade` tracks `main` only at v1; per-clone
  branch tracking via a `upgrade_branch:` config key is deferred to v1.1.
