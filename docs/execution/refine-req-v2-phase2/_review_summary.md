# Review Summary: Refine Requirements v2 — Phase 2 (Classification)

> **Review mode:** Self-review pass (SMALL CHANGE discipline — max 1 issue per section), run
> autonomously. The source plan
> (`docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`) already carries a complete
> `## Decisions` section appended by `cast-plan-review` (2026-06-11, BIG-CHANGE pass, 7 issues, all
> resolved), and its bodies were patched inline to match. Dispatching seven fresh `cast-plan-review`
> subagents over already-reviewed material would re-litigate settled decisions against the run's
> "proceed fully autonomously" directive — so this is a lightweight consistency review instead.
> **Recorded default:** if a reviewer wants the full per-sub-phase `cast-plan-review` gauntlet, run
> `/cast-plan-review` on each `spN_*/plan.md` before execution.

## Open Questions

No **blocking** open questions for the execution plan itself — all design ambiguity was resolved at
plan review. Two items are carried (non-blocking) into execution, both already handled in the
sub-phase plans:

1. **Corpus privacy/location** (→ sp4): can the second-brain/linkedout writeups be committed as eval
   fixtures, or must the corpus live outside the repo? Owner call during sp4. The eval script is built
   to take a `--corpus-dir` path either way, so this does not block the build — only the final
   accuracy number. (`human_action_needed` for the overall run.)
2. **Classifier model tier** (→ sp2a/sp4): `sonnet` is the planned default; the sp4 corpus eval is the
   designed resolver (escalate to `opus` only on a <85% miss). Not blocking — the numbers decide.

## Review Notes by Sub-Phase

### sp1_taxonomy_module (WP A)
- Keystone correctly placed first and isolated; all four pure functions + their adversarial tests are
  scoped here. The conditional Phase-1 `EVIDENCE`/`DECISION` BlockKind addition is the one cross-phase
  edit — flagged as "verify first, add only if missing" so it can't double-apply. No issues.

### sp2a_classifier_agent (WP B)
- Cleanly read-only (no cast-server change, no output envelope). The `generic` vs `random_idea`
  boundary (D2) and the "strict tool-call realized as prompt+validation" note are both carried.
  Shared `bin/generate-skills` with sp2c is the only parallel-safety concern — documented in both.
  No issues.

### sp2b_gate_bin (WP C)
- Thin-wrapper discipline preserved (no logic in the bin). Opposite import policy vs sp2c is stated.
  Off-schema-never-crash + exit-2-on-unparseable are both tested. No shared files. No issues.

### sp2c_two_level_checker (WP D)
- The two hardest invariants are explicit: (a) grammar regexes / `_section_spans` untouched (Phase 1
  bridge stays green), (b) mirror-not-import with a full-mapping pin test (D5). The "don't add a global
  Decisions/Evidence requirement" trap (SR #3) is called out. No issues.

### sp3a_refine_integration (WP E)
- Step 0 kept terse (~60 lines) against the ~650-line ceiling; the question-budget ordering and
  headless/fail-soft policies are all carried. `merge_front_matter`-only persistence (D3) is enforced
  in the success criteria. Shared file with Phase 1b (not with sp3b) → rebase rule stated. No issues.

### sp3b_spec_template (WP F)
- Documentation-lockstep framing is correct (code authoritative, spec follows). The
  "classifier outside the delegation/output-json contracts" disambiguation is required and present.
  Template contention is with Phase 1b only, not sp3a — parallel-safe with sp3a confirmed. No issues.

### sp4_corpus_eval (WP G)
- The only genuine human-in-the-loop dependency (corpus labeling + privacy call) is isolated here and
  surfaced as a run-level `human_action_needed`. Tuning discipline (prompt content → model tier, never
  the LOCKED taxonomy) is explicit. `--corpus-dir` decouples the build from the privacy decision. No
  issues.

## Parallel-Safety Verification

- **Group 2 (sp2a/sp2b/sp2c):** disjoint source files. Shared *action* `bin/generate-skills` (sp2a,
  sp2c) is idempotent — documented in both. ✅
- **Group 3 (sp3a/sp3b):** sp3a → `agents/cast-refine-requirements/*`; sp3b → `docs/specs/*` +
  `templates/cast-spec.template.md`. No file overlap. ✅
- **Cross-phase (not within this plan):** `cast-refine-requirements.md` (sp3a) and
  `cast-spec.template.md` (sp3b) are each also touched by Phase 1b — rebase-don't-clobber rule recorded
  in the manifest and both sub-phase plans. ✅
