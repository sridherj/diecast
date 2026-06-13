# Execution Manifest: Product Revamp: Diecast — Phase 2b (Component Kit & Aesthetic Lock)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in the repo root (`/home/sridherj/workspace/diecast`, which resolves to
   `/data/workspace/diecast`).
2. Tell Claude: "Read `docs/execution/product-revamp-diecast-phase2b-component-kit/_shared_context.md`
   then execute `docs/execution/product-revamp-diecast-phase2b-component-kit/spN_<name>/plan.md`."
3. After completion, update the Status column below and append to the Progress Log.

Source plan: `docs/plan/2026-06-11-product-revamp-diecast-phase2b-component-kit.md`.
Decisions ledger (2b.3 appends the aesthetic-lock record here):
`docs/plan/product-revamp-diecast-decisions-so-far.md`.

**Run mode: FULL AUTONOMY (owner-approved).** No user questions, no approval gates, no idle waits.
At decision points pick the recommended option and document it. **Propagate the directive verbatim
to any child** (2b.3's slop-gate checker delegations inherit it).

**Binding constraints (full text in `_shared_context.md`):**
- **C1 — NO TESTS** anywhere: no test files, suites, harnesses, or CI. Verification is manual click-through only (open `prototype/index.html` from disk in Chrome, observe). No review may flag missing tests.
- **C2 — file:// legality.** No `fetch()`, no local ES-module imports; only https CDN import-map imports, classic `<script src>`, relative `<img>`.
- **C3 — Single-file packaging.** All 2b components live inline in `prototype/index.html` (Phase 1 is BUILT — never regress Phase 1 contracts).
- **C4 — Parallel with Phase 2a.** Build against inline `FIXTURES` stubs matching `appState` v1; wire to `window.ORG` when 2a's `org.js` lands (a data-source swap, not a reshape).
- **C5 — Failure policy.** Retry a failed sub-phase once with refined instructions; second failure **off** critical path → log the gap and continue; second failure **on** critical path (**2b.1, 2b.3**) → **stop and report**.
- **C6 — Code root** `prototype/`; execution artifacts under `docs/execution/`.
- **C7 — No `cast-plan-review` dispatch** (run config: skipped, owner-approved).

## Sub-Phase Overview

| #     | Sub-phase                                                       | Directory/File             | Depends On       | Group | Critical | Status      | Notes |
|-------|-----------------------------------------------------------------|----------------------------|------------------|-------|----------|-------------|-------|
| 2b.1  | Grammar — Kit Harness, Avatar Grammar & the Guide's Character   | `sp1_grammar/`             | Phase 1 (built)  | 1     | **Yes**  | Done | Adds `#/kit` route + `FIXTURES` + `Avatar` primitive (circle/square/diamond) + `ColleagueCard` (both densities, one fn) + token extensions; picks the Guide treatment from 3 rendered candidates. Foundation everything else reuses. **Guide = A (diamond) kept, B/C deleted.** Static-verified (node --check + greps PASS); P1 flash-test + P2 optical-balance PROVISIONAL pending human eyeball (browser not connectable). |
| 2b.2a | Shape & Proof — Stage-Spine Variants + the EvidenceBlock Family | `sp2a_spines_evidence/`    | 2b.1             | 2     | No       | Done | `StageSpine` (4 shapes: segments/loop/timebox/pipeline, one fn switched on `spine.shape`) + `EvidenceBlock` (E1–E5, one fn + per-kind sub-renderers; every block carries a confidence/flag signal, no bare green badge; unknown-kind → visible fallback + `console.warn`). Goal-canvas spine zone swapped to `StageSpine` (wrapper byte-identical). Static-verified (node --check; vt-anchors unchanged 5×1; fetch/local-import/raw-hex clean; spine-/ev- prefixes). **Morph-gate static re-check PASS** (anchor uniqueness + wrapper identity + 350ms register intact). **PROVISIONAL (browser not connectable):** four-silhouette squint test + live morph crossfade fidelity + evidence visual taste — human-eyeball carry-forward. |
| 2b.2b | Judgment — Decision Ladder, Nudge Card, Escalation Rail & Dial  | `sp2b_judgment/`           | 2b.1             | 2     | No       | Done | `Decision` ladder (6A pill / 6B callout / 6C trail row, ONE component + `layer` prop, all three from one atom, DEC- id rendered in every layer) + `NudgeCard` (3B, ink-filled primary do-line + always-present why-line + ◈ GuideMark) + `EscalationRail` (7A, three rank-weighted `<button>` options A hero/B outline/C ghost, **nothing pre-selected**, focus order A→B→C, policy line) + `AutonomyDial` (8A static, 3 positions + plain-language legend + L-threshold legend + earned-trust stat). Goal-canvas nudge stub swapped to `NudgeCard` (`.nudge` ZONE WRAPPER keeps `vt-nudge-card`; anchor on wrapper not component — Contract 9). Decision-atom fixtures on Contract-3 field names **VERBATIM** (+ a superseded record proving the 6C strike-through/`superseded_by` link + an `awaiting_human` record for the non-animated error tag). Static-verified (`node --check` PASS; vt-anchors **unchanged 5×1**; `fetch()`/local-import/external-`<img>` all 0; no new raw hex; all 16 contract-3 fields grep-present; raspberry confined to rail hero + L3 badge mapping + dial L3 legend + error fallbacks; rail options are `<button>`s; popover has `aria-expanded`). **PROVISIONAL (browser not connectable, autonomous run):** 6B popover open/Esc-close + focus order A→B→C live behaviour, the nudge-zone morph crossfade fidelity, and decision/rail/dial visual taste at the Steve-Jobs bar — human-eyeball carry-forward. 2b.3 now unblocked. |
| 2b.3  | Aesthetic Lock — Signature Screen & the Slop Gate               | `sp3_aesthetic_lock/`      | 2b.2a **and** 2b.2b | 3  | **Yes**  | Done | **AESTHETIC LOCKED.** `#/goal/CAST-412` composed entirely from the kit (GuideMark · StageSpine · NudgeCard · 3× 4B ColleagueCard · E1 EvidenceBlock · 6A Decision pills); zero Phase-1 stub markup; GoalCanvas = data slice + component calls. 4C card dropped on `#/board` (same FIXTURES.CO object → density-drift clean). Guide voice reconciled to hue-free (checker-purple removed; diamond + left-rule carry identity). **Slop gate (PROVISIONAL, static source review — no browser):** visual `not-generic` PASS + `not-ai-aesthetic` PASS (borderline on Phase-1 `.opbtn`, logged); tone FLAGGED→**CLEAN** after 3 em-dash fixes + re-run. Token grep clean (last raw-hex `#fff` swept, `.next-btn`→`var(--paper)`); morph gate static re-check PASS (vt 5×1, 350ms register, demo walks end-to-end, `node --check` PASS). Human-eyeball carry-forwards: re-run gate on a real 1440px screenshot + Guide flash test + de-em-dash ORG/Phase-1 runtime copy. |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision-gate (`gate_*`) files.** The phase's only externalized judgment — the slop-gate
verdict in 2b.3 — comes from the **checker agents** (`/cast-preso-check-visual` +
`/cast-preso-check-tone`), dispatched *inside* 2b.3 under FULL AUTONOMY. It is not modeled as a
separate human `G`-node. A "fail" verdict is a successful recorded outcome that triggers the
in-2b.3 rework-and-re-run loop — not a sub-phase failure. A borderline pass is logged to
`borderline-calls.md`.

## Dependency Graph

```
                 ┌──▶ 2b.2a (spines + evidence) ──┐
2b.1 (grammar) ──┤                                 ├──▶ 2b.3 (signature screen + slop gate) ──▶ Phase 3 consumes kit
 (harness,       └──▶ 2b.2b (decision/nudge/      ─┘     (aesthetic lock; SC-004 de-risked)
  avatar, Guide)        rail/dial)
```

**Group resolution (for the orchestrator):**
- **Group 1** = `{2b.1}` — runs first; foundation (Avatar/tokens/harness/`FIXTURES`/`ColleagueCard`) every later component reuses.
- **Group 2** = `{2b.2a, 2b.2b}` — **PARALLEL-CAPABLE**; both depend only on 2b.1, touch disjoint component sets, and partition `index.html` by banner section to avoid merge friction. Dispatch as two concurrent sessions/agents, or run serially if single-threaded.
- **Group 3** = `{2b.3}` — depends on **both** members of Group 2; cannot start until 2b.2a and 2b.2b are both Done.

## Execution Order

### Group 1 (foundation — must complete first)
2b.1 **sp1_grammar** — `#/kit` renders every component slot from inline `FIXTURES` with a clean
console from `file://`; `Avatar` primitive (circle/square/diamond); `ColleagueCard` both
densities from one fixture, zero field drift; the Guide's character chosen from 3 rendered
candidates at the Steve-Jobs bar; token extensions (contract #7) added. **Critical path.**

### Group 2 (after 2b.1 — the two run in PARALLEL)
2b.2a **sp2a_spines_evidence** — `StageSpine` renders all four shapes (segments / loop+iter /
timebox meter / pipeline DAG) as materially different silhouettes; `EvidenceBlock` renders all
five treatments (E1–E5) with a confidence/flag signal on every one (no bare green badge); the
goal-canvas spine zone swaps to `StageSpine` and **re-passes the Phase 1 morph gate**.

2b.2b **sp2b_judgment** — the `Decision` ladder renders 6A pill → 6B callout → 6C trail row from
**one** atom; `NudgeCard` (3B) renders `{who, do, why}` with Guide attribution and replaces the
goal-canvas stub; `EscalationRail` (7A) renders three ranked options with **nothing
pre-selected**; `AutonomyDial` (8A) renders three positions + teaching legend + earned-trust stat
line (static).

### Group 3 (after BOTH 2b.2a and 2b.2b)
2b.3 **sp3_aesthetic_lock** — compose `#/goal/CAST-412` entirely from kit components (zero Phase
1 stub markup remains); drop one 4C `ColleagueCard` on `#/board` for the density-drift check;
screenshot at 1440px → **delegate `/cast-preso-check-visual`** (verdict on `not-generic` /
`not-ai-aesthetic` only) + **`/cast-preso-check-tone`** (UI copy); rework until green; Guide
label-free distinctness flash test; token-discipline grep; append the aesthetic-lock record to
`decisions-so-far.md`. **Critical path — SC-004 de-risk.**

## Files Touched by More Than One Sub-Phase

As in Phase 1, **all four sub-phases build up the same single file** — forced by the file://
single-file constraint (C2/C3). Within Group 2 the two parallel sub-phases touch **disjoint
banner sections** of that file (2b.2a = spine/evidence sections; 2b.2b = decision/nudge/rail/dial
sections), which is what makes the parallelism safe — partition by banner comment, do not edit
the other's section.

| File | 2b.1 | 2b.2a | 2b.2b | 2b.3 | Owner notes |
|------|------|-------|-------|------|-------------|
| `prototype/index.html` | Modify | Modify | Modify | Modify | Additive: harness+Avatar+ColleagueCard+tokens → (spines+evidence ∥ decision/nudge/rail/dial) → signature-screen composition. 2b.2a/2b.2b partition by banner section; 2b.3 wires the goal canvas zone-by-zone. Never regress a Phase 1 contract. |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Append (Guide pick + deviations) | — | — | Append (aesthetic-lock record) | 2b.1 records the chosen Guide treatment + any sample deviations; 2b.3 records the lock + checker verdicts. |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | — | — | — | Append (conditional) | 2b.3 only, **only if** a slop-gate verdict is a borderline pass. |

## Out-of-Manifest (intentionally NO sub-phase, NO gate file)

- **A separate human decision-gate (`gate_*` / `G`-node)** → not modeled. FULL AUTONOMY resolves the slop-gate verdict inside 2b.3 via the checker delegations.
- **Real canvases / real per-family vocabulary / real org data** → Phases 3 / 2c / 2a (HOLD SCOPE). 2b builds components against `FIXTURES` and placeholder spine vocabulary only.
- **Board / ticket / marketplace surfaces** → Phase 5 (which reuses the lockup, decision ladder, escalation rail, and dial built here).
- **`org.json` / data spine** → Phase 2a. 2b wires to `window.ORG` as a data-source swap when 2a lands (C4).
- **Any test file / harness / CI** → none, ever (Constraint C1).
- **`/cast-update-spec` or a new `docs/specs/` entry** → none this phase. Greenfield design artifact; no spec applies (FR-020).
- **`/cast-plan-review` auto-dispatch** → skipped per the run config (owner-approved, Constraint C7).

## Progress Log

<!-- Update after each sub-phase completes. -->
- **2b.1 (sp1_grammar) — DONE** (2026-06-12, run_20260611_221313_b4091e). Built additively into
  `prototype/index.html` (Phase 1 untouched: appState v1, closed 5-op set, dispatcher/scenario
  engine, and all 5 vt- anchors verified unchanged). Added `#/kit` route (hash-only, hidden from
  nav), inline `FIXTURES` (canonical vocab + `CO_SOLO` broken-state stub), `Avatar` (4 kinds, one
  fn, optical sizing), `ColleagueCard` (card+line from one `slots` fragment — grep-confirmed single
  lockup), token extensions (Contract 7: `--fail`, L-badge `.lbadge--l1/l2/l3`, confidence glyphs),
  and the Guide character: **treatment A (diamond) KEPT, B + C deleted** (rubric + reasoning in
  `decisions-so-far.md`). Static verification PASS (`node --check`; grep-clean of `fetch()`/local
  imports; one ColleagueCard lockup; no vt- on kit components; only `--fail` raw hex added, in
  `:root`). **PROVISIONAL (browser not connectable, autonomous run):** P1 Guide label-free flash
  test + P2 optical avatar balance — carry-forward human-eyeball check noted. Group 2 (2b.2a ∥
  2b.2b) unblocked.
- **2b.2a (sp2a_spines_evidence) — DONE** (2026-06-12, run_20260611_223836_161cc7). Built additively
  into `prototype/index.html` in a `spine-*` / `ev-*` banner section (Phase 1 + 2b.1 regions
  untouched; only the goal-canvas spine-zone **inner content** was swapped, wrapper kept
  byte-identical). Added: `StageSpine({spine})` — one fn, four-way `spine.shape` switch yielding four
  materially-different silhouettes (`segments` bar / `loop` band+`↺ iter` / `timebox` single meter,
  deliberately lighter / `pipeline` node chain), each PLACEHOLDER-watermarked; `EvidenceBlock({kind,
  data})` — one fn + five sub-renderers (E1 acceptance panel w/ hand-drawn SVG screenshot thumbs +
  checker rows reusing the 2b.1 line-density `ColleagueCard` for attribution + flagged R02 signal ·
  E2 confirm/refute ledger, refuted rows struck-but-visible · E3 red→green repro, same test name ·
  E4 verdict card w/ H/M/L glyph + first-class `spike_ref` link · E5 hand-rolled inline-SVG bar chart
  + `<details>` provenance + dated version chip), **every block carries a confidence/flag signal, no
  bare green badge**; unknown `kind`/`shape` → visible fallback + `console.warn`, no throw. Spine +
  evidence `FIXTURES` (canonical vocab; `segments`/`loop` mirror `appState.spines` verbatim) and two
  `#/kit` gallery sections added. **Goal-canvas spine zone now renders through `StageSpine`** (Phase 1
  stub markup gone). Static verification PASS (`node --check`; vt-anchors **unchanged 5×1**;
  `fetch()`/local-import/external-`<img>` all 0; raw hex clean — new white text uses `var(--paper)`;
  `spine-*`/`ev-*` prefixes present; no edits to 2b.2b's decision/nudge/rail/dial sections).
  **Morph-gate static re-check PASS** (anchor uniqueness + `.spine-zone` wrapper identity + 350ms
  `::view-transition-group` register + reduced-motion guard all intact). **PROVISIONAL (browser not
  connectable, autonomous run):** four-silhouette squint test, the live feature→debug morph crossfade
  fidelity, and the E1–E5 visual treatments at the Steve-Jobs bar — human-eyeball carry-forward noted.
  2b.3 still blocked on 2b.2b.
- **2b.2b (sp2b_judgment) — DONE** (2026-06-12, run_20260611_224854_a38214). Built additively into
  `prototype/index.html` in a `dec-*` / `nudge-*` / `rail-*` / `dial-*` banner section (Phase 1 + 2b.1 +
  2b.2a regions untouched; only the goal-canvas **nudge zone** inner content was swapped — the `.nudge`
  zone wrapper kept its `vt-nudge-card` anchor, Contract 9). Added: `Decision({atom, layer})` — ONE
  component, three projections of ONE atom (6A inline pill `⚖ classification: feature → bug · L2` / 6B
  CSS-positioned popover, no portal lib, `aria-expanded` + Esc-to-close, ephemeral local UI state not
  appState / 6C diff-first trail row), the DEC- id rendered in **every** layer (ID-match verifiable);
  `NudgeCard({nudge})` — 3B, ink-filled primary do-line CTA (hue-neutral; raspberry reserved) +
  always-present subordinate why-line + `◈` GuideMark + `data-op="nudge:n2"`; `EscalationRail({escalation})`
  — 7A, header w/ L3 badge + `@you` route, evidence pack (what I want / what I tried), three
  rank-weighted `<button>` options (A hero accent-filled + RECOMMENDED tag / B outline / C ghost) each
  w/ a consequence line, **nothing pre-selected**, DOM order = focus order A→B→C, policy-provenance line;
  `AutonomyDial({value, trust})` — 8A static, 3-position segmented control (Balanced default) +
  plain-language legend + L-threshold teaching legend (L1 silent / L2 digest / **L3** stop, L3 via the
  rasp L-badge mapping) + earned-trust stat `ⓘ 99.4% compliance across 312 runs`. Decision-atom
  `FIXTURES.DECISIONS` on Contract-3 field names **VERBATIM** (`id · phase · title · reversibility ·
  rationale · options_considered[] · consequences · revisit_if · originating_agent · author_type ·
  timestamp · status · supersedes/superseded_by · spike_ref · influenced[]`; `diff` is a render hint, not
  a contract field): a primary L2 `Classify CAST-412 as bug, not feature` + a **superseded** record
  (`superseded_by → DEC-CAST-412-03`, proving the 6C strike-through + link) + an `awaiting_human` record
  (non-animated `awaiting` tag). `FIXTURES.ESCALATION` + `FIXTURES.AUTONOMY` added; two `#/kit` gallery
  sections added. **Goal-canvas nudge stub gone — now renders through `NudgeCard`.** Static verification
  PASS (`node --check`; vt-anchors **unchanged 5×1**; `fetch()`/local-import/external-`<img>` all 0; no new
  raw hex — token/rgba only; all 16 contract-3 fields grep-present; `dec-`/`nudge-`/`rail-`/`dial-`
  prefixes present; raspberry confined to rail hero + L3 badge mapping + dial L3 legend + error
  fallbacks; rail options are `<button>`s; callout has `aria-expanded`; no edits to 2b.2a's spine/evidence
  sections or the goal-canvas spine zone). **PROVISIONAL (browser not connectable, autonomous run):** the
  6B popover open/Esc-close + A→B→C focus order live behaviour, the nudge-zone morph crossfade fidelity,
  and the decision/rail/dial visual taste at the Steve-Jobs bar — human-eyeball carry-forward noted.
  **Group 2 complete (2b.2a ∥ 2b.2b both Done) → 2b.3 (aesthetic lock) is now unblocked.**
- **2b.3 (sp3_aesthetic_lock) — DONE** (2026-06-12, run_20260611_230342_b92fb0). **THE AESTHETIC IS LOCKED**
  (de-risks SC-004 before Phase 3). Composed the signature `#/goal/CAST-412` canvas **entirely from kit
  components** (zero Phase-1 stub markup remains; `GoalCanvas` is now a data slice + component calls): guide-line →
  `GuideMark` (locked diamond + real ORG-derived narration) · spine → `StageSpine` · nudge → `NudgeCard` · In-flight
  work → 3-row **4B line-density `ColleagueCard`** stream (`FIXTURES.CO`/`.CC`/`.YOU`) · Stage artifacts → one **E1
  `EvidenceBlock`** · receipt-trail → **6A `Decision` pills** (receipt `{decision_id,label,level}` → pill
  `{id,diff,reversibility}`). Dropped one **4C `ColleagueCard`** on `#/board` from the **same `FIXTURES.CO` object**
  (density-drift clean). Reconciled the Guide voice to **hue-free** (removed the residual checker-purple `◈` in the
  chat header + guide attribution; ink left-rule on `.msg.guide`; identity = shape + structure, never color). Body
  Part-2 restructured `1fr·1fr` grid → single stacked column (E1 needs full width — recorded deviation). Swept dead
  Phase-1 CSS (`.loop*`/`.seg`/`.ph-mark`/`.receipt`/`.work-item`/`.guide-mark`/`.chat-h .gmark`) which also removed
  the last **raw-hex `#fff`**; `.next-btn` → `var(--paper)`. **Slop gate (PROVISIONAL — static source review of the
  rendered component HTML/CSS, no browser in autonomous runs):** `/cast-preso-check-visual` → `not-generic` **PASS** +
  `not-ai-aesthetic` **PASS** (borderline on the Phase-1 chat `.opbtn` ghost-pill — within tokens, no rework; logged
  to `borderline-calls.md`); `/cast-preso-check-tone` → first pass **FLAGGED** 3 on-screen em-dashes → reworked
  (sentence split + the UI's `·` middot, no literal `--`) → re-run **CLEAN**. Static verification PASS (`node --check`
  of the extracted module; vt- anchors **unchanged 5×1**; `::view-transition-group(*)` 350ms register + reduced-motion
  guard intact; `fetch()`/local-import/external-`<img>` all 0 real; no raw hex outside `:root`; closed 5-op set +
  `advance()` whole — demo walks end-to-end by inspection). **Concurrency:** composed against the post-`2a.3`
  ORG-wired `index.html`; FIXTURES-sourced zones are the sanctioned C4 `#/kit` exception (real per-goal
  `work_stream` renderer is Phase 3). **Human-eyeball carry-forwards (never block):** re-run BOTH checkers on a real
  1440px screenshot; Guide label-free flash test on the rendered screen; de-em-dash the ORG `nudge.why` + Phase-1
  chat-script runtime copy (2a/Phase-1-owned, not assessed by the tone pass). **Phase 2b COMPLETE — Phase 3 may
  consume the kit.**
