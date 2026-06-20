# High-Level Phasing Plan: Exploration Pipeline — N×M Workflow + 90/10 Hat + Diecast HTML Surface

## Overview

Three pillars, two parallel tracks, converging at the end. **Track A** rebuilds the starter
exploration as a deterministic Claude **Workflow** that fans research across N steps × M hats as
isolated clean-context agents (realizing the origin's documented angle-independence), adds the new
first-class **90/10 hat**, and keeps per-step synthesis unchanged. **Track B** builds the horizontal
**dual md/html + commenting** artifact surface — validated first against the *existing* requirements
HTML render, so it doesn't wait on Track A. The two converge in the exploration WHAT/HOW HTML render.
Both unknowns (can a Workflow be the exploration engine? does in-viewer iframe commenting work?) are
de-risked by spikes up front. The Workflow ships **in parallel** to today's `cast-explore` — no
big-bang migration (the user merges later).

Key insight from the spec: Pillar 3 *extends an existing, spec'd pipeline* (`cast-requirements-render`),
not greenfield — so it reuses the render-job pattern, the same-door comment API, and the "render not
authored artifact" + "selectable units, no ids" DOM conventions rather than reinventing them.

## Phase 1a: Spike — Workflow as the exploration engine (parallel with 1b)
**Outcome:** We know exactly how the starter-exploration entrypoint launches a Claude Workflow that
receives approved steps + a hat-matrix as args and runs an isolated N×M fan-out within the concurrency
cap — or we know it can't, and why.
**Dependencies:** None
**Estimated effort:** 1–2 sessions
**Verification:** A toy Workflow runs 2 steps × 2 hats, each cell a separate single-context agent, and
writes 4 distinct research notes; the launch path from a skill/command (not a subagent) is demonstrated.

Key activities:
- Prototype a minimal Workflow script: `pipeline()`/`parallel()` over a 2×2 `(step, hat)` matrix calling a stub single-hat agent.
- Determine the entrypoint mechanism: how the "Run starter exploration" step triggers the Workflow tool (main-agent skill/command vs server-side dispatch) given Workflows are non-interactive and opt-in.
- Confirm args passing (steps + hat-matrix) and the `min(16, cores−2)` concurrency behavior with queued cells.
- **Decision gate:** mechanism viable → proceed to Phase 3a as planned. If launch can't be wired cleanly → revisit Phase 3a (fallback: keep the orchestrator-agent but enforce per-hat child isolation).

## Phase 1b: Spike — Dual md/html viewer + in-frame commenting (parallel with 1a)
**Outcome:** We know whether a full standalone HTML render displays cleanly in the artifact viewer via
iframe/srcdoc AND whether a text selection inside it yields a comment via the same-door API — tested
against the *existing* `refined_requirements.html`.
**Dependencies:** None
**Estimated effort:** 1–2 sessions
**Verification:** The existing requirements HTML renders inside the phase-tab viewer (iframe/srcdoc) without breaking the page; selecting text inside it produces a `change_requests`/comment row via the same-door API.

Key activities:
- Render an existing `refined_requirements.html` inside the artifact viewer via iframe/srcdoc; confirm no `<head>/<style>` collision with the host page.
- Test `/cast-comment-html`'s injected comment layer inside the iframe — does selection + "+ Comment" work across the iframe boundary, or only on a full-page serve?
- **Decision gate:** in-iframe commenting works → Phase 3b proceeds in-viewer. If not → fallback to a "comment on full-page render" surface (as requirements `/render` does today), with the viewer linking to it.

## Phase 2a: Single-hat researcher + the 8 hats (Track A foundation, parallel with 2b)
**Outcome:** A new lean single-hat researcher agent exists and produces a clean-context research note
for any one `(step, hat)` — including the new 90/10 hat — with First Principles stripped of its 80/20 content.
**Dependencies:** None (the agent is independently testable; Phase 3a wires it into the Workflow)
**Estimated effort:** 2–3 sessions
**Verification:** Running the agent for each of the 8 hats on one real step yields 8 distinct notes; the 90/10 note matches the spec's note shape; the First Principles note contains no 80/20 content.

Key activities:
- Build the new lean single-hat agent, param'd by hat, reusing only the web-fetch/resilient-browser protocol from `cast-web-researcher` (not its 7-in-one structure).
- Author all 8 hat prompts; carve the 80/20 notion OUT of First Principles.
- Implement the **90/10 hat** to the spec (6 always-ask questions; note shape: core / proposed cut / effort / self-checks / disqualifiers / verdict) — generative builder, not auditor.
- Fold in gstack **techniques only** (specificity ladder, anti-sycophancy phrasing, [EUREKA] tags) — never its review/boil-the-ocean principles.

## Phase 2b: Dual md/html artifact viewer — general capability (Track B, parallel with 2a)
**Outcome:** The Diecast artifact viewer renders both `.md` (as today) and `.html` (iframe/srcdoc) in
the phase-tab surface, and the existing refined-requirements HTML is viewable in-viewer (consumer #2).
**Dependencies:** Phase 1b
**Estimated effort:** 2–3 sessions
**Verification:** A phase tab containing both a `.md` and a `.html` artifact shows both, HTML rendered; requirements HTML appears in the viewer, not only on `/render`.

Key activities:
- Extend the markdown-only gate (`api_artifacts.py:52`) and the phase-tab glob (`api_goals.py` `get_phase_tab`) to admit `.html`; pass HTML through verbatim instead of `md.markdown()`.
- Render HTML via iframe/srcdoc in `macros/markdown_viewer.html`; treat `.html` as a render-class artifact (generated-by stamp, atomic) per `cast-requirements-render` US4.
- Surface refined-requirements HTML in the viewer (consumer #2).
- `/update-spec` on `cast-requirements-render.collab.md`: add the dual md/html viewer behavior + the exploration render consumer + apply the US7 "selectable units, no ids" DOM contract to rendered HTML.

## Phase 3a: N×M Workflow engine + relevance gating + entrypoint (Track A core)
**Outcome:** The starter exploration runs as a Workflow: interactive Phase-1 (intent + decompose +
approval + hat-matrix) hands off to a deterministic N×M fan-out + per-step synthesis barrier, producing
all existing markdown artifacts. Ships in parallel to `cast-explore`.
**Dependencies:** Phase 1a (spike), Phase 2a (single-hat agent)
**Estimated effort:** 3–4 sessions
**Verification:** A full run on a real goal produces `research/{NN}-{step}-{hat}.ai.md` per applicable cell, one playbook per step, and `summary.ai.md`; a forced hat-agent failure drops one cell to `null` without sinking the run.

Key activities:
- Write the Workflow script: `pipeline()` per step → `parallel()` over `M_applicable(step)` hats → per-step synthesis barrier (existing synthesizer, unchanged).
- Implement relevance gating at interactive Phase-1 (compute `M_applicable(step)` from step type/tags; always-on = Contrarian/First Principles/90/10); emit the `hat-matrix` as a Workflow arg.
- Build the entrypoint (skill/command) per the Phase-1a decision; keep `cast-explore` intact alongside.
- Failure isolation (null cell + log, "surface don't suppress" the dropped cells); respect the concurrency cap.

## Phase 3b: Diecast-wide commenting on HTML artifacts (Track B)
**Outcome:** Any HTML artifact in the viewer is annotatable; comments use the `{quoted_text,
section_hint, body}` shape and the same-door API, anchored via verbatim-substring relocation.
**Dependencies:** Phase 2b (and the Phase 1b decision on in-iframe vs full-page)
**Estimated effort:** 2–3 sessions
**Verification:** Selecting text in an HTML artifact and submitting yields a comment via the same-door API; the comment relocates correctly after a re-render via verbatim-substring matching.

Key activities:
- Wire the `/cast-comment-html` injection (or its in-viewer equivalent per the 1b decision) to served HTML artifacts.
- Route comments through the same-door comment API with `anchor_space='render'`; use verbatim-substring relocation (stable anchor-ids deferred, per spec Out of Scope).
- Reuse the displaced-comment / re-anchor machinery (`comment_anchor.py`); accept `block_ref=None` for ref-less containers.

## Phase 4: Exploration WHAT/HOW HTML render (convergence of A + B)
**Outcome:** A completed exploration produces a polished `exploration.html` (WHAT agent → HOW agent →
render-checker), visible in the dual viewer and commentable.
**Dependencies:** Phase 3a (exploration md output), Phase 2b/3b (viewer + commenting)
**Estimated effort:** 2–3 sessions
**Verification:** The exploration render passes the 4-criteria render-checker (all hats visible per step; per-step POV legible at zero-click; hats kept distinct not blended; not AI-slop) and renders in the viewer with working comments.

Key activities:
- Build the exploration content (WHAT) agent — decides what each section conveys, no HTML — and the presentation (HOW) agent — bespoke HTML — modeled on `render_job_service`.
- Implement the exploration render-checker enforcing the 4 locked criteria.
- Lay out the HTML so each step shows its opinionated POV with the distinct hat takes beneath it (distinct, not blended).
- Land `exploration.html` at `goals/{slug}/exploration/exploration.html` (atomic, served-by stamp).

## Phase 5: End-to-end integration & parity validation
**Outcome:** The full pipeline runs unattended after step approval on a real goal, and its output
quality is compared head-to-head against today's `cast-explore` so the user can decide the eventual merge.
**Dependencies:** Phase 4
**Estimated effort:** 1–2 sessions
**Verification:** All nine SC-001…SC-009 pass on a real goal; a side-by-side of the N×M output vs a `cast-explore` run on the same goal is produced for the user's merge decision.

Key activities:
- Run the new pipeline and `cast-explore` on the same goal; compare playbook quality and angle sharpness.
- Verify every Success Criterion; confirm md substrate is byte-compatible with `cast-high-level-planner`.
- Capture parity notes for the user's parallel→merge decision.

## Build Order

```
        ┌─ Phase 1a (spike: Workflow engine) ─────────────┐
        │                                                 ▼
Phase 1 ┤                                   Phase 2a ─► Phase 3a ─┐
(spikes)│                                  (hat agent) (Workflow) │
        │                                                         ▼
        └─ Phase 1b (spike: viewer+comment) ─► Phase 2b ─► Phase 3b ─► Phase 4 ─► Phase 5
                                              (viewer)   (commenting)  (render)  (e2e)
```

**Critical path:** Phase 1a → Phase 2a → Phase 3a → Phase 4 → Phase 5
(Track B — 1b → 2b → 3b — runs in parallel and must land before Phase 4's convergence.)

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Workflow tool can't be cleanly launched from a Diecast starter-task entrypoint (non-interactive/opt-in friction) | High | Phase 1a spike resolves the mechanism before any engine work; fallback = orchestrator-agent with enforced per-hat child isolation |
| `cast-comment-html` selection/commenting doesn't work across the iframe boundary | High | Phase 1b spike tests it first; fallback = full-page render surface (as requirements `/render` today) linked from the viewer |
| N×M token cost balloons on large goals | Med | Relevance gating (always-on = 3 hats) + concurrency cap; surface dropped/queued cells (don't silently suppress) |
| Exploration HTML lacks anchor ids → imprecise re-anchor | Low | Accepted: verbatim-substring relocation per the render spec's US7 "no ids" DOM contract; stable ids deferred |
| 90/10 hat overlaps First Principles after the carve-out | Med | Explicit prompt boundaries already specified (90/10 accepts value as given; First Principles re-litigates value); verify in Phase 2a |
| Extending the artifact viewer regresses existing md rendering | Med | Dual-format dispatch keyed off extension; `.md` path unchanged; regression test the md viewer in Phase 2b |

## Open Questions

- **Entrypoint mechanism** — does the "Run starter exploration" starter-task launch the Workflow via a new main-agent skill/command or a server-side dispatch? Resolved by the Phase 1a spike.
- **In-iframe vs full-page commenting** — if Phase 1b shows iframe commenting is infeasible, do we accept the full-page-render fallback for in-viewer HTML comments? Decision pending the spike.
- **Requirements adoption timing** — does surfacing requirements HTML in-viewer (consumer #2, spec US10/P2) ship in this goal or as a fast-follow? Leaning: include it in Phase 2b since it's the cheapest way to validate the dual viewer against a real render.

## Spec References

- **`cast-requirements-render.collab.md`** — Pillar 3 extends this pipeline. Consistency flags: the dual md/html *viewer* is NEW behavior (today's render serves on its own `/render` page) → `/update-spec` in Phase 2b to add the viewer behavior + exploration render consumer. Conventions reused as-is: US4 "render not authored artifact" (atomic, generated-by stamp) and US7 "selectable units, no ids" DOM contract → applied to `exploration.html`.
- **`cast-requirements-roundtrip.collab.md`** — reference for same-door comment intake; exploration commenting reuses the same door, but write-back round-trip to exploration md is **out of scope** (exploration HTML is a render; comments are feedback only).
- **`cast-workflow-routing.collab.md`** — goal already routed to `new_initiative` (PRD → architecture → phased plan → execute); no routing change in this plan.
