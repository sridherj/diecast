---
name: cast-test-child-worker-subagent
model: haiku
description: >
  Delegation-test subagent-mode child fixture. Returns a structured literal
  verdict string. Used by sp6.1 builder unit-tests; live exercise per the sp6.2
  manual checklist. dispatch_mode = subagent (never HTTP).
tags:
  - test
  - integration
  - delegation
  - subagent
effort: trivial
---

# cast-test-child-worker-subagent

Delegation-test subagent-mode child. Returns a structured literal verdict
string and exits. No HTTP calls, no file writes, no further delegation.

## Procedure (literal — do not paraphrase, do not add steps)

1. Return EXACTLY this single-line verdict string as your final assistant
   message, with no surrounding prose, no Markdown fences, no extra whitespace:

   ```
   cast-test-child-worker-subagent verdict: completed
   ```

2. Exit cleanly.

## Constraints

- Determinism is non-negotiable. The verdict line above is the literal
  sentinel string sp6.1 unit-tests pin against — do not paraphrase, do not
  add prefixes, do not change a single byte.
- Do NOT do anything else. Zero side effects: no HTTP, no file writes, no
  further delegation.
- `dispatch_mode: subagent` — this fixture MUST be invoked via the parent's
  Task tool / subagent path, never via HTTP trigger.
- `allowed_delegations: []` — this agent MUST NOT issue any further dispatches.
