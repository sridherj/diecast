# cast-review-code

Launch an independent Claude Code review session in a new terminal tab with full context.

Builds a self-contained review brief capturing intent, dependencies, session context,
and relevant specs, then launches a separate Claude Code instance to perform the review.

## Type

`cast-agent`

## I/O Contract

- **Input:** File paths (optional). If omitted, reviews all files from `git diff`.
- **Output:** Review session launched in a new terminal tab. Review brief written to `/tmp/review-brief-<timestamp>.md`.
- **Config:** `config.yaml` (model: opus, timeout: 120m, context: lightweight, interactive: true)

## Usage

```bash
/cast-review-code                          # review all git changes
/cast-review-code src/foo.py src/bar.py    # review specific files
```

## How It Works

1. **Gather files** — uses provided paths or `git diff --name-only`
2. **Find specs** — matches changed files against `docs/specs/_registry.md` linked_files
3. **Build review brief** — writes a self-contained brief to `/tmp/` with intent, dependencies, session context, specs, diff summary, and recent commits
4. **Launch review tab** — resolves the terminal binary via `agents/_shared/terminal.py:resolve_terminal()` (walks `$CAST_TERMINAL` → `$TERMINAL` → `~/.cast/config.yaml:terminal_default`; raises `ResolutionError` linked to `docs/reference/supported-terminals.md` if all three are empty), then opens a new tab running `claude --permission-mode acceptEdits` with the brief as context and `/review` as the workflow

## Notes

- The review session is fully independent — no shared context with the invoking session
- The brief file is the context bridge — it must be self-contained
- Spec matching uses YAML frontmatter `linked_files` from spec files
