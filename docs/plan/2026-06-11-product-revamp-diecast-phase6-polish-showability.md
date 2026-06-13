# Product Revamp: Diecast — Phase 6: Polish & Showability (Slop-Gate, Walkthrough, Single-File)

## Overview

Phase 6 turns a complete-but-raw prototype into a **showable artifact**: the FR-002 scenario-chooser
front door, driver.js guided walkthroughs plus a presenter demo-script overlay (owner default: both),
a density/consistency pass, a full slop-gate re-run over **every** screen, a single distributable
file that opens from disk, and the SC-006 surface→buildable-goal map that converts the prototype
into the v2 execution roadmap. Nothing new is *demonstrated* in this phase — every flow, surface,
and script already exists from Phases 1–5; this phase makes them navigable by a stranger,
defensible to a peer (SC-004), and portable as one file. The key insight inherited from the build
architecture: because every screen is a projection of `ORG` through `render(appState)`, "polish"
here is mostly *gating and packaging*, not re-authoring.

This is a planning-only document. The prototype does not exist on disk yet; file paths below
describe what execution will create or modify, consistent with the prior six phase plans.

## Operating Mode

**HOLD SCOPE** — per the delegation directive: "Scope mode: HOLD SCOPE — plan exactly what the
high-level plan section says for this phase." The high-level Phase 6 section lists five key
activities (chooser, walkthrough overlays, density+slop pass, single-file inline + drift sweep,
surface→goal map); this plan details exactly those, no extras. The one nice-to-have that surfaced
during planning (a standalone written demo runbook) is **excluded** — the demo-script overlay
already serves that job.

**NO TESTS (owner directive):** this deliverable has no concept of tests. No test files, suites,
harnesses, or CI appear anywhere in this plan. All verification is manual: open
`prototype/index.html` (or the dist file) from disk in Chrome, click, observe. Fake test-result
*content* rendered as prototype UI data (E1 acceptance panel, E3 red→green) is data, not tests.

## Position in Overall Plan

```
Phase 1 ──► { 2a ∥ 2b ∥ 2c } ──► Phase 3 ──► { Phase 4 ∥ Phase 5 } ──► Phase 6 (THIS PLAN — terminal)
```

Phase 6 is the last phase on the critical path (1 → 2b → 3 → 5 → 6). It consumes the final route
table, the complete `SCRIPTS` map, the full ORG spine, and the per-phase slop-gate/drift-grep
precedents. Nothing depends on Phase 6 except the post-mockup v2 planning session, which consumes
its SC-006 map.

## Depends On (from prior plans)

| Source | What this phase consumes |
|--------|--------------------------|
| Phase 1 | Single-file `prototype/index.html` (file:// contract — no fetch, no local ES modules; only https CDN import-map imports and classic `<script src>` work from disk); `render(appState)` + hash routing; scenario engine (`{narration, patch, transition?}` + `advance()`, index at `appState.chat.scriptIndex`); closed op vocabulary (5 ops); **driver.js already pinned in the import map — usage was deferred to THIS phase**; design + motion tokens; `#/` chooser stub (bare route, outside the three-tier shell); reduced-motion fade fallback. |
| Phase 2a | `window.ORG` via classic script `prototype/data/org.js` (generator-authored, seed 42, never hand-edited); canonical vocabulary (CAST-412 "Add RBAC to checkout" · CAST-431 · CAST-452 · CAST-461 · M04/S03/R02 · rework 1/3 · 99.9%·505 · 99.4%·312 · crud-orchestrator · CAST-417 = THE feature L3); drift-grep canon recorded for this phase's final re-run; the `#/kit` fixture-literal exception (sanctioned "until its data swap"). |
| Phase 2b | Component kit + avatar grammar (human=circle, maker=square outline, checker=square fill, Guide=diamond); `#/kit` isolation route (hidden from nav); slop-gate mechanic: `/cast-preso-check-visual` + `/cast-preso-check-tone` on screenshots, scoped to `not-generic`/`not-ai-aesthetic`; L-badge colors; ●/◐/○ confidence glyphs (never percentages). |
| Phase 3 | `SCRIPTS.feature`/`SCRIPTS.debug` + additive `appState.chat.scriptKey`; the real CAST-412 morph (one atom DEC-CAST-412-03, one receipt, undo emits no second receipt); execution drill-in; **E1 rasters in `prototype/assets/` loaded by relative `<img>` with 2b CSS/SVG onerror fallback** — the inlining decision of this phase resolves their packaging; drift-grep base set. |
| Phase 4 | `SCRIPTS.spike`/`SCRIPTS.data` (SCRIPTS map complete at 4 family keys); the data flow's L3 = the one script-wired rail resolution (reload resets, ORG unmutated); FR-017 parity pane (`appState.parityOpen`); drift additions: `CAST-452 · CAST-461 · 180ms · 1h40m · 8% · source names`. |
| Phase 5 | Final route table (10 routes: `#/board · #/ticket/CAST-412 · #/decision/:atomId · #/decisions/CAST-412 · #/hire · #/marketplace · #/agent/:slug · #/skills/new · #/layer2 · #/reqs/CAST-412`); `SCRIPTS.hiring` (script keys closed at 5); appState additive keys (`boardFilter · hiring · autonomyLevel · reqsDoc`); drift additions (CAST-417 · PR # canon · 99.4 · 312 · 6 candidates · 12 contracts · 8-agent chain · 5 dimension names · PM persona name · cast-export-csv); cross-link audit precedent. |

**Total route inventory Phase 6 fronts:** `#/` (chooser, this phase makes it real) ·
`#/goal/:id` ×4 goals · the 10 Phase 5 routes · `#/kit` (hidden harness). The five chooser
scenarios map 1:1 onto the five `SCRIPTS` keys: feature, debug, spike, data, hiring.

## Contracts This Phase Exports

- **`prototype/dist/diecast-prototype.html`** — the single distributable file (generated, never
  hand-edited; regenerate via `prototype/_build/inline.mjs`).
- **`docs/plan/product-revamp-diecast-v2-surface-goal-map.md`** — the SC-006 surface→buildable-goal
  map, input to the post-mockup v2 planning session.
- **`TOURS` map** (`{feature, debug, spike, data, hiring}`) keyed identically to `SCRIPTS`;
  `data-tour="…"` anchor attributes on shell zones and key components.
- **appState additive key:** `demoScriptOpen: boolean` (presenter overlay). No new ops (closed
  at 5), no new SCRIPTS keys (closed at 5), no new top-level ORG keys.
- **CSS prefixes:** `choose-*` (chooser) · `tour-*` (driver.js token overrides) · `demo-*`
  (demo-script overlay), following the per-surface prefix convention.

---

## Sub-phase 6.1: Front Door — Scenario Chooser & Guided Walkthroughs

**Outcome:** A stranger can land on `#/`, understand the five things the demo can show, click one,
and be carried through it: the FR-002 scenario chooser is real (replacing the Phase 1 stub), each
of the five flows has a driver.js anatomy tour, and a presenter-facing demo-script overlay shows
the current flow's scripted beats. The demo self-navigates (SC-002 precondition).

**Dependencies:** Phases 4 + 5 executed (all routes and all five SCRIPTS exist).

**Estimated effort:** 1 session (~3h)

**Verification (manual, from disk):** Open `prototype/index.html` via file:// in Chrome. `#/`
shows five scenario cards + a standalone-areas row; every card and link routes correctly and
resets the right script (scriptKey set, scriptIndex 0). Start each of the five tours: popovers
appear on the right elements, styled in Diecast tokens (visibly NOT stock driver.js), next/prev
work, Esc dismisses. Press `s` inside a flow: the demo-script overlay lists that flow's beats with
the current beat highlighted; advancing chat moves the highlight; `s` again (or ✕) closes it.
With reduced-motion emulated, tour transitions don't animate. Reload anywhere → clean reset, no
console errors.

Key activities:

- **Chooser screen (`#/`, bare route per Phase 1 — no nav/chat shell):** five verb-first scenario
  cards — "Follow a feature" (CAST-412, `SCRIPTS.feature`) · "Chase a bug" (CAST-431,
  `SCRIPTS.debug`) · "Run a spike" (CAST-452, `SCRIPTS.spike`) · "Answer a data question"
  (CAST-461, `SCRIPTS.data`) · "Hire an agent" (`#/hire`, `SCRIPTS.hiring`). Card title/goal-id/
  one-line hook derive from `ORG.goals` (drift rule: goal titles never retyped); the verb labels
  and a static `SCENARIOS = [{key, verb, route, scriptKey, blurb}]` descriptor are demo chrome and
  live inline in `index.html`. Each card: primary affordance enters the flow (sets
  `chat.scriptKey`, resets `chat.scriptIndex`, navigates — plain handler, no new op); secondary
  "Guided tour" link enters the flow AND starts that flow's driver.js tour.
- **Standalone-areas row** below the cards: Board · Marketplace · Agent ops
  (`#/agent/crud-orchestrator`) · Layer-2 · Requirements doc (`#/reqs/CAST-412`) · Decision trail
  (`#/decisions/CAST-412`). `#/kit` stays hidden. The Guide opens the screen with one line in its
  voice (diamond GuideMark) — the persistent character is present at the front door. Typographic
  cards only (mono goal-ids, family-shape glyph reused from StageSpine); no new illustrations.
- **driver.js wiring:** import from the Phase 1 import-map pin; add the driver.js v1 stylesheet
  via CDN `<link>` (a gap no prior phase covered — see design review) plus a `tour-*` token
  override block restyling popovers: `--paper` background, `--ink` text, mono titles, raspberry
  progress/active accents, `--radius-sm/md`, no shadows beyond the existing elevation idiom.
  Stock driver.js styling would fail the slop gate on sight.
- **Five tours, `TOURS` keyed like `SCRIPTS`,** 5–8 stops each, anchored on new
  `data-tour="…"` attributes (added to shell zone wrappers and key components — attributes, not
  CSS classes, so styling refactors can't silently break tours). Tours explain **anatomy, not
  story**: where the WHAT lives, the stage spine and its family shape, evidence, the chat rail,
  where decisions surface, the dial/escalation where relevant. The last stop of every tour points
  at the chat advance control: "the demo advances here" — handing off to the scenario engine,
  which owns the narrative. Tours never call `advance()`. Set driver.js `animate: false` under
  `prefers-reduced-motion`.
- **Demo-script overlay (the "both" half of the owner's walkthrough default):** a dismissible
  presenter panel (`demo-*` prefix; paper surface, ink text) toggled by the `s` key and a small
  control in the nav-rail footer; renders `SCRIPTS[chat.scriptKey]` as a numbered beat list
  (narration + a one-line hand-authored talking point per beat) with the `chat.scriptIndex` beat
  highlighted. State = new additive `appState.demoScriptOpen` boolean; plain handler; reload
  resets. Positioned bottom-left so it never covers the chat rail. Copy obeys FR-018 (hyphens not
  em dashes, no GPT-isms) — it will be tone-gated in 6.2.

**Design review:**
- ⚠ **driver.css was never planned:** Phase 1 pinned the driver.js *module* but no phase added its
  stylesheet. Action (in activities): CDN `<link>` + token override block. Not a prior-phase
  revision — Phase 1 explicitly deferred all usage here.
- ⚠ **Stock-tour slop risk:** default driver.js popovers (white, rounded, generic sans) are
  exactly the generic aesthetic the gate exists to kill. The `tour-*` override block is mandatory,
  and one tour-popover-open capture is in the 6.2 gate list.
- **Naming:** `data-tour` attributes, `TOURS` keyed = `SCRIPTS` keys, `choose-*`/`tour-*`/`demo-*`
  prefixes — all follow established conventions. ✓
- **Architecture:** no new ops, no new script keys, one additive appState key; chooser stays a
  bare route (Phase 1 precedent), so no vt- anchor duplication risk (anchors live on shell zone
  wrappers, which the chooser doesn't render). ✓
- **Edge:** keyboard `s` only binds outside text inputs (the prototype has none, but the parity
  terminal pane fakes one — guard on `event.target`); tour start on a route whose element set
  doesn't match (e.g., user navigated mid-tour) → driver.js skips missing stops natively; verify
  it degrades quietly rather than erroring.

---

## Sub-phase 6.2: The Gate — Density/Consistency Pass + Full Slop-Gate Sweep

**Outcome:** Every screen in the prototype — including the three new Phase 6 surfaces — passes
`not-generic` / `not-ai-aesthetic`, and a cross-surface density/consistency pass has removed the
tells that say "mockup": filler text, skeleton corners, token drift, inconsistent grammar. This is
the SC-004 gate ("showable without apology") run as a single full sweep, superseding the per-phase
spot gates.

**Dependencies:** Sub-phase 6.1 (the new surfaces must exist to be gated).

**Estimated effort:** 1 session (~3h), gate reruns included

**Verification (manual):** The consistency checklist below has every box checked; all 21 gate
captures have passing verdicts from both checkers; every flagged surface was fixed and re-gated;
zero hardcoded hex outside `:root`; zero lorem/TODO/FIXME/placeholder strings render anywhere
(including the retired Phase 1 spine watermark).

Key activities:

- **Density + consistency pass (one sweep, all routes), checklist:**
  - Token discipline: grep `prototype/index.html` for hex literals outside `:root` → migrate to
    tokens (the Phase 4 parity ink-dark pane already uses tokens; it stays the one sanctioned
    identity exception).
  - Rhythm + type: 8px spacing scale holds; mono = machine voice (ids, stats, logs), sans = human
    prose, consistently; label casing and button hierarchy (hero/outline/ghost) match the
    escalation-rail grammar everywhere.
  - Grammar consistency: avatar shapes (circle/square-outline/square-fill/diamond), L-badge
    colors, ●/◐/○ confidence (no percentages anywhere), receipts/pills render identically across
    routes.
  - Density: every panel carries believable product-grade content — no empty corners, no
    one-line stubs left from phase stitching; sweep rendered output for `lorem`, `TODO`, `FIXME`,
    `placeholder`, `stub`, and the Phase 1 watermark idiom; confirm `placeholder:false` spine
    state shows no residue.
- **Full slop-gate sweep — 21 captures** (per-phase gates covered ≤15 surfaces; this is the
  every-screen re-run the high-level plan requires). Capture via the `/browse` headless-browser
  skill against the file:// URL (manual Chrome screenshots are an acceptable fallback):
  1. `#/` chooser at rest · 2. a tour popover open (feature tour, stop 2-ish) · 3. demo-script
  overlay open over the feature canvas · 4. `#/goal/CAST-412` at rest · 5. CAST-412 execution
  drill-in, focus-run tree open · 6. CAST-412 post-morph debug-shape state · 7. `#/goal/CAST-431`
  (iteration panel + E2/E3 visible) · 8. `#/goal/CAST-452` at rest · 9. CAST-452 parity moment
  open · 10. `#/goal/CAST-461` at rest (◐-flagged E5) · 11. CAST-461 resolved state (post-L3
  re-rendered E5) · 12. `#/board` · 13. `#/ticket/CAST-412` · 14. CAST-417 escalation frame
  (`#/decision/…`) · 15. `#/decisions/CAST-412` (trail + dial) · 16. `#/hire` step 3 stack-ranked
  report (remaining wizard steps eyeballed, not formally gated) · 17. `#/marketplace` ·
  18. `#/agent/crud-orchestrator` (resume + one ops tab) · 19. `#/skills/new` · 20. `#/layer2` ·
  21. `#/reqs/CAST-412` (delta view on).
  → Delegate: `/cast-preso-check-visual` + `/cast-preso-check-tone` on each capture, scoped (as
  in Phases 2b–5) to `not-generic` / `not-ai-aesthetic`. Review verdicts; fix flags in
  `prototype/index.html`; re-capture and re-gate **failed surfaces only**.
- **Tone pass on the new copy:** chooser blurbs, tour stop text, demo-script talking points run
  through the tone check with the captures; FR-018 vocabulary rules (Diecast, `cast-*`, Layer not
  Tier, maker-checker, hyphens not em dashes) applied.

**Design review:**
- ⚠ **Gate volume:** 21 captures × 2 checkers is the largest gate run of the project — batch the
  captures first, then run checkers over the batch; re-gate only failures (activities reflect
  this). Budgeted inside the session estimate.
- ⚠ **Fixes can move tour anchors:** density fixes that restructure DOM can orphan `data-tour`
  stops. Rule: 6.2 fixes preserve `data-tour` attributes; a post-fix tour click-through is part of
  6.4's final checklist.
- **NO TESTS compliance:** everything here is screenshots + human checklist; no harness. ✓

---

## Sub-phase 6.3a: Distributable — Single-File Inline + Disk Smoke Test (parallel with 6.3b)

**Outcome:** One file — `prototype/dist/diecast-prototype.html` — contains the entire prototype
(markup, styles, scripts, ORG data, base64 E1 rasters) and runs every flow when double-clicked
from disk, with only the locked CDN libraries and fonts fetched from the network. The final
cross-surface fake-data drift sweep is clean with **zero** sanctioned exceptions.

**Dependencies:** Sub-phase 6.2 (inline after content is final — never before, or every fix
happens twice).

**Estimated effort:** 0.5–0.75 session (~2h)

**Verification (manual, from disk):** Double-click `prototype/dist/diecast-prototype.html` →
all five scenarios run end-to-end; the morph plays; E1 rasters render (network tab shows requests
only to the pinned CDNs + fonts — no `assets/` or `data/` requests); tours + demo overlay work;
reduced-motion fallback works; console clean; file size recorded and ≤ ~5MB; the dist header
comment marks it generated. Dev `prototype/index.html` still works unchanged. The drift grep
returns hits only from the ORG data block; lorem/em-dash sweep returns zero.

Key activities:

- **Write `prototype/_build/inline.mjs`** — a zero-dependency, build-time-only Node one-shot
  (the Phase 2a generator precedent; never part of the runtime or dev loop) that reads
  `prototype/index.html` and emits `prototype/dist/diecast-prototype.html`:
  - Replace `<script src="data/org.js"></script>` with the file's content inlined as a classic
    script block (match on the exact `src` attribute, not generic regex over all scripts).
  - Replace each `<img src="assets/…">` with a base64 data-URI (E1 rasters). Size guard: if the
    emitted file exceeds ~5MB, recompress rasters to WebP ≤250KB each and re-run.
  - Prepend a header comment: `<!-- GENERATED by prototype/_build/inline.mjs — edit
    prototype/index.html, then re-run. -->`. Idempotent: re-running regenerates from dev files.
  - 2b's CSS/SVG `onerror` raster fallbacks stay in the markup (inert once inlined — harmless,
    and they keep the dev file resilient).
- **CDN deps stay CDN** (import-map preact/htm/driver.js, driver.css link, Google Fonts): the
  "opens from disk" contract has meant "one local file + https CDN" since Phase 1's file://
  constraint analysis — vendoring ES modules into the file without a bundler is brittle and
  re-introduces exactly the toolchain FR-001 forbids. Documented tradeoff: the file needs network
  for ~15KB of libraries + fonts; a fully-offline variant (one-shot `vite-plugin-singlefile`, per
  the playbook, outside the dev loop) is noted as available but **not built**.
- **Final fake-data drift sweep (the 2a canon re-run, on the dev files, post-6.2):**
  consolidated grep set = Phase 3 base (CAST-412 "Add RBAC to checkout" · M04/S03/R02 · 99.9 ·
  505 · rework 1/3 · crud-orchestrator) + Phase 4 additions (CAST-452 · CAST-461 · 180ms · 1h40m
  · 8% · source names) + Phase 5 additions (CAST-417 · canon PR # · 99.4 · 312 · 6 candidates ·
  12 contracts · 8-agent chain · 5 dimension names · PM persona name · cast-export-csv). Every
  canonical literal in `index.html` must come from `ORG` rendering, not retyped strings — eyeball
  each grep hit; new Phase 6 copy (tours, demo script, chooser) is checked for goal-title/id
  consistency against `ORG.goals`.
- **Retire the `#/kit` exception:** 2b's fixture literals were "the one sanctioned grep exception
  until its data swap" — complete the swap (kit fixtures read `ORG`) if execution hasn't already,
  so the final sweep passes with zero exceptions. `#/kit` ships inside the dist (hidden,
  hash-only, harmless) rather than being stripped — stripping buys nothing and complicates the
  inliner.
- **Disk smoke test** of the dist file per the verification paragraph above, including a
  network-tab pass confirming no local-path requests escaped inlining.

**Design review:**
- ⚠ **Generated-file hygiene:** the dist file will tempt hand-edits during demo prep. The header
  comment + "regenerate, never edit" rule in activities is the guard.
- ⚠ **Inliner brittleness:** matching exact `src` attributes (not greedy regex) and the
  re-run-idempotent design keep the 60-line script from corrupting markup; the smoke test is the
  backstop. No error-handling beyond "refuse to emit if an expected src isn't found" (mirrors the
  2a generator's refuse-on-violation posture).
- **file:// legality re-verified post-inline** — base64 data-URIs and inline classic scripts are
  exactly the file://-legal forms Phase 1 established; the inliner introduces no `fetch`. ✓
- **NO TESTS compliance:** the inliner is packaging tooling (2a precedent), not a test harness;
  its only check is refuse-on-missing-src. ✓

---

## Sub-phase 6.3b: The Map — Surface→Buildable-Goal Roadmap (SC-006) (parallel with 6.3a)

**Outcome:** `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` exists: every prototype
surface maps to a named, buildable, stack-rankable follow-on v2 goal — the input document for the
post-mockup v2 planning session. SC-006 is satisfiable the moment that session convenes.

**Dependencies:** Sub-phase 6.2 (surfaces final — the map describes what actually shipped).
Independent of 6.3a; runs in parallel.

**Estimated effort:** 0.5 session (~1.5h)

**Verification (manual):** Every route in the final inventory (chooser + 4 goal canvases + 10
Phase 5 routes + the cross-cutting mechanics) appears exactly once; every row names a concrete
goal slug with an outcome sentence, size, dependencies, and a suggested rank; a cold reader could
create the v2 goal backlog from this document alone.

Key activities:

- **One table per theme group**, rows = surfaces, columns: *Surface/Route* · *What it proves*
  (FR/US/SC refs) · *Follow-on v2 goal* (kebab slug + one-line outcome) · *Size* (S/M/L) ·
  *Depends on* (other v2 goals) · *Suggested rank*. Groups: canvas core & morph (render
  architecture, family canvases, chat steering) · evidence (E1–E5 as real artifact pipelines) ·
  decisions & autonomy (atom capture, trail, dial, escalation) · colleague surfaces (board,
  ticket, hiring, marketplace, agent ops) · platform substrate (scenario-engine→real chat,
  `org.js`→real API, three access tiers) · requirements loop (ties to the separate
  refine-requirements-v2 goal — reference, don't duplicate).
- **Cross-cutting mechanics get rows too** (the morph itself, the decision-receipt mechanism, the
  L1/L2/L3 autonomy engine, the slop-gate-as-CI idea) — SC-006 says *each surface maps to a
  buildable goal*, and the mechanics are the most build-relevant "surfaces" of all.
- **Suggested rank is advisory:** the column seeds the stack-ranking conversation; the v2 planning
  session owns the final order. State this in the doc's preamble.
- Cross-reference each row against the refined requirements' FR/US table so no FR lands
  unmapped; note explicitly which v1 prototype elements are *demo chrome with no v2 goal* (tours,
  demo overlay, inliner) so the map is exhaustive rather than silently partial.

**Design review:**
- ⚠ **Vague-goal risk:** "improve the board" is not buildable. Rule in activities: every row's
  goal has a one-line *outcome* (what is true when done), same discipline as this plan's
  sub-phases.
- **Location/naming:** `docs/plan/` beside the decisions-so-far doc, project-prefixed name —
  consistent with the planning artifact convention. ✓

---

## Sub-phase 6.4: Showability Sign-Off — SC-002 Dry Run & Final Checklist

**Outcome:** The phase gate passes end-to-end on the **dist file**: the high-level Phase 6
verification paragraph holds, and the one item no machine can verify — a fresh viewer stating
what the product does within ~3 minutes (SC-002) — is staged as a concrete human action with the
artifact ready to hand over.

**Dependencies:** Sub-phases 6.3a + 6.3b.

**Estimated effort:** 0.25–0.5 session (~1h)

**Verification (manual — this IS the phase and project gate):** On
`prototype/dist/diecast-prototype.html` from disk: each of the five chooser scenarios walks
start-to-finish; each tour click-through still anchors correctly post-6.2 fixes; every flow shows
≥1 in-context decision record and the prototype contains the autonomy-gated stop (SC-007
final cross-check); feature-vs-debug side-by-side contrast obvious (SC-005 spot-check); the
SC-006 map exists and is exhaustive; slop-gate and drift-sweep results from 6.2/6.3a are on
record. SC-002 itself: owner shows the dist file to 1–2 fresh peers using the chooser + tours and
records whether they can state what the product does within ~3 minutes — **the one human action
item this plan leaves open**.

Key activities:

- Run the five-scenario full click-through on the dist file (not the dev file — the distributable
  is what gets shown).
- Post-fix tour audit: every `data-tour` stop in all five tours still resolves (6.2's flagged
  risk, closed here).
- SC-001/SC-007 final cross-check against the refined requirements' success-criteria table;
  record the per-criterion verdicts in a short closing note appended to the decisions-so-far doc
  (one paragraph, not a new artifact).
- Stage the SC-002 showing: hand the owner the dist file path + the suggested 3-minute path
  (chooser → "Follow a feature" tour → morph beat → board). Recording the peer's statement is the
  owner's action, outside this plan's execution.

**Design review:**
- **No flags** — this sub-phase creates nothing new; it executes checklists defined above. The
  only output is the verdict note appended to decisions-so-far.

---

## Build Order

```
{ Phase 4 ∥ Phase 5 done }
          │
          ▼
   Sub-phase 6.1  (chooser + tours + demo overlay)
          │
          ▼
   Sub-phase 6.2  (density pass + 21-capture slop gate)
          │
   ┌──────┴──────┐
   ▼             ▼
 6.3a          6.3b
 (inline +     (SC-006
  drift +       surface→goal
  disk smoke)   map)
   └──────┬──────┘
          ▼
   Sub-phase 6.4  (dist-file gate + SC-002 staging)
```

**Critical path:** 6.1 → 6.2 → 6.3a → 6.4. (6.3b is off the critical path; it can also absorb
idle time during 6.2's checker runs.)

**Honest effort total: ~2.75–3.25 sessions** vs the high-level envelope of 2. The overage is the
21-capture full gate (the per-phase gates never covered everything at once) and the five tours.
Per the owner's no-cut policy: extend the timeline, don't cut — nothing here is optional for
SC-002/SC-004/SC-006.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 6.1 | driver.css never planned by any prior phase | Add CDN `<link>` + `tour-*` token override block (in 6.1 activities) |
| 6.1 | Stock driver.js popover styling = instant slop-gate failure | Token override mandatory; tour-popover capture #2 in the 6.2 gate list |
| 6.1 | `s` shortcut could fire inside the parity fake-terminal | Guard handler on `event.target` |
| 6.2 | Largest gate run of the project (21 × 2 checkers) | Batch captures, then checkers; re-gate failures only |
| 6.2 | Density fixes can orphan `data-tour` anchors | Fixes preserve `data-tour`; post-fix tour audit in 6.4 |
| 6.3a | Dist file invites hand-edits | Generated-file header + regenerate-never-edit rule |
| 6.3a | Inliner could corrupt markup | Exact-src matching, refuse-on-missing-src, disk smoke test backstop |
| 6.3b | Map rows degenerate into vague themes | Every row needs a one-line outcome, same bar as sub-phase outcomes |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| A late slop-gate failure on an old surface implies a big re-design at the worst time | High | The per-phase gates (2b–5) already passed these surfaces; 6.2 is a regression re-run, so failures should be drift-sized, not design-sized. If a structural failure appears, fix the *component* (kit-level), not the screen — the data-driven render propagates it everywhere |
| Base64 rasters balloon the dist file past emailable size | Med | ~5MB guard + WebP recompression step in the inliner activity; E1 is the only raster set in the prototype |
| CDN dependency makes the demo fail offline (conference wifi, airplane) | Med | Documented tradeoff with a named fallback (one-shot `vite-plugin-singlefile`, never in dev loop); the owner knows the file needs network for ~15KB of libs + fonts before any showing |
| Tour copy drifts the canon (retyped goal titles in popover text) | Med | Phase 6 copy explicitly included in the 6.3a drift sweep; titles render from `ORG.goals` wherever possible |
| SC-002 fails with the fresh peer (they can't say what the product is) | High | That outcome is the *point* of the test — it feeds the v2 map's rankings rather than blocking this phase; the chooser + tour path is designed around the 3-minute read (verb-first cards, anatomy tours) |
| 21-capture gate + fixes overruns the session budget | Med | Honest estimate already raised to ~3 sessions; owner policy is extend-not-cut |

## Open Questions

None blocking — full-autonomy directive; every judgment call is recorded below. Three
execution-time taste calls intentionally left to the builder (all reversible in minutes):
exact tour stop counts/copy per flow (within the 5–8 band), the chooser's family-shape glyph
treatment on cards, and whether the hiring wizard's non-report steps need formal gate captures
after eyeballing (escalate into the gate list only if the eyeball is doubtful).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| (none) | — | — |

Per FR-020 and the delegation directive, this deliverable is greenfield: the seven cast-server
specs in `docs/specs/_registry.md` govern the runtime/infrastructure, not this prototype. No
`/cast-update-spec` flow is invoked. (Forward note, unchanged from the high-level plan: when the
SC-006 map's v2 goals are planned, *those* plans author product specs — downstream of this one.)

## Decisions Made Autonomously

1. **Sub-phase shape 6.1 → 6.2 → {6.3a ∥ 6.3b} → 6.4** — chooser/tours must exist before the
   every-screen gate; inlining strictly after content is final; the SC-006 map needs final
   surfaces but not the dist file, so it parallelizes with inlining.
2. **Walkthrough format = BOTH driver.js tours + demo-script overlay** — adopted the
   plan.collab.md USER-DEFERRED default verbatim, restated as the owner default in this run's
   dependencies. No new information argued against it.
3. **Five tours keyed identically to `SCRIPTS`; tours teach anatomy, scripts carry the story;
   tours never call `advance()`** — keeps one narrative engine (the Phase 1 scenario engine) and
   makes tours safe to run at any script index.
4. **Tour anchors = `data-tour` attributes**, not CSS classes — styling refactors (6.2 will cause
   them) can't silently break tours.
5. **driver.css via CDN `<link>` + mandatory token restyle** — closes a real gap (no phase
   planned the stylesheet) without touching the Phase 1 plan; stock styling would fail the gate.
6. **Demo-script overlay = `appState.demoScriptOpen` + plain handler + `s` key** — one additive
   key, no sixth op (vocabulary stays closed at 5), reload-resets like every other UI state.
7. **Chooser stays a bare route** (Phase 1 "Home = bare scenario-chooser" precedent) with a
   GuideMark intro line; card titles/ids render from `ORG.goals` (drift rule); verb labels are
   demo chrome inline in `index.html`. **No ORG generator batch in Phase 6** — chooser/tour/demo
   copy is presentation chrome, not org data.
8. **Single-file mechanism = zero-dep Node one-shot `prototype/_build/inline.mjs` emitting
   `prototype/dist/diecast-prototype.html`** — deviates from the playbook's "hand-inline by hand"
   because base64-encoding rasters by hand is error-prone and unrepeatable; the 2a generator
   established the build-time-Node-tooling precedent; `vite-plugin-singlefile` rejected as a
   dependency for what ~60 lines of `fs` + exact-src replacement does. Dev files stay canonical;
   dist is generated and regenerable.
9. **E1 rasters base64-inlined in the dist** (the delegation explicitly left this my call) —
   a truly single emailable file beats a file+folder pair for SC-004's "distributable" intent;
   cost is ~33% size on a handful of images, bounded by the ~5MB guard + WebP recompression.
   Dev keeps relative paths + the 2b onerror fallback.
10. **CDN libraries/fonts stay CDN in the dist** — "opens from disk" has meant "local file +
    https CDN" since Phase 1's file:// analysis; vendoring ESM without a bundler is brittle and
    against FR-001's spirit. Offline tradeoff documented with a named, not-built fallback.
11. **`#/kit` exception retired in the final drift sweep** (complete the 2b data swap if
    execution hasn't) so the project-final sweep has zero sanctioned exceptions; `#/kit` ships
    hidden inside the dist rather than being stripped (stripping adds inliner complexity for no
    viewer-visible gain).
12. **Gate list fixed at 21 captures** including the three new Phase 6 surfaces and both scripted
    states (morphed CAST-412, resolved CAST-461); hiring wizard formally gated on its hero
    report-card step only, others eyeballed — formal-gating all five wizard steps would add 8
    captures for screens that share one layout family.
13. **Honest effort ~2.75–3.25 sessions vs the 2-session envelope**, stated rather than squeezed
    — Phase 5 precedent + the owner's extend-don't-cut policy.
14. **SC-002 fresh-viewer test = the single human action item**; staged (artifact + suggested
    3-minute path) but its execution is by definition outside an autonomous run.
15. **No standalone demo-runbook document** — the demo-script overlay is the runbook (HOLD SCOPE;
    the high-level plan never asked for one).
16. **Plan review skipped** per the run configuration in decisions-so-far ("Plan review: skipped —
    cross-phase reconciliation only"; Phases 1–5 precedent). Treated as `no_review: true`; a
    manual `/cast-plan-review` command is recorded in this run's next_steps instead.

## Suggested Revisions to Prior Sub-Phases

None required. Two near-misses checked and cleared: (a) Phase 1's driver.js import-map pin lacked
the stylesheet — but Phase 1 explicitly deferred *all* driver.js usage to this phase, so adding
the `<link>` here is consumption, not revision; (b) Phase 4's "no further script keys planned"
was already revised by Phase 5 (`SCRIPTS.hiring`), and Phase 6 adds none — the five-key set this
plan's chooser fronts is exactly the closed set Phase 5 exported.
