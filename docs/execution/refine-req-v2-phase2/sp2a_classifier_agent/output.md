# sp2a Output — `cast-goal-classifier` Agent

**Status:** ✅ Complete. The standalone classify seam exists, is enum-pinned to `families.py`, and
its skill is generated. **sp3a** can now wire it into `cast-refine-requirements`.

## What was built

| File | Action | Notes |
|------|--------|-------|
| `agents/cast-goal-classifier/cast-goal-classifier.md` | Created | The classifier prompt (the door) |
| `agents/cast-goal-classifier/config.yaml` | Created | `dispatch_mode: subagent`, `model: sonnet`, `interactive: false`, `context_mode: lightweight`, `timeout_minutes: 10` |
| `cast-server/tests/test_goal_classifier_prompt.py` | Created | 14 pins (enum drift + contract) — all green |
| `~/.claude/skills/cast-goal-classifier/SKILL.md` | Generated via `bin/generate-skills` | Verified present |

No cast-server code changed (only a new test file added). No output-envelope logic added.

## Contracts sp3a / downstream must honor

**Dispatch:** `dispatch_mode: subagent` (owner Decision #2) — invoke via the **Agent/Task tool**,
never via HTTP trigger. It is deliberately OUTSIDE `cast-delegation-contract.collab.md`: it writes
no `.output.json` envelope and no files. Do not "fix" that.

**Input the caller passes:** `title` + raw `writeup` text, and on a re-classify also the prior
`classification` mapping (so the agent can note a changed family).

**Output the agent returns:** EXACTLY ONE bare JSON object as its final message — no prose, no code
fences:
```
{family, confidence, reasoning, uncertainty_factors, alt_family, modifiers}
```
`modifiers` = `{irreversible: bool, unknown_cause: bool}`. `family`/`alt_family` are bare
`WorkFamily` string values.

**Mandatory follow-up in the caller (sp3a):** the returned JSON MUST be passed through
`families.py::validate_classification()` before use. That is where the enum-typing guarantee lands
(the "strict tool-call" realization): an off-taxonomy label is coerced to `random_idea` and the
coercion is recorded. The prompt is enum-constrained; the validator is defence-in-depth.

## Design decisions encoded in the prompt

- All **9** `WorkFamily` values are named with rich one-line descriptions; a module-scoped pin test
  asserts each `.value` appears in the prompt, so prompt↔enum drift fails CI.
- **`random_idea` is stated as the DEFAULT and the floor**; the prompt's explicit tie-breaker is
  "when in genuine doubt, pick `random_idea`."
- **Sharpened `generic` vs `random_idea` boundary (Decision D2)** via the test "Could I act on this
  as-is?": yes-but-no-family → `generic` ("has shape, wrong bucket"); not-enough-to-act-on →
  `random_idea` ("not enough signal yet"). Tie goes to `random_idea`. This keeps the sp4 corpus
  eval's confusion-pair from bleeding together.
- The agent classifies only; it does **not** decide silent/confirm/choose (that gate is code:
  `families.py::gate` + sp2b's `bin/cast-classify-gate`).

## Verification run

- `uv run --project cast-server pytest cast-server/tests/test_goal_classifier_prompt.py -v` → **14 passed**.
- `bin/generate-skills` → wrote 69 SKILL.md files; `~/.claude/skills/cast-goal-classifier/SKILL.md` confirmed present.
- `load_agent_config('cast-goal-classifier')` parses to `dispatch_mode=subagent, model=sonnet, interactive=False, context_mode=lightweight, timeout_minutes=10`.

A live subagent smoke dispatch was **not** run (this runner's allowlist does not include
`cast-goal-classifier`, and it is subagent-dispatch only). The pin test + config-load check + prompt
eyeball cover the success criteria; sp4's corpus eval is the live behavioral gate.

## Success criteria — all met
- [x] `agents/cast-goal-classifier/{cast-goal-classifier.md,config.yaml}` exist with the contracts.
- [x] Prompt names all 9 `WorkFamily` values and sharpens `generic` vs `random_idea`.
- [x] Pin test green: prompt ⊇ every enum value.
- [x] `bin/generate-skills` run; generated skill verified present.
- [x] No cast-server code change; no output-envelope logic added.
