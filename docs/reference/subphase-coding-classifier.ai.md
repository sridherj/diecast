# Sub-phase Coding-vs-Non-Coding Classifier

> Used by `cast-subphase-runner` (B4) to decide whether to delegate post-execution review
> to `cast-review-code`. This is a contributor-extensible heuristic doc — add new examples
> as the rule's edges are discovered.

## Rules

1. **Coding sub-phase if** the verification section mentions tests (e.g., `pytest`, test file
   names), files (e.g., specific paths, function names, module names), or the activities
   include `Edit` / `Write` / file-creation actions.

2. **Non-coding sub-phase if** activities use words like "research", "explore", "decompose",
   "synthesize", "plan", "spec" with NO `Edit` / `Write` actions and NO test file authoring.

3. **Hybrid sub-phases (research-then-implement)** should be split into two sub-phases at
   planning time. If a hybrid slipped through and is being executed in one run, classify the
   *executed-this-run portion* — i.e., the portion that wrote files is coding; the upstream
   research portion was already done.

## When in Doubt

If the heuristic is ambiguous on a real sub-phase (this happens when a "research" sub-phase
also writes a `playbook.ai.md`, for example), the runner asks the user via
`cast-interactive-questions`:

> "This sub-phase looks like a hybrid (research + light file authoring). Treat as coding
> (review with cast-review-code) or non-coding (skip)?"

CI lint (`cast-agent-compliance`) flags any sub-phase that the runner had to ask about —
surfaces classification quality regressions over time.

## Worked Examples

### Coding (DELEGATE to cast-review-code)

1. **`sp1_b5_polling_foundation`** — verification mentions `tests/test_b5_*.py`, edits agent prompts and skill files.
2. **`sp2_b6_terminal_portability`** — creates `agents/_shared/terminal.py`, edits prompts.
3. **`sp4b_us10_tshirt_estimates`** — edits `db/schema.sql`, `task.py`, authors a migrator script.
4. **`sp4d_us14_typed_next_steps`** — edits config.yaml across many agents, authors a JSON Schema.

### Non-Coding (SKIP cast-review-code)

5. **A `cast-explore` decomposition run** — output is `decomposition.ai.md`. No source-file edits, just structured markdown.
6. **A `cast-web-researcher` deep-dive** — output is `research_notes.ai.md`. No Edits to source.

### Hybrid (resolve via cast-interactive-questions or split at plan time)

7. A "research the current cast-orchestrate behavior, then write a refactor plan" sub-phase →
   research is non-coding, writing the plan is light file authoring (markdown only). The
   runner should ask: review the plan with cast-review-code, or skip?

## Adding a New Example

Open a PR adding the example to the appropriate section above with a one-line rationale.
The classifier evolves through accumulated worked examples — that's the point.
