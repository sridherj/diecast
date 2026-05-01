# Sub-phase 6: Wire Installer into `/cast-init`

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Add a final "install cast-hook entries" step to the `/cast-init` skill. Default ON; `--no-hooks`
opts out. Project-level scope by default (`<project_root>/.claude/settings.json`); `--user`
flag for global install. Document the surface so end users know they can also run
`cast-hook install` / `cast-hook uninstall` directly.

## Dependencies

- **Requires completed:** sp5 (the installer must be real, not the placeholder).
- **Assumed codebase state:** `/cast-init` is defined as either a skill markdown file
  under `agents/cast-init/` or as a script under `bin/`. Confirm at impl time — see
  Step 6.1.

## Scope

**In scope:**
- Locate the `/cast-init` definition (skill markdown or shell entry).
- Append a hook-install step at the end. Wire it to call
  `install_hooks.install(project_root=<the goal repo root>)` (or the `cast-hook install`
  CLI form, whichever fits the existing cast-init shape).
- Add `--no-hooks` opt-out flag/parameter to cast-init's surface.
- Add a final printed line: "Restart Claude Code to activate the hooks."
  (per Risks #5 in the plan).

**Out of scope (do NOT do these):**
- Reworking other parts of cast-init.
- Adding a new test file specifically for cast-init's hook-install integration — the
  installer's own tests (sp5) cover correctness; sp8 covers end-to-end against a tmp
  project.
- Auto-uninstall on package removal (Decision out-of-scope).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-init/cast-init.md` (or wherever) | Modify | Existing skill |
| Possibly `bin/cast-init` | Modify | If it exists as a script |

## Detailed Steps

### Step 6.1: Locate `/cast-init`

```bash
find . -maxdepth 4 -type f \( -name "cast-init*" -o -path "*/cast-init/*" \) 2>/dev/null \
  | grep -v __pycache__ | grep -v node_modules
```

Expect one or more of:
- `agents/cast-init/cast-init.md` (skill prompt)
- `bin/cast-init` (script entry)
- `.claude/skills/cast-init/SKILL.md` (skill SKILL file)

Read whichever is the actual orchestrator for cast-init. The plan calls out
`agents/cast-init/cast-init.md` as the likely location but says "confirm at impl time."

### Step 6.2: Add the hook-install step

The exact shape depends on what `/cast-init` looks like. Two patterns are possible:

**Pattern A: cast-init is a markdown skill prompt.** Add a step in the workflow section:

```markdown
## Step N: Install cast-hook entries

> Skip with `--no-hooks`.

Install the Claude Code hooks that capture user-typed `/cast-*` slash commands as
top-level `agent_run` rows.

```bash
cast-hook install   # writes to <project>/.claude/settings.json
```

This is **idempotent**: re-running is safe. It NEVER replaces existing third-party
hooks — only appends our entries. To remove later: `cast-hook uninstall`.

**After install: restart Claude Code to activate the hooks.**
```

**Pattern B: cast-init is a Python/bash script.** Add a function call near the end:

```python
from cast_server.cli import install_hooks
from pathlib import Path

if not args.no_hooks:
    install_hooks.install(project_root=Path(project_root_arg))
    print("Restart Claude Code to activate the hooks.")
```

Match the existing surface — if other steps in cast-init are bullets in markdown, this is
a bullet. If they're script invocations, this is a script invocation.

### Step 6.3: Document the standalone CLI form

In `cast-init`'s "Where this can also be run" or similar section (or just inline in the
step), add a one-liner:

> The hook install is also available standalone: `cast-hook install`,
> `cast-hook install --user` (global), `cast-hook uninstall`. Run from your project root.

### Step 6.4: Verify the wiring

Run `/cast-init` against a tmp project that already has unrelated hooks. Steps:

```bash
TMP=$(mktemp -d)
cd $TMP
git init                                 # marker
mkdir -p .claude
cat > .claude/settings.json <<EOF
{
  "hooks": {
    "PreCompact": [
      {"hooks": [{"type": "command", "command": "echo unrelated", "timeout": 5}]}
    ]
  }
}
EOF

# Run cast-init in this project (exact invocation depends on how /cast-init is dispatched).
# If it's a skill, you'd invoke it through Claude Code; for verification just call the
# install path directly:
cast-hook install

# Verify
cat .claude/settings.json
# Expect: PreCompact preserved, UserPromptSubmit + Stop now have our entries.
```

### Step 6.5: Failure-mode probe

In the same tmp project:

```bash
# Make settings read-only and re-run cast-init
chmod 0o444 .claude/settings.json
cast-hook install
# Expect: SystemExit with readable message naming --user as workaround.
chmod 0o644 .claude/settings.json
```

This confirms the user-safety failure-mode surface (Decision #9) propagates through the
cast-init wiring.

## Verification

### Automated Tests (permanent)

None added in this sub-phase. The installer's tests (sp5) cover the contract.

### Validation Scripts (temporary)

The Step 6.4 + Step 6.5 manual probes.

### Manual Checks

```bash
git diff agents/cast-init/                # or wherever cast-init lives
git status                                # confirm only the cast-init file changed
```

### Success Criteria

- [ ] cast-init has a clearly-marked "Install cast-hook entries" step at or near the end.
- [ ] `--no-hooks` opt-out documented.
- [ ] Standalone `cast-hook install` / `uninstall` documented.
- [ ] The "Restart Claude Code to activate the hooks." line is printed/included.
- [ ] Manual run against a tmp project preserves unrelated hooks and adds ours.
- [ ] Read-only settings.json failure surfaces a readable message (not a traceback).

## Execution Notes

- The plan acknowledges that `/cast-init` is "wherever cast-init is defined" — there's
  some indirection. Read the file before editing to match its style.
- Risks #5: Claude Code is already running when the user does `/cast-init`. New hooks in
  settings.json don't take effect until restart. Surface this prominently.
- **Spec-linked files:** sp7 will author `cast-hooks.collab.md`. The cast-init wiring
  is part of that spec's "how to install" surface, so cite this file's path in the spec.
- **Skill/agent delegation:** if `/cast-init` is itself a skill, you don't necessarily
  need to invoke another skill from it — just call the installer directly.
- The `--no-hooks` flag should default to **off** (i.e., hooks ARE installed by default,
  per Decision #8). Make sure the flag's polarity is correct.
