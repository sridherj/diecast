# Sub-phase 1a — UPDATE Byte-Fidelity Spike: Binding Verdict

> **This verdict is a binding dependency for Sub-phase 3a and Sub-phase 3b** (not an orchestrator
> gate — a recorded verdict, per the owner decision of 2026-06-12). Both sub-phases MUST read this
> file before building the UPDATE prompt section. The greppable `VERDICT` / `MECHANISM` trailer is
> at the bottom.

## The question

Can the **production** `cast-requirements-how` agent hold unchanged unit containers **byte-identical**
when handed a prior published render + a `block_diff` changed-set + an explicit "copy every unchanged
container byte-exact" obligation? PASS → Sub-phase 3b uses **gate-enforced LLM copy**; FAIL → Sub-phase
3b uses **deterministic splice**.

## Method (measurement spike — zero production edits)

- **Three docs**, `≥5` trials each (the plan's `≥5` floor — `≥3` cannot resolve a 95% bar):
  - `new_initiative` and `data_analysis` from their published goldens under `signoff/golden/`;
  - **`bug_fix`** — the family whose lead-unit paraphrase is the entire reason this plan exists
    (it served `structural_violation` in the 5c sweep). This is the load-bearing case.
- Per doc, **2–3 surgical source edits** authored under `edits/<doc>/` (one modified FR body, one
  added SC, one removed bullet). The deterministic changed-set is `block_diff.summarize(diff_blocks(
  old, new))` — the engine consumed unchanged (FR-024), persisted as `edits/<doc>/changed-set.json`.
- A **throwaway UPDATE prompt** (`trials/<doc>/update-prompt.txt`) mirrors the production
  `_build_how_prompt` CREATE shape, then appends an UPDATE section inlining the **prior golden
  render** + the **changed-set** + the **copy-exact obligation**. It is driven against the **real**
  `cast-requirements-how` agent through the production `ProductionAgentRunner` subprocess path (the
  same `claude -p … --tools ""` harness the pipeline uses). The WHAT doc is generated once per doc on
  the **new** source via the real `cast-requirements-what` agent, then held fixed across that doc's
  trials, so trial-to-trial variance is purely HOW stochasticity.
- **Measurement reuses the shared walker** `container_text_index` (imported from `maker_gate.py:259`
  — never re-walked by hand). For every prior-render unit container NOT in the changed-set, we test
  byte-survival two ways: (a) **container TEXT** identity — the prior container's exact descendant-
  text appears verbatim in the candidate's `document_text`; (b) **raw HTML slice** identity — the
  prior unit element's exact `outerHTML` bytes appear verbatim in the candidate HTML. Each
  non-surviving container is classed **whitespace-only** (normalized-equal but raw-different) vs
  **reworded** (normalized-different) — the load-bearing distinction for 3b's normalization layer.

Changed/removed containers are excluded from the unchanged denominator (ref-bearing blocks by
canonical id; ref-less blocks by distinctive old-text markers). Each trial also records
changed-block correctness (added/modified blocks rendered) and removed-block drop.

## Results (15 HOW trials + 3 WHAT runs, all against the real agents)

| Doc | Trials | Unchanged containers measured | Byte-identical | **Per-doc rate** | Reworded | Whitespace-only | add/mod rendered | removed dropped |
|-----|--------|------------------------------|----------------|------------------|----------|-----------------|------------------|-----------------|
| `bug_fix` | 5/5 | 40 (8/trial) | 36 | **90.0%** ❌ | 4 | 0 | 5/5 ✓ | 5/5 ✓ |
| `data_analysis` | 5/5 | 5 (1/trial) | 5 | **100.0%** ✓ | 0 | 0 | 5/5 ✓ | 5/5 ✓ |
| `new_initiative` | 5/5 | 200 (40/trial) | 200 | **100.0%** ✓ | 0 | 0 | 5/5 ✓ | 5/5 ✓ |
| **Overall** | **15/15** | **245** | **241** | **98.4%** | **4** | **0** | **15/15** | **15/15** |

Raw-HTML-slice identity and container-text identity agreed exactly on every trial (raw == text
everywhere): there were **no** serialization-noise near-misses. Every divergence was a true rewrite.

## Reading

1. **The PASS bar is per-doc** (`≥95%` unchanged byte-identity across `≥5` trials, **all three** docs).
   `bug_fix` lands at **90.0%** → the spike **FAILS**. The high 98.4% pooled rate is misleading: it is
   dominated by `new_initiative`'s 200 clean containers. The whole point of the `≥5`-trials × bug_fix
   requirement (plan-review Decision #4) was to stop exactly this averaging-away.

2. **The failure mode is rewording, not whitespace — decisively.** `whitespace-only = 0`,
   `reworded = 4` (100% of divergences). In `bug_fix`, HOW paraphrased the **unchanged** "Out of
   scope / Deliberately left for later" narrative container in **4 of 5** trials despite a literal
   copy-exact instruction — re-expressing a block it was told to copy verbatim. Prior bytes:
   *"…One sibling defect in the same file is explicitly deferred, not forgotten — named only so a
   fixer working in goal_card.py does not conflate the two leaks."* The candidate re-wrote it. This
   is precisely the lead-unit/narrative-cell paraphrase the owner diagnosed as the carry-forward —
   reproduced under controlled measurement.

3. **The whitespace-vs-reworded split rules OUT the normalization escape hatch.** The plan's
   `check_update_fidelity` would compare **normalized** container text (Decision #3) — that recovers
   *whitespace/serialization* near-misses. But there are **zero** whitespace-only divergences here;
   the failures are **semantic rewrites** that normalization cannot recover. So a
   gate-enforced-LLM-copy mechanism would not converge on `bug_fix` even with the normalization layer —
   it would thrash on a genuine paraphrase the gate correctly rejects, then degrade. The
   plan's own conditional ("if failures are whitespace-only dominant, normalization may rescue a
   near-miss into PASS-equivalent") is **not** triggered: the failures are reworded-dominant
   (in fact reworded-exclusive). **Do not upgrade FAIL to PASS.**

## Consequence for Sub-phase 3b (binding)

Use the **deterministic-splice** UPDATE mechanism: the server keeps the unchanged unit-container
bytes from the prior render verbatim and splices HOW-rendered changed-block fragments. Byte-identity
of unchanged containers is then guaranteed **by construction**, at the cost of a fragment-rendering
HOW sub-contract — the cost the FAIL branch always anticipated. An LLM-copy + `check_update_fidelity`
gate is **not** sufficient on its own: it cannot hold `bug_fix`'s narrative cells byte-identical, and
the divergence is not the whitespace kind a normalization layer absorbs.

Notes carried forward to 3b:
- The splice boundary is the **unit container** (`container_text_index` `is_unit` element). 3b
  keeps the prior render's unchanged unit-container bytes and re-renders only changed-block
  fragments; `container_text_index` (the same shared walker) identifies the splice seams.
- HOW **does** get changed-block correctness right (15/15 add/mod rendered) and **does** drop removed
  blocks (15/15) — so the fragment-rendering sub-contract is the reliable part; only verbatim
  carriage of untouched prose is not. The splice mechanism leans on exactly the HOW capability that
  works and removes reliance on the one that does not.

## Artifacts

- `edits/<doc>/new.collab.md`, `edits/<doc>/edits.md`, `edits/<doc>/changed-set.json` — authored
  edits + the deterministic changed-set.
- `trials/<doc>/what.md`, `trials/<doc>/update-prompt.txt` — the generated WHAT doc + the exact
  UPDATE prompt driven against the real agent.
- `trials/<doc>/trial-N.{html,raw.txt,json}` — each candidate render, raw agent stdout, and its
  per-trial measurement record.
- `aggregate.json` — the machine-readable roll-up.
- `harness.py` — the throwaway measurement harness (imports `container_text_index`, `diff_blocks`,
  `summarize`, `_build_how_prompt`, `_build_what_prompt`, `ProductionAgentRunner`, `extract_render`
  from production; edits nothing).

---

```
VERDICT: FAIL
MECHANISM: deterministic-splice
UNCHANGED_BYTE_IDENTITY: 98.4% overall (per-doc: bug_fix 90.0%, data_analysis 100.0%, new_initiative 100.0%) — PASS bar is per-doc ≥95%, bug_fix fails
DIVERGENCE_KIND: whitespace-only=0, reworded=4 (100% reworded → normalization layer cannot rescue; do NOT upgrade to PASS)
```
