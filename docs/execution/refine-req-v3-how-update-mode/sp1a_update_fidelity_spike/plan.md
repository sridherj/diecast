# Sub-phase 1a: Evidence — UPDATE Byte-Fidelity Spike

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` before
> starting — especially "The 1a verdict is a dependency, not a formal orchestrator gate" and the
> `check_update_fidelity` comparison-granularity contract.

## Objective

Answer the one load-bearing unknown with measurements: **can the HOW agent hold unchanged unit
containers byte-identical when handed a prior render + a changed-block list?** The verdict
**selects the Sub-phase 3b UPDATE mechanism** — PASS → gate-enforced LLM copy; FAIL → deterministic
splice. This is a binding decision recorded in a spike note, not advisory. Read-only against
production code; **no production edits in this sub-phase.**

## Dependencies

- **Requires completed:** None. (Phase 5d sign-off is an execution-start gate for the phase as a
  whole, not a data dependency for the spike.)
- **Assumed codebase state:** the production `cast-requirements-how` agent + the `eval_*` /
  `agent_service` subprocess pattern exist and run; the two clean published goldens
  (`new_initiative`, `data_analysis`) live under `docs/goal/refine-requirements-better-rendering-v3/signoff/golden/`;
  the family corpus sources live under `cast-server/tests/fixtures/family_corpus/`.
- **Runs in parallel with Sub-phase 1b.** Disjoint outputs (different spike dirs); no shared files.

## Scope

**In scope:**
- A throwaway UPDATE-prompt prototype (prior render + `block_diff` changed-set + "copy unchanged
  containers byte-exact" obligation) exercised against the **production** `cast-requirements-how`
  agent via the `eval_*` / `agent_service` subprocess pattern.
- **Three docs**, not two: `new_initiative`, `data_analysis`, **plus one `bug_fix`-class doc** — the
  family whose lead-unit paraphrase is the entire reason this plan exists (plan-review Decision #4).
- 2–3 small source edits authored per doc (one modified FR body, one added SC, one removed bullet).
- **≥5 trials per doc** (plan-review Decision #4 — ≥3 cannot resolve a 95% bar; one miss reads as 67%).
- Per-trial measurement: fraction of unchanged unit containers byte-identical, correctness of
  changed-block re-renders, whether removed blocks are dropped, **and the KIND of any byte-divergence
  (whitespace-only vs. reworded)**.
- An explicit PASS/FAIL **verdict** with the chosen mechanism, written to
  `spikes/update-fidelity/verdict.md`.

**Out of scope (do NOT do these):**
- NO production code edits — this is a measurement spike. The UPDATE prompt prototype is throwaway.
- Do NOT implement `check_update_fidelity`, the mode decision, or any 3a/3b code — only measure.
- Do NOT decide the anchoring crux (that is locked); this spike measures byte-fidelity only.
- Do NOT collapse whitespace-only and reworded divergence — they argue for different mechanisms
  (whitespace-only → normalization layer; reworded → splice).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/verdict.md` | Create | Does not exist — the binding PASS/FAIL verdict + mechanism |
| `docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/trials/*.{json,html,md}` | Create | Raw per-trial artifacts (prompts, renders, diffs, measurements) |
| `docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/edits/*.md` | Create | The authored small source edits per doc |

> Spike dirs use the descriptive slug `update-fidelity/` (Phase-1 `spikes/{1a,1b}/` precedent of
> keeping spike evidence away from render-class filenames + CI collection).

## Detailed Steps

### Step 1a.1: Assemble the three corpus docs + author edits

- Recover the corpus source for each of `new_initiative`, `data_analysis`, and one `bug_fix`-class
  doc. The first two have published goldens under `signoff/golden/`; for `bug_fix` use its
  `family_corpus/` source (the family that served `structural_violation` in 5c).
- For each doc, author 2–3 minimal source edits and save them under `edits/<doc>/`: one **modified FR
  body**, one **added SC**, one **removed bullet**. Keep edits surgical — the spike measures whether
  *unchanged* containers survive, so the edited surface must be small and well-isolated.

### Step 1a.2: Build the throwaway UPDATE prompt prototype

Mirror the production `_build_how_prompt` CREATE shape, then add an UPDATE section that inlines:
- the **prior render** (the published golden HTML),
- the **`block_diff` changed-set** (`summarize(diff_blocks(old, new))` — the deterministic engine,
  consumed unchanged), and
- the obligation: **"copy every unchanged unit container byte-exact; re-render only the changed-block
  refs; drop removed blocks."**

Drive it against the **production** `cast-requirements-how` agent via the `eval_*` / `agent_service`
subprocess pattern (the same harness `eval_family_sweep.py` uses). Do not stub the agent.

### Step 1a.3: Measure each trial

For each of ≥5 trials × 3 docs, compute and record:
- **Unchanged-container byte-identity rate:** walk both the prior render and the candidate via
  `container_text_index` (import from `maker_gate.py:259` — do not re-walk by hand); for every block
  NOT in the changed-set, compare **both** the container text AND the raw HTML slice. Record the
  fraction byte-identical.
- **Changed-block correctness:** did the modified/added blocks re-render coherently in the prior
  page's structure?
- **Removed-block drop:** was the removed bullet actually gone?
- **Divergence KIND** for every non-identical unchanged container: **whitespace-only** (a stray space,
  newline, attribute-order) vs. **reworded** (semantic paraphrase). This distinction is load-bearing
  for Sub-phase 3b's normalization layer.

Write each trial's prompt, candidate render, diff, and measurement to `trials/`.

### Step 1a.4: Write the binding verdict

`spikes/update-fidelity/verdict.md` must end with an explicit, machine-greppable verdict:

```
VERDICT: PASS | FAIL
MECHANISM: gate-enforced-llm-copy | deterministic-splice
UNCHANGED_BYTE_IDENTITY: <overall %, per-doc breakdown>
DIVERGENCE_KIND: <whitespace-only count vs reworded count>
```

- **PASS** iff **≥95% of unchanged containers byte-identical across ≥5 trials per doc** (all three
  docs). → `MECHANISM: gate-enforced-llm-copy`.
- **FAIL** otherwise → `MECHANISM: deterministic-splice`.
- If failures are **whitespace-only dominant**, record an explicit note: 3b's normalization layer
  (normalized-text comparison via `container_text_index`) may recover a near-miss into PASS-equivalent
  behavior — but the raw verdict is still computed on byte-identity. Surface the recommendation; do
  not silently upgrade FAIL to PASS.

## Verification

### Validation Scripts (temporary — this whole sub-phase is a spike)
- The trial harness itself is the validation: ≥15 trials (3 docs × ≥5) run end-to-end against the
  production agent, each producing a measurement record under `trials/`.
- A one-off aggregation script prints the per-doc and overall byte-identity rate + the
  whitespace/reworded split, and emits the `VERDICT`/`MECHANISM` lines.

### Manual Checks
- `grep -c "container_text_index" <spike harness>` — confirm the measurement reuses the shared walker
  (import from `maker_gate.py:259`), never a hand-rolled DOM walk.
- Confirm **zero** production files changed: `git status --short cast-server/ agents/` is clean.
- Confirm the `bug_fix`-class doc is one of the three measured (the failing family is exercised).

### Success Criteria
- [ ] Three docs measured (`new_initiative`, `data_analysis`, one `bug_fix`-class), **≥5 trials each**.
- [ ] Per-trial records capture byte-identity rate, changed-block correctness, removed-block drop, and
      **divergence kind (whitespace-only vs reworded)**.
- [ ] `verdict.md` ends with an explicit `VERDICT` + `MECHANISM` (the binding 3b mechanism selector).
- [ ] Measurement reuses `container_text_index`; no second walker.
- [ ] No production code edited (`cast-server/`, `agents/` clean).

## Execution Notes

- **This verdict is binding for sp3a and sp3b.** Both read `spikes/update-fidelity/verdict.md` before
  building the UPDATE prompt section. PASS → gate-enforced LLM copy (HOW emits the full page, a new
  gate verifies byte-identity); FAIL → deterministic splice (server keeps prior bytes, splices HOW
  fragments). The owner decided this is a **recorded verdict, not an orchestrator gate** — so make the
  verdict file unambiguous and greppable; downstream sub-phases depend on reading it, not on an
  orchestrator pause.
- **The whitespace-vs-reworded split is not bookkeeping** — it directly shapes 3b's `check_update_fidelity`
  normalization layer (plan-review Decision #3 / 1a's own design-review note). A whitespace-only failure
  mode argues for normalization, NOT a splice; do not collapse the two.
- Cost is explicitly **not** a constraint for this goal — run the full ≥5-trials × 3-docs spike, don't
  sample it.
- **No browser** — this is a Python re-implementation dry-run; no visual gate here (1b owns the
  placement half).
