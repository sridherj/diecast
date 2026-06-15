# Exploration Summary: Product Revamp — Diecast Vision Prototype

**Date:** 2026-06-11
**Steps researched:** 6 (6 web researchers + 4 code explorers)
**Playbooks generated:** 6 of 6
**Spec:** refined_requirements.collab.md v0.3.0 · **Framing:** VISION-FIRST (locked)

---

## Impact Ratings

| # | Step | Impact | Rationale |
|---|------|--------|-----------|
| 6 | Prototype build approach | **9/10** | The 10x lens: data-driven render + scenario engine decides whether ~35 surfaces cost days or weeks; every other playbook executes through it |
| 2 | Canvas + chat mechanics | **9/10** | Specifies the core thesis (SC-003); the typed-op keystone collapses four mechanics into one ~30-line dispatcher identical to the real product's binding |
| 3 | Family canvases + evidence | **9/10** | Proves "the UI adapts per workflow" by contrast; resolves Q#12 with the E1–E5 evidence catalog |
| 4 | Agents as colleagues | **9/10** | Carries the second aha ("Hire. Don't install."); highest-leverage reuse (preso board arc) + the one greenfield concentration (hiring funnel) |
| 5 | Decisions & autonomy | **9/10** | The trust mechanism for the AI-blackbox posture; L3-rarity discipline is make-or-break for the colleague thesis |
| 1 | Design language | **9/10** | The through-line for SC-002/004/005; resolves Q#11 with the hybrid three-register direction + agent-colleague grammar |

**Average Impact: 9.0/10** — unusually uniform because the six steps are six faces of one build.

---

## Top Recommendations

### 1. Build one `index.html`, no build step: `render(appState) → DOM`
Import maps + htm/Preact (~3KB), hash routing, one in-memory JSON state. The spec's ~35 surfaces
are projections of ONE fake org, not 35 pages. Time-to-vision-grade: **~5–7 focused days**. (PB-06)

### 2. The keystone: typed ops, not generated pixels
Chat never paints UI. Every scripted chat line carries a `data-op` (`morph` / `nudge` / `promote` /
`drillInto` / `pin`) dispatched through ~30 lines of vanilla JS inside `startViewTransition`. The
whole 2026 field converged here (Vercel paused free-form RSC gen-UI; Shopify MCP-UI; Google A2UI) —
so the static fake is grammatically identical to the real product's tool-call binding. (PB-02)

### 3. One hero morph, flawless — not four mediocre ones
"This is actually a bug, not a feature" → feature canvas shared-element-morphs into the debug loop
(~350ms, 4 persistent anchors, decision receipt, undoable, reduced-motion fallback). This single
transition IS SC-003. Do not spread morph effort across all four families. (PB-02, PB-03)

### 4. One six-zone canvas grammar; deviate exactly 2 zones per family
Header / spine / work / evidence / execution drill-in / decision chips. Only the **stage spine**
(backbone · loop counter · timebox meter · pipeline DAG) and the **evidence surface** change per
family — that alone carries SC-005 while keeping one product feel. Cost: 1 shell + 8 zone variants,
not 4 layouts. (PB-03)

### 5. Lock the E1–E5 evidence catalog (resolves Q#12)
E1 Acceptance Panel (feature: screenshots + tests + checker rows + PR) · E2 Confirm/Refute Ledger +
E3 Red→Green repro (debug) · E4 Verdict Card with spike_ref (spike) · E5 Rendered Report +
Provenance (analysis). Rule: outcome first, proof one click in, trace two clicks in. Never a bare
green badge. (PB-03)

### 6. Design direction — DECIDED by owner (Q#15): pure Diecast identity, one light world
Existing identity everywhere: cream `#F5F4F0`, raspberry `#D6235C` accent, IBM Plex Mono + DM Sans
(`design-samples/option-e-diecast-light.html`). No dark register — rejected as fashion-import, not
requirement; WHAT/HOW separate via surface tone. Surviving from PB-01: the **agent-colleague
grammar** (actor chip, binary confidence glyph, L1/L2/L3 pill, raspberry as the single status
accent), the fixed block library, one-signature-morph motion register, and the hard slop-gate
(no glass + gradient + glow + orb). Refinements welcome during build. (PB-01 + owner decision)

### 7. Re-author the preso surfaces, don't embed them
The preso a08–a13 slides are near-complete *design comps* (board arc, marketplace, resume) — lift
tokens, vocabulary, and layout; rebuild as real DOM (the SVGs can't click). The five-element
colleague-card lockup (avatar+glyph · paired checker · rework meter · reversibility badge ·
in-flight pill) is ONE component reused on board, ticket, resume, and hiring report. (PB-04)

### 8. The hiring funnel middle is the one greenfield concentration
Marketplace + resume endpoints exist as designs; the assessment → federation → stack-ranked report →
hire → onboard wizard does not. Build it as 5 screens; the centerpiece is an eval report card with
per-dimension radar + deep links to the actual fake work each candidate produced — never a
pricing-grid comparison. Maker+checker are hired together. (PB-04)

### 9. Keep L3 rare — exactly one hard stop per flow
~5–8 decision atoms per goal (judgment calls, never steps), mostly silent L1 chips, a couple of L2
digest entries, exactly ONE L3 stop with an evidence pack + three pre-framed options. The dial
(Conservative/Balanced/Autonomous) re-keys the same reversibility engine — demo it by toggling and
watching an L2 promote to a stop. An agent that asks constantly has failed the thesis. (PB-05)

### 10. One fake-data spine, committed as frozen JSON
Seeded faker for structure + LLM-written prose, hand-tuned, committed. Canonical vocabulary verbatim:
CAST-412 (one title everywhere — fix the preso's drift), M04/S03/R02, rework 1/3, L1/L2/L3,
crud-orchestrator, the 8-agent chain, 12 contracts, "99.9% compliant across 505 runs." Decision
atoms, dial tooltip stats, and marketplace cred all read from the same spine. (PB-05, PB-06)

---

## Recommended Technology Stack (consolidated)

| Layer | Component | Choice |
|-------|-----------|--------|
| Packaging | Build step | **None** — native import maps, single `index.html`, CDN deps <15KB |
| Render | Component layer | **htm + Preact** (CDN, no compiler) |
| State | App state | **One JSON object** + `render(state)`; no state library |
| Routing | Screens | **`location.hash`** + ~20-line switch; deep-linkable |
| Morph | FR-004 / SC-003 | **CSS View Transitions API** + `view-transition-name` anchors; reduced-motion fade fallback |
| Interactivity | All dynamics | **Scenario engine**: ordered `{patch, narration, transition}` steps + `advance()` (~50 lines) |
| Chat binding | Grammar | **5 typed ops** (`morph·nudge·promote·drillInto·pin`) → one dispatcher |
| Canvas | Architecture | **One `CanvasFrame`**, six zones, `data-family` keyed; 4 spine + 5 evidence (E1–E5) variants |
| Design | Tokens | **Diecast identity, one light world** (owner decision Q#15): `runs-threaded.html` app palette base + preso identity (IBM Plex Mono / DM Sans, `#D6235C` accent); no dark register |
| Colleague UI | Atom | **Five-element colleague-card lockup**, one component everywhere |
| Fake data | Spine | **Seeded @faker-js (build-time only) + LLM prose → frozen `org.json`** |
| Demo overlay | Walkthrough | **driver.js** (MIT, ~5KB) |
| Dropped | — | reveal.js, Vite (dev loop), React, routers, state libs, AI app-builders as architect, cast-preso checker pipeline (except the two slop checkers as a design gate) |

---

## Architecture Overview

```
 index.html (single file, no build) ─ importmap ▶ preact/htm/driver.js (CDN)
     │  location.hash → render(appState)
     ▼
 ┌─ AppShell ──────────────────────────────────────────────────────────────┐
 │  Nav rail │ CanvasFrame (WHAT-first, data-family keyed)  │ ChatRail      │
 │           │  zone-header (pill·L1·nudge ▣)               │  scripted     │
 │  feature  │  zone-spine   ◆──◆──● | ↺2/3 | ▣ 3h | ⬡→⬡    │  steps[]      │
 │  debug    │  zone-work    (iteration history)            │  data-op →    │
 │  spike    │  zone-evidence E1│E2+E3│E4│E5                │  dispatcher → │
 │  data     │  zone-exec ▸  run list→dispatch tree→        │  startView-   │
 │  board    │               maker-checker (rework 1/3)     │  Transition   │
 │  market   │  zone-chips   ⚖ decision chips (US10)        │               │
 │  layer-2  │                                              │               │
 └───────────┴──────────────────────────────────────────────┴───────────────┘
     ▲ every surface reads from
 data/org.json — ONE spine: CAST-412 · agents · 8-chain · 12 contracts · decision atoms (5-8/goal)
     +
 Colleague-card lockup (1 component) → board · ticket · resume · hiring report
 Escalation rail (1 component)      → US5 board + US10 L3 stops (all phases)
 Digest atom (1 component)          → L2 decisions + US7 write-back notices
 Registers: workbench(dark) · studio(light) · living-canvas(the morph) — same 6 tokens
```

---

## Build Order

| Phase | What | Effort | Delivers |
|-------|------|--------|----------|
| 1 | Spine + skeleton: index.html, merged tokens, router, `render(state)` | 0.5 d | Load-bearing foundation |
| 2 | Fake-org `org.json` (seeded faker + LLM prose, frozen) + decision atoms | 0.5–1 d | Every screen's data, coherent |
| 3 | Component kit (~8 pieces incl. colleague-card lockup, EvidenceBlock, escalation rail) | 1.5 d | Screens become 10-line data slices |
| 4 | Feature backbone flow end-to-end (canvas → drill-in → E1 evidence) | 1 d | First full vertical slice |
| 5 | Scenario engine + the hero morph (riskiest piece — build early) | 1 d | SC-003 demonstrated |
| 6 | Debug / spike / data canvases + scripts + their L3 moments | 1–1.5 d | All 4 flows clickable (SC-001/005) |
| 7 | Board→ticket→decision→escalation arc + hiring funnel + ops/Layer-2 + reqs-doc loop | 1.5–2 d | The colleague surfaces (the largest re-authoring cost) |
| 8 | Polish: driver.js overlays, scenario chooser, density pass, slop-gate, single-file inline | 1 d | Showable without apology (SC-004) |

**Total estimated effort: ~7–9 focused days** (playbook-06 budget 5–7 + buffer for the step-7 re-authoring).

---

## Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| 2026 AI-slop aesthetic (glass+gradient+glow+orb) sinks SC-004 | High | Hard slop-gate: cast-preso `not-generic`/`not-ai-aesthetic` checkers pass/fail every screen |
| Per-screen hand-building blows the budget (the cardinal sin) | High | Data-driven render; any chrome appearing twice becomes a component immediately |
| Embedding preso SVGs as live UI ("comps ≠ components") | High | Mine for layout/vocabulary only; re-author as DOM |
| L3 over-asking reads as nagging tool, kills colleague thesis | High | Hard budget: exactly 1 L3 per flow; L1 silent, L2 batched digest |
| Morph reads as gimmick / cognitive reload | Med | 4 persistent anchors, ~350ms, receipt + undo, reduced-motion fade |
| Fake-data drift across 35 screens (preso already drifted CAST-412) | Med | One frozen spine JSON; zero ad-hoc naming |
| Hiring funnel (greenfield) lands as pricing-grid CRUD | Med | Eval-report-card shape: radar + pros/cons + deep links to real fake work |
| Trace-tree-as-canvas turns Diecast into an observability dashboard | Med | Span tree lives behind the execution tab only, never on the WHAT |

---

## Reference Implementations / Precedents

| Reference | What | Used by |
|-----------|------|---------|
| `docs/plan/mockups/runs-threaded.html` | Only real app-chrome in repo; execution drill-in CSS + token base | PB-02/03/06 |
| `cast_server/templates/macros/run_node.html` | Recursive dispatch-tree renderer (rework tags, context bars) | PB-02/03 |
| Preso v2/v3 a08–a13 + M5/M6/M7/M8/M9 mockups | Board arc, marketplace, resume, spike card, decision box, SVG chart idiom | PB-03/04 |
| cast-preso-visual-toolkit `:root` tokens | FR-018-compliant identity (IBM Plex Mono, DM Sans, #D6235C) | PB-01/04/06 |
| CSS View Transitions API (Baseline 2025) | The morph primitive | PB-02/03/06 |
| AG-UI / CopilotKit / A2UI / Shopify MCP-UI | Typed-op chat→UI binding consensus | PB-02 |
| Linear board + GitHub agents panel | Peer-assignee board craft | PB-04 |
| Apify Actor store / A2A Agent Card | Marketplace credibility + resume shape | PB-04 |
| Google structured hiring + LMArena + eval radars | Hiring report design | PB-04 |
| ADR + Amazon one-way/two-way doors | Decision atom + reversibility framing | PB-05 |
| Hypothesizer (UIST) / Undo-Replay red→green | Debug evidence treatments E2/E3 | PB-03 |
| Hex/Deepnote notebook→report | Analysis family shape + E5 | PB-03 |

---

## Open Items Resolved by This Exploration

- **[USER-DEFERRED: design language] → RESOLVED (owner decision, Q#15):** pure Diecast identity,
  one light world, no dark register (`design-samples/option-e-diecast-light.html`); refinements
  welcome during build. PB-01's hybrid-register proposal explored via samples A–D and rejected.
- **[USER-DEFERRED: evidence patterns] → RESOLVED (proposal):** E1–E5 catalog (PB-03). Owner
  blesses at plan review.
- **One new taste call surfaced (non-blocker):** feature-family PR shown on canvas vs execution tab
  only. Recommendation: link on canvas, diff in the tab (PB-03 hand-off note).

## All Files

```
exploration/
  steps.ai.md                                approved 6-step decomposition (vision-first)
  research/
    01-design-language.ai.md                 web (7 angles)
    02-canvas-chat-mechanics.ai.md           web      + 02-…-code.ai.md  terrain map
    03-family-canvases-evidence.ai.md        web      + 03-…-code.ai.md  terrain map
    04-agents-as-colleagues.ai.md            web      + 04-…-code.ai.md  terrain map
    05-decisions-autonomy.ai.md              web (7 angles)
    06-prototype-build-approach.ai.md        web      + 06-…-code.ai.md  terrain map
  playbooks/
    01-design-language.ai.md                 9/10 — hybrid registers + colleague grammar
    02-canvas-chat-mechanics.ai.md           9/10 — typed ops + hero morph
    03-family-canvases-evidence.ai.md        9/10 — six-zone grammar + E1–E5
    04-agents-as-colleagues.ai.md            9/10 — lockup + board arc + hiring funnel
    05-decisions-autonomy.ai.md              9/10 — decision atom + L3 rarity + dial
    06-prototype-build-approach.ai.md        9/10 — no-build SPA + scenario engine
  summary.ai.md                              this file
```

**Pipeline note:** all 16 children (6 researchers, 4 code explorers, 6 synthesizers) completed; one
mid-run rate-limit pause was cleared via continue signals. No failures, no missing files.
