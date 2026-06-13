# Sub-phase 4b-4: The Spec Records the Survival Contract, and SC-003 Proves It End-to-End

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4b/_shared_context.md` before starting —
> especially the **DECISION #10 OVERRIDE** section (the survival contract is recorded
> override-aware).

## Objective

`cast-requirements-render.collab.md` records the 4b contract — quote-anchoring preserved under a
varying render, the logical id backbone the diff agent reads, the LLM-resolution trust boundary, the
survival gate (override-aware: surfaced, not blocking), and the contract-v2 carve-out — in a single
`/cast-update-spec` pass; and the SC-003 sweep passes against the real pipeline: with open comments
present, a maker regenerate leaves every comment anchored with zero new orphans; a moved/reworded
block is re-anchored by the LLM, not dropped; the diff never shows a change absent from the source.

## Dependencies

- **Requires completed:** **4b-1 + 4b-2 + 4b-3** (terminal sub-phase).
- **Assumed codebase state:** survival gate live (`check_comment_survival` + widened `gate_html` +
  `.comment-unplaced` badge); reanchor contract v2 + refine-loop wiring; narration store/API/render.
- `bin/cast-spec-checker`; `docs/specs/_registry.md`; the `eval_` real-pipeline harness for SC-003.

## Scope

**In scope:**
- One `/cast-update-spec` pass on `cast-requirements-render.collab.md` (the five deltas below).
- The SC-003 sweep (three verification blocks) via the `eval_` real-pipeline harness; record results
  + the human-eyeball carry-forward in the goal's artifacts.
- A Phase-5 / reconciliation hand-off note in the goal dir.

**Out of scope (do NOT do these):**
- Do NOT implement new behavior — this sub-phase records what 4b-1/2/3 built and proves it. Clause
  texts were fixed by the plan up front (the spec records behavior, it does not retro-discover it).
- Do NOT modify `cast-requirements-roundtrip.collab.md` (consumed, not modified — the verdicts-only
  writeback call site stays valid under contract v2 by construction).
- Do NOT re-open any owner-resolved decision.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-requirements-render.collab.md` | Modify (via `/cast-update-spec`) | Draft v2; gains the five deltas + new `linked_files` |
| `docs/specs/_registry.md` | Modify | row bumped for the render spec |
| `docs/goal/refine-requirements-better-rendering-v3/...` (SC-003 evidence + hand-off note) | Create | sweep results + carry-forward + reconciliation hand-off |

## Detailed Steps

### Step 4b4.1: `/cast-update-spec` on `cast-requirements-render.collab.md`

→ Delegate: `/cast-update-spec` with these deltas (review the diff before approval, per the skill's
inline gate):

1. **Anchoring under a varying render:** the comment/version layer keeps quote/verbatim-substring
   anchoring with the DOM contract unchanged (zero `id=`, zero `data-block-anchor`; FR-025's
   transient-id exception stays diff-view-only); `<mark>` placement is re-derived per render, and the
   **comment-survival gate** (in-block placeability over real open comments, riding the
   verbatim-carriage clause) is part of structural maker gating. **Override-aware wording:** an
   in-block miss is a surfaced structural violation that flags the served best attempt
   (`structural_violation`) and shows the `.comment-unplaced` tray badge — it does **not** block
   publish or trigger the deterministic fallback (which fires only on literal no-output).
   Cross-boundary quotes are a recorded limitation surfaced by the same badge (US12 tray grouping +
   SC-009 selector list extended).
2. **The logical id backbone the diff agent reads:** the WHAT-doc id-mapping and the parsed
   `Block.ref` space are the same id vocabulary; `block_diff` set-arithmetic stays deterministic,
   source-side, and unchanged (FR-024 engine untouched).
3. **The LLM-resolution trust boundary:** the LLM narrates the deterministic change set and
   re-anchors/resolves moved-or-reworded comments only; narration is structurally validated (every
   note keys to a `summarize()` item, else 422) and rendered by attachment only — a diff can never
   show a change absent from the source. FR-024's byte-for-byte guarantee re-scoped to the
   `counts`/`items` keys with `narration` as a sibling; FR-023 gains the narration POST.
4. **FR-027/US13 superset:** `cast-comment-reanchor` contract v2 — optional `change_set` +
   block-context inputs, `narration` output, the `resolved` verdict with its recoverability
   rationale and the `relocated > resolved > orphaned-when-unsure` bias, the anchor-pickability rule;
   still the bare-JSON subagent carve-out (recorded, not drift).
5. **New surfaces appended to `linked_files`:** `version_diff_narrations` migration, the survival
   additions in `maker_gate.py`, the narration fragment/CSS touches, the widened `gate_html` seam in
   `render_job_service.py`, the `.comment-unplaced` JS/CSS.

→ Follow-up: review the `/cast-update-spec` diff before approving — confirm the DOM contract is
asserted **unchanged**, the survival wording is **override-aware** (surfaced, not blocking), and no
owner-resolved decision is re-opened.

### Step 4b4.2: Run the SC-003 sweep (the phase gate)

Via the `eval_` real-pipeline harness (not default CI). Record evidence into the goal dir.

- **Same-source regenerate (render-only):** with N open comments placed, force a maker re-render
  (cache-busted attempt against the same source) → **zero DB changes of any kind** (no new version,
  no displacement, no orphans), survival gate green, all in-block marks place on the new DOM.
  Deterministic check: comment rows byte-identical before/after.
- **Source-edit regenerate (the full loop):** edit the source so one commented block is
  reworded+moved, one is deleted, one untouched → version cut → `displaced_comment_ids` contains
  exactly the reworded + deleted ones → agent dispatch → reworded comment `relocated` (422 backstop
  not triggered), deleted-block comment `orphaned` (surfaced in tray), untouched comment never
  displaced → **zero new orphans beyond the genuinely-deleted block** → new maker render publishes
  with survival green and the relocated mark placed.
- **Trust-boundary check:** the posted narration for that version pair contains only notes keyed to
  the deterministic items (assert server-accepted = recomputed set); the rendered panel shows no
  change entry beyond `summarize()`'s items.

### Step 4b4.3: Spec-checker + registry + hand-off note

- `bin/cast-spec-checker` green on the updated spec; bump the `docs/specs/_registry.md` row.
- Record the **human-eyeball browser pass** over the tray badge + narration panel as a carry-forward
  item (autonomous runs cannot drive a browser; static verdicts never block).
- **Hand-off note for Phase 5 / reconciliation** (one short section in the goal dir):
  - the narration POST is the surface Phase 5's round-trip summaries may reuse; the writeback
    dispatch site remains verdicts-only and may adopt `change_set` context at reconciliation;
  - **4a/4b both touched `render_job_service.py`** — list the exact seams for the merge (4b widens
    `gate_html`'s report; 4a inserts `run_checker → decide_quality` after it), **including the
    override-era ordering contract:** survival is evaluated inside the structural gate
    (`gate_html`), and under DECISION #10 OVERRIDE a survival-failing attempt is a **flagged,
    servable** structural state — it is part of the *surfaced* report 4a wraps, **not** a
    disqualifier from the best-scoring serve. The merge must keep survival evaluated before
    `run_checker` scores an attempt, and must preserve the override (no survival→block / no
    survival→deterministic-fallback).

## Verification

### Automated / eval gate
- `bin/cast-spec-checker` green on `cast-requirements-render.collab.md`.
- The SC-003 sweep (three blocks above) green via the `eval_` harness; evidence files written to the
  goal dir.
- Default CI sweep (`pytest cast-server/tests/`) green — the spec pass + sweep introduce no code
  regressions.

### Manual Checks
- Diff-review the `/cast-update-spec` output before approval (the inline gate).
- Confirm `docs/specs/_registry.md` row reflects the new version/date.
- Confirm `cast-requirements-roundtrip.collab.md` is untouched.

### Success Criteria
- [ ] All five spec deltas recorded in one `/cast-update-spec` pass; DOM contract asserted unchanged;
      survival wording is override-aware (surfaced, not blocking).
- [ ] `linked_files` includes the five new surfaces.
- [ ] SC-003 sweep green: same-source regenerate = zero DB changes + survival green; source-edit loop
      = zero new orphans beyond the deleted block + relocated mark placed; trust-boundary check
      passes.
- [ ] `bin/cast-spec-checker` green; `_registry.md` bumped.
- [ ] Phase-5 / reconciliation hand-off note written, incl. the override-era `render_job_service`
      merge contract.
- [ ] Human-eyeball browser pass recorded as a non-blocking carry-forward.

## Execution Notes

- **This IS the spec work** — all flags from 4b-1/2/3 resolve in one pass; the DOM contract is
  asserted unchanged. Same discipline as Phase 3's 3e.
- **Override-awareness is the subtle bit.** The source-plan body for 4b-4 (delta #1, the hand-off
  note) predates DECISION #10 OVERRIDE and frames survival as blocking / disqualifying. Record the
  **override-era** contract: survival-failing attempts are servable + flagged + badge-surfaced;
  fallback only on literal no-output. "Never silently drop" binds by surfacing, not hiding.
- **Spec-linked files:** this sub-phase IS the spec edit; nothing to flag forward.
