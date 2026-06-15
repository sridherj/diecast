# Step 5 Research — HTML-First Human-Consumption Render (grasp the WHAT in ~2 minutes)

> **Exploration step:** Step 5 of `exploration/steps.ai.md` — *What information architecture and
> visual treatment let an unfamiliar reader state a goal's job/outcome/scope in two minutes
> without opening the raw writeup?*
> **Resolves / serves:** SC-001 (2-minute comprehension), SC-003 (HTML replaces markdown for humans),
> FR-001 (WHAT-before-HOW + Directional section), FR-002 (classification pill), FR-005/FR-006
> (HTML render + L1/L2/L3 + progressive disclosure), FR-007 (keep emitting spec-kit markdown).
> **Author:** cast-web-researcher | **Date:** 2026-06-11 | **Method:** 7-angle research, GO-BROAD.
> **Audience:** the playbook synthesizer + owner. This is a *design-ready* brief — opinionated, cited.

---

## TL;DR — Recommendation

**The hard problem is information architecture, not styling.** SC-001 ("state the WHAT in 2 minutes")
is a *scanning* test, and the research is unanimous that users scan rather than read
([NN/g F-pattern][nng-f]). So the render must be engineered around the way people scan: a
**summary-first / BLUF (bottom-line-up-front) lead**, **assertion-format headings** that carry meaning
on their own, **three sharply-distinct visual levels**, and **everything below the fold deferred behind
progressive disclosure** — never a long page the reader has to plow through.

Concretely, the render is **five composable layers**, top to bottom:

1. **Above-the-fold "Goal Card" (the whole SC-001 surface).** A classification pill + a one-sentence
   **job statement (L1)** + 3–5 **outcome/scope assertions (L2)**, all visible without scrolling, all
   WHAT. A competent stranger should pass the 2-minute test from this card *alone*. Everything else on
   the page is optional depth.
2. **L1/L2/L3 hierarchy**, lifted near-verbatim from the cast-preso* visual toolkit
   (`.slide-title` / `.l1-body` / `.l2-body` / `.source-citation` scale, the `:root` token system),
   with **distinct size + weight + color per level** so the eye ranks content pre-reading
   ([NN/g visual hierarchy][nng-vh]).
3. **Progressive disclosure via native `<details>/<summary>`** — acceptance scenarios, EARS detail,
   rationale, constraints, and full FR/SC tables collapse by default; the summary view stays ≤~50 words
   per block (cast-preso density limits). Disclosure is for *secondary* depth only — never hide the WHAT.
4. **WHAT-before-HOW**, with HOW quarantined into a single, visually-muted, non-binding **"Directional
   ideas" section at the bottom, omitted entirely when the family makes HOW irrelevant** (FR-001, US1
   Scenario 3). Use the toolkit's *question-annotation* (muted/italic) treatment so HOW is visibly
   subordinate to WHAT's *callout* (accent) treatment.
5. **Per-family structural variation** driven by the **block-recipe model** Step 3 lands (not five
   hardcoded layouts): the render is `family → ordered block recipe → HTML`, where each block
   (`problem`, `evidence`, `decision`, `scope`, `question`, `open`) has one canonical visual treatment.
   A bug renders symptom/repro-first; a PRD renders job/scope-first; a stub renders a *prompt-to-begin*,
   not an empty skeleton.

**The store this renders from is decided in Step 2** (DB-canonical element rows → generated renders).
Step 5 consumes that: HTML and the spec-kit markdown (FR-007) are **two pure projections of the same
element rows** — same `rows → render` function the repo already runs for `goal.yaml`/`tasks.md`. The
markdown render is *unchanged* for agents; the HTML render is the net-new human surface. **No framework
migration is needed** — this is server-rendered Jinja with `<details>` and a token stylesheet
(consistent with Step 4's "no React" verdict).

**The single biggest mistake to avoid:** treating "HTML output" as a CSS theming task. If the L1 line
isn't a self-contained assertion of the job, no amount of styling passes the 2-minute test
([NN/g layer-cake scanning][nng-text]).

---

## Why this is the headline thread (and why it's hard)

SC-001 is the *only measurable headline success criterion in the whole goal*, and it is a human-factors
claim: **a stranger states the job/outcome/scope in 2 minutes.** That reframes the work away from
"render markdown as pretty HTML" toward three IA decisions, each backed by decades of UX research:

- **What to surface vs. hide** — progressive disclosure (Nielsen, 1995): show what users *frequently*
  need up front; defer the rest ([NN/g progressive disclosure][nng-pd]).
- **How to rank by level** — visual hierarchy via size/weight/color so the eye sorts content *before*
  reading it ([NN/g visual hierarchy][nng-vh], [Toptal typographic hierarchy][toptal]).
- **What order to lead with** — inverted pyramid / BLUF: most important first, so a reader who stops
  early still leaves with the gist ([NN/g inverted pyramid][nng-ip]).

The render also **varies per family** (Step 3) and must **keep emitting the spec-kit markdown** for
downstream agents (FR-007). Get the IA wrong and the entire goal fails its own headline test even if
comments, versioning, and routing all work.

---

## Angle 1 — Expert Practitioner (information architecture & content design)

**The settled practitioner consensus: people don't read, they scan — so comprehension is engineered by
making the scan land on meaning.** NN/g's eye-tracking corpus is the authority here, and three findings
are load-bearing for SC-001:

1. **Scanning is the default, not the exception.** "People scan online content to determine if it
   offers the information they need; leading with the most important details improves comprehension"
   ([NN/g inverted pyramid][nng-ip]). When users scan in an **F-pattern**, "they miss big chunks of
   content, and the skipped phrases are often as important as those that are read"
   ([NN/g F-pattern][nng-f]). The design implication is not "fight the scan" but "feed it": put meaning
   where the eye goes (top, left, headings).

2. **The "layer-cake" scan is the one to design for.** NN/g identifies four scan patterns; the
   **layer-cake** pattern — reading headings and subheadings while skipping the prose between — is the
   one that correlates with *successful* information-finding ([NN/g text-scanning patterns][nng-text]).
   This is the empirical justification for **assertion-format headings**: if a reader consumes *only*
   the headings, they must still get the whole argument. cast-preso* already enforces exactly this rule
   ("Can someone read ONLY the titles and understand the full argument?" — `visual_toolkit.human.md §5`).
   It is the highest-leverage single rule for the 2-minute test.

3. **BLUF / inverted pyramid is the lead structure.** The inverted pyramid is "a three-tiered diagram
   that forces the most important stuff to the very top"; the reader "can leave the story at any point
   and still understand it" ([NN/g inverted pyramid][nng-ip]; [Wikipedia: inverted pyramid][wiki-ip]).
   For requirements this maps cleanly: **lead with the job statement and outcomes (the WHAT), defer the
   acceptance detail and rationale (the depth).** BLUF is the military/intelligence sibling of the same
   idea — "bottom line up front" — used precisely because decision-makers must grasp the point in
   seconds ([Intelligence inverted-pyramid][intel-ip]).

**Content-design corollaries the render must honor:**
- **Front-load the sentence and the section.** Put the conclusion first in each block, the support after
  — so a half-scan still yields the point.
- **Chunk and label.** Short, labeled blocks beat long prose; the label (heading) does the work for the
  scanner.
- **One idea per unit.** cast-preso's "one idea per slide" becomes "one assertion per requirement block."

**Practitioner verdict:** SC-001 is won or lost on the **lead card + assertion headings**, not on
typography polish. Design the above-the-fold Goal Card so that scanning *only* its headings answers
"what is the job, what's the outcome, what's in/out of scope." Everything else is progressive depth.

**Sources:** [NN/g F-pattern][nng-f] · [NN/g text-scanning / layer-cake][nng-text] · [NN/g inverted
pyramid][nng-ip] · [Wikipedia inverted pyramid][wiki-ip] · [W&M "how we read online"][wm-read]

---

## Angle 2 — Tools & Technologies (what renders the levels + disclosure, on this stack)

**Everything Step 5 needs is server-side HTML + CSS + one native HTML element. No JS framework.**

- **Progressive disclosure = native `<details>/<summary>`.** Zero JS, accessible-by-default,
  print-friendly, and already the toolkit's recommended disclosure primitive (Step 1 §C). The reader
  expands depth on demand; the summary view stays scannable. **Accessibility caveats to bake in**
  (from MDN / a11y guidance): every `<summary>` must have *discernible, visible text* available to
  assistive tech (never `display:none`/`aria-hidden` the label); the state change must be perceivable;
  and expanding pushes content down rather than overlaying, so layout must tolerate reflow
  ([MDN HTML accessibility][mdn-a11y]; [Accessibility Insights summary-name][a11y-summary];
  [DAISY details KB][daisy-details]). For the print/PDF and "show everything" paths, force all
  `<details open>` in `@media print` (the toolkit already does this for fragments — `components.css`
  §5).
- **L1/L2/L3 = the cast-preso token + type scale, lifted as-is.** `theme.css :root` gives
  `--color-bg/text/muted/surface/accent` + callout/question pairs; `typography.css` gives the scale
  (`.slide-title` mono 1.6em/700, `.l1-body` 1.1em/600/text, `.l2-body` 0.9em/400/muted,
  `.source-citation` 0.5em/muted). **Hard rule from the toolkit's own visual checker: never hardcode
  hex — always `var(--color-*)`** so a project can re-brand with a one-line `--color-accent` override
  (`visual_toolkit.human.md §10`). This is the OSS-generalization win (FR-012) for free.
- **Semantic annotation components map perfectly onto requirements metadata.** The toolkit's two
  components (`components.css`) are already the two things a requirements doc needs to distinguish:
  - **`.callout`** (numbered, accent left-border, accent badge) = *"this is asserted / decided"* → use
    for **stated requirements and the job statement**.
  - **`.question-annotation`** (muted left-border, italic, `?` icon) = *"this is open / a risk / not
    binding"* → use for **open questions, gaps, and the Directional (HOW) section**.
  This gives instant pre-reading legibility: accent = commitment, muted = tentative.
- **Renders are generated artifacts, not edited.** Step 2 fixes the mechanism: a
  `_rerender_requirements_html()` mirrors `_rerender_tasks_md()` (`task_service.py:389`), writing the
  HTML to the goal folder with the `<!-- AUTO-GENERATED -->` header convention. The HTML render slots
  into the **same route→template→entity path already used for `goal_detail.html`** (`routes/pages.py`),
  and registers in `PHASE_ARTIFACTS` (`config.py:53–58`) so the existing UI serves it. **Additive, no
  migration.**

**What the toolkit gives that's directly reusable (the render kit):** the `:root` block, the type
scale, the two components, the subtle 40px engineering-grid background (`visual_toolkit §3` — "if
someone asks 'is there a grid?', you got it right"), the **consulting-exhibit** archetype
(action title → evidence bullets with bold leads → source line) as the **canonical requirement-block
shape**, the **compare/contrast** archetype (two-col, muted=out-of-scope / accent=in-scope) for the
**scope block**, and the **build-up-sequence** archetype for ordered/dependency lists.

**Tools verdict:** the render is a Jinja template + a lifted token stylesheet + `<details>`. The
heaviest "technology" decision — does this need React? — was already answered *no* in Step 4, and the
render reconfirms it: static visual hierarchy and native disclosure need no client framework.

**Sources:** [MDN HTML accessibility][mdn-a11y] · [Accessibility Insights — summary name][a11y-summary]
· [DAISY `<details>` KB][daisy-details] · cast-preso `visual_toolkit.human.md`, `theme.css`,
`typography.css`, `components.css`, `consulting-exhibit.html` (repo).

---

## Angle 3 — AI / ML Approaches (render for agents AND humans through one door — FR-013)

The spec demands agents be first-class *consumers* of the render, not just humans (FR-013). Step 5's job
is to keep the two audiences served by **two projections of one structured store**, never two
hand-maintained artifacts:

- **Two renders, one source.** `rows → markdown` (agents, FR-007, *unchanged*) and `rows → HTML`
  (humans, US3). Because both derive from the same element rows (Step 2), they cannot drift — the
  classic failure where a "pretty HTML version" and the "real markdown" disagree is structurally
  impossible. This is the AI-native payoff: an agent that writes a requirement element (US7 write-back)
  gets *both* renders regenerated for free.
- **The classification pill is a structured field, not decoration.** Step 3's classifier emits
  `{family, confidence, reasoning, alt_family}` as front-matter / a row field. The HTML pill renders
  that field; an agent reads the *same* field to route (Step 6). FR-002 (human pill) and FR-013
  (agent-readable) fuse into one data element. The pill should also surface the **confidence-gated
  state** Step 3 designed: ≥0.9 silent pill; 0.5–0.9 pill + "confirm?" affordance; <0.5 two-option
  choice — i.e. the render *shows the uncertainty* instead of asserting a possibly-wrong label.
- **LLM-generated layout is the wrong default — deterministic templates win.** A tempting AI-native
  move is "let the model emit bespoke HTML per goal." Reject it for the canonical render: it sacrifices
  the consistency SC-001 depends on (the layer-cake scan only works if every doc scans the *same way*),
  is non-deterministic (breaks golden-file testing), and re-introduces the FR-007 byte-stability risk.
  **The model's job is to fill blocks with good content (assertion headings, tight L1 lines); the
  template's job is to place and rank them.** This mirrors the cast-preso pipeline split: the
  *what-planner* writes content at levels, the *toolkit* fixes the visual treatment.
- **AI as a comprehension *checker* (validates SC-001 cheaply).** cast-preso ships three independent
  0–1.0 checkers (content/visual/tone) plus an 8-pass compliance checker (Step 1 §C). The directly
  portable criteria — `achieves-stated-outcome`, `one-clear-takeaway` (<5s scan), `l1-l2-hierarchy`,
  `not-generic`, `not-ai-aesthetic` — become an **automated pre-screen for SC-001** before the human
  timed-read test: an LLM judge reads *only the rendered headings + Goal Card* and is asked to state the
  WHAT; if it can't, the render fails before a human ever sees it. This makes SC-001 a CI-cheap gate,
  not only a manual study.

**AI verdict:** keep generation and layout separate — agents/LLMs produce *content at levels*,
deterministic templates produce *the page*. Render the classification as a structured, confidence-aware
field so the same pill serves the human (pill) and the agent (routing key). Reuse the cast-preso checker
rubric as an automated SC-001 pre-screen.

**Sources:** cast-preso `cast-preso-check-{content,visual,tone}.md`, `cast-preso-what-planner.md`,
`cast-preso-compliance-checker.md` (repo) · Step 3 note §3 (confidence-gated classifier) · Step 2 note
(rows → render projections).

---

## Angle 4 — Community & Open Source (who has solved "skim a long structured doc fast")

The render's closest prior art isn't slide decks — it's **developer documentation**, where teams have
spent a decade making dense reference skimmable:

- **Stripe docs — the benchmark for layered disclosure.** Stripe is repeatedly cited as the gold
  standard precisely because it uses a **layered approach "so everyone — from junior developers to
  technical leads — finds the information they need"** ([apidog: Stripe docs][apidog-stripe]). The
  pattern to steal: a **scannable conceptual lead** (what/why, prose-light) with **expandable depth and
  side-by-side reference** beneath — the documentation analog of the Goal Card + `<details>` depth.
- **Diátaxis — "shape follows purpose" formalized.** The dominant 2020s docs framework splits content by
  *user need* (tutorial / how-to / reference / explanation), each with a *different structure and
  language* ([Diátaxis reference][diataxis-ref]; [coderslingo overview][coderslingo]). Stripe, Django,
  Kubernetes, and AWS all map to it. The transferable principle for Step 5: **don't render every family
  the same** — a "reference"-shaped block (the FR/SC tables) reads differently from an
  "explanation"-shaped block (the job statement / rationale), and the render should treat them as
  distinct visual genres. This is the OSS-validated backbone of FR-005 (per-family variation).
- **ADR / MADR — status + supersession as a first-class visual.** The decision-record community renders
  **Status** (proposed/accepted/superseded) prominently and links superseded records forward (Step 1
  §E). For v2's versioned render, surface the **version + converged/unconverged state** as a pill
  alongside classification — a reader must see *"v3, 2 open comments"* at a glance.
- **GitHub issue forms — the pill-with-escape-hatch UX.** GitHub's template chooser shows typed pills
  with descriptions *and always keeps a "blank" escape hatch* (Step 3 §2). The render's classification
  pill should mirror this: a confident, legible label that is **one click to override** — never a
  cage. This is the community-tested guard against the Template-Enforcer anti-pattern *at the render
  layer*.
- **Spec-kit — markdown as the interchange contract.** spec-kit keeps each phase as a markdown artifact
  the next phase reads (Step 1 §E, Step 2 §4). v2's markdown render plays exactly this role for
  downstream agents (FR-007). The HTML render is *additive on top*, not a replacement — the community
  pattern is "structured source → multiple rendered surfaces," which is precisely the Step 2 architecture.

**Community verdict:** the render's real lineage is **layered developer docs (Stripe) + purpose-shaped
structure (Diátaxis) + status-forward decision records (ADR)** — all of which validate
*summary-first + expandable depth + per-purpose shaping*. Borrow Stripe's layering, Diátaxis's
shape-follows-purpose, and GitHub's pill-with-escape-hatch.

**Sources:** [apidog — Stripe docs benchmark][apidog-stripe] · [Diátaxis reference][diataxis-ref] ·
[coderslingo — Diátaxis][coderslingo] · [Decision Lab — progressive disclosure][decisionlab] ·
Step 1 §E + Step 3 §2 (repo).

---

## Angle 5 — Frameworks & Patterns (the named techniques, mapped to render decisions)

| Pattern | What it says | How Step 5 uses it |
|---|---|---|
| **Progressive disclosure** (Nielsen 1995) | Show frequently-needed options up front; defer the rest to a secondary layer; keep the primary list small ([NN/g][nng-pd]) | Goal Card = primary layer (WHAT); `<details>` = secondary layer (acceptance detail, EARS, rationale). |
| **Inverted pyramid / BLUF** | Most important first; reader can stop early and still get the gist ([NN/g][nng-ip]) | Job statement + outcomes lead; HOW + open questions trail. Each block front-loads its conclusion. |
| **Visual hierarchy (size/weight/color)** | The eye ranks before it reads; every design needs ~3 levels — heading, subheading, body — differentiated by size, weight, *and* color ([NN/g][nng-vh]; [Toptal][toptal]) | L1/L2/L3 = the cast-preso scale; **distinctness across all three channels**, not size alone (color is the cheapest differentiator and the most skipped). |
| **Layer-cake scanning** | Successful scanners read headings, skip prose ([NN/g][nng-text]) | Assertion-format headings — the doc must be comprehensible from headings alone. |
| **Squint test / 5-second test** | Blur the page; the most important thing should still dominate | A render passes only if, squinted, the pill + job statement + level-1 assertions are what stand out. Reuse cast-preso `one-clear-takeaway` (<5s) checker. |
| **Miller's Law / chunking** (7±2) | Working memory holds ~a handful of items ([cognitive-load research][readability]) | ≤6 visual elements per block, ≤5 outcome assertions in the Goal Card (toolkit density limits). |
| **Diátaxis (shape follows purpose)** | Different content types need different structures ([Diátaxis][diataxis-ref]) | Per-family block recipes — bug ≠ PRD ≠ research render. |
| **Consulting exhibit (action title + evidence + source)** | Executive-doc convention: claim-as-title, evidence body, provenance line | The canonical **requirement-block** shape (assertion heading → bold-lead bullets → acceptance/source line). |

**Density limits to enforce as render constraints** (cast-preso `visual_toolkit §5`, validated by the
chunking/cognitive-load literature): ≤50 words body per block, ≤15 words per bullet, ≤6 elements per
unit, ≥30% whitespace, min 18pt-equivalent (WCAG AA). Make these **warnings the renderer emits** when a
block exceeds them — a too-dense block is an SC-001 regression, caught at generation time.

**Patterns verdict:** Step 5 is not inventing technique — it is *composing* four well-established
patterns (progressive disclosure + inverted pyramid + visual hierarchy + layer-cake headings) that the
cast-preso toolkit already encodes in CSS. The contribution is wiring them to requirement elements and
per-family recipes.

**Sources:** [NN/g progressive disclosure][nng-pd] · [NN/g inverted pyramid][nng-ip] · [NN/g visual
hierarchy][nng-vh] · [NN/g text-scanning][nng-text] · [Toptal typographic hierarchy][toptal] ·
[Readability / cognitive load][readability] · [Diátaxis][diataxis-ref].

---

## Angle 6 — Contrarian View (where progressive disclosure & "pretty HTML" hurt)

**The sharpest objection: progressive disclosure can *destroy* the 2-minute test instead of enabling
it.** The same NN/g that champions disclosure is its harshest critic when it's misapplied:

- **Hidden content is missed content.** "Valuable content hidden under an accordion may be missed
  altogether; users can't scan collapsed content" ([NN/g accordions on desktop][nng-accordion]). If the
  render collapses anything load-bearing for the WHAT, the reader fails SC-001 *because* of disclosure.
  **Hard rule: the WHAT is never behind a `<details>`. Disclosure is for depth only** (acceptance
  scenarios, EARS phrasing, rationale, full tables). The Goal Card must stand alone, fully expanded.
- **Interaction cost is real.** "Each step — scrolling, scanning headings, deciding, targeting the
  click, waiting — incurs a cost that accumulates; readers treat clicks like currency and resent wasted
  ones" ([NN/g accordions][nng-accordion]). A reader doing the 2-minute test should need **zero clicks**
  to state the WHAT. Disclosure that demands a click to learn the job is a bug.
- **Don't collapse content users need *all* of.** "Avoid accordions when users need most/all of the
  page's content, or need it visible simultaneously for comparison" ([NN/g accordions][nng-accordion]).
  Scope (in vs out) is a comparison — render it **open, side-by-side** (compare/contrast archetype), not
  behind disclosure.
- **"Beautiful HTML" is a vanity trap (SC-003 risk).** SC-003 wants HTML to *replace* markdown for
  humans. The failure mode: a visually rich render that is *slower* to extract the WHAT from than the
  plain markdown was — decorative illustrations, animation, dense multi-column layouts that fight the
  scan. The cast-preso tone/visual checkers exist exactly to catch this (`not-generic`,
  `not-ai-aesthetic`). **Polish that doesn't speed comprehension is negative value.**
- **Family-specific layouts can over-fit and confuse.** If every family renders *radically* differently,
  the reader re-learns the page each time and the layer-cake scan breaks (the scan relies on
  consistency). **Resolve via the block-recipe model:** families differ in *which blocks appear and in
  what order*, but each block has *one* canonical visual treatment everywhere. Variation in content
  selection, consistency in visual grammar.
- **Illustrations are usually decoration.** The toolkit's own rule: "only illustrate when it
  communicates something text can't; decorative fails the checker" (Step 1 §C). For requirements, that
  means **diagrams earn their place only for the heavy-UI (user-flow) and research/architecture
  families** — and even then SVG-with-HTML-overlay-text, ≤5 elements. Default to *no* illustration.

**The steelman for disclosure (why we still use it):** without it, a full PRD render is a wall of text
that *also* fails SC-001 — the reader can't find the WHAT in the noise. The resolution is not
"disclosure yes/no" but **"disclosure boundary"**: WHAT always open, depth always collapsed. That
boundary *is* the design.

**Contrarian verdict:** the render's risk is not "too plain" — it's "WHAT buried behind a click" or
"polish that slows the scan." Enforce: zero clicks to the WHAT; scope rendered open; illustrations only
when they out-communicate text; one visual grammar across families.

**Sources:** [NN/g accordions on desktop][nng-accordion] · [NN/g accordions for complex content][nng-accordion2]
· [UXPin — progressive disclosure best practices][uxpin] · cast-preso visual/tone checkers (repo).

---

## Angle 7 — First Principles (reduce the render to its irreducible job)

**Strip the render to its atom: a render exists to transfer *one model of the work* from the document
into a stranger's head, as cheaply as possible.** SC-001 quantifies "cheaply" as 2 minutes. From first
principles, three primitives must reach the reader's head in that budget — and they are exactly the
three a requirements doc carries (and exactly the three Step 3's first-principles analysis isolated):

1. **What reality are we in?** — the problem/context.
2. **What do we intend to change?** — the job/outcome/scope (the *WHAT*).
3. **What don't we know / what's only a guess?** — open questions and the non-binding HOW.

If the render delivers those three to a competent stranger, it has done its job. Everything else —
illustrations, tables, EARS phrasing, the spec-kit markdown — is either *depth* (defer it) or *for a
different consumer* (the agent, via markdown).

**This yields three irreducible render laws:**

- **Law 1 — Identity of levels = importance, nothing else.** L1 is "what survives a 90% cut" (the job
  statement). L2 is "what survives a 50% cut" (outcomes, scope). L3 is "everything else" (acceptance
  detail, rationale, provenance). The *visual* treatment must be a faithful function of *informational*
  rank — if L2 ever visually competes with L1, the scan misranks and comprehension slows. (This is the
  cast-preso `l1-l2-hierarchy` law, derived here independently.)
- **Law 2 — Front-load at every scale.** The page front-loads (Goal Card first), the section
  front-loads (assertion heading first), the sentence front-loads (conclusion first). The reader who
  stops at *any* scale still leaves with the gist (the inverted-pyramid invariant). This is why BLUF is
  not a style choice but a structural requirement of a time-bounded comprehension test.
- **Law 3 — Confidence must be visible.** A requirements doc that renders a tentative HOW idea with the
  same authority as a committed outcome *lies to the reader* and corrupts the model they build. The
  WHAT/HOW split (FR-001) and the accent-vs-muted treatment are not decoration — they are the render
  telling the truth about *what is decided vs. what is a guess*. Same for the confidence-gated
  classification pill: render certainty as certainty and ambiguity as ambiguity.

**The minimum viable render** (degrades gracefully — matters because the corpus is bimodal: 2-line stubs
or 90-line narratives, Step 1 §D): a classification pill + a one-line job statement + a list of outcome
assertions + (if present) an open-questions block. A *stub* renders this as a **prompt-to-begin**, not
an empty template (Step 1 §D, the "stub is a render-state not a family" finding). A full PRD renders the
same skeleton with every block populated and depth collapsed. **One skeleton, variable fill** — the
render never breaks on sparse input, never pads on rich input.

**Essential vs. convention.** *Essential:* the three primitives; importance-faithful levels;
front-loading at every scale; visible confidence; the WHAT-always-open / depth-always-collapsed
boundary. *Convention:* the specific colors, the 40px grid, IBM Plex Mono, the exact `<details>`
styling, the number of outcome bullets. Build the render on the essentials; treat the cast-preso tokens
as the (excellent, reusable) convention layer.

**First-principles verdict:** the render is "transfer three primitives in 2 minutes." That single job
dictates levels-as-importance, front-loading, and visible confidence — and makes "make it pretty" a
strictly subordinate concern.

**Sources:** Step 3 note §7 (three understanding primitives) · [NN/g inverted pyramid][nng-ip] ·
[NN/g visual hierarchy][nng-vh] · cast-preso `visual_toolkit §5` (repo).

---

## The render design (synthesis — what to build)

### A. The five-layer page

```
┌─────────────────────────────────────────────────────────────┐
│ [ pill: "Bug fix · debug" ]        [ v3 · 2 open comments ]   │  ← classification + version state
│                                                              │
│  L1  Goal Card / Job statement (one sentence, the WHAT)      │  ← .slide-title / .l1-body, accent
│      "Restore child-completion signalling so parent agents   │     ALWAYS visible, never collapsed
│       resume when a delegated child finishes."               │
│                                                              │
│  L2  • Outcome: parent resumes within one poll cycle         │  ← .l1-body bold-lead bullets
│      • In scope: signalling path; Out: retry policy          │  ← compare/contrast for scope
│      • 3–5 assertions, each a complete claim                 │     (squint test passes here)
├─────────────────────────────────────────────────────────────┤
│  ▸ Acceptance scenarios (EARS)            <details, closed>   │  ← L3 depth, progressive disclosure
│  ▸ Symptom / repro / expected-vs-actual   <details, closed>  │     family-specific blocks
│  ▸ Constraints & rationale                <details, closed>  │
│  ▸ Full FR / SC tables                     <details, closed> │
├─────────────────────────────────────────────────────────────┤
│  ? Directional ideas (non-binding HOW)    [muted section]    │  ← question-annotation treatment;
│    "Likely the HX-Trigger toast path — exploration may differ"│    OMITTED ENTIRELY if HOW irrelevant
└─────────────────────────────────────────────────────────────┘
   >cast_                                            (nav marker)
```

### B. L1/L2/L3 system (lift the cast-preso scale; differentiate on all three channels)

| Level | Content (importance rule) | Treatment (from `typography.css`) | Channel distinctness |
|---|---|---|---|
| **L1** | Job statement — *survives a 90% cut* | `.slide-title` mono 1.6em / 700 / `--color-text` + accent pill | largest, heaviest, accent-adjacent |
| **L2** | Outcomes & scope assertions — *survive 50% cut* | `.l1-body` sans 1.1em / 600 / `--color-text` | bold, full-contrast, bullet-led |
| **L3** | Acceptance detail, EARS, rationale | `.l2-body` sans 0.9em / 400 / `--color-muted` | smaller, lighter, muted, inside `<details>` |
| **meta** | Provenance, source, version, IDs | `.source-citation` 0.5em / `--color-muted` | smallest, quietest |

Distinct **size + weight + color** at each step (NN/g: don't rely on size alone — color is the cheapest,
most-skipped differentiator [NN/g visual hierarchy][nng-vh]). Enforce the toolkit's `l1-l2-hierarchy`
rule: **L2 must never visually compete with L1.**

### C. Progressive-disclosure boundary (the load-bearing rule)

- **Always open (the SC-001 surface):** pill, job statement, outcome/scope assertions, version state.
- **Always collapsed (`<details>`):** acceptance scenarios, EARS detail, symptom/repro, constraints,
  rationale, full FR/SC tables, cross-references.
- **Accessibility:** every `<summary>` carries discernible visible text; `@media print` forces all
  `open`; layout tolerates reflow on expand ([MDN][mdn-a11y], [DAISY][daisy-details]).
- **Zero-click invariant:** a reader states the WHAT without expanding anything.

### D. WHAT-before-HOW (FR-001 / US1)

- WHAT leads (job/outcome/scope, accent/`.callout` grammar).
- HOW is confined to a single **"Directional ideas"** section at the bottom, rendered with the
  **`.question-annotation`** muted/italic grammar so it visibly reads as *tentative, non-binding,
  subject to change by exploration*.
- **Omit the section entirely when the family makes HOW irrelevant** (US1 Scenario 3 — e.g. a pure
  data-analysis question). Do not pad it.

### E. Classification pill + per-family variation (FR-002 / FR-005)

- **Pill** renders Step 3's `{family, confidence}` field; confidence-gated (≥0.9 silent / 0.5–0.9
  pill+confirm affordance / <0.5 two-option), one-click overridable (GitHub-issue-forms escape hatch).
- **Per-family = block recipe, not bespoke layout.** The render is `family → ordered [blocks] → HTML`,
  one canonical treatment per block. Indicative recipes (from Step 3 §7 + Step 1 §D corpus):
  - **Bug/debug:** `symptom · repro · expected-vs-actual` open at top → outcome → (HOW usually omitted).
  - **New initiative/PRD:** `job · outcomes · scope(in/out, compare-contrast) · open questions`; richest;
    Directional present.
  - **Small pilot/POC:** one-screen `job · outcome · open`; minimal ceremony.
  - **Data analysis/research:** `question · data sources · expected-output-shape · findings`; **no
    acceptance criteria** (spike rule, Step 3 §1); HOW omitted.
  - **Fuzzy ideation / stub:** loosest — `problem` only; if near-empty, render **prompt-to-begin**, not
    a skeleton (Template-Enforcer guard at the render layer).
  - **(Step 1 §D additions — flag for Step 3):** Testing/QA charter, Refactor/Migration, Personal/Non-eng
    each want their own recipe; v2 may render via generic fallback + noted classification (FR-002 S4).

### F. Illustrations (default: none)

Only when a diagram out-communicates text (toolkit rule): **heavy-UI family** (user-flow diagram) and
**research/architecture** (SVG, `viewBox`, class-named colors, ≤5 elements, **text overlaid in HTML, not
inside the image**, Annie-Ruygt Style-Bible prefix for any raster). Decorative illustration fails the
visual checker and *slows* the scan — reject it.

### G. FR-007 preservation (non-negotiable)

The HTML render is **purely additive**. `rows → markdown` (`refined_requirements.collab.md`, spec-kit
shape) is emitted **unchanged**, gated by Step 2's golden-file test against `bin/cast-spec-checker`. The
HTML is a *second projection* of the same rows — it never becomes the source, never alters the markdown
contract. SC-004 (downstream agents green) is the regression gate.

---

## Validation protocol for SC-001 (the timed-read test)

SC-001 is the acceptance gate; design the test now so the render is built against it.

1. **Automated pre-screen (CI-cheap, run first).** Feed *only* the rendered headings + Goal Card (HTML
   stripped to text) to an LLM judge with the prompt: *"State this goal's job, primary outcome, and
   what's in/out of scope. If you cannot, say what's missing."* Reuse the cast-preso `one-clear-takeaway`
   (<5s scan) and `l1-l2-hierarchy` criteria. Fail → fix before human testing.
2. **Human timed read (the real SC-001).** ≥3 readers unfamiliar with each goal; one goal per priority
   family (≥3 families per the spec). Open the HTML render only (no raw writeup, no markdown). Start a
   2-minute timer. Reader writes the WHAT (job, outcome, scope) in their own words.
3. **Score.** Pass if the reader's WHAT matches the intended job/outcome/scope on all three within 2:00,
   without expanding any `<details>` (the zero-click invariant). Record clicks, scroll, and where the eye
   went first (informal think-aloud).
4. **Family coverage.** Run across families so per-family recipes are each validated — a render that
   passes for a PRD but fails for a bug isn't done.
5. **Regression.** Snapshot passing renders; the golden-file markdown test (FR-007) + the LLM pre-screen
   guard against drift on future changes.

**Failure-mode checklist** (from the contrarian angle): WHAT behind a click; L2 competing with L1; HOW
rendered as authoritative; decorative illustration; family layout so different the scan re-learns;
density over limits.

---

## Open items to flag for plan review

1. **Block recipes depend on Step 3's final taxonomy.** Step 1 §D argues 5 families → ~8 (add
   Testing/QA, Refactor/Migration, Personal/Non-eng; Spike first-class). The render's recipe table must
   consume whatever Step 3 lands — built data-driven (`family → blocks`), so adding a family is a config
   change, not a template rewrite.
2. **Pill confidence display.** Confirm the three-tier confidence UX (silent / confirm / choose) is what
   the owner wants surfaced in the render vs. handled only in the agent interaction.
3. **Disclosure default per family.** Recommended: WHAT open, depth collapsed, *everywhere*. Confirm the
   owner is OK with acceptance scenarios collapsed-by-default for the heavier families (a reviewer doing
   *review* — not the 2-min skim — will expand them; a "expand all" control + print-forces-open covers
   the rest).
4. **Illustration scope for v2.** Recommend shipping the render with **no illustrations** in the first
   pass (default-none); add the heavy-UI user-flow diagram and research/architecture SVG as a later
   per-family increment. Confirm.
5. **SC-001 study logistics.** Who are the ≥3 unfamiliar readers (the OSS-generalization constraint means
   they should *not* all be the maintainer)?

---

## Sources

**Codebase / prior-step (primary evidence):**
- `skills/claude-code/cast-preso-visual-toolkit/visual_toolkit.human.md` — token system, type scale,
  density limits (§5), grid (§3), archetype catalog (§9), override pattern (§10)
- `.../templates/css/{theme,typography,components}.css` — `:root` tokens, `.slide-title/.l1-body/.l2-body/.source-citation`, `.callout`, `.question-annotation`
- `.../templates/slide-archetypes/{consulting-exhibit,compare-contrast,build-up-sequence}.html` — requirement-block / scope / dependency layouts
- `agents/cast-preso-check-{content,visual,tone}.md`, `cast-preso-compliance-checker.md` — render validation rubric (SC-001 pre-screen)
- `cast-server/cast_server/services/task_service.py:389,428` — `rows → render` + `# AUTO-GENERATED` header (the HTML render mirrors this)
- `cast-server/cast_server/routes/pages.py`, `config.py:53–58` — Jinja page path + `PHASE_ARTIFACTS` registry
- `exploration/research/01-…` §C (cast-preso kit) + §D (corpus: bimodal length, stub-as-render-state, per-family structure); `02-canonical-source-of-truth.ai.md` (rows → renders, FR-007 golden test); `03-workflow-classification-taxonomy.ai.md` §3/§7 (confidence-gated pill, blocks-not-templates, three primitives)

**Web (external corroboration):**
- [NN/g — Progressive Disclosure][nng-pd]
- [NN/g — Inverted Pyramid: Writing for Comprehension][nng-ip]
- [NN/g — Visual Hierarchy: UX Definition][nng-vh]
- [NN/g — F-Shaped Pattern of Reading][nng-f]
- [NN/g — Text Scanning Patterns (layer-cake)][nng-text]
- [NN/g — Accordions on Desktop: When and How][nng-accordion]
- [NN/g — Accordions for Complex Content][nng-accordion2]
- [Wikipedia — Inverted pyramid (journalism)][wiki-ip]
- [Intelligence writing — inverted pyramid / BLUF][intel-ip]
- [W&M Swem Library — How People Read Online][wm-read]
- [Toptal — Structuring Effective Typographic Hierarchy][toptal]
- [MDN — HTML: A good basis for accessibility (`<details>/<summary>`)][mdn-a11y]
- [Accessibility Insights — summary discernible text][a11y-summary]
- [DAISY KB — `<details>` accessibility/reflow caveats][daisy-details]
- [apidog — Why Stripe's API Docs Are the Benchmark][apidog-stripe]
- [Diátaxis — Reference / shape-follows-purpose][diataxis-ref]
- [coderslingo — The 4 Types of Documentation (Diátaxis)][coderslingo]
- [The Decision Lab — Progressive Disclosure][decisionlab]
- [UXPin — Progressive Disclosure best practices][uxpin]
- [Readability Matters — reduce cognitive load / working memory][readability]

[nng-pd]: https://www.nngroup.com/videos/progressive-disclosure/
[nng-ip]: https://www.nngroup.com/articles/inverted-pyramid/
[nng-vh]: https://www.nngroup.com/articles/visual-hierarchy-ux-definition/
[nng-f]: https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/
[nng-text]: https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/
[nng-accordion]: https://www.nngroup.com/articles/accordions-on-desktop/
[nng-accordion2]: https://www.nngroup.com/articles/accordions-complex-content/
[wiki-ip]: https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)
[intel-ip]: https://intelligenceshop.com/2021/07/08/the-inverted-pyramid/
[wm-read]: https://guides.libraries.wm.edu/writing-for-web/how-we-read-online
[toptal]: https://www.toptal.com/designers/typography/typographic-hierarchy
[mdn-a11y]: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML
[a11y-summary]: https://accessibilityinsights.io/info-examples/web/summary-name/
[daisy-details]: https://kb.daisy.org/publishing/docs/html/details.html
[apidog-stripe]: https://apidog.com/blog/stripe-docs/
[diataxis-ref]: https://diataxis.fr/reference/
[coderslingo]: https://coderslingo.com/blog/diataxis-framework-documentation/
[decisionlab]: https://thedecisionlab.com/reference-guide/design/progressive-disclosure
[uxpin]: https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/
[readability]: https://readabilitymatters.org/articles/increase-readability-reduce-cognitive-load
