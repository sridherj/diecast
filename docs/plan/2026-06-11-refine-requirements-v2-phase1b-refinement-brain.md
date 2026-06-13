# Refine Requirements v2: Phase 1b — Refinement Brain Upgrades (gbrain imports)

## Overview

This plan details Phase 1b of the refine-requirements-v2 goal: porting the portable quality
upgrades from second-brain's `taskos-refine-requirements` lineage (and the wider gbrain/gstack
skill family — `/spec`, `/office-hours`, `/plan-eng-review`) into the
`cast-refine-requirements` agent prompt. These are **pure agent-prompt edits** — no cast-server
code, no parser, no DB — which is why this phase runs in parallel with Phase 1 and de-risks
output quality before the render/comments/versioning build lands.

**Planning-time finding that corrects the playbook:** two of the "six gbrain imports" listed in
Playbook 01 §Step 6 **already exist** in the current prompt
(`agents/cast-refine-requirements/cast-refine-requirements.md`):

| Import | Current state |
|--------|---------------|
| Stage-adaptive framework (vague→JTBD; specific→Example-Mapping; near-complete→EARS) | **Present** — Step 1.3 "Detect Stage and Select Framework" has exactly this table |
| Explicit exit conditions + log gaps into Open Questions on budget exhaustion | **Present** — Step 2.4 "Exit Conditions" including the budget-exhaustion → Open Questions rule |
| Dated Decisions section (Chose / Over / Because) | **Missing** |
| Adversarial meta-pass ("what would an engineer reject?") | **Missing** — and **cut from this phase by plan review** (2026-06-11, Decision #3): the fresh-context reviewer subagent (activity 8) subsumes it; running both duplicated the consistency/measurability/feasibility rubric and fed the prompt-bloat risk |
| Evidence-quoting mandate for confidence scores | **Missing** (Quality Bar gestures at it — "low means low" — but nothing operationalizes it) |
| Scope-mode detection from signal words (MVP / comprehensive / dream) | **Missing** |

The two present imports become **verify-and-sharpen** work; the missing ones are the new
build (minus the adversarial meta-pass, cut by review — see Decisions appendix). The owner
confirmed at planning time (2026-06-11) that **both optional ports are in scope**: the gstack
`/spec` HARD GATE and the `/office-hours`-style adversarial reviewer subagent.

## Position in Overall Plan

```
Phase 0: SPIKES ✅ (gate cleared 2026-06-11)
   ▼
Phase 1: Parser & Thin Spine ──────────► Phase 2 ─► Phase 3a/3b ─► Phase 4 ─► Phase 5
Phase 1b: THIS PLAN (no deps — parallel with Phase 1, off the critical path)
```

Phase 1b has **no dependencies** and **nothing downstream depends on it structurally** — but two
soft couplings exist and are honored below:

- **Decisions section ↔ Phase 4 versioning:** dated decision rows become per-version provenance
  when versioning lands. The section format chosen here should not need rework then.
- **Scope-mode / classification question budget ↔ Phase 2:** the scope-mode confirm (when
  ambiguous) and Phase 2's classification confirm (FR-004) both draw on the same 7-question
  budget. Phase 2's planner should know scope-mode claims one slot in the worst case.

## Depends On (from prior plans)

First wave — no prior sub-phase plans exist. Inputs are the high-level plan
(`plan.collab.md` Phase 1b section), Playbook 01 (§Step 6 import table, §2d keep/drop verdicts),
and Research Note 01 §2 (the gbrain survey with the source mechanics of each import).

## Operating Mode

**HOLD SCOPE** — the phase brief is explicit and bounded: "pure agent-prompt edits", "1 session
(~1 day of prompt edits)", "keep it scoped there [agents/cast-refine-requirements/*]". The one
genuine scope fork ("Optionally port the gstack `/spec` HARD GATE + an `/office-hours`-style
adversarial reviewer subagent") was resolved by the owner at planning time: **both included**.
With that decision made, scope is fixed — no further extras. Plan review (2026-06-11) made one
**cut** (the adversarial meta-pass, Decision #3) and several precision/correctness amendments;
see the Decisions appendix. Revised estimate after both optional ports and the meta-pass cut:
**~1.5 sessions**.

## Sub-phase: Sharper Refinement Brain — gbrain Imports Landed in the Agent Prompt

**Outcome:** `cast-refine-requirements` produces sharper drafts: every refinement run states its
detected scope mode with quoted evidence, presents confidence scores backed by verbatim quotes,
records conversation decisions as dated Chose/Over/Because rows (captured at answer-time) in a
new `## Decisions` section, gets a fresh-context adversarial reviewer score **before** the user's
final go-ahead, and never emits the final file without showing the user the (fully reviewed)
draft first. `bin/cast-spec-checker` still exits 0 on all output, and the prompt-pinning tests
(`tests/test_b1_domain_search.py` plus the new `tests/test_phase1b_prompt_pins.py`) stay green.

**Dependencies:** None.

**Estimated effort:** ~1.5 sessions (1 session of prompt edits + 0.5 session of verification
re-refinements).

**Verification:** see the dedicated block after the activities — the phase brief's
"re-refine 2-3 real writeups" criterion is expanded into specific, checkable assertions.

### Key activities

All edits target `/home/sridherj/workspace/diecast/agents/cast-refine-requirements/cast-refine-requirements.md`
unless stated otherwise. Source mechanics for each port are in Research Note 01 §2
(`goals/refine-requirements-v2/exploration/research/01-learn-from-existing-systems.ai.md`) —
do not re-research.

**1. Verify & sharpen the stage-adaptive framework (Step 1.3 — already present).**
- Keep the existing signal table verbatim; add one sentence making its *purpose* explicit: this
  is the Template-Enforcer guard at the authoring layer — a vague-stage writeup must never be
  forced to full EARS depth; the detected stage licenses which sections may legitimately stay
  thin (and therefore low-confidence) without padding.
- Cross-link it to the new scope-mode detection (activity 4): stage = how mature the input is;
  scope mode = how ambitious the output should be. Both are detected in Phase 1, both stated to
  the user in Step 2.1.

**2. Verify & sharpen exit conditions (Step 2.4 — already present).**
- Keep the three exit triggers. Strengthen the budget-exhaustion rule into a zero-silent-failure
  invariant: *every* section still below medium confidence at exit MUST have a matching
  `[NEEDS CLARIFICATION: …]` entry in Open Questions (the shape `cast-spec-checker` already
  lints). No section may silently ship low-confidence — this is the "no silent low-confidence
  sections" guarantee the high-level plan names.

**3. Add the dated Decisions section (Chose / Over / Because) — new.**
- New `## Decisions` section in the Step 3.1 output template, inserted between `## Out of Scope`
  and `## Open Questions`, as a table: `| Date | Chose | Over | Because |`.
- **Population rule (answer-time buffering — Decision #4):** the moment an AskUserQuestion fork
  is resolved in Phase 2, append a `{date, chose, over, because}` entry to an in-memory list —
  `date` = the harness-provided `currentDate`, `chose` = the option the user picked, `over` =
  the option(s) they rejected, `because` = their stated/implied rationale at that moment. At
  persist time, render the table verbatim from that list. Do NOT reconstruct the table from
  session memory at the end — that confabulates the `Over`/`Because` fields after intervening
  turns. (This mirrors `cast-plan-review`'s own B2 buffer-at-decision-time pattern.) Decisions
  made unilaterally by the agent (a default the user never saw) do NOT go here — this section
  records *human* choices, which is what makes it provenance for Phase 4 versioning.
- If no forks were resolved (0-question runs), emit the section with a single "*No decisions
  recorded this refinement.*" line rather than omitting it — downstream parsers (Phase 1's block
  model) prefer a stable section set.
- **Lockstep template edit:** add `## Decisions` to `templates/cast-spec.template.md` as an
  optional section with the same table shape. The checker (`bin/cast-spec-checker`) enforces only
  four REQUIRED_SECTIONS (User Stories, Functional Requirements, Success Criteria, Open
  Questions) and tolerates additive H2s — verified at planning time (R1 only asserts required
  sections are *present*; it never rejects extra H2s) — so no checker code change is needed. Add
  one line to the shape-rules doc (`agents/cast-spec-checker/cast-spec-checker.md`) noting
  Decisions as a recognized optional section, so the next checker editor doesn't "clean it up".

**4. Add scope-mode detection from signal words — new.**
- Extend Step 1.3 (it is already the "detect, then adapt" home) with a second detection table,
  reusing the wording of the Garry Tan framework already shipped in `cast-detailed-plan` (keep
  the two agents' vocabulary identical — SCOPE REDUCTION / HOLD SCOPE / SCOPE EXPANSION — so a
  goal's language is interpreted the same way at refinement and at planning):
  - "MVP", "minimum", "just enough", "spike", "v0" → SCOPE REDUCTION: fewer EARS scenarios,
    ruthless Out of Scope, defer-by-default.
  - No signals / balanced language → HOLD SCOPE (default): scenario depth per the stage table.
  - "comprehensive", "full-featured", "dream", "ideal", "10x" → SCOPE EXPANSION: exhaustive
    edge cases, stretch items captured in Directional ideas.
- State the detected mode + the quoted signal words in the Step 2.1 draft presentation. If
  signals conflict, confirming the mode becomes a Phase 2 question (counts against the
  7-question budget — it is exactly the "high-risk unknown" tier).
- Persist the result as a new front-matter field `scope_mode: reduction | hold | expansion`
  (additive; the checker does not lint front-matter keys).

**5. ~~Add the adversarial meta-pass~~ — CUT by plan review (Decision #3, 2026-06-11).**
- **Removed from scope.** The fresh-context reviewer subagent (activity 8) is now the sole
  adversarial pass. Rationale: the meta-pass rubric (cross-section contradictions, unmeasurable
  constraints, circular questions, un-failable scenarios) overlapped the reviewer's
  Consistency/Clarity/Feasibility dimensions; running both duplicated work and fed the
  prompt-bloat risk the plan names as #1. Activity number retained as a tombstone so downstream
  cross-references (verification items, Build Order) stay legible.
- **Consequence (tracked in Key Risks):** when the reviewer fail-softs (unavailable / Agent-tool
  denied), a refinement run now ships with **no** adversarial pass at all. Accepted: the run
  still surfaces the "review skipped" note, and the zero-silent-failure Open-Questions invariant
  (activity 2) plus evidence-quoting (activity 6) remain in force on every run.

**6. Add the evidence-quoting mandate for confidence scores — new.**
- Extend Step 1.5 (sufficiency check) and Step 2.1 (present draft): a section may only be rated
  medium or high confidence if the agent can cite a verbatim quote from the raw writeup or the
  conversation supporting that rating; the quote is shown next to the rating in the Step 2.1
  presentation (conversation-only — the persisted front-matter shape is unchanged).
- Unquotable support → the rating drops to low and the gap goes to Open Questions. This is
  `/plan-eng-review`'s "quote the verbatim motivating line" pre-emit gate, applied to
  confidence instead of findings — it kills the "high confidence because I didn't check"
  failure mode the Quality Bar already names.

**7. Port the gstack `/spec` HARD GATE — owner-confirmed optional, in scope.**
- Add the gate rule near the top of the Workflow section: **"Do NOT write
  `refined_requirements.collab.md` in your first response. Always present the (fully reviewed)
  draft and give the user at least one opportunity to react before persisting — even when every
  section is medium+ confidence."**
- Amend Step 1.5's exit ("If all sections are medium+, skip directly to Phase 3") to "skip the
  *questioning loop*, but still run the independent reviewer (activity 8), then present the draft
  and wait for one go-ahead". This is an intentional behavior change: today's prompt allows a
  zero-interaction one-shot; the gate makes the minimum interaction one draft-review. Cost: one
  extra round-trip on clean runs. Accepted by design — it is the anti-one-shot discipline the
  import exists for.
- **The gate applies when running interactively (Decision #1, owner-revised 2026-06-11).** When
  `cast-refine-requirements` is invoked headless / HTTP-delegated (a parent dispatching it as a
  child with no human present to give the go-ahead), the agent does NOT wait at the gate: after
  the adversarial reviewer subagent (the sole post-draft pass — the meta-pass was cut,
  Decision #3) it **persists automatically** and records `auto-persisted: non-interactive run`
  in its output contract. Headless invocation is therefore explicitly **supported**, not a
  non-goal: the anti-one-shot discipline holds wherever a human is present, and an
  unattended/orchestrated run never hangs waiting for a go-ahead that cannot come.

**8. Port the `/office-hours`-style adversarial reviewer subagent — owner-confirmed optional, in scope.**
- New step run **before the HARD-GATE draft presentation** (Decision #2): the meta-pass having
  been cut, the reviewer is the single adversarial pass and must run on the draft *before* the
  user's final go-ahead, so the user reviews — and signs off on — the version that actually gets
  persisted. (Originally numbered Step 3.0b "after Phase 2, before persist"; reordered to precede
  the Step 2.1 final draft presentation / go-ahead.)
- Dispatch a **fresh-context subagent via the Claude Code Agent tool** (general-purpose; NOT
  Diecast HTTP delegation — see design review) whose prompt contains ONLY the draft document (not
  the conversation). It scores 1-10 on five dimensions — Completeness / Consistency / Clarity /
  Scope / Feasibility — and returns specific issues per dimension scoring <7.
- Convergence guard: fix the <7 issues, re-dispatch; **max 3 iterations**, then proceed with
  remaining issues logged to Open Questions.
- **Stub-skip (Decision #6):** skip the reviewer entirely when the input is a vague-stage stub
  (<200 words / Stage-1 per the Step 1.3 stage table) and surface "review skipped: stub-sized
  input" exactly like the fail-soft note. A thin stage-1 draft is thin by design; a 3-iteration
  fresh-context review is wasted dispatch there. Reuses the stage detection already in Step 1.3.
- **Fail-soft:** if the subagent errors or is unavailable, note "independent review skipped:
  <reason>" to the user and proceed — the reviewer must never block refinement. (Note: on a
  skipped/failed reviewer run there is now no adversarial pass at all — see activity 5
  tombstone.)
- Issues that need the user (not the agent) to resolve fold into the remaining question budget
  or Open Questions; do not exceed the 7-question budget on the reviewer's behalf.
- Keep the reviewer prompt compact (~40 lines, inline in the agent prompt) — it is a rubric,
  not an essay.

**9. Regenerate skills, add the prompt-pinning test, and keep existing tests green.**
- The user-facing skill is generated: run `bin/generate-skills` after the edits so
  `~/.claude/skills/cast-refine-requirements/SKILL.md` picks up the new prompt (pre-existing
  files are backed up to `.cast-bak-<timestamp>/` automatically).
- **New prompt-pinning test (Decision #5):** add `tests/test_phase1b_prompt_pins.py` asserting
  the new anchors are present after edits and survive `generate-skills` regen — `## Decisions` in
  `templates/cast-spec.template.md`, `scope_mode` in the agent prompt, the HARD-GATE sentence,
  the reviewer rubric heading (the five dimensions), and the evidence-quoting mandate. Mirrors
  the `test_b1_domain_search.py` pattern; it is the automated tripwire against silent regression
  and regen drift. (No meta-pass anchor — that import was cut, Decision #3.)
- `tests/test_b1_domain_search.py` pins prompt content (the "Domain Web Search" section must
  survive; numeric question caps must NOT reappear — Issue #14). The edits in activities 1-8
  must not touch Step 2.2.1; run the test to prove it.

### Verification

Re-refine **3 real writeups** spanning the stage spectrum (pick from existing
`goals/*/requirements.human.md` across the workspaces at execution time — one <200-word vague
idea, one specific feature, one detailed near-complete spec) and assert:

1. **Stage-adaptive:** the vague writeup gets JTBD framing and is NOT padded to full EARS depth;
   the near-complete one gets EARS + gap analysis. (Confirms activity 1.)
2. **Scope mode:** each run states a detected mode with quoted signal words; at least one run's
   front-matter carries `scope_mode`. (Activity 4.)
3. **Decisions populated:** at least one run resolves a fork via AskUserQuestion and its output
   contains a dated `| Date | Chose | Over | Because |` row matching that answer, captured at
   answer-time. (Activity 3.)
4. **Reviewer is the adversarial pass:** the reviewer subagent surfaces ≥1 real contradiction /
   unmeasurable constraint / scope-or-feasibility issue across the three runs, and each finding
   is visibly either fixed or logged to Open Questions — none silently dropped. (Activities 5
   tombstone + 8. Replaces the former "meta-pass bites" item, which was cut with the meta-pass.)
5. **Evidence quoting:** every confidence rating in the Step 2.1 presentations carries a
   verbatim quote. (Activity 6.)
6. **HARD GATE + ordering:** on the cleanest writeup (all sections medium+ after the draft), the
   agent still runs the reviewer, *then* presents the draft and waits before writing — i.e. the
   user sees the post-reviewer version. (Activities 7 + 8, Decision #2.)
7. **Reviewer runs, skips stubs, and fails soft:** the reviewer returns five 1-10 scores on at
   least one run; on the <200-word stub it is skipped with the "review skipped: stub-sized input"
   note (Decision #6); on one run, simulate unavailability (deny the Agent tool call) and confirm
   refinement completes with the "review skipped" note. (Activity 8.)
8. **No regressions + new pins green:** `bin/cast-spec-checker <output>` exits 0 on all three
   re-refined files AND on one pre-existing spec from `docs/specs/` (template change is additive);
   `pytest tests/test_b1_domain_search.py tests/test_phase1b_prompt_pins.py` passes;
   `bin/generate-skills --dry-run` lists the agent without error. (Activity 9, Decision #5.)

### Design review

- **Spec consistency — template is the contract:** `templates/cast-spec.template.md` is the
  canonical shape "enforced by cast-spec-checker" and shared with `cast-update-spec`. The
  `## Decisions` addition MUST be additive-optional (checker requires only its four sections —
  confirmed against `bin/cast-spec-checker` REQUIRED_SECTIONS / R1 at planning time, which only
  asserts required-section *presence* and never rejects extra H2s), and the shape doc
  `agents/cast-spec-checker/cast-spec-checker.md` gets the one-line recognition note.
  Verification item 8 pins this (now also automated via `test_phase1b_prompt_pins.py`). No
  `/cast-update-spec` run is needed: the template + checker doc *are* the behavior contract for
  this surface, and no `docs/specs/_registry.md` entry covers the refinement agent (the registry
  was checked — closest specs are runtime/delegation contracts, not this).
- **Architecture — reviewer dispatch mode:** the reviewer runs as a **Claude Code Agent-tool
  subagent**, not a Diecast HTTP-dispatched child. Rationale: `cast-refine-requirements` runs
  interactively in the user's session (often as a top-level skill with no run_id), has no
  `allowed_delegations` in its `config.yaml`, and the office-hours pattern's entire value is
  *fresh context seeing only the document* — which the Agent tool gives for free, fail-soft,
  with no new agent directory and no server dependency. Flag for later: if the reviewer proves
  valuable, promote it to a registered `cast-requirements-reviewer` agent (and consider its
  relationship to Phase 3a's `cast-requirements-checker`, which reviews the *HTML render for
  comprehension* — a different rubric; keep them separate in v2).
- **Architecture — reviewer runs before the gate (Decision #2):** with the meta-pass cut, the
  reviewer is the only post-draft mutation. It MUST run before the HARD-GATE draft presentation
  so the user signs off on the persisted version, not a pre-review draft.
- **Error & rescue:** the load-bearing fail-soft / zero-silent-failure rules are: reviewer
  unavailability never blocks (activity 8), reviewer findings are never silently dropped
  (activity 8), and low-confidence sections always surface in Open Questions (activity 2). Each
  has a matching verification item. (The former "meta-pass findings never dropped" rule is
  retired with the meta-pass — Decision #3.)
- **Prompt-size watch:** the prompt is 435 lines today; the remaining activities (3, 4, 6, 7, 8)
  add roughly 90-120 lines (the meta-pass cut removes ~30). Integrate into existing steps (1.3,
  1.5, 2.1, 2.4, 3.x) rather than appending parallel sections, and keep the reviewer rubric
  compact. If the file passes ~650 lines, stop and trim before adding more — instruction-following
  degrades with bloat.
- **Naming:** `## Decisions` (matches the high-level plan's wording), front-matter key
  `scope_mode`, scope-mode vocabulary identical to `cast-detailed-plan`'s Garry Tan table.

## Build Order

Single sub-phase — internal edit order only (one session):

```
[1,2 verify/sharpen] ─► [4 scope-mode] ─► [6 evidence-quoting] ─► [3 Decisions + template]
        ─► [8 reviewer subagent] ─► [7 HARD GATE: reviewer-then-present] ─► [9 regen + pins + tests]
        ─► verification re-refinements (3 writeups)
```

Rationale: detection edits (4) before presentation edits (6) before output-shape edits (3); the
reviewer (8) is wired in *before* the HARD GATE (7) so the gate presents the post-reviewer draft
(Decision #2); the meta-pass (5) is cut (Decision #3); regen + the new pinning test (9) last.

## Design Review Flags

| Flag | Action |
|------|--------|
| Template change ripples to `cast-update-spec` outputs | Keep `## Decisions` optional-additive; verify checker on a pre-existing spec (verification 8) + automated pin (Decision #5) |
| Reviewer dispatch mode (Agent tool vs HTTP child) | Agent-tool subagent in v2; revisit registration if it earns its keep |
| Prompt bloat risk (435 → ~555 lines after meta-pass cut) | Integrate into existing steps; hard stop + trim at ~650 |
| Playbook 01 overstates the import count (2 of 6 already present; meta-pass cut → 3 of 6 land) | Recorded here; carry into `decisions_so_far` for later sub-phase planners so Phase 2/4 don't re-plan them |
| HARD GATE changes documented zero-interaction behavior; interactive-only, headless auto-persists (Decision #1, owner-revised) | Intentional (Decisions #1, #2); one confirm minimum on the post-reviewer draft when interactive; headless runs auto-persist after the reviewer and record `auto-persisted: non-interactive run` — watch for gate fatigue in real use |
| Meta-pass cut → no adversarial pass when reviewer fail-softs | Accepted (Decision #3); evidence-quoting + Open-Questions invariant still hold every run |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt bloat dilutes instruction-following (the agent starts skipping steps) | Med | Integrate edits into existing steps; ~650-line ceiling; meta-pass cut reduces additions; verification runs 1-8 double as an instruction-following smoke test |
| Reviewer subagent adds latency/cost to every refinement | Med | Max 3 iterations, re-dispatch only on <7 scores, fail-soft skip, and stub-skip for <200-word / Stage-1 inputs (Decision #6) |
| No adversarial pass at all when the reviewer fail-softs (meta-pass cut, Decision #3) | Low-Med | Accepted; "review skipped" note surfaced; evidence-quoting (activity 6) + zero-silent-failure Open-Questions invariant (activity 2) still run every time |
| Question-budget contention (scope-mode confirm + Phase 2's future classification confirm + ordinary clarifications all share 7) | Low-Med | Scope-mode asks only when signals conflict; noted in "Position in Overall Plan" so the Phase 2 planner budgets for it |
| Gate fatigue: HARD GATE annoys users on trivially-clear writeups | Low | Gate applies to interactive runs only (headless auto-persists, Decision #1); minimum interaction is exactly one draft go-ahead on the post-reviewer draft; if real use shows fatigue, soften to "gate only when any section < high" as a follow-up |
| Two checkouts drift (`/data/workspace/diecast` vs `/home/sridherj/workspace/diecast`) — both currently identical for this agent | Low | All Phase 1b edits land in the external project checkout per goal config; the owner reconciles to main as usual |

## Open Questions

**None blocking.** All planning-time forks were resolved: the optional-ports scope was confirmed
by the owner (both included, 2026-06-11); Decisions-section placement, front-matter key, and
reviewer dispatch mode are decided above with rationale. Plan review (2026-06-11) resolved six
further forks — see the Decisions appendix. One watch-item (not a blocker): whether the HARD
GATE's mandatory draft-review feels like friction in daily use — revisit after the verification
re-refinements.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `templates/cast-spec.template.md` (canonical shape, checker-enforced) | full template; new optional `## Decisions` | None — additive; checker requires only its 4 sections, R1 never rejects extra H2s (verified) |
| `docs/specs/_registry.md` | full registry scan | No registered spec covers the refinement agent's I/O; runtime/delegation specs unaffected (no HTTP delegation added) |
| `agents/cast-spec-checker/cast-spec-checker.md` (shape rules doc) | section rules | None — gets a one-line additive note recognizing `## Decisions` |

## Suggested Revisions to Prior Sub-Phases

None — first wave. For the parent's `decisions_so_far` digest: (a) two of Playbook 01's six
imports were already present in the agent prompt — stage-adaptive framework and exit
conditions; (b) the adversarial meta-pass import was **cut** by plan review (reviewer subagent
subsumes it); (c) `## Decisions` table shape is `| Date | Chose | Over | Because |`, placed
between Out of Scope and Open Questions, populated by **answer-time buffering** — Phase 4's
versioning should consume this shape, and Phase 1's parser should treat `Decisions` as a known
optional block; (d) front-matter gains `scope_mode`; (e) the reviewer subagent is
Agent-tool-dispatched, unregistered, runs before the HARD GATE, skips <200-word stubs, in v2;
(f) the HARD GATE applies on interactive runs only — headless / HTTP-delegated runs are
explicitly supported and auto-persist after the reviewer subagent, recording
`auto-persisted: non-interactive run` in the output contract (Decision #1, owner-revised).

## Decisions

- **2026-06-11T16:34:57Z — Issue #1: When there's no interactive user (headless/HTTP-delegated), how should the HARD GATE behave?** — Decision (owner override, 2026-06-11): The gate applies only when running interactively. On headless / HTTP-delegated invocation (no human to give the go-ahead), the agent persists automatically after the reviewer subagent (the sole adversarial pass — meta-pass cut per Decision #3) and records `auto-persisted: non-interactive run` in its output contract; headless invocation is explicitly supported. Rationale: keeps the anti-one-shot discipline where a human is present, but never hangs an unattended/orchestrated run waiting for a go-ahead that cannot come. (Supersedes the earlier "unconditional gate, headless is a non-goal" resolution recorded at this timestamp.)
- **2026-06-11T16:34:57Z — Issue #2: The HARD GATE shows the draft at Step 2.1 but the post-processing passes mutate it before persist — how should they be ordered?** — Decision: Run the reviewer (and any post-draft mutation) BEFORE the final draft presentation/go-ahead; reorder Build Order so the user signs off on the persisted version. Rationale: a gate over a version the user never sees again is not a real gate.
- **2026-06-11T16:34:57Z — Issue #3: The adversarial meta-pass and the reviewer subagent have overlapping rubrics — how to handle the duplication?** — Decision: Drop the meta-pass (activity 5) entirely; the fresh-context reviewer is the sole adversarial pass. Rationale: the rubrics overlap on consistency/measurability/feasibility; running both duplicated work and fed the #1 prompt-bloat risk. Accepted consequence: a fail-softed reviewer leaves no adversarial pass on that run (tracked in Key Risks).
- **2026-06-11T16:34:57Z — Issue #4: Activity 3 reconstructs the Decisions table from session memory at persist time — risk of fabricated rationale?** — Decision: Buffer each decision at answer-time ({date, chose, over, because} appended when the fork resolves) and render the table verbatim at persist; date from the harness currentDate. Rationale: end-of-session reconstruction confabulates the Over/Because fields; mirrors cast-plan-review's own B2 buffer-at-decision-time pattern.
- **2026-06-11T16:34:57Z — Issue #5: New behaviors are verified only by manual re-refinement — add an automated prompt-pinning test?** — Decision: Add tests/test_phase1b_prompt_pins.py asserting the new anchors (## Decisions in the template, scope_mode, HARD-GATE sentence, reviewer rubric heading, evidence-quoting mandate; no meta-pass anchor) are present and survive generate-skills regen. Rationale: cheap automated tripwire against silent regression and regen drift, matching the test_b1 pattern and the well-tested-is-non-negotiable bar.
- **2026-06-11T16:34:57Z — Issue #6: The 'skip reviewer for <200-word stubs' mitigation is in the risk table but not encoded in activity 8 — make it a firm rule?** — Decision: Encode the stub-skip in activity 8: skip the reviewer for <200-word / Stage-1 inputs (per the Step 1.3 stage table) with a "review skipped: stub-sized input" note. Rationale: aligns the build spec with the stated mitigation and cuts the most wasteful dispatch on intentionally-thin drafts; reuses existing stage detection.
