## Phase 1b: Refinement Brain Upgrades (gbrain imports) — parallel with Phase 1
**Outcome:** `cast-refine-requirements` produces sharper drafts via portable upgrades from
second-brain's `taskos-refine-requirements`, independent of the render/comments/versioning build.
**Dependencies:** None (pure agent-prompt edits; run concurrently with Phase 1).
**Estimated effort:** 1 session (~1 day of prompt edits)
**Verification:** Re-refine 2-3 real writeups (one vague, one near-complete) and confirm the
stage-adaptive behavior, a populated Decisions section, and that the adversarial meta-pass surfaces at
least one real contradiction; no regression in the existing spec-checker pass.

Key activities:
- Import the **stage-adaptive framework** (vague → JTBD; specific → Example-Mapping; near-complete →
  EARS) — this *is* the Template-Enforcer guard the spec fears, applied at the authoring layer.
- Add **explicit exit conditions** + log gaps into Open Questions when budget exhausts (no silent
  low-confidence sections).
- Add a dated **Decisions section** (Chose / Over / Because) — pairs naturally with Phase 4 versioning.
- Add the **adversarial meta-pass** ("what would an engineer reject?") and the **evidence-quoting
  mandate** for confidence scores (cite draft text).
- Add **scope-mode detection** from signal words (MVP / comprehensive / dream).
- Optionally port the gstack `/spec` HARD GATE ("no output before Phase 1") and an `/office-hours`-style
  adversarial reviewer subagent (Diecast child-delegation makes this trivial).

