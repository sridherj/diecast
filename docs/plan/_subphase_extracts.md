# Sub-Phase Extracts — product-revamp-diecast (for reconciliation)

> Mechanical extracts: per-plan outline + exported contracts + suggested revisions.
> Rich per-phase decision summaries live in product-revamp-diecast-decisions-so-far.md.

---

## phase1-keystone  (source: 2026-06-11-product-revamp-diecast-phase1-keystone.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (downstream phases consume these)
- Sub-phase 1.1: Skeleton — One File, One State, One Render
- Sub-phase 1.2: Nervous System — Typed-Op Dispatcher & Scenario Engine
- Sub-phase 1.3: Proof — Hero Morph Spike & Decision Gate
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Notes for Downstream Phases
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

None — this is the first detailed plan of the run. (The playbook-06 `./state.js` deviation
is recorded in Decisions #1 and Notes for Downstream Phases rather than here, since

---

## phase2a-data-spine  (source: 2026-06-11-product-revamp-diecast-phase2a-data-spine.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (downstream phases consume these)
- Sub-phase 2a.1: Schema Lock & Self-Validating Generator
- Sub-phase 2a.2: Author the Org — Goals, Decisions, Roster, Hiring, Layer-2
- Sub-phase 2a.3: Wire, Sweep, Freeze
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Notes for Downstream Phases
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

None required — including for the two siblings that planned in parallel (2b, 2c): their
exported contracts were adopted wholesale (Decisions #8–#9). Two advisory notes rather than
revisions:

- **Phase 1:** its inline data stubs (appState spines, nudge, hardcoded receipt) are consumed
  and replaced by 2a.3 as Phase 1's own plan anticipated ("Phase 2a extends, must not
  rename"). The demo-script receipt stub (`label: 'Reclassified feature→bug — debug loop',
  at: '17:52'`) becomes atom `DEC-CAST-412-03` — if Phase 1 execution lands first, keep the
  stub's wording verbatim so 2a.3's swap is invisible in the demo.
- **Phase 2b:** its `#/kit` fixtures hand-type canonical vocabulary by design ("so 2a wiring
  is a data swap"). After 2a's freeze, those fixture literals are the one *sanctioned*
  exception to the drift grep until the swap happens — the 2a.3 grep allowlist should include

---

## phase2b-component-kit  (source: 2026-06-11-product-revamp-diecast-phase2b-component-kit.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (Phases 2a/2c/3/4/5 consume these)
- Sub-phase 2b.1: Grammar — Kit Harness, Avatar Grammar & the Guide's Character
- Sub-phase 2b.2a: Shape & Proof — Stage-Spine Variants + the EvidenceBlock Family
- Sub-phase 2b.2b: Judgment — Decision Ladder, Nudge Card, Escalation Rail & Autonomy Dial
- Sub-phase 2b.3: Aesthetic Lock — Signature Screen & the Slop Gate
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

- **Phase 1, minor (non-breaking):** Phase 1 renders the receipt stub as "a 6A-style pill" and
  applies `vt-nudge-card`/`vt-receipt-trail` anchors. Two clarifications this plan adds on top:
  (a) when 2b.2b's real `Decision` pill replaces the stub, the **anchor must sit on the trail's
  zone wrapper, not on the pill component** (contract #9) — if Phase 1's execution placed the
  anchor on the pill element itself, move it to the wrapper during 2b.2b (visual result
  identical, prevents the `#/kit` duplicate-name hazard); same for the nudge card. (b) No
  appState changes are needed by 2b — `receipts[]` entries should migrate to the full decision-
  atom shape in Phase 3/5, not now; Phase 1's stub receipt shape (`{level, label, at,
  rationale}`) remains valid as a subset. No change to Phase 1's plan document is required —

---

## phase2c-stage-research  (source: 2026-06-11-product-revamp-diecast-phase2c-stage-research.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Sub-phase 2c.1: Practitioner Evidence Base — Mine + Targeted Scan (×4 families, parallel)
- Sub-phase 2c.2: Spine Derivation & Practicality Pressure-Test
- Sub-phase 2c.3: Canonical Stage-Model Note, Encoding Contract & Self-Evaluation Gate
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

- **None required.** Phase 1's contracts accommodate this phase as-is (decision #3 resolves
  the only tension — `steps` element type — without touching Phase 1).
- **Conditional flag to Phase 2b (not a revision yet):** if 2c.2's shape-compatibility check
  finds a derived spine that genuinely contradicts its locked variant (segments / loop band /
  timebox meter / pipeline DAG), the stage-model note will carry a "spine-variant revision
  proposed" flag for 2b/Phase 3 reconciliation. Until evidence forces it, the four locked
  variants stand.
- **Note to Phase 2a (coordination, not revision):** reserve a `stageModels` top-level slot in
  the org data using the field contract in Sub-phase 2c.3; do not freeze `org.json` step

---

## phase3-feature-debug-morph  (source: 2026-06-11-product-revamp-diecast-phase3-feature-debug-morph.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (Phases 4/5/6 consume these)
- Sub-phase 3.1: Feature Backbone — Stage-Navigator Canvas & E1 Evidence
- Sub-phase 3.2: Execution Drill-In — Runs, Dispatch Tree, Maker-Checker Loop
- Sub-phase 3.3: Debug-Loop Canvas — Investigation Surface, E2 Ledger & E3 Red→Green
- Sub-phase 3.4: The Real Hero Morph & Flow Stitch (SC-003)
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

- **Phase 2a (advisory, non-breaking — uses its own extension mechanism):** Phase 3 extends
  the generator with `goals[id].execution` + `goals['CAST-412'].morph_view` and three new
  invariants (tree-agent referential check, rework-tag consistency, one focus run). This is
  the freeze policy's designed additive path, not a value mutation — but 2a's invariant-gate
  section should be understood as *growing* with later phases; if 2a execution wants to
  pre-reserve the `execution`/`morph_view` keys as documented extension points (empty or
  absent until Phase 3), that would make the contract explicit at zero cost.
- **Phase 1 (clarification only):** Phase 1's anchor decision #6 used the nudge card as a
  stand-in for the evidence strip "until Phase 3 builds real evidence." This plan keeps the
  nudge-card anchor *and* adds `vt-evidence-strip` (six anchors total) rather than swapping —
  both elements are conceptually persistent chrome; no Phase 1 change needed.
- **Phase 2b:** none. If 2b's `#/kit` fixture swap to spine data hasn't happened by 3.4's
  drift grep, the fixture block remains the one sanctioned allowlist exception (2a already

---

## phase4-spike-data  (source: 2026-06-11-product-revamp-diecast-phase4-spike-data.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (Phases 5/6 consume these)
- Sub-phase 4.1: Spike Flow — Timebox Canvas, Memo Surface & Verdict↔Decision Linkage
- Sub-phase 4.2: Data-Analysis Flow — Pipeline Canvas, Notebook Surface & E5 Rendered Report
- Sub-phase 4.3: FR-017 Three-Access-Tiers Parity Moment (hosted in the spike flow)
- Sub-phase 4.4: Four-Family Stitch, Slop Gate & Drift Sweep
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

- **Phase 2a (advisory, non-breaking — same channel Phase 3 used):** Phase 4 extends the
  generator additively with `goals['CAST-452'].parity`, `goals['CAST-461'].evidence.
  resolved_view`, thin `execution` blocks for both goals, and four new gate invariants
  (parity artifact resolution, transcript non-empty, resolved-view series coverage, thin-run
  agent resolution). This is the freeze policy's designed additive path; if 2a execution
  wants to pre-reserve `parity` and `resolved_view` as documented extension points, that
  makes the contract explicit at zero cost — exactly the note Phase 3 filed for
  `execution`/`morph_view`.
- **Phase 3 (none required):** Phase 3 explicitly left `StageSurface`'s `memo`/`notebook`
  kinds thin "Phase 4 fleshes out" — this plan does exactly that in place; no interface
  change, no revision.
- **Phase 5 (coordination note, parallel not prior):** Phase 4 claims the CAST-452/CAST-461
  canvas banner sections and the single 4.1 generator batch; Phase 5's plans should not
  schedule generator work against these two goals or edit their sections. (The shared
  components both phases consume — `IterationPanel`, `ColleagueCard`, `Decision` — are

---

## phase5-colleague-surfaces  (source: 2026-06-11-product-revamp-diecast-phase5-colleague-surfaces.md)

### Outline
- Overview
- Position in Overall Plan
- Operating Mode
- Depends On (from prior plans)
- Contracts This Phase Exports (Phase 6 consumes these)
- Sub-phase 5.0: Shared Rails — ORG Extension, Route Skeleton & the Digest Atom
- Sub-phase 5a: Board Arc, Decision Trail & the Autonomy Dial (US5 + US10)
- Sub-phase 5b: Hiring Funnel, Marketplace, Agent Ops & Layer-2 (US6 + US8 + US9)
- Sub-phase 5c: Requirements-Doc Loop (US7)
- Sub-phase 5.4: Stitch, Cross-Links, Slop Gate & Drift Sweep
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

1. **Phase 4 — "SCRIPTS complete `{feature, debug, spike, data}` … no further script keys
   planned":** Phase 5 adds the additive `SCRIPTS.hiring` key for the US6 chat-initiated
   side-arc. No existing key or beat is touched; the Phase 3 scriptKey contract explicitly
   supports additive keys. Suggest amending the Phase 4 note to "no further *family* script
   keys planned" — the four-family set does remain closed.
2. **Phase 2a — ORG additive extensions:** this phase extends ORG via the generator
   (`goals['CAST-412'].requirements_doc`, `agents[].versions/monitoring`, `org.skills`, the
   `dial_demo` marker + new invariants). This follows 2a's stated additive-extension policy and
   Phase 3's generator-batch precedent — listed for reconciliation visibility, not as a

---

## phase6-polish-showability  (source: 2026-06-11-product-revamp-diecast-phase6-polish-showability.md)

### Outline
- Overview
- Operating Mode
- Position in Overall Plan
- Depends On (from prior plans)
- Contracts This Phase Exports
- Sub-phase 6.1: Front Door — Scenario Chooser & Guided Walkthroughs
- Sub-phase 6.2: The Gate — Density/Consistency Pass + Full Slop-Gate Sweep
- Sub-phase 6.3a: Distributable — Single-File Inline + Disk Smoke Test (parallel with 6.3b)
- Sub-phase 6.3b: The Map — Surface→Buildable-Goal Roadmap (SC-006) (parallel with 6.3a)
- Sub-phase 6.4: Showability Sign-Off — SC-002 Dry Run & Final Checklist
- Build Order
- Design Review Flags
- Key Risks & Mitigations
- Open Questions
- Spec References
- Decisions Made Autonomously
- Suggested Revisions to Prior Sub-Phases

### Suggested Revisions to Prior Sub-Phases

None required. Two near-misses checked and cleared: (a) Phase 1's driver.js import-map pin lacked
the stylesheet — but Phase 1 explicitly deferred *all* driver.js usage to this phase, so adding
the `<link>` here is consumption, not revision; (b) Phase 4's "no further script keys planned"
was already revised by Phase 5 (`SCRIPTS.hiring`), and Phase 6 adds none — the five-key set this
