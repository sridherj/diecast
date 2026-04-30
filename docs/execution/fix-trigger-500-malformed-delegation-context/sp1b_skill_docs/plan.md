# Sub-phase 1b: SKILL.md doc reword — `output_dir` is optional

> **Pre-requisite:** Read `docs/execution/fix-trigger-500-malformed-delegation-context/_shared_context.md` before starting this sub-phase.

## Objective

Update `skills/claude-code/cast-child-delegation/SKILL.md` so the parent-facing delegation docs match the spec (`docs/specs/cast-delegation-contract.collab.md:66`) and the new server behavior (sp1a). Specifically: line 126 must mark `delegation_context.output.output_dir` as **optional** with a documented goal-dir fallback, instead of describing it as required.

## Dependencies

- **Requires completed:** None. This sub-phase is independent of sp1a — the doc reword reflects intent already locked in by spec line 66; sp1a brings the server into compliance, this brings the skill into compliance, and either can land first.
- **Assumed codebase state:** `skills/claude-code/cast-child-delegation/SKILL.md` line 126 still reads:
  > `delegation_context.output.output_dir` (string): Directory where child should write artifacts (typically `{output_dir}` from your preamble).

## Scope

**In scope:**

- Replace the single line at `skills/claude-code/cast-child-delegation/SKILL.md:126` with the reworded text shown in Step 2.1.
- Verify line 127 (`expected_artifacts`) and surrounding bullets remain unchanged.
- Do not reflow the rest of the document.

**Out of scope (do NOT do these):**

- Editing any other line of `SKILL.md` (no rewrites, no whitespace cleanup, no reordering of bullets).
- Editing `agents/cast-orchestrate/cast-orchestrate.md` or any other agent prompt.
- Editing `docs/specs/cast-delegation-contract.collab.md` — the spec already documents the fallback at line 66.
- Editing server code (sp1a owns that).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `skills/claude-code/cast-child-delegation/SKILL.md` | Modify | Line 126 documents `output_dir` as required without a fallback note |

## Detailed Steps

### Step 2.1: Reword the `output_dir` bullet on line 126

In `skills/claude-code/cast-child-delegation/SKILL.md`, locate this exact line:

```markdown
- `delegation_context.output.output_dir` (string): Directory where child should write artifacts (typically `{output_dir}` from your preamble).
```

Replace it with:

```markdown
- `delegation_context.output.output_dir` (string, **optional**): Directory where child should write artifacts. Defaults to the goal directory (`<goals>/<goal_slug>`) when omitted — see `docs/specs/cast-delegation-contract.collab.md:66`. Pass `{output_dir}` from your preamble explicitly when you need a non-default location (e.g., a sub-phase under `docs/execution/<project>`).
```

The replacement is a single line; do not split it across multiple lines unless the surrounding bullets are already wrapped (they are not — keep style consistent with the bullets above and below).

### Step 2.2: Confirm no collateral damage

```bash
cd /data/workspace/diecast
git diff skills/claude-code/cast-child-delegation/SKILL.md
```

The diff must show exactly one removed line (the old line 126) and one added line (the reworded line). No other deletions, additions, or whitespace-only changes.

### Step 2.3: Render-check the line

Open `skills/claude-code/cast-child-delegation/SKILL.md` in a Markdown viewer (or simply re-read it) to confirm the bullet renders cleanly inside the surrounding "**Key fields:**" list — i.e., it is still a single bullet, the bold `**optional**` renders, and the inline code references for paths/files still tokenize as code.

## Verification

### Automated Tests (permanent)

None. Documentation-only changes; no automated test surface in this repo for SKILL.md content.

### Validation Scripts (temporary)

```bash
# Confirm exactly one bullet line was changed.
git diff --stat skills/claude-code/cast-child-delegation/SKILL.md
# Expected: 1 file changed, 1 insertion(+), 1 deletion(-)
```

```bash
# Confirm the new line literally contains "**optional**" and the spec reference.
grep -n '`delegation_context.output.output_dir`' skills/claude-code/cast-child-delegation/SKILL.md
# Expected: a single hit on (was) line 126, now containing "**optional**"
#           and "cast-delegation-contract.collab.md:66".
```

### Manual Checks

1. `git diff skills/claude-code/cast-child-delegation/SKILL.md` shows a single-line replacement on what used to be line 126 — no other diff.
2. The reworded line includes the literal substring `**optional**`.
3. The reworded line includes the literal substring `cast-delegation-contract.collab.md:66`.
4. The reworded line keeps the `{output_dir}` reference so callers know how to override.
5. The line above (about `delegation_context.context` custom fields) and the line below (about `expected_artifacts`) are byte-identical to before.

### Success Criteria

- [ ] Line 126 in `skills/claude-code/cast-child-delegation/SKILL.md` matches the reworded text in Step 2.1 verbatim.
- [ ] No other line in the file is modified.
- [ ] `git diff --stat` reports exactly `1 insertion(+), 1 deletion(-)` for that file.
- [ ] No other files were touched in this sub-phase.

## Execution Notes

- **Spec-linked files:** `SKILL.md` is parent-facing documentation, not a spec. The change is asserting alignment with `docs/specs/cast-delegation-contract.collab.md:66`, which already documents the fallback behavior. Read that line of the spec before editing to confirm the wording you reference is accurate.
- **Single-line discipline.** The plan deliberately scopes this to one line. If you find yourself reading more than ±3 surrounding lines or considering broader cleanup, stop — that's scope creep. File a follow-up note instead.
- **No emoji, no rephrasing for style.** Keep the technical, terse tone of the surrounding bullets. The reworded line is provided verbatim; do not "improve" it.
- **Parallel safety with sp1a.** sp1a touches `cast-server/` files only; sp1b touches `skills/claude-code/cast-child-delegation/SKILL.md` only. No conflict possible. Either order of merge works.
