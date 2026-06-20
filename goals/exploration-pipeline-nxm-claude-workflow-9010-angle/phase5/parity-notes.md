# Parity Notes — N×M pipeline vs `cast-explore` (merge-decision deliverable)

**Status: STRUCTURAL / PRE-COMMITTED.** A live head-to-head (Run 1 = N×M, Run 2 = `cast-explore`
on the SAME goal) was **NOT executed** — both runs require live WebSearch + (for Run 1) the
main-agent Workflow tool, unavailable from this verifier context. This document does the parts that
do NOT need a live run: it **pre-commits the win conditions**, states the **fairness guardrails**,
maps the **hat↔angle correspondence**, and frames the **four axes** so the eventual live comparison
is evidence, not cherry-picked vibes. The live quotes-and-numbers fill-in is the runbook's Run-1/Run-2
deliverable. This is **advisory input** to the user's parallel→merge call — Phase 5 does NOT cut over;
the Decisions table fixes "Workflow ships in parallel … user merges later." [[feedback_ask_with_recommendation]]

## Collision-safe strategy (named, per Activity A)

**Strategy (i) — throwaway sibling goal (preferred).** Run `cast-explore` in a second goal dir
`exploration-pipeline-nxm-claude-workflow-9010-angle-baseline` so it gets its own
`exploration/` (it HARDCODES `<output-dir>/exploration/`, `cast-explore.md:73` — an ad-hoc
`exploration-baseline/` target is not honorable by instruction). Both trees then live simultaneously
with clean provenance. Fallback (ii) — run `cast-explore` first, `cp -r exploration/
exploration-baseline-snapshot/`, then Run 1 overwrites `exploration/`; the snapshot is the durable
Run-2 evidence. **Verify both trees side-by-side and intact BEFORE any read.** (Runbook R0.)

## Fairness guardrails (pre-committed, before any notes are read)

1. **Non-isomorphic hat sets, stated up front.** `cast-explore` researches **7 angles** in a single
   per-step context; the N×M pipeline runs **up to 8 hats**, each in an **isolated clean context**,
   including the NEW first-class **90/10 hat** that has **no `cast-explore` equivalent** (it was a
   buried sub-bullet inside the old first-principles angle). The comparison holds **goal + approved
   steps constant** but is NOT a like-for-like angle map.

2. **Hat ↔ angle correspondence (explicit; 90/10 marked as no-baseline):**

   | N×M hat (8) | `cast-explore` angle counterpart | Note |
   |-------------|----------------------------------|------|
   | `expert-practitioner` | "how the best orgs do it" angle | text reused, reframed single-hat |
   | `tool-landscape` | tool-comparison angle | direct |
   | `ai-native` | "what AI makes newly possible" angle | direct |
   | `community-wisdom` | practitioner-lessons angle | direct |
   | `framework-methodology` | structured-approaches angle | direct |
   | `contrarian` (always-on) | contrarian section (single-context) | **sharpness thesis** — isolation vs contamination |
   | `first-principles` (always-on) | first-principles section (single-context) | **sharpness thesis** + 80/20 carved OUT |
   | `90-10` (always-on, NEW) | — *(buried sub-bullet only)* | **no baseline counterpart — do NOT force a pairing** |

3. **Confound disclosure.** Both runs draw on **live web search (nondeterministic)** and the same
   model family; differences may owe to run-to-run variance, not architecture. Where a quoted
   before/after is the *whole* evidence for an axis, use **2–3 examples**, not one, so a single
   lucky/unlucky draw doesn't carry the verdict.

4. **Pre-committed win conditions (write these BEFORE reading the live notes; judge against them, not
   post-hoc):**
   - **Angle sharpness WIN** = the isolated `contrarian` note names a **concrete, specific failure
     mode** (a named mechanism / scenario) that the `cast-explore` contrarian section **hedged,
     generalized, or omitted** — in ≥2 of the steps. The thesis (`web-researcher-angle-fanout.md`):
     "contrarian gets watered down … first principles contaminated" when angles share one context.
   - **First-principles sharpness WIN** = the isolated `first-principles` note reasons from value/physics
     **without drifting into effort-minimization or tool talk** (the contamination the carve-out
     prevents), where the `cast-explore` first-principles section visibly blends in 80/20 / tooling.
   - **90/10 WIN** = the `90-10` note delivers a **clean cut proposal** with a `RECOMMENDED CUT |
     CUT WITH CAUTION | DO NOT CUT` verdict that `cast-explore` **only buried as a sub-bullet** (or
     never surfaced as an explicit cut decision).
   - **Playbook quality WIN** = the N×M playbook for a step is **more opinionated / more actionable /
     better-sourced**, OR surfaces an angle the single-context pass missed, in ≥2 steps.
   - **No-win / regression** = if isolation produces **more boilerplate, redundant, or thinner** notes
     than the single-context pass with no sharper take, that is honest evidence AGAINST the thesis and
     must be recorded as such.

## The four axes (frame now; numbers/quotes filled by the live runbook)

### Axis 1 — Playbook quality
Per step, diff the two pipelines' `playbooks/{NN}-{slug}.ai.md`. **Note:** the synthesizer is
IDENTICAL across both pipelines (`cast-playbook-synthesizer`, unchanged) — so any playbook-quality
delta is **entirely attributable to the upstream research it was fed** (M isolated hat notes vs 1
blended per-step note). This is a clean experiment: same synthesizer, different research substrate.
**Fill from live:** ≥2 steps where the N×M playbook is more opinionated/actionable/sourced, OR cite
that it is not. *(Pending Run 1 + Run 2.)*

### Axis 2 — Angle sharpness (the core hypothesis)
Compare Run-1 `contrarian` / `first-principles` notes vs the corresponding angle SECTIONS inside
`cast-explore`'s single per-step note. **Fill from live:** concrete before/after quotes (2–3) on
contrarian + first-principles; confirm the `90-10` hat delivers a clean-context cut proposal
`cast-explore` only buried. Judge strictly against the pre-committed win conditions above.
*(Pending Run 1 + Run 2.)*

### Axis 3 — Cost / time
- **Wall-clock:** record start/end for both runs.
- **Cell count (the explicit trade):** `cast-explore` = 7 angles × N steps (+ code angle). N×M
  ungated worst case = `Σ M_applicable(step)`; with relevance gating the always-on floor is **3 hats
  × N steps** + whatever the interactive Phase-1 gated in. **Record live cell count vs `N×M_total`**
  to show gating kept the premium bounded. Concurrency cap `min(16, cores−2)` (`workflow.mjs:125`)
  bounds wall-clock despite the cell increase.
- **Token/cost:** if run records expose per-run totals, record them; else degrade to
  wall-clock + cell-count (acceptable, noted). The N×M premium (more isolated contexts = more
  prompt-replay of goal context per cell) is the explicit cost the user weighs at merge.
*(Pending both runs.)*

### Axis 4 — Recommended disposition (advisory ONLY — not a decision)
One paragraph, written AFTER the live axes are filled: does the sharpness/quality gain (Axes 1–2)
justify the cost premium (Axis 3)? Framed strictly as **input to the user's parallel→merge call**.
Per the Decisions table the Workflow stays **parallel** to `cast-explore`; Phase 5 does NOT cut over.
[[feedback_ask_with_recommendation]] *(Pending live axes.)*

## Structural read available now (no live run needed)

Even absent the live numbers, the **architecture** supports the thesis on its face:
- **Isolation is real, not nominal.** Each hat cell is a fresh clean-context `cast-hat-researcher`
  invocation (`workflow.mjs` `parallel()` over hats) that loads exactly ONE hat block and MUST NOT see
  siblings (SC-002 evidence) — so the "contrarian watered down by sharing context with 6 polite
  angles" failure mode the thesis names is **structurally precluded**, not merely discouraged.
- **The carve-out is real.** 80/20 is DELETED from first-principles and re-homed in a dedicated 90/10
  hat (SC-003 evidence) — so the "first-principles contaminated by effort-minimization" failure mode
  is also structurally precluded.
- **The cost premium is real and bounded.** More isolated contexts ⇒ more goal-context replay per
  cell (the premium), but relevance gating (always-on floor = 3 hats) + `min(16, cores−2)` concurrency
  bound it. The trade is genuine; only the live magnitude is unknown.

**Net (structural, advisory):** the design makes the *mechanism* for sharper isolated angles real and
the cost premium real-but-bounded. Whether the realized quality gain on a given goal clears the cost
bar is exactly the empirical question the live runbook answers — and exactly the call the user keeps
at merge time. **No cutover recommended; parallel disposition stands until the live evidence lands.**
