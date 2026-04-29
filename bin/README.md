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
