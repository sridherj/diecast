# Shared Context: Product Revamp: Diecast — Phase 1 (Keystone)

> Read this file at the start of **every** sub-phase. It carries the cross-phase contracts,
> the binding constraints, and the codebase conventions all three sub-phases share. The
> per-sub-phase `plan.md` files do not repeat it — they reference it.

## Source Documents
- **Plan:** `docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md` (the detailed phase plan — the authority for Outcome / Verification / Key activities / Design review of each sub-phase).
- **Decisions ledger:** `docs/plan/product-revamp-diecast-decisions-so-far.md` (owner-locked stack/identity/run-config decisions; the morph-gate verdict is appended here in 1.3).
- **Reconciliation:** `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` (cross-phase COHESIVE check across all 8 phases).
- **Exploration playbooks (reference, not boundary):** `goals/product-revamp-diecast/exploration/playbooks/02-canvas-chat-mechanics.ai.md` (dispatcher + scenario engine keystone) and `goals/product-revamp-diecast/exploration/playbooks/06-prototype-build-approach.ai.md` (no-build single-file architecture). NOTE playbook 06's `import './state.js'` snippet is **deliberately not followed** — see the `file://` constraint below.
- **Design reference:** `goals/product-revamp-diecast/exploration/design-samples/app-shell.html` (the `:root` token block is lifted from here verbatim; the layout is a *reference, not a boundary*).

## Project Background

This phase builds the load-bearing skeleton of the Diecast vision prototype and answers its
riskiest technical unknown: **can a static file, opened from disk with no build step, deliver
a vision-grade canvas morph?** The deliverable is one self-contained file,
`prototype/index.html`, where `render(appState) → DOM` drives every pixel, `location.hash`
routes between surfaces, all interactivity flows through a ~30-line typed-op dispatcher
(`morph · nudge · promote · drillInto · pin`), and a placeholder feature-spine → debug-spine
**hero morph** runs through the CSS View Transitions API at a locked motion register (~350ms,
≥4 persistent anchors, reduced-motion fade fallback).

The phase ends at a **morph decision gate** (resolved *inside* sub-phase 1.3, autonomously,
via a pre-written 5-item checklist — **not** a separate human gate): View Transitions carries
the morph convincingly → Phase 3 builds real canvases on this technique; it doesn't → switch
to the keyed CSS panel-swap contingency *before* any real canvas is built.

Everything later phases touch is exported here as a contract (tokens, `appState` shape, op
vocabulary, scenario-step shape, anchor names, packaging rule). Get this phase right and every
subsequent screen is a ~10-line data slice; get it wrong and the mockup becomes a project.

## Operating Mode — FULL AUTONOMY

**FULL AUTONOMY MODE (owner-approved).** Never ask the user questions, never pause for approval
gates, never go idle waiting for input. At any decision gate, pick the recommended option and
document it inline in the sub-phase output. Propagate this directive verbatim to any child
agent you dispatch. The phase-level "HOLD SCOPE" rule also applies: skeleton + spike only — no
real surfaces, no real data, no component kit (those are Phases 2–3). Rigor goes into edge
cases (file:// constraints, reduced motion, transition failure modes), not extra features.

---

## BINDING CONSTRAINTS (encoded into every sub-phase — do not violate)

These are hard rules. A sub-phase that breaks one is wrong even if it "works."

### C1 — NO TESTS anywhere
No test files, no test suites, no harnesses, no CI, no pytest, no `*.test.*`, no assertion
frameworks. **Verification is manual click-through only:** open `prototype/index.html` from
disk in Chrome (double-click / `file://`) and observe. Every "Verification" section in these
sub-phases is human-eyeball + DevTools observation. If you feel the urge to write a test,
write a manual-check step instead.

### C2 — `file://` legality (single-file inline architecture is FORCED)
A page opened from disk has origin `null`, which **blocks**:
- `fetch()` (CORS) — so **no** `fetch('data/org.json')`.
- local ES-module imports — so **no** `import './state.js'`, no relative `import` of project files.

Only these load from disk and are therefore **allowed**:
- **https CDN imports** via the import map (e.g. `import { render } from 'preact'` resolved to an `esm.sh` URL).
- **classic `<script src>`** tags (including a classic local `prototype/foo.js` if ever needed — but Phase 1 ships none).
- **relative `<img>`** (`<img src="./asset.png">`).
- inline `<style>` and inline `<script type="module">`.

Single-file inline architecture is the *consequence*, not a style choice.

### C3 — Prototype code root & packaging
Prototype code root is `prototype/` (i.e. `/home/sridherj/workspace/diecast/prototype/`).
**Phase 1 ships exactly one file: `prototype/index.html`** — inline `<style>` + inline
`<script type="module">`, nothing else. No `state.js`, no `data/org.json`, no CSS file.

### C4 — Cross-phase contracts are exported by THIS phase (encode verbatim, downstream extends-not-renames)
The contracts in the next section are the interfaces later phases consume. Implement them
exactly as written. Downstream phases may *extend* them (add keys/values) but must **not**
rename existing keys or change the op grammar.

### C5 — Failure policy
Retry a failed sub-phase **once** with refined instructions. A second failure → mark the
sub-phase **partial** and log the specific gap (what failed, what was tried, what remains) in
the sub-phase output and the manifest Notes column. Do not silently drop work.

---

## Data Schemas & Contracts (the 7 exported contracts — copy verbatim)

These come from the plan's "Contracts This Phase Exports" section. Reproduce them exactly in
`prototype/index.html`.

### Contract 1 — File layout & packaging rule
Build root `prototype/`; Phase 1 ships exactly one file, `prototype/index.html`, with inline
`<style>` and inline `<script type="module">`. `file://` blocks local ES-module imports *and*
`fetch()`; only https CDN imports (import map), inline modules, and classic `<script src>` work
from disk. (Identical to C2/C3 above — the constraint *is* the contract.)

### Contract 2 — `appState` shape (v1 — Phase 2a extends; must NOT rename existing keys)
```js
const appState = {
  route:   '#/goal/CAST-412',        // mirror of location.hash, set by router
  family:  'feature',                // 'feature' | 'debug'  (2a adds: 'spike' | 'data')
  goal:    { id: 'CAST-412', title: 'Add RBAC to checkout', crumb: 'northwind / goals' },
  spines:  {                         // PLACEHOLDER labels — Phase 2c replaces vocabulary
    feature: { placeholder: true, shape: 'segments',
               steps: ['Requirements','Exploration','Plan','Execution','Ship'], current: 3 },
    debug:   { placeholder: true, shape: 'loop', iter: { current: 2, budget: 3 },
               steps: ['Reproduce','Hypothesize','Experiment','Observe'], current: 1 },
  },
  nudge:   { who: 'Guide', do: 'Review CAST-412’s PR', why: 'checker flagged R02 — unblocks 2 queued tasks' },
  receipts: [],                      // decision receipt stubs, pushed by morph op
  pinned:  [],                       // canvas objects created by promote/pin ops
  drill:   null,                     // 'execution' | null — drillInto target
  chat:    { messages: [], scriptIndex: 0 },
};
```

### Contract 3 — Op vocabulary (closed set; all changes route through ONE dispatcher)
`morph:<family>` · `nudge:<id>` · `promote:<artifactId>` · `drillInto:<target>` ·
`pin:<artifactId>`. Chat/canvas controls carry `data-op="op:arg"`. `pin` stays a **distinct**
op from `promote` (not aliased) — the closed 5-op vocabulary is itself the contract being
proven.

### Contract 4 — Scenario step shape
`{ narration: string, patch: (s) => void, transition?: 'morph' }` walked by `advance()`;
engine state lives in `appState.chat.scriptIndex` (replayable — reload resets cleanly).

### Contract 5 — View-transition anchor names (persistent chrome set, prefix `vt-`)
`vt-goal-header` · `vt-chat-rail` · `vt-nudge-card` · `vt-receipt-trail` · `vt-nav-rail`
(5 anchors — the ≥4 requirement with one spare). **Uniqueness rule:** each name must appear on
exactly one rendered element per snapshot, or the whole transition silently skips. Anchor
elements stay *mounted across both families* (same component identity, different content).

### Contract 6 — Motion tokens
`--morph-duration: 350ms` · `--ease-morph: cubic-bezier(0.2,0.8,0.2,1)` ·
`--motion-fast: 120ms` · reduced-motion fade `180ms`.

### Contract 7 — Design tokens
The `:root` block from `design-samples/app-shell.html` adopted **verbatim** as canonical names:
`--cream --cream-deep --paper --ink --ink-60 --ink-35 --hairline --hairline-soft --rasp
--rasp-08 --rasp-15 --maker --checker --ok --warn --mono --sans` — plus the motion tokens
(Contract 6) and `--radius-sm: 4px` / `--radius-md: 8px`.

## Identity & Motion (owner-locked)
- **Diecast light world:** cream `#F5F4F0`, ink `#1A1A28`, raspberry `#D6235C`, maker `#3B5BB0`, checker `#6B47B0`. **IBM Plex Mono** (400/500/600) + **DM Sans** (400/500/700) via Google Fonts `<link>`.
- **Motion register (locked, playbook 02):** morph ~350ms; speed > spectacle; motion *reveals layout*, never performs; everything non-morph ≤150ms ease-out; `prefers-reduced-motion` → sub-200ms fade. Centralized as CSS custom properties (Contract 6).

## Stack (owner-locked)
No build step · import maps · **htm + Preact** (CDN, <15KB gzipped) · one in-memory JSON state ·
`location.hash` routing · CSS View Transitions morph · ~50-line scenario engine · 5 typed ops
through one dispatcher. Pin exact CDN versions (e.g. `https://esm.sh/preact@10.26.2`,
`preact/hooks`, `htm@3/preact`) so a CDN bump can't break the demo mid-walkthrough. Include a
`driver.js` import-map entry now (usage deferred to Phase 6) so the <15KB budget stays honest.

## Codebase Conventions
- Components PascalCase (`AppShell`, `CanvasFrame`, `ChatRail`); ops camelCase verbs; tokens kebab-case; route grammar `#/area/id`.
- All app-state updates go through an explicit top-level `paint()` (synchronous Preact `render()`); **no component-local `useState` for app state** — this is what keeps the render synchronous inside `startViewTransition` (1.2/1.3 depend on it).
- Placeholder spine vocabulary carries `placeholder: true` in data **and** a visible `PLACEHOLDER` watermark when rendered (1.3) so screenshots can't be mistaken for Phase-2c-derived real vocabulary.

## Key File Paths
| Path | Role |
|------|------|
| `prototype/index.html` | The **only** deliverable file (built up across 1.1 → 1.2 → 1.3). |
| `goals/product-revamp-diecast/exploration/design-samples/app-shell.html` | Source of the canonical `:root` token block + layout reference. |
| `docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md` | The phase plan (authority for each sub-phase's content). |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Decisions ledger — 1.3 appends the morph-gate verdict here. |

## Relevant Specs
**No specs cover files in this plan.** Per the phase plan's Spec References table and FR-020:
the prototype is greenfield; all 7 specs in `docs/specs/_registry.md` govern the cast-server
runtime, none of which this prototype touches. No `/cast-update-spec` action this phase
(new product specs are downstream, post-prototype). Sub-phases create/modify only
`prototype/index.html` — a design artifact, not product behavior — so no spec-linked file is
touched.

## Sub-Phase Dependency Summary
| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 1.1 Skeleton (`sp1_skeleton/`) | Sub-phase | — | 1.2 | None (sequential) |
| 1.2 Nervous System (`sp2_nervous_system/`) | Sub-phase | 1.1 | 1.3 | None (sequential) |
| 1.3 Proof — Hero Morph & Gate (`sp3_proof/`) | Sub-phase | 1.2 | Phases 2a/2b/2c (morph verdict) | None (sequential) |

**Strictly sequential — no parallel group, no `gate_*` file.** The morph decision gate lives
*inside* 1.3 and is resolved autonomously via the pre-written 5-item checklist (Contract: full
autonomy). All three sub-phases edit the same single file (`prototype/index.html`) in order,
which is exactly why they cannot run in parallel.
