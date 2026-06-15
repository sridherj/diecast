# Goal: Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement

**Domain:** Developer-tooling / requirements engineering / AI-native authoring systems (document data-modeling, information architecture, dev-productivity UX)
**Scope:** Multi-week exploration → design → incremental build; v2 ships the data model + render + classifier + router *seam* (pipelines stubbed)
**Date:** 2026-06-11

> This decomposition seeds a research pipeline. Each step below is an independent
> **web-research + code-exploration target**. Steps are framed as *problems to solve*,
> not components to build. All 6 of the refined spec's open questions are mapped to a
> resolving step (see "Open-Question Coverage" at the end).

---

## Multi-Lens Insights

Insights from expert / contrarian / data / 10x analysis that shaped this decomposition —
the things a naive "build an HTML generator + a comments box" plan would miss entirely:

- **Stable element identity is the real keystone, not HTML.** Comments, version diffs,
  change summaries, downstream round-trip provenance, and cross-references *all* reduce to
  one primitive: every requirement element (US/FR/SC) needs a durable ID that survives
  edits and re-renders. Get that wrong and every other feature becomes fragile text-anchor
  matching. This is why the canonical-store decision (Step 2) must precede annotation,
  versioning, and round-trip work — they are consumers of it, not peers.

- **The framework-migration question is probably a false premise.** Everyone assumes
  "Google-Docs-style comments ⇒ React/Next.js SPA." The contrarian read: if elements carry
  stable IDs and the server renders anchored DOM nodes, comments can be plain DB rows keyed
  to element IDs, layered onto the existing FastAPI+Jinja stack with a sprinkle of vanilla
  JS. The exploration's job is to *kill or confirm* the rewrite assumption with evidence,
  not inherit it.

- **There is rich historical data to mine before designing anything.** Diecast already
  solved "DB-canonical with auto-generated file renders" for goals and tasks — that pattern
  is sitting in the codebase as a working precedent for the architecture decision. The
  maintainer has a *corpus* of real writeups across three workspaces
  (second-brain, linkedout-oss, diecast) that is ground-truth for validating the 5-family
  taxonomy empirically instead of by intuition. And cast-preso* skills are a working library
  of progressive-disclosure / visual-hierarchy patterns. A senior mines all of this *first*.

- **"Classify into families" can quietly become the Template Enforcer anti-pattern.** The
  spec already names this risk. The contrarian sharpening: the *axis* of classification may
  be wrong. Owner's five families are shaped by "what document layout do I need?" — but work
  could equally be classified by uncertainty/risk, by decision-reversibility, or by
  producer-vs-consumer. Validate the taxonomy axis against how other communities actually
  cut this (PRD vs RFC vs ADR vs spike vs notebook) before cementing five boxes.

- **The 10x move is agent-first, not human-first-then-retrofit.** The spec demands agents be
  first-class producers and consumers (FR-013). If comments/versions/routing are built as a
  human GUI feature and an agent API is bolted on later, it gets rebuilt. Designing the
  comment/version/router mechanism as a plain data+API contract that a human UI *and* an
  agent both call through the same door is the difference between v2 and v4.

- **"Living source of truth" is the feature that makes this more than a doc generator.** A
  requirements file that silently goes stale the moment exploration finds a new constraint
  is just a pretty README. The round-trip write-back (Step 7) — provenance, notification,
  conflict surfacing — is what makes requirements *canonical* rather than *initial*.

---

## Step 1: How to learn from existing systems and the maintainer's own corpus before designing?

**What:** Before committing to any architecture, taxonomy, or render, mine the prior art
that already exists — Diecast's own working DB-canonical pattern, the gbrain/second-brain
requirements handling, cast-preso* presentation patterns, the maintainer's real writeup
corpus across three workspaces, and the external landscape (Linear/Notion/Jira specs,
GitHub spec-kit, ADR/RFC/PRD conventions, Jupyter/observable for research-type work). The
problem: *what has already been solved here, and what does the ground-truth data say about
the owner's intuitions?*

**Why:** Skipping this produces a plan built on assumptions. The owner's 5-family taxonomy,
the DB-vs-files instinct, and the "needs React" worry are all hypotheses that existing
evidence can confirm or refute cheaply — *before* expensive design work bakes them in.
Diecast literally already implements "DB-canonical, generated file renders" for goals/tasks;
designing the requirements store without studying that precedent risks reinventing (or
contradicting) it. This is the explicit gbrain open question, and it de-risks Steps 2 and 3.

**Success looks like:** A prior-art brief that (a) documents how Diecast's goal/task
DB-canonical+render pattern works and whether it's reusable for requirements; (b) reports
gbrain's portable requirements-handling ideas with a keep/drop verdict each; (c) catalogs
reusable cast-preso* visual-hierarchy/progressive-disclosure patterns; (d) tabulates the
maintainer's real writeups by apparent workflow family (ground-truth for Step 3); and
(e) summarizes how 4–6 external tools/communities model requirement docs, comments, and
versioning. Every later step can cite this brief instead of re-researching.

**Dependencies:** None (foundational; runs first).

### Substeps
1. Code-explore Diecast's existing goal/task entities, renderers, and file-generation path; extract the reusable "DB-canonical → generated renders" mechanics and its limits.
2. Survey `~/workspace/second-brain` (gbrain) for requirements-handling ideas worth porting; produce a keep/drop list with rationale.
3. Inventory cast-preso* skills for transferable presentation patterns (hierarchy levels, progressive disclosure, illustration use, slide archetypes).
4. Sample the maintainer's writeup corpus across the three workspaces and bucket each by likely workflow family — this becomes empirical input to the taxonomy validation in Step 3.
5. Web-research external prior art: PRD/RFC/ADR/spike templates, spec-kit, Linear/Notion/Jira doc+comment+version models, notebook-style research artifacts — extract patterns and anti-patterns.

---

## Step 2: What should be the canonical source of truth for requirements? (PRIMARY)

**What:** Resolve the keystone architecture question: are requirements **DB entities with
auto-generated HTML + markdown renders** (mirroring Diecast's goal/task pattern), or do
**files stay canonical with a thin DB layer only for comments/versions**? Within that,
decide the **stable-ID scheme** for every requirement element (US/FR/SC) and the **archival
mechanism** for superseded versions. The problem: *where does truth live, and how do
elements keep a durable identity across edits, renders, and versions?*

**Why:** This is the decision everything else hangs off. Annotations (Step 4), version
diffing and change summaries (Step 4), archival (US5), and downstream round-trip provenance
(Step 7) are all *consumers* of stable element identity and a canonical store. Choosing
wrong is the most expensive mistake to reverse — it forces a re-architecture of every
dependent feature. The owner explicitly deferred this to exploration as the primary target;
the archive-mechanism question (DB vs folder) is explicitly coupled to it and resolved here.
A weak answer here caps the ceiling of the entire goal.

**Success looks like:** A recommendation (with trade-off table) for canonical store + stable-ID
scheme + archive mechanism, validated against three pressures: (1) the existing downstream
contract — planner/task-suggester/spec-checker must keep consuming spec-kit markdown
unchanged (FR-007); (2) stable IDs must survive re-renders and edits well enough to anchor
comments and diffs (FR-008); (3) the chosen store must make versioning/archival natural,
not bolted on. The recommendation names exactly what changes in the codebase and what the
migration path is, and is decision-ready for owner sign-off at plan review.

**Dependencies:** Step 1 (reuses Diecast's DB-canonical precedent and external storage models).

### Substeps
1. Specify both architectures concretely (entities, tables, render pipeline, migration) and build a trade-off matrix across edit-stability, agent-writability, versioning, downstream-contract preservation, and implementation cost.
2. Design the stable-ID scheme for US/FR/SC elements (allocation, persistence across edits, use as comment anchors and cross-reference targets) — FR-008.
3. Decide the archive mechanism (DB rows vs archive folder) for superseded versions, ensuring comments + resolution state travel with the archived version (US5); resolve jointly with the store choice.
4. Verify the chosen store keeps the spec-kit markdown render byte-compatible enough that planner/task-suggester/spec-checker run unchanged (FR-007, SC-004); define the regression check.

---

## Step 3: How to classify work into families and shape the document per family without becoming a Template Enforcer?

**What:** Validate the owner's five priority families (new initiative/PRD, small pilot/POC,
bug fix/debug, data analysis/research, random ideas/exploration) against how other teams and
OSS communities actually classify work, then design per-family *document* templates plus the
classifier itself. The problem: *what are the right families for an open-source product, and
how do we shape each requirements document to its family without forcing rigid structure
onto fuzzy ideation?*

**Why:** This shapes the most visible output — the document organization and the
classification pill at the top. Get the taxonomy wrong and an OSS product's users feel their
work doesn't fit; over-structure the "random ideas" family and you kill ideation (the
explicitly-named Template Enforcer anti-pattern). Because this is product not personal
tooling (FR-012), the families and templates must generalize beyond the maintainer's three
workspaces — which is exactly why Step 1's corpus and external survey feed this. This step
defines US2's document shaping, *separate from* the downstream routing in Step 6.

**Success looks like:** A validated family taxonomy (the five, adjusted by external evidence,
with an explicit generic fallback for unmatched work — FR-002/FR-003 Scenario 4); one
first-class document template per family with sections/ordering/visual treatment; a classifier
design that surfaces the detected family as a pill and *asks the user to confirm when
ambiguous* rather than guessing (FR-004); and a documented guard against the Template
Enforcer (how the loosest "ideas" family stays unstructured). Per-family inspiration templates
researched online are cited. Long-tail families (add-tests, heavy-UI-flow, PRD-only) are
designed-for but flagged out of v2 scope.

**Dependencies:** Step 1 (corpus + external classification survey). Informs Steps 5 and 6.

### Substeps
1. Cross-check the five families against external work-classification schemes (PRD vs RFC vs ADR vs spike vs notebook; how Linear/Shape-Up/etc. cut work types); confirm, merge, or re-cut the axis.
2. Design one document template per family (section set, ordering, emphasis) and the generic fallback shape.
3. Design the classifier: signals it reads, how it surfaces the family pill, and the confirm-on-ambiguity clarifying-question behavior (FR-004).
4. Define the Template-Enforcer guard: explicit rules for keeping the "random ideas/exploration" family loose and refusing to force scenarios onto raw ideation.
5. Web-research and collect per-family inspiration templates as design references.

---

## Step 4: How to let humans AND agents annotate and iterate on a spec without forcing a framework rewrite?

**What:** Design the inline-comment / annotation experience (Google-Docs-style, anchored to
specific requirement elements), the open/resolved lifecycle, the version progression
(v2/v3… driven by unresolved comments), and the per-version change summary — and answer
the standing question of whether this genuinely requires migrating off FastAPI+Jinja to
React/Next.js or whether standard JS annotation libraries / element-anchored comments on
stable IDs suffice. The problem: *how do reviewers (human or agent) leave durable, anchored
feedback that drives the next version, on the lightest stack that actually works?*

**Why:** This is the iteration engine (US4/US5) and the second of the goal's three threads
(faster iteration). Without anchored comments and delta change-summaries, review collapses
back to manual markdown edits and chat re-explanations (the exact thing SC-002 measures
against). The framework question is a major cost fork: an unnecessary React migration would
balloon scope, while wrongly avoiding it would produce a clunky UX — so the exploration must
*decide it with evidence*, not assume. And per FR-013, the mechanism must be designed so an
agent can comment/resolve/version through the *same door* as a human, or it gets rebuilt later.

**Success looks like:** A recommended annotation approach (named libraries or a
stable-ID-anchored server-rendered design) with an explicit verdict on the React/Next.js
question and its justification (FR-009); a comment data model with open/resolved state and a
retained resolution trail (FR-010); a versioning flow where open comments mark the spec
unconverged and produce the next version; a change-summary design that diffs stable-ID
elements between versions (FR-017); and an explicit demonstration that the same
comment/version API is callable by an agent, not just the GUI (FR-013). Single-writer /
async — no realtime collaborative editing (out of scope).

**Dependencies:** Step 2 (stable IDs + canonical store + archival). Feeds Step 7's change-summary surface.

### Substeps
1. Research standard JS annotation/commenting libraries and element-anchored-comment patterns; evaluate each against the FastAPI+Jinja stack and produce the explicit "React/Next.js required? yes/no + why" verdict.
2. Design the comment data model (anchor to stable element ID, open/resolved state, resolution trail) — FR-009/FR-010.
3. Design the version-progression flow: open comments ⇒ unconverged ⇒ produce v_n+1; resolution marking carried across versions.
4. Design the change-summary generator as a stable-ID element diff between versions (FR-017), reusable by Step 7's round-trip provenance.
5. Define the agent-parity contract: the exact same comment/version operations exposed as an API an agent calls identically to the human UI (FR-013).

---

## Step 5: How to make a reader grasp the WHAT of a goal in ~2 minutes?

**What:** Design the HTML-first human-consumption render — progressive disclosure (summary
first, details expandable), L1/L2/L3 visual hierarchy with distinct color/size/design per
level, WHAT-before-HOW ordering with HOW confined to a marked "Directional" section, the
classification pill, and illustrations — mining cast-preso* patterns for inspiration. The
problem: *what information architecture and visual treatment let an unfamiliar reader state
a goal's job/outcome/scope in two minutes without opening the raw writeup?*

**Why:** This is the headline thread (faster comprehension) and the single measurable success
criterion (SC-001: 2-minute comprehension; SC-003: HTML replaces markdown for humans). "HTML
output" framed as styling misses the point — the hard problem is *information architecture*:
what to surface, what to hide behind progressive disclosure, how to rank by level. WHAT/HOW
separation (US1) lives here in the render. Get this wrong and the whole goal fails its own
headline test even if every other piece works. The render also varies per family (Step 3),
so it must consume the family templates rather than hardcode one layout.

**Success looks like:** An HTML render design that leads with WHAT and confines HOW to a
visually-distinct non-binding "Directional ideas" section, omitted entirely when irrelevant
(FR-001, US1 Scenario 3); applies L1/L2/L3 level-based visual treatments and progressive
disclosure (FR-006); displays the classification pill (FR-002); varies structure per family
(FR-005, US3 Scenario 3); and *continues emitting the spec-kit markdown render* for
downstream agents unchanged (FR-007). Validated by a timed-read test: 3+ readers state the
WHAT within 2 minutes across multiple families (SC-001). cast-preso* patterns reused are cited.

**Dependencies:** Step 2 (render pipeline + canonical store), Step 3 (per-family templates). Reuses Step 1's cast-preso inventory.

### Substeps
1. Design the L1/L2/L3 hierarchy system: what content maps to each level and the distinct color/size/design treatment per level.
2. Design progressive disclosure: what shows in the 2-minute summary view vs. what collapses behind expand affordances.
3. Render the WHAT/HOW separation: WHAT-led layout + visually distinct, non-binding "Directional" section, omitted when the family makes HOW irrelevant (US1).
4. Integrate the classification pill and per-family structural variation (consume Step 3 templates).
5. Specify illustration use and adapt concrete cast-preso* patterns; define the timed-read validation protocol for SC-001.

---

## Step 6: How to route a classified goal into the right downstream workflow from any phase?

**What:** Design the phase-agnostic workflow router: given a goal's classification, resolve a
family-specific downstream-workflow handle (bug → logs→RCA→confirm→fix/test; prototype →
spike→demo→learnings; etc.), record the routing decision on the goal, and make the router
invokable from *any* phase — not only after requirements. Decide the seam: does
classify+route live *inside* cast-refine-requirements or get *extracted* as a standalone
agent/service that refinement (and later, other phases) call? v2 ships the seam + named
pipeline **stubs**, not the pipelines. The problem: *where does the router live, and how does
any phase ask "what workflow does this goal belong in?" without re-running refinement?*

**Why:** This is the third thread (workflow routing) and the most architecturally future-loaded.
Phase-agnostic invocation (FR-016) strongly implies extraction — bury the router inside the
refinement agent and you can't call it from planning or execution later without a rewrite.
Shipping stubs behind a stable seam (FR-015) lets each real family pipeline land incrementally
as a later goal without re-opening this interface. Skipping the clean seam now means every
future pipeline re-litigates the boundary. Note the separation from Step 3: Step 3 shapes the
*document*; Step 6 routes the *goal into downstream work* — same classification, two distinct
effects (US2 vs US6).

**Success looks like:** A router design that resolves a family → downstream-workflow handle,
records the decision on the goal (FR-014), and routes unimplemented families to a **named
stub** (not a failure or silent generic fallback) that lists the intended steps (FR-015,
US6 Scenario 2); a decided seam boundary (inside-agent vs standalone service) with rationale,
resolving the router-placement open question; phase-agnostic invocation that re-resolves from
the goal's current classification without re-refinement (FR-016, US6 Scenario 3); and
update-on-reclassification behavior that surfaces the changed downstream workflow (US6
Scenario 4). Validated by tracing routing across one goal per family + one cross-phase
re-invocation (SC-005). v2 explicitly does *not* build the pipelines or wire non-requirements
phases (out of scope) — only the seam + stubs.

**Dependencies:** Step 3 (classification taxonomy). Architecturally consistent with Step 2's store (routing decision is recorded on the goal).

### Substeps
1. Decide router placement (extracted standalone phase-agnostic agent/service vs. inside cast-refine-requirements) with rationale — resolves the open question.
2. Design the router interface: classification → downstream-workflow handle, recorded on the goal (FR-014).
3. Design the stable seam + named stubs per family (steps enumerated, e.g. bug: logs→RCA→confirm→fix/test) so real pipelines drop in later (FR-015).
4. Design phase-agnostic invocation: any phase resolves routing from current classification without re-refinement (FR-016); handle reclassification updates (US6 Scenario 4).
5. Define the agent-as-caller contract so a future agent invokes the router through the same door as the requirements phase (FR-013).

---

## Step 7: How to keep requirements a living source of truth as downstream phases change them?

**What:** Design the round-trip mechanism by which downstream phases (exploration, planning,
execution) write requirement-affecting changes *back* into the requirements artifact — with
provenance (which phase/agent originated it), user notification (what changed, from where),
inclusion in the version change summary, and conflict surfacing instead of silent overwrite.
The problem: *how do requirements stay current with the work instead of silently drifting
stale the moment a downstream phase discovers something new?*

**Why:** This is the constraint that makes requirements *canonical* rather than merely
*initial* (US7, FR-018). Without it, the requirements file is a pretty snapshot that's wrong
by the second planning session — and the owner explicitly wants requirements to "never
silently drift out of date relative to the work." The hard parts are provenance and conflict
handling: a write-back with no source attribution is untraceable, and a silent overwrite of a
human-authored requirement is a data-loss bug. This rides on Step 2's canonical store and
Step 4's change-summary machinery — it is the payoff that ties them together. It's also a
prime agent-as-producer surface (FR-013): downstream *agents* are the typical write-back
source.

**Success looks like:** A round-trip design where a downstream-originated change lands in the
requirements files (e.g., appended additions or annotated edits) rather than living only in a
downstream artifact (FR-018, US7 Scenario 1); a user notification describing what changed and
the originating phase/source (FR-019); provenance preserved and rendered in the version change
summary so the write-back reviews as a delta (FR-020, reusing Step 4's diff); and conflict
surfacing — a downstream change that contradicts an existing requirement is raised to the user,
never silently overwritten (US7 Scenario 4). Validated by tracing one downstream change
end-to-end into the files + notification (SC-006).

**Dependencies:** Step 2 (canonical store / write target), Step 4 (change-summary + version machinery).

### Substeps
1. Design the write-back path: how a downstream phase appends/annotates the requirements artifact (additions, not silent rewrites) — FR-018.
2. Design provenance capture: tag each write-back with originating phase/agent, surfaced in the version change summary (FR-020, reuse Step 4 diff).
3. Design the user notification: what changed + where it came from, delivered when requirements update from a downstream source (FR-019).
4. Design conflict detection + surfacing: contradicting changes raised to the user rather than silently overwritten (US7 Scenario 4).
5. Define the agent-as-source contract: a downstream agent triggers write-back through the same mechanism a human edit would (FR-013).

---

## Open-Question Coverage (traceability)

The refined spec flagged 6 open questions for exploration to resolve. Each maps to a step:

| Open question (from refined_requirements.collab.md) | Resolving step |
|------------------------------------------------------|----------------|
| Canonical source of truth — DB-entities-with-renders vs files-canonical-with-DB-comment-layer | **Step 2** (primary) |
| Router placement — inside cast-refine-requirements vs extracted standalone phase-agnostic agent/service | **Step 6** |
| Annotation approach — JS libraries vs element-anchored stable-ID comments vs React/Next.js migration | **Step 4** |
| Archive mechanism — archive folder vs DB for old versions | **Step 2** (resolved jointly with the store) |
| gbrain improvements — portable requirements-handling ideas | **Step 1** |
| Classification taxonomy validation — five families validated against external users | **Step 3** |

**Sequencing rationale:** Step 1 (learn from existing systems + corpus) is the data/intelligence
step and runs first. Step 2 (canonical store + stable IDs) is the keystone every dependent
feature consumes, so it precedes annotation (4), router-recording (6), and round-trip (7).
Step 3 (taxonomy) gates both the per-family render (5) and the router (6). Steps 5, 6, 7 are
the build-facing problems and depend on the architecture + taxonomy decisions landing first.
