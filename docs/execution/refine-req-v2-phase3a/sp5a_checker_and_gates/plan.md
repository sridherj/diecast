# Sub-phase 5a: `cast-requirements-checker` + Zero-Click Extractor + Golden Gates — WP-F

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.
> **Parallel with sp5b** — distinct files, no conflicts.

## Objective
Land the SC-001 gate machinery: the `extract_zero_click_view()` extractor (makes "zero clicks" a
structural property of the gate input, not prompt discipline) + its bin wrapper; the
`cast-requirements-checker` subagent (judges only the zero-click surface, returns the canonical bare
JSON verdict); the per-family **golden HTML snapshots** in default CI plus the structural assertion
battery and rescue-path goldens; and the `tests/eval_render_checker.py` eval harness — the SC-001
sign-off artifact (owner decision #1: snapshots in default CI, checker as an `eval_` harness).

## Dependencies
- **Requires completed:** sp4 (renderer + service + route all green; the full render stack exists).
- **Assumed codebase state:** `render_requirements()` is byte-stable; `tests/fixtures/family_docs/`
  fixtures exist (Phase 2 WP-D); the agent fleet tooling (`bin/generate-skills`,
  `/cast-agent-compliance`, `/cast-agent-design-guide`) is available.

## Scope
**In scope:**
- `requirements_render/zero_click.py` → `extract_zero_click_view(html) -> str` (stdlib
  `html.parser`): keeps Goal Card, headings, open content, `<summary>` lines; drops
  closed-`<details>` bodies and tags. Bin wrapper `bin/cast-render-zero-click <file>` (sys.path
  bootstrap like `bin/cast-spec-checker`; exit 2 on unreadable input).
- `agents/cast-requirements-checker/cast-requirements-checker.md` + `config.yaml` (Naming Contract
  shape: `model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `timeout_minutes: 10`). Input: path to a rendered
  `refined_requirements.html`; the agent runs `bin/cast-render-zero-click` and judges ONLY that
  extracted surface (it must be the unfamiliar reader — never opens the markdown/writeup). Output:
  EXACTLY ONE bare JSON object (canonical verdict schema; no prose, no fences).
- Golden snapshots in default CI + structural assertion battery + rescue-path goldens.
- `tests/eval_render_checker.py` — the SC-001 sign-off eval harness (excluded from default discovery
  by the `eval_` filename).
- The agent pin test + run `bin/generate-skills` + `/cast-agent-compliance`.

**Out of scope (do NOT do these):**
- Any renderer/service/route changes (sp1–sp4 — done). If a golden reveals a render bug, fix it in
  the owning sub-phase's file but keep the change minimal and re-run that sub-phase's tests.
- The new spec doc + FR-007 guard extension (sp5b — parallel).
- Wiring the checker into `cast-refine-requirements` (v2 ships it **standalone** — explicit
  non-goal; the ~650-line prompt ceiling is claimed by Phases 1b/2).
- Putting the checker inside `cast-delegation-contract` (it is deliberately outside — bare JSON, no
  `.output.json`).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/zero_click.py` | Create | Does not exist |
| `bin/cast-render-zero-click` | Create | Does not exist |
| `agents/cast-requirements-checker/cast-requirements-checker.md` | Create | Does not exist |
| `agents/cast-requirements-checker/config.yaml` | Create | Does not exist |
| `cast-server/tests/test_zero_click_extractor.py` | Create | Extractor behaviour |
| `cast-server/tests/test_requirements_renderer.py` | Modify | Add golden byte-compares + full structural battery + rescue goldens |
| `cast-server/tests/golden/requirements_render/{family}.html` | Create | One golden per family + rescue goldens |
| `cast-server/tests/eval_render_checker.py` | Create | SC-001 eval harness (excluded from default CI) |
| `cast-server/tests/test_requirements_checker_agent.py` | Create | Agent string pin test |

## Detailed Steps

### Step 5a.1: `extract_zero_click_view()` + bin wrapper
Stdlib `html.parser` subclass that walks the rendered HTML and emits the text a non-clicking reader
sees: Goal Card text, headings, open content, `<summary>` lines; **drops** closed-`<details>` body
text and all tags. Bin wrapper `bin/cast-render-zero-click <file>`: bootstrap `sys.path` (pattern
from `bin/cast-spec-checker`), read the file, print the extracted view; **exit 2** on unreadable
input.

### Step 5a.2: `cast-requirements-checker` agent
Create `agents/cast-requirements-checker/cast-requirements-checker.md` + `config.yaml` per the
Naming Contract. Lineage: `cast-spec-checker` (deterministic cousin) + `cast-preso-check-*` (verdict
style). The prompt:
- **Input:** a path to a rendered `refined_requirements.html`. The agent runs
  `bin/cast-render-zero-click` and judges ONLY the extracted surface — it never opens the markdown or
  the raw writeup (it must be the unfamiliar reader).
- **Rubric (reused from cast-preso):** `one-clear-takeaway` (single takeaway identifiable in <5s from
  the Goal Card) + `l1-l2-hierarchy` (job statement dominates; assertions secondary), plus the
  restate test: state the job, the primary outcome, and what's in/out of scope.
- **Output:** EXACTLY ONE bare JSON object — the canonical verdict schema
  `{can_state_what, restated_job, restated_outcome, restated_scope:{in,out}, missing, score, issues}`
  — no prose, no fences (Phase 2 classifier precedent).
- **PASS rule (binary, code-checkable):** `can_state_what == true` AND no `missing[]` entry naming
  job/outcome/scope. `score` follows preso scoring (start 1.0, −0.15/error, −0.05/warning) and tracks
  improvement only — **the gate is the boolean, never the float** (judge variance must not flip it).
- State, in the prompt, that the checker is **outside `cast-delegation-contract.collab.md`** (returns
  bare JSON as final text, writes no `.output.json`) — the Phase 2 classifier carve-out — so nobody
  "fixes" it into an output envelope.

### Step 5a.3: `bin/generate-skills` + conformance gate
Run `bin/generate-skills` after creating the agent. Then run **`/cast-agent-compliance`** (consult
`/cast-agent-design-guide`) to validate `config.yaml` fields + the subagent I/O contract against
fleet canon (plan-review #2 — the string pin-test checks rubric/verdict keys only, not config
conformance).
→ Delegate: `/cast-agent-compliance` — target `agents/cast-requirements-checker/`; review its
output for `dispatch_mode`/`context_mode`/`timeout_minutes` conformance + the subagent-mode
carve-out.

### Step 5a.4: Golden snapshots + structural battery (default CI)
Extend `tests/test_requirements_renderer.py`: render each `tests/fixtures/family_docs/` fixture →
byte-compare against `tests/golden/requirements_render/{family}.html`; regeneration via
`UPDATE_GOLDENS=1` env flag. Add the full structural assertion battery from the plan's Verification
list: Goal Card outside `<details>`; pill `family-pill--{value}` present; scope compare open; **zero
`id=` and zero `data-block-anchor` on requirement sections**; zero hardcoded hex outside `:root`;
every block under a heading with contiguous text. Add **rescue-path goldens** (plan-review #4):
(a) missing classification, (b) garbage classification → `GENERIC` + "Unclassified" pill + warning,
(c) stub → prompt-to-begin — each asserting the expected `RenderResult.warnings` entry, not just the
HTML.

### Step 5a.5: Zero-click extractor test
`tests/test_zero_click_extractor.py`: extractor output contains Goal Card + headings + `<summary>`
text, and contains **NO** text that lives inside a closed `<details>` body.

### Step 5a.6: Eval harness (SC-001 sign-off)
`tests/eval_render_checker.py`: dispatch the checker on each family's golden render; print per-family
verdicts + warnings; **gate: `can_state_what == true` for every family** and `missing[]` empty for
job/outcome/scope. Run on demand and before declaring the phase done. Excluded from default discovery
by the `eval_` filename (Phase 2 precedent). Use `/cast-child-delegation` mechanics if dispatching
the subagent via the agent runtime.

### Step 5a.7: Agent pin test
`tests/test_requirements_checker_agent.py`: assert `cast-requirements-checker.md` contains the rubric
names `one-clear-takeaway` and `l1-l2-hierarchy` and **every** canonical verdict key (precedent:
`tests/test_b1_domain_search.py`).

## Verification

### Automated Tests (permanent, default CI)
- `cd cast-server && pytest tests/test_requirements_renderer.py` — goldens byte-match + full
  structural battery + rescue goldens green.
- `pytest tests/test_zero_click_extractor.py` — extractor keeps open surface, drops closed bodies.
- `pytest tests/test_requirements_checker_agent.py` — rubric + verdict-key pins green.
- `bin/cast-render-zero-click <a-rendered-file>` prints the zero-click view; exit 2 on a bad path.

### Validation Scripts (temporary / manual-slow)
- `cd cast-server && UPDATE_GOLDENS=1 pytest tests/test_requirements_renderer.py` regenerates
  goldens after an intentional template change; diff to confirm only intended changes.
- `python tests/eval_render_checker.py` (the SC-001 sign-off) — every family `can_state_what: true`,
  no `missing[]` for job/outcome/scope.

### Manual Checks
- `/cast-agent-compliance` on `agents/cast-requirements-checker/` reports conformant.
- Confirm `eval_render_checker.py` is **not** collected by default `pytest` (the `eval_` prefix).

### Success Criteria
- [ ] `extract_zero_click_view()` + `bin/cast-render-zero-click` (exit 2 on bad input) work.
- [ ] `cast-requirements-checker` agent exists, judges only the zero-click surface, returns the bare
      canonical verdict; PASS rule is the boolean `can_state_what` + `missing[]`, not the score.
- [ ] `bin/generate-skills` run; `/cast-agent-compliance` passes; agent pin test green.
- [ ] One golden per family + rescue goldens byte-match in default CI; full structural battery green;
      zero `id=`/`data-block-anchor`; zero hex outside `:root`.
- [ ] `tests/eval_render_checker.py` excluded from default CI; on-demand run shows
      `can_state_what: true` for every family (**SC-001 sign-off**).
- [ ] Checker is standalone (NOT wired into `cast-refine-requirements`) and outside the delegation
      contract.

## Execution Notes
- "Zero clicks" being a property of the **extractor input** (not the prompt) is the whole point —
  the checker physically cannot see collapsed content, so a render that hides the WHAT fails the gate
  deterministically.
- Goldens are byte-compares: render determinism (sp2) is the precondition. If a golden is flaky,
  the bug is a stray timestamp/nondeterminism in the renderer — fix the renderer, not the test.
- The eval harness is the **SC-001 sign-off artifact** — running it green per family is the phase
  gate, distinct from the deterministic structural goldens that run every CI.

**Spec-linked files:** the checker agent I/O is documented by sp5b's new spec
(`cast-requirements-render.collab.md`); coordinate the verdict schema + PASS rule wording with sp5b
so the spec and the agent prompt agree. The checker's outside-the-delegation-contract carve-out is
recorded in that spec — read `cast-delegation-contract.collab.md` before asserting the carve-out.
