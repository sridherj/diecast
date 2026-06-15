# Design Decisions — Locked Component Spec

**Date:** 2026-06-11 · **Authority:** owner blessed the Diecast design system + component gallery
as the starting point and delegated component picks ("make meaningful choices and proceed").
**Reference:** `design-samples/component-gallery.html` (retained as the canonical visual reference),
`design-samples/option-e-diecast-light.html` (the blessed world).

## Identity (owner decision, Q#15)

- **Pure Diecast identity, one light world.** Cream `#F5F4F0` bg, white surfaces, ink `#1A1A28`,
  raspberry `#D6235C` as the single status accent, IBM Plex Mono (machine voice/headings) +
  DM Sans (body). No dark register. WHAT/HOW separation via surface tone (`#EFEDE7` + rule),
  never a theme flip. Refinements welcome during build.
- Agent hues: maker `#3B5BB0` (info-blue), checker `#6B47B0` (focus-violet) — agent chrome only.
- Hard slop-gate stands: no glass/gradient/glow/orb; cast-preso `not-generic`/`not-ai-aesthetic`
  checkers gate every screen.

## Component picks (from the gallery)

| # | Component | Pick | Why |
|---|-----------|------|-----|
| 1 | Feature stage spine | **1B segment bar** | Strongest at-a-glance progress; labeled segments read without counting dots; the accent-filled current segment is the clearest "you are here" of the three. |
| 2 | Debug-loop spine | **2B staged band + counter** | Keeps the same zone grammar as 1B (band of stages) while the ↺ + "iter 2/3" badge makes the loop unmistakable — maximizes the SC-005 contrast that matters (shape), not chrome divergence. **2C's hypothesis ledger is not lost:** it is the work-zone content (the E2 Confirm/Refute Ledger), not the spine. |
| 3 | Nudged next step | **3B nudge card with "why now"** | The why-line is the opinionated-defaults thesis made visible (FR-003): the product doesn't just point, it justifies. 3A loses the why; 3C reads as a dismissible banner. |
| 4 | Colleague lockup | **4C mini-card (canonical) + 4B paired-avatars line (compact density of the same component)** | One component, two densities: 4C on board/marketplace/hiring surfaces where the stat footer ("99.9% · 505 runs") carries credibility; 4B inline in activity logs/dispatch trees where a card is too heavy. Same fields, same order — no drift. |
| 5 | Evidence panel (E1) | **5B stat tiles + screenshot strip** | The most "testing is the outcome of WHAT" of the three — evidence is the hero, not a footnote. Tiles give glanceable numbers; the screenshot strip is the US4 fitted-proof signature for features. 5C hides proof behind a disclosure (wrong default); 5A undersells it. |
| 6 | Decision record | **All three as one disclosure ladder: 6A pill → 6B callout → 6C trail row** | They aren't alternatives — they're PB-05's badge→popover→full-record layers. 6A is the in-context chip on the artifact; clicking opens 6B (rationale + revisit-if); 6C is the cross-phase trail's diff-first row. One decision atom, three projections. |
| 7 | L3 escalation rail | **7A hero/outline/ghost cards** | Rank as structural weight (the preso a11 checker explicitly failed equal cards). Guardrail kept from PB-05: rank is visible but nothing is pre-selected — a real click on a real consequence is required; no rubber-stamp default. |
| 8 | Autonomy dial | **8A segmented control + legend** | The legend *is* the documentation — it teaches the L1/L2/L3 model in one screen (PB-05's explicit requirement). The earned-trust stat line stays wired to the same fake number the marketplace resume shows. |

## Evidence catalog (closes Q#16)

**E1–E5 blessed as working defaults** (owner: "this Diecast design system as starting point is
correct"): E1 Acceptance Panel (= pick 5B) · E2 Confirm/Refute Ledger (= gallery 2C, in the work
zone) · E3 Red→Green repro · E4 Verdict Card with spike_ref · E5 Rendered Report + provenance.
Rule: outcome first, proof one click in, trace two clicks in; never a bare green badge.
Revisit-on-sight: these are mockup-cheap to change once rendered in the flows.

## PR placement taste call (closes Q#17)

**Link on canvas, diff in the execution tab** (PB-03 recommendation, adopted): the WHAT surface
carries the PR pointer inside the E1 panel; the full diff lives behind the execution drill-in.
Keeps the canvas about acceptance evidence, not raw code.

## Status of session questions

- Q#15 design direction — **resolved** (owner): Diecast identity, one light world.
- Q#16 evidence treatments — **resolved** (owner delegated; E1–E5 as defaults).
- Q#17 PR placement — **resolved** (delegated; link-on-canvas).
- No open questions remain for the exploration phase.

## Canvas anatomy principle (owner, 2026-06-11)

**The center canvas completely morphs based on the work, and it has exactly two parts:**

1. **Stages + the artifacts at each stage.** The spine is a *navigator*, not just a progress
   indicator — each stage owns its artifacts (requirements → refined doc; exploration →
   playbooks; plan → plan doc; execution → tickets/PRs/evidence). Clicking a stage shows its
   artifacts. The "evidence surface" (E1–E5) is the artifacts view of the current/Done stage,
   not a separate zone.
2. **Work happening.** A live tasks/todo stream — mostly automated (agent tasks rendered with
   the colleague lockup + run status), sometimes manual (assigned `@you`, same list, marked
   `manual`, carrying the needs-you accent when blocking). What this stream contains is
   family-specific: experiments for debug, tickets for feature, draft/review todos for PRD.

This collapses the six-zone grammar into: **header + spine(navigator) + stage-artifacts +
work-stream**, with decision chips and the execution drill-in woven into those two parts.
`design-samples/app-shell.html` (updated) renders this anatomy.

## The Guide (owner concept, 2026-06-11 — name TBD)

**One guiding subagent accompanies the user through the entire journey.** It is the mind whose
surfaces the canvas renders:

- **Intent → path:** detects what kind of work the goal is and *composes the stage spine* for it
  (stages are guide-decided, not hardcoded per family). Examples (owner, illustrative — steps not
  final): bug fix → repro · RCA · evidence · potential fixes · fix · tests; new feature →
  requirements · prototype with choices to lock UI · locked design · eng design · execution ·
  test reports.
- **At each step it reasons about the right next step** and suggests it — the nudge card (+ its
  why-line) is the guide's voice.
- **It can pivot mid-flow** (reclassify, reorder, change course) — pivots render as the canvas
  morph + a decision receipt.
- **The chat rail is its conversation.** Worker agents (makers/checkers) are dispatched by the
  guide into the work-happening stream; the guide is the one persistent character end-to-end.
- **Identity requirement:** the guide must be visible as a character (own identity in chat,
  on nudges, on decision receipts) — distinct from worker agents — or guiding reads as anonymous
  UI magic rather than a colleague with judgment.
- **Relationship to prior spec work:** the refine-requirements-v2 "phase-agnostic workflow
  router" (US6 there) is this entity's classification function; the nudge engine (FR-003 here)
  and the morph (FR-004) are its actuation.
- **Stage vocabulary impact:** the feature flow gains design stages (prototype-with-UI-choices →
  locked design → eng design) — a design-lock loop the current four-phase model lacks.

**Name (locked, owner): "the Guide."** Externally visible everywhere (chat voice, nudge
attribution, decision receipts), so plain-and-instant beats clever-metaphor (Foreman/Caster
rejected for decode cost). Internal agent slug: `cast-guide`.

## Familiar-tool principle (owner reframe, 2026-06-11 — supersedes the abstract two-panel canvas)

**Think from the user's mental model: today every step is a discrete tool they already know.**
Requirements = a doc · execution = a Linear/Jira board · review = a PR thread · tests = a CI
report · analysis = a notebook · debugging = an incident timeline. Therefore:

- **Each stage renders as the familiar tool for that step, full-bleed.** No invented "canvas
  zones" the user must learn. The spine is a discrete-step stepper (checkout/CI mental model);
  clicking a step makes the canvas BECOME that step's familiar surface.
- **Diecast's novelty is confined to the connective tissue:** the stepper stringing discrete
  steps together, the Guide sequencing/pivoting them, and agents appearing as peer actors
  INSIDE familiar views (same assignee slot as humans, Linear-style).
- **Work-in-flight is a thin status strip** (CI-status mental model), not a peer panel
  competing with the step's surface.
- The earlier "two-part canvas" principle survives as: part 1 = the stepper + the step's
  familiar surface (which IS the stage's artifact); part 2 = the in-flight strip.

Step → familiar-surface mapping (working set): doc (requirements, PRD), board/ticket list
(execution, fix), PR-thread/report (review, verify, repro), investigation ledger (debugging),
notebook+chart (analysis), memo+timebox (spike).

## Build-phase design directive (owner, 2026-06-11 — FINAL, governs the prototype build)

**The samples in `design-samples/` are INSPIRATION, not spec.** The owner rated the
diecast-flows.html system "a reasonable start at high level." During the actual build
iteration, the designer must re-derive the best possible design from first principles at a
**Steve-Jobs bar**: taste-first, insanely-great standard, ruthless simplicity, every detail
intentional, willing to discard anything in these samples that a better idea beats.

**What stays locked (the constraints, not the pixels):**
- Diecast identity, one light world (Q#15).
- The familiar-tool principle (each stage renders as the tool users already know).
- The Guide as the one persistent character (concept + name).
- Agents as peers inside familiar surfaces (humans=circles, agents=squares grammar — or better,
  if a better idea preserves the same legibility).
- L1/L2/L3 attention discipline (what-needs-me always one glance away).
- The canvas two-part anatomy (stage navigator + artifacts · work happening).
- Hard slop-gate.

**What is explicitly open to be beaten:** every layout, component rendering, spacing choice,
and interaction detail in the samples. If the build-phase designer can do better, they must.
