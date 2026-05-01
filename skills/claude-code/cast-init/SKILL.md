---
name: cast-init
description: >
  Scaffold the Diecast docs/ tree (exploration, spec, requirement, plan, design, execution,
  ui-design) and write a project-local CLAUDE.md that points at the canonical conventions
  spec. Re-runnable; non-destructive 4-option merge prompt on existing layout.
trigger_phrases:
  - /cast-init
  - "scaffold this project"
  - "set up cast in this project"
  - "initialize cast"
---

# /cast-init — Project Scaffold

Initialize a project for use with Diecast. After a successful run the project root
contains the seven canonical `docs/<area>/` directories (each with a `.gitkeep`) plus a
project-local `CLAUDE.md` that points at the
[`cast-init-conventions` spec](../../../docs/specs/cast-init-conventions.collab.md).

The skill is **idempotent and non-destructive** on re-run: detection logic surfaces a
4-option prompt rather than silently overwriting (Decision #5).

> **Canonical spec.** The file conventions written into the project's `CLAUDE.md` are
> documented in `docs/specs/cast-init-conventions.collab.md`. The `CLAUDE.md` template is
> a pointer; the spec is canonical. Never inline the conventions into the template.

> **Delegation.** This skill is purely client-side — there is no `agents/cast-init/`. The
> only delegation is to `cast-interactive-questions` for the 4-option merge prompt. The
> skill MUST follow that protocol when prompting (one question at a time, structured
> options, recommendation first).

## Inputs

- **Working directory:** `<cwd>` is the project root. Resolve once via `pwd`; do not
  accept user-supplied paths (eliminates path-traversal concerns; FR-008 of the
  delegation contract).
- **`{{PROJECT_NAME}}`:** derived from `basename "$(pwd)"`. Sanitize for markdown safety
  (escape backticks, square brackets, asterisks, underscores, pipes if present).
- **`--no-hooks`** *(optional, default off):* opt out of the Step 4 hook install. By
  default `/cast-init` installs the `cast-hook` entries that capture every user-typed
  `/cast-*` slash command as a top-level run. Pass `--no-hooks` to skip that step (the
  scaffold still happens). The hooks can be installed later via standalone
  `cast-hook install`.
- **`--user`** *(optional, default off):* when installing hooks, write to user-scope
  `~/.claude/settings.json` instead of project-scope `<cwd>/.claude/settings.json`.
  Has no effect if combined with `--no-hooks`.

## Pre-flight

1. `pwd` resolves to a directory the agent can write to. If not, fail with a clear
   message ("`/cast-init` must be run from the project root and needs write access.").
2. `~/.claude/skills/cast-*/SKILL.md` exists for at least one cast-* skill. If not,
   warn — `/cast-init` still scaffolds, but the "Skills available" list will be empty.
3. Verify the canonical spec is reachable at the published Diecast repo URL — do **not**
   embed the spec contents; the template only references it by path.

## Step 1: Detect existing state

For each path, record whether it exists:

- The seven canonical directories: `docs/exploration/`, `docs/spec/`, `docs/requirement/`,
  `docs/plan/`, `docs/design/`, `docs/execution/`, `docs/ui-design/`.
- `<cwd>/CLAUDE.md`.

Branch:

- **Clean project** (no canonical dirs, no `CLAUDE.md`): jump to Step 3 (scaffold all,
  render template).
- **Partial state** (any canonical dir OR `CLAUDE.md` exists): jump to Step 2 (4-option
  prompt).

## Step 2: 4-option merge prompt (Decision #5)

→ **Delegate to `cast-interactive-questions`.** Render a single AskUserQuestion with the
four options below. Lead with the recommendation. Do not add a fifth option (e.g., "show
diff before deciding") — the selective-expansion budget is already spent on
`bin/cast-doctor`, `.cast-bak-*` retention, and `./setup --dry-run`.

```text
**Question #1: Existing project layout detected**

I found {{N}} of the seven canonical docs/ directories already present and CLAUDE.md
{{exists | does not exist}}. How should I proceed?

- **Option A — Skip (keep existing) (Recommended):** Most existing layouts are intentional;
  skipping is the safest non-destructive default. Exit without changes.
- **Option B — Overwrite CLAUDE.md only:** Re-renders the template with the current
  project name and skill list. Backs up the old CLAUDE.md to ~/.claude/.cast-bak-<ts>/
  first.
- **Option C — Add missing dirs only:** Creates the canonical dirs that don't exist and
  leaves CLAUDE.md alone. Appends a single HTML-comment hint to the bottom of the
  existing CLAUDE.md pointing at the conventions spec.
- **Option D — Cancel:** Exit without changes.
```

Behavior per option:

- **A (Skip):** print `Cast-init detected existing layout. No changes made.`; emit
  `next_steps: []`; exit 0.
- **B (Overwrite CLAUDE.md only):**
  1. Call `bin/_lib.sh::backup_if_exists "<cwd>/CLAUDE.md"` via subprocess (the helper
     places the file under `~/.claude/.cast-bak-${RUN_TIMESTAMP}/`). The skill MUST NOT
     replicate the backup primitive in Python — single source of truth.
  2. Render the template (Step 3.2) and write `<cwd>/CLAUDE.md`.
  3. Skip directory creation.
  4. Run Step 4 (install cast-hook entries) unless `--no-hooks`.
  5. Emit `next_steps` per Step 5.
- **C (Add missing dirs only):**
  1. For each canonical dir that does not exist: `mkdir -p` + `touch .gitkeep`.
  2. Append exactly one HTML comment to the bottom of the existing `CLAUDE.md`:
     `<!-- cast-init suggests adopting the conventions in docs/specs/cast-init-conventions.collab.md from github.com/sridherj/diecast -->`.
     If the comment is already present (idempotence check), skip the append.
  3. Run Step 4 (install cast-hook entries) unless `--no-hooks`.
  4. Emit `next_steps` per Step 5.
- **D (Cancel):** exit 0; print `Cancelled. No changes made.`; emit `next_steps: []`.

## Step 3: Scaffold (clean-project path)

### 3.1 Directories

For each canonical dir:

```text
mkdir -p docs/<area>
touch docs/<area>/.gitkeep
```

`touch` is idempotent — re-running on a populated directory updates the `.gitkeep`
mtime but is otherwise a no-op. The seven canonical areas are exactly: `exploration`,
`spec`, `requirement`, `plan`, `design`, `execution`, `ui-design`.

> Do **not** modify the seven names. The US2 acceptance scenarios enumerate them
> verbatim; renaming breaks downstream agent contracts and the conventions spec.

### 3.2 Render `CLAUDE.md` template

1. Read `templates/CLAUDE.md.template` from the installed Diecast repo. Resolve the
   repo via `${CAST_REPO_DIR:-$(readlink -f ~/.claude/skills/diecast)}` — `./setup`
   creates `~/.claude/skills/diecast` as a symlink pointing at the repo root.
2. Substitute `{{PROJECT_NAME}}` ← `basename "$(pwd)"` (markdown-sanitized).
3. Substitute `{{SKILLS_LIST}}` ← Step 3.3 output.
4. Write `<cwd>/CLAUDE.md`. If a CLAUDE.md already exists at this point on the
   clean-project branch, it appeared mid-run — bail with an error and instruct the user
   to re-run.

After 3.3 finishes, fall through to Step 4 (hook install) unless `--no-hooks` was passed.

### 3.3 Generate the skills-available list

Enumerate `~/.claude/skills/cast-*/SKILL.md`. For each, parse the YAML front matter,
extract `name` and the first non-blank line of `description`. Render as a bulleted
markdown list, alphabetized by name:

```markdown
- `/cast-explore` — Full exploration pipeline: decompose → research → playbooks → impact summary.
- `/cast-goal-decomposer` — Decompose a goal into structured steps.
- `/cast-init` — (you just ran this!)
- `/cast-refine-requirements` — Refine requirements interactively.
…
```

Mark the entry for `/cast-init` with `(you just ran this!)` so the user immediately sees
themselves in the list — small UX win that reinforces that the file is project-local.

> **Known limitation (deferred to v1.1):** the list goes stale after a `/cast-upgrade`
> adds new skills. The fix (`--refresh-claude-md` flag) is held per Design Review Flag.
> Workaround documented in `docs/troubleshooting.md`: re-run `/cast-init` and pick
> "Overwrite CLAUDE.md only".

## Step 4: Install cast-hook entries (default ON)

> Skip with `--no-hooks`.

Install the Claude Code hooks that capture every user-typed `/cast-*` slash command as a
top-level `agent_run` row. This is the wiring that makes the runs tree show the human
action that initiated downstream work — without it, only agent-dispatched children appear.

By default this step runs at **project scope**, writing to `<cwd>/.claude/settings.json`.
Pass `--user` to install at user scope (`~/.claude/settings.json`) instead.

Behavior:

```bash
~/.claude/skills/diecast/bin/cast-hook install            # project scope, the default
~/.claude/skills/diecast/bin/cast-hook install --user     # user (global) scope
```

The bare `cast-hook` command is **not** on PATH — it lives at the absolute path
above. `./setup` creates the `~/.claude/skills/diecast` symlink to the repo root,
which makes `bin/cast-hook` (a thin `uv run` wrapper) reachable.

`cast-hook install` is **idempotent**: re-running is safe and never duplicates entries. It
**never replaces** existing third-party hooks — it appends our `UserPromptSubmit` and
`Stop` entries alongside whatever else lives in `settings.json`. Missing `settings.json`
is created. Malformed `settings.json` aborts with a readable message rather than
overwriting the user's file.

To remove later: `cast-hook uninstall` (or `cast-hook uninstall --user`).

If `--no-hooks` was passed to `/cast-init`, skip this step entirely and do not print the
restart line below.

After install (and on every successful `/cast-init` run that did not pass `--no-hooks`),
print this final line so it is the last thing the user sees:

```text
Restart Claude Code to activate the hooks.
```

This matters because Claude Code reads `settings.json` at startup; new hook entries do not
take effect in the current session.

### Standalone surface

The same install path is available outside `/cast-init` for users who skipped it or who
want to (re-)install later from a project root:

```bash
~/.claude/skills/diecast/bin/cast-hook install              # project scope (default)
~/.claude/skills/diecast/bin/cast-hook install --user       # user (global) scope
~/.claude/skills/diecast/bin/cast-hook uninstall            # remove our entries; preserve everything else
~/.claude/skills/diecast/bin/cast-hook uninstall --user
```

## Step 5: Emit typed `next_steps` (US14)

Always emit (except on options A and D, which emit `[]`):

```json
{
  "next_steps": [
    {
      "command": "/cast-refine-requirements",
      "rationale": "Draft requirements for your first goal — produces docs/requirement/<goal>_requirements.human.md.",
      "artifact_anchor": "docs/requirement/"
    },
    {
      "command": "/cast-explore",
      "rationale": "Open-ended research-and-plan pipeline if you'd rather explore than write requirements first.",
      "artifact_anchor": "docs/exploration/"
    },
    {
      "command": "(read)",
      "rationale": "Skim the project-local CLAUDE.md you just wrote — it's the contract every cast-* agent honors.",
      "artifact_anchor": "CLAUDE.md"
    }
  ]
}
```

The `(read)` pseudo-command is the documented placeholder per the typed-`next_steps`
contract (Phase 3a sp4d) for "human action, not an invocable skill".

## Idempotence + safety details

- `.gitkeep` writes are safe to repeat (`touch` is a no-op on existing files).
- `CLAUDE.md` is **never** overwritten without explicit user confirmation. The Overwrite
  branch backs up first via `bin/_lib.sh::backup_if_exists`.
- Existing populated `docs/`: if the user already has `docs/api/` (e.g., from MkDocs),
  `/cast-init` only adds the seven canonical subdirectories. It never touches existing
  top-level files in `docs/` or unrelated subdirectories.
- The skill never accepts user-supplied paths — `<cwd>` is always derived from `pwd`.
  Eliminates path-traversal concerns.

## Output (terminal JSON, contract-v2)

```json
{
  "contract_version": "2",
  "agent_name": "cast-init",
  "task_title": "Initialize Diecast project layout",
  "status": "completed",
  "summary": "Scaffolded seven docs/ subdirectories and wrote project-local CLAUDE.md.",
  "artifacts": [
    {"path": "docs/exploration/.gitkeep", "type": "data", "description": "Canonical exploration directory keeper."},
    {"path": "docs/spec/.gitkeep", "type": "data", "description": "Canonical spec directory keeper."},
    {"path": "docs/requirement/.gitkeep", "type": "data", "description": "Canonical requirement directory keeper."},
    {"path": "docs/plan/.gitkeep", "type": "data", "description": "Canonical plan directory keeper."},
    {"path": "docs/design/.gitkeep", "type": "data", "description": "Canonical design directory keeper."},
    {"path": "docs/execution/.gitkeep", "type": "data", "description": "Canonical execution directory keeper."},
    {"path": "docs/ui-design/.gitkeep", "type": "data", "description": "Canonical ui-design directory keeper."},
    {"path": "CLAUDE.md", "type": "data", "description": "Project-local Claude Code conventions; references cast-init-conventions spec."},
    {"path": ".claude/settings.json", "type": "data", "description": "Claude Code settings with appended cast-hook UserPromptSubmit + Stop entries (omitted from artifacts when --no-hooks was passed)."}
  ],
  "errors": [],
  "next_steps": [/* see Step 5 */],
  "human_action_needed": false,
  "human_action_items": []
}
```

## Anti-patterns

- **Inlining the conventions in the template.** Push elaboration into the spec instead.
  The template is a pointer.
- **Adding a fifth option to the merge prompt.** Decision #5 locks it at four. Resist.
- **Replicating `backup_if_exists` in Python.** Call the bash helper via subprocess.
  Forking the helper between languages was an explicit anti-pattern in the plan.
- **Touching existing top-level `docs/` files.** `/cast-init` only adds the seven
  canonical subdirectories. Anything else is the user's.
- **Accepting a user-supplied target directory.** `<cwd>` is always `pwd`. No flag
  surface to override — eliminates path-traversal and "wrong project" footguns.
- **Inverting the `--no-hooks` polarity.** Hooks are installed by default
  (Decision #8). `--no-hooks` is the opt-out; there is no `--hooks` flag. Skipping the
  install also means skipping the "Restart Claude Code…" final line.
- **Calling the installer in a way that overrides existing hooks.** The installer is a
  polite citizen — it appends to whatever already lives in `settings.json` and never
  deletes a third-party hook. `/cast-init` MUST go through `cast-hook install` (or
  `install_hooks.install(...)`); never hand-edit `settings.json` from this skill.
