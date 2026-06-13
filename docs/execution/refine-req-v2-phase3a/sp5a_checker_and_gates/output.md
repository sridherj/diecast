# sp5a output — Checker + Zero-Click Extractor + Golden Gates (WP-F)

**Status: COMPLETE.** All success criteria met. Default-CI tests green (110 sp5a-specific;
235 across the requirements_render suite). The `eval_render_checker.py` SC-001 sign-off harness
is wired and verified in offline-replay mode; its **live per-family run requires the `claude`
CLI** (deferred — see "Human action" below).

## What landed

### 1. Zero-click extractor (the gate's *input* discipline)
- `cast-server/cast_server/requirements_render/zero_click.py` →
  `extract_zero_click_view(html: str) -> str`. Stdlib `html.parser` subclass. Keeps the Goal
  Card, every heading, all open content, and each `<summary>` label; **drops** the body of every
  closed `<details>` plus all tags / `<style>` / `<script>`. Visibility model: the outermost
  *closed* `<details>` ancestor cuts off everything below it except its own direct `<summary>`;
  a `<details open>` reveals its body.
- `bin/cast-render-zero-click <file>` — sys.path bootstrap mirrors `bin/cast-classify-gate`;
  prints the extracted view; **exit 2** on unreadable input / wrong arg count. Executable.

### 2. `cast-requirements-checker` agent (the SC-001 gate)
- `agents/cast-requirements-checker/cast-requirements-checker.md` + `config.yaml`
  (`model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `timeout_minutes: 10`, `allowed_delegations: []`).
- Judges **only** `bin/cast-render-zero-click` output — never the source HTML/markdown (it must
  stay the unfamiliar reader). Rubric reuses cast-preso's `one-clear-takeaway` + `l1-l2-hierarchy`
  plus the restate test (job / outcome / in-out scope).
- Emits EXACTLY ONE bare JSON verdict (no prose, no fences):
  `{can_state_what, restated_job, restated_outcome, restated_scope:{in,out}, missing, score, issues}`.
- **PASS rule (binary, code-checkable):** `can_state_what == true` AND no `missing[]` entry naming
  `job`/`outcome`/`scope`. The gate is the boolean — **never** the `score` float.
- Explicitly **outside `cast-delegation-contract.collab.md`** (subagent-mode, bare JSON as final
  text, writes no `.output.json`) — the Phase 2 classifier carve-out. **sp5b: keep this carve-out
  + the verdict schema + PASS-rule wording in agreement with the new spec.**
- `bin/generate-skills` run (SKILL.md generated). `/cast-agent-compliance` audit: **0 violations,
  0 critical** — conformant for the subagent-mode checker class (matches `cast-goal-classifier`).

### 3. Golden snapshots + structural battery (default CI)
- `cast-server/tests/golden/requirements_render/` — **12 goldens**: one per `WorkFamily` (9) +
  3 rescue goldens (`rescue_missing_classification`, `rescue_garbage_classification`,
  `rescue_stub`). Regenerate with `UPDATE_GOLDENS=1 pytest tests/test_requirements_renderer.py`.
- `cast-server/tests/test_requirements_renderer.py` extended with byte-compares + the full
  structural battery: Goal Card outside `<details>`; `family-pill--{value}` present; scope compare
  open when present; **zero `id=` / zero `data-block-anchor`**; **zero hex outside `:root`**
  (FR-012); every recipe `<section>` under an `<h2>`; no `user-select` suppression; no adjacent-
  span fragmentation. Rescue goldens assert the expected `RenderResult.warnings` entry, not just
  the HTML.

### 4. Tests
- `cast-server/tests/test_zero_click_extractor.py` — keeps open surface + summaries, drops closed
  bodies, nested-closed fully hidden, `<style>`/`<script>` never leak.
- `cast-server/tests/test_requirements_checker_agent.py` — pins the two rubric names + **every**
  canonical verdict key + the binary PASS rule + bare-JSON contract + the carve-out.
- `cast-server/tests/eval_render_checker.py` — SC-001 sign-off harness. **Excluded from default
  pytest** (the `eval_` prefix; verified via `--collect-only`). Modes: `--live` (dispatch the real
  checker per family via `claude -p`, tools disabled, fed the deterministic zero-click view),
  `--verdicts FILE` (offline replay), `--out-verdicts FILE`. Gate logic verified in replay
  (correctly flips to exit 1 when any family fails).

## Important deviation (for sp5b + downstream awareness)
The Phase 2 **WP-D `tests/fixtures/family_docs/` fixture set never landed** (the behavioural test
header already documented this). To avoid blocking sp5a on a missing precondition, the goldens and
the eval render the **same deterministic programmatic family docs** the behavioural suite builds
(`_build_family_doc` in `test_requirements_renderer.py` — one source of truth, imported by the
eval). These are byte-stable, so they are a faithful golden input. **When the real fixtures land,
repoint the golden/eval inputs at them and regenerate with `UPDATE_GOLDENS=1`.**

## Verification run
```
cd cast-server
pytest tests/test_requirements_renderer.py tests/test_zero_click_extractor.py \
       tests/test_requirements_checker_agent.py        # 110 passed
python tests/eval_render_checker.py --verdicts <file>  # gate logic OK (exit 0/1 correct)
bin/cast-render-zero-click <rendered.html>             # prints view; exit 2 on bad path
```

## Human action needed (deferred, non-blocking)
- **Live SC-001 sign-off:** run `python cast-server/tests/eval_render_checker.py --live` once in an
  environment with the `claude` CLI to capture the empirical per-family `can_state_what: true`
  verdicts. The harness + gate are in place; only the live LLM dispatch is deferred (no CLI/network
  in this autonomous run; `cast-requirements-checker` is not in this runner's HTTP allowed_delegations).
