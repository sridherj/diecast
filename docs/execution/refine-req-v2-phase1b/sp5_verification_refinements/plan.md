# Sub-phase 5: Verification Re-Refinements (3 real writeups)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` before starting.

## Objective

Prove the upgraded `cast-refine-requirements` behaves as designed by running it live against three
real writeups spanning the stage spectrum, then asserting all 8 of the plan's verification items.
This is the phase brief's "re-refine 2–3 real writeups" criterion expanded into specific,
checkable assertions. It is the instruction-following smoke test for the whole phase: if the
prompt edits bloated past the point of reliable instruction-following, these runs expose it.

## Dependencies
- **Requires completed:** sp1–sp4 (all behavior landed, skill regenerated, pins green).
- **Assumed codebase state:** agent prompt < 650 lines with all anchors; `test_phase1b_prompt_pins.py`
  and `test_b1_domain_search.py` passing; `bin/cast-spec-checker` unchanged.

## Scope

**In scope:**
- Pick 3 real writeups from `goals/*/requirements.human.md` across the workspaces: one <200-word
  vague idea (Stage-1 stub), one specific feature, one detailed near-complete spec.
- Run `cast-refine-requirements` on each (interactively where a fork/go-ahead is needed; one run
  should deny the Agent tool to exercise fail-soft).
- Assert the 8 verification items below; record evidence (which output file, which line) for each.
- Capture results in this sub-phase's output.

**Out of scope (do NOT do these):**
- Editing the agent prompt, template, or checker (sp1–sp3 own those). If a verification item
  fails, file it as a finding for the owning sub-phase — do not patch behavior here beyond an
  obvious typo fix, and if you do, re-run sp4's pins.
- Adding new automated tests (sp4 owns the pinning test).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| Three `refined_requirements.collab.md` outputs (in the chosen goal dirs / a scratch dir) | Create | Produced by the live runs |
| `docs/execution/refine-req-v2-phase1b/sp5_verification_refinements/results.md` | Create | Verification evidence table |

## Detailed Steps

### Step 5.1: Select 3 writeups across the stage spectrum
```bash
# Survey candidates; pick one stub (<200 words), one specific, one near-complete.
for f in $(ls goals/*/requirements.human.md 2>/dev/null); do printf '%5s  %s\n' "$(wc -w < "$f")" "$f"; done | sort -n
```
Record the three chosen paths and their word counts.

### Step 5.2: Run the agent on each writeup
Invoke `/cast-refine-requirements` per writeup. For the stub, expect the reviewer to be skipped.
For at least one run, resolve an `AskUserQuestion` fork (to exercise the Decisions table). For one
run, **deny the Agent tool call** when the reviewer dispatches, to exercise fail-soft.

### Step 5.3: Assert the 8 verification items (record evidence per item)
1. **Stage-adaptive:** the vague writeup gets JTBD framing and is NOT padded to full EARS depth;
   the near-complete one gets EARS + gap analysis.
2. **Scope mode:** each run states a detected mode with quoted signal words; ≥1 run's front-matter
   carries `scope_mode`.
3. **Decisions populated:** ≥1 run resolves a fork and its output has a dated
   `| Date | Chose | Over | Because |` row matching that answer, captured at answer-time.
4. **Reviewer is the adversarial pass:** the reviewer surfaces ≥1 real contradiction / unmeasurable
   constraint / scope-or-feasibility issue across the three runs, and each finding is visibly
   either fixed or logged to Open Questions — none silently dropped.
5. **Evidence quoting:** every confidence rating in the Step 2.1 presentations carries a verbatim
   quote.
6. **HARD GATE + ordering:** on the cleanest writeup (all sections medium+ after the draft), the
   agent still runs the reviewer, *then* presents the draft and waits before writing — the user
   sees the post-reviewer version.
7. **Reviewer runs, skips stubs, fails soft:** the reviewer returns five 1–10 scores on ≥1 run;
   on the <200-word stub it is skipped with `review skipped: stub-sized input`; on the
   tool-denied run, refinement completes with the `review skipped` note.
8. **No regressions + new pins green:** `bin/cast-spec-checker <output>` exits 0 on all three
   re-refined files AND on one pre-existing spec from `docs/specs/`;
   `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` passes;
   `bin/generate-skills --dry-run` lists the agent without error.

### Step 5.4: Record results
Write `results.md` with a table: item # | pass/fail | evidence (output file + line / observed
behavior). For any fail, name the owning sub-phase (sp1–sp4) and the specific gap.

## Verification

### Automated Tests (permanent)
- Re-run the suite as item 8: `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q`.

### Validation Scripts (temporary)
```bash
# Checker exits 0 on every re-refined output + one pre-existing spec.
for out in <the three output paths>; do bin/cast-spec-checker "$out" && echo "OK $out"; done
SPEC=$(ls docs/specs/*.md | head -1); bin/cast-spec-checker "$SPEC" && echo "OK pre-existing $SPEC"
pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q
bin/generate-skills --dry-run >/dev/null && echo "dry-run OK"
```

### Manual Checks
- Read each output's `## Decisions` section: the ≥1 fork-resolving run has a real dated row whose
  Chose/Over/Because match the answer given (not reconstructed).
- Confirm the stub run's transcript shows `review skipped: stub-sized input`.
- Confirm the tool-denied run completed and noted `independent review skipped: <reason>`.

### Success Criteria
- [ ] 3 writeups chosen across stages (one <200-word stub), paths + word counts recorded.
- [ ] All 8 verification items pass, each with recorded evidence in `results.md`.
- [ ] `bin/cast-spec-checker` exits 0 on all three outputs + one pre-existing spec.
- [ ] `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` passes.
- [ ] `bin/generate-skills --dry-run` lists the agent without error.
- [ ] Any failure is attributed to its owning sub-phase in `results.md`.

## Execution Notes
- → Delegate: the reviewer subagent in item 4/7 is itself a `/cast-refine-requirements` behavior —
  you are exercising it, not re-implementing it. To deny the Agent tool for the fail-soft test,
  decline the tool call when it dispatches.
- These are live LLM runs — expect minor wording variance. Assert on **structure** (a quote is
  present, a dated row exists, the mode is stated), not exact strings.
- If item 8's checker fails on an output, the output itself is malformed — re-read which section
  the checker flags; the fix is usually a missing Open Questions entry (zero-silent-failure, sp1)
  or a malformed Decisions table (sp2).
- **Spec-linked files:** the re-refined outputs are checked against
  `templates/cast-spec.template.md` via `bin/cast-spec-checker` (item 8) — that IS the SAV check.
