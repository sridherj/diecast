# Review Summary: refine-req-v3-phase4b

Review scope: **SMALL CHANGE** (max ~1 issue per section), run as a focused self-review by the
execution-plan author. The **source plan** (`2026-06-12-refine-requirements-v3-phase4b-comment-survival.md`)
already passed a BIG-CHANGE `cast-plan-review` (8 issues / 8 resolved — see its appendix), so this
pass targets only **split-introduced** risks (seam mechanics, the override re-shaping, cross-sub-phase
contracts) rather than re-reviewing the design.

## Open Questions — BOTH RESOLVED (owner-approved 2026-06-12; recommendations baked into the plans)

1. **[4b-2] `block_ref` derivation at the dispatch site — is there a helper, or does it need one?**
   **RESOLVED:** add a tiny pure quote→`block_ref` helper (`parse_requirements` + per-block
   `strip_inline_markdown` substring test, reusing 4b-1's stripper); `block_ref` stays optional and is
   **omitted, never guessed,** for cross-boundary quotes. Baked into sp4b2 §4b2.3 + Success Criteria
   + the shared-context contract comment.
   The contract-v2 input gives each displaced comment a `block_ref` "derived deterministically by the
   parent from the parsed old version." Mapping a comment's `quoted_text` → the `Block.ref` whose old
   body contained it is a small new bit of logic at the `cast-refine-requirements` dispatch site.
   `comment_service` displacement is a whole-document string-find (not block-resolved), so there may
   be **no existing quote→block_ref helper**. *Recommendation:* add a tiny pure helper (e.g. reuse
   `parse_requirements` + per-block `strip_inline_markdown` substring test — the same maps 4b-1
   builds) at the dispatch site, OR mark `block_ref` truly optional and let the agent reason from
   `old_content` when it's absent. Either is valid; flagging so the 4b-2 executor doesn't assume a
   helper exists. **Non-blocking** — `block_ref` is an optional input by contract.

2. **[4b-3] The narration POST needs an actor — confirm it rides the request body.**
   **RESOLVED:** `created_by` rides the POST body `{base, overview, item_notes, created_by}` (alias
   `actor` accepted), matching the resolve/relocate convention; the server stamps the row from it.
   Baked into sp4b3 §4b3.3 + Success Criteria + the shared-context contract.

## Review Notes by Sub-Phase

### 4b-1 (survival gate + tray badge)
- **Architecture:** the OVERRIDE re-shaping is the load-bearing change — verified the existing
  `_execute_pipeline` retry (line 592) + `publish()` best-attempt+flag path (line 497) absorb a
  merged-in survival violation with **no new branch**. `state.parsed` (used by `check_html` at line
  493) is available to `check_comment_survival` at the same seam. ✓
- **Code Quality:** `comment_service.list_comments` accepts `state=`, `db_path=`, `goals_dir=`
  (confirmed line 125–128) — the fetch signature in §4b1.2 is valid. The frozen `GateReport`/
  `SurvivalReport` must be re-constructed on merge, not mutated (noted in §4b1.2). ✓
- **Tests:** the override flips the old "survival blocks publish" test into a "flagged-serve" test —
  captured explicitly in Verification so the executor doesn't copy the stale source-plan assertion. ✓
- **Performance:** single-walk + once-per-pass strip (P1) is specified. ✓

### 4b-2 (reanchor contract v2)
- **Architecture:** extend-in-place; safety machinery carried untouched; new inputs optional. ✓
- **Code Quality:** see Open Question 1 (`block_ref` derivation). The `resolved` state-machine guard
  (Decision #11) is specified. ✓
- **Tests:** eval gate extended with legacy + narration + adversarial + moved-reworded + markdown-seam
  + over-eager-resolve fixtures. ✓
- **Coupling:** narration POST depends on 4b-3's endpoint — flagged in Execution Notes (guard the POST
  / land the wiring after 4b-3 so the eval gate runs independently). ✓

### 4b-3 (narration store / API / render)
- **Architecture:** server recomputes the diff (never trusts the poster) + attachment-only render =
  three-layer "never invent a change" guarantee. ✓
- **Code Quality:** see Open Question 2 (actor in the POST body).
- **Security:** autoescaped fragments only; size caps; JSON-only behind slug validation. ✓
- **Tests:** byte-identical `counts`/`items` assertion (with + without narration); all-or-nothing 422;
  FR-007 read-only + block-diff/diff-render regression sweeps stay green. ✓

### 4b-4 (spec + SC-003 e2e gate)
- **Spec consistency:** all 4b-1/2/3 flags resolve in one `/cast-update-spec`; DOM contract asserted
  unchanged; survival wording made **override-aware** (surfaced, not blocking) — the single most
  important correction vs. the source-plan body. ✓
- **Process:** clause texts fixed up front; the hand-off note carries the override-era
  `render_job_service` merge contract for the 4a/4b second-lander. ✓

## Verdict

**4 sub-phases / 2 open questions (both RESOLVED + baked in) / 0 blocking.** The split is faithful to
the source plan and correctly applies the four owner-resolved edits (override, C2, C3, extend-in-place
+ tier). Ready for execution.
