# Sub-phase 4: Regenerate Skills + Prompt-Pinning Tests

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` before starting.

## Objective

Land plan activity 9: make the prompt edits user-facing and tripwire them against regression.
Regenerate the user-facing skill from the edited agent prompt, add the new prompt-pinning test
that asserts every Phase 1b anchor is present and survives regen, and prove the pre-existing pin
(`test_b1_domain_search.py`) still passes. This is the automated guarantee that sp1–sp3's edits
do not silently rot or get "cleaned up" by a future editor or a regen pass.

## Dependencies
- **Requires completed:** sp1, sp2, sp3 — all prompt/template/checker-doc anchors must already
  exist for the pins to assert on them.
- **Assumed codebase state:** agent prompt ~500–555 lines with all Phase 1b anchors;
  `templates/cast-spec.template.md` has `## Decisions`; `tests/test_b1_domain_search.py` present.

## Scope

**In scope:**
- Run `bin/generate-skills` so `~/.claude/skills/cast-refine-requirements/SKILL.md` regenerates.
- Create `tests/test_phase1b_prompt_pins.py` asserting the new anchors are present **and survive
  generate-skills regen**.
- Prove `tests/test_b1_domain_search.py` still passes (Domain Web Search survives; numeric
  question caps did NOT reappear — Issue #14).
- Confirm `bin/generate-skills --dry-run` lists the agent without error.

**Out of scope (do NOT do these):**
- Any further edits to the agent prompt's behavior (sp1–sp3 own those). If a pin reveals a missing
  anchor, the fix belongs in the owning sub-phase — note it and add the anchor minimally, but do
  not redesign behavior here.
- A meta-pass anchor — that import was CUT (Decision #3). Do NOT pin a meta-pass.
- The live re-refinement verification (→ sp5).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `tests/test_phase1b_prompt_pins.py` | Create | Does not exist |
| `~/.claude/skills/cast-refine-requirements/SKILL.md` | Regenerate | Stale (pre-Phase-1b prompt) |

## Detailed Steps

### Step 4.1: Regenerate skills
Run `bin/generate-skills` (pre-existing files auto-backup to `.cast-bak-<timestamp>/`). Confirm
`~/.claude/skills/cast-refine-requirements/SKILL.md` now contains the Phase 1b anchors (scope_mode,
`## Decisions`, the HARD-GATE sentence, the reviewer rubric, evidence-quoting).

### Step 4.2: Author the pinning test (Decision #5)
Create `tests/test_phase1b_prompt_pins.py`, mirroring the `tests/test_b1_domain_search.py` pattern
(read the file, assert substrings). Pin these anchors in BOTH the source agent prompt
(`agents/cast-refine-requirements/cast-refine-requirements.md`) and the regenerated skill
(`~/.claude/skills/cast-refine-requirements/SKILL.md` — resolve via the same path-helper
`test_b1` uses, or `Path.home()`):
- `## Decisions` present in `templates/cast-spec.template.md`.
- `scope_mode` present in the agent prompt.
- The five scope-mode tokens: `SCOPE REDUCTION`, `HOLD SCOPE`, `SCOPE EXPANSION`.
- The HARD-GATE sentence (a stable substring, e.g. `in your first response`).
- The reviewer rubric heading / its five dimensions:
  `Completeness`, `Consistency`, `Clarity`, `Scope`, `Feasibility`.
- The evidence-quoting mandate (a stable substring, e.g. `verbatim quote`).
- **Negative pin:** assert NO meta-pass anchor (e.g. assert `adversarial meta-pass` does not
  appear as an active rubric) — guards Decision #3.
- **Regen-survival:** assert the same anchors appear in the regenerated SKILL.md, not just the
  source (the tripwire against regen drift).

Reference the existing pattern first:
```bash
sed -n '1,60p' tests/test_b1_domain_search.py   # copy its imports + path resolution
```

### Step 4.3: Prove existing pins green
```bash
pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q
bin/generate-skills --dry-run    # lists the agent without error
```

## Verification

### Automated Tests (permanent)
- `tests/test_phase1b_prompt_pins.py` — the new tripwire (this sub-phase's deliverable).
- `tests/test_b1_domain_search.py` — must still pass unchanged.

### Validation Scripts (temporary)
```bash
pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q && echo "pins green"
test -f ~/.claude/skills/cast-refine-requirements/SKILL.md && \
  grep -q 'scope_mode' ~/.claude/skills/cast-refine-requirements/SKILL.md && \
  grep -q 'Feasibility' ~/.claude/skills/cast-refine-requirements/SKILL.md && \
  echo "regen carried anchors OK"
bin/generate-skills --dry-run >/dev/null 2>&1 && echo "dry-run OK"
```

### Manual Checks
- Confirm the regenerated SKILL.md is the Phase 1b version (spot-check the HARD-GATE sentence and
  the reviewer rubric are present).
- Confirm the test asserts on BOTH source prompt and regenerated skill (regen-survival).

### Success Criteria
- [ ] `bin/generate-skills` ran; SKILL.md regenerated with all Phase 1b anchors.
- [ ] `tests/test_phase1b_prompt_pins.py` exists, mirrors the `test_b1` pattern, pins all anchors
      (including the negative meta-pass pin and regen-survival).
- [ ] `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` passes.
- [ ] `bin/generate-skills --dry-run` lists the agent without error.

## Execution Notes
- → Delegate (optional): if authoring the pytest file, `/cast-pytest-best-practices` covers the
  house test conventions; mirror `test_b1_domain_search.py` rather than inventing a new shape.
- If a pin fails because an anchor is missing, the root cause is in sp1–sp3 — add the minimal
  missing anchor in the owning file, re-run, and note it in the Progress Log; do not redesign.
- `bin/generate-skills` backs up existing skills automatically — no manual backup needed.
- **Spec-linked files:** none modified (tests + generated skill only).
