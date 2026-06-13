# Decision Gate G1: Combined Phase-1 Spike Gate → Phase 3 Entry Condition

> **Context:** Read the output of **both** sub-phases before making this decision:
> - `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md`
> - `docs/goal/refine-requirements-better-rendering-v3/spikes/1b/spike-results.md`
>
> This is a **human decision gate** — the orchestrator stops here. It is **not** an executable
> sub-phase. It aggregates the two spike verdicts into one owning artifact
> (`spikes/PHASE1-GATE.md`) and makes the single **go-to-Phase-3 / surface-to-owner** call, so a
> reader never has to reconcile two separate results files.

## Decision Criteria

Evaluate both spike results together. Both gates must be **green** — or their revisit-triggers
**consciously accepted by the owner** — before Phase 3 (the WHAT→HOW maker pipeline) starts.

**From sp1a (`spike-results.md`):**
- `BEATS DETERMINISTIC: yes` for **≥2 families**, where "clearly beats" =
  `cast-requirements-checker` passes the maker render with restatements **at least as complete**
  as the baseline's, **AND** the structured rubric favors the maker on a **majority** of
  dimensions, **AND** no gate regression (ids verbatim + per-block correct, self-contained, DOM
  contract) — **plus** the human-eyeball carry-forward noted.
- id-audit: set-equality **and** per-block correspondence both pass.
- Self-containment + zero-`id` audits pass.

**From sp1b (`spike-results.md`):**
- `BACKBONE HOLDS: confirmed` — **zero new orphans** for surviving content; only the
  genuinely-deleted block orphaned; 100% mark placement for untouched + relocated comments
  (scoped to the intended container); `displaced_comment_ids` exact; `diff_blocks` partition
  invariant holds; zero-`id` audit passes on both HTML files.
- The `section_hint`-mismatch probe outcome is **recorded** (either acceptable result is fine as
  long as it is measured and noted as a Phase-3 input).

## Options

### Option A: Both gates green → proceed to Phase 3
- **Condition:** sp1a `BEATS DETERMINISTIC: yes` (≥2 families, no gate regression) **AND** sp1b
  `BACKBONE HOLDS: confirmed`.
- **Action:** Write `spikes/PHASE1-GATE.md` recording `1a: BEATS DETERMINISTIC yes`,
  `1b: BACKBONE HOLDS`, and the combined **GO-TO-PHASE-3** decision. Mark G1 "Done" in the
  manifest with the decision in Notes. Phase 3 may begin.
- **Rationale:** the maker ceiling is reachable by hand and the quote-anchored backbone survives
  a varying render — Phase 3's net-new agents have a validated target and the anchor approach
  needs no new machinery.

### Option B: A revisit-trigger fired → surface to owner (do NOT silently re-scope)
- **Condition:** sp1a cannot clear the bar even by hand (maker-vs-hybrid fork) **OR** sp1b fires
  `REVISIT-TRIGGER: quote anchoring insufficient under heavy rewording`.
- **Action:** Write `spikes/PHASE1-GATE.md` recording the exact failing verdict(s) and the
  attached failing cases, and **surface the fork to the owner** — the maker-vs-hybrid fork (1a)
  and/or the id-in-DOM fork (1b). Mark G1 "Done" only once the owner has consciously accepted the
  revisit-trigger or chosen a re-scope. **Phase 3 does not start until the owner rules.**
- **Rationale:** HOLD SCOPE is binding; a failed spike surfaces the decision to the owner —
  never a silent re-decision of the anchor backbone or a silent re-scope of the maker approach.

### Option C: One green, one triggered
- **Condition:** exactly one spike passes; the other fires its revisit-trigger.
- **Action:** Write `spikes/PHASE1-GATE.md` with both verdicts. The green spike's downstream is
  unblocked **only** to the extent it is independent (1b's backbone validation also gates Phase
  4b); the triggered spike's fork goes to the owner before any dependent Phase-3 work starts.
  Mark G1 "Done" once the owner rules on the triggered fork.
- **Rationale:** the two spikes gate partially-disjoint downstream work; do not block the green
  result's independent value, but do not let the triggered fork pass silently either.

## How to Proceed

1. Review `spikes/1a/spike-results.md` and `spikes/1b/spike-results.md` against the criteria above.
2. Write the aggregate artifact
   `docs/goal/refine-requirements-better-rendering-v3/spikes/PHASE1-GATE.md` recording:
   `1a: BEATS DETERMINISTIC yes/no`, `1b: BACKBONE HOLDS / REVISIT-TRIGGER`, and the combined
   **go-to-Phase-3 / surface-to-owner** decision.
3. Update `_manifest.md`: set G1 status to "Done", add the chosen option + the PHASE1-GATE
   decision to Notes.
4. If a revisit-trigger fired, **pause for the owner** — do not advance to Phase 3 planning until
   the owner consciously accepts the trigger or re-scopes.
5. On GO: Phase 3 begins in a fresh planning/execution context, carrying forward the recorded
   inputs (the "clearly beats" rubric, the mark-placement harness semantics, the
   `section_hint`-probe outcome, and the verbatim-carriage carry-forward for the Phase 3
   `/cast-update-spec` activity).
