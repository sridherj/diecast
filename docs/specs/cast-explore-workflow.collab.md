# Cast Explore Workflow — N×M Exploration Engine Spec

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** agents/cast-explore-workflow/cast-explore-workflow.md, agents/cast-explore-workflow/workflow.mjs, agents/cast-explore-workflow/config.yaml, agents/cast-hat-researcher/cast-hat-researcher.md, agents/cast-playbook-synthesizer/cast-playbook-synthesizer.md, docs/plan/2026-06-20-exploration-pipeline-nxm-3a-workflow-engine.md

Behavior contract for the **N×M exploration Workflow engine** (sub-phase 3a). Greenfield —
no prior spec governed it (deferred from 1a to 3a). The engine runs the starter exploration
as a deterministic Claude **Workflow**: interactive Phase-1 (intent → decompose → approve →
hat-matrix) stays with the main agent; on approval a non-interactive JavaScript Workflow fans
research across `N steps × M_applicable(step)` hats — each `(step, hat)` cell a clean-context
`cast-hat-researcher` — then crosses a per-step synthesis barrier calling the **unchanged**
`cast-playbook-synthesizer`. Ships in PARALLEL to `cast-explore` (no migration).

> **Binding G1 correction (supersedes the detailed plan):** the engine is a **JavaScript
> Workflow script** (`workflow.mjs`, Workflow-tool inline-JS API: `agent()`, `parallel()`,
> `pipeline()`, `phase()`, `log()`, `budget`, `args`), NOT a Python `workflow.py`. The G1
> live-fire (`spike-1a-result.md`, run `wf_3ae6d3ec-45c`) proved the 2×2-isolated-cells +
> synthesis + terminal-signal model on the real tool. Entrypoint = a main-agent skill/command
> (Option A); subagents cannot launch workflows.

## User Stories

### US1 — Angle-independent N×M fan-out (Priority: P1)

**As a** user exploring a goal, **I want** every (step, hat) pair researched in its own
clean, isolated context, **so that** no hat's findings prime or pollute another's.

**Independent test:** launch the Workflow on a 2-step goal; inspect two hat notes for the same
step — they share no hat-specific framing and neither references the other hat's content.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the Workflow fans out a step, THE SYSTEM SHALL spawn exactly one
  `cast-hat-researcher` per `(step, hat_id)` in `M_applicable(step)`, each receiving ONLY
  `(step, hat_id, goal_context)`.
- **Scenario 2:** WHEN a cell is built, IF `goal_context` would carry another hat's note or
  another step's text, THE SYSTEM SHALL NOT include it — `goal_context` is the step-neutral
  intent string only.

### US2 — Deterministic Workflow orchestration (Priority: P1)

**As a** user, **I want** the fan-out + synthesis run as a deterministic background Workflow,
**so that** after approval it completes with zero further prompts.

**Independent test:** after the matrix-confirm gate, the run completes with no mid-run user input.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the matrix is confirmed, THE SYSTEM SHALL launch the JavaScript Workflow
  non-interactively and return control; the Workflow posts its own terminal signal on completion.
- **Scenario 2:** WHEN the Workflow runs, THE SYSTEM SHALL NOT issue any interactive prompt from
  `workflow.mjs` or any `cast-hat-researcher` cell.

### US3 — Per-step synthesis barrier, synthesizer unchanged (Priority: P1)

**As a** consumer of playbooks, **I want** one opinionated playbook per step synthesized from
that step's surviving hat notes, **so that** the existing playbook contract is preserved.

**Independent test:** a full run yields exactly one `playbooks/{NN}-{slug}.ai.md` per step;
`git diff` shows zero changes under `agents/cast-playbook-synthesizer/`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN all of a step's hat cells terminate, THE SYSTEM SHALL invoke the unchanged
  `cast-playbook-synthesizer` once for that step, fed the `M_applicable(step)` surviving hat notes.
- **Scenario 2:** WHEN resolving a step's surviving notes, THE SYSTEM SHALL glob
  `research/{NN}-{slug}-*.ai.md` on disk AND intersect with the 8-value `hat_id` vocabulary,
  excluding `-code.ai.md` and slug-prefix collisions.

### US4 — Relevance gating (Priority: P2)

**As a** user, **I want** gateable hats omitted from steps where they add nothing, **so that**
cost stays bounded without losing the always-on angles.

**Independent test:** on a pure-strategy step, `tool-landscape`/`ai-native` notes are ABSENT while
`contrarian`/`first-principles`/`90-10` are PRESENT.

**Acceptance scenarios:**

- **Scenario 1:** WHEN computing the hat-matrix, THE SYSTEM SHALL append `contrarian`,
  `first-principles`, `90-10` to every step unconditionally (never gated).
- **Scenario 2:** WHEN a step is pure-strategy, THE SYSTEM SHALL omit the relevant gateable hats
  from that step's hat list.

### US5 — Failure isolation + loud degradation (Priority: P1)

**As a** user, **I want** a failed hat cell to drop to null (logged + surfaced) without sinking
the step or run, **so that** partial failure is visible, never silent.

**Independent test:** force one cell to fail → run completes, that cell is surfaced in the
summary's dropped-cells section, and the step's playbook is still produced from survivors.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a cell fails (non-zero terminal / missing or `failed` output JSON),
  THE SYSTEM SHALL record it as a dropped cell with `(step, hat, reason)` and proceed with survivors.
- **Scenario 2:** WHEN ALL of a step's hats fail, THE SYSTEM SHALL write a DEGRADED placeholder
  playbook and flag the step degraded — NEVER invoke the synthesizer with empty input.

### US6 — Matrix-confirm cost transparency (Priority: P2)

**As a** user, **I want** to see the projected cell count + cost before launch, **so that** I
approve the bill knowingly.

**Independent test:** the matrix-confirm gate shows live cell count, synthesizer calls, model
tier, and a rough token/$ estimate, plus which gateables were dropped per step.

**Acceptance scenarios:**

- **Scenario 1:** WHEN presenting the matrix-confirm gate, THE SYSTEM SHALL surface a projected-cost
  line (live cells × model tier × rough token/$ estimate) and the dropped gateables per step.
- **Scenario 2:** THE SYSTEM SHALL surface, not block — no cost ceiling is enforced this round.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Entrypoint is a main-agent skill/command (`cast-explore-workflow`) that launches a JavaScript Workflow; not a subagent | Option A; subagents cannot launch workflows |
| FR-002 | Interactive Phase-1 (intent → decompose → approve → hat-matrix) precedes the non-interactive launch | All human gates before launch |
| FR-003 | Each `(step, hat_id)` cell runs in a fresh clean context receiving ONLY `(step, hat_id, goal_context)` | Angle independence by construction |
| FR-006 | The 4-lens decomposer (incl. its "10x" lens) is unchanged; gating is a research-layer device | Decomposer frozen |
| FR-007 | Relevance gating emits `M_applicable(step)`; always-on (`contrarian`/`first-principles`/`90-10`) never gated | hat-matrix arg |
| FR-008 | Exactly one playbook per step via the unchanged `cast-playbook-synthesizer` | Synthesizer input widens 1→M only |
| FR-014 | After approval the Workflow runs with zero further prompts | Non-interactive boundary |
| FR-015 | Concurrency cap `min(16, cores−2)` enforced natively by the tool; excess cells auto-queue; no hand-rolled queue | Surface queued/over-cap state |
| FR-016 | A failed cell drops to null, logged + surfaced; all-cells-failed → DEGRADED placeholder playbook | Surface-don't-suppress |
| FR-017 | md artifact paths unchanged: `research/{NN}-{slug}-{hat-id}.ai.md`, `playbooks/{NN}-{slug}.ai.md`, `summary.ai.md` | Hard `cast-high-level-planner` contract |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | `count(research/*.ai.md) == Σ M_applicable(step)` | Full run; filename-set equality vs persisted hat-matrix |
| SC-002 | No hat note references another hat's content (angle independence) | Inspect two same-step notes |
| SC-003 | A `…-90-10.ai.md` exists for every step (always-on) | glob check |
| SC-004 | Exactly one `playbooks/{NN}-{slug}.ai.md` per step (== N) | glob check |
| SC-005 | Gateable hats absent on pure-strategy steps; always-on present | glob check |
| SC-006 | Forced cell failure → run completes; cell surfaced in summary; step playbook from survivors | Failure-injection run |
| SC-007 | All-hats-fail step → DEGRADED placeholder, synthesizer not called empty | `tests/test_all_hats_fail_placeholder.mjs` |
| SC-008 | Barrier resolves surviving notes by glob ∩ hat_id vocab; `-code.ai.md` + slug-prefix collisions excluded | `tests/test_barrier_glob_intersection.mjs` |
| SC-009 | `summary.ai.md` produced; format matches `cast-explore` Phase-3 shape; dropped-cells section additive | Full run + format diff |

## Open Questions

- **Main-agent ↔ Workflow handoff shape:** the 1a live-fire confirmed non-blocking background +
  in-script terminal signal. Whether the launching skill should additionally surface a poll-helper
  (`/workflows`) affordance to the user is left to Phase-5 ergonomics.
- **Step-type signal for gating:** does `cast-goal-decomposer` emit machine tags per step, or must
  the skill classify step-type from step text? Today the skill derives a coarse step-type by keyword
  classification (mirroring `cast-explore`'s code-relevant-vs-conceptual branch). Richer tags would
  be a decomposer change — out of scope (FR-006 freezes the decomposer).
- **Observed live concurrency cap reconciliation:** the formula `min(16, cores−2)` matched the 1a
  simulator (8-core → 6); the literal live cap on other machines ("16, fewer on low-CPU") should be
  recorded per-run in `summary.ai.md` and reconciled in Phase 5 if it diverges.

## Not Included

- Editing or migrating `cast-explore` (ships in parallel; user merges later — Phase 5 parity).
- Changing `summary.ai.md` consumed-section format (Out-of-Scope; dropped-cells info is additive).
- A cost ceiling / budget enforcement (cost is surfaced at the gate, not blocked).
- The HTML render of exploration output (Phase 4) and in-viewer commenting (Phase 3b).
- Modifying the `cast-goal-decomposer` to emit richer step-type tags (FR-006 freezes it).
