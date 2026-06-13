# Sub-phase 4 Output: Regenerate Skills + Prompt-Pinning Tests

**Status:** completed — all success criteria met.

## What was done

### Step 4.1 — Regenerated skills
- Ran `bin/generate-skills`. Wrote 68 SKILL.md files (56 agents, 12 skills) to
  `~/.claude/skills`; 68 pre-existing files auto-backed-up to
  `~/.claude/skills/.cast-bak-20260612-012744/`.
- Confirmed `~/.claude/skills/cast-refine-requirements/SKILL.md` now carries every
  Phase 1b anchor: `scope_mode`, the `## Decisions` section, the HARD-GATE sentence
  (`in your first response`), the reviewer rubric's five dimensions
  (Completeness / Consistency / Clarity / Scope / Feasibility), and the
  evidence-quoting mandate (`verbatim quote`). The CUT `adversarial meta-pass`
  rubric does **not** appear (Decision #3).

### Step 4.2 — Authored the pinning test (Decision #5)
- Created `tests/test_phase1b_prompt_pins.py`, mirroring the read-file /
  assert-substring shape of `tests/test_b1_domain_search.py`.
- Pins all Phase 1b anchors in BOTH the source prompt
  (`agents/cast-refine-requirements/cast-refine-requirements.md`) and the
  regenerated skill (`~/.claude/skills/cast-refine-requirements/SKILL.md`,
  resolved via `Path.home()`) — the regen-survival tripwire.
- Pins `## Decisions` in `templates/cast-spec.template.md`.
- **Negative pin:** asserts `adversarial meta-pass` appears in neither the prompt
  nor the skill — guards Decision #3. (The tombstone phrase
  "activity-5 meta-pass was cut" is intentionally a different string and is
  allowed to remain.)
- The skill-side pins `pytest.skip` cleanly if the generated SKILL.md is absent
  (e.g. CI without installed skills), so the suite degrades gracefully rather
  than hard-failing.

### Step 4.3 — Proved pins green
- `uv run pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py -q`
  → **32 passed in 0.11s** (the existing B1 pin still passes unchanged; numeric
  question caps did NOT reappear — Issue #14).
- `bin/generate-skills --dry-run` → exits 0, "would write 68 SKILL.md files",
  no skip-warning for cast-refine-requirements (agent listed without error).

## Validation results
```
pins green
regen carried anchors OK
dry-run OK
```

## Success Criteria
- [x] `bin/generate-skills` ran; SKILL.md regenerated with all Phase 1b anchors.
- [x] `tests/test_phase1b_prompt_pins.py` exists, mirrors the `test_b1` pattern,
      pins all anchors (including the negative meta-pass pin and regen-survival).
- [x] `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` passes.
- [x] `bin/generate-skills --dry-run` lists the agent without error.

## Notes
- No edits were needed to the agent prompt — sp1–sp3 had already landed every
  anchor the pins assert on (prompt is 548 lines, under the ~650 ceiling). No
  missing-anchor fixes were required.
- Files created/modified this sub-phase: `tests/test_phase1b_prompt_pins.py`
  (new); `~/.claude/skills/**/SKILL.md` (regenerated, outside repo tree).
- Unblocks sp5 (live re-refinement verification).
