# cast-init File Conventions

> **Spec maturity:** draft
> **Version:** 1
> **Date:** 2026-04-30
> **Owner:** Diecast core
> **Linked files:** `skills/claude-code/cast-init/SKILL.md`, `templates/CLAUDE.md.template`, every `agents/cast-*/cast-*.md` that writes a `.md` artifact

This spec is the **single source of truth** for the file conventions adopted by `/cast-init`
and honored by every `cast-*` agent that writes artifacts under a project's `docs/` tree.
The project-local `CLAUDE.md` written by `/cast-init` references this spec by path; it
**never** inlines the rules. When the rules change, this spec changes — the template does
not.

The shape follows `templates/cast-spec.template.md` (User Story / Independent Test /
Acceptance Scenarios / `FR-NNN` / `SC-NNN`).

---

## User Stories

### US1 — Authorship suffixes signal who wrote a file (Priority: P1)

**As a** contributor reading a goal directory,
**I want to** know at a glance whether a `.md` file was authored by a human, an agent, or
both,
**so that** I can apply appropriate review scrutiny and edit etiquette without opening
the file.

**Independent test:** Create three files in a fresh project — `requirements.human.md`,
`research.ai.md`, `plan.collab.md`. The reader should be able to predict who wrote each
without opening it. The convention also drives agent default write paths (FR-006).

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a `cast-*` agent writes a fully agent-generated artifact (e.g.,
  research notes, summaries), THE SYSTEM SHALL use the `.ai.md` suffix.
- **Scenario 2:** WHEN a contributor edits an `.ai.md` artifact substantively (≥20% of
  lines changed, OR a structural section added/removed), THE SYSTEM SHALL graduate the
  file by renaming `.ai.md` → `.collab.md` in the same commit.
- **Scenario 3:** WHEN `/cast-refine-requirements` writes the first-pass requirements
  draft, THE SYSTEM SHALL use the `.human.md` suffix because the file is meant to be
  edited and owned by a human reviewer thereafter.

### US2 — Date prefixes establish chronological context (Priority: P2)

**As a** contributor browsing `docs/plan/` or `docs/design/`,
**I want to** see plan / design files sorted in chronological order by filename,
**so that** I can find the latest plan without consulting `git log`.

**Independent test:** `ls docs/plan/` shows files sorted oldest-first when `YYYY-MM-DD-`
prefixes are present.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a `cast-*` agent writes a plan or design artifact directly under
  `docs/plan/` or `docs/design/`, THE SYSTEM SHALL prefix the filename with
  `YYYY-MM-DD-` (UTC date the agent ran).
- **Scenario 2:** WHEN an artifact lives inside a goal-named subdirectory
  (e.g., `docs/exploration/<goal>/research_notes.ai.md`), THE SYSTEM SHALL OMIT the date
  prefix because the goal directory already namespaces the file.

### US3 — `_v2` versioning preserves load-bearing prior versions (Priority: P3)

**As a** reviewer of a major rewrite,
**I want to** keep the prior version readable side-by-side with the new one,
**so that** I can audit what changed without diffing through git history.

**Independent test:** Rename `plan.collab.md` → `plan_v2.collab.md` when the v1 plan must
remain visible in the directory listing.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a contributor produces a substantive rewrite that intentionally
  preserves the prior version as historical context, THE SYSTEM SHALL append `_v2`,
  `_v3`, … before the suffix (e.g., `plan_v2.collab.md`).
- **Scenario 2:** WHEN ordinary revisions are made, THE SYSTEM SHALL NOT use `_vN`
  suffixes; ordinary revisions live in git history.

### US4 — Goal directories adopt a flat-vs-folder heuristic (Priority: P2)

**As a** contributor starting a new goal,
**I want to** know whether to write a single file or a goal-named subdirectory,
**so that** small goals stay legible and large goals stay organized.

**Independent test:** A 2-file goal lives flat under `docs/<area>/`. A 5-file goal lives
under `docs/<area>/<goal>/`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the goal produces ≤3 artifact files, THE SYSTEM SHALL use the flat
  layout: `docs/requirement/<goal>_requirements.human.md`,
  `docs/plan/<date>-<goal>-overview.collab.md`.
- **Scenario 2:** WHEN the goal produces >3 artifact files OR includes structured outputs
  (e.g., research notes plus playbooks plus summary), THE SYSTEM SHALL use the folder
  layout: `docs/exploration/<goal>/research_notes.ai.md`,
  `docs/exploration/<goal>/playbooks/`, etc.

### US5 — Per-agent default write paths are predictable (Priority: P1)

**As a** contributor invoking a `cast-*` agent,
**I want to** know in advance where the artifact will land,
**so that** I can configure CI / pre-commit hooks against a stable path.

**Independent test:** Invoke each agent in the table below; assert the artifact lands at
the documented path.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-web-researcher` runs against goal `<g>`, THE SYSTEM SHALL
  write the primary artifact to `docs/exploration/<g>/research_notes.ai.md`.
- **Scenario 2:** WHEN `cast-high-level-planner` runs against goal `<g>` on date `<d>`,
  THE SYSTEM SHALL write the artifact to `docs/plan/<d>-<g>-overview.collab.md`.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Authorship suffix MUST be one of `.human.md`, `.ai.md`, `.collab.md`. No bare `.md` for goal artifacts. | Specs use `.collab.md`; templates use `.template.md`. |
| FR-002 | Graduation rule: rename `.ai.md` → `.collab.md` when a human edit changes ≥20% of lines OR adds/removes a section. | Threshold is a heuristic; PR reviewers decide edge cases. |
| FR-003 | Date prefix `YYYY-MM-DD-` MUST be applied to top-level artifacts under `docs/plan/` and `docs/design/`. | UTC date; matches `RUN_TIMESTAMP` date component. |
| FR-004 | Date prefix MUST NOT be applied to artifacts inside a goal-named subdirectory. | The directory namespaces the file. |
| FR-005 | `_v2`/`_v3` versioning MAY be applied to preserve historical context. SHOULD be rare. | Prefer git history for ordinary revisions. |
| FR-006 | Per-agent default write paths SHALL match the table in §"Per-agent default write paths". | Every cast-* agent that writes a `.md` artifact references this table. |
| FR-007 | Flat layout SHALL be used for goals with ≤3 artifact files. Folder layout for >3 OR structured outputs. | The agent decides at write-time based on its own output cardinality. |
| FR-008 | The `CLAUDE.md` template written by `/cast-init` MUST reference this spec by path and MUST NOT inline the conventions. | Single-source-of-truth; spec is canonical. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A new contributor can identify the author of any `.md` file in a Diecast project from its filename alone. | Manual readability check; documented in `docs/troubleshooting.md`. |
| SC-002 | Every `cast-*` agent's write path matches the per-agent table. | `tests/test_cast_init.sh` Scenario 5 + per-agent integration tests in `tests/`. |
| SC-003 | The `CLAUDE.md` template references this spec by path; the conventions are not duplicated inline. | `grep -F 'docs/specs/cast-init-conventions.collab.md' templates/CLAUDE.md.template` returns a hit; visual review confirms no inline rules. |
| SC-004 | The spec is registered in `docs/specs/_registry.md`. | `grep -F '\| cast-init-conventions ' docs/specs/_registry.md` returns a hit. |

## Authorship suffixes

| Suffix | Author | Examples |
|---|---|---|
| `.human.md` | Human-authored. Edits stay with the human reviewer. | `requirements.human.md` |
| `.ai.md` | Agent-authored, no substantive human edits yet. | `research.ai.md`, `summary.ai.md`, `decomposition.ai.md` |
| `.collab.md` | Mixed authorship over time (human + agent). | `plan.collab.md`, `refined_requirements.collab.md`, all `docs/specs/*.collab.md` |

**Graduation rule:** rename `.ai.md` → `.collab.md` when human edits become substantive
(≥20% of lines changed, OR a structural section added/removed). The rename happens in the
same commit as the substantive edit.

## Date prefixes

`YYYY-MM-DD-<slug>.md` for plan and design docs that benefit from chronological sort.

- **Apply** to: top-level artifacts under `docs/plan/` and `docs/design/`.
- **Skip** for: artifacts inside a goal-named subdirectory (`docs/exploration/<goal>/…`,
  `docs/execution/<goal>/<phase>/…`); the directory already namespaces them.

The date is the UTC date the agent ran (matches the date component of the run's
`RUN_TIMESTAMP` per `bin/_lib.sh`).

## `_v2` versioning

Append `_v2`, `_v3`, … before the suffix when the prior version must remain visible in
the directory listing as historical context (e.g., a substantive rewrite the team needs
to compare side-by-side).

Use sparingly — git history is the default channel for revisions. The cost of `_vN`
filenames is that consumers (other agents, CI hooks) must hard-code the `_vN` to find
the latest; prefer in-place revisions whenever the prior version need not stay visible.

## `<goal_name>` flat-vs-folder heuristic

| Layout | When to use | Example |
|---|---|---|
| **Flat** | Goal produces ≤3 artifact files. | `docs/requirement/auth-rewrite_requirements.human.md`, `docs/plan/2026-04-30-auth-rewrite-overview.collab.md` |
| **Folder** | Goal produces >3 artifact files OR structured outputs (research notes + playbooks + summary). | `docs/exploration/auth-rewrite/research_notes.ai.md`, `docs/exploration/auth-rewrite/playbooks/`, `docs/exploration/auth-rewrite/summary.ai.md` |

The agent decides at write-time based on its own output cardinality. Promotion from flat
to folder is a manual operation: `mkdir docs/<area>/<goal>/ && git mv` the existing files
in.

## Per-agent default write paths

| Agent | Default write path |
|---|---|
| `cast-refine-requirements` | `docs/requirement/<goal>_requirements.human.md` (flat) or `docs/requirement/<goal>/requirements.human.md` (folder) |
| `cast-goal-decomposer` | `docs/exploration/<goal>/decomposition.ai.md` |
| `cast-explore` | `docs/exploration/<goal>/` (subdirectory per goal) |
| `cast-web-researcher` | `docs/exploration/<goal>/research_notes.ai.md` |
| `cast-code-explorer` | `docs/exploration/<goal>/code_exploration.ai.md` |
| `cast-playbook-synthesizer` | `docs/exploration/<goal>/playbooks/` |
| `cast-high-level-planner` | `docs/plan/<date>-<goal>-overview.collab.md` |
| `cast-detailed-plan` | `docs/plan/<date>-<goal>-<phase>-detail.collab.md` |
| `cast-update-spec` | `docs/spec/<spec>.collab.md` |
| `cast-task-suggester` | (DB-backed; no markdown artifact) |
| `cast-orchestrate` | `docs/execution/<goal>/<phase>/` |
| `cast-subphase-runner` | `docs/execution/<goal>/<phase>/<subphase>/` |
| `cast-preso-*` | `docs/design/<preso>/` |

## Cross-references

- **`docs/specs/cast-delegation-contract.collab.md`** — child-agent dispatch contract.
  Every cast-* skill that delegates references this contract; `/cast-init` itself does
  not delegate at runtime (the 4-option prompt is delegated to
  `cast-interactive-questions`).
- **`docs/specs/cast-output-json-contract.collab.md`** — terminal-output JSON schema.
  Every cast-* skill emits its terminal output per this schema, including the typed
  `next_steps` shape that `/cast-init` produces (US14).

## Open Questions

(none — v1 surface is locked per Phase 4 plan-review 2026-04-30)
