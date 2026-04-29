---
name: cast-create-execution-plan
model: opus
description: >
  Takes a plan document and splits it into independently executable sub-phases, each designed
  to run in a separate Claude context. Produces structured output in docs/execution/<project>/.
  Trigger phrases: "create execution plan", "split plan into sub-phases", "executable sub-phases".
memory: user
effort: high
---

# Diecast Create Execution Plan Agent

Take a plan document and split it into independently executable sub-phases, each designed to run in a **separate Claude context**. Produces structured output in `docs/execution/<project>/`.

## Output Routing

Your prompt preamble provides two distinct directories:
- `goal_dir` (e.g., `.diecast/`) — Diecast tracking only. Write **ONLY** the final `.agent-{run_id}.output.json` contract file here.
- `output_dir` (your working directory) — write ALL execution plan artifacts here:
  - `docs/execution/<plan-name>/_manifest.md`
  - `docs/execution/<plan-name>/_shared_context.md`
  - `docs/execution/<plan-name>/sp*_*/plan.md`
  - All gate files, review summaries, etc.

Never write execution plan files into `goal_dir` / `.diecast/` — that directory is for Diecast tracking only.

## Step 1: Gather Inputs

- First argument: plan file path (required)
- Second argument: writeup/background file path (optional)
- If plan path is missing, ask explicitly using AskUserQuestion
- Read both files fully. Understand the intent, scope, and structure of the plan.
- If there are decisions from plan review phase available, read them and use them to understand the context. They are usually at the end of the plan file.

## Step 2: Determine Project Name

- Derive from plan filename or title (e.g., `agent_swarm_foundation.md` -> `agent_swarm`)
- Create directory: `docs/execution/<project-name>/`

## Step 3: Analyze & Split into Sub-Phases

Analyze the plan and identify natural sub-phase boundaries based on:
- **Dependencies** -- what must complete before something else can start
- **Logical grouping** -- related tasks that should be done together
- **Parallelism** -- independent work that can run simultaneously
- **Size** -- prefer 7 focused sub-phases over 4 overloaded ones

**Naming convention:**
- Sequential: `sp1_<name>/plan.md`, `sp2_<name>/plan.md`
- Parallel: `sp3a_<name>/plan.md`, `sp3b_<name>/plan.md`

**Critical constraint:** Parallel sub-phases must NOT modify the same files. Explicitly verify this.

### Decision Gate Detection

When the plan contains **Decision Gates** (look for `### Decision Gate N:` headings or prose describing
points where execution must pause for human judgment), create gate entries:

- **Gate files** use the `gate_` prefix: `gate_1_<name>.md`, `gate_2_<name>.md`
- **Gate IDs** use the `G` prefix: `G1`, `G2`, etc. -- visually distinct from sub-phase IDs
- Subsequent sub-phases that depend on the gate's outcome use the gate ID in their dependencies
- Gate files are NOT executable sub-phases -- the orchestrator stops when it encounters them

**Gate file template:**

```markdown
# Decision Gate N: <Title>

> **Context:** Read the output of Sub-phase N before making this decision.

## Decision Criteria

<What to evaluate -- specific metrics, thresholds, observations from the plan>

## Options

### Option A: <Name>
- **Condition:** <when to choose this>
- **Action:** Mark sub-phases [X, Y] as "Skipped" in manifest, proceed from Sub-phase Z
- **Rationale:** <why>

### Option B: <Name>
- **Condition:** <when to choose this>
- **Action:** Proceed with all sub-phases as planned
- **Rationale:** <why>

## How to Proceed

1. Review Sub-phase N output at `docs/execution/<project>/spN_*/output.md`
2. Evaluate against criteria above
3. Update `_manifest.md`: set this gate's status to "Done", add chosen option to Notes
4. If skipping sub-phases, set their status to "Skipped"
5. Re-run: `/cast-orchestrate docs/execution/<project> --from-subphase GN`
```

Present the proposed breakdown to the user:
- List each sub-phase with a one-line summary
- Show the dependency graph (which sub-phases depend on which)
- Mark parallel groups and decision gates
- Ask for feedback using AskUserQuestion before proceeding

## Step 4: Create `_shared_context.md`

A reference file read by every sub-phase at session start. This is NOT inlined into each sub-phase -- Claude can read files, so keep it DRY.

Include these sections:

```markdown
# Shared Context: <Project Name>

## Source Documents
- Plan: `<path to plan>`
- Writeup: `<path to writeup>` (if provided)

## Project Background
<The "why" -- 2-3 paragraphs summarizing the vision, goals, and motivation from the writeup/plan>

## Codebase Conventions
<Key patterns, directory structures, naming conventions relevant to this project>

## Key File Paths
<Table of important existing files and their roles>

## Data Schemas & Contracts
<Any schemas, APIs, I/O contracts defined in the plan -- copy them verbatim>

## Pre-Existing Decisions
<Decisions from the plan's Review Decisions section or other context that constrain implementation>

## Relevant Specs
<For each spec in docs/specs/ whose linked_files overlap with files in the plan:
- Spec file path and one-line scope
Do NOT paste Behaviors -- sub-phase agents read specs on-demand only when modifying spec-linked files.
If no specs overlap, write "No specs cover files in this plan.">

## Sub-Phase Dependency Summary
<Table showing: Sub-phase | Type | Depends On | Blocks | Can Parallel With>
(Type: "Sub-phase" or "Gate" -- gates pause execution for human decisions)
```

## Step 5: Create Sub-Phase Plan Files

Each sub-phase plan file follows this template. **Verification gets ~30-40% of the file** -- it is the most important section.

```markdown
# Sub-phase N: <Title>

> **Pre-requisite:** Read `docs/execution/<project>/_shared_context.md` before starting this sub-phase.

## Objective
<What this sub-phase accomplishes and why it matters -- one paragraph>

## Dependencies
- **Requires completed:** <list sub-phases that must be done first, or "None">
- **Assumed codebase state:** <what should already exist from prior sub-phases>

## Scope
**In scope:**
- <bullet list of what this sub-phase covers>

**Out of scope (do NOT do these):**
- <bullet list of things to explicitly avoid -- prevents scope creep in fresh context>

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `path/to/file` | Create / Modify | Does not exist / Contains X |

## Detailed Steps

### Step N.1: <Title>
<Prescriptive instructions with code snippets, file paths, and exact commands>

### Step N.2: <Title>
...

## Verification

### Automated Tests (permanent)
<pytest tests that persist in the codebase -- include file paths and test names>

### Validation Scripts (temporary)
<One-off commands or scripts to verify the sub-phase worked -- can be deleted after>

### Manual Checks
<Human-verified items with exact commands to run>

### Success Criteria
<Binary yes/no checklist -- every item must pass>
- [ ] Criterion 1
- [ ] Criterion 2

## Execution Notes
<Gotchas, warnings, common mistakes, tips for the executing context>

**Spec-linked files:** If this sub-phase modifies files covered by a spec listed in `_shared_context.md`,
read the spec file and verify SAV behaviors are preserved.
```

### Claude Skill/Agent Delegation Pass

After drafting each sub-phase's Detailed Steps, scan every step and ask: "Is there an existing
Claude Code skill or agent that does this?" Check two sources: the agents table in `CLAUDE.md`
and the skill list in the system prompt.

If a skill/agent match exists:
- Replace the manual steps with a delegation line: `-> Delegate: /skill-name -- [context/inputs to pass]`
- Add a follow-up step: "Review `/skill-name` output for [what to verify]"
- Don't expand skill/agent-covered work into manual instructions -- provide just enough
  context for the skill to run

This is critical because Claude often skips available skills during execution if they aren't
explicitly called out in the sub-phase plan file.

### Enhancement Pass

After creating initial drafts of all sub-phases:
1. Add code snippets where instructions reference code
2. Add edge cases and error handling notes
3. Batch any clarifying questions and ask user using AskUserQuestion (one batch, not per-sub-phase)

## Step 6: Create `_manifest.md`

The execution index and progress tracker.

```markdown
# Execution Manifest: <Project Name>

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session
2. Tell Claude: "Read `docs/execution/<project>/_shared_context.md` then execute `docs/execution/<project>/spN_name/plan.md`"
3. After completion, update the Status column below

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|---------------|-----------|--------|-------|
| 1 | Sub-phase One Title | `sp1_name/` | -- | Not Started | |
| G1 | Decision Gate Title | `gate_1_name.md` | 1 | Not Started | Decides Sub-phase 2 scope |
| 2 | Sub-phase Two Title | `sp2_name/` | G1 | Not Started | |
| 3a | Sub-phase Three A Title | `sp3a_name/` | 2 | Not Started | Parallel with 3b |
| 3b | Sub-phase Three B Title | `sp3b_name/` | 2 | Not Started | Parallel with 3a |
| 4 | Sub-phase Four Title | `sp4_name/` | 3a, 3b | Not Started | |

Status: Not Started -> In Progress -> Done -> Verified -> Skipped

Gate rows (G-prefix IDs, `gate_` file prefix) pause the orchestrator for human decisions.
Sub-phases can be set to "Skipped" when a gate decision makes them unnecessary.

## Dependency Graph

<ASCII art showing the dependency flow>

## Execution Order

### Sequential Group 1
1. Sub-phase 1: <name>

### Sequential Group 2 (after Group 1)
2. Sub-phase 2: <name>

### Parallel Group 3 (after Group 2 -- run simultaneously)
3a. Sub-phase 3a: <name>
3b. Sub-phase 3b: <name>

### Sequential Group 4 (after Group 3)
4. Sub-phase 4: <name>

## Progress Log
<User updates this after each sub-phase>
```

## Step 7: Review Each Sub-Phase

Run `/cast-plan-review` on each sub-phase plan file with **SMALL CHANGE** mode (max 1 issue per section) to keep reviews lightweight.

Collect all review findings into `_review_summary.md`:

```markdown
# Review Summary: <Project Name>

## Open Questions
<Numbered list of unresolved questions that need user input>

## Review Notes by Sub-Phase
### Sub-phase 1: <name>
- <findings, if any>

### Sub-phase 2: <name>
- <findings, if any>
```

Present open questions to the user for resolution.

## Step 8: Final Summary

Output to the user:
1. List all created files with paths
2. Show the execution order (sequential + parallel groups)
3. Report count of open questions from review
4. Remind user how to execute: start a new Claude session per sub-phase

---

## Output Structure

```
docs/execution/<project-name>/
  _shared_context.md       # Cross-cutting context (read by every sub-phase)
  _manifest.md             # Execution order, dependency graph, status tracking
  sp1_<name>/plan.md       # Sequential sub-phase
  gate_1_<name>.md         # Decision gate (optional -- only when plan has gates)
  sp2_<name>/plan.md       # Sequential sub-phase
  sp3a_<name>/plan.md      # Parallel sub-phase (example)
  sp3b_<name>/plan.md      # Parallel sub-phase (example)
  sp4_<name>/plan.md       # Sequential sub-phase
  _review_summary.md       # Aggregated clarifications from /cast-plan-review
```

## Quality Bar

- Each sub-phase must be self-contained: a fresh Claude context + `_shared_context.md` must be sufficient
- Prefer more focused sub-phases over fewer overloaded ones
- Verification is the most important section -- invest ~30-40% of each sub-phase plan file here
- Parallel sub-phases must not modify the same files -- verify this explicitly during analysis
- Skill/agent delegations are explicit -- no manual steps for work a skill can do
- When in doubt about sub-phase boundaries, ask the user
