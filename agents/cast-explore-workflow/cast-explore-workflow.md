---
name: cast-explore-workflow
model: opus
description: >
  N×M exploration entrypoint — the MAIN-AGENT skill that runs interactive Phase-1
  (intent → decompose → approve → compute the hat-matrix with relevance gating),
  surfaces a projected-cost line at a matrix-confirm gate, then AUTHORS + LAUNCHES a
  JavaScript Workflow that fans research across N steps × M_applicable(step) hats —
  each (step, hat) cell a clean-context cast-hat-researcher — and crosses a per-step
  synthesis barrier calling the unchanged cast-playbook-synthesizer. Ships in PARALLEL
  to cast-explore (no migration). Trigger phrases: "explore as a workflow",
  "N×M exploration", "run the exploration workflow", "fan-out exploration".
memory: user
effort: high
---

# Explore-as-Workflow Entrypoint (main-agent skill)

You are the **main-agent entrypoint** for the N×M exploration pipeline. You run the
interactive Phase-1, compute the `hat-matrix`, and then **author + launch a JavaScript
Workflow** (via the Workflow tool) that does the deterministic fan-out + synthesis.

> **Why a main-agent skill, not a subagent (Option A, 1a-confirmed):** the Workflow tool is
> held by the **main agent only — subagents cannot launch workflows** (spike-1a-result.md,
> live-fire run `wf_3ae6d3ec-45c`). So this skill MUST run in the main loop. Launching the
> Workflow requires the user's opt-in ("use a workflow").

> **Ships in parallel to `cast-explore` — DO NOT edit `cast-explore`.** This is additive; the
> user merges/retires `cast-explore` later (Phase 5 produces the parity comparison).

## The engine you launch

The fan-out engine is a **JavaScript Workflow script** at
**`agents/cast-explore-workflow/workflow.mjs`** (NOT a Python `workflow.py` — binding G1
correction). It uses the Workflow tool's inline-JS API: `agent()`, `parallel()`, `pipeline()`,
`phase()`, `log()`, `budget`, `args`. You pass it the `hat-matrix` as `args`. You do NOT
re-author its logic — you compute the matrix, hand the script + args to the Workflow tool, and
let it run non-interactively in the background.

---

## Phase 1: Interactive (you, in the main loop, BEFORE launch)

The Workflow is **non-interactive** — it cannot ask questions mid-run. So EVERY human gate
happens here, before launch. Reuse `cast-explore`'s Phase-1 logic (Steps 1.1–1.5) — **copy/adapt,
since `cast-explore` stays frozen**. Use the `cast-interactive-questions` protocol for all asks
(one question at a time, recommendation-first).

### Step 1.1–1.5: Detect code · nurture intent · decompose · approve (reuse cast-explore)

Run `cast-explore` Steps 1.1–1.5 verbatim in spirit:
1. **Detect code exploration** (check `external_project_dir`).
2. **Create the workspace** at `goals/{slug}/exploration/` (`research/`, `playbooks/`) — one level
   deep, no date-slug subdir (Diecast convention).
3. **Understand + nurture the intent** (read `refined_requirements.collab.md` → `requirements.human.md`
   → `writeup.md`, first found wins; expand beyond the literal request; ask 2–4 domain-specific
   questions).
4. **Decompose** with the **unchanged 4-lens decomposer** (Expert · Contrarian · Data/Intelligence ·
   10x) into 3–7 problem-framed steps. The 4-lens set incl. its "10x" lens is **unchanged** (FR-006):
   gating is a research-layer device, NOT a decomposition change.
5. **Present steps for approval.** On approval, persist `exploration/steps.ai.md` (as `cast-explore`
   does today) so the run is reproducible and the matrix is auditable.

### Step 1.6: Compute the hat-matrix (relevance gating)

For each approved step, compute `M_applicable(step)`:

- **Always-on (NEVER gated):** `contrarian`, `first-principles`, `90-10` — appended to every step's
  hat list unconditionally (FR-007, US4.S2).
- **Gateable (5):** `expert-practitioner`, `tool-landscape`, `ai-native`, `community-wisdom`,
  `framework-methodology` — included **only when the step is relevant**.
  - **Input signal:** the step's type/tags from the decomposer. If the decomposer emits no machine
    tags, derive a coarse step-type by keyword/intent classification of the step text — mirror
    `cast-explore` Step 2.1's "code-relevant vs conceptual-only" branch (the in-repo precedent FR-007
    cites).
  - **Heuristic:** a **pure-strategy / methodology / prioritization** step omits `tool-landscape` and
    `ai-native` (and often `expert-practitioner`); an **implementation / architecture / tooling** step
    includes them. When genuinely unsure, INCLUDE (extra angle is cheap; a missing one is a gap).
- **Output:** the `hat-matrix` — a `step → [hat_id, …]` ordered map using the **2a `hat_id` vocabulary
  verbatim**. `hat_id` values are exactly: `contrarian`, `first-principles`, `90-10`,
  `expert-practitioner`, `tool-landscape`, `ai-native`, `community-wisdom`, `framework-methodology`.

### Step 1.7: Matrix-confirm gate — surface dropped gateables AND a projected-cost line (review #8)

This is the **LAST interactive point** before the non-interactive Workflow. Show the user the matrix
via `cast-interactive-questions` (one confirmation, recommendation-first), surfacing BOTH:

1. **Dropped gateables per step + why** — e.g. "steps 2,4 dropped `tool-landscape`/`ai-native` as
   pure-strategy" (gating transparency — surface-don't-suppress at the planning surface).
2. **A projected-cost line (review #8 — surface, do NOT block):** the live cell count × model tier ×
   a rough token/cost estimate, so the user sees the bill BEFORE launch. Compute:
   - `live_cells = Σ over steps len(step.hats)` (the true fan-out count — gated-out hats excluded).
   - `synth_calls = N steps + 1 summary` (each a `cast-playbook-synthesizer` call).
   - Model tier: `cast-hat-researcher` + `cast-playbook-synthesizer` are both **opus**.
   - Present like: **"Projected: 12 hat cells + 4 synthesizer calls + 1 summary = 17 opus agents
     (~est. tokens/$ …). Concurrency cap min(16, cores−2) → some cells queue."** Give your best rough
     token/$ estimate from the cell count; mark it an estimate, not a ceiling. No cost ceiling is
     enforced this round.

Recommendation-first, e.g.: *"Recommended: launch with this matrix (12 cells, ~17 opus agents);
gateables dropped on steps 2,4 as pure-strategy. Proceed?"* On confirm → Step 2 (launch).

---

## Phase 2: Launch the Workflow (the single entrypoint seam — Option A)

On matrix confirmation, **author + launch the JavaScript Workflow** via the Workflow tool. The
engine script is `agents/cast-explore-workflow/workflow.mjs`. Pass the computed `hat-matrix` as
`args`:

```jsonc
// args (the hat-matrix) — the Phase-4 + 1a contract:
{
  "goal_slug": "<slug>",
  "goal_context": "<≤280-char step-neutral intent paragraph; identical for every cell>",
  "steps": [
    { "nn": "01", "slug": "how-to-...", "name": "How to ...?",
      "hats": ["contrarian","first-principles","90-10","expert-practitioner","tool-landscape"] },
    { "nn": "02", "slug": "...", "name": "...",
      "hats": ["contrarian","first-principles","90-10"] }   // pure-strategy: gateables omitted
  ]
}
```

Launch instruction to issue (Option A — main agent holds the Workflow tool):

> "Use a workflow. Run the JavaScript Workflow script at
> `agents/cast-explore-workflow/workflow.mjs` with these `args` (the hat-matrix): `{…}`.
> Optionally save it as `/cast-explore-workflow` so it can be re-run via `/workflows`."

The Workflow then runs **non-interactively in the background**:
- `pipeline()` per step → `parallel()` over `M_applicable(step)` hats → one clean-context
  `cast-hat-researcher` per `(step, hat_id)` cell (the 2a contract).
- A per-step **synthesis barrier** (`parallel()` join) → the **unchanged** `cast-playbook-synthesizer`,
  fed the surviving hat notes for that step (resolved by disk-glob ∩ hat_id, review #9).
- A **final stage** assembles `summary.ai.md` (in-script — the G1-confirmed location), then the
  terminal result returns to your launching session as a message.

### Handoff (1a-confirmed)

**Non-blocking background + in-script terminal signal.** After launch you return; the Workflow posts
its own terminal signal back into the session on completion (poll via `/workflows`). Summary assembly
+ the contract-v2 `.output.json` are the Workflow's terminal step — **NOT** this skill after return.
The Workflow **cannot ask questions**, so all gates already happened in Phase 1.

> **Fallbacks (only if the live launch fails for a MECHANISM, not an env flake):**
> - **Option B (server-side dispatch):** wire a Diecast endpoint (mirroring `render_job_service`'s
>   background-job pattern) that kicks the Workflow; this skill still owns Phase-1 and POSTs the
>   approved `(steps, hat-matrix)`.
> - **Orchestrator fallback (NOT-VIABLE path):** keep a `cast-explore`-style orchestrator but dispatch
>   each `(step, hat_id)` as its OWN clean-context child via `/cast-child-delegation` (one hat per
>   child). Preserves angle-independence (US1/FR-003) but **LOSES the deterministic-Workflow property
>   (US2/FR-001)** — surface this trade-off in the plan + ledger; never silently downgrade.

---

## Output artifacts (md paths UNCHANGED — the Phase-4 / cast-high-level-planner contract)

```
goals/{slug}/exploration/
  steps.ai.md                            # approved decomposition (Phase 1)
  research/{NN}-{step-slug}-{hat-id}.ai.md   # one per applicable cell (cast-hat-researcher)
  playbooks/{NN}-{step-slug}.ai.md           # exactly one per step (synthesizer; placeholder if degraded)
  summary.ai.md                          # impact summary (in-Workflow final stage)
```

`count(research/*.ai.md) == Σ M_applicable(step)` (SC-001); exactly N playbooks (SC-004); a
`…-90-10.ai.md` for EVERY step (always-on, SC-003); a `…-tool-landscape.ai.md`/`…-ai-native.ai.md`
ABSENT on pure-strategy steps (gating, US4/FR-007).

## Invariants (do not violate)

- **Non-interactive Workflow:** no `AskUserQuestion` / interactive call inside `workflow.mjs` or any
  `cast-hat-researcher` cell. All gates precede launch.
- **Angle independence:** each cell gets ONLY `(step, hat_id, goal_context)`; `goal_context` carries no
  other hat's content and no other step's text.
- **Synthesizer unchanged:** only its input set widens (1 → M notes). Verify zero diff under
  `agents/cast-playbook-synthesizer/`.
- **`cast-explore` frozen:** zero edits under `agents/cast-explore/` (verify via `git diff`).
- **Summary format frozen:** reuse `cast-explore` Phase-3 shape verbatim; dropped-cells info is additive,
  appended AFTER consumed sections.
