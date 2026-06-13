# Sub-phase 1: Detection Brain — Verify Stage/Exit, Add Scope-Mode

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` before starting.

## Objective

Land the **detection-layer** edits of Phase 1b (plan activities 1, 2, 4). Two already-present
mechanisms get verified-and-sharpened (stage-adaptive framework, exit conditions); one new
mechanism is added (scope-mode detection from signal words, with a `scope_mode` front-matter
field). Detection edits come first because later sub-phases' presentation/output edits reference
the detected stage and scope mode. After this sub-phase the agent *detects* maturity (stage) and
ambition (scope mode) and states both to the user, but does not yet quote evidence, record
decisions, or run the reviewer/gate.

## Dependencies
- **Requires completed:** None (first sub-phase).
- **Assumed codebase state:** `agents/cast-refine-requirements/cast-refine-requirements.md` at its
  current 434-line baseline; Step 1.3 stage table and Step 2.4 exit conditions present and
  unmodified.

## Scope

**In scope:**
- Activity 1 — verify/sharpen the Step 1.3 stage-adaptive framework (add purpose sentence +
  cross-link to scope mode). Keep the existing signal table verbatim.
- Activity 2 — strengthen Step 2.4's budget-exhaustion rule into the zero-silent-failure
  invariant.
- Activity 4 — add a scope-mode detection table to Step 1.3; state the mode + quoted signal words
  in Step 2.1; add the `scope_mode` front-matter field to the Step 3.1 template.

**Out of scope (do NOT do these):**
- Evidence-quoting mandate, `## Decisions` section, `templates/cast-spec.template.md` edits
  (→ sp2).
- Reviewer subagent, HARD GATE (→ sp3).
- `bin/generate-skills`, any test file (→ sp4). Do NOT regenerate skills in this sub-phase.
- Editing `#### Step 2.2.1: Domain Web Search` — it is pinned by `test_b1_domain_search.py`. Leave
  it byte-for-byte unchanged.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | 434 lines; Step 1.3 stage table + Step 2.4 exit conditions present |

## Detailed Steps

### Step 1.1: Sharpen the stage-adaptive framework (activity 1)
In `#### Step 1.3: Detect Stage and Select Framework`, keep the existing stage signal table
verbatim. Add one sentence making its purpose explicit: this is the **Template-Enforcer guard at
the authoring layer** — a vague-stage writeup must never be forced to full EARS depth; the
detected stage licenses which sections may legitimately stay thin (and therefore low-confidence)
without padding. Then add a cross-link sentence: **stage = how mature the input is; scope mode =
how ambitious the output should be** (added in Step 1.1 below); both are detected in Phase 1 and
both stated to the user in Step 2.1.

### Step 1.2: Add the scope-mode detection table (activity 4)
Extend `#### Step 1.3` with a **second detection table**, immediately after the stage table.
Reuse the Garry Tan vocabulary already shipped in `cast-detailed-plan` verbatim — **SCOPE
REDUCTION / HOLD SCOPE / SCOPE EXPANSION** — so the two agents read a goal's language identically:

```markdown
**Detect scope mode** (how ambitious the output should be — orthogonal to stage):

| Signal words in the writeup | Scope mode | Effect on the draft |
|------------------------------|-----------|---------------------|
| "MVP", "minimum", "just enough", "spike", "v0" | SCOPE REDUCTION | Fewer EARS scenarios; ruthless Out of Scope; defer-by-default |
| none / balanced language | HOLD SCOPE (default) | Scenario depth per the stage table above |
| "comprehensive", "full-featured", "dream", "ideal", "10x" | SCOPE EXPANSION | Exhaustive edge cases; stretch items captured in Directional ideas |

State the detected mode and the quoted signal words to the user in Step 2.1. If signals conflict
(reduction *and* expansion words both present), confirming the mode becomes one Phase 2 question
(it counts against the 7-question budget — it is exactly the "high-risk unknown" tier).
```

### Step 1.3: State scope mode in the draft presentation (activity 4)
In `#### Step 2.1: Present Draft`, add a line to the presentation: state the detected scope mode
and the verbatim signal words that triggered it (e.g. `Scope mode: SCOPE REDUCTION — "MVP",
"just the happy path"`). For HOLD SCOPE with no signals, say so explicitly ("Scope mode: HOLD
SCOPE — no scope signals detected").

### Step 1.4: Persist scope_mode in front-matter (activity 4)
In the `#### Step 3.1` output-template front-matter block (near `confidence:`), add an additive
field: `scope_mode: reduction | hold | expansion`. The checker does not lint front-matter keys,
so this is safe. Note in the template comment that it is set from the Step 1.3 scope-mode
detection.

### Step 1.5: Strengthen exit conditions into zero-silent-failure (activity 2)
In `#### Step 2.4: Exit Conditions`, keep the three exit triggers. Replace the soft
budget-exhaustion note with the **zero-silent-failure invariant**: *every* section still below
medium confidence at exit MUST have a matching `[NEEDS CLARIFICATION: …]` entry in Open Questions
(the shape `cast-spec-checker` already lints). No section may silently ship low-confidence. State
this explicitly as the "no silent low-confidence sections" guarantee.

## Verification

### Automated Tests (permanent)
- None authored here — pinning tests are sp4. But run the existing pin to prove no regression:
  `pytest tests/test_b1_domain_search.py` → must pass (proves Step 2.2.1 / Domain Web Search and
  the no-numeric-cap rule are untouched).

### Validation Scripts (temporary)
```bash
F=agents/cast-refine-requirements/cast-refine-requirements.md
grep -nq 'SCOPE REDUCTION' "$F" && grep -nq 'SCOPE EXPANSION' "$F" && echo "scope-mode table OK"
grep -nq 'scope_mode:' "$F" && echo "front-matter field OK"
grep -niq 'no silent' "$F" && echo "zero-silent-failure phrasing OK"
grep -nq 'Template-Enforcer' "$F" && echo "stage purpose sentence OK"
wc -l "$F"   # record the new line count; must stay well under 650
```

### Manual Checks
- Confirm the Step 1.3 stage signal table is byte-for-byte unchanged (only additive sentences +
  the new scope-mode table were added).
- Confirm `#### Step 2.2.1: Domain Web Search` is untouched: `git diff -- "$F"` shows no hunk in
  that section.

### Success Criteria
- [ ] Step 1.3 has the purpose sentence + the stage↔scope cross-link + the new scope-mode table.
- [ ] Scope-mode vocabulary is exactly SCOPE REDUCTION / HOLD SCOPE / SCOPE EXPANSION.
- [ ] Step 2.1 states the detected mode + quoted signal words.
- [ ] Step 3.1 front-matter has `scope_mode: reduction | hold | expansion`.
- [ ] Step 2.4 budget-exhaustion is now the zero-silent-failure invariant referencing
      `[NEEDS CLARIFICATION: …]` in Open Questions.
- [ ] `pytest tests/test_b1_domain_search.py` passes; Step 2.2.1 shows no git diff.
- [ ] Prompt line count recorded and < 650.

## Execution Notes
- Integrate into existing steps — do NOT append a new top-level section.
- Keep the scope-mode wording identical to `cast-detailed-plan`'s table; grep that file for the
  exact phrasing before writing (`grep -n 'SCOPE REDUCTION' agents/cast-detailed-plan/*.md`).
- Do NOT run `bin/generate-skills` here — regen is batched in sp4 to avoid mid-stream backups.
- **Spec-linked files:** none modified in this sub-phase (no template/checker edits here).
