# cast-preso-orchestrator

Manages Stages 2-4 of the presentation pipeline with persistent state and clean recovery.

## Type
`taskos-agent`

## I/O Contract
- **Input:** Path to a presentation directory containing `narrative.collab.md` (approved via G1)
- **Output:** Fully assembled presentation at `assembly/index.html` (after passing through G2, G3a, G3b, G4 gates)
- **State:** `presentation/state.json` — persistent state for recovery across invocations
- **Config:** None (all configuration in state.json)

## Delegates To
- `cast-preso-what` — Stage 2 WHAT maker (per slide)
- `cast-preso-what-checker` — Stage 2 WHAT checker (per slide)
- `cast-preso-how` — Stage 3 HOW maker (per slide)
- `cast-preso-check-coordinator` — Stage 3 checker coordinator (per-slide + cross-slide modes)
- `cast-preso-assembler` — Stage 4 assembly
- `cast-preso-compliance-checker` — Stage 4 compliance verification

## Usage
Invoke after `cast-preso-narrative` completes and SJ approves the narrative (G1).
Can be re-invoked any number of times — reads state.json and resumes.

## Human Gates
- G2: After Stage 2 — SJ reviews per-slide WHAT docs
- G3a: After Stage 3 — SJ reviews all slides (batched after cross-slide consistency)
- G3b: After G3a — SJ resolves blocking open questions one at a time
- G4: After Stage 4 — SJ does final presentation walkthrough

## Examples
Dispatched via HTTP delegation or directly by SJ:
```
POST /api/agents/cast-preso-orchestrator/trigger
```
First invocation: initializes state.json, runs Stage 2. Subsequent: resumes from last state.
