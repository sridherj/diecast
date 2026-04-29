# `bin/` — Diecast Developer Scripts

## `generate-skills`

Materializes Claude Code skill files from `cast-*` agents and skills in this
repo into `~/.claude/skills/` (overridable via `--target-dir`).

### Contract

- **Reads:**
  - `agents/cast-*/cast-*.md` — each cast-* agent's primary doc
  - `skills/claude-code/cast-*/SKILL.md` — each Claude Code skill source
  - Non-`cast-*` subdirectories are skipped with a stderr warning (forward-compat
    for future harness adapter directories — e.g., a `gemini/` skill tree).
- **Writes:**
  - `<target>/cast-*/SKILL.md` — one file per discovered source. Each output
    file is prefixed with a generated-by header and a back-reference comment
    pointing at the source path inside the diecast repo.
- **Default target:** `~/.claude/skills`. Override with `--target-dir <path>`.

### Flags

| Flag | Purpose |
|------|---------|
| `--dry-run` | Print what would happen; touch no files. |
| `--target-dir <path>` | Override the output directory. |
| `--help` | Show usage. |

### Backup behavior

Before overwriting any pre-existing target file, the script moves the original
into `<target>/.cast-bak-<timestamp>/` preserving the relative path. The
timestamp is fixed for a single invocation, so all backups from one run land
in the same folder. The script never deletes backup folders — cleanup is
deferred to Phase 4 `/cast-upgrade`. Until then, you may safely `rm -rf
<target>/.cast-bak-*` once you've confirmed the new generation looks right.

### Idempotency

Two consecutive runs against an unchanged tree produce identical output. The
underlying file writes are unconditional today — there is no checksum-aware
short-circuit, so every successful run touches every output file's mtime. A
checksum-aware overwrite path (and the corresponding "preserve user edits"
guarantee) is deferred to Phase 4 — see refined-req US8 in
`refined_requirements.collab.md`.

### When to run

- After harvesting or editing any `cast-*` agent or skill in this repo.
- During development with `--dry-run --target-dir /tmp/diecast-out` to
  preview the materialization without touching `~/.claude/skills`.
- CI may invoke it with a tmp `--target-dir` to verify the discovery and
  rendering paths still work.

### Safety

The test suite under `tests/test_generate_skills.py` always uses `tmp_path`
and `--target-dir`, never the real `~/.claude/skills`. Manual smoke tests
should follow the same pattern; see the verification block in
`docs/execution/diecast-open-source/phase-1/1.2-generate-skills-port.md`.

## `lint-anonymization`

Scans the working tree for upstream-private references that must not appear
in public Diecast output (personal identifiers, internal paths, private agent
names). Fires on every push and pull request via
`.github/workflows/anonymization-lint.yml`.

### Contract

- **Reads:** every tracked + untracked file in the repo (respects `.gitignore`
  via `git ls-files`; falls back to a `pathlib` walk outside a git repo).
- **Skips by default:** `.git/`, `.venv/`, `__pycache__/`, `node_modules/`,
  `.cast-bak-*/`, `.pytest_cache/`, and `tests/fixtures/forbidden/`. Pass
  `--include-fixtures` to also scan `tests/fixtures/forbidden/` for
  pattern-coverage sweeps.
- **Writes:** nothing. Hits print to stdout in
  `<file>:<line>: matched pattern '<regex>' — anonymization rule X violated.`
  format. Exits 0 on a clean tree, 1 on hits.

### Forbidden patterns

The regex list lives **in the script itself** (`FORBIDDEN_PATTERNS` near the
top of `bin/lint-anonymization`) — there is no separate pattern file because
any external file would itself need to be public. When the upstream private
`## People` table changes, append matching `\b<First Last>\b` entries
during the quarterly review cadence noted in `CONTRIBUTING.md`.

### Self-exemption

Any line carrying the substring `diecast-lint: ignore-line` (typically as a
trailing comment) is excluded from the scan. Use sparingly and only for
provably-legitimate references.

### Flags

| Flag | Purpose |
|------|---------|
| `--root <path>` | Scan a different tree (default: cwd). |
| `--include-fixtures` | Also scan `tests/fixtures/forbidden/`. |

## `audit-interdependencies`

Phase-1 no-op skeleton (D4). Prints `audit-interdependencies stub — Phase 2
wires the four sub-audits` and exits 0. Wired into the CI workflow now so
the workflow shape stays stable when Phase 2 lands the actual sub-audits
(cast-* prefix coverage, shared-module reachability, generated-skill regen
drift, fixture-tree sanity).
