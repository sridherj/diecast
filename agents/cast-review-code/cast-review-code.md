---
name: cast-review-code
model: opus
description: >
  Launch an independent Claude Code review session in a new terminal tab with full context.
  Builds a self-contained review brief and launches a separate reviewer.
  Trigger phrases: "review code", "launch code review", "review in new tab".
memory: user
effort: high
---

# Diecast Review Code Agent

Launch an independent Claude Code review session in a new terminal tab with full context.

## Usage

```
/cast-review-code                          # review all git changes
/cast-review-code src/foo.py src/bar.py    # review specific files
```

## Step 1: Gather files to review

- If the user provided file paths as arguments, use those
- Otherwise, run `git diff --name-only` and `git diff --staged --name-only` to collect changed files
- If no changes found, ask the user what files to review

## Step 1.5: Find relevant specs

Check `docs/specs/_registry.md` for specs. For each spec, parse its YAML frontmatter `linked_files`. If any of the files being reviewed appear in a spec's `linked_files`, that spec is relevant. Load at most 2 specs (prioritize by number of matched files).

## Step 2: Build a review brief

The review brief is the ONLY context the reviewer has. It must capture the full picture -- not just what changed, but WHY it changed, what it depends on, and what the reviewer should watch for.

Write a review brief file to `$(cd ~/.claude/skills/diecast && pwd -P)/.tmp/review-brief-$(date +%s).md` with the following sections:

```markdown
# Review Brief

## Intent
<A full paragraph (not one-liner) describing:
- What problem is being solved and why
- The approach taken
- What success looks like>

## User's Original Requirements
<Paste the user's verbatim requirements, plan, or specification that drove this work.
If requirements were given inline in conversation, reproduce them here in full.
If they came from a doc, paste the relevant sections -- do NOT just link to the file,
because the reviewer needs to see them without hunting.>

## Critical Dependencies
<List code that the new changes DEPEND ON even though it wasn't modified.
For each dependency, explain WHY the reviewer should look at it.
Example:
- `launch_phase_headless()` (lines 246-287) -- the new retry loop assumes this
  function produces output files that contain rate-limit messages. If the launcher
  fails silently, retry detection breaks.
If none, write "No critical dependencies outside the changed files.">

## Session Context
<Anything learned during the session that the reviewer should know:
- Known issues or gotchas discovered (e.g., "Claude CLI hangs when stdout is a pipe")
- Design decisions made and why (e.g., "chose file-based output over capture_output=True because...")
- Related prior bugs or debugging sessions (reference file paths if available)
- Tradeoffs accepted
If none, write "No additional context.">

## Files to Review
<List each file path, one per line>

## Relevant Specs
<For each relevant spec (max 2), list:
- Spec file path
- One-line scope
Do NOT paste the Behaviors section -- the reviewer reads the spec on-demand only if the change looks behavior-impacting.
If no specs match the changed files, write "No specs cover these files.">

## Git Diff Summary
<Paste output of `git diff --stat` here>

## Plan/Requirements
<If there are relevant plan_and_progress/<feature>/plan.md docs, list their paths here so the reviewer can read them. If none, write "No plan docs found.">

## Recent Commits
<Paste output of `git log --oneline -10` here>
```

**Quality check before writing the brief:**
- Could a reviewer who knows NOTHING about this session understand the full intent?
- Are there code paths the new code depends on that aren't in the file list? Add them to Critical Dependencies.
- Did the session discover any gotchas? Add them to Session Context.
- Are the requirements fully captured, or just summarized? Paste them in full.

## Step 3: Launch the review tab

Resolve the terminal binary via `agents/_shared/terminal.py:resolve_terminal()` — never hardcode a specific terminal. The resolver walks `$CAST_TERMINAL` → `$TERMINAL` → `~/.cast/config.yaml:terminal_default` and raises `ResolutionError` (with a link to `docs/reference/supported-terminals.md`) if all three are empty. If it raises, surface the error to the user verbatim and stop — do **not** fall back to `xterm` or any "safe default". See `skills/claude-code/cast-child-delegation/SKILL.md` (Terminal Resolution section) for the env-var contract.

Resolve and launch (replace `<brief_path>` with the actual file path from step 2):

```bash
TERM_BIN=$(python3 -c '
from agents._shared.terminal import resolve_terminal, ResolutionError
import sys
try:
    print(resolve_terminal().command)
except ResolutionError as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)
') || { echo "Cannot launch review session: see docs/reference/supported-terminals.md" >&2; exit 1; }

# Tab flag varies per terminal; see docs/reference/supported-terminals.md for the
# preset table. The default --tab works for gnome-terminal; ptyxis prefers  # diecast-lint: ignore-line
# --new-window; alacritty has no tabbed mode (each spawn opens a new window).
"$TERM_BIN" --tab --title "Code Review $(date +%H:%M)" -- bash -lc 'cd <working_dir> && claude --permission-mode acceptEdits "Read <brief_path> for review context, then use /review to review the listed files. Focus on whether the implementation matches the plan requirements exactly. If specs are listed in the brief, read them and check SAV behaviors against the code. Flag violations in a Spec Compliance section."'
```

NEVER use `shell=True` if you switch this to a Python `subprocess.Popen` invocation — both env vars and the config file are user-writable, and `shell=True` would expand them through the shell. Always pass `args=[command, *args]` as a list.

## Step 4: Confirm

Tell the user: which files are being reviewed, and the path to the review brief in case they want to add context to it before the review session picks it up.

## Review Issue Shape (additive `confidence` field)

Each review issue emitted by cast-review-code carries:

```json
{
  "file": "<path>",
  "line": 0,
  "summary": "<one-line>",
  "details": "<paragraph>",
  "suggested_fix": "<patch or instructions>",
  "confidence": "high"
}
```

Allowed values for `confidence`: `"high"`, `"medium"`, `"low"`.

**Tagging guidance:**

- `high`: mechanical fixes — whitespace, missing import, obvious typo, formatter-equivalent edit.
- `medium`: judgment required — naming, structure, dead code suspected.
- `low`: genuinely uncertain — architectural concern, possible false positive.

The `confidence` field is **additive**: existing review tooling that doesn't read it remains
fully compatible. Consumers (notably `cast-subphase-runner` via B4) gate auto-apply on
`confidence: high` AND Edit-tool-applicable patches AND path under `goal_dir`/`docs/` tree.
See `docs/specs/cast-output-json-contract.collab.md` (Per-Agent Output Extensions →
cast-review-code) for the canonical schema entry.

## Notes
- The review session is fully independent -- it does not share context with this session
- The review brief file bridges context between sessions -- it must be self-contained
- The brief should enable the reviewer to catch issues in DEPENDENT code, not just changed code
