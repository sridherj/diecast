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

Diecast ships three layers of tests. Run them in this order when working
on `./setup` / `/cast-init` / `/cast-upgrade` changes:

1. **Python unit tests + bash smoke tests (fast, ~10 s).**

   ```bash
   uv run pytest -q
   bash tests/setup-correctness-test.sh
   ```

2. **End-to-end Docker integration test (slow, 90-120 s).** See the
   "Running the e2e test" section below. Skip on local development
   unless you are touching install / upgrade plumbing; CI runs it on
   every push to `main` and on PRs labelled `run-e2e`.

3. **Anonymization lint (instant).** Always run before opening a PR:

   ```bash
   bin/lint-anonymization
   ```

## Running the e2e test

`tests/e2e-test.sh` orchestrates a full install → `/cast-init` →
`/cast-upgrade` → migration-runner walk inside a Docker container. It
uses the fake `claude` binary at `tests/fixtures/fake-claude` (Decision
#8) so no API key is needed. Expected runtime: 90-120 s.

Run locally:

```bash
docker build -t diecast-e2e -f tests/Dockerfile.test-e2e .
docker run --rm -v "$(pwd):/work" diecast-e2e
```

The repo is mounted at `/work` at runtime; rebuild the image only when
the `Dockerfile.test-e2e` itself changes.

To gate the test on a pull request before merge, add the `run-e2e`
label. Without the label, only `tests/setup-correctness-test.sh` runs
on PRs (see `.github/workflows/setup-correctness.yml`).

### Common failure modes

| Symptom                                                      | Likely cause                                                 |
|--------------------------------------------------------------|--------------------------------------------------------------|
| `claude: command not found`                                  | Image built without `tests/fixtures/fake-claude` mounted     |
| `bin/run-migrations.py: Permission denied`                   | File lost its `+x` bit on checkout (run `chmod +x`)          |
| Test exits 1 with `assert_grep miss: skill cast-init …`      | `/cast-init` invocation never reached fake-claude            |
| Runtime > 180 s                                              | Docker image cache cold; first build is ~120 s on top of run |
| `bin/lint-anonymization reports findings`                    | Internal name leaked into a generated skill or config        |

If the test fails for a reason not covered here, file an issue with the
full output of `docker run --rm -v "$(pwd):/work" diecast-e2e 2>&1`.

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
