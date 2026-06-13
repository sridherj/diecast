# Sub-phase 5 Results: Live Verification of the Upgraded `cast-refine-requirements`

**Run mode:** headless / HTTP-delegated (cast-subphase-runner) — autonomous, no human at the
keyboard. This shapes how the three interactive-only items (3, 5, 6) were verified; see the
caveat column and the "Headless caveat" section below.

## Step 5.1 — Three writeups chosen across the stage spectrum

| Slot | Writeup | Words | Stage detected | Scope mode |
|------|---------|-------|----------------|------------|
| A (stub) | `goals/comprehensive-ui-test/requirements.human.md` | 84 | Vague idea (Stage 1) | HOLD |
| B (feature) | `goals/child-delegation-integration-tests/requirements.human.md` | 275 | Specific feature | HOLD |
| C (near-complete) | `goals/product-revamp-diecast/requirements.human.md` | 738 | Near-complete / detailed-with-gaps | EXPANSION |

Outputs written to `outputs/{A,B,C}_*.refined.collab.md` in this sub-phase dir (scratch — the
real goal `refined_requirements.collab.md` files were intentionally NOT overwritten).

## Step 5.3 — The 8 verification items

| # | Item | Verdict | Evidence (file:line / observed) |
|---|------|---------|----------------------------------|
| 1 | Stage-adaptive (vague→JTBD not padded; near-complete→EARS+gap) | **PASS** | A:20 "VAGUE IDEA … deliberately NOT padded to full EARS"; A has 2 thin user stories + 5 Open Questions (not padded). C:20 "NEAR-COMPLETE … EARS refinement + gap analysis"; C has 4 EARS user stories + FR/SC tables + 12 Open Questions (gap analysis). |
| 2 | Scope mode stated w/ quoted signals; ≥1 front-matter `scope_mode` | **PASS** | Front-matter `scope_mode:` on all three (A:3 hold, B:3 hold, C:3 **expansion** — non-default). A:25 "HOLD SCOPE — no scope signals detected"; C:24 "SCOPE EXPANSION — quoted signal evidence: \"don't be constrained with what we have so far\" …". |
| 3 | Decisions populated w/ dated `\| Date \| Chose \| Over \| Because \|` row | **PASS** (live-fork sliver flagged) | B:133–135 — three dated `2026-05-01` rows whose Chose/Over/Because transcribe the writeup's verbatim Q1/Q2/Q3 answers (a *documented* human fork, not reconstructed from memory). C:172–173 — two dated `2026-06-11` rows from the writeup's recorded refinement additions. A:111 correctly emits `*No decisions recorded this refinement.*` (0-fork run). **Caveat:** a live in-session `AskUserQuestion` fork → answer-time-buffered row cannot occur headless; that path is pinned in the prompt (Step 3.1 answer-time buffering) and flagged for interactive confirmation. |
| 4 | Reviewer is the sole adversarial pass; ≥1 real issue; each fixed or logged | **PASS** | Real fresh-context reviewer dispatched on C (general-purpose Agent tool, draft-only) returned scores Completeness 4 / Consistency 5 / Clarity 3 / Scope 7 / Feasibility 3 with **16 specific issues** — incl. a real contradiction ("FR-001 asserts auto-detection as settled while detection is an Open Question") and unmeasurable-constraint findings. Disposition (C:30–42): consistency/clarity fixes inline (HOW≡execution C:82; FR softened C:129; Constraints marked directional C:148; SC-005 added C:144); 6 remaining findings logged as new `[NEEDS CLARIFICATION]` in Open Questions (C:193–203). None silently dropped. |
| 5 | Every medium/high confidence rating is quote-backable | **PASS** (live Step-2.1 render flagged) | Each medium/high section rating maps to a verbatim writeup quote (table below). Low ratings correspond to *unquotable* sections — exactly the mandate's drop-to-low fallback (C `constraints: low` ← no quantified constraint quote in the writeup; A `behavior: low` ← vague stub). **Caveat:** the literal Step 2.1 *inline* rendering of each quote is a conversational behavior; headless has no presentation turn — verified structurally (prompt Step 1.5/2.1, pinned by sp4) + demonstrated in-artifact. |
| 6 | HARD GATE + ordering (reviewer → present → wait; user sees persisted version) | **PASS** (interactive wait flagged) | Ordering is correct & pinned: prompt Step 2.5 (reviewer) → Step 3.0 (gate) → Step 3.1 (write). C concretely demonstrates Decision #2: the reviewer ran on C's draft, findings were folded in, and only the **post-reviewer** version was persisted (C:30–42). Headless correctly auto-persists (C:43 / B:32 "Auto-persisted: non-interactive run", Decision #1). **Caveat:** the live human *wait* at the gate requires an interactive run — flagged. |
| 7 | Reviewer returns 5 scores / skips stub / fails soft | **PASS** | Scores: C reviewer returned five 1–10 dims (4/5/3/7/3). Stub-skip: A:30 "review skipped: stub-sized input" (Decision #6). Fail-soft: B:28 "independent review skipped: Agent tool unavailable (reviewer dispatch denied)" — B's refinement completed fully despite the denied reviewer. |
| 8 | No regressions + new pins green | **PASS** | `bin/cast-spec-checker` exits 0 on all three outputs AND on pre-existing `docs/specs/cast-hooks.collab.md`. `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` → **32 passed**. `bin/generate-skills --dry-run` → exit 0, agent listed. |

### Item 5 — quote backing for every medium/high rating

| Output | Section | Rating | Verbatim quote licensing the rating |
|--------|---------|--------|--------------------------------------|
| A | intent | medium | "create a solid plan to test the UI for http://127.0.0.1:8000/ across all screens" + "I should be able to run this anytime!" |
| A | behavior / constraints / out_of_scope | low | (no quotable detail in the 84-word stub → correctly low) |
| B | intent | high | "it was very useful to confirm this important feature worked. Right now I feel its breaking in quite a few ways" |
| B | behavior | medium | Q4: "Allowlist/depth/output-JSON violations get through silently; … orphan .delegation/.prompt/.tmp; 422 shape …" |
| B | constraints | medium | "adapted to diecast's file-canonical contract"; "T1 mocked + T2 live HTTP E2E + manual subagent checklist" |
| B | out_of_scope | high | "without copying contract details that have changed"; "primitive-level tests (not feature-level)" |
| C | intent | high | "Create a mock up version of Diecast that will represent my vision"; "Grill me on this" |
| C | behavior | medium | "things may be very diff for requirements for a bug fix vs user facing feature" |
| C | constraints | low | (no quantified constraint in the writeup → correctly dropped to low — the mandate's unquotable→low path in action) |
| C | out_of_scope | medium | "Agent assessments, hiring is also an interesting aspect"; "advertise their usage/credibility (apify like)" |

## Verification commands (re-runnable)

```
bin/cast-spec-checker outputs/A_comprehensive-ui-test.refined.collab.md        # exit 0
bin/cast-spec-checker outputs/B_child-delegation-integration-tests.refined.collab.md  # exit 0
bin/cast-spec-checker outputs/C_product-revamp-diecast.refined.collab.md        # exit 0
bin/cast-spec-checker docs/specs/cast-hooks.collab.md                           # exit 0 (pre-existing)
uv run pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q   # 32 passed
bin/generate-skills --dry-run                                                   # exit 0, agent listed
```

## Headless caveat (why items 3, 5, 6 carry a flag, not a fail)

This sub-phase ran under a `PROCEED FULLY AUTONOMOUSLY — do NOT ask the user questions`
delegation, which forbids the `AskUserQuestion` forks and the human go-ahead that the plan's
Step 5.2 assumed ("interactively where a fork/go-ahead is needed"). Items 1, 2, 4, 7, 8 are
fully observable headless and PASS on live evidence. Items 3, 5, 6 each have a sliver that is
*definitionally* interactive:

- **3** — a live in-session fork → answer-time-buffered Decisions row (demonstrated instead via
  real dated rows transcribed from documented prior human Q&A; the buffering path is pinned).
- **5** — the Step 2.1 *inline* rendering of per-rating quotes (demonstrated instead by showing
  every medium/high rating is quote-backable and every low rating is unquotable).
- **6** — the human *wait* at the HARD GATE (ordering + Decision-#2 post-reviewer-persist
  demonstrated on C; only the literal pause needs a human).

These three slivers are verified structurally — the mechanisms exist in the prompt and are
pinned green by `tests/test_phase1b_prompt_pins.py` (sp4) — and are flagged for one
human-in-the-loop confirmation run (see output contract `human_action_items`).

## Failure attribution

**No failures.** No verification item is attributable to a gap in sp1–sp4 — every Phase-1b
behavior (stage table, scope-mode table, evidence-quoting mandate, zero-silent-failure
invariant, reviewer rubric + stub-skip + fail-soft, HARD GATE + headless auto-persist,
Decisions table) is present, correctly wired, and demonstrated on live outputs. The only
un-exercised behaviors are the three interactive slivers above, which are blocked by the
headless run mode, not by any sub-phase defect.
