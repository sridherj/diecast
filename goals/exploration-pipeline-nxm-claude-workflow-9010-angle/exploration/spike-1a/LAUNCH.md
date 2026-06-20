# Spike 1a — LIVE launch instructions (the one step a subagent cannot perform)

This subagent (`cast-subphase-runner`) **does not hold the Workflow capability** — confirmed
two ways: (1) ToolSearch over this context surfaces no `Workflow`/`pipeline`/`parallel` tool;
(2) the Claude Code docs state workflows are a *session-level orchestration feature available to
the main agent only — subagents cannot invoke workflows* (code.claude.com/docs/en/workflows.md,
sub-agents.md). So the live fire is handed to the **main agent**.

## IMPORTANT correction to the plan/ledger's mental model

The plan and decisions-ledger describe the engine as a literal `pipeline()` / `parallel()`
**DSL** that "the Workflow tool" runs. The authoritative docs say otherwise:

- There is **no public `Workflow` tool** and **no user-written `pipeline()`/`parallel()` DSL**.
- A workflow is a **JavaScript orchestration script that Claude *generates*** from a natural-
  language request (or a saved `/workflow-name`), which you approve, and the runtime then runs
  in the background. `pipeline()`/`parallel()` (if they exist) are *internal* to that generated
  script and are **not a documented surface**.

=> **Phase 3a must treat `agents/cast-explore-workflow/workflow.py` not as a hand-authored DSL
script the Workflow tool executes, but as the BLUEPRINT/PROMPT from which the main-agent skill
asks Claude to generate (and save) the orchestration workflow.** The Python `toy_workflow.py`
here is the executable *spec + simulator* of that blueprint, not the workflow itself. This is the
single most important finding for 3a — flag it loudly.

## Option A (recommended, and the only documented-viable one): main-agent skill/command

The entrypoint is a **skill/command running in the main agent**. The skill does NOT itself become
the orchestrator; it hands the main agent a fully-specified workflow request + the computed
`{steps, hat_matrix}` args, and the main agent issues the workflow. Concretely, the main agent runs:

> **LIVE LAUNCH COMMAND (paste into the MAIN agent, not a subagent):**
>
> "Use a workflow to run this exploration fan-out. The fan-out graph is specified in
> `goals/exploration-pipeline-nxm-claude-workflow-9010-angle/exploration/spike-1a/toy_workflow.py`
> (run `python3 toy_workflow.py --print-graph` to see the pipeline/parallel shape). Build the
> workflow so that: for each step in the hat-matrix, run that step's hats **in parallel**, one
> **clean-context** `spike-stub-hat` agent per (step,hat) cell; pass each cell ONLY its own
> `{step, hat, nonce, notes_dir}`; write one note per cell to `…/spike-1a/notes/{step}-{hat}.md`.
> Use this 2×2 hat-matrix as args:
> `{steps:[{nn:'01',slug:'alpha',hats:['contrarian','first-principles']},
>           {nn:'02',slug:'beta', hats:['contrarian','first-principles']}]}`.
> After the run, save it as `/cast-explore-spike` so I can re-run with `/workflows`."

### What to OBSERVE during the live run (records the Issue #1 gate evidence)

1. **Background handoff (non-blocking):** confirm the main session stays responsive after launch
   and the run shows under `/workflows` as running. (Docs: workflows run in the background.)
2. **Terminal signal:** confirm the run's **result/summary lands back in the session as a message**
   on completion, and `/workflows` shows it as completed. (Docs: result lands in session; poll via
   `/workflows`.) **This is the terminal-signal seam 3a inherits.**
3. **Summary-assembly location:** confirm the **final stage of the generated script** is where any
   aggregation/summary is assembled (NOT the launcher after return). (Docs confirm in-script
   assembly.) => 3a's per-step synthesis barrier + summary belong as the **final pipeline stage**,
   not in the launching skill.
4. **Non-interactivity:** confirm the workflow takes **no mid-run user input** — all human-in-loop
   (decompose/approve/compute matrix) must precede launch. (Docs: "No mid-run user input.")
5. **Isolation:** open each of the 4 notes; confirm each contains ONLY its own nonce (no foreign
   nonce). Run `python3 toy_workflow.py --simulate` produces the same 4-note isolation proof
   structurally; the live run must match.
6. **Cap:** for the cap check, re-run the saved workflow with the wide matrix
   (`--wide 6 4` shape, 24 cells) and confirm ≤ the machine cap run concurrently while the rest
   queue (docs: up to 16, fewer on low-CPU; auto-queue).

## Option B (fallback — server-side dispatch)

Only if Option A cannot be wired from a skill/command surface. Mirrors `render_job_service`'s
background-job pattern to kick the workflow. Heavier; less aligned with "launched via the workflow,
not a subagent". Not needed unless A fails — and A is the documented-supported path.

## If the live run is NOT VIABLE

Route to the documented fallback: keep a `cast-explore`-style **orchestrator agent** but enforce
**per-hat child isolation** — each (step,hat) dispatched as its own clean-context child via
`/cast-child-delegation` (one hat per child, NOT 7-hats-in-one-context). Keeps angle-independence
(US1/FR-003); sacrifices only deterministic-Workflow orchestration (US2/FR-001) — surface, don't
silently downgrade.
