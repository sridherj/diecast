# Product Revamp: Diecast — Phase 5: Colleague Surfaces — Board Arc · Hiring Funnel · Ops · Layer-2 · Reqs-Doc

## Overview

This phase makes the two colleague theses — **"humans + agents on one board"** and **"Hire.
Don't install."** — experienceable as real, clickable DOM, plus the US7 requirements-doc loop.
It is the largest re-authoring chunk in the prototype: the preso a08–a13 designs are lifted as
*visual spec only* and rebuilt as navigable HTML (the assignee filter actually filters; the
board→ticket→decision→escalation arc is four connected frames of one story). Because Phases 2a/2b
already shipped the data spine and the component kit, almost every surface here is a thin data
slice: the board is `ORG.board` through `ColleagueCard`, the trail is `ORG.decisions` through the
`Decision` ladder, the hiring report is `ORG.hiring` through a leaderboard + one radar-SVG helper.
The phase splits into three independent sub-streams (5a board/decisions/autonomy · 5b hiring/
marketplace/ops/Layer-2 · 5c reqs-doc loop) bracketed by a thin shared-rails sub-phase (5.0) and
a stitch-and-gates sub-phase (5.4), mirroring Phase 4's executed shape.

## Position in Overall Plan

```
Phase 1 ──► 2a ∥ 2b ∥ 2c ──► Phase 3 ──┬──► Phase 4 (spike+data canvases)
                                        └──► Phase 5 (THIS PLAN) ──► Phase 6 (polish/walkthrough)
```

Phase 5 depends on **2a (data spine) + 2b (component kit)** and reuses one Phase 3 component
(`IterationPanel`) plus Phase 3's execution data on CAST-412. It runs **in parallel with Phase 4**
— shared components only; this plan must not touch CAST-452/CAST-461 or their ORG sections
(Phase 4 ownership). Phase 6 consumes this phase's routes from the scenario-chooser entry screen
("Hire an agent" → `#/hire`).

## Operating Mode

**HOLD SCOPE** — delegation directive: "plan exactly what the high-level plan section says for
this phase, at high practical detail." Every activity below traces to the Phase 5 section of
`plan.collab.md` (US5, US6, US7, US8, US9, US10). One playbook extra (PB-05 Step 7's
"should've asked" correction loop) is explicitly **excluded** as out-of-section scope; see
Decisions Made Autonomously #7.

**NO TESTS** (owner directive, run config): no test files, suites, harnesses, or CI anywhere in
this plan. All verification is manual: open `prototype/index.html` from disk, click, observe.
Fake test-result *content* rendered as UI data is data, not tests.

## Depends On (from prior plans)

| Source | What this phase consumes |
|--------|--------------------------|
| Phase 1 | Single-file `prototype/index.html` (file:// contract — no fetch, no local ES modules); `render(appState)` + hash routing; scenario engine (`{narration, patch}` steps + `advance()`); closed op vocabulary (`morph·nudge·promote·drillInto·pin`); appState v1 keys (extend-only); vt- anchors on shell zone wrappers; design tokens + motion tokens. |
| Phase 2a | `window.ORG` via classic script `prototype/data/org.js`, authored by the seeded self-validating generator in `prototype/data/_build/` (additive extensions go through the generator, never hand-edits). Slices consumed here: `board` · `decisions` (atoms = PB-05 ADR schema verbatim + `diff` field, ids `DEC-<goal>-NN`, supersede-not-edit) · `hiring` (6 candidates, 5 dimensions, produced-work artifact stubs) · `layer2` (12 contracts: 8 chain-aligned + 4 cross-cutting; 8-chain; 6-project portfolio) · `agents` (12 / 6 archetypes, `stats:{compliancePct, loops, runs}` single source) · `humans` · `org`. Canon: CAST-412 = "Add RBAC to checkout"; **CAST-417 (roles-column drop) is THE single feature L3**; one superseded L1 pair (GraphQL→REST); marketplace cred line = crud-orchestrator 99.9% · 505 runs · 2 loops; dial trust = feature-roster aggregate 99.4% · 312 runs. |
| Phase 2b | Component kit (pure `(props)→vdom`, inline): `ColleagueCard` (card + line densities) · `Decision` ladder (`pill`/`callout`/`row` layers, atom field names verbatim) · `EscalationRail` (ranked structural weight 7A, nothing pre-selected) · `AutonomyDial` (`{value, trust}`, shipped static — **this phase wires the toggle**) · `GuideMark`. Avatar grammar: human=circle · maker=square `--maker` outline · checker=square `--checker` fill · Guide=diamond. L-badges: L1=`--ink-35`, L2=`--warn`, L3=`--rasp`; confidence glyphs ●/◐/○. vt- anchors NEVER on kit components. |
| Phase 3 | `IterationPanel` (pure, props-only) reused verbatim as the ticket activity log; `goals['CAST-412'].execution` data (`iteration {findings, rework 1/3, exits, pr+diff_stub}`); `drillInto` reuse pattern for in-goal navigation; `SCRIPTS` map + additive `appState.chat.scriptKey` contract; execution drill-in route (monitoring "replay" link target). |
| Phase 4 | Boundaries only: CAST-452/CAST-461 goals and their ORG sections are Phase 4-owned — untouchable here. Idioms adopted: data-driven inline SVG for charts (E5/M9 precedent — numbers always render from ORG, never rasters); "ORG unmutated, reload resets" for scripted state demos; L3 rails other than the data flow's stay **unresolved stops**. |

## Contracts This Phase Exports (Phase 6 consumes these)

- **Route table (final for the prototype, all hash-only):** `#/board` (real, replaces Phase 1
  stub) · `#/ticket/CAST-412` · `#/decision/:atomId` · `#/decisions/CAST-412` · `#/hire` ·
  `#/marketplace` · `#/agent/:slug` · `#/skills/new` · `#/layer2` · `#/reqs/CAST-412`.
- **appState additive keys (v1 keys untouched):** `boardFilter:'any'|'human'|'agent'|'checker'` ·
  `hiring:{step:1..5, expanded:null|candidateId, compare:false}` ·
  `autonomyLevel:'conservative'|'balanced'|'autonomous'` ·
  `reqsDoc:{openComment:null|commentId, deltaView:false}`.
- **`SCRIPTS.hiring`** (additive script key, ~6 beats) — chat-initiated hiring side-arc.
- **`DigestNotice` component** — the one inform-without-nagging atom, instantiated for the L2
  decision digest (5a) AND the US7 write-back notice (5c).
- **Inline-SVG helpers:** `RadarChart` (per-dimension candidate eval; also the resume benchmark)
  and `Sparkline` (monitoring compliance trend) — both data-driven from ORG, M9 idiom.
- **ORG additive extensions** (via the 2a generator): `goals['CAST-412'].requirements_doc`,
  `agents[].versions/monitoring`, `org.skills`, `dial_demo` atom marker (details in 5.0).
- Drift-grep additions and the slop-gate surface list for Phase 6's full re-run.

---

## Sub-phase 5.0: Shared Rails — ORG Extension, Route Skeleton & the Digest Atom

**Outcome:** All data and plumbing the three sub-streams need exists, so 5a/5b/5c can run fully
in parallel with zero shared-file contention beyond their own route renderers: the single ORG
generator batch has landed and re-validated, all ten Phase 5 routes resolve to labeled stubs,
the new appState keys exist, and `DigestNotice` renders from props.

**Dependencies:** Phases 1, 2a, 2b executed (3's `IterationPanel` needed only from 5a onward).

**Estimated effort:** 0.5 session (~1.5h)

**Verification:** Re-run the generator — it emits with all old + new invariants green. Open
`prototype/index.html` from disk; navigate to each of the ten routes via the address bar; each
renders a labeled stub inside the standard shell (nav rail · CanvasFrame · ChatRail). `window.ORG`
shows the new slices in devtools. No console errors.

Key activities:

- **ONE generator batch** (extend `prototype/data/_build/`, seed 42, output committed; never
  hand-edit `org.js`) adding, additively:
  - `goals['CAST-412'].requirements_doc = { classification:'feature', version:'v2',
    version_history:[{v:'v1', date}, {v:'v2', date, summary}], elements:[{id:'req-NN',
    level:1|2|3, kind:'intent'|'story'|'fr'|'constraint', text, children:[ids],
    decision_refs:[atomIds]}], comments:[{id, anchor:'req-NN', author_id, author_role:'pm'|'eng',
    state:'open'|'resolved', thread:[{who, text, time}]}], delta:[{anchor:'req-NN', change,
    origin_phase:'planning'}], writeback:{origin_phase:'planning', summary, anchors:['req-NN']} }`
    — content derived from the CAST-412 RBAC story; exactly ONE comment thread, with one PM
    commenter (the single PM-framed moment; PM persona comes from `ORG.humans`).
  - Agent-ops fields on `agents[]`: `versions:[{sha7, date, note}]` (≥1 per agent; 4–5 entries
    on crud-orchestrator, 1–2 elsewhere) and `monitoring:{trend:[12 floats], cost_p50_usd,
    latency_p50_s, recent_runs:[{id, when, status}]}` (full depth on crud-orchestrator, thin
    elsewhere). All credibility numbers remain derived from the same `stats` fields (single
    source — no second copy of 99.9/505).
  - `org.skills:[{slug, title, visibility:'private'|'company', owner, created, blurb}]` — 3
    company-wide skills + the pre-staged demo skill `cast-export-csv` (private). Nested under
    the existing `org` key because top-level ORG keys are frozen.
  - `dial_demo:true` marker on exactly one CAST-412 **L2** atom (the planning-phase
    "split FR-014"-style atom from 2a's set) — the atom the dial toggle visibly promotes.
  - **New invariants (generator refuses to emit on violation):** exactly one `dial_demo` atom
    org-wide and it is L2; `requirements_doc` element ids unique, every comment/delta/writeback
    anchor resolves to an element, exactly one comment author has role `pm`; every agent has ≥1
    version; skill slugs are lowercase `cast-*`; CAST-452/CAST-461 sections byte-identical to
    the Phase 4 batch (parallel-phase guard).
- **Route skeleton:** add the ten hash cases to the router with labeled stub renderers; add nav
  rail entries `Board · Hire · Layer-2` (goal routes keep their existing entries; `#/kit` stays
  hidden). No new vt- names anywhere — new routes reuse the existing shell zone wrappers.
- **appState additive keys** (`boardFilter`, `hiring`, `autonomyLevel`, `reqsDoc`) initialized in
  the state literal; v1/v1.1 keys untouched.
- **`DigestNotice` component** (pure props): `{glyph:'⚖'|'↺', summary, rows:[{label, body}]}` —
  non-modal strip, rows expand via native `<details>`. Fixture-render it on `#/kit`.

**Design review:**
- **Parallel-phase data guard:** the generator batch is the one file both Phase 4 and Phase 5
  touch. Mitigation is the byte-identical invariant on CAST-452/461 sections plus running this
  batch as one commit before sub-streams start. ⚠ flagged in the consolidated table.
- Naming: route names mirror existing `#/goal/:id` convention; additive appState keys follow
  Phase 3/4 precedent (`stageFocus`, `parityOpen`). ✓
- file:// constraint respected: all new data ships inside `org.js`; no fetch. ✓

---

## Sub-phase 5a: Board Arc, Decision Trail & the Autonomy Dial (US5 + US10)

**Outcome:** Board → ticket CAST-412 → decision artifact → L3 escalation read as **four frames of
one story** with consistent chrome and canonical vocabulary; the assignee filter actually filters
(4 working states); the ticket shows the maker-checker activity log with inline M04/S03/R02
violations, rework 1/3, and the PR link; the cross-phase decision trail renders diff-first with
the superseded GraphQL→REST pair struck through; and the autonomy dial toggle **visibly promotes
an L2 decision into an L3-style stop** (SC-007's autonomy-gated moment, shown live).

**Dependencies:** Sub-phase 5.0; Phase 3 executed (`IterationPanel` + CAST-412 execution data).

**Estimated effort:** 1.25–1.5 sessions (~4–4.5h)

**Verification (manual, from disk):** Click the four-frame arc end-to-end: `#/board` → ticket
card CAST-412 → `#/ticket/CAST-412` → a log entry's "next › decision" → `#/decision/DEC-CAST-412-NN`
→ from the trail, open the CAST-417 L3 → escalation rail with three ranked options, nothing
pre-selected → "escalated to me" link loops back to the board with the filter applied. Click all
four filter chips — each hides exactly the wrong cards. On `#/decisions/CAST-412`, flip the dial
Balanced→Conservative and watch the `dial_demo` L2 row promote into a pinned stop-and-confirm
card; flip back and it demotes. Reload resets everything (ORG unmutated).

Key activities:

- **Real `#/board`** (re-author preso a08/s8a as DOM; lift layout/vocabulary only, zero SVG
  geometry): four columns (Backlog · In progress · In review · Done) rendered from `ORG.board`;
  humans and agents in the **same assignee stack** — same card format, same columns, distinguished
  only by the 2b avatar grammar (no "Automations" lane, ever). Ticket cards carry the
  `ColleagueCard` line density + in-flight pill (work visible without opening the ticket).
  Header: assignee filter chip row `Any · Human · Agent · Checker` driven by `appState.boardFilter`
  (plain click handlers + re-render — **not** ops; the op vocabulary stays closed at 5), the
  framing line **"Publishes INTO your PM tool. It does not replace Linear / Jira / GitHub
  Projects."**, and an escalation inbox badge `@you · 1` (top-right) linking to the CAST-417
  decision frame.
- **`#/ticket/CAST-412`** (re-author a09): header = ticket title + maker-checker paired lockup +
  3-segment rework meter (1/3). Body = **Phase 3's `IterationPanel` reused verbatim**, fed by
  `goals['CAST-412'].execution.iteration` — iteration bands as first-class history, checker
  findings inline with rule codes M04/S03/R02 (the compliance *checklist*, never a lone
  pass/fail badge), named exits, and the resulting **PR #-link in the footer** (link on surface,
  diff behind the execution drill-in, per the locked PR-placement call). Decision `pill` chips
  render on log entries whose atoms list them in `influenced[]`, opening the 6B callout popover;
  one entry carries the "next › decision" link into the artifact frame.
- **`#/decision/:atomId`** — the decision artifact frame: the `Decision` ladder's full record
  (6C layer, full-frame) rendering every atom field verbatim (id, reversibility badge, decision,
  rationale, options_considered, consequences, revisit_if, originating agent/phase, timestamp,
  supersedes/superseded_by links, spike_ref when present, `diff` line). **Branch:** when the atom
  is L3 + `awaiting_human` (CAST-417, roles-column drop), the frame additionally renders the
  **`EscalationRail`** — three pre-framed options with consequence lines, ranked as structural
  weight (hero/outline/ghost), **nothing pre-selected**, evidence pack ("what I want / what I
  tried"), expiry line. The rail is an **unresolved stop** — options don't wire (only Phase 4's
  data L3 resolves, prototype-wide consistency); the frame's "escalated to me →" link loops back
  to `#/board` with `boardFilter` applied.
- **`#/decisions/CAST-412`** — the cross-phase trail: one diff-first row per atom
  (`time · phase · L-badge · title · who · diff`), filter chips for phase / actor
  (any·human·agent — same chrome as the board filter) / L-level; the superseded GraphQL→REST
  pair renders struck-through with a "superseded by →" link; row click navigates to
  `#/decision/:atomId`. The trail proves chip↔row ID-match: same atoms as the ticket chips.
- **`AutonomyDial` wiring** (the 2b component, static until now) at the trail header: segmented
  Conservative / ●Balanced / Autonomous + the teaching legend + earned-trust tooltip reading the
  feature-roster aggregate (99.4% · 312 runs) from `agent.stats` (single source). Toggling sets
  `appState.autonomyLevel` and re-renders: under Conservative, the `dial_demo` L2 atom leaves
  the digest/trail flow and renders as a **pinned stop-and-confirm card** at the top of the
  trail (escalation-card treatment + "now requires your OK" line) and its L2 badge re-tints —
  the visible threshold shift (a dial that only changes ping frequency is a gimmick). No receipt
  is written; ORG is never mutated; reload resets.
- **L2 digest strip** above the trail via `DigestNotice`: "⚖ 2 decisions made while you were
  away", rows expanding to the 6B callout. This is the minimal substrate the dial promotion
  needs (the L2 must visibly come *from* a quiet digest), and it instantiates the same component
  5c uses for the write-back notice — one inform-without-nagging atom, twice.

**Design review:**
- **Op-vocabulary discipline:** filter chips, dial, trail filters are plain handlers mutating
  additive appState keys — the closed 5-op set is for scripted chat actions only. ✓ (matches
  Phase 3's precedent of not minting ops for UI state).
- **Escalation consistency:** CAST-417 rail = unresolved stop, reusing the single
  `EscalationRail` component (US5 and US10 are the same mechanism — a second escalation UI is
  forbidden). ✓
- **Error/edge:** unknown `:atomId` or ticket id in the hash → render the board/trail with a
  muted "not found" strip, never a blank canvas (zero silent failures).
- ⚠ **Dial-demo honesty:** promoting an already-`recorded` atom into a "stop" is a scripted
  illusion — keep the card's copy in the conditional voice the legend establishes and reset on
  reload, so it reads as a live policy shift, not falsified history. Flagged in the table.

---

## Sub-phase 5b: Hiring Funnel, Marketplace, Agent Ops & Layer-2 (US6 + US8 + US9)

**Outcome:** "Hire. Don't install." is a flow you can click: chat asks for an rbac-agent and the
5-screen wizard runs assessment → federation → stack-ranked eval report (radar + pros/cons +
deep links to real fake work) → hire (maker+checker together) → onboard. The marketplace grid
shows 12 agents across 6 archetypes with in-card pairing and cred stats; every avatar opens a
full resume with service-grade ops tabs (versions, usage, monitoring); skill creation shows the
near-zero-friction private-vs-company path; and Layer-2 is enumerable (12 contracts, the 8-agent
chain, the 6-project portfolio).

**Dependencies:** Sub-phase 5.0. Independent of 5a/5c (parallel-safe).

**Estimated effort:** 1.75–2 sessions (~5.5–6h) — the greenfield concentration (the funnel
middle has no preso reference; endpoints a12/a13/s8b lift as visual spec only).

**Verification (manual, from disk):** On `#/hire`, advance the wizard both ways — via the chat
rail's scripted beats AND via direct Next-button clicks — through all 5 steps. In step 3, expand
a candidate (radar + score + pros/cons render from `ORG.hiring`), follow ≥1 deep link to a
produced-work stub, toggle head-to-head and see the top two outputs side-by-side. Step 4 hires
the pair together (one action, checker in-card). On `#/marketplace`, count 12 cards / 6
archetypes; crud-orchestrator's card reads "99.9% compliant · 2 loops · 505 runs" — identical
digits to its resume and consistent with the dial tooltip's aggregate. Click any avatar anywhere
→ its resume. On the resume's tabs: versions list (SHA-pinned), monitoring sparkline + last-N
runs + a "replay →" link landing on Phase 3's execution drill-in. `#/skills/new` completes in
two frames and the new private skill appears badged in the catalogue.

Key activities:

- **`SCRIPTS.hiring`** (additive script key per the Phase 3 contract; see Suggested Revisions —
  Phase 4 had noted "no further script keys planned"): ~6 beats of Guide-voiced narration whose
  patches drive `appState.hiring.step` — "hire an rbac-agent" → assessment commissioned (step 1)
  → federating to candidates (step 2) → report ready (step 3) → hire the pair (step 4) → onboard
  (step 5). US6's independent test starts "from chat", so the chat rail must be a first-class
  driver; the wizard's own Next buttons set the same state, so both paths stay in sync by
  construction. No new ops — scenario steps patch state directly.
- **`#/hire` wizard** — five frames keyed on `appState.hiring.step`, with a thin step indicator
  (reuse segment-bar styling, not a new component):
  1. **Commission assessment** — the 5-dimension matrix from `ORG.hiring.dimensions` as a
     tunable-looking grid (pre-filled toggles/weights, static), framed "we test them on *your*
     problem" — never a blank form.
  2. **Federation** — "casting to 6 candidates": candidate `ColleagueCard`s in a grid with
     staggered completion states (4 done with ✓-and-score, 2 still in-flight pills) — static
     states, no timers; liveness reads from the pills.
  3. **Stack-ranked report (the centerpiece)** — a leaderboard from `ORG.hiring.candidates`;
     each row expands (`hiring.expanded`) to the eval report card: **per-dimension `RadarChart`**
     (hand-authored data-driven inline SVG — numbers render from ORG, never a raster), numeric
     score, judge-style pros/cons, and **deep links to the candidate's produced-work artifact
     stubs** rendered as real DOM (doc/diff stubs) — the credibility keystone. A **head-to-head
     toggle** (`hiring.compare`) shows the top two candidates' outputs side-by-side. This screen
     is an eval report card; a feature/pricing comparison grid is the named death-state.
  4. **Hire** — one decisive action; the maker and its checker are hired **together** (in-card
     pairing; the checker is part of the hire, never a separate card or purchase).
  5. **Onboard** — a checklist framed as ramping a teammate: connect repo · load style guide /
     tastes · set the autonomy dial (links to `#/decisions/CAST-412`'s dial legend) — never an
     API-key form.
- **`#/marketplace`** (re-author a12): registry grid of the 12 agents (card-density
  `ColleagueCard`), 6 archetype facet chips, in-card `→ paired: <checker>` lockup, cred stat
  line from `agent.stats`, health/freshness badge (active / checker-flagged / benched), and a
  **scope badge + filter** (open Diecast · internal) making this the one unified
  discover-and-hire browser (US8.S3) — `org.skills` entries render in a slim "skills" section of
  the same grid with the same scope badges. A "Hire for a capability →" affordance links to
  `#/hire`.
- **`#/agent/:slug`** (re-author a13, fill any placeholder stats with plausible fake numbers):
  full **resume** — role, I/O contract, autonomy level, paired checker, benchmark radar (reuse
  `RadarChart`), sample-output stub, track-record panel — plus two **ops tabs** making the agent
  operated-like-a-service (US8.S2): **Versions** (SHA-pinned history with notes) and
  **Monitoring** (`Sparkline` compliance trend, cost/latency, last-N runs, "replay →" linking
  into Phase 3's execution drill-in). crud-orchestrator is the deep canonical instance; the
  other 11 render thin from the same component. **Every agent avatar on every surface links
  here** (enforced in 5.4).
- **`#/skills/new`** — skillification in two frames: (1) the near-zero-friction path — a
  terminal-styled one-liner (`/cast-skill new export-csv`, mono, ink-on-paper — reuse Phase 4's
  parity-pane styling decision rather than minting a new terminal treatment) + a
  private/company-wide visibility choice; (2) confirmation — the new skill's card shown in the
  catalogue with its `private` badge and a "promote to company-wide" affordance (display-only).
- **`#/layer2`** — one page, three sections (anchor-linked): the **12-contract catalogue**
  (cards with name + one-line I/O signature; 8 visibly chain-aligned, 4 cross-cutting); the
  **8-agent chain pipeline** (reuse the `StageSpine` `pipeline` shape: refine → decompose →
  research → synthesize → plan → detail → orchestrate → run, with CAST-412's current position
  highlighted); the **portfolio dashboard** (6 project tiles with shipped-through-the-workflow
  stats — proof by volume).

**Design review:**
- ⚠ **Breadth risk:** 5b owns 6 surfaces — the most in any sub-stream. Discipline: every screen
  must be a data slice through existing kit + the two SVG helpers; any layout invented twice
  becomes a shared function immediately. Flagged in the table.
- **Naming:** routes/CSS prefixes `hire-*`, `mkt-*`, `ops-*`, `l2-*` follow Phase 3/4's
  per-surface prefix convention. ✓
- **Architecture:** `RadarChart`/`Sparkline` follow the Phase 4 E5 precedent exactly (inline
  data-driven SVG, existing tokens only, never rasters). ✓
- **Anthropomorphism guard:** structure of employment (resume, report card, onboarding), none of
  the theater — no mascot faces, no "meet your AI employee" copy (FR-018). ✓
- **Edge:** unknown `:slug` → muted not-found strip in the shell (same rule as 5a).

---

## Sub-phase 5c: Requirements-Doc Loop (US7)

**Outcome:** `#/reqs/CAST-412` renders the requirements vision: classification pill up top,
L1/L2/L3 progressive disclosure over the element hierarchy, one anchored inline comment thread
(with the prototype's single PM-framed moment), a v1→v2 change summary anchored to affected
elements, and the "requirements updated from planning — review the delta" write-back notice —
all reading from `goals['CAST-412'].requirements_doc`.

**Dependencies:** Sub-phase 5.0. Independent of 5a/5b (parallel-safe).

**Estimated effort:** 0.75–1 session (~2.5–3h)

**Verification (manual, from disk):** Open `#/reqs/CAST-412`: pill + version chip visible;
collapse/expand L2 and L3 levels via disclosure; click the commented element → the thread opens
anchored beside it, the PM commenter visibly role-tagged, open→resolved state togglable
(display states); the write-back notice names the originating phase and clicking it opens the
delta view, whose rows highlight/scroll to their anchored elements; the decision chip on the
REST-over-GraphQL element opens its 6B popover and matches the trail row's ID on
`#/decisions/CAST-412`.

Key activities:

- **Doc render:** header = workflow **classification pill** ("feature", mono treatment) +
  version chip (v2) + version history popover. Body = the element hierarchy with **L1/L2/L3
  progressive disclosure via native `<details>`** (Phase 4's notebook-cell precedent): L1
  always visible, L2 one disclosure in, L3 nested — hierarchy depth is expressed
  **typographically** (size/indent/weight), explicitly NOT with the colored L-badges (see
  design review).
- **Anchored inline comment thread:** exactly one element carries a comment affordance; clicking
  opens the side-anchored thread (2–3 messages) where one commenter is the **PM** (circle
  avatar + role tag from `ORG.humans`) — the one PM-framed moment in the whole prototype; the
  thread shows open/resolved states. `appState.reqsDoc.openComment` drives it.
- **Version change summary (delta review):** `reqsDoc.deltaView` toggles a diff-first change
  list (same row grammar as the decision trail) anchored to affected elements — review the
  delta, not re-read the doc.
- **Write-back notice:** `DigestNotice` instance at the top — "↺ requirements updated from
  planning — review the delta", naming the originating phase; opens `deltaView`. Same component
  as 5a's L2 digest by contract.
- **Decision chip on a requirement element** (the REST-over-GraphQL atom via its `influenced[]`
  anchor) — completing chip anchor-generality across all three anchor types (ticket: 5a;
  canvas stage: Phase 3; requirements element: here).
- **Entry links:** nav-rail/goal-header path onto the doc from the CAST-412 canvas's
  requirements stage (an `<a href="#/reqs/CAST-412">` on the stage's doc surface — no new op),
  so the doc is reachable in-flow, not only by URL.

**Design review:**
- ⚠ **L1/L2/L3 collision (the sharpest flag in this phase):** US7's L1/L2/L3 are *hierarchy
  levels*; the decision system's L1/L2/L3 are *reversibility*. Both appear on this one screen
  (hierarchy + a decision chip). Rule: hierarchy = typographic depth only, never badges;
  reversibility = the 2b colored badge always prefixed with ⚖ context. Flagged in the table.
- **Reuse integrity:** the write-back notice and the L2 digest are one component (PB-05 hand-off
  #3) — verified by there being exactly one `DigestNotice` in the source. ✓
- **Edge:** delta rows / comments anchoring to a collapsed L3 element must auto-expand the
  disclosure chain on navigate (zero silent failures — a highlight inside a closed `<details>`
  is invisible).

---

## Sub-phase 5.4: Stitch, Cross-Links, Slop Gate & Drift Sweep

**Outcome:** The three sub-streams read as one product: every cross-surface link lands, the
phase's surfaces pass the slop gate, the drift grep is clean, and the Phase 5 verification
paragraph from the high-level plan passes as one continuous click-through.

**Dependencies:** Sub-phases 5a + 5b + 5c.

**Estimated effort:** 0.5–0.75 session (~2h), including gate reruns

**Verification (manual, from disk — this IS the phase gate):** The high-level Phase 5
verification, verbatim: the four-frame arc reads as one story with consistent chrome; the
assignee filter works; the ticket shows the activity log with inline violations + rework 1/3 +
PR link; the hiring funnel clicks assessment → federation → stack-ranked report → hire →
onboard; the dial toggle visibly promotes an L2 to an L3 stop. Plus: every avatar on board,
ticket log, hiring report, marketplace, and trail opens the right resume; both slop-gate
checkers pass on all six gated surfaces; the drift grep returns hits only from `org.js`.

Key activities:

- **Cross-link audit (the colleague-thesis glue):** every agent avatar → `#/agent/:slug` (an
  avatar that goes nowhere is a tool icon); board escalation badge → CAST-417 frame →
  "escalated to me" → board (the loop-back); ticket PR link present; trail row ↔ decision frame
  ↔ ticket chip ID-match spot-check; onboarding's dial link; reqs-doc ↔ canvas entry link;
  marketplace "Hire for a capability" → `#/hire`.
- **Slop gate** on six surfaces: board · ticket log · CAST-417 escalation frame · stack-ranked
  report · agent resume · reqs-doc.
  → Delegate: `/cast-preso-check-visual` + `/cast-preso-check-tone` on screenshots of the six
  surfaces, scoped (as in Phases 2b–4) to not-generic / not-ai-aesthetic. Review output; fix
  flags and re-run failed surfaces.
- **Drift grep extension + re-run:** add `CAST-417 · PR #2341-canon (use the generator's actual
  PR number) · 99.4 · 312 · 6 candidates · 12 contracts · 8-agent chain · the 5 dimension names
  · the PM persona's name · cast-export-csv` to the Phase 3/4 grep set; all canonical strings
  must originate from `org.js` only (2b's `#/kit` fixtures remain the one sanctioned exception
  until its data swap).
- **Script + state sanity:** `SCRIPTS.hiring` advances cleanly alongside direct wizard clicks;
  dial/filters/disclosures all reset on reload (no persistence, ORG unmutated); vt- transition
  spot-check on `#/board` ↔ goal routes (no duplicate-anchor regressions from new routes).

**Design review:** no new flags — this sub-phase exists to enforce the earlier ones.

---

## Build Order

```
            Sub-phase 5.0  (shared rails: ORG batch · routes · DigestNotice)
                  │
      ┌───────────┼───────────────┐
      ▼           ▼               ▼
 Sub-phase 5a  Sub-phase 5b   Sub-phase 5c
 (board arc ·  (hiring funnel ·  (reqs-doc
  trail · dial)  marketplace ·     loop)
                 ops · Layer-2)
      └───────────┼───────────────┘
                  ▼
            Sub-phase 5.4  (stitch · slop gate · drift sweep)
```

**Critical path:** 5.0 → 5b → 5.4 (5b is the widest sub-stream and the greenfield
concentration). 5a ∥ 5b ∥ 5c are fully parallel after 5.0 — separate routes, separate CSS
prefixes, shared code only through 2b kit + 5.0's `DigestNotice`/helpers.

**Total estimate:** ~4.75–5.75 sessions — above the high-level envelope (3–4 sessions). Honest
call, not scope creep: the high-level effort line predates the NO-TESTS-era detailing of six
US-bearing surfaces in 5b. Per the owner's no-cut policy, extend the timeline rather than trim
US7/US8/US9.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5.0 | Generator batch is the one Phase4∥Phase5 shared file | Byte-identical invariant on CAST-452/461 sections; land the batch as one commit before sub-streams start |
| 5a | UI state (filter/dial) could tempt new ops | Plain handlers + additive appState keys only; op vocabulary stays closed at 5 |
| 5a | Dial demo promotes a `recorded` atom — scripted illusion | Conditional-voice copy, pinned-card treatment, reload resets, ORG unmutated |
| 5a | Second escalation UI risk (US5 vs US10) | One `EscalationRail`, two instantiations; CAST-417 stays an unresolved stop |
| 5b | Six surfaces — breadth blowout risk | Every screen = data slice through existing kit; second occurrence of any layout becomes a shared function |
| 5b | Hiring report could collapse into a pricing grid | Eval-report-card shape enforced: radar + pros/cons + deep links to produced work; head-to-head toggle |
| 5b | Charts as rasters would break the drift rule | `RadarChart`/`Sparkline` = data-driven inline SVG from ORG (Phase 4 E5 idiom) |
| 5c | L1/L2/L3 double meaning (hierarchy vs reversibility) on one screen | Hierarchy = typographic depth, no badges; reversibility = ⚖-prefixed colored badge only |
| 5c | Anchored highlight inside collapsed `<details>` is invisible | Auto-expand the disclosure chain on comment/delta navigation |
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cargo-culting preso a08–a13 SVG geometry instead of re-authoring as DOM | High | Lift layout/vocabulary only; the 5.4 click-through gate requires every interaction (filter, expand, link) to actually work |
| 5b's greenfield funnel middle eats the budget | Med | It's last-known-design-free by construction; the wizard reuses ColleagueCard/segment-bar/Radar everywhere; owner policy = extend, don't cut |
| Fake-data drift across 10 new routes | Med | Everything renders from `org.js`; extended drift grep in 5.4; generator invariants |
| Dial toggle reads as a gimmick (ping-frequency knob) | Med | The threshold shift is shown structurally (digest row → pinned stop card), earned-trust tooltip wired to the single-source stat |
| L3 over-asking kills the colleague thesis | High | Data already enforces exactly one L3/flow (2a invariant); this phase adds zero new L3 atoms |
| Parallel-phase collision with Phase 4 (ORG, SCRIPTS) | Med | 5.0 byte-identical guard; `SCRIPTS.hiring` is purely additive; no shared route or CSS prefix |

## Open Questions

None blocking — full-autonomy directive; every judgment call is recorded below. Two
execution-time taste calls intentionally left to the builder (both reversible in minutes):
whether `#/layer2`'s three sections want sub-route anchors or plain in-page anchors, and the
exact head-to-head layout (side-by-side columns vs alternating rows) in wizard step 3.

## Spec References

- `docs/specs/_registry.md` checked: all existing specs govern the cast-server runtime — **none
  govern this deliverable** (FR-020: greenfield; prototype HTML implies nothing about production
  architecture). Per the delegation directive, no `/cast-update-spec` flow is invoked.
- Conflicts found: none.

## Decisions Made Autonomously

1. **Sub-phase shape 5.0 → (5a ∥ 5b ∥ 5c) → 5.4** — mirrors Phase 4's executed
   batch-then-streams-then-gates precedent; 5.0 owns the single generator batch so the three
   streams never contend on `org.js`.
2. **Plan review skipped** — run config ("Plan review: skipped — cross-phase reconciliation
   only") overrides this agent's Step-10 auto-dispatch default; all four prior phases set the
   precedent.
3. **CAST-417's escalation rail stays an unresolved stop** — Phase 4 locked the data L3 as the
   ONE wired rail resolution; wiring a second would break prototype-wide consistency.
4. **AutonomyDial lives on `#/decisions/CAST-412`'s trail header**, not the Phase 3 goal canvas —
   keeps the demo self-contained in 5a's surfaces and avoids re-opening a Phase 3-owned screen
   during a parallel phase; PB-05 only requires the toggle beat to be visible somewhere per-goal.
5. **`SCRIPTS.hiring` added** (additive) — US6's independent test starts "from chat", which a
   click-only wizard wouldn't honor; deviation from Phase 4's "no further script keys planned"
   note is flagged below.
6. **One route `#/decision/:atomId` serves both the decision-artifact and escalation frames**,
   branching on status/level — four story frames with shared chrome beats two near-identical
   routes.
7. **PB-05 Step 7 ("should've asked" correction loop) excluded** — HOLD SCOPE: it is not in the
   high-level Phase 5 section; noted as natural Phase 6+ candy if time allows.
8. **Minimal L2 digest strip included in 5a** even though the high-level section doesn't name
   it — the dial promotion needs a quiet state to promote *from*, and the component is already
   mandated by 5c's write-back notice (one `DigestNotice`, two instantiations).
9. **`org.skills` as an additive nested slice** — ORG top-level keys are frozen (2a), so
   skillification data nests under the existing `org` key.
10. **Agent ops folded into `#/agent/:slug` as tabs** (Resume · Versions · Monitoring) — US8
    says "agent detail page" (singular); a separate ops route would be a near-empty page.
11. **PB-04's Invoice-CRUD spine snippet and circle/hex avatar grammar treated as superseded** —
    2a locked CAST-412 = "Add RBAC to checkout"; 2b locked squares/diamond grammar. Playbook
    layout/vocabulary lifted, its stale data/grammar dropped.
12. **Marketplace = the unified discover-and-hire browser** (scope badges + filter, skills
    section in-grid) rather than a separate catalogue page — US8.S3 asks for *one* mechanism.
13. **Federation screen uses static staggered states** (no timers/animation loops) — file://
    simplicity; liveness conveyed by two in-flight pills.
14. **`RadarChart`/`Sparkline` as data-driven inline SVG helpers** — Phase 4's E5 precedent;
    rasters would violate the numbers-render-from-ORG drift rule.
15. **Skillification's terminal snippet reuses Phase 4's parity-pane ink-dark treatment** —
    one sanctioned terminal styling in the prototype, not two.
16. **Effort stated honestly at ~4.75–5.75 sessions** vs the 3–4 envelope — owner policy is
    extend-don't-cut; under-promising here beats trimming US7/US8/US9 silently.
17. **Slop-gate surface list set to six** (board, ticket, escalation, report, resume, reqs-doc)
    — the per-phase-gates precedent (Phases 3/4 gated 4 surfaces each) scaled to this phase's
    surface count; Phase 6 re-gates everything anyway.

## Suggested Revisions to Prior Sub-Phases

1. **Phase 4 — "SCRIPTS complete `{feature, debug, spike, data}` … no further script keys
   planned":** Phase 5 adds the additive `SCRIPTS.hiring` key for the US6 chat-initiated
   side-arc. No existing key or beat is touched; the Phase 3 scriptKey contract explicitly
   supports additive keys. Suggest amending the Phase 4 note to "no further *family* script
   keys planned" — the four-family set does remain closed.
2. **Phase 2a — ORG additive extensions:** this phase extends ORG via the generator
   (`goals['CAST-412'].requirements_doc`, `agents[].versions/monitoring`, `org.skills`, the
   `dial_demo` marker + new invariants). This follows 2a's stated additive-extension policy and
   Phase 3's generator-batch precedent — listed for reconciliation visibility, not as a
   conflict.
