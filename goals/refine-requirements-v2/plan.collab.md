# High-Level Phasing Plan: Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement

## Overview

This goal evolves `cast-refine-requirements` from a markdown generator into a **workflow-aware,
HTML-first, living requirements system** along three threads: faster *comprehension* (an HTML render
a stranger can grasp in 2 minutes), faster *iteration* (anchored comments → versions → change
summaries), and *workflow routing* (one classification that both shapes the document and routes the
goal into a family-specific downstream pipeline — invokable from any phase).

**The single most plan-shaping fact is an owner decision made *after* exploration** (see
`exploration/summary.ai.md` → "Post-Exploration Decisions"), which **overrides the playbooks where
they conflict**:

> **Canonical store = files-canonical + DB sidecar, at file/coarse-block granularity. NO
> per-requirement element IDs.** Comments and versions anchor at file or coarse-block level, not at
> individual US/FR/SC elements. Change summaries operate at file/block level.

This is a major simplification. Playbooks 02, 04, 05, and 07 were written GO-BROAD around a
**DB-canonical element-row store with stable per-element surrogate IDs (ULIDs)** as "the keystone."
The owner adopted **Playbook 01's leaner recommendation instead** (file stays canonical, thin DB
sidecar for the things files can't do). The consequence threaded through this entire plan: **the
stable-element-ID keystone, scenario-level surrogates, and element-level diff machinery drop out of
v2 scope.** Wherever a playbook says "anchor to `element_uid`," read it as "anchor to a **coarse block
anchor**" in this plan. FR-007 is preserved *for free* because the `.collab.md` file **remains** the
canonical spec-kit markdown — the HTML is a one-way, read-only render *from* the file, not a
projection from a DB.

The new (downscaled) keystone is therefore the **spec-kit parser + coarse block-anchoring scheme**
(Phase 1) — the substrate the render, comments, versioning, and round-trip all consume. Two threads
ride off the critical path: the **router** (Phase 3b, independent of the render) and the **gbrain
refinement-brain upgrades** (Phase 1b, independent agent-prompt edits that de-risk quality early).

FR-016 (phase-agnostic router) is **confirmed** by the owner as a core flow ("users frequently start
a goal as one kind of work and diverge midway"), so the extracted resolver seam is justified.

### Decisions Resolved at Plan Review (owner, 2026-06-11)

These were settled interactively after the first draft and are now baked into the phases below:

1. **Determinism floor = thin spine + Claude re-anchoring.** Reject both a heavy deterministic
   anchoring engine *and* a fully-LLM no-spine design. Keep only three deterministic things — comment
   rows **exist** (DB), **version snapshots**, and **conflict = content-hash compare** — because each
   is a place where being wrong means silent data loss or unauditable state (US7 S4). Everything else
   is a Claude subagent: classify, render, summarize, **re-anchor comments by their stored quote**
   (surfacing genuine orphans), and apply write-backs. **Consequence:** the `heading-path + ordinal`
   anchoring engine is *deleted*; comments store a **quote + section hint** and are re-located by a
   subagent. Comment granularity becomes "wherever the reviewer selected" — no fixed block level. This
   also **resolves the human-edit-model question**: the editable textarea stays, with a Claude
   re-anchor pass on save.
2. **Family set widened to ~8 + generic fallback.** Owner's 5 plus testing/QA, refactor/migration,
   and personal/non-eng (the biggest unrepresented clusters in the owner's own corpus per Playbook 01).
   Spike is a within-family modifier, not a family; "stub" stays a render-state, not a family. Cheap
   because families are block recipes, and it serves FR-012.
3. **Round-trip gate = by blast radius.** Pure additions auto-apply + FYI; modifications to existing
   content gate via `AskUserQuestion`; conflicts always surface. Policy as config, loosenable later.
4. **Illustrations: none in v2.** **Notification surface: unified** — Phase 4 (comments) and Phase 5
   (round-trip) share one HTMX `needs_attention` badge + optional LDN inbox.
5. **SC-001 verification = a `cast-requirements-checker` agent (the AI reader), not outside humans.**
   The human timed-read is deferred for v2. Build a checker *agent* (cousin of `cast-spec-checker` and
   the `cast-preso-check-*` family) that opens the HTML render as an *unfamiliar reader* and tries to
   state the job/outcome/scope from the Goal Card + headings alone — failing the render if it can't.
   This is also the FR-013 win made concrete: an agent consuming requirements the way a human would.
6. **Classification = a standalone `cast-goal-classifier` agent, not an embedded step.** Extract it so
   the seam is phase-agnostic (any phase can reclassify later, per decision #2), but in v2 only
   `cast-refine-requirements` calls it — symmetric with the extracted router resolver. Net: three small
   first-class agents come out of this goal — `cast-goal-classifier`, `cast-requirements-checker`, and
   `cast-requirements-writeback` — alongside the upgraded `cast-refine-requirements`.
7. **Commenting UX = LOCKED** (validated on the Phase-0 spike `prototype/render-demo.html`, owner sign-off
   2026-06-11): select text → a subtle "💬 Comment" pill → an **inline composer anchored to the selection**
   (not a modal, not a rail dialog), placed **below by default and flipped above when the viewport is
   cramped** (GitHub/Google-Docs behavior). Comments store the **quoted text** (not a DOM position),
   highlight via a `<mark>`, carry open/resolved state, and are authored by human *or* agent through the
   same path. Implementation is ~90 lines of **vanilla JS over the existing Jinja+HTMX stack — no
   framework, no annotation library.** Phase 4 builds to this locked interaction.
8. **Version-diff UX = LOCKED** (validated on the same spike, owner sign-off 2026-06-11): a version toggle
   (`Current (vN)` / `Changes since v(N-1)`) reveals **both** (a) a **"What changed" summary panel**
   (`+added · ~modified · −removed`, each item clickable to jump to the change) **and** (b) **inline
   tracked-changes** on the render (green=added, amber=modified with prior text struck, red=removed).
   The diff is **block-level structural set arithmetic** over two parsed version snapshots — matched by
   heading token + content (the same quote/content-matching the comment re-anchor uses, since there are
   no element IDs). The change *set* is deterministic; a subagent may narrate it but never invents it.
   Phase 4 builds the diff engine reusable; Phase 5 round-trip reuses it with a provenance badge.
9. **Re-anchor validation = trust + iterate, NOT a standalone gate** (owner, 2026-06-11). The Claude
   re-anchor subagent (decision #1) is accepted on confidence rather than proven by a separate Phase-0
   Spike B; it is validated and tuned **during Phase 4 implementation**. This is low-risk because
   **orphaning is always surfaced for human triage** — a re-anchor miss never silently loses a comment;
   worst case it's flagged. **Fallback** if it proves flaky in real use: reintroduce a lightweight anchor
   (heading-path / ordinal) for the hard cases, partially reopening decision #1.

---

## Phase 0: Spikes — De-risk Render & Annotation UX
**Outcome:** The riskiest bets are validated (or killed) on **throwaway prototypes** before any
production build — (a) the HTML information architecture actually delivers 2-minute comprehension, and
(b) the thin-spine "store-the-quote + Claude-re-anchor" comment model actually survives file edits.
Each spike ends in a go / adjust decision that feeds the build phases.
**Dependencies:** None (runs first; can overlap Phase 1b).
**Estimated effort:** 1-2 sessions (throwaway code — explicitly *not* production; do not carry it forward).
**Verification:** Each spike hits its named success criterion below; the go/adjust decision is recorded
in the plan or the Phase 1 design note.

Key activities (spikes — throwaway):
- **Spike A — Render comprehension (de-risks Phase 3a / SC-001).** Hand-build ONE HTML render of an
  *existing* real `refined_requirements.collab.md` (this goal's own file is the fixture): Goal Card +
  L1/L2/L3 + `<details>` depth + Directional section, using the cast-preso tokens. **No parser needed —
  hand-write the HTML.** *Success =* the `cast-requirements-checker` rubric (one-clear-takeaway +
  l1-l2-hierarchy) restates job/outcome/scope from the Goal Card + headings alone. *Fail →* rework the
  information architecture before Phase 3a.
- **Spike B — Comment-on-quote + Claude re-anchor (decision #1).** ~~Standalone Phase-0 gate.~~
  **Resolved by owner to trust + iterate (decision #9):** accepted on confidence and validated during
  Phase 4 build rather than proven here first. Safe because orphaning is always surfaced (a miss is
  flagged, never silently lost). Fallback: add a lightweight anchor for hard cases if it proves flaky.
- **Spike C — Vanilla-JS annotation loop on the real stack (confirms "no React").** Wire selection →
  popover → `hx-post` → server fragment swap on the existing FastAPI + Jinja + HTMX stack (can fold
  into Spike A's page). *Success =* a comment can be left and rendered back with **zero** new frontend
  framework; `find cast-server -name package.json` stays empty. *Fail →* escalate the React question
  with prototype evidence (the playbooks bet heavily it won't come to this).
- **Catch-all for further unknowns:** fold any other "prove-it-first" item here as it surfaces (e.g. a
  quick classifier-accuracy eval on the corpus). Phase 0 is the home for unknowns, not Phase 3+.

**Decision gates:** A pass → the corresponding build phase proceeds as planned. B fail is the important
one — it reopens decision #1 (thin spine) and would add a deterministic anchor back into Phase 1.

> ### 🚦 HUMAN GATE — ✅ CLEARED (owner, 2026-06-11)
> Phase 0 was a **gating prototype, not a checkpoint to pass through.** The owner played with the spike
> (`prototype/render-demo.html`) hands-on and **signed off on the render, the commenting UX (decision
> #7), and the version-diff UX (decision #8).** Spikes A (comprehension) and C (no-React annotation
> loop) are validated; Spike B (re-anchor) was resolved to trust + iterate during the build (decision
> #9). **Gate cleared → the build phases below are approved to be detailed and executed.** Remaining
> phase detail is still refined per-phase via `/cast-create-execution-plan`, but the direction is locked.

## Phase 1: Foundation — Spec-Kit Parser & Thin Sidecar Spine
> *(Provisional until the Phase 0 human gate clears — see above.)*
**Outcome:** `refined_requirements.collab.md` parses into an ordered, typed **block model** for
rendering, and a **thin DB spine** exists — comment rows, version snapshots, and content hashes — with
**no deterministic anchoring engine** (comments store a quote + section hint; a subagent re-locates
them). The `.collab.md` file remains byte-canonical (FR-007 untouched). Every later phase consumes this.
**Dependencies:** None (the downscaled keystone — build first).
**Estimated effort:** 1-2 sessions (smaller than the original draft — the anchoring engine is deleted
per the thin-spine decision).
**Verification:** `pytest` — parser produces the expected typed blocks from this goal's own
`refined_requirements.collab.md`; `bin/cast-spec-checker` exits 0 on the file unchanged; a snapshot
test pins the version-snapshot + content-hash behavior.

Key activities:
- **Codify the resolved architecture as a short design note** (`docs/design/` or atop the parser
  module): files-canonical + **thin DB spine** (comment rows / version snapshots / conflict hash), no
  per-element IDs, **no deterministic anchoring engine** — comments are stored with a quote + section
  hint and re-located by a Claude subagent. Record this so future readers don't re-inherit either the
  playbooks' DB-canonical/ULID premise *or* assume a heavy anchor scheme.
- **Build `requirements_render/parser.py`:** read `refined_requirements.collab.md` → ordered typed
  blocks `{kind, level, body}` where `kind ∈ {Intent, UserStory, FR, SC, Constraint, Scope,
  Directional, OpenQuestion}`. Reuse the spec-checker's own regexes (`US_HEADING_RE`, `FR_ID_RE`,
  `SC_ID_RE`, `EARS_SCENARIO_RE`) as the grammar so the parser and the FR-007 contract can never drift.
  This serves the render only — it is **not** a comment-anchoring index.
- **Add the thin DB spine** via the house migration pattern (`db/connection.py` `_run_migrations()` +
  `schema.sql`): `requirement_versions` (file snapshots + a per-version content hash) and
  `requirement_comments` (+ append-only `comment_events` trail). A comment row stores
  `{goal_slug, version, quoted_text, section_hint, state, author, ...}` — **no `block_anchor` column,
  no element surrogate.** Re-location is a runtime subagent step, not a stored key. Defer routing
  columns to Phase 3b and `change_request*` tables to Phase 5.
- **FR-007 read-only guard (golden-file test):** assert that generating the HTML render does **not**
  mutate `.collab.md` bytes and `bin/cast-spec-checker` stays green. Trivial under files-canonical —
  the render only *reads* the file.

---

## Phase 1b: Refinement Brain Upgrades (gbrain imports) — parallel with Phase 1
**Outcome:** `cast-refine-requirements` produces sharper drafts via portable upgrades from
second-brain's `taskos-refine-requirements`, independent of the render/comments/versioning build.
**Dependencies:** None (pure agent-prompt edits; run concurrently with Phase 1).
**Estimated effort:** 1 session (~1 day of prompt edits)
**Verification:** Re-refine 2-3 real writeups (one vague, one near-complete) and confirm the
stage-adaptive behavior, a populated Decisions section, and that the adversarial meta-pass surfaces at
least one real contradiction; no regression in the existing spec-checker pass.

Key activities:
- Import the **stage-adaptive framework** (vague → JTBD; specific → Example-Mapping; near-complete →
  EARS) — this *is* the Template-Enforcer guard the spec fears, applied at the authoring layer.
- Add **explicit exit conditions** + log gaps into Open Questions when budget exhausts (no silent
  low-confidence sections).
- Add a dated **Decisions section** (Chose / Over / Because) — pairs naturally with Phase 4 versioning.
- Add the **adversarial meta-pass** ("what would an engineer reject?") and the **evidence-quoting
  mandate** for confidence scores (cite draft text).
- Add **scope-mode detection** from signal words (MVP / comprehensive / dream).
- Optionally port the gstack `/spec` HARD GATE ("no output before Phase 1") and an `/office-hours`-style
  adversarial reviewer subagent (Diecast child-delegation makes this trivial).

---

## Phase 2: Classification — Family Detection & Block Recipes
**Outcome:** Every goal is classified into a work **family** with a confidence signal; the
classification is surfaced as a pill and persisted as machine-readable front-matter (humans read the
pill, agents read the field). The requirements document is shaped by a **composable block-recipe**
model, not rigid per-family templates — and the loosest "random idea" family is the structural floor.
**Dependencies:** Phase 1 (block model is what recipes select over).
**Estimated effort:** 2-3 sessions
**Verification:** Classify the maintainer's real writeup corpus across the three workspaces; ≥85%
match a held-out human-assigned family. Audit N `random_idea` renders: **zero** empty/auto-padded
scope/metric/acceptance fields (Template-Enforcer guard holds). A downstream agent reads
`classification.family` from front-matter without re-running the classifier.

Key activities:
- **Define the 6-block document model** (`problem, evidence, decision, scope, question, open`) and
  `FAMILY_RECIPES` as ordered block lists per family. `problem` is always present; `open` is always
  allowed, never required. An unclassifiable goal still emits `problem` — there is no failure state.
- **Build a standalone `cast-goal-classifier` agent** (owner decision at plan review — extract, don't
  embed). Internally it makes the Claude strict tool-call `classify_work_family` returning
  `{family, confidence, reasoning, uncertainty_factors, alt_family}` with an enum-typed `family` (an
  off-taxonomy label is structurally impossible); whitelist-validate in code anyway; off-schema →
  `random_idea`, never crash. Packaging it as its own agent (not a buried step) makes the seam
  **phase-agnostic** so any phase can reclassify later — mirroring the extracted router resolver and
  honoring decision #2 (reclassify-from-any-phase is a core flow). **In v2, only `cast-refine-requirements`
  calls it** (ship the door, not the future callers). Result persists as front-matter, consumed by both
  US2 (document shape) and US6 (routing) — one classification, never run twice.
- **Gate confirm-on-ambiguity in code, not the model** (FR-004): `≥0.9` silent pill · `0.5-0.9`
  pill + one-click confirm · `<0.5` forced top-2 + "just notes / not sure yet" escape hatch. The model
  returns a number; *code* decides whether to ask.
- **Persist one classification, consume it twice:** YAML front-matter on the requirements artifact
  (agents + Phase 3b router) and the pill at the top of the HTML render (Phase 3a). Never classify twice.
- **Lock the ~8-family set + generic fallback** (resolved at plan review): new-initiative, pilot/POC,
  bug-fix, data-analysis, random-idea, **+ testing/QA, refactor/migration, personal/non-eng**, plus a
  generic fallback. **Spike is a within-family modifier, not a family; "stub" is a render-state, not a
  family.** Encode as `FAMILY_RECIPES` entries (config, not new templates). Still validate the
  classifier's accuracy against the corpus, but the family list itself is decided.
- **Encode reversibility/uncertainty as block-inclusion modifiers** (not new families): a never-seen
  bug picks up `question` (spike shape); a one-way-door initiative escalates to include `scope`.
- **Build the Template-Enforcer guard structurally:** the `random_idea` renderer literally has no
  scope/metric/acceptance slots to pad; structure is *offered*, never auto-generated empty.

---

## Phase 3a: Comprehension — HTML-First Render (parallel with Phase 3b)
**Outcome:** Refinement emits a well-designed, read-only HTML render as the primary human-consumption
artifact: an above-the-fold **Goal Card** (pill + one-sentence job statement + 3-5 outcome/scope
assertions, all WHAT, zero clicks), L1/L2/L3 visual hierarchy, progressive disclosure of depth, HOW
quarantined to a bottom "Directional" section, and per-family structural variation. **This is the
headline thread and the goal's only measurable headline criterion (SC-001).**
**Dependencies:** Phase 1 (parser/block model) + Phase 2 (taxonomy + block recipes).
**Estimated effort:** 3-5 sessions
**Verification (v2):** **A `cast-requirements-checker` agent is the SC-001 gate** (owner decision at
plan review). The agent opens the HTML render as an *unfamiliar reader* and, from the Goal Card +
headings alone, restates the job, primary outcome, and in/out scope — failing the render if it can't.
It reuses cast-preso's `one-clear-takeaway` + `l1-l2-hierarchy` rubric and runs in CI per family, with
one golden HTML snapshot per family. The **human timed-read with outside readers is deferred** for v2
(addable later as a confirmation increment).

Key sub-deliverable — **build the `cast-requirements-checker` agent**: a checker agent in the
`cast-spec-checker` / `cast-preso-check-*` lineage that takes a rendered requirements HTML and returns
a structured verdict `{can_state_what: bool, restated_job, missing[], score}`. It is reusable beyond
CI: a human (or another agent) can run it on demand to sanity-check any goal's render, and it doubles
as the FR-013 "agent-as-consumer" demonstration.

Key activities:
- **Build the block-recipe render engine** (`family → ordered blocks → HTML`) as a thin Jinja engine,
  data-driven off Phase 2's `FAMILY_RECIPES` so adding a family is a config change. Each block has
  **one** canonical visual treatment (consulting-exhibit shape: assertion heading → bold-lead bullets
  → source line). Include a generic fallback recipe and a **stub → prompt-to-begin** render.
- **Lift the cast-preso visual toolkit nearly verbatim** (`theme.css` tokens are already byte-identical
  to `style.css` `:root`): `.slide-title / .l1-body / .l2-body / .source-citation / .callout /
  .question-annotation`. **Hard rule: never hardcode hex — always `var(--color-*)`** (one-line rebrand
  = FR-012 win). Assign **level by importance** (L1 = survives a 90% cut = job statement; L2 = survives
  50% = outcomes/scope; L3 = acceptance detail/EARS/rationale).
- **Render the Goal Card + classification pill** as the entire SC-001 surface, always open, zero
  clicks. Scope renders **open, side-by-side** (in vs out is a comparison, never collapsed).
- **Wire the progressive-disclosure boundary:** only *depth* (acceptance scenarios, EARS, symptom/repro,
  constraints, rationale) wraps in `<details>` closed-by-default; **the WHAT is never collapsed**.
  `@media print` forces all open; add an "expand all" for deep review.
- **WHAT-before-HOW (FR-001):** HOW confined to a muted/italic "Directional ideas" section, **omitted
  entirely** when the family makes HOW irrelevant (e.g. data-analysis) — never padded.
- **Serve + regenerate:** clone the `/preso/review/{goal_slug}` serving precedent → `GET
  /goals/{slug}/render`; add `_rerender_requirements_html()` mirroring `_rerender_tasks_md()` with the
  `<!-- AUTO-GENERATED -->` header. Markdown stays the edit + agent source; HTML is generated read-only.
- **Selectable DOM for Phase 4:** render each block as a clean, text-selectable unit so the vanilla-JS
  comment layer can capture the reviewer's selection (the **quote**) and nearest section heading (the
  **hint**) — there is **no** `data-block-anchor`/`id="fr-007"` to emit (the thin-spine decision deleted
  stored anchors; placement is re-derived by a subagent from the stored quote). **Illustrations: none
  in v2** (resolved — decorative SVG fails the cast-preso visual checker and slows the scan).

---

## Phase 3b: Routing — Phase-Agnostic Workflow Router (parallel with Phase 3a)
**Outcome:** A classified goal resolves to a family-specific downstream-workflow **handle** (a named
**stub** for unbuilt pipelines), the decision is recorded on the goal, and the resolver is invokable
from **any phase** without re-running refinement. v2 ships the seam + stubs, not the pipelines.
**Dependencies:** Phase 2 (classification produces the family the resolver consumes).
**Estimated effort:** 1-2 sessions
**Verification:** Seed 5 goals (one per family) → `resolve` returns the correct handle/stub and
persists `workflow_family`/`routing_handle` (SC-005). Flip a goal's `phase`, call `resolve` again →
**byte-identical** handle, **no** re-classification. Assert no unimplemented family ever resolves to
`STARTER_TASKS` or a generic bucket (0 silent fallbacks; every stub names its steps).

Key activities:
- **Add the family registry to `config.py`** beside `STARTER_TASKS`: a closed `WORKFLOW_FAMILIES` set
  and a **total** `WORKFLOW_REGISTRY` map, every value `status="stub"` with enumerated `steps`
  (bug-fix: `logs→RCA→confirm→fix/test`; etc.). Flipping a family to `"implemented"` later is a
  registry-only diff — no seam change (FR-015).
- **Build the pure resolver `workflow_router_service.py`** modeled on `orchestration_service.py` (no
  LLM, no subprocess, `db_path=` injectable, CLI hook). `resolve(family)` is **total** — defined for
  every family + `None` (→ `needs-classification`) + unknown (→ `unmatched`, a Special Case that
  *announces itself*, never a silent Null Object). The resolver **never re-classifies** — it is a pure
  consumer of the persisted family (this is how FR-016 phase-agnosticism is preserved, not built).
- **Add recording columns to `goals`** (`workflow_family`, `routing_handle`, `routed_at`) via the
  `ALTER TABLE … ADD COLUMN` migration pattern; thread through `GoalUpdate`; they auto-render to
  `goal.yaml` for free. **Not** `tags` (flat, collides).
- **Write `record_routing_decision(slug, family, handle)`** — the only part that writes; idempotent
  (re-recording the same family is a no-op). Keep it separate from the pure `resolve`.
- **Expose `POST /api/goals/{slug}/route`** — the phase-agnostic surface a future planning/execution
  agent hits to re-resolve from persisted state (FR-016).
- **Have `cast-refine-requirements` call the `cast-goal-classifier` agent** (built in Phase 2), then
  write `workflow_family` to the goal and call `record_routing_decision`. Refinement is the **only** v2
  caller of the classifier and the router — do not wire other phases. Handle reclassification updates
  surfacing the changed downstream workflow (US6 Scenario 4). Optionally ship a `/cast-router` skill.
  Net seam: **classifier agent + resolver service, both phase-agnostic, both single-caller in v2.**

---

## Phase 4: Iteration — Annotation & Versioning Engine
**Outcome:** Reviewers (human or agent) leave **block-anchored** comments with an open/resolved
lifecycle and retained trail; unresolved comments mark the spec unconverged and drive new versions;
each new version emits a deterministic **block-level change summary**; only the current version lives
in the goal folder, older versions archived in the DB with comments intact. Built **API-first** so an
agent uses the same door as the human UI.
**Dependencies:** Phase 1 (thin spine + version/comment schema) + Phase 3a (selectable DOM to capture
quotes from).
**Estimated effort:** 3-4 sessions
**Verification:** A single dual-assertion test proves **agent parity** (one handler returns JSON to a
header-less call, HTML fragment to an `HX-Request` call). A comment left on a quote in v2 is re-located
to the right place after an unrelated edit by the re-anchor subagent, and becomes `orphaned` (not lost)
when its quote genuinely no longer exists. A spec with any open comment reports `unconverged`; the next
version flips it to `converged`. `find cast-server -name package.json` stays empty (no framework added).

Key activities:
- **Build the comment API *before any UI*** (the FR-013 forcing function): `comment_service.py` +
  `POST/GET …/comments`, `POST …/comments/{id}/resolve`, content-negotiated on `HX-Request` (JSON for
  agents, HTML fragment for HTMX) — the exact pattern already in `api_agents.py`. `author_kind` is the
  *only* human-vs-agent distinction; **no privileged UI write path.**
- **Store comments by quote, re-locate by subagent** (the thin-spine decision): a comment row holds the
  `quoted_text` + `section_hint` + `version` it was left against — **no stored block anchor.** On
  display against a changed file, a **Claude re-anchor subagent** finds where each open comment now
  belongs from its quote; an unfindable quote → `orphaned`, surfaced for triage (never silently lost).
  This is the deliberate trade: less determinism, far less machinery, intelligence handles drift.
- **Ship a ~150-line vanilla-JS comment layer** over the selectable DOM (selection → capture quote +
  nearest heading → popover → `hx-post`), wired on `htmx:afterSwap`. **No React, no annotation
  library.**
- **Keep the editable textarea + re-anchor on save** (resolves the human-edit-model question): a human
  whole-file edit is allowed; on save, the re-anchor subagent re-locates open comments against the new
  text. No need to forbid free-text editing — the subagent absorbs the drift.
- **Version snapshot + comment carry-over:** `create_next()` gates on open-comment count (open ⇒
  unconverged), snapshots the current file to a new `version` (with its content hash), marks the prior
  archived. Open comments carry forward and are re-located by quote; unfindable → `orphaned`. Only the
  current version's files land in the goal folder (FR-011).
- **Change summary (FR-017):** diff the parsed blocks of two version snapshots
  (`added/removed/modified/unchanged`, matched by heading + content) — the structural diff is the
  source of truth; a Claude subagent may *narrate* it into prose but never *invent* it. **Build this
  reusable — Phase 5 consumes the same engine.**
- **Archive retrieval (US5 S3):** an archived version returns *with* its comments and resolution state
  (the append-only `comment_events` trail makes this free).

---

## Phase 5: Living Source of Truth — Round-Trip Write-Back
**Outcome:** A downstream phase's requirement-affecting change lands **back in the requirements file**
with provenance (which phase/agent, derived from what), the user is notified (what changed + from
where), the change appears in the version change summary, and a change that conflicts with current
content is **surfaced, never silently overwritten**. v2 builds the *receiving* mechanism and proves it
with a *simulated* downstream emitter (real planner/executor emitters are a later goal).
**Dependencies:** Phase 1 (block anchors + write target) + Phase 4 (change-summary diff, versioning,
same-door API, append-only trail — all reused verbatim).
**Estimated effort:** 3-4 sessions
**Verification:** **SC-006** — a simulated downstream change (via `tests/fixtures/synthetic_child.py`)
traces end-to-end: `change_request` row → conflict verdict → surgical file apply → version bump →
change summary with provenance badge → outbox row → notification surfaced. Assert **0** modifications
to existing content applied without a passed gate or surfaced conflict; **0** lost/duplicate
notifications after an injected crash between commit and relay.

Key activities:
- **Model write-back as "propose + notify + gate," never auto-sync.** Land a first-class
  `change_request{origin, base}` entity + append-only `change_request_events` + `notifications_outbox`
  (house migration pattern). The two load-bearing fields a naive design forgets: `origin_*` (powers
  notify + audit, the W3C-PROV Activity/Agent/Entity triple as denormalized columns) and
  `base_version_id` (powers conflict detection).
- **One same-door endpoint** `POST /api/specs/{slug}/change-requests`: a human "suggest edit" and an
  agent write-back are the *identical* POST; `author_type` is data, not a code branch (FR-013).
- **Extend the `output.json` contract additively** with a `requirements_writeback` artifact type
  (parents ignore unknown fields — breaks no existing parent; reuses the test-covered carrier).
- **Conflict detection = three-way predicate against `base_version_id`** using the retained
  deterministic spine: the downstream change carries the version it read; compare the target region's
  content vs its content at that base version via content hash; diverged ⇒ `conflicted` ⇒ surface
  (accept-incoming / keep-current / merge-with-free-edit). This is the one place the hash spine earns
  its keep — a missed conflict is silent overwrite (US7 S4). **No CRDT/OT** (co-editing is out of scope).
- **Build the `cast-requirements-writeback` agent as the SOLE file writer** (the delegation contract
  forbids cast-server writing artifact files — server owns the proposal DB, an agent owns the file
  apply). The agent locates the target region by quote (same subagent skill as comment re-anchoring) and
  applies a surgical addition/annotation leaving the rest of the file byte-identical; lift
  `orchestration_service.update_manifest_status()` as the surgical-edit template. **Do not** build on
  `api_artifacts.save_artifact`'s whole-file overwrite — that is the silent-drift bug US7 exists to kill.
- **Graduated-trust gate by blast radius** (resolved at plan review): pure additions auto-apply + FYI;
  modifications to existing content gate via `AskUserQuestion`; conflicts always surface. Policy lives in
  config so it can be loosened later without a code change.
- **Notification via transactional outbox** (change + alert commit in one txn) → polling relay → the
  **unified notification surface shared with Phase 4** (resolved at plan review): one HTMX
  `needs_attention` badge carrying a **structured** payload (today it's a bare boolean) + an optional
  W3C-LDN-aligned `/inbox` JSON endpoint so agents consume the same notification humans see. Comment
  notifications and round-trip notifications use this one surface, not two.

---

## Build Order

```
Phase 0: SPIKES (render + comment/re-anchor prototype)
   │   🚦 HARD HUMAN GATE — owner plays with the prototype before any build/detailing
   ▼
Phase 1: Parser & Thin Spine ──────────┬──────────────────────────────────────────────┐
   (downscaled keystone)               │                                              │
                                       ▼                                              │
Phase 1b: gbrain upgrades        Phase 2: Classification & Block Recipes              │
   (parallel, off critical path)       │                                              │
                          ┌────────────┴────────────┐                                 │
                          ▼                          ▼                                 │
              Phase 3a: HTML Render        Phase 3b: Workflow Router                   │
                 (headline, SC-001)        (off critical path, SC-005)                 │
                          │                                                            │
                          ▼                                                            │
              Phase 4: Annotation & Versioning ◄─────────────────────────────────────┘
                 (reuses block anchors + builds the reusable diff engine)
                          │
                          ▼
              Phase 5: Round-Trip Write-Back
                 (reuses Phase 4 diff + versioning; needs writeback agent)
```

**Critical path:** Phase 0 (spikes) → 🚦 human gate → Phase 1 → Phase 2 → Phase 3a → Phase 4 → Phase 5
**Off the critical path (start as soon as deps allow):** Phase 1b (no deps), Phase 3b (after Phase 2).
**Gate:** nothing after Phase 0 is detailed or built until the owner signs off on the prototype.

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Claude re-anchor places a comment wrong** (the cost of the thin-spine decision — non-determinism in placement) | Med-High | The subagent re-locates by stored quote; an unfindable quote is surfaced as `orphaned`, never silently moved. Mitigate further by showing the reviewer the re-located position and the original quote so a mis-placement is visible. Accepted trade for deleting the anchoring engine; tune with eval cases. |
| **Re-anchor cost/latency** (a subagent call on every edited render) | Medium | Only re-anchor *open* comments, and only when the file content hash changed since last anchor; cache results per version hash. No LLM call when nothing changed. |
| **Missed conflict = silent overwrite** (US7 S4) | High | Conflict detection stays deterministic (content-hash compare against base version) — the one piece deliberately kept out of the LLM's hands. A diverged base always routes to `conflicted` → surfaced. |
| **SC-001 fails despite good styling** — the L1 line isn't a self-contained job assertion | High | SC-001 is an information-architecture problem, not CSS. Enforce assertion-format headings; gate every render through the LLM pre-screen *before* a human ever reads it. |
| **Taxonomy cemented to a 3-workspace corpus** skewed toward second-brain/linkedout (FR-012) | Medium | Ship families + generic fallback + re-classify path; validate against *external* users before locking; SC-001 readers must not all be the maintainer. |
| **Template-Enforcer creep** — structure forced onto `random_idea` | Medium | Make over-structuring *structurally impossible*: the loose renderer has no scope/metric slots to pad. Audit N renders for empty auto-padded fields. |
| **Agent-parity bolted on after a GUI-first build** (FR-013) | Medium | Build comment + write-back APIs *before* the UI; the UI is a client of the same door. A single dual-assertion test guards it. |
| **FR-007 markdown contract regresses** when HTML is added | Medium | Trivial under files-canonical (HTML is read-only on the file) — but lock it with the golden-file test from Phase 1, day one. |
| **Router silently re-classifies or falls back to `STARTER_TASKS`** | Medium | Resolver is pure + total; absent family → `needs-classification`; unknown → self-announcing `unmatched`. A test asserts no unimplemented family ever returns the generic seed. |

---

## Open Questions

**None.** All questions were resolved at plan review (2026-06-11) — see "Decisions Resolved at Plan
Review" in the Overview: determinism floor (thin spine + Claude re-anchor), family set (~8 + fallback),
round-trip gate (by blast radius), illustrations (none), notification surface (unified), human-edit
model (textarea stays + re-anchor on save), SC-001 verification (a `cast-requirements-checker` agent as
the gate; outside-reader study deferred), and classifier placement (a standalone `cast-goal-classifier`
agent, refinement-only caller in v2). The plan is ready to split into executable sub-phases.

---

## Spec References

- **`cast-delegation-contract.collab.md`** (Draft v1) — **constraint on Phase 5:** cast-server never
  writes artifact files. The round-trip file apply MUST be performed by the `cast-requirements-writeback`
  agent; the server owns only the proposal DB. No phase here changes this spec'd behavior.
- **`cast-output-json-contract.collab.md`** (Draft v1) — **constraint on Phase 5:** the contract-v2
  `output.json` shape is additive ("parents ignore unknown fields"), so registering a
  `requirements_writeback` artifact type extends it without breaking existing parents. Phase 5 should run
  `/cast-update-spec` to record the new artifact type rather than diverge silently.
- **`cast-init-conventions.collab.md`** (Draft v1) — relevant to Phase 1/3a artifact naming: the
  `.collab.md` authorship suffix and `_v2` versioning rule. The generated HTML render and version
  archival should conform to these conventions; consider an `/cast-update-spec` pass if HTML renders
  become a new first-class artifact class.
- No loaded spec contradicts this plan. Phases 3b (new `goals` columns + router service) and 5 (new
  write-back artifact type) are the two places where `/cast-update-spec` should be folded into the phase
  activities to keep specs current.
```
