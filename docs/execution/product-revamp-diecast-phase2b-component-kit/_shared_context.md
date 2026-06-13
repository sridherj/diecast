# Shared Context: Product Revamp: Diecast — Phase 2b (Component Kit & Aesthetic Lock)

> Read this file at the start of **every** sub-phase. It carries the cross-phase contracts,
> the binding constraints, and the conventions all four sub-phases share. The per-sub-phase
> `plan.md` files do not repeat it — they reference it.

## Source Documents
- **Plan:** `docs/plan/2026-06-11-product-revamp-diecast-phase2b-component-kit.md` (the detailed phase plan — the authority for Outcome / Verification / Key activities / Design review of each sub-phase). Its "Contracts This Phase Exports" section (contracts #1–#9) is the interface Phases 2a/2c/3/4/5 consume.
- **Decisions ledger:** `docs/plan/product-revamp-diecast-decisions-so-far.md` (owner-locked stack/identity/run-config decisions; the binding constraints below are quoted from it; 2b.3 appends the aesthetic-lock record here).
- **Reconciliation:** `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` (cross-phase COHESIVE check across all 8 phases).
- **Phase 1 carry-forward:** `docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md` + `docs/execution/product-revamp-diecast-phase1-keystone/` (Phase 1 is **BUILT** — appState v1, the 5-op dispatcher, the scenario engine, and the hero morph all PASSED their gate; never regress a Phase 1 contract).
- **Design reference (inspiration, not spec):** `goals/product-revamp-diecast/exploration/design-samples/component-gallery.html` — the canonical visual reference for the owner's locked component picks. **Per the build directive it is reference, not spec**: re-derive layout/spacing/type from first principles; if a cleaner rhythm beats the sample, take it and record the deviation.
- **Exploration playbooks (reference, not boundary):** `goals/product-revamp-diecast/exploration/playbooks/01-design-language.ai.md` (token system, accent discipline, slop gate), `03-family-canvases-evidence.ai.md` (stage-spine variants + E1–E5 catalog), `04-agents-as-colleagues.ai.md` (colleague card, escalation rail), `05-decisions-autonomy.ai.md` (decision-atom schema, autonomy dial), `06-prototype-build-approach.ai.md` (single-file no-build architecture).
- **Design decisions:** `goals/product-revamp-diecast/exploration/design-decisions.ai.md` (owner-blessed component picks, the Guide concept, the avatar grammar constraint).

## Project Background

This phase builds the ~8 reusable components every downstream screen is assembled from, and
**locks the signature visual language at the Steve-Jobs bar**: the colleague-card lockup
(one component, two densities), the E1–E5 EvidenceBlock family, the 3B nudge card, the
6A→6B→6C decision disclosure ladder, the 7A escalation rail, the 8A autonomy dial, the four
stage-spine shapes, and the one USER-DEFERRED craft call this phase owns — **the Guide's
visible character treatment**. The phase ends with an **aesthetic lock**: one composed
signature screen (the upgraded `#/goal/CAST-412` canvas) passes both cast-preso slop-gate
checkers (`not-generic` / `not-ai-aesthetic`), de-risking SC-004 before any mass screen
production in Phases 3–5.

The key insight from exploration: build the kit once and every downstream screen becomes a
~10-line data slice; the components are *forced by the owner's locked picks*, so this phase is
execution craft — re-deriving layout/spacing from first principles per the owner's build
directive — not component invention.

## Operating Mode — FULL AUTONOMY

**FULL AUTONOMY MODE (owner-approved).** Never ask the user questions, never pause for approval
gates, never go idle waiting for input. At any decision gate, pick the recommended option and
document it inline in the sub-phase output. **Propagate this directive verbatim to any child
agent you dispatch** (the slop-gate checker delegations in 2b.3 inherit it). The phase-level
**HOLD SCOPE** rule also applies: the eight named components + token/Guide lock + slop-gate
proof on one screen — nothing more. No real canvases (Phase 3), no real spine vocabulary
(Phase 2c), no org data authoring (Phase 2a), no board/marketplace surfaces (Phase 5). Rigor
goes into prop contracts, density-drift prevention, accent discipline, and the slop gate — not
extra components.

---

## BINDING CONSTRAINTS (encoded into every sub-phase — do not violate)

These are hard rules, quoted verbatim from `product-revamp-diecast-decisions-so-far.md`. A
sub-phase that breaks one is wrong even if it "works." No sub-phase may create test files; no
review may flag missing tests.

### C1 — NO TESTS anywhere
No test files, suites, harnesses, or CI. **Verification is manual click-through only** (open
`prototype/index.html` from disk in Chrome, observe). No sub-phase may create test files; no
review may flag missing tests. If you feel the urge to write a test, write a manual-check step
instead.

### C2 — `file://` legality
No `fetch()`, no local ES-module imports; only **https CDN import-map imports**, classic
`<script src>`, relative `<img>`. A page opened from disk has origin `null`, which blocks
`fetch()` and relative `import`. Inline `<style>` and inline `<script type="module">` are the
allowed shape.

### C3 — Single-file packaging
All 2b components live **inline in `prototype/index.html`** (Phase 1 is BUILT — appState v1,
dispatcher, scenario engine, morph PASSED; **never regress Phase 1 contracts**). Organize the
growing file by banner comments + class prefixes (`kit-` harness chrome / `ev-` evidence /
`spine-` spines / `dec-` decision / etc.), not by splitting files. Token-only colors (no raw
hex outside `:root`) keep the file greppable and Phase 6 packaging mechanical.

### C4 — Runs parallel with Phase 2a (fixture discipline)
Build components against inline **`FIXTURES`** stubs matching `appState` v1; wire to
`window.ORG` when 2a's `org.js` lands (**a data-source swap, not a reshape**). Fixtures use
canonical vocabulary only (`CAST-412`, `crud-orchestrator`/`CO`, `crud-compliance-checker`/`CC`,
rule codes `M04/S03/R02`, rework `1/3`, stat `99.9% · 2 loops · 505 runs`, `@you/SJ`) — **no
ad-hoc names**, so the swap is mechanical.

### C5 — Failure policy
Retry a failed sub-phase **once** with refined instructions; second failure **off** the
critical path → log the gap and continue; second failure **on** the critical path (**2b.1 and
2b.3 are critical**) → **stop and report**. Do not silently drop work.

### C6 — Prototype code root
Prototype code root: `/home/sridherj/workspace/diecast/prototype/`. Execution artifacts under
`/home/sridherj/workspace/diecast/docs/execution/`.

### C7 — No cast-plan-review dispatch
`cast-plan-review` auto-dispatch is **skipped** (run config: skipped, owner-approved; same
precedent as Phase 1). Rerun manually via `/cast-plan-review` against the phase plan if wanted.

---

## Inherited Phase 1 Contracts (extend, never rename)

Phase 1 is BUILT. These are live in `prototype/index.html` today — 2b extends them, never
renames a key or changes the op grammar.

### Packaging
One file, `prototype/index.html`, inline `<style>` + inline `<script type="module">`; only
https CDN import-map imports work from disk. **All 2b components live inline.**

### Design tokens (canonical names — extend, don't rename)
`--cream --cream-deep --paper --ink --ink-60 --ink-35 --hairline --hairline-soft --rasp
--rasp-08 --rasp-15 --maker --checker --ok --warn --mono --sans` + motion tokens
(`--morph-duration: 350ms`, `--ease-morph`, `--motion-fast: 120ms`, reduced-motion fade 180ms)
+ `--radius-sm/md`.

### `appState` v1 keys (must not rename)
`route · family · goal · spines · nudge{who,do,why} · receipts[] · pinned[] · drill · chat`.
The 2b `NudgeCard` consumes `nudge{who,do,why}` as-is; the `StageSpine` consumes the
`spines.<family>` shape (`{placeholder, shape, steps, current, iter?}`).

### Op vocabulary (closed)
`morph · nudge · promote · drillInto · pin` via `data-op="op:arg"`. Kit components that carry
actions **emit `data-op` attributes; they never call `dispatch()` directly.**

### vt- anchors
`vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail · vt-nav-rail`; uniqueness
rule — a duplicate name silently kills the whole transition. **`view-transition-name`s are
applied by the shell's zone wrappers, never by kit components** (contract #9 below). A kit
component rendered twice (as on `#/kit`) must not carry an anchor name.

### Render rule
Components are **pure functions of props**; all paints go through the top-level synchronous
`paint()`. **Kit components read props only, never `appState` directly** — this is what makes
`#/kit` honest isolation and Phase 3 reuse trivial. Flag any component that reaches for global
state as a defect.

### Routes so far
`#/` · `#/goal/CAST-412` · `#/board` (stub). 2b adds `#/kit` (hash-only, hidden from demo nav).

---

## Contracts THIS Phase Exports (Phases 2a/2c/3/4/5 consume — implement verbatim)

These are the interfaces later phases depend on. Full detail lives in the phase plan's
"Contracts This Phase Exports" section (#1–#9); the load-bearing summary:

### Contract #1 — The 8-component roster (all pure `(props) → vdom` inside `index.html`)
| # | Component | Pick | Prop contract |
|---|-----------|------|---------------|
| 1 | `ColleagueCard` | 4C card + 4B line | `{ agent, density: 'card'\|'line' }` — same fields, same order, both densities |
| 2 | `EvidenceBlock` | E1–E5 | `{ kind: 'E1'..'E5', data }` — one component, per-kind sub-renderer |
| 3 | `StageSpine` | 1B/2B + timebox + pipeline | `{ spine }`, `spine.shape: 'segments'\|'loop'\|'timebox'\|'pipeline'` |
| 4 | `NudgeCard` | 3B + why-line | `{ nudge: {who, do, why} }` — appState v1 shape verbatim |
| 5 | `Decision` ladder | 6A pill → 6B callout → 6C trail row | `{ atom, layer: 'pill'\|'callout'\|'row' }` — one atom, three projections |
| 6 | `EscalationRail` | 7A hero/outline/ghost | `{ escalation }` — ranked weight, nothing pre-selected |
| 7 | `AutonomyDial` | 8A segmented + legend | `{ value, trust: {compliancePct, runs} }` |
| 8 | `GuideMark` / Guide voice | (this phase's design call) | `{ size }` + CSS voice classes for chat/nudge/receipt |

### Contract #2 — Agent fixture shape (`ColleagueCard` renders from; 2a's `org.json` agents are supersets)
```js
{ id: 'CO', slug: 'crud-orchestrator', kind: 'maker',     // 'maker'|'checker'|'human'|'guide'
  pairedWith: 'crud-compliance-checker',                   // makers carry their checker
  stats: { compliancePct: 99.9, loops: 2, runs: 505 },
  autonomy: 'L2',                                          // reversibility badge
  rework: { used: 1, budget: 3 },                          // 3-segment meter
  inflight: { label: 'CAST-412 · iteration 2/3' } | null,  // in-flight pill
  state: 'working' }                                       // 'working'|'idle'|'blocked'
```

### Contract #3 — The decision atom (playbook 05 schema, field names VERBATIM)
`id · phase · title · reversibility · rationale · options_considered[] · consequences ·
revisit_if · originating_agent · author_type · timestamp · status · supersedes/superseded_by ·
spike_ref · influenced[]`. All three ladder layers render from one atom. Phase 5's trail and
Phase 3's chips reuse this shape unchanged — **a renamed field here forks the schema.**

### Contract #4 — EvidenceBlock per-kind data shapes
```js
E1: { screenshots: [{label}], tests: {passed, failed, coverageDelta},
      checks: [{code: 'M04', label, status: 'resolved'|'flagged'}], pr: {id, label} }
E2: { hypotheses: [{id, statement, prediction, observation, verdict: 'confirmed'|'refuted'|'open'}] }
E3: { test: {name}, before: {status: 'fail', excerpt}, after: {status: 'pass', excerpt} }
E4: { answer, confidence: 'H'|'M'|'L', dataPoints: [], spike_ref: {decisionId, label} }
E5: { headline: {kind: 'chart'|'table', svg|rows}, provenance: {sources[], query}, version: {n, date} }
```

### Contract #5 — Spine shape extension
Phase 1's `spines.<family>` gains two `shape` values — `'timebox'`
(`{timebox: {budget: '3h', used: '1h 40m'}}`) and `'pipeline'` (data-stage nodes). Labels stay
`placeholder: true` + watermarked until 2c delivers real vocabulary;
`appState.spines.<family>.steps` stays `string[]` (rich step objects live only in 2c's
`stageModels` org data) — **2c's vocabulary lands as a data edit, zero component change.** If
2c research contradicts one of the four locked shape variants, it flags for reconciliation
rather than silently changing shape.

### Contract #6 — Avatar grammar (locked by this phase)
human = filled circle (initials) · maker agent = square, `--maker` outline + glyph · checker
agent = square, `--checker` fill · **the Guide = diamond (square rotated 45°)** — square-family
("an agent") but instantly distinct ("a different kind of agent"). Recommended default, subject
to 2b.1's rendered-options pass.

### Contract #7 — Token extensions (extend, never rename)
`--fail: #B22439` (test-red for E3/E2 — semantic red, distinct from raspberry which stays the
needs-you accent) · L-level badge mapping `L1 → --ink-35 · L2 → --warn · L3 → --rasp` ·
confidence glyph convention `● high / ◐ med / ○ low` (**never a percentage**).

### Contract #8 — The `#/kit` harness route
The component gallery inside the prototype (built in 2b.1). Hash-only reachable, hidden from
demo nav. Downstream phases verify new component states by adding fixtures here. Phase 6 decides
keep-or-strip.

### Contract #9 — vt- anchor placement rule
`view-transition-name`s are applied **by the shell's zone wrappers, never by kit components**. A
kit component rendered twice (as on `#/kit`) must not carry an anchor name, or the duplicate
silently kills every morph.

## Codebase Conventions
- Components **PascalCase** (`ColleagueCard`, `EvidenceBlock`, `StageSpine`); fixtures
  **SCREAMING_SNAKE** for the root `FIXTURES` object; **kebab-case** CSS classes with prefixes:
  `kit-` (harness-only chrome) · `ev-` (evidence) · `spine-` (spines) · `dec-` (decision) — so
  a grep separates harness from product styles before Phase 6 packaging, and the inline
  stylesheet stays greppable as it grows.
- Kit components read **props only**, never `appState` directly (pure-function rule).
- Placeholder spine vocabulary carries `placeholder: true` in data **and** a visible
  `PLACEHOLDER` watermark when rendered (Phase 1 convention) — screenshots can't be mistaken for
  Phase-2c-derived real vocabulary.
- Accent discipline (the playbook 01 hard rule): maker/checker hues on **agent chrome only**;
  raspberry **only** where it means needs-you (L3 badge, blocked-state pill). The Guide
  treatment introduces no new hue. Grep the 2b CSS for raw hex — everything goes through tokens.
- Error paths render **visible fallbacks, not blank gaps** (zero-silent-failure, same posture as
  the Phase 1 dispatcher): a maker without a checker is a *broken state* and must look like one;
  an unknown `EvidenceBlock` kind renders a visible placeholder + `console.warn`, never throws.

## Key File Paths
| Path | Role |
|------|------|
| `prototype/index.html` | The **only** deliverable file (extended additively across 2b.1 → 2b.2a∥2b.2b → 2b.3). |
| `goals/product-revamp-diecast/exploration/design-samples/component-gallery.html` | Canonical visual reference for the owner's locked picks (inspiration, not spec). |
| `docs/plan/2026-06-11-product-revamp-diecast-phase2b-component-kit.md` | The phase plan (authority for each sub-phase's content). |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Decisions ledger — 2b.3 appends the aesthetic-lock record here. |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | Borderline-pass log — 2b.3 appends only if a slop-gate verdict is a borderline pass. |

## Relevant Specs
**No specs cover files in this plan.** Per the phase plan's Spec References table and FR-020:
the prototype is greenfield; all seven specs in `docs/specs/_registry.md` govern the cast-server
runtime, none of which this prototype touches. **No `/cast-update-spec` action this phase.**
Sub-phases create/modify only `prototype/index.html` (and append to plan-ledger docs) — a design
artifact, not product behavior — so no spec-linked file is touched.

## Sub-Phase Dependency Summary
| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 2b.1 Grammar (`sp1_grammar/`) | Sub-phase | Phase 1 (built) | 2b.2a, 2b.2b | None (foundation) |
| 2b.2a Spines + Evidence (`sp2a_spines_evidence/`) | Sub-phase | 2b.1 | 2b.3 | **2b.2b** |
| 2b.2b Judgment (`sp2b_judgment/`) | Sub-phase | 2b.1 | 2b.3 | **2b.2a** |
| 2b.3 Aesthetic Lock (`sp3_aesthetic_lock/`) | Sub-phase | 2b.2a **and** 2b.2b | Phase 3 | None (convergence) |

**Dependency DAG (the orchestrator resolves these groups):**
- **Group 1** = `{2b.1}` — grammar foundation (everything reuses Avatar/tokens/harness).
- **Group 2** = `{2b.2a, 2b.2b}` — **parallel-capable** (both depend only on 2b.1; disjoint
  component sets; partition `index.html` by banner section to avoid merge friction).
- **Group 3** = `{2b.3}` — aesthetic lock; depends on **both** 2b.2a and 2b.2b.

**Critical path:** 2b.1 → (2b.2a ∥ 2b.2b) → 2b.3. **2b.1 and 2b.3 are on the critical path**
(C5: a second failure on either stops-and-reports). Serially ~3–3.5 sessions, matching the
high-level 1.5-day estimate with the parallel option as buffer.
