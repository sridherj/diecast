# cast-explore-workflow

The **N×M exploration entrypoint** — a **main-agent skill** that runs interactive Phase-1,
computes the `hat-matrix` (relevance gating), surfaces a projected-cost line at a
matrix-confirm gate, then **authors + launches a JavaScript Workflow** that fans research
across `N steps × M_applicable(step)` hats and crosses a per-step synthesis barrier.

Ships **in parallel** to `cast-explore` (no migration; `cast-explore` untouched). The user
merges/retires `cast-explore` later (Phase 5 produces the parity comparison).

## Type

Claude Code Skill — **main-agent** entrypoint (NOT a subagent). The Workflow tool is held by
the main agent only; subagents cannot launch workflows (1a Option A, live-confirmed in
`spike-1a-result.md`, run `wf_3ae6d3ec-45c`).

## The engine (binding G1 correction)

The fan-out engine is a **JavaScript Workflow script** at **`workflow.mjs`** — NOT a Python
`workflow.py`. It uses the Workflow tool's inline-JS API: `agent()`, `parallel()`, `pipeline()`,
`phase()`, `log()`, `budget`, `args`. The G1 live-fire proved this exact model (2×2 isolated
cells + synthesis + terminal signal).

```
pipeline() per step
  → parallel() over M_applicable(step) hats        # one clean-context cast-hat-researcher / cell
  → synthesis barrier (parallel() join)            # the UNCHANGED cast-playbook-synthesizer
final phase("summary")                              # in-script summary.ai.md + terminal signal
```

## hat-matrix arg shape (the interface Phase 4 + 1a consume)

```jsonc
{
  "goal_slug": "<slug>",
  "goal_context": "<≤280-char step-neutral intent; identical for every cell>",
  "steps": [
    { "nn": "01", "slug": "how-to-...", "name": "How to ...?",
      "hats": ["contrarian","first-principles","90-10","expert-practitioner","tool-landscape"] },
    { "nn": "02", "slug": "...", "name": "...",
      "hats": ["contrarian","first-principles","90-10"] }
  ]
}
```

`hat_id` values = the 2a vocabulary verbatim. Always-on (never gated): `contrarian`,
`first-principles`, `90-10`. Gateable (5): `expert-practitioner`, `tool-landscape`, `ai-native`,
`community-wisdom`, `framework-methodology`. Each `(nn, slug, hat_id)` triple = one fan-out cell.

## Output artifacts (md paths UNCHANGED — cast-high-level-planner contract)

- `exploration/research/{NN}-{slug}-{hat-id}.ai.md` — one per applicable cell (SC-001).
- `exploration/playbooks/{NN}-{slug}.ai.md` — exactly one per step (SC-004); placeholder if degraded.
- `exploration/summary.ai.md` — impact summary; in-Workflow final stage (Out-of-Scope to change format).

## Load-bearing review decisions baked in

- **Review #7 — all-hats-fail placeholder:** if every hat of a step is dropped, the script writes a
  DEGRADED placeholder playbook + flags the step in summary; the synthesizer is NEVER called with empty
  input. Tested in `tests/test_all_hats_fail_placeholder.py`.
- **Review #8 — projected-cost line:** the matrix-confirm gate surfaces live cell count × opus tier ×
  rough token/$ estimate (surface, don't block).
- **Review #9 — barrier glob ∩ hat_id:** the synthesis barrier resolves surviving notes from disk and
  INTERSECTS with the 8-value hat vocabulary, pinning to `{NN}-{slug}-{hat_id}.ai.md` and excluding
  `-code.ai.md` + slug-prefix collisions. Tested in `tests/test_barrier_glob_intersection.py`.

## Invariants

- **Non-interactive Workflow** — no interactive call inside `workflow.mjs` or any cell; all gates
  precede launch.
- **Angle independence** — each cell gets ONLY `(step, hat_id, goal_context)`.
- **Synthesizer unchanged** — only its input set widens (1 → M notes).
- **`cast-explore` frozen** — zero edits under `agents/cast-explore/`.

## Key Files

- `cast-explore-workflow.md` — the main-agent skill (Phase-1 + gating + matrix-confirm + launch).
- `workflow.mjs` — the JavaScript Workflow engine (fan-out + barrier + isolation + summary).
- `config.yaml` — `model / timeout_minutes / context_mode / proactive / allowed_delegations`.
- `tests/` — review #7 + review #9 unit tests (run via the project venv pytest).
