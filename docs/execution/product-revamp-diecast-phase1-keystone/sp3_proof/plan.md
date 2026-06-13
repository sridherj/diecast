# Sub-phase 1.3: Proof — Hero Morph Spike & Decision Gate

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase1-keystone/_shared_context.md`
> before starting. It carries the 7 exported contracts (especially Contract 5 — the `vt-` anchor
> names + uniqueness rule, and Contract 6 — the motion tokens), the binding constraints (NO TESTS,
> file:// legality, single-file packaging), and FULL AUTONOMY mode. This plan does not repeat them.

## Objective

Answer the phase's riskiest unknown and record the verdict. Make the placeholder feature-spine
→ debug-spine morph run as a ~350ms shared-element transition with **≥4 persistent anchors
gliding** (not crossfading), the family-specific spine content crossfading between visibly
**different shapes** (segment bar vs loop band + `↺ iter 2/3` badge), a stub decision receipt
appearing, and `prefers-reduced-motion` degrading to a 180ms fade. Then **run the pre-written
5-item gate checklist and record the verdict autonomously** (FULL AUTONOMY — this is *not* a
human gate, and there is *no* `gate_*` file): View Transitions carries the morph → locked for
Phase 3; it can't → adopt and document the keyed CSS panel-swap contingency *before* any real
canvas is built. Also tidy the file for handoff (remove the dev op-strip, final console-clean
pass, confirm <15KB).

## Dependencies
- **Requires completed:** Sub-phase 1.2.
- **Assumed codebase state:** `prototype/index.html` has the closed-set dispatcher, the five op functions, the ~50-line scenario engine, the ~6-step demo script (including `morph:debug` + reverse `morph:feature`), and the ChatRail "Next ▸" control. The five anchor elements (nav rail, goal header, nudge card, receipt trail, chat rail) are mounted as persistent structure across both families. A temporary dev op-strip exists, marked for removal/gating.

## Scope

**In scope (edit the single file `prototype/index.html` only):**
- Tag the five anchors (Contract 5) with `view-transition-name` in CSS, honoring the uniqueness rule.
- Style the transition at the locked register via `::view-transition-group(*)` using the motion tokens.
- Make the two placeholder spines **visually contrasting shapes**: feature = labeled segment bar (5 segments, accent-filled current); debug = staged band + `↺ iter 2/3` badge — each carrying a visible `PLACEHOLDER` watermark.
- Render the stub decision receipt as a 6A-style pill in the receipt-trail anchor zone.
- Reduced-motion fallback path verified (180ms fade, no sliding).
- **Run the 5-item gate checklist, record the verdict + one-line evidence per item** in this sub-phase's output, append it to `docs/plan/product-revamp-diecast-decisions-so-far.md` (and `product-revamp-diecast-borderline-calls.md` if the fallback is taken).
- **Contingency (only if the gate fails):** implement the keyed CSS panel-swap (`data-family` on `CanvasFrame`, stacked panels, FLIP-animated anchors) — same dispatcher, same ops, only the transition mechanism inside `dispatch()` changes.
- **Handoff tidy:** remove the dev op-strip (or gate behind `#/dev`), final console-clean pass, confirm library weight <15KB.

**Out of scope (do NOT do these — HOLD SCOPE):**
- Real canvases, real evidence panels (the 6B/6C disclosure ladder is Phase 2b), real per-family vocabulary (Phase 2c), the Guide's visible character (Phase 2b). The spines stay watermarked placeholders.
- More than 5 named anchors. Naming everything makes everything glide and nothing read (playbook 02 pitfall).
- Building the panel-swap contingency *as well as* View Transitions if the gate **passes** — only one mechanism ships. Build the contingency **only** on a failed verdict.
- Tests / harness / CI (C1). `fetch()` / local imports / extra files (C2/C3).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Exists from 1.2: dispatcher + ops + scenario engine + demo script + ChatRail. Add anchor `view-transition-name` CSS, contrasting spine shapes + watermark, receipt pill, reduced-motion path; remove dev op-strip. |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append) | Exists. Append the morph-gate verdict + 5-item evidence. |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | Modify (append) | Create if absent. **Only if** the fallback (panel-swap) is taken — record the borderline call. |

## Detailed Steps

### Step 1.3.1: Tag the five anchors (Contract 5) with `view-transition-name`
- In the inline `<style>`, give each persistent element its name: `vt-goal-header`, `vt-chat-rail`, `vt-nudge-card`, `vt-receipt-trail`, `vt-nav-rail`.
- **Uniqueness rule (critical):** each name must appear on **exactly one rendered element per snapshot**. A duplicate silently skips the *whole* transition. Because the anchor elements stay mounted across both families (1.1/1.2 built them that way), this holds — verify it (manual check #1 below). Keep to **5 names max** (the ≥4 requirement + one spare).

### Step 1.3.2: Style the transition at the locked register (Contract 6)
```css
::view-transition-group(*) {
  animation-duration: var(--morph-duration);            /* 350ms */
  animation-timing-function: var(--ease-morph);         /* cubic-bezier(0.2,0.8,0.2,1) */
}
```
- The family-specific **spine zones carry NO `view-transition-name`** → they get the root crossfade. Verify the default old/new crossfade reads cleanly; only add per-zone names if it doesn't.

### Step 1.3.3: Make the two spines visually contrasting shapes (the SC-005 seed)
- **feature** = a labeled **segment bar**: 5 segments, the `current` one accent-filled (raspberry).
- **debug** = a staged **loop band** with a `↺ iter 2/3` badge.
- Both render a small **`PLACEHOLDER`** watermark tag so screenshots can't be mistaken for Phase-2c-derived vocabulary. The contrast is what makes the morph read as "same goal, new *shape*."

### Step 1.3.4: Render the stub decision receipt (6A-style pill)
- In the `vt-receipt-trail` zone, render each `appState.receipts[]` entry as a pill: `L2 · Reclassified feature→bug` + timestamp. Pill + label + timestamp only — the 6B/6C disclosure ladder is Phase 2b.

### Step 1.3.5: Reduced-motion path
- Confirm the 1.2 dispatcher's `reduced.matches → fade(apply)` branch yields a ≤200ms (180ms) fade with **no sliding** under DevTools → Rendering → Emulate `prefers-reduced-motion: reduce`.

### Step 1.3.6: Run the gate checklist and record the verdict (autonomous)
Advance the demo script to the *"this is actually a bug…"* step and evaluate all five criteria. **All must pass to lock View Transitions for Phase 3:**
1. **Anchors glide** rather than crossfade (shared-element identity is real).
2. **No flash/flicker/layout jump** at transition start or end.
3. **Runs from `file://`** in Chrome (primary demo browser) — no protocol-specific breakage.
4. **Feels like ~350ms of revealed layout, not spectacle** (the Linear/Raycast register). *(The soft, taste criterion — judge against "motion reveals layout, never performs"; keep a screenshot/recording as evidence.)*
5. **Reduced-motion fallback works.**

Record the verdict with **one line of evidence per item** in this sub-phase's output, and **append it to `docs/plan/product-revamp-diecast-decisions-so-far.md`**. Because FULL AUTONOMY is in effect, you resolve the gate yourself — the pre-written checklist + retained evidence keep the call checkable rather than vibes. Do **not** pause for a human.

### Step 1.3.7: Contingency branch — ONLY if the gate fails
Adopt the **keyed CSS panel-swap**:
- `data-family` attribute on `CanvasFrame`; family panels stacked in one CSS grid cell with opacity/transform transitions at the same motion tokens.
- The 4–5 anchors animated via **FLIP** (measure → mutate → invert → play with `element.animate`).
- **Same dispatcher, same ops** — only the transition mechanism inside `dispatch()` changes (~1 extra session). The op-vocabulary contract (Contract 3) is what makes this swap cheap and the gate safe to resolve autonomously.
- Record the borderline call in `docs/plan/product-revamp-diecast-borderline-calls.md` and note the mechanism switch in `decisions-so-far.md`. Downstream phase plans do **not** change shape — only Phase 3's "real morph" activity swaps its mechanism.

### Step 1.3.8: Handoff tidy
- **Remove the dev op-strip** (1.2's verification crutch) or gate it behind `#/dev`. The showable artifact must not ship a raw op-button strip.
- Final **console-clean** pass (no stray `console.debug`/`console.log`).
- Confirm library weight **<15KB** gzipped (preact + htm; `driver.js` still mapped-but-unloaded).

## Verification (this is the phase's headline verification)

### Automated Tests (permanent)
- **None.** Constraint C1. Do not create any test file.

### Validation Scripts (temporary)
- None that run code. Verification is the gate checklist, observed in Chrome + DevTools.

### Manual Checks (open from disk in Chrome and observe — this is the spike)
1. **Anchors persist and glide:** Open `index.html` from disk; advance to the *"this is actually a bug…"* step. Observe: goal header, chat rail, nudge card, receipt trail, nav rail **persist and glide/resize** (do not crossfade); feature segment bar crossfades out, debug loop band + iteration badge crossfade in; total ~350ms (confirm in DevTools → **Animations** panel). Confirm each `vt-` name maps to exactly one element (no silent skip).
2. **Receipt + reverse:** The receipt pill (`L2 · Reclassified feature→bug`) appears in the receipt trail during/immediately after the morph; the reverse step morphs back **without state loss**.
3. **Reduced motion:** DevTools → Rendering → Emulate `prefers-reduced-motion: reduce` → the same step produces a ≤200ms fade, **no sliding** motion.
4. **Continuity:** Goal title and context **never disappear** mid-transition (reads as "same goal, new shape", not "new page").
5. **Gate checklist:** Walk all 5 items above; record pass/fail + one-line evidence each.
6. **Handoff clean:** Dev op-strip gone (or behind `#/dev`); console clean; Network tab confirms <15KB library weight.

### Success Criteria (binary — every item must pass)
- [ ] ≥4 anchors glide (not crossfade) through a ~350ms shared-element transition; ≤5 `vt-` names, each unique per snapshot.
- [ ] Feature segment bar and debug loop band are visibly different shapes; both watermarked `PLACEHOLDER`.
- [ ] Decision-receipt pill appears in the receipt trail on morph; reverse morph restores feature state with no loss.
- [ ] `prefers-reduced-motion: reduce` → ≤200ms fade, no sliding.
- [ ] Runs from `file://` in Chrome with a clean console; library weight <15KB; dev op-strip removed or gated behind `#/dev`.
- [ ] **The 5-item gate verdict is recorded** in this sub-phase's output **and** appended to `docs/plan/product-revamp-diecast-decisions-so-far.md` (one-line evidence per item).
- [ ] If (and only if) the verdict is **fail**: the keyed CSS panel-swap contingency is implemented (same dispatcher/ops) and the borderline call is logged in `docs/plan/product-revamp-diecast-borderline-calls.md`.

## Execution Notes
- **Gate honesty under full autonomy.** The 5 criteria are written *before* the spike runs, so the autonomous verdict is checkable, not vibes. Item 4 (taste) is the soft one — judge it against the "motion reveals layout, never performs" register and keep the screenshot/recording as evidence. Zero silent failure: the verdict is recorded in **two** places (sub-phase output + decisions-so-far).
- **Duplicate `view-transition-name` is the #1 silent failure.** If the morph just crossfades with nothing gliding, the first thing to check is whether a `vt-` name is rendered on two elements at once (e.g. an anchor that unmounts/remounts per family). Keep anchors mounted across families.
- **Anchor-count discipline.** 5 named anchors max. Do not name the spine zones — they're meant to root-crossfade. Naming everything makes everything glide and nothing read.
- **Fallback parity is the safety net.** The contingency keeps the identical op grammar and motion tokens, so no downstream phase plan changes shape either way — only Phase 3's real-morph activity swaps its mechanism. That's why this gate is safe to resolve without a human.
- **Build the contingency only on failure.** If the gate passes, do not also build the panel-swap. One mechanism ships.
- **Spec-linked files:** none. `prototype/index.html` is greenfield; the two plan docs appended to are planning artifacts, not specs.
- **Failure policy (C5):** retry once with refined instructions on failure; second failure → mark partial, log the exact gap. NOTE: a **gate verdict of "fail"** is **not** a sub-phase failure — it is a successful, recorded outcome that triggers the contingency. "Partial" applies only if the morph spike itself can't be built/observed to reach a verdict.
