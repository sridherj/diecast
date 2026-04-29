# Test Cases: cast-preso-orchestrator

## TC-1: Cold Start
- Input: presentation/ directory with only narrative.collab.md
- Expected: Initializes state.json (version: 2), extracts slide list, enters
  STAGE2_PLANNING, dispatches cast-preso-what-planner (single child)
- Verify: state.json has stage2.planner.status = "running" with a run_id;
  no stage2.phases entries yet (planner hasn't run)

## TC-1b: Planner Completion → Fanout
- Setup: Planner has written _slide_list.md (8 slides) and 8 stub files
- Expected: Orchestrator reads manifest, populates state.json stage2.slides with
  8 entries (all pending), dispatches 8 cast-preso-what-worker children in parallel
- Verify: All 8 workers have distinct run_ids in state.json; stage2.status = "in_progress"

## TC-2: Resume After Session Drop (Stage 2 in progress)
- Setup: state.json (v2) with stage2, planner completed, 3/8 slides approved,
  2 checking, 3 pending
- Expected: Dispatches workers for the 3 pending slides only; waits on the 2 in-flight
  checkers; does not re-run the planner
- Verify: Approved slides not re-dispatched; new run_ids only for the 3 pending
  slides; planner not re-invoked

## TC-3: Resume After Session Drop (Stage 3 in progress)
- Setup: state.json with stage3, 6/8 slides passed, 2 still making
- Expected: Checks if in-flight children are still running, waits or re-dispatches
- Verify: Passed slides not re-checked, in-flight children handled correctly
- Verify: if a child completes between status check and next poll iteration,
  the orchestrator detects the output file on the next loop and does NOT re-dispatch

## TC-4: Rework Loop (Stage 3)
- Setup: Deliberately create a slide that fails tone check
- Expected: Orchestrator re-dispatches HOW maker with feedback, re-checks
- Verify: rework_count incremented, feedback passed to maker, max 3 iterations

## TC-5: Escalation (Max Reworks)
- Setup: Slide that fails checking 3 times
- Expected: Orchestrator presents escalation to the user via interactive questions
- Verify: the user gets clear options (accept/guide/simplify/skip), decision recorded in state.json

## TC-6: Cross-Slide Consistency
- Setup: All slides passed per-slide checks but with deliberate style drift
- Expected: Cross-slide check flags drift, targeted rework dispatched
- Verify: Only drifting slides re-worked, others untouched

## TC-7: G2 Gate
- Setup: All Stage 2 slides approved
- Expected: Orchestrator presents summary via interactive questions
- Verify: the user can approve all, flag specific slides, or reject

## TC-8: G3b Open Questions
- Setup: 3 blocking + 2 nice-to-have open questions
- Expected: Orchestrator walks the user through blocking questions one at a time
- Verify: Each question presented individually, resolutions recorded

## TC-9: G4 Final Approval
- Setup: Assembly + compliance check passed
- Expected: Orchestrator presents final summary for approval
- Verify: Approval recorded, current_stage set to "complete"

## TC-10: State Reconstruction
- Setup: Delete or corrupt state.json after partial progress
- Expected: Orchestrator reconstructs from disk artifacts
- Verify: Conservative reconstruction, presented to the user for confirmation

## TC-11: G3a Gate Rejection + Selective Rework
- Setup: All Stage 3 slides passed, cross-slide passed. At G3a, the user flags
  slides 02-problem and 05-evidence for revision with specific feedback.
- Expected: Only those 2 slides go through rework. Cross-slide re-runs after
  fixes. G3a re-presented. Other slides untouched.
- Verify: rework_count incremented for flagged slides only. the user's feedback
  passed to HOW maker. Cross-slide check runs again.

## TC-12: G3b Auto-Skip (No Blocking Questions)
- Setup: All slides passed, cross-slide passed. Open questions exist but all
  are nice-to-have (zero blocking).
- Expected: G3b auto-approved. Nice-to-have questions presented in batch summary.
  Stage advances to 4.
- Verify: gates.G3b.status = "skipped", no individual question prompts.

## TC-13: Resume Between Planner and Workers
- Setup: Planner wrote _slide_list.md + stubs, then session dropped before any
  worker was dispatched. state.json has stage2.planner.status = "completed" but
  stage2.slides is populated from the manifest with all slides pending.
- Expected: On resume, orchestrator does NOT re-run the planner; it dispatches
  workers for all pending slides in parallel.
- Verify: No new planner run_id; N worker run_ids created (N = slide count).

## TC-14: G2 Flag Triggers Worker-Only Rework
- Setup: All 8 slides approved by checker. At G2, the user flags 2 slides with
  feedback "outcome too abstract — add a proof point".
- Expected: Only those 2 slides reset to pending (worker re-dispatched with
  rework mode + feedback). Planner not re-invoked. Other slides untouched.
  After rework + re-check pass, G2 re-presented.
- Verify: rework_count incremented for flagged slides only; planner.status unchanged.

## TC-15: G2 Reject Triggers Planner Re-Run
- Setup: At G2, the user chooses Option C (Reject and redo Stage 2).
- Expected: state.json stage2.planner.status reset to "pending", stage2.slides
  cleared. Orchestrator re-enters STAGE2_PLANNING in rework mode.
- Verify: Fresh planner run_id; no slide entries left over from prior attempt.

## TC-16: v1 state.json Detected
- Setup: state.json exists with version: 1 (pre-split schema, per-slide Stage 2).
- Expected: Orchestrator treats as corrupt, falls back to reconstruction from
  disk artifacts (§12.5), presents reconstruction summary to the user before proceeding.
- Verify: New state.json written with version: 2; the user prompted to confirm before
  any dispatch.
