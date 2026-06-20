# Exploration Pipeline (N×M Workflow + 90/10 + HTML): Sub-phase 3a — N×M Workflow Engine + Relevance Gating + Entrypoint

## Overview

This sub-phase builds the **Track A core**: the starter exploration run as a deterministic Claude
**Workflow**. Interactive Phase-1 (intent → decompose → approve → compute the hat-matrix) stays with
the main agent; on approval it launches a non-interactive Workflow that fans research across
`N steps × M_applicable(step)` hats — each `(step, hat)` cell a **separate clean-context agent**
(`cast-hat-researcher`, the 2a contract) — then crosses a **per-step synthesis barrier** that calls the
existing `cast-playbook-synthesizer` **unchanged** (one synthesizer per step → one playbook). All
existing markdown artifacts land at their current paths, so `cast-high-level-planner` is unaffected.

The key insight inherited from the spec: this is **angle-independence made real** — today's pipeline
researches all hats in one per-step context (priming/pollution); the Workflow gives every hat its own
fresh context. The engine ships **in parallel** to `cast-explore` — no migration, no edits to
`cast-explore` (the user merges later).

Two structural seams from prior rounds are load-bearing here and are NOT re-litigated: the
`cast-hat-researcher` I/O contract (2a) is exactly what `parallel()` over hats calls; and the
entrypoint-mechanism choice (1a Option A preferred) is consumed, not re-decided. Where 1a's spike
verdict is not yet recorded, the dependent activities are marked `[PENDING 1a outcome]`.

## Operating Mode

**HOLD SCOPE** — parent goal front-matter is `scope_mode: hold`, and this sub-phase is core
implementation (not a spike like 1a). Rigor over both ambition and minimalism: every FR in scope
(FR-001/002/003/007/008/014/015/016 plus US6/US9-substrate) must be satisfied, edge cases mapped
(failure isolation, cap saturation, empty-matrix cells, synthesizer-with-one-surviving-hat), and the
md-artifact compatibility contract treated as inviolable. No stretch goals (HTML render is Phase 4;
commenting is 3b); no cuts (failure isolation and the cap are not "nice-to-have" — they're FR-015/016).

## Position in Overall Plan

```
        ┌─ Sub-phase 1a (spike: Workflow engine) ───────────┐  verdict + mechanism
        │                                                   ▼
Phase 1 ┤                              Sub-phase 2a ─► ►► Sub-phase 3a (THIS) ─┐
(spikes)│                            (cast-hat-researcher)  (Workflow core)    │
        │                                                                      ▼
        └─ Sub-phase 1b ─► 2b ─► 3b ──────────────────────────────► Phase 4 (exploration render) ─► Phase 5
```

- **Dependencies:** **Sub-phase 1a** (entrypoint-mechanism verdict + the `(steps, hat-matrix)` arg
  shape) and **Sub-phase 2a** (the `cast-hat-researcher` agent + its `hat_id` vocabulary + note paths).
- **Blocks:** **Phase 4** consumes 3a's markdown output (`research/`, `playbooks/`, `summary.ai.md`) as
  the substrate the WHAT/HOW HTML render reads. The md artifact output shape **is** the Phase-4
  interface — getting the paths/shape right here is a contract, not a detail.
- **Critical path:** 1a → 2a → **3a** → 4 → 5. This is the third node on the critical path.

## Depends On (from prior plans)

| From | Interface this sub-phase consumes |
|------|-----------------------------------|
| **1a** | Entrypoint = main-agent SKILL/COMMAND launches the Workflow tool (Option A preferred, Option B = server-side dispatch fallback; orchestrator-agent + enforced per-hat child isolation = NOT-VIABLE fallback). Workflow receives `(approved_steps, hat-matrix)` as **args**. Non-interactive/background handoff semantics observed at spike E2/A5. Concurrency cap `min(16, cores−2)` confirmed. |
| **2a** | Agent **`cast-hat-researcher`**, pure function `(step, hat_id, goal_context) → one note` at `goals/{slug}/exploration/research/{NN}-{step-slug}-{hat-id}.ai.md` + contract-v2 `.output.json` terminal signal. `hat_id` vocabulary: always-on `contrarian`/`first-principles`/`90-10`; gateable `expert-practitioner`/`tool-landscape`/`ai-native`/`community-wisdom`/`framework-methodology`. Each cell = fresh clean context (no cross-hat priming). `parallel()` over hats calls EXACTLY this contract — one child per `(step, hat_id)`. |
| **existing (unchanged)** | `cast-playbook-synthesizer` — input = raw research notes for a step + goal context + step name → ONE playbook. The synthesis barrier hands it the `M_applicable(step)` surviving hat notes for that step. **Not modified.** |
| **existing (unchanged)** | `cast-explore` — left fully intact, no migration. 3a ships alongside it. |

## Sub-phase 3a: N×M Workflow Engine + Relevance Gating + Entrypoint

**Outcome:** The starter exploration runs as a Workflow. Interactive Phase-1 (intent + decompose +
approval + hat-matrix computation) hands off to a deterministic N×M fan-out + per-step synthesis
barrier, producing all existing markdown artifacts (`research/{NN}-{step}-{hat}.ai.md`, one
`playbooks/{NN}-{step}.ai.md` per step, `summary.ai.md`). A forced hat-agent failure drops one cell to
`null` (logged, surfaced) without sinking the step or the run. Ships in parallel to `cast-explore`,
which is untouched.

**Dependencies:** Sub-phase 1a (spike verdict), Sub-phase 2a (`cast-hat-researcher`).

**Estimated effort:** 3–4 sessions.

**Verification:**
1. **Full run on a real goal** (use this goal, or a small throwaway 3-step goal) produces:
   - `exploration/research/{NN}-{step-slug}-{hat-id}.ai.md` for **every applicable cell** —
     `count(research/*.ai.md) == Σ M_applicable(step)` (SC-001).
   - **exactly one** `exploration/playbooks/{NN}-{step-slug}.ai.md` **per step** (`== N`) (SC-004).
   - `exploration/summary.ai.md` (US6/SC-009).
2. **Angle independence:** inspect two hat prompts for the same step — they share no hat-specific
   framing; no agent's note references another hat's content (SC-002, FR-003). (Inherited from 2a's
   per-hat clean context; 3a must not re-introduce shared context when assembling the matrix.)
3. **Relevance gating:** for a pure-strategy step, gateable hats (Tool Landscape, AI-Native) are
   **absent** from `research/` while always-on (`contrarian`, `first-principles`, `90-10`) are
   **present** (US4, FR-007).
4. **90/10 present everywhere:** a `…-90-10.ai.md` note exists for **every** step (always-on) (SC-003).
5. **Failure isolation:** force one `cast-hat-researcher` cell to fail → run completes, that cell is
   `null` in the run log AND surfaced (not silently dropped), and the step's playbook is still produced
   from surviving hats (FR-016, US12, SC-009).
6. **Cap respected:** on a goal whose live cell count exceeds `min(16, cores−2)`, excess cells queue
   (no over-subscription, no error) (FR-015).
7. **No-intervention:** after step approval, the run completes with zero further prompts (FR-014,
   US11, SC-009) — proves the non-interactive Workflow boundary.
8. **`cast-explore` untouched:** `git diff` shows no changes under `agents/cast-explore/`.

### Key activities

Grouped into three work areas. **3a-i** (interactive Phase-1 + gating) and **3a-ii** (the Workflow
script + barrier) have a hard dependency: the script consumes the `hat-matrix` that gating produces.
**3a-iii** (entrypoint wiring) is `[PENDING 1a outcome]`.

#### 3a-i — Interactive Phase-1 extension: hat-matrix computation (relevance gating)

- **Locate the Phase-1 host.** Per 1a Option A, the interactive Phase-1 (intent → decompose → step
  approval) runs in a **main-agent skill/command** — a **new** `cast-explore-workflow` skill that lives
  alongside intact `cast-explore` (do NOT edit `cast-explore`; name confirmed below). It reuses the
  Phase-1 logic from `cast-explore` (Steps 1.1–1.5: code-exploration detection, intent nurturing,
  4-lens decompose, step approval) — copy/adapt, since `cast-explore` stays frozen. The decomposer's
  4-lens set (incl. its "10x" lens) is **unchanged** (FR-006) — gating is a research-layer device, not
  a decomposition change.
- **Implement relevance gating → emit `hat-matrix`.** After step approval, compute `M_applicable(step)`
  for each approved step:
  - **Input:** each step's type/tags (problem-framed step name + any tags the decomposer attaches;
    if the decomposer emits no machine tags, derive a coarse step-type by keyword/intent classification
    of the step text — mirror today's code-exploration relevance call in `cast-explore` Step 2.1's
    "code-relevant vs conceptual-only" branch, which is the in-repo precedent FR-007 cites).
  - **Always-on (never gated):** `contrarian`, `first-principles`, `90-10` (FR-007, US4.S2) — these are
    appended to every step's hat list unconditionally.
  - **Gateable (5):** `expert-practitioner`, `tool-landscape`, `ai-native`, `community-wisdom`,
    `framework-methodology` — included only when the step is relevant (e.g. a pure-strategy step omits
    `tool-landscape`/`ai-native`; an implementation step includes them).
  - **Output:** the `hat-matrix` — a `step → [hat_id, …]` map (ordered list of `hat_id`s using the 2a
    vocabulary verbatim). This is the **Workflow arg** (FR-007, FR-014, US11.S1).
- **Hat-matrix arg shape (pin this — Phase-4 + 1a both reference it):**
  ```jsonc
  {
    "goal_slug": "exploration-pipeline-nxm-claude-workflow-9010-angle",
    "goal_context": "<short intent paragraph passed to every hat-researcher>",
    "steps": [
      { "nn": "01", "slug": "how-to-...", "name": "How to ...?",
        "hats": ["contrarian","first-principles","90-10","expert-practitioner","tool-landscape"] },
      { "nn": "02", "slug": "...", "name": "...",
        "hats": ["contrarian","first-principles","90-10"] }   // pure-strategy step: gateables omitted
    ]
  }
  ```
  `nn` is the zero-padded step index already used in the artifact path convention; `slug` is the
  kebab step slug. Each `(nn, slug, hat_id)` triple is exactly one fan-out cell.
- **Persist the approved decomposition** as `exploration/steps.ai.md` (as `cast-explore` does today) so
  the run is reproducible and the matrix is auditable.
- **Show the matrix to the user before launch** (cheap human gate, within still-interactive Phase-1):
  surface which gateable hats were dropped per step and why, so gating is transparent
  (surface-don't-suppress applied at the planning surface too). Use the `cast-interactive-questions`
  protocol — one confirmation, recommendation-first ("Recommended: launch with this matrix; gateables
  dropped on steps 2,4 as pure-strategy"). This is the **last** interactive point before the
  non-interactive Workflow.

#### 3a-ii — The Workflow script: fan-out + synthesis barrier

- **Write the Workflow script** (location: `agents/cast-explore-workflow/workflow.py` — see Naming
  below; the seed shape comes from 1a's E1 toy, promoted to real). Structure:
  ```
  workflow(args = {goal_slug, goal_context, steps[]}):
    for each step in args.steps:                          # pipeline() — per step
      pipeline(step):
        notes = parallel(                                 # parallel() over M_applicable(step) hats
          cast_hat_researcher(step, hat_id, goal_context) # EXACTLY the 2a contract — one child / cell
          for hat_id in step.hats
        )                                                 # <-- this parallel() is the synthesis barrier
        surviving = [n for n in notes if n is not null]   # failure isolation (FR-016): drop null cells
        cast_playbook_synthesizer(                        # existing synthesizer, UNCHANGED
          step_name = step.name,
          goal_context = goal_context,
          research_notes = surviving                      # the M_applicable hat notes for THIS step
        )                                                 # -> playbooks/{NN}-{step-slug}.ai.md
    # after all steps: assemble summary.ai.md (see below)
  ```
  - **`pipeline()` per step / `parallel()` over hats** matches the Workflow tool's pipeline/parallel
    composition (from the 1a A0 tool-docs note). The `parallel()` join **is** the per-step synthesis
    barrier — synthesis for a step starts only when all that step's hat cells have terminated
    (succeeded → note; failed → null). Steps themselves run concurrently subject to the global cap, so
    a fast step's synthesis need not wait on a slow step's hats.
  - **Each cell calls `cast-hat-researcher` with `(step, hat_id, goal_context)`** — the 2a pure-function
    contract, one child per cell, fresh clean context. The script reads the `hats` list from the matrix
    arg to decide which cells to spawn (it never spawns a gated-out hat). **Do NOT** pass any other
    hat's framing or output into a cell — angle independence (FR-003) is preserved by construction.
- **Synthesis barrier — feed surviving hat notes (the one real change to the synthesizer's _inputs_,
  not the synthesizer).** Today `cast-explore` hands the synthesizer **one** research file per step;
  here it gets the **`M_applicable(step)` hat notes** for that step (the surviving, non-null cells).
  The synthesizer's I/O contract (raw research notes + goal context + step name → one playbook) is
  satisfied unchanged — it already "reads all the research" and produces one opinionated playbook
  (`cast-playbook-synthesizer` Step 1: "Read all the research notes"). Resolve the note set by globbing
  `research/{NN}-{step-slug}-*.ai.md` for that step at barrier time (the authoritative on-disk set),
  rather than trusting the in-memory `parallel()` return — this makes the barrier robust to a child
  that wrote its file then reported a soft error.
- **Failure isolation (FR-016, US12).** A `cast-hat-researcher` cell that fails (non-zero terminal,
  timeout, or missing/empty `.output.json`) → its cell resolves to `null`, is **logged** with the
  `(step, hat_id)` and reason, and is **surfaced** in the run log + final summary's "dropped cells"
  section (surface-don't-suppress — never a silent gap). The step's synthesis proceeds from the
  surviving hat notes. **Edge case:** if **all** of a step's hats fail (zero surviving notes), do NOT
  invoke the synthesizer with empty input — write a placeholder `playbooks/{NN}-{step-slug}.ai.md`
  stating "no surviving research for this step; cells dropped: […]" and flag the whole step as degraded
  in the summary. (A run with all-dropped cells is a loud failure, not a silent empty playbook.)
- **Concurrency cap (FR-015).** The Workflow tool enforces `min(16, cores−2)` natively (confirmed at
  1a E4). The script does **not** hand-roll a queue — it lets the tool queue excess cells. The worst
  case is `N × M_total` (e.g. 5×8 = 40) when gating drops nothing; gating + the native cap keep the
  live set bounded. **Surface** queued/over-cap state in the run log so a large goal's queueing is
  visible (don't suppress). Record the observed cap on the run machine in the summary.
- **Assemble `summary.ai.md`.** Reuse `cast-explore`'s Phase-3 summary shape **verbatim**
  (`cast-explore` Steps 3.1–3.3: verify files, read all playbooks, write impact ratings + top
  recommendations + stack + build order + risks). **Out of Scope** forbids changing `summary.ai.md`
  format — match it byte-for-byte-shaped so `cast-high-level-planner` consumes it unchanged. Append a
  **"Dropped cells / degraded steps"** section listing any null cells (this is additive run-metadata,
  not a format change to the consumed sections — keep it after the existing sections). The summary
  assembly can run inside the Workflow's terminal step or be handed back to the main agent post-Workflow
  `[decide at 3a-iii per 1a handoff semantics]`.

#### 3a-iii — Entrypoint wiring `[PENDING 1a outcome]`

- **[PENDING 1a outcome] Build the entrypoint per the 1a verdict.**
  - **If 1a VIABLE (Option A, expected):** the `cast-explore-workflow` skill/command hosts the
    interactive Phase-1 (3a-i), and on approval issues the **Workflow tool call** with the
    `(steps, hat-matrix)` args (3a-ii). The skill is the non-subagent surface that launches the tool;
    the Workflow then runs non-interactively in the background. Wire the main-agent → Workflow handoff
    exactly as the spike demonstrated (the spike's recorded launch invocation is the template).
    *Unknown until 1a recorded:* whether the main agent **blocks** until the Workflow completes or
    **returns** and the Workflow posts its own terminal signal — the spike observes this at E2/A5; 3a
    designs the handoff to match. Default assumption for planning: non-blocking background + the
    Workflow's terminal step writes `summary.ai.md` and a contract-v2 `.output.json`.
  - **If 1a VIABLE via Option B (server-side dispatch):** wire a Diecast server endpoint (mirroring the
    `render_job_service` / child-dispatch background-job pattern) that kicks the Workflow; the
    `cast-explore-workflow` skill still owns interactive Phase-1 and POSTs the approved
    `(steps, hat-matrix)` to that endpoint.
  - **If 1a NOT-VIABLE (orchestrator fallback):** re-scope 3a-ii — instead of the Workflow tool, keep a
    `cast-explore`-style orchestrator agent BUT dispatch each `(step, hat_id)` as its **own
    clean-context child** via `/cast-child-delegation` (one hat per child — NOT today's
    7-hats-in-one-context). The per-step synthesis barrier becomes a `/cast-child-delegation` poll-all
    barrier. This preserves angle-independence (US1/FR-003) but **loses the deterministic-Workflow
    property (US2/FR-001)** — surface this trade-off explicitly in the plan and the goal's decisions
    ledger; do not silently downgrade. Failure isolation, gating, summary, and md-artifact paths are
    all unchanged from the Workflow path.
- **Keep `cast-explore` intact.** No edits under `agents/cast-explore/`. The new
  `cast-explore-workflow` is additive; the user merges/retires `cast-explore` later (Phase 5 produces
  the parity comparison for that decision). Add `cast-explore-workflow` to the agent registry; its
  `config.yaml` `allowed_delegations` must list **`cast-hat-researcher`** and
  **`cast-playbook-synthesizer`** (and `cast-goal-decomposer`/`cast-code-explorer` if Phase-1 reuses
  them) — mirror `cast-explore/config.yaml`.

### Naming (pinned for the ledger)

| Thing | Name / location | Rationale |
|-------|-----------------|-----------|
| Entrypoint skill/command | **`cast-explore-workflow`** | `cast-{verb}-{noun}`; parallels intact `cast-explore`; the name 1a's plan already forward-referenced. |
| Workflow script | **`agents/cast-explore-workflow/workflow.py`** | Co-located with the skill that launches it; mirrors agent dir layout (`config.yaml`, `*.md`, script). |
| Hat-matrix arg | **`hat-matrix`** = `{goal_slug, goal_context, steps:[{nn,slug,name,hats:[hat_id…]}]}` | Shape pinned above; `hat_id` values are 2a's vocabulary verbatim. |
| Synthesis barrier | per-step `parallel()` join → `cast-playbook-synthesizer` (unchanged), fed the surviving `research/{NN}-{slug}-*.ai.md` glob | Synthesizer I/O contract untouched; only its _input set_ widens from 1 file to M. |
| Research note paths | `goals/{slug}/exploration/research/{NN}-{step-slug}-{hat-id}.ai.md` (2a) | Consumed by Phase 4; matches SC-001/SC-003 expectations. |
| Playbook paths | `goals/{slug}/exploration/playbooks/{NN}-{step-slug}.ai.md` (one per step) | Unchanged from `cast-explore`; FR-008/SC-004. |
| Summary path | `goals/{slug}/exploration/summary.ai.md` | Unchanged format (Out-of-Scope guard); FR-009/US6. |

### Design review

- **Spec consistency:** No *existing* spec governs the exploration Workflow engine (greenfield, flagged
  in 1a). The markdown artifact layout is a **hard compatibility contract** with `cast-high-level-planner`
  (Constraints) — treated as inviolable above (paths/shape unchanged; summary format frozen). **Action:**
  create a new **`cast-explore-workflow.collab.md`** spec via `/cast-update-spec` (create mode) as a 3a
  activity, documenting the N×M engine behavior contract (matrix arg shape, fan-out, barrier, failure
  isolation, cap, md-artifact paths) — this is the spec 1a deferred to 3a. Register it in
  `docs/specs/_registry.md`. ⚠️ Flag.
- **Angle-independence preservation:** the gain of 2a's per-hat clean context is easy to silently lose
  at the assembly layer — e.g. if the script built one shared prompt and templated hats into it, or if
  goal_context leaked another hat's output. **Guard:** each cell receives ONLY `(step, hat_id,
  goal_context)`; `goal_context` is the step-neutral intent paragraph, never another hat's note. State
  this as an invariant the script enforces and a verification step (V2) checks. ✓ guarded.
- **Synthesizer-unchanged invariant:** the only change is the synthesizer's _input set_ (1 file → M hat
  notes); its prompt/contract/output path are untouched (US5/FR-008). Verify by `git diff` on
  `cast-playbook-synthesizer` showing zero changes. ✓
- **Error & rescue (data-mutation / external calls):** fan-out spawns many children → partial failure is
  the *expected* path, not the exception. Covered: null-cell isolation (FR-016), all-cells-failed
  placeholder, surfaced dropped-cells log. **Additional:** a child that writes a corrupt/empty note must
  be treated as null (validate the note is non-empty + has the expected hat heading before counting it
  surviving) — else the synthesizer ingests garbage. Add note-validation at the barrier. ⚠️ → added to
  3a-ii barrier activity.
- **Cap / resource:** worst-case 40 cells; rely on the tool's native cap (no hand-rolled queue), surface
  queueing. No unbounded spawn. ✓
- **Non-interactive boundary:** the Workflow cannot ask questions (Constraints) — all human gates
  (intent, decompose, approve, matrix-confirm) precede launch in 3a-i. **Guard:** no `AskUserQuestion`
  or any interactive call inside `workflow.py` or `cast-hat-researcher` cells. State as an invariant. ✓
- **Security:** artifact writes are confined to `goals/{slug}/exploration/**`; `{slug}` comes from the
  goal (not user free-text at run time) and `{step-slug}`/`{hat-id}` are derived from approved
  decomposition + the fixed 2a vocabulary — low path-traversal surface. **Guard:** sanitize `step-slug`
  to `[a-z0-9-]` when forming paths (defense-in-depth, since slugs derive from step names). ✓
- **Naming conventions:** `cast-explore-workflow` follows `cast-{verb}-{noun}`; `hat_id` values reuse
  2a's literal vocabulary (incl. `90-10` matching `…-90-10.ai.md`). ✓

## Build Order

```
3a-i (Phase-1 skill + gating → hat-matrix) ─┐
                                            ├─► 3a-ii (workflow.py: fan-out + barrier + isolation + summary)
2a artifact (cast-hat-researcher) ──────────┘            │
1a verdict (mechanism) ─────────────────────────────────┴─► 3a-iii (entrypoint wiring) [PENDING 1a]
                                                                      │
                                                                      ▼
                                                            create cast-explore-workflow.collab.md spec
                                                                      │
                                                                      ▼
                                                            full-run verification (V1–V8)
```

**Critical path within 3a:** 3a-i → 3a-ii → 3a-iii → verification. 3a-i (gating) and the 3a-ii script
skeleton can be drafted in parallel once 2a's contract is fixed, but the script's barrier can't be
exercised end-to-end until gating emits a real matrix. 3a-iii is gated on the 1a verdict — if 1a is not
yet recorded, build 3a-i/3a-ii against the Option-A assumption and leave the launch call as the single
`[PENDING 1a]` seam.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 3a | Greenfield engine has no spec; md layout is a hard `cast-high-level-planner` contract | Create `cast-explore-workflow.collab.md` via `/cast-update-spec` (create mode) + register in `_registry.md`; document matrix-arg/fan-out/barrier/isolation/cap/md-paths. |
| 3a | Angle-independence can be silently lost at the assembly layer | Each cell gets ONLY `(step, hat_id, goal_context)`; `goal_context` carries no other hat's content. Verify (V2). |
| 3a | A child writing a corrupt/empty note could feed the synthesizer garbage | Validate note non-empty + has expected hat heading at the barrier; else treat as null cell. |
| 3a | All-cells-failed step would call synthesizer with empty input | Write a placeholder degraded playbook + flag the step in summary; never an empty/silent playbook. |
| 3a | Workflow is non-interactive but Phase-1 needs human gates | All gates precede launch in 3a-i; no interactive call inside `workflow.py` or hat cells (invariant). |
| 3a | `summary.ai.md` format is Out-of-Scope to change | Reuse `cast-explore` Phase-3 summary shape verbatim; dropped-cells info is additive, appended after consumed sections. |
| 3a | 1a NOT-VIABLE fallback silently loses determinism | If orchestrator fallback, record that US2/FR-001 (deterministic Workflow) is dropped while angle-independence is kept — surface in plan + ledger. |
| 3a | `cast-explore` must stay frozen (parallel ship, FR Out-of-Scope) | No edits under `agents/cast-explore/`; verify via `git diff` (V8). |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 1a verdict not yet recorded when 3a starts → entrypoint design uncertain | High | Build 3a-i/3a-ii against the Option-A assumption (the spike's recommended path); isolate the launch call as the single `[PENDING 1a]` seam so a Option-B/orchestrator verdict reshapes only 3a-iii, not the engine. |
| Token/cost balloon on a large goal (up to N×M_total = 40 cells) | Med | Relevance gating (always-on = 3) + native cap; surface queued/dropped cells; the matrix-confirm gate (3a-i) lets the user see cell count before launch. |
| Synthesizer ingests a corrupt/empty hat note as if valid | Med | Barrier validates each note (non-empty + expected hat heading) before counting it surviving; invalid → null cell, logged. |
| md-artifact drift breaks `cast-high-level-planner` (hard contract) | High | Paths/shape pinned to 2a + `cast-explore`; `summary.ai.md` format frozen; Phase-5 parity run is the final check, but 3a verifies path/count (V1) directly. |
| Fan-out partial failure masked (a dropped cell looks like a gated-out cell) | Med | Distinguish *gated* (never in the matrix) from *dropped* (in matrix, failed) in the log; the summary's dropped-cells section lists only true failures, with reasons (surface-don't-suppress). |
| Steps-concurrent execution lets a slow step's hats starve the cap | Low | Accept native tool scheduling (no hand-rolled queue); observe + record cap behavior; if starvation observed, note for Phase-5 tuning (not a 3a blocker). |

## Open Questions

- **[Resolved by 1a, consumed here]** Entrypoint mechanism: Option A (main-agent skill launches the
  Workflow tool — expected) vs Option B (server-side dispatch) vs NOT-VIABLE (orchestrator + per-hat
  child isolation). 3a-iii is `[PENDING 1a outcome]`; the engine (3a-i/3a-ii) is mechanism-agnostic.
- **[PENDING 1a]** Main-agent ↔ Workflow handoff: does the launching skill **block** until the Workflow
  completes, or **return** while the Workflow runs in the background and posts its own terminal signal?
  The spike observes this at E2/A5. Planning default: non-blocking background; the Workflow's terminal
  step writes `summary.ai.md` + a contract-v2 `.output.json`. Affects where summary assembly lives
  (in-Workflow vs handed back to the main agent).
- **Step-type signal for gating:** does the `cast-goal-decomposer` (via the Phase-1 reuse) emit machine
  tags per step, or must 3a-i classify step-type from the step text? If the decomposer emits no tags,
  3a-i derives a coarse step-type by keyword/intent classification (mirroring `cast-explore`'s
  code-relevant-vs-conceptual branch). Confirm during 3a-i implementation; if richer tags are wanted,
  that's a `cast-goal-decomposer` change — **out of scope here** (FR-006 freezes the decomposer), so
  3a-i must work with whatever the decomposer emits today.
- **Summary assembly location:** in the Workflow's terminal step vs handed back to the main agent
  post-run — decided at 3a-iii per the 1a handoff semantics above.

## Suggested Revisions to Prior Sub-Phases

None required — 2a's `cast-hat-researcher` contract and 1a's `(steps, hat-matrix)` arg shape both slot
in cleanly. One **clarification to carry forward to the ledger** (not a deviation): the synthesis
barrier resolves each step's hat notes by **globbing `research/{NN}-{slug}-*.ai.md` on disk** (the
authoritative set), rather than trusting the `parallel()` in-memory return — this hardens the barrier
against a child that writes its note then soft-fails. This assumes 2a's note write is atomic (the
agent writes the full note then the `.output.json` terminal signal); if 2a's write is non-atomic,
flag it for a small 2a hardening (atomic write / temp-then-rename). Worth confirming 2a's write is
atomic; if not, that's the one prior-sub-phase nudge.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| *(new) `cast-explore-workflow.collab.md`* | To be **created** in 3a (engine behavior contract: matrix arg, fan-out, barrier, isolation, cap, md paths) | N/A — greenfield; `/cast-update-spec` create mode + register in `_registry.md`. |
| `cast-requirements-render.collab.md` | N/A for 3a — governs the HTML/render track (2b/3b/4), not the Workflow engine | None (out of scope for this sub-phase). |
| `cast-workflow-routing.collab.md` | Goal already routed `new_initiative`; no routing change | None. |
| *(contract, not a spec file)* `cast-high-level-planner` md-artifact consumption | `research/*.ai.md`, `playbooks/*.ai.md`, `summary.ai.md` paths + `summary.ai.md` format | None — 3a preserves all paths/shape (hard constraint); the dropped-cells section is additive. |

## Plan Review Decisions (2026-06-20)

- **Issue #1 (Architecture) — Decision: 1A (accepted).** Add a **hard pre-3a gate**: `3a-iii` (entrypoint wiring) may not start until 1a records VIABLE + the proven handoff/terminal-signal mechanism (see 1a's updated E2). 3a builds 3a-i/3a-ii against the Option-A assumption; the launch call stays the single `[PENDING 1a]` seam.
- **Issue #7 (Tests) — Decision: T3 A (accepted).** Add a 3a unit test for the **all-hats-fail placeholder playbook**; pair it with Phase 4's cross-phase degraded-step render test.
- **Issue #8 (Performance) — Decision: P1 A (accepted).** At the **3a-i matrix-confirm gate, surface a projected-cost line** (live cell count × model tier × rough token/cost estimate) alongside the dropped-gateables, so the user sees the bill before launch. Surface, do not block (cost ceiling not added this round).
- **Issue #9 (Performance/Correctness) — Decision: P2 A (accepted).** Pin the **synthesis-barrier glob** to the exact `{NN}-{slug}-{hat_id}.ai.md` set by **intersecting glob results with the known hat_id vocabulary** — eliminates `-code.ai.md` contamination AND slug-prefix collisions (the same exposure Phase 5 documents for SC-001). Keep the disk-glob for robustness.
