---
status: refined
scope_mode: hold
classification:
  family: new_initiative
  confirmed_by: user
  classified_at: '2026-06-20'
  taxonomy_version: 1
confidence:
  intent: high
  behavior: medium
  constraints: high
  out_of_scope: high
open_unknowns: 0
questions_asked: 7
---

# Exploration Pipeline: N×M Workflow + 90/10 Hat + Diecast HTML Surface

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** goals/exploration-pipeline-nxm-claude-workflow-9010-angle/requirements.human.md
> **Origin anchor:** ~/workspace/second-brain (exploration-agent-design.md, web-researcher-angle-fanout.md)

## Intent

The **starter exploration** (today: the `cast-explore` pipeline) takes any goal, decomposes it into
problem-framed steps, researches each step through multiple **generative "thinking hats"** — idea-
surfacing lenses meant to find ways to *do things differently / faster*, **never review/scoring
lenses** — then synthesizes opinionated, actionable per-step playbooks *"worth printing and pinning
to the wall."* This generative, idea-finding model is the whole point of exploration and is anchored
in the second-brain origin; it is not borrowed and not negotiable.

This goal does three things:

1. **Realizes the origin's already-documented angle-independence principle.** Per
   `web-researcher-angle-fanout.md:10`, the *"sequential single-context approach causes
   priming/pollution — earlier angles bias later ones. The contrarian angle gets watered down…
   first principles thinking gets contaminated."* Today's pipeline still researches all hats inside
   ONE per-step context. This goal fans research out across **N steps × M hats as isolated clean-
   context agents**, orchestrated by a deterministic Claude **Workflow**.
2. **Promotes the latent "90/10 solution" value to a first-class hat.** Today it is a buried sub-
   bullet inside the First Principles research hat and the decomposer's 10x lens. It becomes its own
   isolated, clean-context hat.
3. **Makes dual md/html rendering + commenting a Diecast-wide artifact capability** — exploration is
   the marquee new HTML producer; refined-requirements is consumer #2; other artifacts inherit it.

**JTBD:** *"When I start a new goal, I want each hat's take on each step researched in its own clean
context (no cross-priming), still synthesized into opinionated per-step playbooks, and surfaced as a
polished HTML report I can read and annotate anywhere in Diecast — including an explicit 90/10
'laziest-path-to-most-of-the-value' hat."*

## User Stories

### US1 — Isolated N×M research fan-out (Priority: P1)
**As a** goal owner, **I want** each `(step, hat)` researched by its own clean-context agent, **so
that** hats don't cross-prime each other and each perspective stays sharp.
**Independent test:** two hat-agent prompts for the same step share no hat-specific framing; no agent
sees another hat's output before producing its own.
**Acceptance scenarios:**
- **S1:** WHEN the autonomous phase runs, THE SYSTEM SHALL invoke one agent per applicable `(step, hat)` cell.
- **S2:** WHEN a hat-agent is prompted, THE SYSTEM SHALL include only that step and that hat's framing.

### US2 — Deterministic Workflow orchestration (Priority: P1)
**As a** maintainer, **I want** the autonomous research+synthesis phase orchestrated by a Workflow
script, **so that** fan-out/barriers are deterministic instead of hand-rolled child delegation.
**Independent test:** the autonomous phase is launched via the Workflow tool, not `/cast-child-delegation`.
**Acceptance scenarios:**
- **S1:** WHEN the autonomous phase begins, THE SYSTEM SHALL drive fan-out and the synthesis barrier from a deterministic Workflow script.

### US3 — First-class 90/10 hat (Priority: P1)
**As a** goal owner, **I want** a dedicated 90/10 hat, **so that** every step gets a clean-context
deep dive on the laziest-high-value path instead of a buried one-liner.
**Independent test:** a `…-90-10.ai.md` note exists per step; the First Principles note contains no
80/20 content.
**Acceptance scenarios:**
- **S1:** WHEN researching a step, THE SYSTEM SHALL accept the step's value as given and propose the cheapest viable path to ~90% of it.
- **S2:** WHEN the cheap cut is disqualified (hard-10%-is-the-moat, regulated/trust-critical, irreversible), THE SYSTEM SHALL flag it rather than recommend the cut.

### US4 — Relevance-gated matrix (Priority: P2)
**As a** goal owner, **I want** only applicable hats to run per step, **so that** cost stays
controlled and low-signal notes don't bloat synthesis.
**Independent test:** for a pure-strategy step, gateable hats (e.g. Tool Landscape, AI-Native) are
absent while always-on hats are present.
**Acceptance scenarios:**
- **S1:** WHEN a step is not relevant to a gateable hat, THE SYSTEM SHALL omit that `(step, hat)` cell from the fan-out.
- **S2:** WHEN gating any step, THE SYSTEM SHALL always include the Contrarian, First Principles, and 90/10 hats.

### US5 — Per-step synthesis unchanged (Priority: P2)
**As a** goal owner, **I want** the existing per-step synthesizer preserved (one synthesizer per step
→ one opinionated playbook), **so that** the actionable-playbook deliverable is unchanged; only the
research layer gains the hat dimension.
**Independent test:** exactly one playbook file is produced per step, as today.
**Acceptance scenarios:**
- **S1:** WHEN a step's hat notes are complete, THE SYSTEM SHALL synthesize them into exactly one opinionated playbook for that step.

### US6 — Markdown substrate preserved (Priority: P2)
**As a** downstream planner, **I want** all existing md artifacts still produced at existing paths,
**so that** `cast-high-level-planner` consumes them unchanged. (HTML is additive, not a replacement.)
**Independent test:** `exploration/research/*.ai.md`, `playbooks/*.ai.md`, and `summary.ai.md` exist at their current paths after a run.
**Acceptance scenarios:**
- **S1:** WHEN the pipeline finishes, THE SYSTEM SHALL have written every existing markdown artifact at its current path and shape.

### US7 — General WHAT/HOW HTML render capability (Priority: P1)
**As a** Diecast user, **I want** a content agent (decides WHAT each section conveys, no HTML) + a
presentation agent (renders bespoke HTML) + a render-checker, **so that** any artifact can become a
polished HTML view — modeled on the v3 requirements renderer (`render_job_service.py`).
**Independent test:** the content agent emits no HTML; the presentation agent emits one self-contained
HTML doc; the render-checker returns a verdict.
**Acceptance scenarios:**
- **S1:** WHEN an artifact is rendered to HTML, THE SYSTEM SHALL split content (WHAT agent) from presentation (HOW agent) and gate the result with a render-checker.

### US8 — Dual md/html artifact viewer (Priority: P1)
**As a** Diecast user, **I want** the artifact viewer to render both `.md` (as today) and `.html`
(via iframe/srcdoc) in the phase-tab surface where md shows now, **so that** I see polished HTML in
place without leaving the viewer.
**Independent test:** opening a phase tab with both a `.md` and a `.html` artifact shows both, the HTML rendered.
**Acceptance scenarios:**
- **S1:** WHEN a phase tab contains a `.html` artifact, THE SYSTEM SHALL render it via iframe/srcdoc alongside any `.md` artifacts.

### US9 — Diecast-wide commenting (Priority: P1)
**As a** Diecast user, **I want** to select text in any HTML artifact and leave a comment, **so that**
I can give feedback inline. Comments use the `/cast-comment-html` `{quoted_text, section_hint, body}`
shape and the same-door re-anchor API.
**Independent test:** a text selection in an HTML artifact produces a comment row via the same-door API.
**Acceptance scenarios:**
- **S1:** WHEN a user selects text in an HTML artifact and submits a comment, THE SYSTEM SHALL persist it via the same-door re-anchor API in the `{quoted_text, section_hint, body}` shape.

### US10 — refined-requirements HTML in-viewer (Priority: P2)
**As a** Diecast user, **I want** the refined-requirements render (today exiled to
`/goals/{slug}/render`) surfaced in the dual viewer, **so that** HTML+commenting is uniform across
Diecast. Requirements is consumer #2; exploration is consumer #1.
**Independent test:** the refined-requirements HTML appears in the artifact viewer, not only on the separate `/render` page.
**Acceptance scenarios:**
- **S1:** WHEN a goal has a refined-requirements HTML render, THE SYSTEM SHALL surface it in the dual artifact viewer.

### US11 — Interactive Phase-1 stays with the main agent (Priority: P2)
**As a** goal owner, **I want** intent + decompose + step approval + hat-matrix computation to happen
before the Workflow launches, **so that** human-in-loop decisions precede the non-interactive run;
approved steps + the `hat-matrix` pass in as Workflow `args`.
**Independent test:** the Workflow is launched only after step approval, receiving the approved steps + hat-matrix as args.
**Acceptance scenarios:**
- **S1:** WHEN the user approves the decomposition, THE SYSTEM SHALL launch the Workflow with the approved steps and computed hat-matrix as args.

### US12 — Failure isolation (Priority: P3)
**As a** goal owner, **I want** a failed hat-agent to drop that cell to `null` (logged), **so that**
one bad cell never sinks the step or the run; the playbook synthesizes from surviving hats.
**Independent test:** with one hat-agent forced to fail, the run completes and the step's playbook is still produced.
**Acceptance scenarios:**
- **S1:** WHEN a hat-agent fails, THE SYSTEM SHALL log it, drop that cell to `null`, and continue synthesizing the step from the surviving hats.

## The 8 Hats (M_total = 8)

| # | Hat | Generative question | Gating |
|---|-----|---------------------|--------|
| 1 | Expert Practitioner | "How do the world's best people/orgs do this?" | gateable |
| 2 | Tool/Product Landscape | "Best tools — how do they really compare?" | gateable |
| 3 | AI-Native/Innovation | "What's newly possible with AI that wasn't 2 years ago?" | gateable |
| 4 | Community Wisdom | "What do practitioners who've actually done this say?" | gateable |
| 5 | Framework/Methodology | "What structured approaches exist?" | gateable |
| 6 | Contrarian | "What does the majority get wrong?" | **always-on** |
| 7 | First Principles | "From scratch, physics-only — what would you do? What IS the value here?" | **always-on** |
| 8 | **90/10 Solution (NEW)** | "Wearing the 90/10 hat: what gets ~90% of this step's value for ~10% of effort?" | **always-on** |

### The 90/10 hat (detail)

Generative framing (Buchheit, verbatim): *"accomplish 90% of what you want with only 10% of the
work/effort/time… a 90% solution available right away beats a 100% solution that takes ages."* The
hat is a **builder proposing the laziest viable path**, not an auditor. It **accepts the step's value
as given** and optimizes effort to reach it.

**Always asks (6):**
1. What's the laziest path to ~90% of this step's value? The ONE thing the user must be able to do for it to count as working?
2. What can be hardcoded / faked (Wizard-of-Oz) / manualized (concierge) / bought (no-code) instead of built?
3. What's the embarrassing-but-shippable v0, and what gets cut to reach it?
4. Is this a real 90/10 or a disguised 50/50? (Ninety-Ninety rule; does the remainder still clear the viability floor?)
5. Does the cheap version stay on-path (deferred tail buildable later) or become a load-bearing dead end?
6. Is the cut disqualified? (hard-10%-is-the-moat · regulated/trust-critical · irreversible/one-way-door)

**Note output shape:** core (~90% value) · proposed cut (~10% effort: mechanic + concrete v0 +
deferred tail) · effort estimate (core vs full; flag hidden 50/50) · self-checks
(viability/tail-deferrable/on-path/reversibility) · disqualifiers · deferred-decision log · verdict
(RECOMMENDED CUT | CUT WITH CAUTION | DO NOT CUT) · sources.

**Distinctness:** vs **First Principles** — First Principles re-litigates *what the value is* and may
reframe/shrink the step; 90/10 never re-opens the goal, it finds the cheapest path to the given
value. vs **Contrarian** — Contrarian runs the broad adversarial failure-hunt; 90/10
proposes-a-cut-and-self-checks only enough to keep that cut safe.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The starter-exploration entrypoint launches a **Workflow** for the autonomous phase. | not a child-delegation orchestrator |
| FR-002 | Research fan-out = N steps × `M_applicable(step)` hats; each cell is a separate agent. | |
| FR-003 | Each hat-agent prompt contains ONLY its step + its hat. | angle independence |
| FR-004 | A new lean **single-hat researcher** agent exists, param'd by hat. | reuses the web-fetch/resilient-browser protocol only |
| FR-005 | `M_total = 8` includes the new 90/10 hat; the 80/20 sub-notion is removed from the First Principles **research hat**. | |
| FR-006 | The decomposer's 4-lens set (incl. its "10x" lens) is unchanged. | decomposition-time device, not a research hat |
| FR-007 | Relevance gating computes `M_applicable(step)` at interactive Phase-1 from each step's type/tags; always-on hats (Contrarian, First Principles, 90/10) are never gated out; output is a `hat-matrix` (step→hats) passed as a Workflow arg. | mirrors today's code-exploration gating |
| FR-008 | Per-step synthesis is unchanged (one synthesizer per step → one playbook). | |
| FR-009 | All existing md artifacts still produced: `exploration/research/{NN}-{step}-{hat}.ai.md`, `exploration/playbooks/{NN}-{step}.ai.md`, `exploration/summary.ai.md`. | rooted at `goals/{slug}/` |
| FR-010 | A WHAT agent (content) + HOW agent (HTML) + render-checker produce polished HTML, tool-free, gated by Python checks mirroring their contracts; exploration HTML lands at `goals/{slug}/exploration/exploration.html` (atomic write, `served-by` stamp). | models `render_job_service.py` |
| FR-011 | The artifact viewer renders `.html` (iframe/srcdoc) alongside `.md`; the markdown-only gate (`api_artifacts.py:52`) and phase-tab globs (`api_goals.py:~422`) are extended to allow `.html`. | |
| FR-012 | HTML artifacts are servable to `/cast-comment-html`; comments feed the same-door re-anchor API via **verbatim-substring relocation** this round. | stable anchor-ids deferred |
| FR-013 | The refined-requirements HTML render is reachable in the dual viewer (consumer #2). | generalizes the capability |
| FR-014 | Interactive decomposition/approval precede Workflow launch; steps + `hat-matrix` are Workflow `args`. | |
| FR-015 | The Workflow respects the concurrency cap `min(16, cores−2)`; excess cells queue. | |
| FR-016 | A failed hat-agent is logged and drops its cell to `null` without sinking the step or the run. | |
| FR-017 | The exploration render-checker grades 4 criteria: (1) every applicable hat is visible per step; (2) the per-step opinionated POV is legible at the zero-click surface; (3) hat perspectives stay DISTINCT (not prematurely blended); (4) visual quality / not generic AI-slop. | mirrors the requirements render-checker's comprehension+visual structure, adapted to the distinct-hats requirement |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Each step has one research note per applicable hat | count `research/*.ai.md` = Σ `M_applicable(step)` |
| SC-002 | No hat-agent prompt contains another hat's content | prompt inspection |
| SC-003 | A 90/10 note exists for every step; First Principles note has no 80/20 content | file inspection |
| SC-004 | One opinionated playbook per step still produced | count `playbooks/*.ai.md` = N |
| SC-005 | A polished exploration HTML renders and passes the render-checker's 4 criteria | checker verdict |
| SC-006 | The viewer shows both the `.html` report and the `.md` artifacts in the phase tab | UI check |
| SC-007 | Selecting text in any HTML artifact yields a comment via the same-door API | end-to-end |
| SC-008 | refined-requirements HTML is viewable in the dual viewer | UI check |
| SC-009 | A full exploration completes without manual intervention after step approval | run |

## Constraints

- Workflow concurrency caps at `min(16, cores−2)`; worst-case **ungated** bound is `N × M_total`
  (e.g. 5 × 8 = **40** cells) which queues — relevance gating keeps the live set smaller.
- Workflows run **non-interactively** → all human-in-loop steps precede launch; Workflows launch via
  the Workflow **tool**, not as a dispatchable subagent (entrypoint = a skill/command).
- The markdown artifact layout is a hard compatibility contract with `cast-high-level-planner`.
- A full standalone HTML doc cannot be inline-injected into the viewer page (own `<head>/<style>`) →
  **iframe/srcdoc** is required.
- **gstack contributes TECHNIQUES only** (specificity ladder, anti-sycophancy phrasing, [EUREKA]
  tags) — never its "boil-the-ocean" completeness ethos or its review/score/gate **principles**.
- Token cost scales with the matrix; relevance gating is the primary cost control.

## Out of Scope

- Rewriting `cast-high-level-planner` or any downstream consumer; changing `summary.ai.md` format.
- Adding CEO/Viability, Security/Risk, or Eng-Pragmatism hats (90/10 only this round).
- A stable anchor-id scheme for HTML comments (deferred; verbatim-substring relocation this round).
- Changing the per-step synthesis model or the decomposer's lens set.
- Replacing markdown with HTML (HTML is additive visualization).
- Retiring `cast-explore` / big-bang migration (Workflow ships in parallel; user merges later).
- Multi-goal orchestration.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-20 | New goal as home | reuse existing goal / standalone doc | distinct, sizable multi-pillar feature |
| 2026-06-20 | `new_initiative` family | `refactor_migration` | large new design surface warrants full PRD depth |
| 2026-06-20 | Relevance-gated matrix | full Cartesian / user-tunable knob | cost control; matches code-exploration gating precedent |
| 2026-06-20 | Synthesis unchanged (multi-agent split) | perspectives-only / origin-pure | user: "split between diff agents is right" — only research isolation changes |
| 2026-06-20 | 90/10 only (M=8); gstack = techniques only | add CEO/Security/Eng hats | avoid dilution; exact ask |
| 2026-06-20 | Carve 80/20 out of First Principles | leave it embedded | clean angle-independence; 90/10 gets its own clean-context depth |
| 2026-06-20 | Dual md/html; md still produced; HTML additive & Diecast-wide | html-only / md-only / exploration-only | user: "md files will still be produced… html on top… part of entire diecast" |
| 2026-06-20 | HTML rendered in-viewer (iframe/srcdoc) | its own /render-style page | user: "where md is shown now" |
| 2026-06-20 | Verbatim-substring relocation this round | stable anchor-ids now | proven cast-comment-html path; defer ids |
| 2026-06-20 | Workflow ships in parallel to cast-explore | replace autonomous phase outright | user: "have it in parallel — i will take care of merging later" |
| 2026-06-20 | New lean single-hat agent | refactor cast-web-researcher to dual-mode | don't carry forward the 7-in-one-context structure we're retiring |
| 2026-06-20 | Lock exploration render-checker rubric now (4 criteria) | defer to cast-detailed-plan | enough known from the requirements checker's comprehension+visual structure; closes the only open item |

## Open Questions

None — all ambiguities were resolved during refinement (see Decisions). The exploration render-checker
rubric is pinned in the Functional Requirements.
