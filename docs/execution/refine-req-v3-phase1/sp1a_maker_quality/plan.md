# Sub-phase 1a: The Maker Quality Ceiling Is Proven By Hand

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase1/_shared_context.md` before starting.

## Objective

Prove *by hand* that an LLM maker working from the cast-preso visual toolkit can produce a
requirements render that **clearly beats** the v2 deterministic page on comprehension and
visual quality for **at least two work families**, while carrying every canonical id verbatim
on the correct block (FR-003) and staying a self-contained single file (FR-007). This is a
**ceiling proof** — a human crafts the HTML to establish that the bar is *reachable*; Phase 3
re-proves it agent-generated. If the bar cannot be cleared even by hand, the maker-vs-hybrid
fork is surfaced for the owner to revisit before Phase 3 commits — never silently re-scoped.

## Dependencies

- **Requires completed:** None (parallel with sp1b).
- **Assumed codebase state:** v2 is intact — `renderer.render_requirements()`,
  `zero_click.extract_zero_click_view`, and the `cast-requirements-checker` agent all exist
  and run. The cast-preso visual toolkit is present at
  `~/.claude/skills/cast-preso-visual-toolkit/`.

## Scope

**In scope:**
- Assembling a ≥2-family corpus (this goal's `new_initiative` doc + an authored `bug_fix` doc;
  optional stretch `data_analysis` doc).
- Hand-running the cast-preso-how **8-step discipline** per doc (brainstorm → archetype
  shortlist → brief → HTML), adapted to a scrolling document page (not a reveal.js slide).
- The v2 deterministic baseline render of each source for side-by-side comparison.
- Four audits: id-token set-equality **and per-block correspondence**, self-containment grep,
  zero-`id` grep, and `cast-requirements-checker` verdicts on both maker + baseline.
- Writing `spikes/1a/spike-results.md` with a per-family `BEATS DETERMINISTIC: yes/no` verdict
  and a *recommended* gate disposition (the binding call is made at G1).

**Out of scope (do NOT do these):**
- Do **not** invoke `/cast-preso-how` — it generates reveal.js slides and the net-new
  requirements agents are Phase-3-owned. Follow only its 8-step *discipline* by hand.
- Do **not** build any new agent — Phase 1 builds none.
- Do **not** write `goals/{slug}/refined_requirements.html` or drop any file into a real goal
  folder via `render_requirements()`.
- Do **not** tune `cast-requirements-checker`, change any spec, or run `/cast-update-spec`.
- Do **not** touch Phase-2 files (`goal_card.py`, `_first_sentence`, comment-affordance UI).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/fixtures/<bug_fix-doc>.collab.md` | Create | Does not exist — authored from a real defect |
| `docs/goal/.../spikes/1a/<family>-maker.html` (one per family) | Create | Does not exist |
| `docs/goal/.../spikes/1a/<family>-baseline.html` (one per family) | Create | Does not exist — `render_requirements()` output |
| `docs/goal/.../spikes/1a/briefs/<family>-brief.md` (approach notes per family) | Create | Does not exist |
| `docs/goal/.../spikes/1a/spike_id_audit.py` | Create | Throwaway audit script |
| `docs/goal/.../spikes/1a/spike-results.md` | Create | The gate-evidence artifact |

## Detailed Steps

### Step 1a.1: Assemble the family corpus
- **Doc 1 (`new_initiative`):** this goal's own
  `docs/goal/refine-requirements-better-rendering-v3/refined_requirements.collab.md` — the only
  real classified doc in the repo.
- **Doc 2 (`bug_fix`):** author a real `bug_fix` requirements doc from the actual v2 dogfooding
  defect — the `goal_card.py` raw-markdown leak (real problem, real evidence, real fix scope) —
  in the standard refined-requirements shape with `classification.family: bug_fix` front matter.
  Store under `spikes/1a/fixtures/`. **Author from the real defect; do not synthesize fiction.**
- **Doc 3 (`data_analysis`, stretch — only if sessions allow):** a `data_analysis` doc by the
  same method.
- Generate the v2 deterministic baseline for each via `render_requirements()` — a **pure call**;
  do **not** drop files into `goals/{slug}/`. Capture the HTML to `spikes/1a/<family>-baseline.html`.

### Step 1a.2: Hand-run the preso-how discipline per doc
For each doc, in-session and by hand (no new agent):
1. Brainstorm 2-3 visual approaches with slide-specific pros/cons and an honest
   Steve-Jobs-test verdict.
2. Shortlist archetypes from the toolkit library
   (`~/.claude/skills/cast-preso-visual-toolkit/templates/slide-archetypes/*.html` — 11
   archetypes incl. compare-contrast, single-stat-hero, timeline, diagram-annotated).
3. Write a short brief to `spikes/1a/briefs/<family>-brief.md`.
4. Craft the HTML — starting from the toolkit's style tokens
   (`visual_toolkit.human.md`) and adapting archetype vocabulary (e.g. single-stat-hero for
   the Goal Card, compare-contrast for decisions, timeline for phases) to a **scrolling
   document page**, not a reveal.js slide.
- **Conscious non-delegation (record it):** `/cast-preso-how` is **not** invoked — only its
  8-step discipline is followed by hand. Note this explicitly in the brief so an execution-time
  reader neither invokes the slide agent nor skips the discipline.

### Step 1a.3: Honor the resolved page-structure decision
- Section names are **family-appropriate communication** ("key decisions", "what broke and the
  evidence", …) — **never** US/FR/SC slots.
- Canonical ids appear as small **anchoring labels** on their blocks (visible text, **NOT**
  `id=` attributes).

### Step 1a.4: Respect the v2 DOM contract while hand-crafting
- Each requirement unit = one contiguous semantic `<section>`/`<li>` under a real `<h2>`/`<h3>`,
  no span fragmentation.
- **Zero `id=` and zero `data-block-anchor` anywhere** (FR-012/FR-013).
- FR-028 script tags (`/static/htmx.min.js`, `/static/requirements_comments.js`) +
  `data-goal-slug` present, so **sp1b can reuse these files**.

### Step 1a.5: Run the audits (throwaway scripts under `spikes/1a/`)
- **id-token set equality AND per-block correspondence** (`spike_id_audit.py`): the set of
  `US-NN`/`FR-NNN`/`SC-NNN` tokens visible in the maker HTML **equals** the set parsed from the
  source (no missing, no invented, no renamed) **and** each id label sits on the block whose
  source text it identifies. FR-003 is per-block, not just set-membership — set-equality alone
  would pass even with a label on the wrong block, and **Phase 3 reuses this audit as its
  acceptance pattern**, so encode it faithfully.
- **Self-containment grep:** no external `src`/`href` fetches beyond the FR-028 sanctioned two;
  no CDN fonts; CSS inline.
- **Zero-`id` grep:** no `id=`, no `data-block-anchor`.

### Step 1a.6: Judge the gate
- → **Delegate:** `cast-requirements-checker` (subagent, bare-JSON verdict) over the zero-click
  extract (`extract_zero_click_view`) of **both** the maker HTML and the deterministic baseline,
  per doc.
  - **Review `cast-requirements-checker` output for:** `can_state_what`; completeness of
    `restated_job` / `outcome` / `scope`; `missing[]`. If a verdict looks anomalous (fails a page
    a human clearly comprehends), **record the anomaly as Phase-4a input — do not tune the
    checker now** (it is replaced by a richer one in Phase 4a).
- Supplement with a **structured rubric self-assessment** (hierarchy, scannability,
  family-appropriateness, visual quality) comparing maker vs baseline side by side.
- **No browser in autonomous runs:** record the human-eyeball browser pass as an explicit
  **carry-forward** item — static verdicts + carry-forward, never block.

### Step 1a.7: Write the decision-gate verdict
Write `spikes/1a/spike-results.md` recording, per family:
- `BEATS DETERMINISTIC: yes/no` with evidence.
- The checker verdicts (maker + baseline), the rubric table, the four audit results.
- A **recommended** disposition: quality clearly beats → recommend Phase 3 proceeds; cannot
  clear the bar even by hand → recommend surfacing the **maker-vs-hybrid fork** to the owner.
  **The binding decision is made at G1 — do not silently re-scope here.**

## Verification

### Automated Tests (permanent)
- **None.** Phase 1 adds no CI tests. Spike scripts are `spike_*.py` under `spikes/1a/` and are
  never collected by pytest.

### Validation Scripts (temporary)
- `spike_id_audit.py` — prints, per family: source id-set, HTML id-set, set-equality result,
  and per-block correspondence pass/fail. Include the raw output in `spike-results.md`.
- A self-containment grep + a zero-`id` grep, output captured in `spike-results.md`.

### Manual Checks
- Open each `<family>-maker.html` and `<family>-baseline.html` in a browser side-by-side
  (recorded as a **carry-forward** item if no browser is available in this run).
- Confirm the brief for each family records the conscious `/cast-preso-how` non-delegation.

### Success Criteria
- [ ] `spikes/1a/spike-results.md` exists with an explicit per-family `BEATS DETERMINISTIC: yes/no`.
- [ ] ≥2 families covered: one committed maker HTML + one baseline HTML each.
- [ ] id-audit run recorded: set-equality **and** per-block correspondence both pass (or the
      failure is the recorded gate result).
- [ ] Self-containment audit recorded: no fetches beyond the FR-028 sanctioned two, CSS inline.
- [ ] Zero-`id` audit recorded: no `id=`, no `data-block-anchor` in any maker HTML.
- [ ] `cast-requirements-checker` verdicts captured for **both** maker and baseline, per doc.
- [ ] A recommended gate disposition is written (beats → proceed / fork → surface) — not a
      binding re-scope.

## Execution Notes

- **Artifact placement is load-bearing:** spike HTML lives under `docs/goal/.../spikes/1a/`,
  **never** as `goals/{slug}/refined_requirements.html` (would be served live / trip
  `test_fr007_readonly_guard.py` and the FR-026 folder invariant).
- **Hand-effort honesty:** a human crafts better than the eventual agent will. State the
  hand-effort plainly in `spike-results.md` — this is a *ceiling* proof; the gate wording is
  "reachable by hand", and Phase 3 re-proves it agent-generated.
- **Family breadth caveat:** only one real classified doc exists; the `bug_fix` doc is authored.
  Note that family breadth is re-validated across all nine families in Phase 5 (SC-002).
- **Spec-linked files:** this sub-phase modifies none. It consumes
  `cast-requirements-render.collab.md` and `cast-goal-classification.collab.md` read-only — no
  spec edits, no `/cast-update-spec`.
