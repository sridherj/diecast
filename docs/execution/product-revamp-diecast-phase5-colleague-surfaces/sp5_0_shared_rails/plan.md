# Sub-phase 5.0: Shared Rails — ORG Extension, Route Skeleton & the Digest Atom

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase5-colleague-surfaces/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

All data and plumbing the three sub-streams need exists, so **5a/5b/5c can run fully in parallel
with zero shared-file contention beyond their own route renderers**: the single ORG generator batch
has landed and re-validated, all ten Phase 5 routes resolve to labeled stubs, the new appState keys
exist, and `DigestNotice` renders from props. This sub-phase is the **root of the critical path**
(5.0 → 5b → 5.4) — nothing downstream can start until it lands.

## Dependencies
- **Requires completed:** Phases 1, 2a, 2b (3's `IterationPanel` is needed only from 5a onward; 5.0
  itself doesn't use it). Phase 4 is complete in the working tree — its generator batch already
  committed `org.js`, so 5.0's batch layers additively on top (Reconciliation F3).
- **Assumed codebase state:** `prototype/index.html` carries the Phase 1–4 canvases (feature, debug,
  spike, data), the full kit, the closed 5-op dispatcher, the 6×1 vt- anchor set, and
  `SCRIPTS = {feature, debug, spike, data}`. `prototype/data/org.js` carries the frozen 2a spine +
  2c vocabulary + the Phase 4 additive keys. The `#/board` route is still the Phase 1 **stub**.

## Estimated effort
0.5 session (~1.5h).

## Scope
**In scope:**
- The one generator-extension batch (four additive payloads + new gate invariants).
- The ten Phase 5 route stubs in the router + the nav-rail entries `Board · Hire · Layer-2`.
- The four additive appState keys initialized in the state literal.
- The `DigestNotice` component (pure props) + its `#/kit` fixture render.

**Out of scope (do NOT do these):**
- Any real board/ticket/decision/trail rendering (5a), hiring/marketplace/ops/Layer-2 surfaces (5b),
  or reqs-doc rendering (5c) — 5.0 ships **labeled stubs only** for the new routes.
- The `RadarChart` / `Sparkline` helpers (authored in 5b where first used; 5.0 ships only their data).
- Any hand-edit of `org.js`; any new op; any test file/suite/harness.
- **Any touch of the CAST-452/CAST-461 ORG sections or the Phase 4 canvas/parity `index.html`
  sections** (Phase 4 ownership — byte-identical guard).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/generate-org.mjs` | Modify | Seeded self-validating generator; **5.0 is the sole Phase-5 owner** |
| `prototype/data/org.js` | Regenerate (never hand-edit) | Frozen `window.ORG`; gains the four additive payloads |
| `prototype/index.html` | Modify | Phase-1–4 prototype; gains the ten route stubs + nav entries + appState keys + `DigestNotice` |

## Detailed Steps / Key Activities

### Step 5.0.1: The single generator-extension batch
Extend `generate-org.mjs` (seed 42, output committed; **never hand-edit `org.js`**) with four
additive payloads:

- **(a) `goals['CAST-412'].requirements_doc`** =
  `{ classification:'feature', version:'v2', version_history:[{v:'v1', date}, {v:'v2', date,
  summary}], elements:[{id:'req-NN', level:1|2|3, kind:'intent'|'story'|'fr'|'constraint', text,
  children:[ids], decision_refs:[atomIds]}], comments:[{id, anchor:'req-NN', author_id,
  author_role:'pm'|'eng', state:'open'|'resolved', thread:[{who, text, time}]}], delta:[{anchor:'req-NN',
  change, origin_phase:'planning'}], writeback:{origin_phase:'planning', summary, anchors:['req-NN']} }`
  — content derived from the CAST-412 RBAC story; **exactly ONE comment thread**, with one PM
  commenter (the single PM-framed moment; the PM persona comes from `ORG.humans`).
- **(b) Agent-ops fields on `agents[]`:** `versions:[{sha7, date, note}]` (**≥1 per agent**; 4–5
  entries on crud-orchestrator, 1–2 elsewhere) and `monitoring:{trend:[12 floats], cost_p50_usd,
  latency_p50_s, recent_runs:[{id, when, status}]}` (full depth on crud-orchestrator, thin elsewhere).
  **All credibility numbers remain derived from the same `stats` fields** (single source — no second
  copy of 99.9 / 505).
- **(c) `org.skills:[{slug, title, visibility:'private'|'company', owner, created, blurb}]`** — 3
  company-wide skills + the pre-staged demo skill `cast-export-csv` (`private`). **Nested under the
  existing `org` key** because top-level ORG keys are frozen (Decision 9).
- **(d) `dial_demo:true` marker** on exactly one CAST-412 **L2** atom (the planning-phase
  "split FR-014"-style atom from 2a's set) — the atom the dial toggle visibly promotes.

**New invariants (generator refuses to emit on violation):**
- exactly one `dial_demo` atom org-wide and it is **L2**;
- `requirements_doc` element ids unique; every comment / delta / writeback anchor resolves to an
  element; **exactly one** comment author has role `pm`;
- every agent has **≥1** version; skill slugs are lowercase `cast-*`;
- **CAST-452/CAST-461 sections byte-identical** to the Phase 4 batch (parallel-phase guard).

Regenerate (`node generate-org.mjs`); gate green; `git diff org.js` additive-only; F4 byte-identical
outside the four declared additions.

### Step 5.0.2: Route skeleton
Add the **ten** hash cases to the router with labeled stub renderers: `#/board` (real, replaces the
Phase 1 stub — but in 5.0 it's still a labeled stub the 5a runner fills), `#/ticket/CAST-412`,
`#/decision/:atomId`, `#/decisions/CAST-412`, `#/hire`, `#/marketplace`, `#/agent/:slug`,
`#/skills/new`, `#/layer2`, `#/reqs/CAST-412`. Add nav-rail entries **`Board · Hire · Layer-2`** (goal
routes keep their existing entries; `#/kit` stays hidden). **No new vt- names anywhere** — new routes
reuse the existing shell zone wrappers (nav rail · CanvasFrame · ChatRail).

### Step 5.0.3: appState additive keys
Initialize the four additive keys in the state literal; **v1/v1.1 keys untouched**:
- `boardFilter:'any'` · `hiring:{step:1, expanded:null, compare:false}` ·
  `autonomyLevel:'balanced'` · `reqsDoc:{openComment:null, deltaView:false}`.

### Step 5.0.4: The `DigestNotice` component
Pure props: `{glyph:'⚖'|'↺', summary, rows:[{label, body}]}` — a **non-modal strip**, rows expand via
native `<details>`. Fixture-render it on `#/kit`. This is the one inform-without-nagging atom,
instantiated later for the L2 decision digest (5a) AND the US7 write-back notice (5c) — **exactly one
definition in source** (PB-05 hand-off #3).

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual click-through) — verbatim from the plan:**
- Re-run the generator (`node generate-org.mjs`) — it emits with **all old + new invariants green**.
- Open `prototype/index.html` from disk; navigate to **each of the ten routes** via the address bar;
  each renders a **labeled stub** inside the standard shell (nav rail · CanvasFrame · ChatRail).
- `window.ORG` shows the new slices in devtools (`requirements_doc` on CAST-412, `versions` +
  `monitoring` on agents, `org.skills`, the `dial_demo` marker on one L2 atom). **No console errors.**
- `git diff` on `data/org.js` shows **only additive keys**; CAST-452/CAST-461 sections byte-identical.
- The nav rail shows the new `Board · Hire · Layer-2` entries; `#/kit` stays hidden.
- `DigestNotice` renders on `#/kit` from props; its rows expand via native `<details>`.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] Generator regenerates `org.js` deterministically; gate green (all old + 6 new invariants);
      `git diff` additive-only; CAST-452/461 sections byte-identical (F4 / parallel-phase guard).
- [ ] All ten routes resolve to labeled stubs in the standard shell; no console errors.
- [ ] The four additive appState keys exist in the state literal; v1/v1.1 keys untouched.
- [ ] `DigestNotice` renders from props on `#/kit`; exactly one definition in source.
- [ ] Nav rail gains `Board · Hire · Layer-2`; `#/kit` hidden.
- [ ] Closed 5-op set intact; 6×1 vt- anchors unchanged (no new vt- name); `node --check` clean.

## Design review (verbatim from the plan)
- **Parallel-phase data guard:** the generator batch is the one file both Phase 4 and Phase 5 touch.
  Mitigation is the byte-identical invariant on CAST-452/461 sections plus running this batch as one
  commit before sub-streams start. ⚠ flagged in the consolidated table.
- **Naming:** route names mirror the existing `#/goal/:id` convention; additive appState keys follow
  the Phase 3/4 precedent (`stageFocus`, `parityOpen`). ✓
- **`file://` constraint respected:** all new data ships inside `org.js`; no fetch; `DigestNotice`
  rows use native `<details>`. ✓

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5.0 | Generator batch is the one Phase4∥Phase5 shared file | Byte-identical invariant on CAST-452/461 sections; land the batch as one commit before sub-streams start |
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) |

## Execution Notes
- **Generator single-owner:** 5.0 is the *only* Phase-5 sub-phase that edits `generate-org.mjs`.
  Commit the regenerated `org.js` before any parallel 5a/5b/5c work touches `index.html` data reads.
- **Single-source credibility:** the agent-ops `monitoring`/`versions` payloads must never restate the
  `stats` numbers — `99.9% · 505 runs · 2 loops` stays derived from `agent.stats` (5b reads it; 5.0
  only authors the ops fields *around* it).
- **Spec-linked files:** none — the prototype is greenfield (FR-020); no `/cast-update-spec` action.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
