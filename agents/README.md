# `agents/` — Diecast Agent Sources

Each `cast-*` agent lives in its own directory: `agents/cast-foo/cast-foo.md`
plus an optional `config.yaml` (and any agent-local fixtures or runs/). The
directory name and the `name:` frontmatter field MUST match.

## Frontmatter contract (pinned for v1)

`bin/generate-skills` ports each `cast-foo.md` into a Claude Code skill at
`~/.claude/skills/cast-foo/SKILL.md`. The frontmatter is currently passed
through untouched — the contract is the **union of fields** observed across
representative upstream agents (`cast-detailed-plan`, `cast-tasks`,
`cast-update-spec`, etc.) at port time:

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `name` | yes | string | Must equal the parent directory name (e.g., `cast-foo`). |
| `description` | yes | string \| YAML block scalar | Single line or `>`/`\|` block. Trigger phrases live here. |
| `model` | no | string | `opus`, `sonnet`, or `haiku`. Omit to inherit harness default. |
| `memory` | no | string | Typically `user`. Reserved for future memory routing. |
| `effort` | no | string | `low`, `medium`, or `high`. Hints orchestrator budgeting. |

Phase 2 `/cast-harvest` will enforce this contract during harvest from
upstream. Any harvested agent missing a required field, or carrying an
unknown field, will be flagged for human reconciliation rather than silently
materialized. Adding a new field to the contract is a deliberate, documented
change to this README — not a side effect of one harvested agent.

## Naming

- Directory: `agents/cast-<slug>/`
- Primary doc: `agents/cast-<slug>/cast-<slug>.md`
- Optional config: `agents/cast-<slug>/config.yaml`

Non-`cast-*` directories under `agents/` are reserved for future use (e.g.,
adapter shims for non-Claude harnesses) and are skipped by `bin/generate-skills`
with a stderr warning.
