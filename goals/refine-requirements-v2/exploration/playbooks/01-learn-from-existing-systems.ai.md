# Step 1: Learn from Existing Systems & the Maintainer's Corpus — Playbook

> Synthesis of Research Note 01 (web) + Code Exploration 01 (codebase) into an opinionated,
> actionable prior-art brief. This is the **intelligence step**: it does not build, it
> *decides what the build steps inherit*. Every later step (2–7) should execute from the
> verdicts below instead of re-mining the corpus.
> **Agent:** cast-playbook-synthesizer · **Date:** 2026-06-11 · **Status:** ai

---

## TL;DR

**Don't greenfield this — assemble it.** Diecast already runs two production artifact patterns
(DB-canonical render for goals/tasks; file-canonical for requirements), gstack's `/spec` is a
battle-tested authoring loop, and `cast-preso*` is a working HTML information-architecture
library you can lift nearly verbatim. The build reduces to **one net-new primitive — stable
element IDs (`id="req-NNN"`) — plus three thin DB sidecar tables (versions, comments, routing)
keyed to it.** The single highest-leverage insight: stable element identity is the keystone that
*every* downstream feature (comments, diffs, change summaries, round-trip provenance,
cross-references) consumes — get it right once and the rest become plain rows; get it wrong and
every feature degrades to fragile text-anchor matching. Three of the goal's loudest assumptions
are also refuted by evidence here: a DB-entity rewrite is the *wrong* (heavier) choice, React is
almost certainly unnecessary, and the 5-family taxonomy is only ~56% right.

---

## Recommended Stack

The Step-1 deliverable is a set of **adopt/build/reject decisions** that pin the stack for Steps
2–7. One pick per concern, defended.

| Concern | Pick | Why (and why not the alternative) |
|---------|------|-----------------------------------|
| Canonical store | **Hybrid: files stay canonical + thin DB sidecar** | Keeps FR-007 (downstream markdown contract) free; DB-entity rewrite is *more* migration for no payoff. Spec-Kit + the gap analysis both vote file-canonical. |
| Element identity | **`id="req-NNN"` assigned at generation time** + `TextQuoteSelector` fuzzy fallback | Survives edits to surrounding content; char-offset anchoring shifts on any upstream edit. This is the keystone primitive — nothing else exists today. |
| Annotation tech | **Vanilla-JS annotator on SSR HTML** (recogito/text-annotator-js or @duckyb/annotator) | Kills the React premise. All mature libs run on server-rendered DOM; a SPA migration balloons scope for zero functional gain. |
| Render kit | **Lift `cast-preso-visual-toolkit` CSS tokens + L1/L2/L3 scale + checkers** | A working in-house IA library already solves headline-comprehension; building a new one is waste. Retune density numbers (slides ≠ docs). |
| Authoring loop | **Port gstack `/spec` phased gate + `/office-hours` adversarial reviewer** | Near-exact prior art for AI-native refinement; Diecast's child-delegation makes the reviewer subagent trivial to wire. |
| Comment lifecycle | **GitHub three-state threads (Open → Addressed → Resolved)** | Binary open/resolved (Notion/Google) loses the reviewer-vs-author actor distinction the iteration loop needs. |
| Versioning semantics | **ADR-style immutable supersede + explicit snapshots** | Auto-version-on-save (Google/Confluence) produces noise; ADR "new version supersedes old" matches US5 archival cleanly. |
| Taxonomy axis | **~8 inferred families + generic fallback + confirm-on-ambiguity** | 5 hardcoded boxes miss Testing/Refactor/Personal; the maintainer never labels family, so infer-with-confidence, never user-pick. |

---

## Implementation Steps

These are the **synthesis actions** Step 1 hands forward — each is a decision to carry into a
later step, with the evidence already gathered so that step doesn't re-research.

### Step 1: Name the two patterns Diecast already runs — and pick Pattern B
**Impact: High** | **Effort: 0 (decision already supported by evidence)**

Diecast runs Pattern A (DB-canonical, file is a disposable one-way render — `goal.yaml` via
`goal_service.py:337-363`, `tasks.md` via `task_service.py:389-455`, full re-render on every
mutation) *and* Pattern B (file-canonical, DB stores only a path pointer — every
`*.collab.md`/`*.human.md`, `tasks.task_artifacts` JSON in `schema.sql:35`). The requirements
artifacts this goal is about live entirely in **Pattern B today**.

**Verdict for Step 2:** do NOT promote requirements to DB entities (Pattern A). Keep human-facing
content file-canonical and add a thin DB layer for what files can't do. This preserves FR-007 for
free (the file *is* already the spec-kit markdown downstream agents read) and is the lowest
migration cost. Imitate Pattern A's *convention* (generated-render header, write-on-change,
`PHASE_ARTIFACTS` registry in `config.py:53-58`) — not its goal/task *schema*.

```
# The hybrid, concretely (Step 2's starting point):
refined_requirements.collab.md   # canonical, file-side, spec-kit shape (FR-007 preserved)
refined_requirements.html        # generated render, file-side (add to PHASE_ARTIFACTS)
DB sidecar (new tables):
  artifact_versions   (id, goal_slug, artifact, version, snapshot_ref, change_summary, created_at)
  artifact_comments   (id, element_id, anchor_quote, body, status, author, thread_parent, created_at)
  artifact_routing    (goal_slug, family, workflow_handle, decided_at)   # Step 6
```

### Step 2: Treat stable element IDs as the keystone — design them first
**Impact: High** | **Effort: feeds Step 2's primary deliverable**

Every angle of both research notes converges on this: comments, version diffs, change summaries,
and round-trip provenance all reduce to **one durable element identity that survives edits and
re-renders.** Diecast has goal slugs (`_slugify`, not collision-guarded) and task ints — but
**no element-level ID exists anywhere today.** This is the single biggest gap.

Assign `id="req-NNN"` (or `US-NN`/`FR-NNN`/`SC-NNN`) to each requirement block **at generation
time**, with W3C `TextQuoteSelector` (exact + 32-char prefix/suffix) as the fuzzy fallback when an
ID is missing. This is FR-008 and it gates Steps 4, 5, and 7. Resolve it before any annotation or
versioning design — they are *consumers* of it, not peers.

### Step 3: Adopt the W3C Web Annotation model — and kill the React premise
**Impact: High** | **Effort: feeds Step 4's decisive verdict**

The "Google-Docs comments ⇒ React/Next.js SPA" assumption is a **false premise**, confirmed by
four independent mature libraries that all run on server-rendered HTML: Hypothesis (3-tier
selector fallback), `@duckyb/annotator` (framework-agnostic TS), recogito/text-annotator-js
(vanilla, `overrideId` for server IDs), Velt (commercial). The W3C Web Annotation Data Model
(standard since 2017) defines the shape: a comment is `{target: element-id, body, state}`.

**Verdict for Step 4:** No React. Element-ID-anchored comments + vanilla-JS annotator on the
existing FastAPI+Jinja stack is sufficient. Comment model:
`{ anchor(element-id + TextQuoteSelector fallback), status(Open/Addressed/Resolved), author,
created_at, thread[replies] }`. Use **three-state** (GitHub PR model), not binary. Versions are
**explicit snapshots with required change summaries**, never auto-version-on-save.

### Step 4: Widen the taxonomy to ~8 families — inferred, never user-labeled
**Impact: High** | **Effort: feeds Step 3 taxonomy validation**

Two independent corpus tallies (22 docs web-side, 27 docs code-side) agree the proposed 5
families capture only **~45–56%** of real writeups. The missing first-class families, both
corpus-confirmed *and* industry-confirmed (Shape Up "chore"/"spike", universal Feature/Bug/Chore/
Spike/Epic set):

1. **Testing / QA charter** — biggest unrepresented cluster (E2E harnesses, red-test-then-fix).
2. **Refactor / Migration / chore** — before/after state + Definition of Done, not user stories.
3. **Personal / Non-eng** — the tool is a life-OS too (trips, comms, GTM); needs different render.
4. **Spike** as first-class — fact-finding, **no acceptance criteria** (conflating it with a
   feature is an anti-pattern).

Two corrections that matter more than the family count: **"stub" is a render-state, not a family**
(detect at render → show prompt-to-begin, never an empty template), and **classification must be
inferred with a confidence signal + confirm-on-ambiguity** (FR-004), because the maintainer
*never labels* family — it's inferable from structural signals (symptom+repro=bug;
before/after-schema=refactor; question→data→output=research). Also model **domain** (software /
research / life-admin / positioning) as a *separate axis* from work-type.

### Step 5: Lift the cast-preso render kit nearly verbatim
**Impact: High** | **Effort: feeds Step 5; mostly adoption, not invention**

`cast-preso-visual-toolkit` is a ready-to-lift library, not just inspiration. Adopt directly:

- **CSS token block** (`theme.css :root`) — drop in, override only `--color-accent`. Hard rule
  (enforced by the visual checker): never hardcode hex, always `var(--color-*)`.
- **L1/L2/L3 scale** already classed: `.slide-title` (assertion heading) / `.l1-body` (survives
  50% cut) / `.l2-body` (first to cut) / `.source-citation` (acceptance criteria/provenance).
- **Two semantic components** map perfectly onto requirements metadata: numbered accent
  **callout** = "this is decided"; muted italic **question-annotation** ("?") = "this is open."
- **Assertion-format headings** + the "read ONLY the headings and understand the argument" test —
  the highest-leverage single rule for SC-001's 2-minute comprehension.
- **Progressive disclosure via native `<details>/<summary>`** with a `callout=none`-style static
  fallback for print/search/accessibility.
- **Consulting-Exhibit archetype = the default requirement block** (assertion title → scope
  sentence → evidence bullets → source line; "no orphan data" ↔ "no requirement without
  rationale").
- **Three-dimension checker harness** (content/visual/tone, each `{dimension, verdict, score,
  issues[]}` with `what_good_looks_like` + `what_worked`) — reuse the schema + AI-slop criteria
  (em-dashes = hard fail, GPT-ism ban).

**Retune, don't copy:** drop the per-slide density caps (≤50 words, ≥30% whitespace are projector
constraints); a dense doc needs ≥3 hierarchy tiers (MoSCoW) + traceability IDs.

### Step 6: Port six gbrain refinement upgrades (free quality wins)
**Impact: Medium** | **Effort: ~1 day of agent-prompt edits, independent of the render build**

second-brain's `taskos-refine-requirements` lineage is *ahead* of Diecast's
`cast-refine-requirements`. Six high-leverage imports sharpen the refinement brain independent of
the render/comments/versioning build — quick wins that de-risk the whole goal:

| Import | Why it matters |
|--------|----------------|
| Stage-adaptive framework (vague→JTBD; specific→Example-Mapping; near-complete→EARS) | The exact "Template Enforcer" guard the spec fears — no premature EARS on half-formed ideas |
| Explicit exit conditions + log gaps in Open Questions when budget exhausts | No silent low-confidence sections |
| Decisions section (Chose / Over / Because, dated) | Captures conversation choices that otherwise vanish; pairs with versioning |
| Adversarial meta-pass ("what would an engineer reject?") | Surfaces contradictions, unmeasurable constraints, circular open questions |
| Evidence-quoting mandate for confidence scores (cite draft text) | Removes the "didn't bother checking" failure mode |
| Scope-mode detection from signal words (MVP/comprehensive/dream) | Calibrates scenario depth early |

Plus the gstack `/spec` HARD GATE ("no output after first message, always start Phase 1"), the
`/office-hours` adversarial reviewer subagent (5-dim 1-10, max-3 iterations, fail-soft), and the
0-10 rate→gap→fix→re-rate loop for the comment/iteration UX (US4).

### Step 7: Adopt the right negative knowledge from external tools
**Impact: Medium** | **Effort: 0 (decisions, recorded here for Steps 2/4/7)**

The external survey supplies anti-patterns to design *against*: Notion's version-retention cap
(US5 wants archival without loss), Google Docs' unreliable programmatic anchoring (→ favor stable
IDs over text ranges), Confluence's per-edit version noise (→ explicit snapshots), and the
notebook-rot cautionary tale (without disciplined provenance + conflict surfacing, a "living"
doc degrades *faster* than a static one — directly relevant to US7). ADR immutability (new record
supersedes, old gets only a "Superseded by" link) is the model for US5/US7 provenance.

---

## Architecture / Process Flow

How Step 1's verdicts feed the dependent steps:

```
                        STEP 1 (this brief) — the intelligence layer
                                       │
   ┌───────────────┬──────────────────┼──────────────────┬─────────────────┐
   ▼               ▼                  ▼                  ▼                 ▼
 §A Diecast     §B gbrain          §C cast-preso       §D corpus         §E external
 DB patterns    refine upgrades    render kit          family tally      prior art
   │               │                  │                  │                 │
   │ "Pattern B     │ 6 imports        │ tokens + L1/L2    │ 5→~8 families    │ W3C anno,
   │  + sidecar"    │ (agent quality)  │ + checkers        │ infer+confirm    │ ADR, 3-state
   ▼               ▼                  ▼                  ▼                 ▼
┌─────────┐   ┌──────────────┐   ┌──────────┐      ┌──────────┐     ┌──────────┐
│ STEP 2  │   │ refine-req   │   │ STEP 5   │      │ STEP 3   │     │ STEP 4   │
│ store + │   │ agent upgrade│   │ HTML     │      │ taxonomy │     │ comments │
│ stable  │◀──┤ (parallel,   │   │ render   │◀─────┤ +template│────▶│ +version │
│ IDs ★   │   │  free win)   │   │          │      │          │     │ (no React)│
└────┬────┘   └──────────────┘   └──────────┘      └────┬─────┘     └────┬─────┘
     │  stable IDs are the keystone every box below consumes              │
     ├───────────────────────────┬──────────────────────────────────────┤
     ▼                           ▼                                       ▼
┌──────────┐              ┌──────────┐                            ┌──────────┐
│ STEP 6   │              │ STEP 7   │                            │ change   │
│ router   │              │ round-   │                            │ summary  │
│ (record  │              │ trip /   │◀───────────────────────────┤ = stable │
│ on goal) │              │ living   │   reuses Step 4 diff        │ -ID diff │
└──────────┘              └──────────┘                            └──────────┘

★ = the keystone. Get stable element IDs right and 4/6/7 become plain DB rows.
```

---

## Key Decisions

| Decision | Recommendation | Rationale (what's traded off) |
|----------|----------------|-------------------------------|
| DB-entity rewrite vs file-canonical + sidecar | **File-canonical + thin DB sidecar** | Trades a "cleaner" DB model for keeping FR-007 free and minimal migration. The downstream markdown contract is the constraint that wins. |
| Stable-ID scheme | **Generation-time `id="req-NNN"` + TextQuoteSelector fallback** | Trades a tiny generation-time cost for edit-survivable anchors. Char-offset anchoring is rejected outright (shifts on any edit). |
| React/Next.js migration | **No — vanilla JS on SSR DOM** | Trades a "modern" SPA for not ballooning scope. Four mature libs prove SSR is sufficient; the migration buys nothing functional. |
| Comment lifecycle states | **Three-state (Open/Addressed/Resolved)** | Trades binary simplicity for the reviewer-vs-author actor distinction the iteration loop genuinely needs. |
| Versioning trigger | **Explicit snapshot + required change summary** | Trades auto-save convenience for signal-over-noise. Confluence/Google auto-versioning is the named anti-pattern. |
| Taxonomy size & method | **~8 families, inferred w/ confidence, confirm-on-ambiguity** | Trades the owner's tidy 5 for empirical fit (~56%→full). User-pick rejected: the maintainer never labels. |
| "Stub" handling | **Render-state (prompt-to-begin), not a family** | Trades a taxonomy box for correct UX on sparse input — multiple 2-line stubs appear across families. |
| Render kit | **Reuse cast-preso toolkit, retune density** | Trades bespoke control for a working library. Building new IA from scratch is the waste to avoid. |
| gbrain refinement upgrades | **Port the six; run in parallel with the build** | Trades nothing — they're independent agent-prompt edits that de-risk quality early. |
| Agent parity (FR-013) | **Comments/versions/routing = plain data+API rows** | Trades a GUI-first build for a same-door human+agent contract. Bolting an API on later = rebuild. |

---

## Pitfalls to Avoid

1. **Copying the goal/task DB schema for requirements.** Pattern A's *schema* assumes clean
   entities; requirements are file-canonical blobs the DB has never seen content of. Copy the
   *convention* (render header, write-on-change, registry), not the tables — or you build new
   infrastructure mislabeled as "extending the existing pattern."

2. **Inheriting the React rewrite premise unexamined.** The spec itself flags this; the evidence
   refutes it. Design annotation on the existing stack first and only escalate to a SPA if a UX
   prototype *proves* it's needed (it almost certainly won't).

3. **Cementing five hardcoded family boxes.** For an OSS product (FR-012) tuned to a
   three-workspace corpus skewed toward second-brain/linkedout, five boxes will make external
   users feel their work doesn't fit. Ship families + a generic fallback + a re-classify path,
   and validate against *external* users before locking.

4. **Forcing structure onto the "random ideas" family — the Template Enforcer.** The loosest
   family must stay loose; never force EARS scenarios onto raw ideation. The gbrain stage-adaptive
   framework is the concrete guard. Over-structuring ideation kills the very thing it captures.

5. **Char-offset-only comment anchoring.** Any upstream edit shifts every offset and orphans every
   comment. Stable element IDs + a quote-selector fallback are non-negotiable; this is the
   fragility that makes or breaks the whole iteration loop.

6. **Auto-versioning on every save.** Produces Confluence/Google-style noise where reviewers can't
   tell a typo fix from a scope change. Require explicit snapshots with a change summary; the
   summary is a stable-ID element diff, not a prose re-description.

7. **Silent file/DB divergence.** `_update_goal_yaml_fields` already commits the DB *then* no-ops
   on a missing file (`goal_service.py`), and `tasks.md` full re-render obliterates external edits.
   Any sidecar must content-hash or structurally parse to detect drift — don't inherit the silent
   divergence footgun.

8. **Treating a notebook as a spec for the research family.** Jupyter/Observable have no
   versioning, no acceptance criteria, and cell-order dependency — architecturally incompatible.
   Borrow the *inline-output-in-context* display only; keep spec structure (question → hypotheses
   → findings → conclusions → follow-up).

9. **Building comments/versions/routing as a human GUI with an agent API bolted on later.** FR-013
   demands the same door. If the human UI and an agent don't POST to the identical data+API
   contract, it gets rebuilt — the difference between v2 and v4.

10. **Generalizing the taxonomy from this corpus alone.** Most diecast `refined_requirements.
    collab.md` are empty stubs; the refined-shape signal lives in second-brain/linkedout. Weight
    this skew before cementing families for the OSS constraint — flagged for human attention.

---

## Success Metrics

- **Pattern coverage clarity**: Step 2 can name exactly which of Pattern A/B requirements use
  today and why the hybrid is chosen — target: trade-off matrix with ≥5 dimensions, decision-ready
  for owner sign-off.
- **Keystone resolved before consumers**: stable-ID scheme (FR-008) is specified *before* Step 4
  annotation or Step 7 round-trip design begins — target: zero downstream design that assumes text
  anchoring.
- **React question closed with evidence**: Step 4 emits an explicit "React required? No + why"
  verdict citing ≥3 SSR-compatible libraries — target: decision made, not deferred.
- **Taxonomy empirically grounded**: Step 3 classifies against the ~49-doc combined corpus tally,
  not intuition — target: ≥8 families with a generic fallback and a documented Template-Enforcer
  guard.
- **Render kit reuse**: Step 5 cites specific cast-preso artifacts adopted (token block, L1/L2/L3
  classes, ≥3 archetypes, checker schema) — target: <30% net-new CSS/IA invention.
- **Refinement upgrades shipped in parallel**: ≥4 of the 6 gbrain imports land as agent-prompt
  edits independent of the render build — target: quality de-risked before the keystone build.
- **Citations carry through**: every later step cites this brief instead of re-researching —
  target: zero duplicate corpus/external research in Steps 2–7.

---

## Impact Rating: 9/10

**Justification:** Step 1 is foundational by design — it runs first and every later step is meant
to cite it. Its synthesis doesn't just gather facts; it *refutes three of the goal's biggest
assumptions with evidence* (DB-entity rewrite is wrong, React is unnecessary, the 5-family
taxonomy is ~half-right) and *names the true keystone* (stable element IDs) before any design
spend. That redirection is worth more than the brief's weight in research: it prevents the two
most expensive reversible mistakes (wrong canonical store, fragile anchoring) and hands Steps 2–7
adopt/build/reject verdicts they can execute from directly. Docked one point only because the
final decisions (store trade-off matrix, React UX prototype, taxonomy lock) are correctly left to
the owning steps — Step 1 supplies the inputs and the strong prior, not the signed-off call.
