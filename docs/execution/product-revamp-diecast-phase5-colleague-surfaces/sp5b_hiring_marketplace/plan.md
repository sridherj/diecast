# Sub-phase 5b: Hiring Funnel, Marketplace, Agent Ops & Layer-2 (US6 + US8 + US9)

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase5-colleague-surfaces/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

**"Hire. Don't install."** is a flow you can click: chat asks for an rbac-agent and the **5-screen
wizard** runs assessment → federation → stack-ranked eval report (radar + pros/cons + deep links to
real fake work) → hire (maker+checker together) → onboard. The marketplace grid shows **12 agents
across 6 archetypes** with in-card pairing and cred stats; **every avatar opens a full resume** with
service-grade ops tabs (versions, usage, monitoring); skill creation shows the near-zero-friction
private-vs-company path; and **Layer-2 is enumerable** (12 contracts, the 8-agent chain, the 6-project
portfolio).

This is the **widest sub-stream (six surfaces) and the greenfield concentration** — the hiring-funnel
middle has no preso reference. It is the **critical path** (5.0 → 5b → 5.4).

## Dependencies
- **Requires completed:** Sub-phase 5.0 (the ORG batch — `agents[].versions/monitoring`, `org.skills`,
  plus the hiring/layer2 slices already in 2a; the route stubs; the `hiring` appState key).
- **Independent of 5a/5c** (parallel-safe — disjoint routes + CSS prefixes). See the file-collision
  honesty note in the manifest.

## Estimated effort
1.75–2 sessions (~5.5–6h) — the greenfield concentration (the funnel middle has no preso reference;
endpoints a12/a13/s8b lift as visual spec only).

## Scope
**In scope:** `SCRIPTS.hiring`; the six route renderers `#/hire`, `#/marketplace`, `#/agent/:slug`,
`#/skills/new`, `#/layer2`; the `RadarChart` + `Sparkline` inline-SVG helpers.
**Out of scope (do NOT do these):** the board arc / trail / dial (5a); the reqs-doc (5c); minting a
sixth op; wiring the CAST-417 escalation; any test file; any hand-edit of `org.js`; touching the
Phase 4 canvas/parity sections.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Carries the 5.0 stubs for these routes; gains the `hire-*`/`mkt-*`/`ops-*`/`l2-*` renderers, `RadarChart`/`Sparkline`, and `SCRIPTS.hiring` |

## Detailed Steps / Key Activities

- **`SCRIPTS.hiring`** (additive script key per the Phase 3 contract; Phase 4 noted "no further script
  keys planned" — see Suggested Revisions): **~6 beats** of Guide-voiced narration whose patches drive
  `appState.hiring.step` — "hire an rbac-agent" → assessment commissioned (step 1) → federating to
  candidates (step 2) → report ready (step 3) → hire the pair (step 4) → onboard (step 5). US6's
  independent test **starts "from chat"**, so the chat rail must be a first-class driver; the wizard's
  own Next buttons set the same state, so both paths stay in sync **by construction**. **No new ops** —
  scenario steps patch state directly.
- **`#/hire` wizard** — five frames keyed on `appState.hiring.step`, with a thin step indicator (reuse
  segment-bar styling, **not a new component**):
  1. **Commission assessment** — the 5-dimension matrix from `ORG.hiring.dimensions` as a
     tunable-looking grid (pre-filled toggles/weights, static), framed "we test them on *your*
     problem" — **never a blank form**.
  2. **Federation** — "casting to 6 candidates": candidate `ColleagueCard`s in a grid with **staggered
     completion states** (4 done with ✓-and-score, 2 still in-flight pills) — **static states, no
     timers**; liveness reads from the pills.
  3. **Stack-ranked report (the centerpiece)** — a leaderboard from `ORG.hiring.candidates`; each row
     expands (`hiring.expanded`) to the eval report card: **per-dimension `RadarChart`** (hand-authored
     data-driven inline SVG — numbers render from ORG, never a raster), numeric score, judge-style
     pros/cons, and **deep links to the candidate's produced-work artifact stubs** rendered as real DOM
     (doc/diff stubs) — the credibility keystone. A **head-to-head toggle** (`hiring.compare`) shows the
     top two candidates' outputs side-by-side. This screen is an **eval report card**; a
     feature/pricing comparison grid is the **named death-state**.
  4. **Hire** — one decisive action; the maker and its checker are hired **together** (in-card pairing;
     the checker is part of the hire, never a separate card or purchase).
  5. **Onboard** — a checklist framed as ramping a teammate: connect repo · load style guide / tastes ·
     set the autonomy dial (links to `#/decisions/CAST-412`'s dial legend) — **never an API-key form**.
- **`#/marketplace`** (re-author a12): registry grid of the **12 agents** (card-density `ColleagueCard`),
  **6 archetype facet chips**, in-card `→ paired: <checker>` lockup, cred stat line from `agent.stats`,
  health/freshness badge (active / checker-flagged / benched), and a **scope badge + filter** (open
  Diecast · internal) making this **the one unified discover-and-hire browser** (US8.S3) —
  `org.skills` entries render in a slim "skills" section of the same grid with the same scope badges. A
  **"Hire for a capability →"** affordance links to `#/hire`.
- **`#/agent/:slug`** (re-author a13, fill any placeholder stats with plausible fake numbers): full
  **resume** — role, I/O contract, autonomy level, paired checker, benchmark radar (reuse `RadarChart`),
  sample-output stub, track-record panel — plus two **ops tabs** making the agent operated-like-a-service
  (US8.S2): **Versions** (SHA-pinned history with notes) and **Monitoring** (`Sparkline` compliance
  trend, cost/latency, last-N runs, **"replay →"** linking into Phase 3's execution drill-in).
  **crud-orchestrator is the deep canonical instance**; the other 11 render thin from the same
  component. **Every agent avatar on every surface links here** (enforced in 5.4).
- **`#/skills/new`** — skillification in **two frames**: (1) the near-zero-friction path — a
  terminal-styled one-liner (`/cast-skill new export-csv`, mono, **ink-on-paper — reuse Phase 4's
  parity-pane styling decision rather than minting a new terminal treatment**) + a private/company-wide
  visibility choice; (2) confirmation — the new skill's card shown in the catalogue with its `private`
  badge and a "promote to company-wide" affordance (display-only).
- **`#/layer2`** — one page, three sections (anchor-linked): the **12-contract catalogue** (cards with
  name + one-line I/O signature; 8 visibly chain-aligned, 4 cross-cutting); the **8-agent chain
  pipeline** (reuse the `StageSpine` `pipeline` shape: refine → decompose → research → synthesize →
  plan → detail → orchestrate → run, with CAST-412's current position highlighted); the **portfolio
  dashboard** (6 project tiles with shipped-through-the-workflow stats — proof by volume).

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual, from disk) — verbatim from the plan:**
- On `#/hire`, advance the wizard **both ways** — via the chat rail's scripted beats AND via direct
  Next-button clicks — through all 5 steps.
- In step 3, expand a candidate (radar + score + pros/cons render from `ORG.hiring`), follow ≥1 deep
  link to a produced-work stub, toggle head-to-head and see the top two outputs side-by-side.
- Step 4 hires the pair together (one action, checker in-card).
- On `#/marketplace`, count **12 cards / 6 archetypes**; crud-orchestrator's card reads
  **"99.9% compliant · 2 loops · 505 runs"** — identical digits to its resume and consistent with the
  dial tooltip's aggregate. Click any avatar anywhere → its resume.
- On the resume's tabs: versions list (SHA-pinned), monitoring sparkline + last-N runs + a "replay →"
  link landing on Phase 3's execution drill-in.
- `#/skills/new` completes in two frames and the new private skill appears badged in the catalogue.
- Unknown `:slug` → muted not-found strip in the shell (same rule as 5a).

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] `SCRIPTS.hiring` (~6 beats) drives `appState.hiring.step` from chat; direct Next clicks set the
      same state; both paths stay in sync; no new op.
- [ ] `#/hire` runs all 5 steps; step 3 is an eval-report card (radar + pros/cons + produced-work deep
      links + head-to-head), NOT a pricing grid; step 4 hires maker+checker together; step 5 is a
      teammate-onboarding checklist linking to the dial legend.
- [ ] `#/marketplace` shows 12 agents / 6 archetypes + scope filter; cred line digits match the resume
      and the dial tooltip aggregate (single source = `agent.stats`).
- [ ] `#/agent/:slug` renders resume + Versions + Monitoring tabs; `RadarChart`/`Sparkline` are inline
      SVG (not rasters); "replay →" lands on Phase 3's execution drill-in.
- [ ] `#/skills/new` completes in two frames; the new private skill appears badged.
- [ ] `#/layer2` shows the 12-contract catalogue + the 8-agent chain (`StageSpine` pipeline, CAST-412
      position highlighted) + the 6-project portfolio.
- [ ] Every agent avatar on these surfaces links to `#/agent/:slug`; closed 5-op set intact; 6×1 vt-
      anchors unchanged; `node --check` clean.

## Design review (verbatim from the plan)
- ⚠ **Breadth risk:** 5b owns 6 surfaces — the most in any sub-stream. Discipline: every screen must
  be a data slice through existing kit + the two SVG helpers; any layout invented twice becomes a
  shared function immediately. Flagged in the table.
- **Naming:** routes/CSS prefixes `hire-*`, `mkt-*`, `ops-*`, `l2-*` follow Phase 3/4's per-surface
  prefix convention. ✓
- **Architecture:** `RadarChart`/`Sparkline` follow the Phase 4 E5 precedent exactly (inline
  data-driven SVG, existing tokens only, never rasters). ✓
- **Anthropomorphism guard:** structure of employment (resume, report card, onboarding), none of the
  theater — no mascot faces, no "meet your AI employee" copy (FR-018). ✓
- **Edge:** unknown `:slug` → muted not-found strip in the shell (same rule as 5a).

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5b | Six surfaces — breadth blowout risk | Every screen = data slice through existing kit; second occurrence of any layout becomes a shared function |
| 5b | Hiring report could collapse into a pricing grid | Eval-report-card shape enforced: radar + pros/cons + deep links to produced work; head-to-head toggle |
| 5b | Charts as rasters would break the drift rule | `RadarChart`/`Sparkline` = data-driven inline SVG from ORG (Phase 4 E5 idiom) |
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) |

## Execution Notes
- **`SCRIPTS.hiring` is additive** (Decision 5) — US6's independent test starts "from chat", which a
  click-only wizard wouldn't honor; this deviates from Phase 4's "no further script keys planned" note.
  The four-**family** set (`feature, debug, spike, data`) stays closed; `hiring` is a demo-arc key.
- **Marketplace = the unified discover-and-hire browser** (Decision 12) — scope badges + filter, skills
  section in-grid, rather than a separate catalogue page (US8.S3 asks for *one* mechanism).
- **Agent ops fold into `#/agent/:slug` as tabs** (Decision 10) — US8 says "agent detail page"
  (singular); a separate ops route would be a near-empty page.
- **Federation uses static staggered states** (Decision 13) — no timers/animation loops; liveness via
  two in-flight pills (file:// simplicity).
- **`RadarChart`/`Sparkline` as data-driven inline SVG** (Decision 14) — rasters would violate the
  numbers-render-from-ORG drift rule; hand-author axes/labels + `<title>`/`<desc>`, existing tokens
  only. These helpers are exported for Phase 6.
- **Skillification's terminal snippet reuses Phase 4's parity-pane ink-dark treatment** (Decision 15) —
  one sanctioned terminal styling in the prototype, not two.
- **Two builder taste calls intentionally left open** (both reversible in minutes): whether `#/layer2`'s
  three sections want sub-route anchors or plain in-page anchors; and the exact head-to-head layout
  (side-by-side columns vs alternating rows) in wizard step 3. Pick either; document the pick.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
