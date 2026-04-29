# Contributing to Diecast

Thanks for your interest in contributing. Diecast is an Apache-2.0 licensed
project for shipping reusable Claude Code agents and skills as a small,
opinionated framework. This guide covers what you need to know to send a
patch.

## Clone

```bash
git clone git@github.com:sridherj/diecast.git
cd diecast
```

## Install dependencies

> Installer lands in Phase 4. For now, see `docs/install.md` once it ships.

```bash
./setup    # placeholder until Phase 4
```

## Run tests

> Test harness lands in Phase 4 alongside the installer.

```bash
# Placeholder — test runner not wired up yet.
```

## Naming conventions

- **Agents and skills published by this repo use the `cast-*` prefix.**
  For example: `cast-explore`, `cast-plan-review`. Other prefixes are
  reserved for upstream internal use and must not appear in public
  contributions; the anonymization linter will reject them.
- Branch names: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`.
- Conventional Commits for messages: `feat:`, `fix:`, `docs:`, `chore:`,
  `refactor:`, `test:`.

## Anonymization rule (CI-enforced)

Diecast is harvested from a private monorepo. The anonymization lint
exists to keep upstream-private references (personal email addresses,
internal teammate names, internal project paths) out of the public repo.

- The lint script is `bin/lint-anonymization` (lands in sub-phase 1.3).
- CI fails any pull request that introduces a forbidden string.
- There is **no pre-commit hook** — run the linter manually before
  pushing:

  ```bash
  bin/lint-anonymization
  ```

- If you add a name to your private memory or notes (for example, a
  teammate appearing in a personal `CLAUDE.md` People table), also add
  it to `bin/lint-anonymization`'s forbidden list during your next
  quarterly sweep. The linter is the canonical source of truth for
  what must never ship publicly.

## Authorship convention for `.md` files

Goal artifacts and exploration documents use authorship suffixes:

- `*.human.md` — written by a human, not edited by an AI.
- `*.ai.md` — written by an AI, lightly reviewed if at all.
- `*.collab.md` — co-authored: AI draft with substantial human edits,
  or vice versa.

Default suffixes:

| Document type            | Default suffix |
|--------------------------|----------------|
| Requirements             | `.human.md`    |
| Plans                    | `.collab.md`   |
| Research, summaries      | `.ai.md`       |

When a `.ai.md` accumulates significant human edits, rename it to
`.collab.md`. Code, configuration, and structured data files (YAML,
JSON, TOML, etc.) do **not** use the convention.

## Pull requests

Before opening a pull request:

1. Anonymization-lint passes (`bin/lint-anonymization` returns 0).
2. Linked issue or design doc, if applicable.
3. Tests added or updated.
4. Docs touched in the same PR if behavior changed.
5. Conventional Commit message in the PR title.

The pull request template (`.github/PULL_REQUEST_TEMPLATE.md`) restates
the same checklist for convenience.

## Code of conduct

Participation is governed by the [Contributor Covenant](CODE_OF_CONDUCT.md).
Report concerns via [GitHub Discussions](https://github.com/sridherj/diecast/discussions).

## Security

Do **not** open public issues for security vulnerabilities. See
[SECURITY.md](SECURITY.md) for the private disclosure path.
