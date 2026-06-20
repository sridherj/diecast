# Exploration Pipeline N×M: Sub-Phase 5 — End-to-End Integration & Parity Validation

## Overview

This is the final, smallest sub-phase: prove the whole pillar works end-to-end on a **real**
goal and produce a head-to-head comparison against today's `cast-explore` so the user can make
the eventual parallel→merge call. **No new feature work** — every prior sub-phase (entrypoint skill
→ interactive Phase-1 + hat-matrix → `cast-explore-workflow/workflow.py` N×M fan-out via
`cast-hat-researcher` → per-step `cast-playbook-synthesizer` → md artifacts →
`exploration_render_service` WHAT/HOW/checker → `exploration.html` → dual viewer (2b) + commenting
(3b)) is now built. Phase 5 wires nothing new; it **runs, verifies, and compares**.

The work is three threads run over one real goal: (1) an unattended end-to-end run after step
approval, (2) a SC-001…SC-009 verification matrix with a concrete check per criterion, and (3) a
side-by-side parity comparison of the N×M output against a `cast-explore` run on the SAME goal,
captured as durable parity notes for the merge decision. A load-bearing sub-check rides along:
confirming the md substrate stays byte-compatible with `cast-high-level-planner`'s glob contract.

## Operating Mode

**HOLD SCOPE** — requirements declare `scope_mode: hold` (frontmatter) and the Decisions table
fixes "Workflow ships **in parallel** to cast-explore… user merges later." Phase 5 is pure
verification + comparison against a fixed, fully-enumerated SC-001…SC-009 checklist. No scope
expansion (no new hats, no merge/cutover, no stable anchor-ids — all explicitly Out of Scope), no
reduction (every one of the nine SCs must be checked, none deferred). Maximum rigor on a fixed
surface: that is exactly HOLD SCOPE.

## Position in Overall Plan

```
Phase 1a ─► Phase 2a ─► Phase 3a ─┐
(spike)    (hat agent) (Workflow) │
                                  ▼
Phase 1b ─► Phase 2b ─► Phase 3b ─► Phase 4 ─► [Phase 5 ◄ YOU ARE HERE]
(spike)    (viewer)   (commenting)  (render)    (e2e + parity)
```

Phase 5 sits at the tail of the critical path. It is the only sub-phase that exercises **all** prior
outputs simultaneously, on a single real goal, and it is terminal — nothing depends on it except the
user's merge decision.

## Depends On (from prior plans)

Phase 5 consumes the concrete interfaces below. If any is absent or off-contract, Phase 5 is blocked
and the gap belongs to that earlier phase (see Suggested Revisions if a contract is wrong, not just
missing).

| From | Interface Phase 5 exercises |
|------|------------------------------|
| Entrypoint (3a, `[PENDING 1a]` seam) | Skill/command that launches `agents/cast-explore-workflow/workflow.py` after step approval, passing `(approved_steps, hat-matrix)` as args |
| Interactive Phase-1 (3a) | Relevance gating emits the `hat-matrix` `{goal_slug, goal_context, steps:[{nn, slug, name, hats:[hat_id…]}]}`; always-on hats `contrarian`, `first-principles`, `90-10` never gated |
| `cast-hat-researcher` (2a) | Per-cell note at `exploration/research/{NN}-{step-slug}-{hat-id}.ai.md`, exactly one hat block selected; hat_id vocabulary literal (`90-10`, `first-principles`, `contrarian`, + 5 gateable) |
| `cast-playbook-synthesizer` (3a, unchanged) | One playbook per step at `exploration/playbooks/{NN}-{step-slug}.ai.md`; synthesizes from surviving hat notes |
| Workflow (3a) | `summary.ai.md`; concurrency cap `min(16, cores−2)`; failed cell → `null` + logged (FR-016) |
| `exploration_render_service` + agents (4) | `cast-exploration-what` → `cast-exploration-how` → `cast-exploration-render-checker`; atomic `goals/{slug}/exploration/exploration.html` with AUTO-GENERATED + source-digest + served-by envelope |
| Dual viewer (2b) | `.html` rendered via `<iframe srcdoc sandbox="allow-scripts allow-popups">`; `kind` discriminator; `api_artifacts.py:52` gate + `api_goals.py get_phase_tab` glob admit `.html` |
| HTML commenting (3b) | postMessage-to-host bridge → same-door create endpoint; `artifact_ref="exploration/exploration.html"`; `anchor_space='render'`; verbatim-substring relocation |

---

## Sub-phase 5: End-to-End Integration & Parity Validation

**Outcome:** On one real goal, the full pipeline runs unattended after step approval; all nine
SC-001…SC-009 are verified with recorded evidence; the md substrate is confirmed byte-compatible
with `cast-high-level-planner`; and a durable side-by-side parity document (N×M vs `cast-explore` on
the same goal) exists for the user's parallel→merge decision.

**Dependencies:** Phase 4 (which transitively requires 3a, 3b, 2b — the whole pipeline).

**Estimated effort:** 1–2 sessions. (Activity A is mostly wall-clock for two autonomous runs;
B–E are focused verification + writing, not building.)

**Verification (this sub-phase is itself "done" when):**
- The SC verification matrix (Activity B) shows a PASS with cited evidence for every one of
  SC-001…SC-009 — or a documented, attributed FAIL routed to the owning phase.
- `byte-compat-check.md` (Activity C) confirms `cast-high-level-planner`'s three globs resolve over
  the new run with no shape regression.
- `parity-notes.md` (Activity D) exists with the four comparison axes filled (playbook quality,
  angle sharpness, cost/time, recommended-disposition) plus the raw artifacts of both runs retained.
- Auto-review (Step 10) of THIS plan completes (or is recorded as rerun-manually).

### Key activities

**A. Two runs on one real goal (the comparison substrate).**
- Pick ONE real goal with a codebase-light, decomposable scope (3–5 steps keeps the matrix legible
  and cost bounded; recall the ungated worst case is `N×M_total` = e.g. 5×8 = 40 cells). Prefer an
  existing exploration-phase goal so step decomposition is realistic, NOT a toy.
- **Run 1 (new N×M pipeline):** drive interactive Phase-1 (intent → decompose → approve steps →
  compute hat-matrix) via the entrypoint skill, then let the Workflow run **unattended** — no manual
  intervention after approval (this IS SC-009). Capture wall-clock start/end and, if available from
  run records, token/cost. Retain the full `exploration/` tree + `exploration.html`.
  → Delegate the launch to the **Phase-3a entrypoint skill/command** (the `[PENDING 1a]` seam,
    resolved in execution). Do NOT hand-roll child delegation — US2 requires the Workflow tool.
- **Run 2 (baseline):** run `cast-explore` on the SAME approved goal/steps.
  → Delegate: dispatch the **`cast-explore`** agent on the same goal.
  → **Collision mechanics (reviewer correction):** `cast-explore` invoked from a Diecast goal dir
    HARDCODES writing to `<output-dir>/exploration/` (`cast-explore.md:73` — "write ALL artifacts
    directly into `<output-dir>/exploration/`"). It will NOT honor an ad-hoc `exploration-baseline/`
    target, so "write its output to a scratch copy" is not achievable by instruction alone. Use ONE
    of these collision-safe strategies and name which in `parity-notes.md`:
    (i) **throwaway sibling goal** — create a second goal dir (same slug + `-baseline`) and run
        `cast-explore` there, giving it its own `exploration/`; OR
    (ii) **sequence + snapshot** — run `cast-explore` FIRST, `cp -r` the resulting `exploration/` to a
        retained `exploration-baseline-snapshot/`, THEN run the N×M pipeline (which overwrites
        `exploration/`). Snapshot is the durable Run-2 evidence.
    Strategy (i) is preferred (cleaner provenance, both trees live simultaneously). Verify the two
    trees are side-by-side and intact BEFORE any Activity B/D read touches them.
- Keep both runs' artifacts under version control or a retained scratch dir — they are the evidence
  base for Activities B and D and must survive the session.

**B. SC verification matrix (the nine-criterion gate).** For each SC, run the concrete check from
the table below and record PASS/FAIL with the literal evidence (a count, a quoted line, a checker
JSON verdict, a screenshot/DOM assertion). Write the result table into `sc-verification.md`.

| SC | Criterion | Concrete check (the evidence to record) |
|----|-----------|------------------------------------------|
| SC-001 | One research note per applicable hat per step | **Persist the emitted hat-matrix JSON as the ground-truth expectation** (it is the Workflow arg from US11/FR-007); then `ls exploration/research/*.ai.md \| wc -l` **==** `Σ M_applicable(step)` derived from that saved matrix. The expected set is `{(nn,slug,hat_id)}` from the matrix MINUS any cells FR-016 dropped to `null` (read the Workflow log for dropped cells); assert the **exact filename set** matches, not just the count — a count match can hide a mis-slugged file. Record expected-set, actual-set, the set-diff (empty on PASS), and per-step breakdown. Exclude any `-code.ai.md` files from the count (cast-code-explorer notes are not hat notes) |
| SC-002 | No hat-agent prompt contains another hat's content | Prompt inspection: open 2–3 `cast-hat-researcher` invocation records (or re-derive from the agent + hat_id), confirm exactly ONE hat block present, no sibling hat framing. Quote the selected-hat header + assert absence of others |
| SC-003 | 90/10 note per step; First Principles note has no 80/20 content | File inspection: confirm a `*-90-10.ai.md` exists for every step (count == N); grep the `*-first-principles.ai.md` notes for 80/20 / "Pareto" / "20% of effort" language → must be ABSENT. Quote one 90/10 note's verdict line (RECOMMENDED CUT \| CUT WITH CAUTION \| DO NOT CUT) to confirm note-shape |
| SC-004 | One opinionated playbook per step | `ls exploration/playbooks/*.ai.md \| wc -l` **==** N. Record count + confirm 1:1 step↔playbook slug mapping |
| SC-005 | Polished exploration HTML passes the 4-criteria render-checker | Run / read the `cast-exploration-render-checker` verdict JSON for `exploration.html`. Record the bare-JSON verdict; confirm all 4 FR-017 criteria pass (every applicable hat visible per step; per-step POV legible zero-click; hats DISTINCT not blended; not AI-slop) |
| SC-006 | Viewer shows both `.html` report and `.md` artifacts in the phase tab | UI check: open the exploration phase tab in the running cast-server; confirm `exploration.html` renders in the srcdoc iframe AND the `.md` artifacts list beside it. Record a DOM/visual assertion (iframe present with `kind="html"`; md viewer present) |
| SC-007 | Selecting text in an HTML artifact yields a comment via the same-door API | End-to-end: in the viewer, select text inside `exploration.html`, "+ Comment", submit; confirm a comment row persists with `artifact_ref="exploration/exploration.html"`, `anchor_space='render'`, and the `{quoted_text, section_hint, body}` shape. Record the created row (or API response) |
| SC-008 | refined-requirements HTML viewable in the dual viewer | UI check (consumer #2): confirm the existing `refined_requirements.html` for this goal surfaces in the viewer, not only on `/render`. Record presence |
| SC-009 | Full exploration completes without manual intervention after step approval | The Run-1 observation from Activity A: zero human input between step approval and terminal `summary.ai.md` + `exploration.html`. **Operationalize "no manual intervention"** so it isn't a subjective recollection: after step approval, the run must reach terminal state with (a) zero AskUserQuestion / human-gate prompts emitted by the Workflow or its children, and (b) zero manual edits to the goal dir. Record the run timeline, the terminal `.output.json` `status==completed`, and an explicit "human-input events after approval: 0" line. If the run did pause for any input, SC-009 is a FAIL routed to Phase 3a (the Workflow is supposed to be non-interactive per US2/Constraints), not a Phase-5 note |

- Where a check needs the running server (SC-006/007/008), use the standing cast-server UI.
  Per memory [[project_diecast_prototype_no_browser_visual_gates]]: if this run is autonomous and
  cannot drive Chrome, record a **static structural verdict** (assert the iframe/comment-row
  server-side) plus a **human-eyeball carry-forward** note — never a silent pass, never a hard block.
  Surface the degraded gate with a machine-readable flag [[feedback_surface_dont_suppress]].
- A FAIL is NOT a Phase-5 defect to fix here — Phase 5 builds nothing. Attribute each FAIL to its
  owning phase (e.g. SC-005 fail → Phase 4; SC-001 miscount → Phase 3a gating) and record it as a
  routed regression, not a silent patch.

**C. Byte-compatibility with `cast-high-level-planner` (US6 / FR-009 contract).**
- The planner reads three globs (confirmed in `cast-high-level-planner.md`, the "Input Sources →
  Optional (enriches plan quality)" section — verify the exact line at execution time; it had
  drifted from the `:115-117` cited here): `exploration/research/*.ai.md`,
  `exploration/playbooks/*.ai.md`, `exploration/summary.ai.md`.
- **Contract-severity caveat (reviewer correction):** in the planner these three are listed under
  **Optional**, not a hard input — the planner explicitly degrades to "a higher-level plan with more
  open questions" when exploration is absent. So a byte-compat regression does NOT crash the planner;
  it silently *degrades plan quality*. That makes Activity C's value **higher**, not lower (a silent
  degradation is exactly what no one would catch), but it reframes a FAIL: the symptom is "planner
  ingested but produced a thinner plan / ignored the fan-out," not "planner errored." The optional
  confirmation dispatch below must therefore inspect plan QUALITY for evidence the research was used,
  not merely assert "no missing-artifact error."
- **Subtlety to verify explicitly:** the research glob now matches **M notes per step** instead of
  the old 1-per-step (`cast-explore` wrote `{NN}-{step}.ai.md`; new writes `{NN}-{step}-{hat-id}.ai.md`).
  The planner "skims playbooks for impact ratings… don't re-read all research" (`:130`) — so the
  research-fan-out is additive to a glob it already treats as a bag. Confirm: (1) all three globs
  resolve non-empty over Run 1; (2) `playbooks/*.ai.md` and `summary.ai.md` keep the **same shape**
  `cast-explore` produces (the synthesizer is unchanged per US5, and summary format is Out-of-Scope
  to change); (3) no path moved. Record the glob resolution + a diff of the playbook/summary *shape*
  (headings, not content) between Run 1 and Run 2. Write to `byte-compat-check.md`.
- Optional but cheap confirmation: dispatch `cast-high-level-planner` (read-only intent) against
  Run 1's goal dir and confirm it ingests without error. → Delegate: **`cast-high-level-planner`**
  on the Run-1 goal; verify it produces `plan.collab.md` without a missing-artifact error AND that
  the plan reflects exploration content (cite ≥1 playbook impact rating or research insight the
  planner surfaced) — because the globs are Optional inputs, a silent "ingested but ignored the
  fan-out" is the real failure mode here, not a hard error. A thin plan that never references the
  M-per-step research is the byte-compat regression to catch.

**D. Side-by-side parity comparison (the merge-decision deliverable).** Compare Run 1 (N×M) vs
Run 2 (`cast-explore`) on the SAME goal across four axes; write `parity-notes.md`.

- **Fairness guardrails (reviewer addition — keeps this from reading as cherry-picked vibes):**
  - **Non-isomorphic hat sets, stated up front.** `cast-explore` researches 7 angles; the N×M
    pipeline runs up to 8 hats including the NEW first-class 90/10 hat that has no `cast-explore`
    equivalent (it was a buried sub-bullet). The comparison holds goal + approved steps constant but
    is NOT a like-for-like angle map. State the hat↔angle correspondence table explicitly and mark
    90/10 as "new, no baseline counterpart" rather than forcing a false pairing.
  - **Confound disclosure.** Both runs draw on live web search (nondeterministic) and the same model
    family; differences may owe to run-to-run variance, not architecture. Note this caveat; where a
    quoted before/after is the *whole* evidence for an axis, prefer 2–3 examples over one so a single
    lucky/unlucky draw doesn't carry the verdict.
  - **Pre-commit the win condition.** Before reading the notes, write down what would count as
    "isolation produced a sharper take" (e.g. the contrarian note names a concrete failure mode the
    `cast-explore` contrarian section hedged or omitted). Judge against that, not post-hoc.
  Compare across four axes:
- **Playbook quality** — per step, compare the two pipelines' playbooks. Is the N×M playbook more
  opinionated / more actionable / better-sourced? Note where isolated-context research surfaced an
  angle `cast-explore`'s single-context pass missed (the whole thesis:
  `web-researcher-angle-fanout.md` — "contrarian gets watered down… first principles contaminated").
- **Angle sharpness** — the core hypothesis. Inspect the `contrarian` and `first-principles` notes
  from Run 1 vs the corresponding angle sections inside `cast-explore`'s single per-step note. Did
  isolation produce sharper, less-primed takes? Quote a concrete before/after. Confirm the new
  **90/10 hat** delivers a clean-context cut proposal that `cast-explore` only buried as a sub-bullet.
- **Cost / time** — wall-clock and (if available) token/cost for both runs. Note the N×M premium and
  whether relevance gating kept it bounded (live cell count vs `N×M_total`). This is the explicit
  trade the user weighs at merge.
- **Recommended disposition (advisory only, NOT a decision)** — a one-paragraph read of whether the
  quality gain justifies the cost premium, framed as input to the user's parallel→merge call. Per
  the Decisions table this stays parallel; Phase 5 does NOT cut over [[feedback_ask_with_recommendation]].

**E. Wrap-up.**
- → Delegate: **`/cast-wrap-up`** to capture session learnings + any spec drift discovered during
  verification. Review for accuracy.
- Append the ledger summary (file path + SC-matrix shape + parity method + artifacts produced) so
  the cumulative decisions doc closes Round 5.

### Design review

- **Spec consistency (US6 / FR-009):** Phase 5 is the *enforcement point* for the
  `cast-high-level-planner` byte-compatibility contract — Activity C exists precisely so the
  research-glob fan-out (1→M files) doesn't silently break a downstream consumer. ✓ Covered. No
  `/update-spec` needed: Phase 5 changes no behavior; spec updates for the new behaviors already
  landed in their owning phases (2b updated `cast-requirements-render.collab.md`; 3a/4 are internal).
- **Spec consistency (roundtrip):** comments on `exploration.html` are **feedback only** — write-back
  to exploration md is Out of Scope (plan Spec References + `cast-requirements-roundtrip.collab.md`).
  SC-007's check must assert the comment row persists, NOT that it round-trips into the md. ✓ Flagged
  so the verifier doesn't over-test.
- **Architecture:** Run 2 must NOT overwrite Run 1's `exploration/` (both pipelines write to the same
  canonical paths). Activity A mandates a separate baseline location — a real collision risk worth
  the callout, not a hypothetical. ✓ Mitigated in-activity.
- **Error & rescue (surface, don't suppress):** FR-016 failed-cell isolation should be *observed*, not
  forced, in a real run; but if Run 1 happens to drop a cell to `null`, SC-001's `Σ M_applicable`
  count must account for it (count surviving cells, log the null) rather than reading as a FAIL.
  Record dropped cells with the machine-readable flag, never suppress
  [[feedback_surface_dont_suppress]]. ✓
- **Security:** no new surface — Phase 5 runs existing pipelines and inspects their output. The only
  I/O is reading goal-dir artifacts and the same-door comment API already hardened in 3b. No flags.

### Suggested Revisions to Prior Sub-Phases

None. The Round 1–4 contracts (entrypoint seam, hat-matrix shape, `cast-hat-researcher` I/O, unchanged
synthesizer, `exploration_render_service` envelope, dual-viewer `kind` seam, postMessage comment
bridge + `artifact_ref`) are each directly exercisable by a Phase-5 verification check without
modification. The one contract Phase 5 leans on hardest — the `cast-high-level-planner` three-glob
read — is satisfied by the unchanged playbook/summary shape (US5) plus an additive research glob, so
no upstream revision is required. **If** Activity C surfaces a real shape regression in
`playbooks/*.ai.md` or `summary.ai.md`, that is a Phase-3a defect (the synthesizer was supposed to be
unchanged) and would be routed back there — but that is a contingent finding, not a known revision.

## Build Order

Single sub-phase. Internal activity order: **A** (two runs) **→** B, C, D run in parallel over the
shared artifact base **→** E (wrap-up) last.
- Run 1 and Run 2 may execute in parallel **only under collision strategy (i)** (disjoint goal dirs).
  Under strategy (ii) they MUST be sequenced (Run 2 → snapshot → Run 1) because both write the same
  `exploration/`. The diagram below assumes strategy (i).

```
A.Run1 (N×M, unattended) ─┐
                          ├─► [B: SC matrix] ─┐
A.Run2 (cast-explore)  ───┘   [C: byte-compat]├─► E: wrap-up + ledger
                              [D: parity notes]┘
```

**Critical path:** A.Run1 → B (SC-009 is observed during Run 1; SC-001/005 need Run 1 complete) → E.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5 / Activity A | Run 2 (`cast-explore`) overwriting Run 1's canonical `exploration/` paths | Write baseline to a disjoint location; verify both trees intact before B/D |
| 5 / Activity B | Autonomous run may not be able to drive Chrome for SC-006/007/008 UI checks | Static structural verdict + human-eyeball carry-forward + machine-readable degraded flag; never silent-pass, never hard-block |
| 5 / Activity B | A failed SC is not a Phase-5 fix | Attribute + route the regression to the owning phase; Phase 5 builds nothing |
| 5 / Activity C | Research glob now matches M files/step (was 1) | Explicitly confirm planner's bag-glob semantics + unchanged playbook/summary shape |
| 5 / Activity D | "Recommended disposition" could be read as a cutover decision | Frame strictly as advisory input to the user's parallel→merge call |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| The two runs' artifacts collide on shared canonical paths, corrupting the comparison base | High | Activity A writes baseline to a disjoint dir; verify both trees before any verification reads them |
| N×M token cost on the chosen real goal balloons past a reasonable run | Med | Pick a 3–5 step goal; rely on relevance gating (always-on = 3 hats) + concurrency cap; record the gated-vs-ungated cell count as parity data, not a blocker |
| Autonomous run can't reach the browser → SC-006/007/008 can't be UI-verified live | Med | Server-side structural assertion + carry-forward human gate per memory; flag the gate as degraded, don't suppress |
| A real-run FAIL tempts an in-phase fix, blurring Phase 5's verify-only mandate | Med | Hard rule: Phase 5 fixes nothing; every FAIL is attributed + routed to its owning phase |
| Parity comparison reads as subjective hand-waving | Low | Force concrete before/after quotes on the contrarian / first-principles / 90-10 axes (the named thesis), not vibes |

## Open Questions

- **Which real goal hosts the validation run?** Needs the user's pick (or an agreed selection rule:
  smallest exploration-phase goal with a realistic 3–5 step decomposition). This is the one input
  Phase 5 cannot self-resolve — flagged for the user. → Ask with a recommendation
  [[feedback_ask_with_recommendation]]: recommend the smallest real exploration-phase goal so cost
  stays bounded while decomposition stays realistic.
- **Cost/token capture fidelity** — if run records don't expose per-run token totals, the cost axis
  of parity falls back to wall-clock + cell-count only. Acceptable degradation; note it in
  `parity-notes.md` rather than blocking.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `refined_requirements.collab.md` (goal) | SC-001…SC-009; US6 md-substrate contract; FR-009/FR-016/FR-017; Out of Scope (no cutover, no write-back) | None — Phase 5 verifies against these, changes none |
| `cast-requirements-render.collab.md` | US4 atomic/served-by stamp, US7 "selectable units, no ids" — applied to `exploration.html` (verified, not changed) | None (the dual-viewer behavior was spec-updated in Phase 2b) |
| `cast-requirements-roundtrip.collab.md` | same-door comment intake — exploration comments reuse the door; write-back is Out of Scope | None — SC-007 asserts persistence only, not round-trip |
| `cast-high-level-planner` agent contract | reads `exploration/research/*.ai.md`, `playbooks/*.ai.md`, `summary.ai.md` (listed as **Optional** inputs; verify exact line at exec — drifted from `:115-117`) | None — additive research glob + unchanged playbook/summary shape; verified in Activity C. Note: these are Optional planner inputs, so a regression DEGRADES plan quality silently rather than erroring (see Activity C caveat) |

## Decisions (cast-plan-review — Round 5, 2026-06-20)

Reviewer decisions from the Phase-5 plan review. All are sharpening edits to a fundamentally sound
verify-only plan; none change scope. The verify-only mandate, SC→check mapping, and spec-consistency
handling were reviewed and found consistent. One item (goal pick) requires the user's call.

- **2026-06-20T00:00:00Z — Is each SC mapped to a concrete, executable check?** — Decision: Yes, with two correctness hardenings applied inline. SC-001 now asserts the exact filename SET against a persisted hat-matrix (count-only can mask a mis-slug) and EXCLUDES `cast-code-explorer`'s `-code.ai.md` notes, which land in the same `research/` dir and would over-count. SC-009 now defines "no manual intervention" as a machine-checkable assertion (zero human-gate events post-approval) routed to Phase 3a on FAIL, not a subjective recollection. Rationale: more edge cases, explicit over clever — a green count that hides a wrong file is the failure mode a verify-only phase exists to catch.
- **2026-06-20T00:00:00Z — Is the byte-compat contract (Activity C) framed correctly?** — Decision: Corrected. The three planner globs are **Optional** inputs (verified in `cast-high-level-planner.md`), not a hard contract; the planner degrades to a thinner plan when exploration is absent rather than erroring. Reframed Activity C + its optional dispatch + the Spec-References cell so a FAIL is detected as "ingested-but-ignored / thinner plan," not "missing-artifact error." Rationale: a silent quality degradation is precisely what nobody catches — this raises Activity C's value and fixes a wrong severity model.
- **2026-06-20T00:00:00Z — Is the run-collision mitigation (Activity A) achievable as written?** — Decision: Corrected. `cast-explore` HARDCODES writing to `<output-dir>/exploration/` (`cast-explore.md:73`), so "write Run 2 to a scratch `exploration-baseline/` copy" is not achievable by instruction. Replaced with two concrete collision-safe strategies — (i) throwaway sibling goal [preferred], (ii) sequence Run-2→snapshot→Run-1 — and reconciled the Build-Order "parallel" claim to strategy (i) only. Rationale: the original mitigation would silently fail and corrupt the comparison base (the High-impact risk the plan itself names).
- **2026-06-20T00:00:00Z — Is the parity method (Activity D) rigorous, not hand-wavy?** — Decision: Strengthened with fairness guardrails: state the non-isomorphic hat sets up front (7 angles vs 8 hats; 90/10 has no baseline counterpart — do not force a false pairing), disclose web-search/model confounds, prefer 2–3 examples per axis over a single quote, and pre-commit the win condition before reading notes. Rationale: this is the merge-decision deliverable; the named risk is "reads as subjective hand-waving," and a pre-committed win condition + confound disclosure is the difference between evidence and a cherry-pick.
- **2026-06-20T00:00:00Z — Is the verify-only (no in-phase fixes) mandate consistent throughout?** — Decision: Confirmed consistent — no change needed. The mandate is stated in Overview, Operating Mode, Activity B, Design Review, Key Risks, and the Design-Review-Flags table, and every FAIL path routes to an owning phase. This is a strength of the plan; recording it so the consistency is not later eroded.
- **2026-06-20T00:00:00Z — [USER INPUT REQUIRED] Which real goal hosts the validation run?** — Decision: DEFERRED to user (the plan's one self-acknowledged un-resolvable input). Reviewer recommendation: pick the smallest existing exploration-phase goal with a realistic 3–5 step decomposition so N×M cost stays bounded while the matrix stays legible; avoid a toy. Flagged here so it is not silently defaulted at execution time. [[feedback_ask_with_recommendation]]
- **2026-06-20T00:00:00Z — Claude skill/agent delegation check** — Decision: No gap. Every activity that should delegate already names its agent explicitly (`cast-explore`, the Phase-3a entrypoint skill, `cast-exploration-render-checker`, `cast-high-level-planner`, `/cast-wrap-up`). The plan correctly forbids hand-rolled child delegation per US2. No missing-delegation issue to raise.
