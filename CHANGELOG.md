# Changelog

All notable changes to Diecast are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [1.0.0] — UNRELEASED (staged for launch event)

> Diecast's first public release. Ships the workflow chain (Layer-2),
> parent-child delegation primitive, cast-server with Diecast design tokens,
> the cast-crud reference family (Layer-1), and one-command setup.

### Install seam: gstack pattern, no PATH dependency (BREAKING)
- `./setup` now creates `~/.claude/skills/diecast/` as a symlink to the repo
  root. Binaries are reachable as `~/.claude/skills/diecast/bin/cast-server`
  and `~/.claude/skills/diecast/bin/cast-hook` — no PATH manipulation.
- `~/.local/bin/cast-server` shim is **removed** by `./setup --upgrade`
  (backed up under `~/.claude/.cast-bak-<ts>/.local/bin/cast-server`).
- `cast-hook install` writes the absolute path
  `~/.claude/skills/diecast/bin/cast-hook <subcommand>` into
  `.claude/settings.json` instead of bare `cast-hook <subcommand>`. PATH-based
  resolution was unreliable: Claude Code fires hooks with a restricted shell
  PATH that frequently excluded `~/.local/bin/` and `.venv/bin/`, so hooks
  silently failed with "command not found".
- **BREAKING:** if you aliased `cast-server` in your shell rc, update it to
  point at `~/.claude/skills/diecast/bin/cast-server`. If you previously ran
  `cast-hook install` in any project, the old bare-`cast-hook` entries in
  that project's `.claude/settings.json` are now orphans — re-run
  `~/.claude/skills/diecast/bin/cast-hook install` from each affected
  project to refresh.
- New cast-doctor checks: green "diecast skill root linked" + yellow when
  the symlink is missing or the binary is unreachable.
- Spec updated: `docs/specs/cast-hooks.collab.md` v2 inverts FR-002 (PATH
  forbidden, absolute path required) and adds FR-014 (skill-root symlink)
  and FR-015 (legacy shim removal on upgrade).

### Port + env-var seam (sp1, first-run launch)
- Default cast-server port shifted from `8000` to `8005`.
- New env-var `CAST_HOST` (client-side connect target, default `localhost`).
- The pre-existing `CAST_HOST` (server bind) is renamed to `CAST_BIND_HOST`
  (default `127.0.0.1`).
- New `host` / `port` keys in `~/.cast/config.yaml`. `bind_host` is
  intentionally env-var-only via `CAST_BIND_HOST`.
- If you have an old cast-server still running on `:8000`, kill it manually
  (`lsof -ti:8000 | xargs kill`) before re-running `./setup`. No automatic
  detection.

### Setup
- **US1:** One-command `./setup` installs cast-* agents and skills to
  `~/.claude/` and puts `cast-server` on PATH. Surfaces a one-time
  `$CAST_TERMINAL` prompt if the env var is unset.
- **US2:** `/cast-init` scaffolds a fresh project with the spec-kit shape:
  `docs/{exploration,spec,requirement,plan,design,execution,ui-design}/` and a
  project-local `CLAUDE.md`.
- **US12:** `/cast-upgrade` re-installs the latest agent fleet and skills
  in-place, preserving local config. Tracks `main` only at v1; per-clone
  branch tracking via a `upgrade_branch:` config key is deferred to v1.1.

### Agent fleet
- **US3:** ~14 cast-* agents harvested from internal sources, anonymized of
  internal entity names, paths, and personal references. Tone-and-voice
  pass to "the maintainer" / "the project."
- **US16:** cast-crud reference family (Layer-1) ships as a worked example —
  see `docs/maker-checker.md`. Includes maker chain
  (cast-crud-orchestrator → schema → entity → repository → service →
  controller), checker chain (cast-crud-compliance-checker, cast-mvcs-compliance),
  test makers (cast-repository-test, cast-service-test, cast-controller-test,
  cast-integration-test-creator, cast-integration-test-orchestrator), and seed
  helpers (cast-seed-db-creator, cast-seed-test-db-creator).

### Six behaviors (US6)
- **B1:** Refined-requirements interactive shape (template-driven; 0–3
  AskUserQuestions per session).
- **B2:** Inline decision-buffer pattern in plan-review.
- **B3:** Auto-dispatch of `cast-plan-review` after `cast-detailed-plan`.
- **B4:** `cast-review-code` delegation primitive (independent review session
  in a new terminal tab).
- **B5:** File-based parent-child polling (`.agent-run_<RUN_ID>.output.json`),
  resilient to cast-server restart.
- **B6:** Terminal portability via `$CAST_TERMINAL` (kitty, alacritty,
  gnome-terminal, iTerm2 — auto-detected; user-overridable).

### Spec-kit shape (US7)
- Project scaffold matches the spec-kit shape: exploration → spec →
  requirement → plan → design → execution → ui-design.

### UI / cast-server (US5)
- cast-server rebranded with Diecast design tokens: cream `#F5F4F0`
  background, magenta `#D6235C` accent, IBM Plex Mono headings, 5px grid.
- Run-status, runs list, and goal pages refreshed.

### Parent-child delegation (US4)
- File-based contract; polling backoff (1s/2s/5s/10s/30s); 5-minute idle
  timeout; `human_action_needed` escape hatch. See `docs/delegation-pattern.md`.

### File conventions (US9)
- Authorship suffixes for goal artifacts: `.human.md`, `.ai.md`, `.collab.md`.
- Public docs ship without suffix.

### CC-time estimates (US10)
- T-shirt-sized estimates on tasks: XS / S / M / L / XL.

### Brand consistency (US11)
- Locked taglines: **"Cast to spec. No drift."** / **"Cast from the same
  die. Every run."**

### Discipline rules (US13, US14)
- B3-style auto-dispatch of plan-review after detailed-planning.
- Typed `next_steps` field in agent output JSON contract; proactive
  defaults.

### Launch assets (US15)
- README hero + watercolor heroes + GitHub Pages site at `docs/`.
- Three workflow GIFs in README's "What you get" section + delegation-pattern
  doc.
- Public docs set: `docs/{thesis,how-it-fits,delegation-pattern,maker-checker,multi-harness,roadmap}.md`.
- GitHub Discussions enabled; Topics set; social preview uploaded.

### Out of v1 (deliberate)
- Discord (revisit at v1.1 if Discussions surfaces real-time chat demand).
- Multi-harness adapters (Codex/Copilot — ship when a non-Claude user asks
  unprompted).
- Linear / Asana / Jira PM-tool adapters (target v2.0).

### Roadmap
- v1.1 — agent contracts (target ~30 days post-launch).
- v1.2 — evals harness (target ~60 days post-launch).
- v2.0 — PM-tool adapters (target ~90–120 days post-launch).
- 90-day kill criterion: <100 stars + <15 active users + no third-party
  traction → archive.

[1.0.0]: https://github.com/sridherj/diecast/releases/tag/v1.0.0

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
