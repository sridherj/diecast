# Sub-phase 4a-1: The Checker Speaks a Folded, Code-Gateable Verdict

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4a/_shared_context.md` before starting.

## Objective

Create `agents/cast-requirements-render-checker/` as a net-new, registry-discoverable agent
(`.md` + `config.yaml`, picked up by `bin/generate-skills`), runnable tool-free via the Phase 3
`AgentRunner`. It grades comprehension **and** visual quality in ONE pass and emits ONE bare-JSON
verdict that is a strict **superset** of the v2 SC-001 cold-reader shape. Alongside it, create the
pure module `cast_server/requirements_render/checker_verdict.py` that parses the verdict and
**computes the binary PASS and the canonical score CODE-SIDE** — the agent never decides its own
gate. The checker's prompt carries the **gap-amnesty clause** (owner edit, revision d).

## Dependencies

- **Requires completed:** Phase 3 built (the `AgentRunner` seam, `maker_gate.py`, the agent-dir
  conventions). **None within Phase 4a** — the verdict contract is fixed by the plan, not discovered
  from the prompt, so 4a-1 runs in **parallel with 4a-2**.
- **Assumed codebase state:** `agents/cast-requirements-checker/` and `agents/cast-comment-reanchor/`
  exist as the subagent carve-out precedent; `zero_click.extract_zero_click_view`,
  `maker_gate.py`, and `eval_render_checker._parse_verdict_json` exist;
  `cast-goal-classification.collab.md`'s `WorkFamily` enum exists.

## Scope

**In scope:**
- `agents/cast-requirements-render-checker/cast-requirements-render-checker.md` (the prompt +
  contract block + the gap-amnesty clause).
- `agents/cast-requirements-render-checker/config.yaml` (subagent carve-out; `model: opus`
  placeholder).
- `cast_server/requirements_render/checker_verdict.py` (pure: `parse_verdict`, `derive_pass`,
  `canonical_score`, the `CheckerVerdict` frozen dataclass).
- `cast-server/tests/test_checker_verdict.py`.
- Regenerate `bin/generate-skills` output so the skill appears without manual registry edits.

**Out of scope (do NOT do these):**
- Do NOT touch `render_job_service.py`, `config.py`, `schema.sql`, or `pages.py` — those are 4a-2.
- Do NOT wire the checker into the loop or write any `decide_quality` logic — 4a-2 owns that.
- Do NOT modify or retire the v2 `cast-requirements-checker` agent or `eval_render_checker.py` —
  they remain the deterministic-substrate SC-001 gate, untouched.
- Do NOT edit the spec — 4a-3 records the contract verbatim.
- Do NOT add viewport-fit or any image/screenshot criteria (a scrolling document; autonomous runs
  cannot drive a browser).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-render-checker/cast-requirements-render-checker.md` | Create | Does not exist |
| `agents/cast-requirements-render-checker/config.yaml` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/checker_verdict.py` | Create | Does not exist |
| `cast-server/tests/test_checker_verdict.py` | Create | Does not exist |
| generated skills output (`bin/generate-skills`) | Regenerate | Stale (no checker skill) |

## Detailed Steps

### Step 4a1.1: Author the checker agent `.md`

Philosophy: **you are an unfamiliar reader with taste** — the SC-001 cold reader and the design
reviewer in one pass. The runner inlines all inputs into the user message (the agent is tool-free
and physically cannot fetch anything else), in this order:

1. the **zero-click view** (the exact `extract_zero_click_view` output — the restate test is
   performed on THIS SECTION ALONE, before reading further; state this ordering as a **hard rule**
   in the prompt);
2. the **full candidate HTML** (visual quality + below-the-fold comprehension);
3. the **family label** (e.g. `new_initiative`) — so family-appropriateness is judgeable;
4. NOTHING else: **never the canonical source, never the WHAT doc** (fidelity-to-source is
   `maker_gate`'s job; the checker judges only what a reader experiences).

**Comprehension criteria** (the SC-001 fold-in + document-depth additions): `restate-test` (state
job / primary outcome / in-out scope from the zero-click surface alone — **the gated core**),
`one-clear-takeaway`, `l1-l2-hierarchy` (both reused verbatim from the fleet vocabulary),
`section-outcomes-land` (each section communicates one clear takeaway, not a reformatted dump),
`scannable-not-wall` (navigable by headings; no wall-of-text blocks).

**Visual criteria** (adapted from the preso check-visual vocabulary — pattern reference, NOT
invocation): `not-generic`, `hierarchy-clear`, `toolkit-consistent`, `whitespace-breathes`,
`not-ai-aesthetic`, `family-appropriate-structure` (sections read as family communication — "what
broke and the evidence", "signal sources" — **never** US/FR/SC slots), `anchor-labels-unobtrusive`
(visible id labels stay small metadata, **warning-only**). Viewport-fit + the three image criteria
are **dropped**.

**GAP-AMNESTY CLAUSE (owner edit, revision d) — put this verbatim in the prompt:**

> `.rr-gap` markers are honest communication of a source gap, not a comprehension failure of the
> render. When a section is marked `.rr-gap` (a question + fixed status vocabulary), do NOT score
> it as a missing outcome or a comprehension defect — the render is faithfully surfacing that the
> *source* is incomplete. Judge the render on how clearly it communicates the gap, not on the gap's
> existence.

Without this clause the loop fights the Phase-5 gap contract (a `.rr-gap` page would be perpetually
re-worked as if the maker were hiding the WHAT).

### Step 4a1.2: The verdict contract block (record it in the `.md`)

Emit ONE bare JSON object — no prose, no fences (the FR-011 subagent carve-out). Schema is fixed in
`_shared_context.md` ("Checker verdict … /v1"). Hard rules to state in the prompt:
- v2 field names/semantics unchanged (strict superset);
- `issues[]` carries `dimension` (`comprehension|visual`) + `evidence`;
- **every `error` issue MUST contribute ≥1 `rework_feedback` string** — a fail with no actionable
  feedback is a prompt bug;
- the agent's own `score` is **advisory** (code recomputes the canonical score); say so, so the
  agent doesn't try to game its own gate.

### Step 4a1.3: `config.yaml` (subagent carve-out precedent)

```yaml
dispatch_mode: subagent
interactive: false
context_mode: lightweight
allowed_delegations: []
timeout_minutes: 15
model: opus   # [USER-DEFERRED] tier knob — placeholder, do not tune here
```

(Mirror `cast-requirements-checker` / `cast-comment-reanchor` exactly; the `model:` placeholder +
tuning-knob comment is the Phase-3a convention adopted verbatim. Owner confirmed `opus` 2026-06-12.)

### Step 4a1.4: `checker_verdict.py` (pure, I/O-free, beside `maker_gate.py`)

- `CheckerVerdict` — frozen dataclass mirroring the JSON shape.
- `parse_verdict(raw: str) -> CheckerVerdict` — tolerant extraction reusing the
  `eval_render_checker._parse_verdict_json` salvage pattern (fenced/chatty wrappers tolerated);
  genuinely malformed JSON **raises** (the service layer maps that raise to checker-unavailable
  handling — the parser NEVER coerces garbage into a verdict).
- `derive_pass(v) -> bool` — **the binary PASS, code-side**: `can_state_what == True` AND no
  `missing[]` entry containing a gated token (`job`/`outcome`/`scope`) AND **zero `severity:"error"`
  issues in either dimension**. Warnings never block (judge taste-variance must not churn the loop).
- `canonical_score(v) -> float` — **recompute** deterministically from issue counts:
  `1.0 − 0.15·errors − 0.05·warnings`, floored at 0 (the preso convention). Never trust the
  agent-emitted float for ranking.

Pull the gated-token set and severity strings out as module constants so the test and the agent
prompt reference one source.

### Step 4a1.5: Fold in the Phase-1a judge anomalies

→ Read `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md` for recorded
judge anomalies (the 1a carry-forward). If the v2 checker mis-judged a family-restructured page,
the new prompt must explicitly allow family vocabulary (the `family-appropriate-structure`
criterion already does this — verify it covers the recorded anomaly; extend the prompt if not).

### Step 4a1.6: Regenerate skills

Run `bin/generate-skills` so the checker appears in the skill registry without manual edits.

## Verification

### Automated Tests (permanent)

`pytest cast-server/tests/test_checker_verdict.py` green, **≥1 fixture per outcome**:
- a clean pass (`can_state_what`, no missing, no error issues) → `derive_pass` True, `canonical_score` 1.0;
- fail-on-gated-missing (`missing` contains `outcome`) → `derive_pass` False;
- fail-on-error-issue (one `severity:"error"` visual issue, `can_state_what` True, no missing) →
  `derive_pass` False (asserts the error-issue extension over the v2 boolean);
- warnings-only → `derive_pass` True (asserts warnings never block) + `canonical_score` reflects the
  `−0.05·warnings` term;
- malformed JSON → `parse_verdict` **raises**;
- fenced / chatty wrapper around valid JSON → salvaged and parsed (the `_parse_verdict_json` pattern);
- `canonical_score` recompute independent of the agent-emitted `score` (feed a flattering `score:1.0`
  with two error issues → recomputed 0.7).

### Validation Scripts (temporary)

A hand-run of the agent over the Phase-1a maker-evidence HTML **and** a deliberately low-quality
fixture → verdicts that **discriminate** (evidence passes or near-passes; low-quality fails with
non-empty `rework_feedback`). Record as a **smoke-run note**, not a CI test. (The committed
low-quality fixture itself lands in 4a-3; for this smoke run, any clearly-bad HTML works.)

### Manual Checks

- → **Delegate: `/cast-agent-compliance`** over `agents/cast-requirements-render-checker/` — review
  output for allow-list, naming, and directory-convention violations; fix any flagged.
- → **Delegate: `/cast-agent-design-guide`** (I/O-contract section) while authoring — confirm the
  verdict contract block sits in the agent `.md` as the contract block.
- Confirm `bin/generate-skills` regenerated and the skill appears (grep the generated output).
- Confirm the prompt carries the gap-amnesty clause verbatim and the zero-click-first hard rule.

### Success Criteria

- [ ] `agents/cast-requirements-render-checker/` exists, passes `/cast-agent-compliance`, and is
      registry-discoverable after `bin/generate-skills`.
- [ ] The prompt grades comprehension + visual in ONE pass, inputs in the fixed order, never sees
      source/WHAT, carries the gap-amnesty clause + the zero-click-first hard rule.
- [ ] Verdict is a strict superset of the v2 shape; every `error` issue carries `rework_feedback`.
- [ ] `checker_verdict.py` is pure; `derive_pass` extends the v2 boolean with the zero-error-issue
      rule; warnings never block; `canonical_score` is recomputed code-side (agent float advisory).
- [ ] `test_checker_verdict.py` green with ≥1 fixture per outcome (incl. malformed-raises and
      score-recompute-independent-of-agent-float).
- [ ] v2 `cast-requirements-checker` + `eval_render_checker.py` untouched.

## Execution Notes

- **The gate is code-owned.** The agent emits a verdict; `checker_verdict.py` decides PASS and the
  ranking score. This is the FR-010 "the gate is the boolean" discipline extended to the visual
  dimension AND to best-attempt ranking — judge variance can never flip the gate or skew the rank.
- **The cold-reader property is structural.** The runner (4a-2) inlines only the rendered artifact +
  family; the checker is tool-free. Do not add any prompt instruction that assumes access to the
  source — it cannot have it.
- **Spec-linked files:** the checker I/O is new spec'd behavior under
  `cast-requirements-render.collab.md`. **Flag it for 4a-3's `/cast-update-spec`; do NOT edit the
  spec here.** The contract block in the `.md` is the verbatim text 4a-3 records.
