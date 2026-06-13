# Sub-phase 2a: `cast-goal-classifier` Agent (standalone classify seam)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package B of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Create the standalone `cast-goal-classifier` subagent — the phase-agnostic classify seam. Given a
goal title + raw writeup, it emits exactly one bare JSON object classifying the work into one of the
nine `WorkFamily` values with confidence, reasoning, uncertainty factors, an alternate family, and
modifiers. It is registered first-class (mirrors the extracted router resolver) but in v2 only
`cast-refine-requirements` calls it — ship the door, not the future callers.

## Dependencies
- **Requires completed:** sp1 (`families.py` — for the canonical enum values the prompt must mirror
  and the pin test compares against).
- **Assumed codebase state:** `WorkFamily` exists with its 9 values. No gate bin yet (sp2b, parallel).
- **Parallel with:** sp2b, sp2c. **Shared-file caution:** sp2a and sp2c both run `bin/generate-skills`
  — see Execution Notes for the coordination rule.

## Scope

**In scope:**
- `agents/cast-goal-classifier/cast-goal-classifier.md` (the prompt) + `config.yaml`.
- The input/output contract, the 9 enum descriptions, the sharpened `generic` vs `random_idea` boundary.
- A pin test grepping the prompt for every `WorkFamily` value.
- Run `bin/generate-skills`; verify the generated skill appears.

**Out of scope (do NOT do these):**
- The gate logic — that is `bin/cast-classify-gate` (sp2b) + `gate()` in `families.py` (sp1). This
  agent only *classifies*; it does NOT decide silent/confirm/choose.
- Wiring into `cast-refine-requirements` (sp3a).
- Any cast-server code change — the classifier is a Claude Code subagent, not an HTTP child; it writes
  no `.output.json` envelope (it returns JSON as final text).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-goal-classifier/cast-goal-classifier.md` | Create | Does not exist |
| `agents/cast-goal-classifier/config.yaml` | Create | Does not exist |
| `cast-server/tests/test_goal_classifier_prompt.py` | Create | Does not exist (pin test) |
| (generated) skill for `cast-goal-classifier` | Create via `bin/generate-skills` | Does not exist |

## Detailed Steps

### Step 2a.1: `config.yaml`
```yaml
model: sonnet            # triage task; escalate to opus only if the sp4 corpus eval misses 85%
dispatch_mode: subagent  # Agent tool, no cast-server dependency, no polling (owner Decision #2)
interactive: false
context_mode: lightweight
timeout_minutes: 10
proactive: false
```

### Step 2a.2: The prompt (`cast-goal-classifier.md`)
- **Input contract:** goal title + raw writeup text (+ the prior `classification` mapping when
  re-classifying, so the agent can note a changed family).
- **Output contract:** EXACTLY ONE bare JSON object —
  `{family, confidence, reasoning, uncertainty_factors, alt_family, modifiers}` — **no prose, no
  code fences**. `modifiers` is `{irreversible: bool, unknown_cause: bool}`.
- Embed all 9 `WorkFamily` enum values with rich one-line descriptions (the playbook's descriptions,
  extended to the 3 added families: `testing_qa`, `refactor_migration`, `personal_non_eng`).
- State that **`random_idea` is the default when unsure** (the floor).
- **Sharpened `generic` vs `random_idea` boundary (Decision D2)** — the prompt MUST distinguish the
  two low-structure fallbacks crisply or the sp4 corpus eval shows them bleeding together:
  - `generic` = "structured, real work that fits no specific family" (has shape, wrong bucket).
  - `random_idea` = "not enough signal yet — a thought, not a plan" (the floor).
  - "When in genuine doubt, pick `random_idea`."

### Step 2a.3: "Strict tool-call" realization note (embed in the prompt header as a design comment)
The repo has no `anthropic` SDK usage and agents are Claude Code sessions, so the literal
`tool_choice`-forced `classify_work_family` call is realized as **prompt-constrained JSON output +
MANDATORY code validation** (`validate_classification`, sp1). The enum-typing guarantee lands at the
validation boundary: an off-taxonomy label cannot ENTER the system. If a future guide agent gains
direct API access, swap in the real forced tool call without changing any consumer (the front-matter
contract is the seam).

### Step 2a.4: Generate the skill
```bash
bin/generate-skills
ls .claude/skills/ | grep cast-goal-classifier   # or wherever generated skills land
```

## Verification

### Automated Tests (permanent)
- `cast-server/tests/test_goal_classifier_prompt.py`: grep-pin the agent prompt to contain **every**
  `WorkFamily` value (precedent: `tests/test_b1_domain_search.py` pinning prompt sections). Import the
  enum from `families.py` and assert each `.value` appears in the prompt text → enum drift between
  prompt and `families.py` fails CI.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_goal_classifier_prompt.py -v
# Smoke: dispatch the subagent on a known bug writeup, confirm bare JSON with family/confidence/modifiers.
```

### Manual Checks
- Confirm `config.yaml` has `dispatch_mode: subagent` and `interactive: false`.
- Confirm the generated skill is present after `bin/generate-skills`.
- Eyeball the prompt: all 9 families described; `generic` vs `random_idea` boundary explicit;
  output-format instruction says bare JSON, no fences.

### Success Criteria
- [ ] `agents/cast-goal-classifier/{cast-goal-classifier.md,config.yaml}` exist with the contracts above.
- [ ] The prompt names all 9 `WorkFamily` values and sharpens `generic` vs `random_idea`.
- [ ] Pin test green: prompt ⊇ every enum value.
- [ ] `bin/generate-skills` run; generated skill verified present.
- [ ] No cast-server code change; no output-envelope logic added.

## Execution Notes
- **`bin/generate-skills` coordination (parallel with sp2c):** `generate-skills` regenerates ALL
  skills from `agents/`. It is idempotent and deterministic, so running it in both sp2a and sp2c
  converges to the correct final state — the only risk is a simultaneous-write race if the two
  sessions run at literally the same instant. The orchestrator runs each sub-phase in a separate
  session; if you observe a partial skills tree, simply re-run `bin/generate-skills`. Commit the
  generated output with your sub-phase.
- The classifier is read-only: consumes text, returns JSON, writes no files. Single-writer of the
  requirements doc stays `cast-refine-requirements`.
- Subagent dispatch sits OUTSIDE `cast-delegation-contract.collab.md` — do NOT make it emit an
  `.output.json` envelope. sp3b's new spec records this so nobody "fixes" it later.

**Spec-linked files:** The classifier's contract is specced by sp3b (`cast-goal-classification.collab.md`),
which lands in parallel/after. No existing spec governs this file.
