# Sub-phase 2: Evidence-Quoting Mandate + Dated Decisions Section

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` before starting.

## Objective

Land the **output-quality** edits of Phase 1b (plan activities 6 and 3). Confidence ratings
become un-fakeable — a section may only be rated medium/high if the agent can quote verbatim
support, shown next to the rating. Human decisions become durable provenance — a new dated
`## Decisions` (Chose/Over/Because) section, buffered at answer-time, with a lockstep additive
edit to the canonical spec template and a recognition note in the checker's shape-rules doc.

## Dependencies
- **Requires completed:** sp1 (scope-mode + zero-silent-failure landed; Step 2.1 already states
  detected mode — evidence quotes attach to the same presentation).
- **Assumed codebase state:** sp1's edits present; `templates/cast-spec.template.md` and
  `agents/cast-spec-checker/cast-spec-checker.md` at baseline; `bin/cast-spec-checker` unchanged.

## Scope

**In scope:**
- Activity 6 — evidence-quoting mandate at Step 1.5 (sufficiency check) and Step 2.1 (present
  draft); unquotable support drops the rating to low and routes the gap to Open Questions.
- Activity 3 — new `## Decisions` section in the Step 3.1 output template (between `## Out of
  Scope` and `## Open Questions`); answer-time buffering population rule; 0-fork fallback line;
  lockstep additive edit to `templates/cast-spec.template.md`; one-line recognition note in
  `agents/cast-spec-checker/cast-spec-checker.md`.

**Out of scope (do NOT do these):**
- Scope-mode / stage / exit-condition edits (done in sp1).
- Reviewer subagent, HARD GATE (→ sp3).
- `bin/generate-skills`, test files (→ sp4).
- **Never modify `bin/cast-spec-checker`** — the template + checker doc ARE the contract; the
  checker tolerates additive H2s. Confirm REQUIRED_SECTIONS = the four required sections only;
  do not add `Decisions` to them.
- Do NOT touch `#### Step 2.2.1: Domain Web Search`.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | sp1 edits present |
| `templates/cast-spec.template.md` | Modify | Canonical 4-required-section shape; no Decisions block |
| `agents/cast-spec-checker/cast-spec-checker.md` | Modify | Shape rules; no mention of Decisions |

## Detailed Steps

### Step 2.1: Evidence-quoting mandate (activity 6)
In `#### Step 1.5: Run Sufficiency Check` and `#### Step 2.1: Present Draft`, add the rule: a
section may be rated **medium or high** confidence ONLY if the agent can cite a **verbatim quote**
from the raw writeup or the conversation that supports the rating. The quote is shown next to the
rating in the Step 2.1 presentation (conversation-only — the persisted front-matter shape is
unchanged). If support is unquotable, the rating **drops to low** and the gap goes to Open
Questions. Frame it as `/plan-eng-review`'s "quote the verbatim motivating line" gate applied to
confidence — it kills the "high confidence because I didn't check" failure mode the Quality Bar
already names. Example presentation line to include:
`Intent — HIGH ("we keep losing track of which goals are actually blocked")`.

### Step 2.2: Add `## Decisions` to the Step 3.1 output template (activity 3)
In the `#### Step 3.1` output template, insert a new section **between `## Out of Scope` and
`## Open Questions`**:

```markdown
## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
```

Document the **answer-time buffering** population rule inline (mirror `cast-plan-review`'s B2
buffer-at-decision-time pattern): the moment an `AskUserQuestion` fork resolves in Phase 2, append
`{date, chose, over, because}` to an in-memory list — `date` = harness `currentDate`, `chose` =
the option the user picked, `over` = the option(s) rejected, `because` = their stated/implied
rationale **at that moment**. Render the table verbatim from the list at persist. **Do NOT
reconstruct from end-of-session memory** (it confabulates Over/Because after intervening turns).
Decisions the agent made unilaterally (a default the user never saw) do NOT go here — this records
**human** choices only, which is what makes it provenance for Phase 4 versioning. If no forks were
resolved (0-question runs), emit the section with a single
`*No decisions recorded this refinement.*` line rather than omitting it (Phase 1's parser prefers
a stable section set).

### Step 2.3: Lockstep edit — spec template (activity 3)
Add `## Decisions` to `templates/cast-spec.template.md` as an **optional** section with the same
`| Date | Chose | Over | Because |` table shape, placed between `## Out of Scope` and
`## Open Questions`. Mark it optional in a template comment.

### Step 2.4: Recognition note — checker shape doc (activity 3)
Add **one line** to `agents/cast-spec-checker/cast-spec-checker.md` noting `## Decisions` as a
recognized **optional** section (so the next checker editor does not "clean it up"). Do NOT add it
to REQUIRED_SECTIONS anywhere.

## Verification

### Automated Tests (permanent)
- None here (pins are sp4). Run the existing pin for no-regression:
  `pytest tests/test_b1_domain_search.py` → must pass.

### Validation Scripts (temporary)
```bash
F=agents/cast-refine-requirements/cast-refine-requirements.md
grep -nq '## Decisions' "$F" && echo "Decisions in output template OK"
grep -niq 'verbatim quote' "$F" && echo "evidence-quoting mandate OK"
grep -niq 'answer-time' "$F" && echo "answer-time buffering rule OK"
grep -nq '## Decisions' templates/cast-spec.template.md && echo "template OK"
grep -niq 'Decisions' agents/cast-spec-checker/cast-spec-checker.md && echo "checker doc note OK"

# CRITICAL: the checker must still pass on a pre-existing spec and ignore the new optional H2.
python3 - <<'PY'
import re, pathlib
src = pathlib.Path('bin/cast-spec-checker').read_text()
m = re.search(r'REQUIRED_SECTIONS\s*=\s*[\[{(]([^\])}]*)', src)
print('REQUIRED_SECTIONS snippet:', m.group(0)[:200] if m else 'NOT FOUND — inspect manually')
assert 'Decisions' not in (m.group(0) if m else ''), "Decisions must NOT be a required section"
print('OK: Decisions is not required')
PY
# Sanity: checker exits 0 on a known-good existing spec (pick any from docs/specs/).
SPEC=$(ls docs/specs/*.md 2>/dev/null | head -1); [ -n "$SPEC" ] && bin/cast-spec-checker "$SPEC" && echo "checker exit 0 on $SPEC"
wc -l "$F"
```

### Manual Checks
- Confirm `## Decisions` sits exactly between `## Out of Scope` and `## Open Questions` in BOTH
  the agent prompt's Step 3.1 template AND `templates/cast-spec.template.md`.
- Confirm the answer-time-buffering rule explicitly forbids end-of-session reconstruction.

### Success Criteria
- [ ] Evidence-quoting mandate present at Step 1.5 and Step 2.1; unquotable → low + Open Questions.
- [ ] `## Decisions` table (`| Date | Chose | Over | Because |`) in the Step 3.1 template, between
      Out of Scope and Open Questions.
- [ ] Answer-time buffering rule + 0-fork fallback line documented; human-only constraint stated.
- [ ] `templates/cast-spec.template.md` has the additive optional `## Decisions` block.
- [ ] `agents/cast-spec-checker/cast-spec-checker.md` has the one-line recognition note.
- [ ] `bin/cast-spec-checker` UNCHANGED; REQUIRED_SECTIONS still the four required sections;
      checker exits 0 on a pre-existing spec.
- [ ] `pytest tests/test_b1_domain_search.py` passes; prompt line count recorded and < 650.

## Execution Notes
- The template is the contract — keep the Decisions block strictly additive-optional. If the
  checker were to reject an extra H2 (it does not), STOP and re-read `_shared_context.md` §Relevant
  Specs rather than weakening the section.
- Do NOT run `bin/generate-skills` here — batched in sp4.
- **Spec-linked files:** `templates/cast-spec.template.md` is the canonical checker-enforced shape.
  After editing it, run `bin/cast-spec-checker` on a real spec to confirm SAV behavior (exit 0) is
  preserved. No `docs/specs/` registry entry covers this agent, so no `/cast-update-spec` run.
