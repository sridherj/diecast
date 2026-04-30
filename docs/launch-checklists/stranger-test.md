# Stranger Test Checklist

> Hand-off from Phase 4 sp3 → Phase 6 dogfood program.
> Last updated: 2026-04-30.

## Purpose

The automated CI test (`tests/e2e-test.sh`) catches "did the script
run?". This document is the **human-eyes counterpart**: a checklist for
a stranger — someone who has never seen the Diecast repo before — to
walk the install + first-skill flow and report friction.

This is the canonical signal for "is the README understandable?",
"does the install fail in expected ways for a normal user's
environment?", and "do the first three skills feel useful?".

## Who runs this

- A friend, colleague, or community member who is **not** a Diecast
  contributor.
- Has Claude Code installed and at least one project they want to use
  it on.
- Comfortable on a terminal but not necessarily a Diecast/TaskOS power
  user.

## Pre-flight (run by the inviter, not the stranger)

- [ ] Repo is checked into `git` and pushed to `main`. README quick-start
      is up-to-date.
- [ ] `tests/setup-correctness-test.sh` and `tests/e2e-test.sh` both
      green on `main`. (If either is red, stop — fix before bothering a
      stranger.)
- [ ] `bin/lint-anonymization` clean.
- [ ] CHANGELOG `## [Unreleased]` is informative — the stranger may
      glance at it to understand "what changed".

## Stranger-side checklist

> The stranger should **note any friction at each step** — wording that
> tripped them up, missing context, copy-paste commands that didn't
> work, error messages that confused them. Verbatim quotes are gold.

### 1. Clone

- [ ] On a clean machine (or fresh VM, container, codespace), run:

      ```bash
      git clone git@github.com:sridherj/diecast.git
      cd diecast
      ```

- [ ] Did the clone succeed without surprise prompts (SSH keys,
      LFS pointers, …)?

### 2. Install

- [ ] Run `bin/cast-doctor`. Read the output. Did every prerequisite
      come back GREEN, or did the messages tell you exactly how to fix
      what was missing?
- [ ] Run `./setup`.
  - [ ] Did the script complete in under 90 seconds?
  - [ ] Did the `$CAST_TERMINAL` prompt make sense?
  - [ ] After `./setup` exits, does `which cast-server` resolve to a
        real path?
  - [ ] Does `cast-server --version` print the contents of `VERSION`?

### 3. First project

- [ ] Open Claude Code in **any unrelated project** of your own (not
      this repo).
- [ ] Run `/cast-init`.
  - [ ] Did the seven `docs/` directories appear?
  - [ ] Did a project-local `CLAUDE.md` appear at the project root?
  - [ ] Does the `CLAUDE.md` content make sense to you in 30 seconds?

### 4. First skill

- [ ] In the same project, write a one-line goal in a file (e.g.
      `docs/exploration/feeling-stuck.human.md`).
- [ ] Run `/cast-refine` (or `/cast-refine-requirements`) against that
      goal.
  - [ ] Did the skill ask reasonable questions?
  - [ ] After answering, did a refined `*.collab.md` appear?
  - [ ] Did the next-steps panel point at a sensible follow-up?

### 5. Reflection

- [ ] Note the **single most confusing moment** of the walk.
- [ ] Note the **single most surprising-in-a-good-way** moment.
- [ ] Would you keep using Diecast tomorrow? Why / why not?

## Reporting back

Open an issue on `github.com/sridherj/diecast` titled `Stranger test
report — <date>` with:

1. Your environment (OS, terminal, Claude Code version).
2. The friction notes from each step above (verbatim where possible).
3. Your answers to the three reflection prompts.

Phase 6 dogfood program owns the triage of these reports — see the
Phase 6 detailed plan for SLA + fix routing.

## What this checklist deliberately does **not** cover

- `/cast-upgrade` — that flow is rare on day one; covered by the
  automated e2e test and exercised when v1.1 ships.
- The full cast-crud family — Phase 5's worked example
  (`docs/maker-checker.md`) covers it; not a first-touch surface.
- Migration framework — zero migrations in v1; nothing to exercise.

## Cross-references

- Automated e2e: [`tests/e2e-test.sh`](../../tests/e2e-test.sh)
- Setup correctness scenarios: [`tests/setup-correctness-test.sh`](../../tests/setup-correctness-test.sh)
- Phase 4 plan: `taskos/goals/diecast-open-source/phase-4-detailed-plan.collab.md`
- Phase 6 plan: `taskos/goals/diecast-open-source/phase-6-detailed-plan.collab.md`
