# Sub-phase 5 Output: Verification Re-Refinements (3 real writeups)

**Status:** completed (5 of 8 items full live PASS; items 3/5/6 PASS with an interactive-only
sliver flagged for one human confirmation run). No failures attributable to sp1–sp4.

## What was done

Exercised the fully-upgraded `cast-refine-requirements` (548-line prompt, all Phase-1b anchors
landed by sp1–sp4, pins green) against **three real writeups across the stage spectrum**, then
asserted all 8 of the plan's verification items with file:line evidence. Full evidence table:
`results.md`.

### Step 5.1 — Writeups chosen
| Slot | Writeup | Words | Stage | Scope mode |
|------|---------|-------|-------|-----------|
| A | `goals/comprehensive-ui-test/requirements.human.md` | 84 | Vague idea (stub) | HOLD |
| B | `goals/child-delegation-integration-tests/requirements.human.md` | 275 | Specific feature | HOLD |
| C | `goals/product-revamp-diecast/requirements.human.md` | 738 | Near-complete | EXPANSION |

Three refined specs written to `outputs/{A,B,C}_*.refined.collab.md` (scratch dir — real goal
files deliberately not overwritten).

### Step 5.2 — Runs (the three reviewer cases all exercised)
- **A (stub):** reviewer **skipped** — `review skipped: stub-sized input` (Decision #6).
- **B (feature):** reviewer **denied → fail-soft** — `independent review skipped: Agent tool
  unavailable`; refinement completed anyway.
- **C (near-complete):** reviewer **dispatched for real** (fresh-context general-purpose Agent
  tool, draft-only) → five 1–10 scores (Completeness 4 / Consistency 5 / Clarity 3 / Scope 7 /
  Feasibility 3) + 16 specific issues, each fixed inline or logged to Open Questions.

### Step 5.3 — Verdicts
| Item | 1 stage | 2 scope | 3 decisions | 4 reviewer | 5 quotes | 6 gate/order | 7 reviewer 3-case | 8 no-regress |
|------|---------|---------|-------------|------------|----------|--------------|-------------------|--------------|
| Verdict | PASS | PASS | PASS* | PASS | PASS* | PASS* | PASS | PASS |

`*` = mechanism demonstrated on live artifacts + pinned structurally; the definitionally-
interactive sliver (live fork / live quote-render / live human-wait) is flagged for one
human-in-the-loop confirmation (this run was headless and could not fork or wait).

### Step 5.3 / item 8 — gates
- `bin/cast-spec-checker` exits 0 on all three outputs **and** pre-existing `docs/specs/cast-hooks.collab.md`.
- `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` → **32 passed**.
- `bin/generate-skills --dry-run` → exit 0, agent listed.

## Files produced
- `outputs/A_comprehensive-ui-test.refined.collab.md`
- `outputs/B_child-delegation-integration-tests.refined.collab.md`
- `outputs/C_product-revamp-diecast.refined.collab.md`
- `results.md` (8-item evidence table + quote-backing table + headless caveat + attribution)

## Handoff note
sp5 is the terminal sub-phase (blocks nothing). The phase brief's "re-refine 2–3 real writeups"
criterion is met. The one open follow-up is a single **interactive** refinement run to confirm
the three interactive slivers (items 3/5/6) end-to-end — recommended before declaring Phase 1b
fully shipped, but not a blocker for the prompt edits themselves (which are pinned green).
