# Live Verification Runbook — completes the [NEEDS-LIVE] SCs + parity numbers

**Who runs this:** the **main agent** (has the Workflow tool) or the user. A subagent cannot — the
Workflow tool is main-agent-only and the hat cells need live WebSearch. Do NOT fabricate; run it.

**Goal pick (the one un-self-resolvable input):** recommendation per the plan — pick the **smallest
existing exploration-phase goal with a realistic 3–5 step decomposition** so N×M cost stays bounded
and the SC-001 matrix stays legible. Avoid a toy. (This goal itself is a candidate; confirm 3–5 steps.)
[[feedback_ask_with_recommendation]]

---

## R0 — Two runs, collision-safe (Activity A)

**Strategy (i), preferred — disjoint goal dirs (runs may go in parallel):**
```
# Run 1 (N×M): drive the Phase-3a entrypoint skill end-to-end on GOAL_SLUG.
#   intent → decompose → APPROVE steps → compute hat-matrix → launch the Workflow UNATTENDED.
#   Use the cast-explore-workflow entrypoint (agents/cast-explore-workflow/cast-explore-workflow.md).
#   PERSIST the emitted hat-matrix JSON to phase5/hat-matrix.run1.json  ← ground truth for SC-001.
#   Record wall-clock start/end; retain the FULL exploration/ tree + exploration.html.

# Run 2 (baseline): dispatch the cast-explore agent on a sibling goal:
#   GOAL_SLUG-baseline  (so cast-explore's hardcoded <output-dir>/exploration/ does not collide).
```
**Strategy (ii) fallback — sequence + snapshot** (if a sibling goal is undesirable):
```
# run cast-explore FIRST on GOAL_SLUG, then:
cp -r goals/GOAL_SLUG/exploration goals/GOAL_SLUG/exploration-baseline-snapshot
# THEN run the N×M pipeline (overwrites exploration/). Snapshot = durable Run-2 evidence.
```
**Verify both trees are side-by-side and intact BEFORE any read below.**

---

## R1 — SC-001 (exact-filename-SET, not count)
```
cd goals/GOAL_SLUG
# expected set from the persisted matrix MINUS FR-016 nulls (read the Workflow log for dropped cells):
#   expected = {NN-slug-hat_id for each applicable cell in phase5/hat-matrix.run1.json, minus null cells}
# actual set (EXCLUDE cast-code-explorer -code.ai.md — they share the NN-slug- prefix):
ls exploration/research/*.ai.md | grep -v -- '-code.ai.md' | sed 's#.*/##;s#\.ai\.md$##' | sort > /tmp/actual.txt
# Build /tmp/expected.txt from the matrix (NN-slug-hat_id per applicable, non-null cell), sort it.
diff /tmp/expected.txt /tmp/actual.txt   # EMPTY = PASS
```
Record: expected-set, actual-set, the set-diff (empty on PASS), per-step breakdown, and any logged
null cells (subtracted, never read as FAIL). A count match that hides a mis-slug is the failure this
catches — assert the **set**, not `wc -l`. **FAIL → route to Phase 3a (gating/glob), not a Phase-5 fix.**

## R3 — SC-003 (90/10 present every step; first-principles has NO 80/20)
```
cd goals/GOAL_SLUG/exploration/research
ls *-90-10.ai.md | wc -l                          # == N (one 90/10 note per step)
grep -iE '80/20|pareto|20% of (the )?effort|laziest|mvp' *-first-principles.ai.md   # must be EMPTY
# quote one 90/10 verdict line to confirm note-shape:
grep -hE 'RECOMMENDED CUT|CUT WITH CAUTION|DO NOT CUT' *-90-10.ai.md | head -1
```

## R4 — SC-004 (one playbook per step)
```
ls goals/GOAL_SLUG/exploration/playbooks/*.ai.md | wc -l   # == N
# confirm 1:1 step↔playbook slug mapping (each NN-slug present exactly once)
```

## R5 — SC-005 (render-checker 4 criteria)
```
# Read/run the cast-exploration-render-checker verdict for the real exploration.html.
# Phase-4 service runs it in the quality loop; capture the bare-JSON verdict.
# Assert: criteria hats=pass, pov=pass, distinctness=pass, visual=pass (derive_pass requires all 4).
```
Record the bare-JSON verdict. **FAIL → route to Phase 4.**

## R6 / R7 / R8 — SC-006 / SC-007 / SC-008 (UI, with the running cast-server)
Open the goal's exploration phase tab in the standing cast-server UI.
- **R6 (SC-006):** confirm `exploration.html` renders in the `<iframe srcdoc kind="html">` AND the
  `.md` artifacts list beside it.
- **R7 (SC-007):** select text inside `exploration.html` → "+ Comment" → type → Submit. Confirm a
  comment row persists with `artifact_ref="exploration/exploration.html"`, `anchor_space='render'`,
  `{quoted_text, section_hint, body}`. **Assert PERSISTENCE only — write-back to the md is Out of
  Scope; do NOT over-test a roundtrip.** Verify the row:
  ```
  # comments DB (see connection.py): SELECT artifact_ref, anchor_space, quoted_text FROM comments
  #   WHERE goal_slug=GOAL_SLUG ORDER BY created_at DESC LIMIT 1;
  ```
- **R8 (SC-008):** confirm the existing `refined_requirements.html` for this goal also surfaces in the
  dual viewer (not only on `/render`).

If the run is autonomous and cannot drive Chrome: the **server-side structural verdict already
recorded in `sc-verification.md` stands** (degraded gate, machine-flagged) — this UI pass is the
**human-eyeball carry-forward**, never a silent pass, never a hard block.
[[project_diecast_prototype_no_browser_visual_gates]] [[feedback_surface_dont_suppress]]

## R9 — SC-009 (no manual intervention after approval)
During Run 1, after step approval: record the run timeline; assert **zero** AskUserQuestion/human-gate
events emitted by the Workflow or children, **zero** manual goal-dir edits; capture the terminal
`.agent-run_*.output.json` with `status==completed`; write an explicit line
**"human-input events after approval: 0"**. If it paused for ANY input → **FAIL routed to Phase 3a**
(the Workflow must be non-interactive per US2/Constraints), not a Phase-5 note.

## R-C — Byte-compat instance confirmation (Activity C, optional-but-cheap)
```
# 1) all three globs resolve non-empty over Run 1:
ls goals/GOAL_SLUG/exploration/research/*.ai.md   | head
ls goals/GOAL_SLUG/exploration/playbooks/*.ai.md  | head
ls goals/GOAL_SLUG/exploration/summary.ai.md
# 2) dispatch cast-high-level-planner (read-only intent) on the Run-1 goal dir.
#    Confirm it produces plan.collab.md WITHOUT a missing-artifact error AND that the plan
#    REFERENCES exploration content (cite >=1 playbook impact rating or M-per-step research insight).
#    A thin plan that never references the fan-out = the silent "ingested-but-ignored" regression
#    (Phase-3a defect if the playbook/summary SHAPE regressed). Diff playbook/summary HEADINGS
#    (not content) between Run 1 and Run 2 to confirm same shape.
```

## R-D — Fill the parity numbers (Activity D)
Fill the four axes in `parity-notes.md` against the **pre-committed win conditions** already written
there: Axis 1 playbook quality (≥2 steps), Axis 2 angle sharpness (2–3 before/after quotes on
contrarian + first-principles + the 90/10 cut), Axis 3 cost/time (wall-clock + live-cell-count vs
`N×M_total` + token cost if available), Axis 4 recommended disposition (advisory; parallel stands).

## R-E — Wrap-up (Activity E)
Dispatch `/cast-wrap-up` for session learnings + spec drift; append the Round-5 ledger summary to
`docs/plan/exploration-pipeline-nxm-decisions-so-far.md` (file paths + SC-matrix shape + parity
method + artifacts produced).
