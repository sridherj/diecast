# Product Revamp: Diecast — Phase 4: Spike + Data-Analysis Flows

## Overview

This phase completes the four-family thesis: the two remaining workflow families become
clickable end-to-end from the frozen org spine, finishing **SC-001 and SC-005**. The spike
family (`CAST-452 — Does the vendor checkout SDK fit our 200ms p95 budget?`) runs its derived
timebox shape — meter spine, probes-tried card, memo conclusion surface — and lands the **E4
verdict card whose `spike_ref` is referenced by a decision** (FR-016 made visible, both
directions navigable). The data-analysis family (`CAST-461 — Which segment drove the Q2
revenue dip?`) runs its derived pipeline shape — question → data sources → analysis →
**E5 rendered visualization** (a real inline-SVG chart + table + provenance, never prose-only).
The spike flow also hosts the **FR-017 three-access-tiers moment**: a faux terminal pane
invoking the same skill next to the canvas doing it with defaults, the same artifact landing
either way, with the chat rail visible alongside — all three tiers on one screenful.

Almost everything here is composition, not invention: the canvas grammar, component kit,
evidence conventions, scripted-flow pattern, and stage-navigator behavior were all settled in
Phases 1–3. Phase 4's net-new work is two thin data-slice canvases, the fleshed-out
`memo`/`notebook` surfaces (Phase 3 shipped thin versions on purpose), the one hand-authored
chart, the parity pane, and two flow scripts. Per the build-cost insight that governs the whole
prototype, each canvas is a projection of `ORG` through the existing `render(appState)` — the
marginal cost of a family is data plus two deviated zones.

## Position in Overall Plan

```
Phase 1 (planned) ──► 2a ∥ 2b ∥ 2c (planned) ──► Phase 3 (planned) ──► ►Phase 4 (THIS PLAN)◄ ∥ Phase 5 ──► Phase 6
  render arch +        data  kit  spines          feature + debug +      spike + data flows      colleague    polish
  morph SPIKE                                     REAL hero morph        SC-001 · SC-005         surfaces
                                                                         completion · FR-016/017
```

Phase 4 is **off the critical path** (1 → 2b → 3 → 5 → 6) and runs **in parallel with
Phase 5** — different surfaces, shared components only. It depends on Phase 3 having settled
the canvas grammar, `StageSurface`, the scripted-flow pattern, and the evidence conventions.
Phase 6 consumes its outputs: four walkable family scripts for the scenario chooser, and the
parity moment as a walkthrough beat.

## Operating Mode

**HOLD SCOPE** — the delegation instruction is explicit ("plan exactly what the high-level
plan section says for this phase, at high practical detail"). The high-level plan bounds
Phase 4 to five activities: the spike canvas (timebox meter, memo surface, E4 verdict with
`spike_ref`), the spike→decision wiring (FR-016), the data-analysis canvas (pipeline/notebook
surface, data-source list, E5 rendered report), the FR-017 three-access-tiers side-by-side
moment, and each family's scripted chat steps + single L3 moment. No colleague surfaces
(Phase 5), no entry-screen routing or asset inlining (Phase 6), no new families, no new ops.
Per the owner's **NO TESTS** rule there are no test files, suites, or CI anywhere in this
plan — all verification is manual: open `prototype/index.html` from disk, click, observe.
(Fake test-result *content* rendered as prototype data is fine and none appears in these two
families anyway; E4/E5 carry their own proof forms.)

## Depends On (from prior plans)

Adopted unchanged from `product-revamp-diecast-decisions-so-far.md` and the prior phase plans:

**From Phase 1 (keystone):**
- ONE file `prototype/index.html`, inline style + module; `file://` blocks local ES-module
  imports and `fetch()` — org data via classic script, images via relative `<img>` only.
- `appState` v1 keys (extend, never rename); closed op vocabulary
  `morph · nudge · promote · drillInto · pin` via `data-op="op:arg"` through the single
  dispatcher; scenario engine `{narration, patch, transition?}` + `advance()`, index at
  `appState.chat.scriptIndex`.
- vt- anchors live on shell zone wrappers (six total after Phase 3, incl. `vt-evidence-strip`);
  duplicate `view-transition-name`s silently kill all transitions; motion tokens
  (`--morph-duration: 350ms`, reduced-motion fade 180ms).

**From Phase 2a (data spine):**
- `window.ORG` frozen; **additive extensions only, authored via
  `prototype/data/_build/generate-org.mjs`** (invariant gate re-run); never hand-edit `org.js`.
- Goals consumed: `CAST-452` (spike — question-as-L1 "Does the vendor checkout SDK fit our
  200ms p95 budget?", `spine_state.timebox_used: '1h40m'` against a 3h budget after one
  L2-recorded extension from 2h, memo artifact, probes-tried work stream, E4 payload: "adds
  180ms p95 — borderline", confidence M (◐), 3 deciding data points, `spike_ref` both
  directions) and `CAST-461` (data — "Which segment drove the Q2 revenue dip?",
  `spine_state.current: 'data-03'`, notebook + report v1/v2 artifacts, pipeline-cell work
  stream, E5 payload: bar-chart series + table + provenance with the two disagreeing sources —
  finance DB vs billing export, 8% apart).
- Decision atoms (playbook-05 schema verbatim + `diff`): each goal has 5–8 atoms with
  **exactly one L3** — spike L3 = the vendor-SDK borderline go/no-go (options: proceed /
  self-host / renegotiate), data L3 = the 8% source disagreement (options: source-of-record /
  show both with reconciliation note / flag for analyst review); L3s carry 3 ranked options,
  none `chosen`, plus an evidence pack. The spike's 2h→3h extension is an L2 atom.
  `spike_ref` integrity is **bidirectional and gate-enforced** (the E4 verdict references the
  atom that references it).
- Canonical tokens render only from `ORG`; the drift grep command from 2a.3's freeze note
  re-runs at this phase's end.

**From Phase 2b (component kit):**
- Components consumed as-is: `StageSpine {spine}` — **the `timebox` and `pipeline` shapes
  already exist** (the spike meter reads `spine.timebox.{budget, used}`); `EvidenceBlock
  {kind, data}` with locked E4/E5 data shapes; `ColleagueCard` (line density); `Decision
  {atom, layer}` ladder; `NudgeCard`; `EscalationRail`; `GuideMark` + Guide voice.
- Confidence glyphs ●/◐/○ (never percentages); L-badge mapping (L1 `--ink-35` / L2 `--warn` /
  L3 `--rasp`); `--fail` token; vt- names never on kit components; `#/kit` harness for
  verifying new component states.

**From Phase 2c (stage research):**
- Stage vocabulary renders **exclusively** from `ORG.stageModels.<family>.steps[]`
  (`{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[], evidence}`) +
  each goal's `spine_state`. Spike: `shape: 'timebox'`, `timebox: {budget: '3h'}`, step ids
  `spk-NN`; data: `shape: 'pipeline'`, step ids `data-NN`. E4 and E5 each have exactly one
  home step. Canonical definitions: `docs/plan/product-revamp-diecast-stage-models.md` —
  cite, never re-derive.

**From Phase 3 (feature + debug + morph):**
- **`StageSurface({step, artifacts})`** keyed on `step.surface`
  (`doc | board | pr-thread | ledger | notebook | memo`) — Phase 3 shipped thin
  `notebook`/`memo` versions and explicitly assigned Phase 4 to flesh them out.
- **Stage navigation:** spine-step clicks route through `dispatch('drillInto:<step-id>')`;
  `'execution'` remains the HOW target; `appState.stageFocus` holds the focused step.
- **`SCRIPTS = {feature, debug}` + `appState.chat.scriptKey`** (set on goal-route entry by
  family) — Phase 4 adds the `spike` and `data` keys the same way.
- Exec drill-in grammar (`RunNode`, `IterationPanel`), CSS prefixes `surf-*`/`exec-*`,
  banner-section partitioning of `index.html` for parallel work, the ORG-extension-via-
  generator pattern (Phase 3 added `goals[id].execution` for CAST-412/431), the slop-gate
  delegation pattern, and the asset rule (`prototype/assets/`, relative `<img>`, `onerror`
  fallback).

## Contracts This Phase Exports (Phases 5/6 consume these)

1. **The complete script set:** `SCRIPTS = {feature, debug, spike, data}` — Phase 6's
   scenario chooser routes into all four; no further **family** `scriptKey` values are
   planned. Demo-arc keys (e.g., Phase 5's `SCRIPTS.hiring`) may be added additively per the
   Phase 3 scriptKey contract; the final key set closes at 5 in Phase 6. *(Amended by
   reconciliation F2, 2026-06-12.)*
2. **Fleshed `StageSurface` kinds `memo` and `notebook`** — the full familiar-tool renderer
   set is now complete (`doc | board | pr-thread | ledger | notebook | memo`); Phase 5c's
   requirements loop reuses `doc` unchanged.
3. **The E5 chart idiom:** a data-driven inline-SVG chart rendered inside `EvidenceBlock`'s
   E5 branch as a pure function of the ORG series — the prototype's one real chart and the
   precedent if any later surface needs one (Phase 5b's eval radar is its own 2b-planned
   treatment; no dependency).
4. **The parity-pane pattern** (`parity-*` CSS prefix, script-patch-driven reveal): a one-off
   for FR-017, referenced by Phase 6's walkthrough overlay as a named beat.
5. **ORG additive extension (via the 2a generator, gate re-run):**
   `goals['CAST-452'].execution` + `goals['CAST-461'].execution` (thin run lists, no tree),
   `goals['CAST-452'].parity = {command, transcript: [...], artifact_id, caption}`, and
   `goals['CAST-461'].evidence.resolved_view = {series: [...both sources...],
   reconciliation_note}` — with new gate invariants (see 4.1).

---

## Sub-phase 4.1: Spike Flow — Timebox Canvas, Memo Surface & Verdict↔Decision Linkage

**Outcome:** `#/goal/CAST-452` is the real spike canvas and is *deliberately the lightest
surface in the prototype*: a timebox-meter spine (3h budget · 1h40m used, with the L2
extension recorded on it), a single probes-tried card as the work zone, the memo familiar
surface at the conclusion step, and the E4 verdict card ("adds 180ms p95 — borderline",
◐ confidence, 3 deciding data points) whose `spike_ref` linkage to the L3 decision atom is
navigable in both directions in ≤1 click each (FR-016 / US2 S3). The spike script walks
end-to-end and stops at the family's single L3. The ORG data extensions for *both* Phase 4
goals land here via the generator, so 4.2 and 4.3 never touch `generate-org.mjs`.

**Dependencies:** Phase 3 executed (canvas grammar, `StageSurface`, script plumbing,
`stageFocus`); 2a/2b/2c executed (org frozen, kit locked, `stageModels.spike` real,
`placeholder: false`). If 2c vocabulary hasn't landed, stop and resolve first (Phase 3's
rule, inherited).
**Estimated effort:** 1–1.25 sessions (~3.5h)

**Verification (manual click-through):**
- Open `prototype/index.html` from disk → `#/goal/CAST-452`: console clean; the timebox meter
  renders from `stageModels.spike.timebox` + `spine_state.timebox_used` (3h budget, 1h40m
  used, proportional fill); real 2c vocabulary, no `PLACEHOLDER` watermark; the header reads
  the question-as-L1 ("Does the vendor checkout SDK fit our 200ms p95 budget?") with the
  spike pill and the nudge from the goal's nudge object.
- **The lightness glance test (playbook 03 pitfall #3):** side-by-side with
  `#/goal/CAST-412`, the spike canvas reads materially lighter — a meter, not a segment bar;
  one card, not a work stream + stage artifacts grid. If it reads as a shrunk feature
  backbone, that is a defect.
- The probes-tried card lists each probe + one-line result from the work stream, with
  line-density `ColleagueCard` attribution where an agent ran the probe.
- The L2 extension chip ("extended 2h→3h") renders on/adjacent to the meter; clicking opens
  the 6B callout with rationale + `revisit_if` from its atom. One L1 chip (the "timeboxed to
  2h; p95 only" atom) renders on its owning artifact.
- Clicking the conclusion step on the spine (`drillInto:<spk-NN>`) renders the **memo
  surface**: one-pager findings memo (dated, mono header, probes summary, conclusion line)
  with its `surfaceWhy` caption. Back/forward and re-render preserve `stageFocus`.
- The E4 verdict card renders at its home step and summarized in the evidence strip:
  one-line answer + ◐ (M) confidence glyph + the 3 deciding data points + the `spike_ref`
  link. **Never a bare pass state.**
- **`spike_ref` both directions, ≤1 click each:** clicking `spike_ref` on the verdict opens
  the L3 decision (rail/callout view, evidence pack visible); from the decision, the
  `spike_ref` field links back to the verdict card (scroll + highlight). Ids match the atom.
- The L3 needs-you chip renders at WHAT level; the `EscalationRail` shows the 3 ranked
  options (proceed / self-host / renegotiate), nothing pre-selected; options are inert
  (the stop is shown, not resolved — see Decisions #4).
- "Next ▸" walks `SCRIPTS.spike` start-to-finish: open → Guide nudge → probe beat →
  timebox/L2-extension beat → verdict (E4) beat → [parity beat slot, filled by 4.3] → L3
  stop → close. Narration interpolates canonical tokens from `ORG`; reload resets clean.
- Exec tab: thin run list (1–2 runs, **no dispatch tree**); `appState.drill` toggles cleanly.
- Generator check: `git diff` on `data/org.js` shows only additive keys; the invariant gate
  passes; drift spot-check (edit a value in the generator, regenerate, reload, observe,
  revert).

Key activities:
- **One generator-extension batch for both Phase 4 goals (the sanctioned path, single
  owner):** extend `generate-org.mjs` with (a) `goals['CAST-452'].execution` and
  `goals['CAST-461'].execution` — thin shape `{runs: [{id, agent, status, when, summary,
  rework_count}]}`, 1–2 runs each, no `focus_run` tree; (b) `goals['CAST-452'].parity =
  {command, transcript: [...lines], artifact_id, caption}` (the FR-017 terminal text — lives
  in the spine so skill names and artifact ids can't drift); (c)
  `goals['CAST-461'].evidence.resolved_view = {series: [...both sources...],
  reconciliation_note}` (consumed by 4.2's L3-resolution beat; the authored report v1/v2
  version semantics stay untouched). New gate invariants: `parity.artifact_id` resolves to
  the E4 verdict artifact; `transcript` non-empty and contains the artifact line;
  `resolved_view.series` covers exactly the two disagreeing sources; thin `execution.runs`
  agents resolve in `ORG.agents`. Regenerate, gate green, diff additive-only.
- **Compose the spike canvas from the shared grammar:** identical header band, decision
  chips, exec tab, chat rail; deviated zones only — spine zone renders `StageSpine` with the
  2b `timebox` shape; work zone renders the single Timebox Card (probes-tried rows). No
  stage-artifacts grid, no ticket stream — the lightness *is* the design (contrarian §6:
  a spike must never look like a mini-feature).
- **Flesh out `StageSurface`'s `memo` kind** (Phase 3 shipped the thin version): one-pager
  memo treatment — dated mono header, the probes summary, the conclusion line, the timebox
  stamp — full-bleed in the stage zone per the familiar-tool principle, `surfaceWhy` caption.
- **Wire E4:** `EvidenceBlock {kind:'E4', data: goal.evidence}` at the step whose
  `evidence === 'E4'`, plus the evidence-strip summary in the default view. Implement the
  bidirectional `spike_ref` navigation as **local disclosure** (the existing chip→callout
  mechanism + scroll/highlight), not a new op — the closed vocabulary stands.
- **Decision chips + L3 at WHAT:** L1 pill, the L2 extension chip on the meter, the L3
  needs-you chip in the header band opening `EscalationRail` (options complete but inert,
  per Phase 3 decision #10).
- **Author `SCRIPTS.spike` (~6–7 steps)** keyed on route entry, leaving an explicit beat
  slot for 4.3's parity step (after the verdict beat, before the L3 — see Decisions #8);
  narration interpolates from `ORG`.

**Design review:**
- **Spec consistency (stage vocabulary):** zero hardcoded stage labels/surfaces/budgets —
  meter math reads `timebox.budget` + `spine_state.timebox_used`; grep for any 2c label
  string in `index.html` must return nothing.
- **Spike-as-mini-feature is the family-killing pitfall:** the review check is the
  side-by-side lightness glance in verification; deviation beyond "meter + one card" toward
  feature-canvas density is a defect, not polish.
- **Error path:** `timebox_used` exceeding `budget` (data error) renders the meter overrun
  segment in `--fail` with a `console.warn` rather than clamping silently (mirrors 3.3's
  iter guard). Unparseable duration strings render the raw string + warn.
- **ORG freeze discipline:** all three data extensions go through the generator with new
  invariants; `resolved_view` is additive on the evidence payload — **no mutation of the
  authored report v1/v2 values** (freeze policy).
- **Naming:** `parity` block keys lower_snake (org-data convention); spike canvas classes
  stay under `surf-*` / existing kit classes — no new prefix needed in 4.1.

## Sub-phase 4.2: Data-Analysis Flow — Pipeline Canvas, Notebook Surface & E5 Rendered Report

**Outcome:** `#/goal/CAST-461` is the real data-analysis canvas: the pipeline-DAG spine with
clickable data-stage nodes, the notebook surface with collapsible analysis cells, the
data-source list with the 8% source disagreement visibly flagged, and the **E5 headline — a
real rendered chart (data-driven inline SVG) + table + provenance-on-demand** — with the
family's single L3 ("which source do I trust?") wired as the one script-resolved rail beat
in the prototype: the scripted choice of "show both with a reconciliation note" visibly
re-renders the headline chart to the reconciled view. The flow ends in a chart, not prose
(US2 S4 / SC verification).

**Dependencies:** Phase 3 (grammar, `StageSurface`, script plumbing). Consumes 4.1's
generator batch (`resolved_view`, thin `execution`) at the E5-wiring and exec-tab steps —
all other activities can start immediately against the frozen 2a data.
**Parallel-capable with 4.1** (disjoint banner sections of `index.html`; the generator has a
single owner in 4.1).
**Estimated effort:** 1 session (~3h)

**Verification (manual click-through):**
- `#/goal/CAST-461` from disk: console clean; pipeline spine renders from `stageModels.data`
  (real vocabulary, no watermark), current step `data-03` marked; header reads the
  question-as-L1 ("Which segment drove the Q2 revenue dip?") with the analysis pill + nudge.
- Pipeline nodes are clickable (`drillInto:<data-NN>`): the sources step renders the
  **data-source list** (source rows: name, kind, freshness, headline figure) with the 8%
  finance-DB-vs-billing-export disagreement flagged in `--warn`, not buried; the analysis
  step renders the **notebook surface** — collapsible cells (collapsed by default,
  expandable; FR-007's no-hidden-state applied to cells), mono query stubs, per-cell status.
- **E5 headline:** the chart is an inline `<svg>` element (DevTools check — not an `<img>`,
  not text): grouped/annotated bar chart of the ORG series with axis labels and real `<text>`
  labels; the table renders beneath; "show the query / source lineage" opens provenance
  (sources, transforms, query stub) in exactly one click; report version chips show
  "Report v1 / Report v2 · re-run on fresh data" with v1 accessible, never deleted (FR-007).
- **Confidence/flag signal:** pre-resolution the E5 carries the ◐/flag state tied to the
  source disagreement — never a bare confident chart while the L3 is open.
- **The wired L3 beat (the flow's signature):** the L3 needs-you chip at WHAT level opens
  the rail (3 ranked options: source-of-record / show both + reconciliation note / flag for
  analyst review; none pre-selected). Advancing the script past the stop plays the user's
  choice of option (b): the headline chart re-renders to `resolved_view` (both series +
  reconciliation note), a receipt with the L3 atom's `decision_id` lands in the receipt
  trail, and the narration frames the choice as **the user's reply**, not the system
  deciding. `ORG` is untouched; reload resets to the unresolved state.
- "Next ▸" walks `SCRIPTS.data` start-to-finish: open → Guide nudge → sources beat
  (disagreement surfaced) → analysis/notebook beat → L3 stop → resolution beat (chart
  re-render) → close on the reconciled report.
- One L1 chip ("excluded 1.2% null-region rows") and the L2 ("median over mean") render from
  their atoms; exactly one L3 in the flow.
- Exec tab: thin run list, no tree. Drift spot-check: series values, source names, the "8%"
  figure all render from `ORG` (generator-edit test).

Key activities:
- **Compose the data canvas from the shared grammar:** header band, chips, exec tab, chat
  rail identical; deviated zones — spine zone renders `StageSpine` with the 2b `pipeline`
  shape (nodes navigate via the existing `drillInto` step-id grammar); work zone renders the
  notebook lane.
- **Flesh out `StageSurface`'s `notebook` kind** (Phase 3 thin version): collapsible cells
  (native `<details>` per cell — `file://`-safe, no JS dependency), mono query stubs,
  transform one-liners, per-cell status chip; full-bleed with `surfaceWhy` caption.
- **Build the data-source list rendering** for the sources step: source rows with the
  disagreement flag (`--warn` treatment + the 8% delta stated); this is plain step-artifact
  rendering inside `StageSurface` (`board`-like rows), not a new component.
- **Flesh out `EvidenceBlock`'s E5 branch into the real report:** the headline chart as a
  **pure function of the ORG series → inline SVG** (the M9 burndown idiom: hand-authored
  axes, bars, labels; existing tokens only — ink/muted for the source-of-record series,
  raspberry accent for the disagreeing series and annotations; real `<text>` elements +
  `<title>`/`<desc>` for accessibility); the data table; the provenance disclosure
  (collapsed by default); the version chips. The chart accepts either the at-rest series or
  `resolved_view.series` + note — one renderer, two states, verifiable in `#/kit`.
- **Wire the L3 + resolution beat:** rail renders from the atom; the script's resolution
  step patches a **presentation-state overlay** (additive script-driven flag selecting
  `resolved_view`) and pushes one receipt carrying the atom's id (the Phase 1/2a receipt
  mechanism, `decision_id` populated). No ORG mutation, no second decision atom.
- **Author `SCRIPTS.data` (~7 steps)** keyed on route entry; narration interpolates from
  `ORG` (the "8%", source names, the headline number).

**Design review:**
- **Prose-only is banned (US2 S4):** the verification's "inline `<svg>` element" check is
  the gate; if chart authoring runs long, the table alone is *not* an acceptable terminal
  state for the flow.
- **Chart drift risk:** zero series literals in markup or script — the SVG is generated from
  `ORG` data at render time; grep for the revenue figures in `index.html` must return
  nothing. (This is why the chart is *not* an illustration-creator raster — see
  Decisions #3.)
- **Color discipline:** the chart uses existing tokens only; if two-series contrast
  genuinely fails with the available palette, flag for reconciliation — never silently mint
  a new color token (2b's extend-only rule).
- **L3-resolution semantics:** at-rest atoms keep `chosen: false` on all options (2a gate
  invariant untouched); the resolution is a scripted presentation overlay + receipt. Whether
  a real product would mutate the atom's status is a product question, deferred (recorded in
  Decisions #6).
- **Error path:** missing/empty series renders a visible "no data" placeholder in the
  evidence zone with `console.warn` — never a blank panel or a thrown render.

## Sub-phase 4.3: FR-017 Three-Access-Tiers Parity Moment (hosted in the spike flow)

**Outcome:** A scripted beat in the spike flow reveals the side-by-side parity moment: a
faux terminal pane running the `cast` skill invocation next to the canvas/memo doing the
same with defaults, **the same E4 verdict-artifact card landing in both panes**, with the
persistent chat rail visible alongside — one screenful showing all three access tiers
(terminal / chat / canvas) over one substrate. Static depiction, no logic (playbook 02
Step 7: a parity *depiction* — and an honest one, since the real codebase materializes
`agents/cast-*.md` to both a terminal skill and a server dispatch emitting the same
contract envelope).

**Dependencies:** Sub-phase 4.1 (spike canvas + the `parity` data block).
**Parallel-capable with 4.2.**
**Estimated effort:** 0.5 session (~1.5h)

**Verification (manual click-through):**
- Advance the spike script to the parity beat: the canvas area splits to two panes —
  terminal left, canvas/memo right — with the chat rail still visible; a caption line states
  the one-substrate claim (text from `ORG.goals['CAST-452'].parity.caption`, not typed in
  markup). Three tiers identifiable in one screenshot; keep the screenshot as evidence.
- The terminal pane renders the transcript from the parity block: prompt line with the
  `cast …` command, output lines, and the artifact-landing line; IBM Plex Mono; static (no
  typing animation — HOLD SCOPE).
- **Same-artifact check:** the verdict-artifact card rendered in the terminal pane's landing
  line and in the canvas pane is the same ORG node — identical id and title (drift check:
  both read the node resolved via `parity.artifact_id`).
- The next script step exits the beat cleanly — normal spike canvas restored, `stageFocus`
  and receipts intact; reduced-motion shows a fade, no slide.
- Anchor audit: the parity layout introduces **no** element carrying any vt- name (DevTools
  search for `view-transition-name` count unchanged); transitions elsewhere still run.
- The beat never fires unprompted — exclusively script-driven.

Key activities:
- **Build the parity reveal as script-patch-driven state:** an additive script-set flag
  (e.g. `appState.parityOpen`, additive key — Phase 1 contract allows extension) toggled
  only by the spike script's patches; **no sixth op, no new `drillInto` target class** (the
  closed vocabulary stands; scripts patch state directly — that is the engine's designed
  mechanism).
- **Build the terminal pane** (`parity-*` CSS prefix): an ink-dark (`--ink`) panel with mono
  text — a deliberate, contained identity exception because it *depicts the terminal tier*,
  not Diecast chrome (see Decisions #7; slop-gate checked in 4.4). Prompt glyph, command
  line, output rows, artifact line — all from the parity data block.
- **Render the artifact landing in both panes:** the same verdict-card stub component fed
  the same resolved ORG node — pixel-equal cards, one data source.
- **Wire the script beat into `SCRIPTS.spike`** at the slot 4.1 reserved (after the verdict
  lands, before the L3 stop): reveal patch → narration naming the three tiers and the
  one-substrate claim → exit patch.

**Design review:**
- **Identity exception flagged:** the dark terminal pane is the only non-light-world surface
  in the prototype; it must read as "a window into the terminal tier" (chrome-light, mono,
  no fake window decorations beyond a minimal title bar). If the slop gate flags it, the
  fallback is a paper-light terminal treatment with a heavy mono frame — recorded in
  borderline-calls.md if taken.
- **Anchor uniqueness (the silent killer):** the parity pane must not duplicate any vt-
  name; the verification's DevTools count check is mandatory.
- **Drift:** the command string, transcript, caption, and artifact id all live in the parity
  data block — nothing typed in markup; the grep in 4.4 enforces it.
- **Scope honesty:** the chat tier is represented by the *existing* persistent rail — no
  fake chat-invocation animation is built (the spec's moment is terminal-vs-canvas with the
  rail present; playbook 02 confirms the chat leg is "invented (scripted)" by the existing
  rail).

## Sub-phase 4.4: Four-Family Stitch, Slop Gate & Drift Sweep

**Outcome:** All four families are clickable end-to-end from disk — **SC-001 and SC-005
fully met** — with `SCRIPTS = {feature, debug, spike, data}` complete; the four-spine glance
contrast is verified and captured as a 4-up screenshot; the slop gate is green on the new
surfaces; the drift grep is clean; Phase 4's decisions are appended to decisions-so-far.

**Dependencies:** Sub-phases 4.1 + 4.2 + 4.3.
**Estimated effort:** 0.5 session (~1.5h), including gate reruns

**Verification (manual click-through — the phase's headline checks):**
- From disk: each of the four goal routes (`CAST-412 / 431 / 452 / 461`) walks its script
  start-to-finish with "Next ▸", console clean throughout; the nav rail lists all four with
  family tags.
- **The 4-up glance test (SC-005):** screenshot all four canvases side by side — a viewer
  names each family in <3 seconds citing the spine shape (segment bar / loop band + ↺ /
  timebox meter / pipeline DAG). Keep the composite as evidence.
- **High-level plan verification restated and checked:** the spike flow produces a verdict
  artifact linked from a decision (`spike_ref` linkage visible both directions); the data
  flow ends in a rendered chart/table, not text; both families render the familiar-tool
  surface for their step (memo+timebox for spike, notebook+chart for analysis);
  iteration/timebox state shown cleanly (meter + extension chip; collapsed-not-deleted
  cells/versions).
- L3 budget audit: exactly one L3 per flow across all four flows (the 2a gate guarantees
  the data; this checks the *rendering* — no stray needs-you chips).
- **Slop gate (continuous, per the high-level risk table):** screenshot the four new/changed
  surfaces — spike canvas, data canvas, parity moment, E5 reconciled-report state →
  **Delegate: `/cast-preso-check-visual`** (verdict scoped to `not-generic` /
  `not-ai-aesthetic`; ignore slide-specific findings) and
  **Delegate: `/cast-preso-check-tone`** on visible copy (narration, nudge text, memo prose,
  reconciliation note — FR-018: no GPT-isms, hyphens not em dashes). Review checker output,
  rework, re-run until green; do not close the phase on a fail.
- **Drift grep re-run** (2a.3's recorded command, extended with this phase's tokens:
  `CAST-452 · CAST-461 · 180ms · 200ms · 1h40m · 8%` and the source names) across
  `prototype/` → every hit is in `data/org.js` / `data/_build/`; the 2b `#/kit` fixture
  exception, if still live, remains the one sanctioned allowlist entry.
- Reduced-motion pass over the parity reveal and any new transitions (≤200ms fades).
- Append the Phase 4 decision summary (~15 lines) to
  `docs/plan/product-revamp-diecast-decisions-so-far.md`.

Key activities:
- Stitch pass: confirm script-beat ordering in both new flows, remove any scaffolding flags,
  confirm `scriptKey` selection on all four routes, and verify the morph demo (Phase 3) still
  runs untouched — Phase 4 must not have disturbed the anchor set.
- Run the two slop-gate delegations on the four surfaces; fix and re-run until green.
- Run the extended drift grep; fix any stray literal by moving it into the generator.
- Capture the 4-up screenshot evidence; write the decisions-so-far appendix.

**Design review:**
- **Gate honesty under full autonomy:** checklist criteria pre-written (above) before the
  run; slop-gate verdicts come from the external checker agents; screenshots + verdicts
  retained; borderline passes logged to `borderline-calls.md`.
- **Parallel-phase courtesy (Phase 5):** before closing, confirm no collisions with Phase 5's
  in-flight banner sections of `index.html` (Phase 4 owns the two goal canvases + parity;
  Phase 5 owns board/hiring/layer2 sections; the generator batch was 4.1-only). If a merge
  conflict surfaces, the section-partition rule resolves it — no shared-zone edits without
  reconciliation.

## Build Order

```
            ┌──► Sub-phase 4.1 (spike canvas + generator batch) ──► Sub-phase 4.3 (FR-017 parity) ──┐
Phase 3 ────┤                                                                                       ├──► Sub-phase 4.4
            └──► Sub-phase 4.2 (data canvas; consumes 4.1's batch at E5/exec wiring) ───────────────┘     (stitch + gates)
```

**Critical path:** 4.1 → 4.3 → 4.4. Sub-phase 4.2 runs fully parallel with 4.1+4.3
(disjoint banner sections; generator single-owned by 4.1 — 4.2's only sync point is
consuming the regenerated `org.js` for `resolved_view` + thin exec). Serially the phase is
~3–3.25 sessions; with the 4.1∥4.2 parallelism it lands at ~2 sessions wall-clock, inside
the high-level 1–1.5 day / 2–3 session estimate.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4.1 | Spike canvas drifting heavy (mini-feature pitfall kills the family thesis) | Lightness glance test in verification; "meter + one card" is the spec, density is a defect |
| 4.1 | ORG mutation outside the generator | All three data extensions via `generate-org.mjs` + new invariants; diff additive-only |
| 4.1 | `spike_ref` navigation tempting a sixth op | Local disclosure (chip→callout + scroll/highlight); closed vocabulary stands |
| 4.1 | Timebox overrun / unparseable duration | `--fail` render + console.warn; never silent clamp |
| 4.2 | Prose-only analysis output (US2 S4 ban) | Inline-`<svg>` element check is the gate; table-only is not a terminal state |
| 4.2 | Chart numbers baked into markup → drift | SVG is a pure function of ORG series; grep for figures in `index.html` must be empty |
| 4.2 | New color token minted for series contrast | Existing tokens only; genuine failure → flag, never silent extension |
| 4.2 | Scripted L3 resolution mutating ORG / atom status | Presentation overlay + one receipt; ORG untouched; reload resets |
| 4.3 | Dark terminal pane vs the locked light world | Deliberate, contained exception (depicts the terminal tier); slop-gate checked; light fallback costed |
| 4.3 | Parity pane duplicating a vt- anchor name (silent transition kill) | DevTools anchor-count audit in verification |
| 4.4 | Self-judged taste under full autonomy | External slop-gate checkers + pre-written checklist; evidence retained |
| 4.4 | Parallel Phase 5 editing the same `index.html` | Banner-section partition (2b/3 precedent); Phase 4 owns its sections + the 4.1 generator batch |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| The hand-authored E5 chart runs long (the prototype's only real chart; no kit asset to lift beyond the M9 idiom) | Med–High | Lift M9's inline-SVG idiom; chart is a small pure function (bars + axes + labels, no interactivity); verify states in `#/kit`; the *reconciled* variant reuses the same renderer with a second series |
| Spike canvas reads as a shrunk feature backbone, collapsing the family contrast (SC-005) | High | "Meter + one card" spec'd in 4.1; lightness glance test; the 4-up screenshot in 4.4 is the proof artifact |
| Parity moment reads as a gimmick or fails the slop gate (dark pane, fake terminal) | Med | Honest framing (the real substrate parity exists in the codebase); minimal chrome; checker loop budgeted; light-paper fallback costed |
| The wired L3 resolution beat reads as the system deciding for the user | Med | Narration phrased as the user's reply; rail shows nothing pre-selected at rest; receipt records the user's choice with the atom id |
| Generator batch conflicts with Phase 5's parallel run | Med | Single batch in 4.1 only; Phase 5 plans no generator work on `goals[CAST-452/461]`; section-partition rule on `index.html` |
| 2c's spike/data vocabulary or 2b's timebox/pipeline spine variants land with flagged contradictions | Med (blocks 4.1/4.2) | Hard dependency stated; reconcile 2c's flag channel before building (Phase 3's rule); the `stageModels` indirection makes vocabulary edits zero-component-cost |
| Script growth makes `index.html` unwieldy (four scripts + parity + two canvases) | Low–Med | Banner sections + `parity-*`/`surf-*` prefixes; Phase 6 owns packaging |

## Open Questions

None blocking — full-autonomy mode resolved all judgment calls (logged below). For
traceability, items deferred *by design*:

- Whether resolving an L3 should mutate the decision atom's status (vs the prototype's
  presentation-overlay + receipt) → real-product design question, same family as Phase 3's
  reversal-atom deferral.
- Entry-screen routing into the spike/data flows (`#/` chooser) and base64-inlining of any
  assets → Phase 6 (FR-002; the parity pane is pure DOM/text, so it adds no asset-inlining
  work).
- Whether the parity beat deserves a driver.js walkthrough step of its own → Phase 6
  walkthrough authoring.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (re-confirmed against the high-level plan's check) | all seven specs govern cast-server runtime | None — FR-020: the prototype is greenfield; no spec applies, none contradicted; no `/cast-update-spec` action (excluded by delegation instruction) |

Note: the FR-017 parity pane *depicts* the real `agents/cast-*.md` → `bin/generate-skills` →
terminal-skill substrate as fake transcript data — reference material rendered as prototype
content, not a spec'd surface being modified.

## Decisions Made Autonomously

1. **Sub-phase split 4.1 ∥ 4.2 → 4.3 → 4.4** — the two canvases are independent data slices
   of the settled grammar (parallel sessions, disjoint banner sections); the parity moment
   needs the spike canvas + parity data; the stitch/gate pass must see all three. Matches the
   2–3 session budget with parallelism.
2. **One generator-extension batch, owned by 4.1, covering both goals** (thin `execution` ×2,
   `parity` block, `resolved_view`) — avoids two parallel sub-phases editing
   `generate-org.mjs` concurrently; 4.2 consumes the regenerated `org.js` at its E5/exec
   wiring steps and starts UI work immediately against frozen 2a data.
3. **The E5 chart is hand-authored data-driven inline SVG (M9 idiom), not an
   illustration-creator raster** — a raster would bake the series numbers into pixels,
   defeating the drift rule (numbers must render from `ORG`), and the high-level plan's own
   threshold ("for any visual richer than hand-authored inline SVG") is not met: M9 proved
   the palette carries a hand-authored chart. `/cast-preso-illustration-creator` stays
   available if the slop gate demands decorative richness, but the chart data itself stays
   SVG-from-data.
4. **The spike L3 stays an unresolved stop; the data L3 is the one script-wired rail
   resolution in Phase 4** — Phase 3 decision #10 established "rails inert except
   script-wired beats" and deferred the feature L3's *choice* to Phase 5a; playbook 05
   explicitly says the data L3 "drives which visualized output renders," which makes it the
   right (and only) place to demonstrate a resolution inside Phase 4 — and it gives the E5
   chart its best beat (the answer visibly changes with the user's call).
5. **The reconciled chart state ships as an additive `evidence.resolved_view` on CAST-461,
   not a re-reading of the authored report v1/v2** — 2a froze v2's semantics as "re-run on
   fresh data"; repurposing it as the reconciliation output would mutate frozen meaning.
   `resolved_view` is the freeze-policy-legal additive path, and the version chips keep
   their authored story.
6. **Scripted L3 resolution = presentation overlay + one receipt (`decision_id` = the L3
   atom), ORG unmutated, reload resets** — consistent with the morph-receipt mechanism and
   the 2a invariant that L3 options rest with `chosen: false`. Whether resolution should
   mutate atom status is a real-product question, deferred.
7. **The parity terminal pane renders ink-dark as a deliberate, contained identity
   exception** — it depicts the *terminal tier*, not Diecast chrome; a cream terminal would
   read as fake. Slop-gate checked in 4.4 with a light-paper fallback costed; taken-fallback
   would be recorded in borderline-calls.md.
8. **Parity beat placement: after the verdict beat, before the L3 stop** — the moment's
   payload is "the same artifact lands either way," so the artifact (the E4 verdict) must
   exist first; ending the flow on the L3 stop preserves the family's demo arc.
9. **Parity reveal is script-patch-driven via an additive appState flag — no sixth op, no
   new `drillInto` target class** — scripts patching state is the engine's designed
   mechanism; the closed 5-op vocabulary is a Phase 1 exported contract.
10. **Thin exec (run list, no dispatch tree) for both CAST-452 and CAST-461** — the shared
    grammar requires the tab; playbook 03 specifies the spike has no dispatch tree by
    default, and duplicating deep trees adds build cost with no demo payoff (HOLD SCOPE;
    mirrors Phase 3's thin-CAST-431 call). The span tree's single `RunNode` call-site rule
    is preserved.
11. **`spike_ref` navigation implemented as local disclosure (chip→callout + scroll/
    highlight), not an op** — matches how decision chips already disclose (6A→6B) in
    Phases 2b/3; both directions in ≤1 click satisfies the playbook 03 success metric.
12. **The chat tier in the FR-017 moment is the existing persistent rail** — no fake
    chat-invocation animation; playbook 02 confirms the chat leg is the scripted/invented
    one, and the rail is already on every screenful (HOLD SCOPE).
13. **The L2 timebox-extension chip renders on the meter** — the 2a-authored "extended once
    2h→3h" atom is the family's L2 beat (playbook 05); placing it on the meter shows
    L2-record-and-notify semantics without a digest surface (which is Phase 5a territory).
14. **`cast-plan-review` auto-dispatch skipped** — the run configuration in
    `product-revamp-diecast-decisions-so-far.md` states "Plan review: skipped — cross-phase
    reconciliation only" (owner-approved; consistent with Phases 1, 2a, 2b, 2c, 3).
    Recorded here; rerun manually via `/cast-plan-review` against this file if wanted.

## Suggested Revisions to Prior Sub-Phases

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
  pure-props kit pieces, so concurrent *use* is conflict-free.)
