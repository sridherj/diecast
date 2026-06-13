# Sub-phase 4.3: FR-017 Three-Access-Tiers Parity Moment (hosted in the spike flow)

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase4-spike-data/_shared_context.md`
> before starting this sub-phase. The binding constraints there are not optional.

## Objective

A scripted beat in the spike flow reveals the side-by-side parity moment: a faux terminal pane
running the `cast` skill invocation next to the canvas/memo doing the same with defaults, **the same
E4 verdict-artifact card landing in both panes**, with the persistent chat rail visible alongside —
one screenful showing all three access tiers (terminal / chat / canvas) over one substrate. Static
depiction, no logic (playbook 02 Step 7: a parity *depiction* — and an honest one, since the real
codebase materializes `agents/cast-*.md` to both a terminal skill and a server dispatch emitting the
same contract envelope). This sub-phase is **on the critical path** (4.1 → 4.3 → 4.4).

## Dependencies
- **Requires completed:** Sub-phase 4.1 (the spike canvas + the `parity` data block in `org.js`).
- **Assumed codebase state:** `#/goal/CAST-452` is the real spike canvas; `SCRIPTS.spike` exists with
  an **explicit reserved beat slot** after the verdict beat, before the L3 stop;
  `goals['CAST-452'].parity = {command, transcript, artifact_id, caption}` resolves in `ORG`.
- **Parallel-capable with 4.2.**

## Scope
**In scope:**
- The parity reveal as script-patch-driven state (additive `appState.parityOpen` flag).
- The terminal pane (`parity-*` CSS prefix; ink-dark; mono; from the parity data block).
- The artifact-landing render in both panes (the same verdict-card stub fed the same ORG node).
- Wiring the beat into `SCRIPTS.spike`'s reserved slot (reveal patch → narration → exit patch).

**Out of scope (do NOT do these):**
- Editing `generate-org.mjs` or `org.js` (4.1 owns the `parity` data — consume it only).
- A sixth op or a new `drillInto` target class (scripts patch state directly).
- Any typing animation, fake window decorations beyond a minimal title bar, or a fake
  chat-invocation animation (the chat tier is the **existing** persistent rail).
- Any vt- name on the parity layout; any test file; any change to the spike canvas's other zones.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Spike canvas (from 4.1); gains the `parity-*` terminal pane + the parity script beat |

## Detailed Steps

### Step 4.3.1: Build the parity reveal as script-patch-driven state
An additive script-set flag (e.g. `appState.parityOpen`, additive key — Phase 1 contract allows
extension) toggled **only** by the spike script's patches. **No sixth op, no new `drillInto` target
class** — the closed vocabulary stands; scripts patch state directly (the engine's designed mechanism).

### Step 4.3.2: Build the terminal pane (`parity-*` prefix)
An ink-dark (`--ink`) panel with mono text — a deliberate, contained identity exception because it
*depicts the terminal tier*, not Diecast chrome (Decision 7; slop-gate checked in 4.4). Prompt glyph,
command line, output rows, artifact line — **all from the parity data block** (nothing typed in
markup). IBM Plex Mono; static (no typing animation — HOLD SCOPE).

### Step 4.3.3: Render the artifact landing in both panes
The same verdict-card stub component fed the same resolved ORG node (via `parity.artifact_id`) —
**pixel-equal cards, one data source**.

### Step 4.3.4: Wire the script beat into `SCRIPTS.spike`
At the slot 4.1 reserved (after the verdict lands, before the L3 stop): reveal patch → narration
naming the three tiers and the one-substrate claim → exit patch.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. With no
> browser, satisfy the layout/anchor checks statically (grep `view-transition-name` count, inspect the
> generated split-pane markup, confirm both panes resolve the same `parity.artifact_id` node) and
> record the "three tiers in one screenshot" item as a non-blocking human-eyeball carry-forward.
> **Do not flag missing tests.**

**Verification (manual click-through) — verbatim from the plan:**
- Advance the spike script to the parity beat: the canvas area splits to two panes —
  terminal left, canvas/memo right — with the chat rail still visible; a caption line states
  the one-substrate claim (text from `ORG.goals['CAST-452'].parity.caption`, not typed in
  markup). Three tiers identifiable in one screenshot; keep the screenshot as evidence.
- The terminal pane renders the transcript from the parity block: prompt line with the
  `cast …` command, output lines, and the artifact-landing line; IBM Plex Mono; static (no
  typing animation — HOLD SCOPE).
- **Same-artifact check:** the verdict-artifact card rendered in the terminal pane's landing
  line and in the canvas pane is the same ORG node — identical id and title (drift check:
  both read the node resolved via `parity.artifact_id`).
- The next script step exits the beat cleanly — normal spike canvas restored, `stageFocus`
  and receipts intact; reduced-motion shows a fade, no slide.
- Anchor audit: the parity layout introduces **no** element carrying any vt- name (DevTools
  search for `view-transition-name` count unchanged); transitions elsewhere still run.
- The beat never fires unprompted — exclusively script-driven.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] The parity beat splits to two panes (terminal left, canvas/memo right) with the chat rail visible.
- [ ] Terminal pane renders entirely from `parity` data (command, transcript, artifact line, caption);
      nothing typed in markup.
- [ ] Both panes render the same verdict-artifact card resolved via `parity.artifact_id` (same id/title).
- [ ] Exit step restores the spike canvas; `stageFocus` + receipts intact; reduced-motion fades.
- [ ] `view-transition-name` count unchanged (no vt- name on the parity layout).
- [ ] The beat is exclusively script-driven; no sixth op; `node --check` clean.

## Design review (verbatim from the plan)
- **Identity exception flagged:** the dark terminal pane is the only non-light-world surface
  in the prototype; it must read as "a window into the terminal tier" (chrome-light, mono,
  no fake window decorations beyond a minimal title bar). If the slop gate flags it, the
  fallback is a paper-light terminal treatment with a heavy mono frame — recorded in
  borderline-calls.md if taken.
- **Anchor uniqueness (the silent killer):** the parity pane must not duplicate any vt-
  name; the verification's DevTools count check is mandatory.
- **Drift:** the command string, transcript, caption, and artifact id all live in the parity
  data block — nothing typed in markup; the grep in 4.4 enforces it.
- **Scope honesty:** the chat tier is represented by the *existing* persistent rail — no
  fake chat-invocation animation is built (the spec's moment is terminal-vs-canvas with the
  rail present; playbook 02 confirms the chat leg is "invented (scripted)" by the existing
  rail).

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4.3 | Dark terminal pane vs the locked light world | Deliberate, contained exception (depicts the terminal tier); slop-gate checked; light fallback costed |
| 4.3 | Parity pane duplicating a vt- anchor name (silent transition kill) | DevTools anchor-count audit in verification |

## Execution Notes
- The dark terminal pane is the prototype's **one** sanctioned identity exception — keep the chrome
  minimal; if the 4.4 slop gate flags it, take the paper-light fallback and **record it in
  `docs/plan/product-revamp-diecast-borderline-calls.md`**.
- Scripts patching `appState.parityOpen` directly is the engine's designed mechanism — resist the
  temptation to add an op or a `drillInto` target.
- **Spec-linked files:** none — greenfield prototype (FR-020). The parity pane *depicts* the real
  `agents/cast-*.md` → `bin/generate-skills` substrate as fake transcript data; it is reference
  material rendered as prototype content, not a spec'd surface being modified — no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review`.
