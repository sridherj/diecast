# sp2_evidence_and_decisions — Output

**Status:** completed
**Checkout edited:** `/home/sridherj/workspace/diecast` (external project checkout, per `_shared_context.md` §Codebase Conventions)
**Prompt line count:** 492 / 650 ceiling (was 459 after sp1; +33 lines)

## What was done

Landed the two output-quality edits of Phase 1b (plan activities 6 and 3) into the
`cast-refine-requirements` agent prompt, plus the two lockstep spec-contract edits.

### Activity 6 — Evidence-quoting mandate (agent prompt)
- **Step 1.5 (Run Sufficiency Check):** added the rule that a section may be rated **medium or
  high** ONLY if a **verbatim quote** from the raw writeup or conversation supports the rating.
  Unquotable support **drops the rating to low** and routes the gap to Open Questions as a
  `[NEEDS CLARIFICATION: …]` entry. Framed as `/plan-eng-review`'s "quote the verbatim motivating
  line" gate applied to confidence; the quote is carried forward to Step 2.1.
- **Step 2.1 (Present Draft):** added a bullet requiring the verbatim quote to be shown inline next
  to every medium/high rating, with the example line
  `Intent — HIGH ("we keep losing track of which goals are actually blocked")`. Noted this is a
  conversation-only presentation detail — the persisted front-matter `confidence:` shape is
  unchanged. A medium/high rating shown without a quote is invalid → drop to low + Open Questions.

### Activity 3 — Dated `## Decisions` section (agent prompt + spec contract)
- **Step 3.1 output template:** inserted `## Decisions` with the
  `| Date | Chose | Over | Because |` table **between `## Out of Scope` and `## Open Questions`**.
- **Answer-time buffering rule** documented inline (mirrors `cast-plan-review`'s
  buffer-at-decision-time pattern): on each `AskUserQuestion` fork resolution append
  `{date, chose, over, because}` to an in-memory list (`date` = harness `currentDate`); render
  verbatim at persist. Explicitly **forbids end-of-session reconstruction** (confabulation risk).
  States the **human-choices-only** constraint (unilateral agent defaults excluded — this is what
  makes the section durable provenance for Phase 4 versioning). **0-fork fallback:** emit the
  section with a single `*No decisions recorded this refinement.*` line (stable section set for
  Phase 1's parser).
- **`templates/cast-spec.template.md`:** added `## Decisions` as an **optional** section (same
  table shape), marked optional via an HTML comment. The canonical template has no `## Out of
  Scope` H2, so the block was placed directly before `## Open Questions` (its faithful position),
  with the comment noting it belongs before Out of Scope / Open Questions when those exist.
- **`agents/cast-spec-checker/cast-spec-checker.md`:** added a one-line recognition note in the
  Required-sections check marking `## Decisions` as a recognized **optional** section that MUST NOT
  be added to REQUIRED_SECTIONS.

## Verification (all green)
- Validation greps: Decisions in output template ✓, evidence-quoting mandate ✓, answer-time
  buffering ✓, template ✓, checker-doc note ✓.
- `bin/cast-spec-checker` **UNCHANGED** (git clean); `REQUIRED_SECTIONS` = the four required
  sections only; `Decisions` is NOT a required section (asserted).
- Checker exits **0** on real spec-kit specs (e.g. `docs/specs/cast-hooks.collab.md`) — the
  additive optional H2 is ignored. (Note: `_registry.md` and older non-spec-kit specs fail R1 as
  they always have — pre-existing, unrelated to this change.)
- `pytest tests/test_b1_domain_search.py` → **8 passed**. `Step 2.2.1` untouched.
- Section ordering confirmed: agent prompt = Out of Scope → Decisions → Open Questions; spec
  template = Success Criteria → Decisions → Open Questions.

## Notes for dependent sub-phases
- **sp3 (reviewer + HARD GATE):** edits the same prompt file — current line count 492/650, ~158
  lines of headroom. The Step 2.1 presentation now carries evidence quotes; the reviewer should
  run BEFORE the HARD-GATE draft presentation (Decision #2).
- **sp4 (regen + pins):** `bin/generate-skills` NOT run here (batched to sp4). New pins in
  `tests/test_phase1b_prompt_pins.py` should anchor: `## Decisions`, the `| Date | Chose | Over |
  Because |` row, "verbatim quote", "answer-time", and the 0-fork fallback line.
- Files modified (all in `/home/sridherj/workspace/diecast`):
  `agents/cast-refine-requirements/cast-refine-requirements.md`,
  `templates/cast-spec.template.md`,
  `agents/cast-spec-checker/cast-spec-checker.md`.
