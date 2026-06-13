# Reconciliation Report — Product Revamp: Diecast Vision Prototype

> Cross-phase reconciliation of the 8 detailed plans (fan-out run run_20260611_174052_9e350b).
> Inputs: `_subphase_extracts.md`, `product-revamp-diecast-decisions-so-far.md`,
> `plan.collab.md`, plus targeted reads of individual plan files.
> Scope rules honored: NO TESTS is the owner rule (no missing-test findings); full-autonomy
> decisions and the skipped cast-plan-review are sanctioned, not findings.

---

## 1. Cross-Phase Interface Table

| Phase | Produces (exported contract) | Consumed by |
|---|---|---|
| 1 Keystone | Single-file `prototype/index.html` (file:// contract: no fetch, no local ES modules; https CDN import maps + classic `<script src>` + relative `<img>` only) · `render(appState)` + hash routing · appState v1 keys (`route · family · goal · spines · nudge · receipts · pinned · drill · chat{messages,scriptIndex}`, extend-only) · closed op set `morph·nudge·promote·drillInto·pin` via one dispatcher (`data-op`) · scenario step shape `{narration, patch, transition?}` + `advance()` · 5 vt- anchors (`vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail · vt-nav-rail`; `vt-evidence-strip` reserved) · design + motion tokens (incl. `--ink-35`, `--warn`, `--ok`) · CDN pins (preact 10.26.x, htm 3, driver.js in import map, unused until 6) | 2a, 2b, 2c, 3, 4, 5, 6 |
| 2a Data Spine | `prototype/data/org.js` classic script → frozen `window.ORG`; seeded (42) self-validating generator `prototype/data/_build/generate-org.mjs` (additive-extension channel, byte-identical re-run, never hand-edit) · ORG top-level keys frozen: `meta · org · humans · guide · agents · stageModels · goals · board · decisions · hiring · layer2` · goal canon CAST-412 ("Add RBAC to checkout") / 431 / 452 / 461; CAST-417 = THE feature L3 · decision atoms `DEC-<goal>-NN` (PB-05 ADR schema + `diff`) · unified `stats` (99.9%·505·crud-orchestrator; dial 99.4%·312) · appState v1.1 (`org` key, `receipts[].decision_id`) · drift-grep canon · `#/kit` fixture-literal grep exception (until its data swap) | 3, 4, 5, 6 (and 2b's data swap) |
| 2b Component Kit | 8 pure `(props)→vdom` components inline: `ColleagueCard · EvidenceBlock(E1–E5) · StageSpine(segments/loop/timebox/pipeline) · NudgeCard · Decision(pill/callout/row) · EscalationRail · AutonomyDial(static) · GuideMark` + `Avatar` primitive · avatar grammar (human=circle, maker=square outline, checker=square fill, Guide=diamond) · decision-atom field names verbatim · agent fixture shape (2a supersets it) · extend-only tokens (`--fail`, L-badge mapping L1=`--ink-35`/L2=`--warn`/L3=`--rasp`, ●/◐/○ glyphs) · vt- anchors on zone wrappers NEVER on kit components · `#/kit` hidden harness route · slop-gate mechanic (`/cast-preso-check-visual` + `/cast-preso-check-tone` on screenshots, `not-generic`/`not-ai-aesthetic`) | 2a (shapes), 3, 4, 5, 6 |
| 2c Stage Research | `docs/plan/product-revamp-diecast-stage-models.md` (canonical vocabulary, cited never re-derived) · `stageModels.<family>` field contract (shape/progression/loop/timebox/steps `{id, label, shortLabel?, does, surface, surfaceWhy, artifacts, refs, evidence}`) · step-id grammar `<family>-NN` (`feat- dbg- spk- data-`) · `appState.spines.steps` stays `string[]` via `shortLabel ?? label` mapping · E1–E5 one home step each · conditional spine-variant flag channel to 2b/3 | 2a (slot reserved verbatim), 3, 4 |
| 3 Feature+Debug+Morph | `vt-evidence-strip` claimed (anchor set = 6, on zone wrapper) · ORG additive batch: `goals[id].execution` (runs, focus_run tree, iteration), `goals['CAST-412'].morph_view` + 3 invariants · components `StageSurface` (doc/board/pr-thread/ledger/notebook/memo), `RunNode`, `IterationPanel` · `SCRIPTS = {feature, debug}` + additive `appState.chat.scriptKey` · additive `appState.stageFocus` · `drillInto` step-id reuse (ops stay 5) · E1 rasters in `prototype/assets/` via relative `<img>` + onerror fallback · CSS `surf-*`/`exec-*` · morph receipt = one atom DEC-CAST-412-03, undo emits no second receipt | 4 (StageSurface memo/notebook), 5 (IterationPanel, scriptKey, drillInto pattern, execution data), 6 |
| 4 Spike+Data | ORG additive batch (one, owned by 4.1): thin `goals[452/461].execution`, `goals['CAST-452'].parity`, `goals['CAST-461'].evidence.resolved_view` + 4 invariants · `SCRIPTS.spike`/`SCRIPTS.data` · E5 = data-driven inline SVG (numbers always from ORG, never rasters) · the ONE script-wired L3 resolution (data flow; all other rails stay unresolved stops) · additive `appState.parityOpen` · `parity-*` CSS · "ORG unmutated, reload resets" idiom | 5 (idioms + boundary), 6 |
| 5 Colleague Surfaces | ORG additive batch (one, owned by 5.0): `goals['CAST-412'].requirements_doc`, `agents[].versions/monitoring`, `org.skills` (nested), `dial_demo` marker + CAST-452/461 byte-identical invariant · final 10-route table (`#/board · #/ticket/CAST-412 · #/decision/:atomId · #/decisions/CAST-412 · #/hire · #/marketplace · #/agent/:slug · #/skills/new · #/layer2 · #/reqs/CAST-412`) · `SCRIPTS.hiring` (additive) · additive appState `boardFilter · hiring · autonomyLevel · reqsDoc` · `DigestNotice`, `RadarChart`, `Sparkline` · CSS `hire-*/mkt-*/ops-*/l2-*` · AutonomyDial toggle wired | 6 |
| 6 Polish | `TOURS` (5 keys mirroring SCRIPTS) on `data-tour` attributes + demo-script overlay (`appState.demoScriptOpen`, `s` key) · driver.css CDN `<link>` + `tour-*` restyle · chooser at `#/` (5 verb-first cards from ORG.goals) · `prototype/_build/inline.mjs` → `prototype/dist/diecast-prototype.html` (inline org.js + base64 rasters, ≤5MB; CDN stays CDN) · full 21-capture slop gate · consolidated final drift sweep, `#/kit` exception RETIRED · SC-006 map `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` | Owner / v2 planning |

**Closed-set ledgers (verified consistent end-to-end):**
- Ops: closed at 5 in every phase (Phase 3 reuses `drillInto`; Phase 4 uses `parityOpen` flag; Phase 5 plain handlers; Phase 6 confirms).
- SCRIPTS keys: feature, debug (P3) + spike, data (P4) + hiring (P5) = 5; Phase 6 closes at 5. (See Finding F2 for Phase 4's stale wording.)
- vt- anchors: 5 (P1) + `vt-evidence-strip` (P3) = 6; all on zone wrappers per 2b's rule; P2b's wrapper-not-pill clarification handled.
- appState keys: every addition additive, no renames anywhere (v1 → v1.1 → scriptKey/stageFocus → parityOpen → boardFilter/hiring/autonomyLevel/reqsDoc → demoScriptOpen).
- ORG top-level keys: frozen at 11 by 2a; all later extensions nest under existing keys (`goals[*].*`, `agents[].*`, `org.skills`) via the generator. No violations.

## 2. Canonical Naming Table

**No naming conflicts found — table omitted.** Verified: goal ids CAST-412/417/431/452/461 identical in all plans; CAST-412 title "Add RBAC to checkout" consistent (2a's rejection of the playbook-04 Invoice alternative propagated); atom ids `DEC-<goal>-NN` and the morph atom `DEC-CAST-412-03` consistent across 2a/3; step-id grammar `<family>-NN` identical in 2c and 2a; component names identical wherever referenced (ColleagueCard, EvidenceBlock, StageSpine, NudgeCard, Decision, EscalationRail, AutonomyDial, GuideMark, StageSurface, RunNode, IterationPanel, DigestNotice, RadarChart, Sparkline); token names consistent — 2b's L-badge tokens (`--ink-35`, `--warn`, `--rasp`) all exist in Phase 1's verbatim app-shell `:root` set; stat canon (99.9%·505·2 loops / 99.4%·312 / M04/S03/R02 / rework 1/3) single-sourced from 2a and quoted identically.

## 3. Conflict List

### F1 — stageModels encoding ownership is contradictory between 2c and 2a (HIGH)

- **What:** Phase 2c's hand-off note (2c.3, "Write the hand-off notes") assigns the encoding to
  2a: "**2a — paste `stageModels` into the org data** … flip `placeholder` to `false`."
  Phase 2a (planned later, adopting 2c's contract) assigns it the other way: "the `stageModels`
  region is **2c-owned** and will be rewritten once by 2c's derived stage vocabulary (via the
  generator)" (line 227) and "**2c:** rewrite ONLY `stageModels` via `generate-org.mjs`"
  (line 484); its risk table even times the gate re-run to that moment (line 449).
  `decisions-so-far.md` records 2a's version. If each execution child follows its own plan file,
  **nobody performs the rewrite**: 2c ends at the markdown note, 2a freezes with watermarked
  placeholders, and Phase 3 (critical path) builds canvases over PLACEHOLDER vocabulary —
  violating 2c's own gate ("Phases 3–4 cite it, never re-derive") and SC-005.
- **Hidden dependency:** the rewrite needs 2a's generator to exist, so within the parallel band
  the true order is 2a.1 (generator) → 2c-encode → freeze-complete → Phase 3. Neither plan
  schedules this slot.
- **Affected files:** `2026-06-11-product-revamp-diecast-phase2c-stage-research.md` (primary);
  `2026-06-11-product-revamp-diecast-phase2a-data-spine.md` (optional cross-ref).
- **Suggested edit (phase2c, 2c.3 hand-off notes):** replace
  "2a — paste `stageModels` into the org data, leave `appState.spines` derivation to the render
  layer, flip `placeholder` to `false`"
  with
  "2c (this phase, final step — runs after 2a.1's generator exists): edit the generator's
  stage-model section in `prototype/data/_build/generate-org.mjs` with the derived vocabulary
  and re-emit `org.js` per 2a's '2c: rewrite ONLY stageModels' instructions; this flips
  `placeholder` to `false` and re-runs the invariant gate. If 2a has not yet landed the
  generator when 2c.3 completes, the encoding step parks until 2a.1 and MUST complete before
  Phase 3 dispatch."
- **Severity: HIGH** — sits on the critical path; ownership is contradictory in writing across
  two plan files; cheap one-edit fix.

### F2 — Phase 4's "no further script keys planned" is contradicted by Phase 5's `SCRIPTS.hiring` (MED)

- **What:** Phase 4's exported contract states "SCRIPTS complete `{feature, debug, spike, data}`
  … no further script keys planned." Phase 5 adds the additive `SCRIPTS.hiring` (sanctioned by
  Phase 3's additive scriptKey contract) and itself filed the amendment request; Phase 6
  confirms the five-key closure. Because Phases 4 and 5 execute in parallel, an executor
  honoring Phase 4's contract text as written could read Phase 5's addition as a violation.
- **Affected file:** `2026-06-11-product-revamp-diecast-phase4-spike-data.md`.
- **Suggested edit:** amend the contract line to: "SCRIPTS four-family set complete
  `{feature, debug, spike, data}` — no further **family** script keys planned; demo-arc keys
  (e.g., Phase 5's `SCRIPTS.hiring`) may be added additively per the Phase 3 scriptKey
  contract. Final key set closes at 5 in Phase 6."
- **Severity: MED** — wording-only, but it is an exported contract read during parallel
  execution; the fix prevents a false contract-violation stop.

### F3 — Parallel generator batches (4.1 ∥ 5.0) regenerate the same committed artifact (LOW)

- **What:** Phase 4.1 and Phase 5.0 each own "ONE generator batch," both editing
  `generate-org.mjs` and re-emitting the committed `prototype/data/org.js` while running in
  parallel. Semantic guards exist and are mutually consistent (Phase 4 claims the CAST-452/461
  sections; Phase 5.0 adds the byte-identical invariant for those sections) — but nothing
  specifies the mechanical serialization of two concurrent edits to one generator + one
  generated file (git-level collision, and seeded-RNG stream shifts from interleaved edits).
- **Resolution (advisory, no file edit required):** orchestrator serializes the two batches —
  run 4.1's generator batch to completion (commit `org.js`) before 5.0's batch starts (or vice
  versa with the byte-identical check pointed at the other phase's sections). Both plans'
  guards then verify the result.
- **Severity: LOW** — both plans already half-anticipate it; execution-scheduling note only.

### F4 — Frozen-value stability under additive generator extensions guarded only by Phase 5 (LOW)

- **What:** the generator is one seeded (42) stream; inserting new generation calls (Phase 3's
  `execution`/`morph_view` batch, Phase 4's batch) can silently perturb previously frozen values
  in untouched sections. 2a's byte-identical check covers idempotent re-runs, not
  extension-under-edit; the drift grep covers canon terms, not all values. Only Phase 5.0
  carries a section-stability invariant.
- **Resolution (advisory):** Phase 3 and Phase 4 generator batches adopt Phase 5's technique —
  assert all ORG sections outside the batch's declared additions are byte-identical before/after.
  One invariant each, zero design change.
- **Severity: LOW** — defense-in-depth on an already-guarded mechanism.

### F5 — Effort overruns vs high-level envelopes (LOW, informational)

- Phase 5 honest at ~4.75–5.75 sessions (envelope 3–4); Phase 6 ~2.75–3.25 (envelope 2).
  Both are explicitly sanctioned by the owner's "extend the timeline, don't cut" policy and are
  flagged honestly inside the plans. Whole-project total drifts from ~14–18 to roughly
  ~17–21+ sessions; critical path (1 → 2b → 3 → 5 → 6) ≈ 13.5–17 sessions. No edit required —
  recorded so the orchestrator's scheduling expectations match the plans, not the envelope.

## 4. Scope Gaps & Overlaps

**Gaps — one real (F1), the rest checked and closed:**
- stageModels placeholder → real-vocabulary encoding: **gap, see F1.**
- `#/kit` fixture → ORG data swap: 2b defines it as "a data-source swap when org.json lands"
  without scheduling it; Phase 3 treats it as optional-by-3.4 (allowlist exception persists);
  **Phase 6 carries an explicit backstop** ("complete the swap … if execution hasn't already",
  phase6 lines 259–261 and checklist item 11) before retiring the exception. Closed — no action.
- driver.js stylesheet missing from Phase 1's import-map pin: Phase 6 checked this and adds the
  `<link>` as consumption (Phase 1 deferred all driver.js usage to 6). Closed.
- Everything Phase 6 needs exists upstream: TOURS keys mirror the 5 SCRIPTS keys; chooser cards
  render from `ORG.goals`; the 21-capture surface list is producible from Phases 3/4/5 routes;
  the inline build consumes only committed dev files. No other gaps.

**Overlaps — all sanctioned or coordinated, no true collisions:**
- All ORG extensions (3, 4, 5) go through 2a's generator extension mechanism — sanctioned by
  definition. The 3→2a and 4→2a "pre-reserve extension-point keys" notes are optional niceties.
- Phase 4 fleshes StageSurface's `memo`/`notebook` kinds in place — explicitly assigned by
  Phase 3 ("Phase 4 fleshes out"); not a collision. Same for Phase 4's E5 branch work inside
  2b's EvidenceBlock (2b shipped E5 as the rendered-report slot; Phase 4 implements its
  renderer with existing tokens).
- Phase 4 ∥ Phase 5 surface and data boundaries are explicitly claimed and mutually honored
  (Phase 4 claims CAST-452/461 sections; Phase 5.0 encodes the byte-identical guard; shared
  components are consume-only). Residual mechanical risk handled as F3.
- Phase 1's stub receipt / nudge data is consumed-and-replaced by 2a.3 exactly as Phase 1's own
  plan anticipated ("Phase 2a extends, must not rename"). Coordinated handoff, not a collision.

## 5. Shared Infrastructure Consistency

- **Slop gate:** one mechanic everywhere — `/cast-preso-check-visual` + `/cast-preso-check-tone`
  on screenshots, scoped `not-generic`/`not-ai-aesthetic`; defined in 2b, applied to 4 surfaces
  (P3), 4 surfaces (P4), 6 surfaces (P5), full 21 captures (P6). Consistent.
- **Drift grep:** one canon, single lineage — recorded by 2a, re-run at 3.4, extended by P4
  (CAST-452 · CAST-461 · 180ms · 1h40m · 8% + source names), swept at 5.4, consolidated +
  finalized in 6 with the `#/kit` exception retired (zero exceptions at project end). Consistent.
- **Scenario engine:** Phase 1's step shape and `advance()` untouched by all later phases; only
  additive `scriptKey` (P3) and new script entries. Consistent.
- **Single-file / file:// rules:** identical statement in every plan (no `fetch()`, no local
  ES-module imports; https CDN import maps, classic `<script src>` for org.js, relative `<img>`
  for rasters). A grep of all 8 plans found `fetch(` only inside prohibitions. The two
  build-time Node tools (2a's generator, 6's inline.mjs) are authoring/dist tooling whose output
  is committed — the prototype itself still opens from disk with no build step, matching the
  high-level plan's "seeded faker, build-time only" sanction. **No violations (checklist #10
  clean).**
- **NO-TESTS rule:** no plan contains test-suite work; the only grep hits are explicit
  NO-TESTS compliance notes in 2a. Clean.

## 6. Dependency Ordering & Verification Chain

- **Phase-level DAG holds as planned** (1 → 2a∥2b∥2c → 3 → 4∥5 → 6). Phase 5's plan correctly
  declares its Phase 3 consumption (IterationPanel, scriptKey, execution data) — already
  satisfied by the DAG; not a hidden dependency at phase granularity.
- **One hidden intra-band edge discovered (from F1):**

```
Phase 1 ──► 2a.1 (generator) ──► 2a.2/2a.3 ──┐
        ──► 2b ──────────────────────────────┼──► Phase 3 ──► 4 ∥ 5 ──► 6
        ──► 2c.1→2c.2→2c.3 ──► [2c-encode]───┘        (4.1 and 5.0 generator
                 (needs 2a.1's generator;              batches serialized — F3)
                  must complete before Phase 3)
```

- **Verification chain (manual click-through only — correct per owner rule):** every phase's
  verification proves its stated outcome: P1 disk-open + morph gate criteria (~350ms, ≥4
  anchors, reduced-motion fallback, 5 ops); 2a generator self-refusal + byte-identical re-run +
  drift grep (build-time validation, sanctioned, not tests); 2b `#/kit` isolation render + slop
  gate on the signature screen; 2c written self-evaluation rubric (research phase — correctly
  has no click-through); P3 both flows + real morph click-through against the SC-003/SC-005
  criteria; P4 verdict-linkage + rendered-E5 + parity click-through; P5 four-frame board-arc
  story + funnel + dial click-through; P6 SC-002 fresh-peer dry run + dist-file disk smoke test.
  No phase relies on automation; no phase's outcome is unverifiable by its stated check.
- **Critical path sanity:** 1 → 2b → 3 → 5 → 6 remains correct (2b > 2a within the band;
  5 > 4). With honest P5/P6 estimates the path is ~13.5–17 sessions (F5); no phase is
  under-scoped; P5's size is acknowledged and owner-sanctioned.

## 7. Suggested-Revisions Assessment (grouped by target phase)

### Target: Phase 1
| From | Revision | Assessment |
|---|---|---|
| 2a | Keep the demo receipt stub's wording verbatim (becomes atom DEC-CAST-412-03) if Phase 1 executes first | **ACCEPT** — execution-time coordination; no plan edit needed |
| 2b | (a) vt- anchor on the trail/nudge zone wrapper, not the pill/card component; (b) receipts keep stub shape (subset of atom) until P3/5 | **ACCEPT** — 2b itself states "no change to Phase 1's plan document is required"; (a) is an execution check during 2b.2b |
| 3 | Keep nudge-card anchor AND add `vt-evidence-strip` (6 anchors) rather than swap | **ACCEPT** — clarification only; "no Phase 1 change needed" per Phase 3 |
| 6 | driver.js stylesheet `<link>` added in Phase 6 | **ACCEPT** — consumption of Phase 1's deferred driver.js usage, not a revision |

### Target: Phase 2a
| From | Revision | Assessment |
|---|---|---|
| 2c | Reserve `stageModels` slot per the 2c.3 contract; don't freeze step vocabulary | **ACCEPT (already satisfied)** — 2a adopted the contract verbatim mid-planning (its Decision #8) |
| 3 | Optionally pre-reserve `execution`/`morph_view` as documented extension points | **ACCEPT** — optional zero-cost nicety; extension mechanism works either way |
| 4 | Optionally pre-reserve `parity`/`resolved_view` (same channel) | **ACCEPT** — same reasoning |
| 5 | ORG additive extensions listed "for reconciliation visibility" | **ACCEPT** — visibility note; conforms to 2a's additive policy and the P3 precedent. Reconciliation confirms: sanctioned |

### Target: Phase 2b
| From | Revision | Assessment |
|---|---|---|
| 2a | After freeze, `#/kit` fixture literals = the one sanctioned drift-grep exception until the data swap | **ACCEPT** — allowlist mechanics, recorded in 2a's grep canon; Phase 6 retires it |
| 2c | Conditional "spine-variant revision proposed" flag if research contradicts a locked variant | **ACCEPT** — conditional channel, fires only on evidence; the four locked variants stand |
| 3 | If the fixture swap hasn't happened by 3.4, the exception persists | **ACCEPT** — restates 2a's allowlist; Phase 6 backstop closes it |

### Target: Phase 4
| From | Revision | Assessment |
|---|---|---|
| 5 | Amend "no further script keys planned" → "no further *family* script keys planned" (SCRIPTS.hiring added) | **APPLY** — see F2; edit `2026-06-11-product-revamp-diecast-phase4-spike-data.md` contract line as specified there. Phase 6 confirms final closure at 5 keys |

### Target: Phase 5
| From | Revision | Assessment |
|---|---|---|
| 4 | Do not schedule generator work against CAST-452/461 or edit their sections (parallel guard) | **ACCEPT (already satisfied)** — Phase 5.0 encodes the byte-identical invariant and consumes shared components read-only |

### Target: Phase 6 / none filed
Phases 1, 2c, 6 filed no actionable revisions (Phase 1 is first; 2c's items were coordination
notes adopted by 2a; Phase 6 checked two near-misses and cleared both). **No REJECTs anywhere**
— every filed revision was either advisory or already absorbed by the target's own plan.

(New APPLY item raised by this reconciliation, not filed by any phase: **F1's edit to
phase2c's hand-off note** — see Conflict List.)

## 8. Verdict

**VERDICT: NEEDS REVISION**

Files to update before execution dispatch:

1. `2026-06-11-product-revamp-diecast-phase2c-stage-research.md` — (F1, HIGH) rewrite the 2c.3
   hand-off note's "2a — paste stageModels into the org data … flip placeholder to false" line
   to assign the org.js stageModels rewrite to **2c itself, via 2a's generator, scheduled after
   2a.1 and before Phase 3 dispatch** (exact replacement text in F1). This aligns 2c with 2a
   lines 45/227/484 and `decisions-so-far.md`, and closes the only unowned critical-path step.
2. `2026-06-11-product-revamp-diecast-phase4-spike-data.md` — (F2, MED) amend the exported
   contract line "SCRIPTS complete {feature, debug, spike, data} … no further script keys
   planned" to "no further **family** script keys planned; demo-arc keys (Phase 5's
   `SCRIPTS.hiring`) may be added additively; final key set closes at 5 in Phase 6" (exact text
   in F2).

Orchestrator advisories (no file edits): serialize the 4.1 and 5.0 generator batches (F3);
have Phase 3/4 batches adopt Phase 5's section-stability invariant (F4); schedule against the
honest P5/P6 effort numbers, not the high-level envelopes (F5).
