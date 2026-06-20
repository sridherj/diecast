# cast-hat-researcher — acceptance checks

The single-cell contract Phase 3a inherits before fan-out. Two layers:

1. **Deterministic gates (runnable, CI-able):**
   - `tests/check-distinctness.sh` — SC-002 (no cross-hat leak), SC-003 (no 80/20 in
     first-principles), and the provenance/divergence check (Plan Review Decision #4-A).
     Pass an optional `<research_dir>` to also check produced notes.
   - `tests/check-failure-path.sh` — FR-016/US12 failure contract: NO note file +
     contract-v2 `status: "failed"` JSON.

2. **Human / LLM-judged checks (taste calls — run once on a real step):**

## The 8-hat acceptance run

Run `cast-hat-researcher` once per hat (8 invocations) on ONE real step from a sample goal.

**SC / FR checklist:**

- [ ] **8 files land** at `goals/{slug}/exploration/research/{NN}-{step}-{hat-id}.ai.md`,
      one per hat-id, each with a single `hat:` front-matter value (FR-009).
- [ ] **SC-002 / FR-003:** diff any two hat notes for the same step — they share no
      hat-specific framing; no note references another hat's question/output.
- [ ] **SC-003:** `grep -iE "80/20|80-20|laziest|10% of (the )?effort|cheapest path"` over the
      first-principles note returns nothing; the 90-10 note is the only place that content lives.
- [ ] **90/10 note-shape:** the `90-10` note contains all required sections — core / proposed
      cut / effort / self-checks / disqualifiers / deferred-decision log / verdict ∈
      {RECOMMENDED CUT, CUT WITH CAUTION, DO NOT CUT} / sources — and answers all 6 always-ask
      questions.
- [ ] **Distinctness read:** read first-principles, contrarian, and 90-10 notes side by side —
      first-principles re-litigates *what the value is*; 90-10 accepts the value as given and
      finds the cheapest path; contrarian runs the broad adversarial failure-hunt. No two read
      the same.
- [ ] **Generative, not a gate:** the 90-10 `verdict` reads as a build-recommendation, not a
      grade; no hat scores/audits the step.

## Failure-path acceptance (manual, complements check-failure-path.sh)

- [ ] Force a cell to fail (unreachable step / injected fetch failure): assert (a) NO note
      file is written and (b) a contract-v2 output JSON with `status: "failed"` IS written.

> Status: the deterministic gates pass at author time (run them in CI). The 8-hat live run
> requires live web research and a sample goal; it has NOT been executed at author time and
> is recorded here as the standing acceptance procedure for Phase 3a's first real fan-out.
