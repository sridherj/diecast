# Step 6 Research — The Cheapest Credible Way to Build a Vision-Grade Clickable Prototype

> **Exploration step:** Step 6 of `exploration/steps.ai.md` — *What's the build recipe that hits
> vision-grade quality in days, not weeks?*
> **Resolves / serves:** FR-001 (self-contained browser-openable HTML/JS/CSS, fake data, no
> backend), FR-002 (scenario-chooser entry), FR-004 (scripted chat visibly morphs the canvas),
> FR-006/FR-007 (four distinct family canvases + visible iteration), FR-019 (polish bar, realistic
> data), FR-020 (greenfield, not bound to cast-server stack), SC-003 (fluidity *demonstrated*),
> SC-004 (showable without apology).
> **Author:** cast-web-researcher | **Date:** 2026-06-11 | **Method:** 7-angle research, GO-BROAD.
> **Audience:** the playbook synthesizer + owner. Opinionated, cited, build-ready.

---

## TL;DR — Recommendation

**Hand-roll a single-page, no-build, data-driven HTML app. Do not let an AItool own the
architecture, and do not stand up a framework toolchain.** The deliverable is explicitly a
*static vision artifact* (FR-001, "no backend, no real agents"), and the failure mode that turns a
mockup into a project is treating it like an app: adding React + a bundler, hand-authoring 20
disconnected screens, or letting v0/Lovable scaffold a Next.js repo you then have to babysit. All
three buy polish on screen 1 and bankrupt you by screen 15.

The vision-grade quality bar (SC-004, "showable without apology") and the days-not-weeks budget are
**only simultaneously reachable through a data-driven render**: every screen is a pure function of
one JSON state object, so the 30+ surfaces the spec demands (US1–US10) are *projections of one fake
org*, not 30 hand-built pages. Author the data once; the screens fall out. This is the single
highest-leverage decision in the whole build.

**The recipe, in one breath:** one `index.html`; **ES-module + import-map** wiring so there is *no
build step* ([Preact no-build][preact-nb], [import maps Baseline][mxb-buildless]); **`htm` +
Preact** (~3KB total, JSX-like ergonomics from a tagged template, zero compiler) as the render
layer ([htm][htm-gh]); **state-as-one-JSON-object** holding the entire fake org, with the URL hash
as the router (`#/feature/CAST-412/execution`) so every screen is deep-linkable and the back button
works; **a scenario script** per flow — an ordered list of `{state-patch, narration}` steps the
"Next" key advances through, which is how the *scripted chat moments* and *canvas-morph* become
real without a backend; the **CSS View Transitions API** (`document.startViewTransition()`) for the
morph itself — same-document transitions hit Baseline in Oct 2025 and are the cheapest way to make a
feature-canvas dissolve into a debug-canvas look *engineered, not janky* ([MDN View Transitions][mdn-vt],
[Chrome cross-doc][chrome-xdoc]); a **seeded `@faker-js/faker`** pass (run once, commit the JSON) to
manufacture the coherent fictional org ([faker.seed][faker-seed]); and **`driver.js`** (MIT,
~5KB, dependency-free) for the demo-script overlay that walks an external viewer through a flow
([driver.js][driverjs]).

**Time-to-vision-grade: ~4–7 focused days**, because the data spine and the component kit are built
once and amortized across every screen. The reuse dividend is real but bounded: **lift the
`cast-preso-visual-toolkit` design tokens and `vite-plugin-singlefile` self-containment trick;
ignore reveal.js entirely** (it is a slide engine, the wrong substrate for a clickable app).

**The single biggest mistake to avoid:** building screens instead of building *data + one renderer*.
If you find yourself writing `bug-screen.html` and `feature-screen.html` as separate files with
copy-pasted chrome, stop — you have already lost the days-not-weeks budget.

---

## Why this step is the 10x lens (and where the weeks hide)

The other five steps decide *what* to draw. This step decides whether drawing it costs days or
weeks — and the spec quietly demands a *lot* of surface area: four full workflow clickthroughs
(US2), a board→ticket→decision→escalation arc (US5, four connected screens), a hiring flow with
assessment→federation→report→onboard (US6), agent-ops + skillification (US8), Layer-2 catalogue +
chain viz + portfolio (US9), a requirements-doc loop with comments and versions (US7), and
decision/autonomy surfaces threaded through all of it (US10). Naively that is **30–40 distinct
screens**, each needing consistent chrome, the same fake CAST-412 ticket, the same agents in the
marketplace and on the board.

The weeks hide in exactly three places:

1. **Re-authoring chrome and data per screen.** Hand-build 35 HTML files and you will spend 60% of
   the budget keeping the nav rail, the chat rail, the fake-org data, and the design tokens in sync
   across files that drift the moment you touch one. *Fix: one renderer, one data object.*
2. **A toolchain you didn't need.** `npm create vite`, a React app, a router library, a state
   library, Tailwind's JIT — every one is a 30-minute setup and a lifetime of "why won't the build
   work" for an artifact that ships as a single file someone double-clicks. *Fix: no build step at all.*
3. **Faking interactivity the hard way.** The spec's marquee moment (FR-004, SC-003) is a chat
   message that *visibly morphs the canvas*. Done naively (hand-wire show/hide on 8 panels with
   bespoke CSS keyframes) this is a multi-day yak-shave per flow. *Fix: state-patch + one View
   Transition call.*

Get the architecture right and the 35 screens collapse into **~8 reusable components × 1 data spine
× 4 scenario scripts**. That is the entire ballgame.

---

## Angle 1 — Expert Practitioner (prototyping craft & static-app engineering)

**The settled practitioner move for a high-fidelity clickable prototype with no backend is
"prototype in static HTML, drive it from mock data."** Max Böck's widely-cited writeup makes the
case directly: static-HTML prototypes let you *"incorporate any kind of mockup data into the UI"* and
design *"with real-life content in mind,"* which is exactly the SC-004 bar — realistic data, no
lorem ipsum (FR-019) ([mxb prototyping][mxb-proto]). The practitioner consensus has three load-bearing
rules:

1. **Separate data from presentation from the first commit.** The prototype is a *view* over a fake
   dataset. Treat the dataset as the product and the screens as disposable. This is what makes 35
   screens tractable: change the fake org's name once, every screen updates. It is also what makes
   the prototype *internally consistent* — the constraint the spec calls out by name ("the same fake
   goal/ticket/agents recur across screens").
2. **One coherent fictional spine, authored deliberately, not 35 ad-hoc names.** A practitioner
   builds the fake org like a set designer builds a film set: one company (say **Northwind** or reuse
   the canonical **CAST-412** ticket and `crud-orchestrator` agent from preso v3, per the spec's
   reuse constraint), a fixed cast of ~8 agents (Maker/Checker/Decision/Spike/Escalation/Mentor
   archetypes from US6 S5), ~6 goals across the four families, one requirements doc. Everything else
   references *these*. Coherence is what reads as "a product" rather than "disconnected mocks"
   (Directional Ideas, fake-data spine).
3. **Script the happy path; don't build a state machine.** A vision prototype is a *rail*, not an
   app. The viewer is meant to walk a curated path (the scenario chooser → a flow → the aha moment).
   Practitioners fake interactivity with **scripted steps**, not real logic: a per-flow ordered list
   of states, advanced by a "Next" affordance or scripted-chat send button. This is the difference
   between "demo that always works in the room" and "app with 40 edge cases half-built."

**Anti-pattern (practitioner red flag):** the "honest prototype" trap — wiring real form validation,
real filtering, real empty states. Every hour spent making the assignee filter *actually* filter is
an hour not spent on the next vision surface. Fake the filter: clicking "agents" swaps to a
pre-baked filtered view. The viewer cannot tell, and you bought back a day.

**Practitioner verdict for Diecast:** static HTML + mock-data-driven render + scripted happy paths.
This is the boring, correct answer and it is what hits days-not-weeks.

---

## Angle 2 — Tools & Technologies (the concrete no-build stack)

The enabling shift since ~2024 is that **the browser now ships the toolchain.** Three platform
features remove the historical reasons to reach for a bundler:

**(a) Import maps — Baseline, all modern browsers.** An import map is a `<script type="importmap">`
JSON blob that resolves bare specifiers (`import { h } from 'preact'`) to CDN URLs, so you get clean
ES-module imports with *no node_modules and no bundler* ([import maps / buildless][mxb-buildless],
[ES modules & import maps][valeria-im]). This is the keystone — it is what makes "no build step"
(FR-001's spirit) literally true rather than aspirational.

**(b) `htm` + Preact — JSX ergonomics without a compiler.** JSX's one hard dependency is a build
step (something must transpile `<div>` to `h('div')`). `htm` removes it by using **tagged template
literals** — a native JS feature — to parse the same markup at runtime. `htm` is *<500 bytes*, Preact
is ~3KB, and the combination gives you components, props, and `html\`...\`` templates that read
almost exactly like JSX, running straight from a CDN ([htm][htm-gh], [Preact no-build][preact-nb],
[no-build TODO with htm/preact][dev-htm]). For a prototype this is the sweet spot: component
ergonomics (so the chat rail and nav are written once and reused), zero toolchain.

> Pragmatic fallback if even Preact feels heavy: **vanilla template-literal rendering** — a `render(state)`
> function that returns an HTML string from JS template literals and sets `container.innerHTML`
> ([template-literal HTML binding][dev-tmpl]). Zero dependencies, dead simple, perfectly adequate for
> a static prototype. Choose htm/Preact only if the interaction surface (promotable artifacts,
> drill-in tabs) makes diffing worth it. **Recommendation: start vanilla, adopt Preact only if
> re-render flicker becomes visible.**

**(c) CSS View Transitions API — the morph, for free.** `document.startViewTransition(() => updateDOM())`
captures a before/after snapshot and cross-fades (or, with `view-transition-name`, *morphs* matched
elements between states). Same-document transitions reached **Baseline "Newly Available" in October
2025** (Chrome 111+, Firefox 133+, Safari 18+) ([MDN View Transitions][mdn-vt]). This is the
*entire* implementation of FR-004's canvas-morph: put the canvas panels inside a container, on the
scripted chat step mutate `state.family = 'debug'` and re-render *inside* a `startViewTransition`
callback, and the feature-canvas dissolves into the debug-canvas with a polished animation you wrote
in two lines. Naming shared elements (the goal title, the chat rail) with `view-transition-name`
makes them *persist and slide* rather than cross-fade — the "engineered, not janky" finish.

> Caveat to record: cross-*document* transitions (separate HTML files) work in Chromium 126+ and
> Safari 18.2+ but Firefox doesn't animate them yet, and they carry a hard 4s timeout
> ([Chrome cross-doc][chrome-xdoc], [CSS-Tricks gotchas][csstricks-xdoc]). **This is a non-issue for
> us** because the recommended architecture is a *single document* (SPA-style hash routing), where
> same-document transitions are fully Baseline. It is one more reason to prefer one `index.html` over
> many files.

**(d) `@faker-js/faker` with a fixed seed — the data factory.** `faker.seed(42)` makes generation
*deterministic*: same seed → same names, companies, dates, every run, every machine
([faker.seed API][faker-seed], [seeded mock data guide][devtoys-faker]). Run a tiny generation
script *once* (Node or even a browser console), seed it, hand-tune the output, and **commit the
resulting JSON as the data spine.** Faker is a build-time convenience, not a runtime dependency — the
shipped prototype contains only the frozen JSON, keeping FR-001 ("no backend") clean. Faker's
domains (person, company, git, lorem, date) cover almost everything: agent names, the fake org, PR
links, commit SHAs, timestamps, realistic ticket prose.

**(e) `driver.js` — the demo-script overlay (Directional Ideas: "demo script overlay").** MIT-licensed,
dependency-free, ~5KB; highlights an element, dims the rest, and shows a popover with next/prev
([driver.js][driverjs], [tour-lib comparison][logrocket-tours]). It is the cheapest way to deliver
the "demo-script overlay could guide external walkthroughs" idea — define a tour as an array of
`{element, popover}` steps and the guided walkthrough for SC-002 ("a peer states what the product
does in 3 minutes") is done. **Licensing note that matters:** prefer `driver.js` (MIT) over
`shepherd.js`/`intro.js` (AGPL / paid commercial license) — for a showable artifact you don't want a
copyleft string attached ([tour licensing][userorbit-tours]).

**Stack summary (the bill of materials):**

| Concern | Choice | Size | Why |
|---|---|---|---|
| No build step | Import maps (native) | 0 | Browser resolves CDN modules |
| Render | `htm` + Preact (or vanilla template literals) | ~3KB / 0 | JSX ergonomics, no compiler |
| Routing | URL hash + tiny switch | 0 | Deep-linkable screens, back-button works |
| State | One JSON object in memory | 0 | Single source of truth → coherence |
| Canvas morph | CSS View Transitions API (native) | 0 | FR-004 in 2 lines, Baseline |
| Fake data | `@faker-js/faker`, seeded, build-time | 0 at runtime | Deterministic coherent org |
| Demo overlay | `driver.js` (MIT) | ~5KB | Guided walkthrough, SC-002 |
| Design tokens | lift `cast-preso` `:root` token block | 0 | Instant craft, brand continuity |
| Ship as 1 file | inline everything (or `vite-plugin-singlefile` once) | — | FR-001 browser-openable |

Total runtime weight: **<15KB of library code**, all from CDN or inlined. No node_modules required to
*run*; the only optional tooling is a one-shot faker script and a one-shot single-file inliner.

---

## Angle 3 — AI/ML Approaches (where AItools help — and where they sink you)

**Use AI as a co-author inside the hand-rolled architecture, never as the architecture's owner.** The
2026 landscape — v0, Lovable, Bolt, Replit, Figma Make, Magic Patterns — is genuinely strong at
*generating a polished single screen from a prompt or a Figma frame* ([vibe-coding comparison][epam-vibe],
[AI prototyping stack][arteeva-stack], [2026 prototyping tools][aakash-2026]). The trap is what they
generate *around* the screen: v0 emits a Next.js + shadcn/ui + Tailwind app; Lovable scaffolds a
Supabase backend; Bolt spins a full-stack repo. For a *static vision prototype* with no backend
(FR-001) and a greenfield-not-bound-to-a-stack mandate (FR-020), inheriting a React/Next toolchain is
the exact "mockup becomes a project" failure this step exists to prevent. You'd spend day 2 fighting
a framework instead of drawing screen 4.

**The right division of labor:**

- **AI generates leaf components and dense content, not the app.** "Generate the HTML+CSS for one
  agent-resume card given this JSON shape," "write 6 realistic decision records with rationale for a
  RBAC goal," "produce the maker-checker activity-log markup for CAST-412." Paste the output into the
  hand-rolled renderer. This is where AI saves real hours — manufacturing *believable density* (the
  thing that separates SC-004 "showable" from "obviously a mock"), which is tedious by hand.
- **AI as the faker.** LLM-generated fake data beats faker for *prose* (ticket descriptions, hiring-report
  pros/cons, decision rationale, chat scripts) where you need domain-coherent English, not just a
  random name. Use faker for the structured spine (names, dates, IDs, SHAs) and an LLM for the prose
  that hangs off it. Together they produce a fake org that reads as real.
- **AI tools as a *look* reference, not a *codebase*.** If you want to explore a visual direction
  fast, generate a screen in v0/Figma Make, screenshot it, steal the layout idea, and *re-implement
  it in the hand-rolled kit.* Take the inspiration; leave the repo. (This dovetails with Step 1's
  design-language exploration.)

**Contrarian sub-note (revisited in Angle 6):** there *is* a world where Lovable/Bolt builds the whole
thing faster — if the prototype were a throwaway you'll never extend and you accept a React repo. But
the spec wants an *execution roadmap* out of this (SC-006: "each surface maps to a buildable follow-on
goal") and a *coherent data spine* across 35 screens. AItools are weakest exactly there — at
cross-screen consistency and at a clean data model — and strongest at one-shot screens. So the
architecture stays hand-rolled; AI fills it in.

**Verdict:** AI is a force-multiplier on *content and components*, a liability as *architect*. Keep
the JSON spine and the renderer in human hands; let the model mass-produce the believable filling.

---

## Angle 4 — Community & Open Source (proven patterns and lift-able assets)

**External community patterns** converge on the same playbook:

- **"Buildless" / "no-build" is an established movement, not a fringe hack.** Max Böck's *Going
  Buildless*, the Preact team's official *No-Build Workflows* guide, and End Point's 2025 *Preact Web
  App Without npm Build* all document production-credible no-build stacks built on import maps + htm
  ([Going Buildless][mxb-buildless], [Preact no-build][preact-nb], [End Point no-build][endpoint-nb]).
  For a prototype — even lower stakes than their production use cases — this is comfortably proven.
- **Mock-data-driven static prototyping** is the documented norm for design-stage artifacts
  ([mxb prototyping][mxb-proto]). The community consensus matches the practitioner angle: data first,
  screens as views.
- **Permissive demo-overlay tooling exists off the shelf** — `driver.js` (MIT) is the community's
  go-to lightweight tour lib precisely because it's dependency-free and copy-paste simple
  ([driver.js][driverjs]).

**Internal lift-able assets** (the spec's "reuse before re-author" constraint, filtered hard to *only
what serves the vision*):

| Asset | Location | Verdict | Why |
|---|---|---|---|
| **Design tokens** (`:root` color + type scale) | `cast-preso-visual-toolkit/base-template/theme.css` | **LIFT** | A ready, tasteful token system (`--color-accent`, `--font-heading: IBM Plex Mono`, the engineering-grid background). Instant craft floor + brand continuity (FR-018). Copy the `:root` block verbatim, then let Step 1's design direction override tokens. |
| **Single-file ship trick** | `cast-preso .../vite.config.js` (`vite-plugin-singlefile`) | **LIFT (optional)** | Proven recipe to inline all JS/CSS/assets into one double-clickable `.html` (FR-001). Use it as the *final* package step only — or skip and just inline by hand since the app is small. |
| **The engineering-grid background + callout/question component CSS** | `cast-preso .../templates/css/` | **LIFT (selectively)** | The callout and muted-question treatments map directly onto WHAT-callout vs HOW-muted (Step 5's IA). Free, on-brand components. |
| **reveal.js slide engine** | preso `index.html`, base-template `main.js` | **DROP** | reveal.js is a *linear slide deck* engine. The prototype is a *non-linear clickable app* with hash routing, a persistent chat rail, and drill-in tabs. Forcing app UX into a slide framework fights the grain. Take the *tokens and the self-contained-build idea*; leave the engine. |
| **Per-slide HTML in `presentation_v3/how/*/slide.html`** (board arc a08–a11, marketplace, agent resume, chain viz) | second-brain preso v3 | **MINE for layout, RE-IMPLEMENT** | The spec explicitly says lift these designs (FR-010, US6, reuse constraint). But they're authored as 1920×1080 *slides*, not interactive screens. Screenshot/read them for the *visual composition* of the board, the resume card, the marketplace grid, the contract catalogue, the chain viz — then re-implement as live components in the kit. Don't import the slide HTML wholesale; it carries reveal-specific sizing and absolute positioning that won't reflow in an app shell. |
| **reference_repos UIs** (gastown, openclaw, gbrain, etc.) | `~/workspace/reference_repos` | **SCAN, terrain-map only** | Per the spec's inspiration constraint and Step 1. Mine for interaction ideas; none is a substrate to build *on*. |

**Net:** lift the token system and the single-file trick; mine the preso slide *compositions* for the
board/marketplace/resume/chain surfaces; ignore reveal.js as an engine. The reuse dividend is "a free
afternoon of design-system + the board-arc visual language," not "a head start on the app skeleton."

---

## Angle 5 — Frameworks & Patterns (the architecture, concretely)

The build rests on five named patterns. Together they are the spec.

**Pattern 1 — State-as-one-JSON-object (single source of truth).** The entire prototype is a pure
function `render(appState) → DOM`. `appState` holds: the fake org, all goals/tickets/agents/decisions,
*and* the current view (`{ route, family, scenarioStep, chatLog, pinnedArtifacts }`). Every screen
reads from it; nothing has private state. This is *the* coherence guarantee (the spec's "same
goal/ticket/agents recur across screens" requirement) and the thing that makes 35 screens a data
problem, not a screen-count problem.

**Pattern 2 — URL-hash routing (deep-linkable screens, free back button).** The route lives in
`location.hash` (`#/board`, `#/feature/CAST-412/execution`, `#/marketplace/rbac-agent`). A 20-line
`onhashchange` switch maps hash → which component to render. Benefits that matter for a *demo*: every
screen is shareable by URL, the browser back button works (so a viewer who drills in can escape), and
the scenario chooser is just a list of links. No router library; the platform already routes.

**Pattern 3 — Scenario script (the no-backend interactivity engine).** Each of the four flows (US2)
is an **ordered array of steps**, each step a `{ patch, narration, transition? }`: `patch` mutates
`appState` (advance the stage, append a scripted chat message, reveal evidence), `narration` is the
canned chat/overlay text, `transition` flags whether to wrap the re-render in a View Transition. A
single "Next" / scripted-send control walks the array. **This is how every dynamic moment in the spec
is faked uniformly:** the canvas-morph (FR-004) is a step whose patch flips `family` and sets
`transition: 'morph'`; the iteration history (FR-007) is steps that append to a visible loop counter;
the autonomy-gated clarification (US10/SC-007) is a step that pauses and shows three options. One
mechanism, every flow. Authoring a flow becomes *writing a script*, not *building a state machine* —
this is the days-not-weeks multiplier on the interactive surfaces.

```
// shape, not final code
scenarios.feature = [
  { narration: "Opening the goal…", patch: s => s.route = '#/feature/CAST-412' },
  { narration: "Actually this is a bug, not a feature.",          // the SC-003 moment
    patch: s => { s.family = 'debug'; s.canvas = debugShape; },
    transition: 'morph' },                                        // → document.startViewTransition
  { narration: "Iteration 2/3 — new hypothesis…",
    patch: s => s.debug.iteration = 2 },
  …
];
```

**Pattern 4 — Component kit (~8 reusable pieces).** Build once, reuse everywhere: `AppShell`
(nav + chat rail + canvas slot), `ChatRail`, `CanvasFrame` (the View-Transition container),
`GoalCard`/`WhatPanel`, `ExecutionDrillIn` (tabs → run list → dispatch tree → maker-checker),
`Board`/`Ticket`, `AgentCard`/`Resume`, `EvidenceBlock` (screenshot / chart / rendered-HTML / test-
summary variants per FR-009). The four *family canvases* (US2) are data-driven variants of
`CanvasFrame` keyed on `family`, **not** four separate screens — feature shows req→explore→plan→
execute; debug shows hypothesis→experiment→observation + iteration counter; spike shows timebox→
conclusion; data shows question→sources→analysis→viz. One component, four configs (this is also what
makes the morph between them a state change rather than a navigation).

**Pattern 5 — Build-time data factory, runtime-frozen.** `faker.seed(N)` + an LLM prose pass generate
the spine *once*; commit the JSON; the runtime imports a static file. No generation at runtime (keeps
FR-001 honest and the demo instant). Re-running the seeded factory reproduces the identical org, so
the data is regenerable but stable.

**Why these five and not a framework:** a framework (React Router + Redux + a component lib) gives you
exactly Patterns 1–4 *plus* a toolchain, a bundler, and 200KB of runtime you don't need for an artifact
that fakes everything. The five patterns above are the *parts of a framework you actually use*,
implemented in ~150 lines of vanilla/Preact, with no build. That is the whole "cheapest credible"
thesis.

---

## Angle 6 — Contrarian View (steelmanning the paths I'm rejecting)

**Contrarian 1: "Just let Lovable/Bolt build it — you'll have all 35 screens by Friday."** The
strongest case for the AI-app-builder route. It's genuinely fast for screen 1 and handles polish and
responsive layout for free ([2026 prototyping tools][aakash-2026]). **Why I still reject it as the
spine:** (a) it ships a React/Next/Supabase repo — a stack the spec explicitly doesn't want to inherit
(FR-020) and a backend the spec explicitly forbids (FR-001); (b) AItools are weakest at *cross-screen
data coherence*, and coherence is the spec's named constraint — you'd spend the saved time fixing the
fake org drifting between screens; (c) the canvas-morph (the one thing that *must* be demonstrated,
SC-003) is a bespoke interaction these tools won't nail from a prompt. **Where it earns a place:**
generating individual dense screens to paste into the hand-rolled kit (Angle 3). Use it as a content
gun, not a general contractor.

**Contrarian 2: "Skip code entirely — Figma + prototype links is the canonical clickable mockup."**
The traditional designer answer, and worth taking seriously. **Why not:** the spec's deliverable is
*locked* as "self-contained HTML/JS/CSS, browser-openable" (FR-001) and the marquee requirement is a
*canvas that morphs* — a real DOM/CSS transition, not a Figma smart-animate fake. Figma can *fake* the
morph frame-to-frame, but you can't ship a Figma file as "open this in a browser," and you can't get
the SC-006 execution-roadmap dividend (real markup that maps to real follow-on build) from Figma
frames. HTML is the right substrate for *this* artifact.

**Contrarian 3: "Just hand-write 35 static HTML files — simplest possible thing."** Tempting for the
first 3 screens. **Why it fails by screen 10:** no shared chrome, no shared data, every fake-org edit
is a 35-file find-replace, and the interactive moments (morph, drill-in, scripted chat) have to be
re-implemented per file. The data-driven render is *more* setup on day 1 (~half a day for the spine +
kit) and *dramatically* less by day 3. The crossover is around screen 6 — and we have 35.

**Contrarian 4: "Use a real SSG (Astro/Eleventy) — you said data-driven, that's literally an SSG."**
Closest contrarian, and a legitimate alternative. Astro/Eleventy *do* give you data-driven templating
and can output static HTML ([Astro from JSON][solita-astro]). **Why I lean no for *this* artifact:** an
SSG re-introduces a build step and a node toolchain (the day-2 tax), and it's optimized for *content
pages*, not a *single stateful app* with live View Transitions and a scenario engine running in the
browser. The interactivity here (morph, scripted chat, drill-in) wants a live client runtime, which is
the SPA shape, not the SSG shape. **If** the prototype were mostly static content pages with light
interaction, Eleventy would win; because it's an *interactive demo*, the no-build SPA wins. Record this
as a genuine fork, decided by the interaction-heaviness of the spec.

**What the contrarians change in the recommendation:** nothing structural, but they sharpen it — (1)
*do* use AItools as a content/component gun; (2) keep an eye on the Eleventy fork if the surfaces turn
out more static than interactive after Step 3/4 land.

---

## Angle 7 — First Principles (reasoning up from the constraints)

Strip to the irreducible requirements and the architecture is forced:

1. **It must open in a browser with no backend (FR-001).** → Output is HTML/CSS/JS files, ideally one.
   No server, no DB. *Everything dynamic must be faked client-side.*
2. **It must demonstrate, not describe, fluidity — a chat message visibly reshapes the canvas
   (SC-003/FR-004).** → There must be a *live client runtime* that mutates the DOM with a polished
   transition. This rules out a pure static-pages approach and rules *in* a stateful single page +
   the View Transitions API. (The single hardest requirement, and it alone selects the SPA shape.)
3. **The same fake org must recur, consistently, across ~35 surfaces (coherence constraint).** → There
   must be *one* data source all screens read. This forces state-as-single-object and data-driven
   rendering; it forbids per-screen hand-authoring.
4. **It must be vision-grade / showable without apology (SC-004) yet built in days (budget).** → Polish
   must come from *reuse and amortization*, not per-screen effort. This forces a component kit + a
   lifted design-token system (the preso tokens) so every screen inherits craft for free.
5. **It must yield an execution roadmap — surfaces map to buildable goals (SC-006).** → The artifact's
   structure should *mirror the product's structure*: screens = components, data = the eventual schema.
   A clean hand-rolled data model does this; an AItool's generated repo or a Figma file does not.
6. **It changes shape per workflow family, with visible iteration (US2/FR-006/FR-007).** → The canvas
   must be *parameterized by family*, not four fixed pages — so "switch family" is a state change (which
   is *also* requirement #2's morph). One component, four configs.

Constraints 1–6 *intersect* at exactly one architecture: **a single-page, no-build, state-driven HTML
app, where screens are pure functions of one JSON spine, family-canvases are configs of one component,
dynamic moments are scripted state-patches, and transitions ride the native View Transitions API.**
Every other approach violates at least one constraint — static pages fail #2, Figma fails #1 and #5,
an AI-builder repo fails #1 and #5, an SSG fights #2. The recommendation isn't a preference; it's the
unique point the constraints converge on.

**First-principles note on *time*:** the budget is set by the ratio of *authored-once* work to
*authored-per-screen* work. Push everything into authored-once (data spine, component kit, scenario
engine, token system) and per-screen cost → "write a 10-line scenario script + a data slice." That
ratio, not raw effort, is what turns weeks into days.

---

## The Build Recipe (named techniques, sequenced for days-not-weeks)

**Day 0 (½ day) — Spine + skeleton.**
1. One `index.html` with an **import map** (Preact/htm + driver.js from a CDN) and the lifted
   `cast-preso` `:root` **design tokens**. *Technique: import maps, no-build.*
2. **State-as-one-JSON-object** stub + `render(state)` + **hash router** switch. *Technique:
   single-source-of-truth + URL-hash routing.*
3. **Seeded faker + LLM prose** pass → commit `data/org.json` (the fake org, 8 agents, 6 goals,
   CAST-412, the requirements doc, decision records). *Technique: build-time deterministic data
   factory.*

**Days 1–2 — The component kit + the backbone flow.**
4. Build the ~8 components (`AppShell`, `ChatRail`, `CanvasFrame`, `WhatPanel`, `ExecutionDrillIn`,
   `Board`/`Ticket`, `AgentCard`/`Resume`, `EvidenceBlock`). *Technique: component kit.*
5. Wire the **feature flow** end-to-end as the richest backbone (US2 flow 1), including the
   WHAT→execution drill-in (US3) and an `EvidenceBlock` (US4).

**Day 3 — The aha moment + the other three families.**
6. Implement the **scenario engine** and author the feature→**debug** morph as the headline scripted
   moment, wrapped in `document.startViewTransition()` with `view-transition-name` on persistent
   chrome. *Technique: scenario script + CSS View Transitions.* (This is SC-003 — build it early,
   it's the riskiest piece.)
7. Add the **debug / spike / data** canvases as `CanvasFrame` configs + their scenario scripts.

**Days 4–5 — The agent-colleague + decision surfaces.**
8. Board→ticket→decision→escalation arc (US5), **mining the preso a08–a11 compositions** for layout.
9. Hiring flow (US6), agent-ops/skillification (US8), Layer-2 surfaces (US9), requirements-doc loop
   (US7) — all data-driven views over the existing spine.
10. Thread **decision records + the autonomy-gated clarification** (US10/SC-007) through the flows.

**Day 6 — Polish + package.**
11. `driver.js` **demo-script overlay** per flow (SC-002 guided walkthrough) + the **scenario-chooser
    entry screen** (FR-002).
12. Inline everything to **one self-contained `.html`** (hand-inline, or the `vite-plugin-singlefile`
    trick as a one-shot). Cross-browser smoke test (Chrome primary; the View Transitions degrade
    gracefully to instant swaps where unsupported).

**Buffer (day 7)** — content density pass (LLM-generate the believable filling: realistic ticket
prose, hiring-report pros/cons, decision rationale) so it reads as a product, not a skeleton (SC-004).

---

## Anti-Patterns (the days→weeks landmines)

- **Building screens instead of data + one renderer.** The cardinal sin. If two files share copy-pasted
  chrome, refactor to a component immediately.
- **Standing up a framework toolchain** (Vite/Webpack/Next, npm install, a router lib, a state lib).
  Every one is day-2 tax for an artifact that ships as one file. Use the platform.
- **Letting an AI builder own the architecture.** Inherits a backend/stack the spec forbids; weak at
  the cross-screen coherence the spec demands. Use AI for content and leaf components only.
- **Making interactions *real*** (real filters, real validation, real empty states). Fake the happy
  path; the viewer can't tell and you buy back days.
- **Many HTML files + cross-document View Transitions.** Firefox won't animate them and the 4s timeout
  bites; the single-document SPA sidesteps both and gets fully-Baseline same-document transitions.
- **reveal.js as the engine.** It's a linear deck; the prototype is a non-linear app. Take its tokens,
  not its runtime.
- **Hand-naming fake data ad hoc.** Drifts instantly across 35 screens. Seed it, commit it, reference it.
- **Hardcoding hex colors.** Use the lifted `--color-*` tokens so Step 1's design direction can
  re-skin the whole prototype by overriding `:root` (also a `cast-preso` hard rule).

---

## Open forks to resolve downstream (not blockers)

- **Render layer: vanilla template literals vs htm/Preact.** Start vanilla; adopt Preact only if
  re-render flicker on drill-in/promote interactions becomes visible. Decide after the component kit
  exists (Day 2).
- **SSG fork (Eleventy/Astro).** Only reconsider if Steps 3–4 reveal the surfaces are mostly static
  content with light interaction. The morch/scripted-chat interactivity currently selects the SPA shape.
- **Single-file packaging: hand-inline vs `vite-plugin-singlefile`.** Trivial either way; defer to Day 6.

---

## Sources

- [MDN — View Transition API][mdn-vt]
- [Chrome for Developers — Cross-document view transitions (MPA)][chrome-xdoc]
- [CSS-Tricks — Cross-Document View Transitions: The Gotchas][csstricks-xdoc]
- [Preact — No-Build Workflows (official guide)][preact-nb]
- [End Point — A Preact Web App Without npm Build (2025)][endpoint-nb]
- [developit/htm — Hyperscript Tagged Markup][htm-gh]
- [DEV — No-build TODO app using htm + Preact][dev-htm]
- [Max Böck — Going Buildless (import maps)][mxb-buildless]
- [ValeriaVG — ES Modules & Import Maps: Back to the Future][valeria-im]
- [Max Böck — Prototyping an App in Static HTML][mxb-proto]
- [DEV — HTML templates by binding JSON with template literals][dev-tmpl]
- [/dev/solita — Building a static website from JSON with Astro][solita-astro]
- [fakerjs.dev — faker.seed() API][faker-seed]
- [DevToys — Mock Data Testing Guide (seeded randomness)][devtoys-faker]
- [driver.js — official site][driverjs]
- [LogRocket — Best product tour JS libraries][logrocket-tours]
- [Userorbit — Best open-source product tour libraries 2026 (licensing)][userorbit-tours]
- [EPAM — v0 vs Lovable vs Bolt vs Replit vs Figma Make][epam-vibe]
- [Anna Arteeva — Choosing your AI prototyping stack][arteeva-stack]
- [Aakash — Best AI Prototyping Tools 2026][aakash-2026]
- Internal: `skills/claude-code/cast-preso-visual-toolkit/` (theme.css tokens, vite-plugin-singlefile, archetypes)
- Internal: `/data/workspace/second-brain/taskos/goals/taskos-gtm/presentation_v3/` (board arc, marketplace, resume, chain-viz slide compositions)

[mdn-vt]: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API
[chrome-xdoc]: https://developer.chrome.com/docs/web-platform/view-transitions/cross-document
[csstricks-xdoc]: https://css-tricks.com/cross-document-view-transitions-part-1/
[preact-nb]: https://preactjs.com/guide/v10/no-build-workflows/
[endpoint-nb]: https://www.endpointdev.com/blog/2025/10/preact-web-app-without-npm-build/
[htm-gh]: https://github.com/developit/htm
[dev-htm]: https://dev.to/ekeijl/no-build-todo-app-using-htm-preact-209p
[mxb-buildless]: https://mxb.dev/blog/buildless/
[valeria-im]: https://valeriavg.dev/es-modules-import-maps-back-to-the-future
[mxb-proto]: https://mxb.dev/blog/prototyping-app-with-static-html/
[dev-tmpl]: https://dev.to/mrhdias/creating-html-templates-for-binding-json-data-with-javascript-template-literals-3p9f
[solita-astro]: https://dev.solita.fi/2024/12/02/building-static-websites-with-astro.html
[faker-seed]: https://fakerjs.dev/api/faker
[devtoys-faker]: https://devtoys.pro/blog/mock-data-testing-guide
[driverjs]: https://driverjs.com/
[logrocket-tours]: https://blog.logrocket.com/best-product-tour-js-libraries-frontend-apps/
[userorbit-tours]: https://userorbit.com/blog/best-open-source-product-tour-libraries
[epam-vibe]: https://www.epam.com/insights/ai/blogs/best-vibe-coding-tools-v0-lovable-bolt-replit-and-figma-make
[arteeva-stack]: https://annaarteeva.substack.com/p/choosing-your-ai-prototyping-stack
[aakash-2026]: https://www.news.aakashg.com/p/ai-prototyping-tools-2026
