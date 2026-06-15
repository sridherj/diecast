# Exploration Summary: Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement

**Date:** 2026-06-11
**Steps researched:** 7 (7 web researchers + 6 code explorers, all completed)
**Playbooks generated:** 7 (all completed)
**Pipeline:** cast-goal-decomposer (fable) → 13 research children (opus) → 7 cast-playbook-synthesizer (fable) → this summary

---

## Impact Ratings

| # | Step | Impact | Rationale |
|---|------|--------|-----------|
| 2 | Canonical source of truth (stable IDs, store, archive) | **10/10** | The keystone — comments, diffs, archival, round-trip are all consumers of stable element identity; wrong choice forces re-architecture of everything downstream |
| 1 | Learn from existing systems + corpus | **9/10** | Refutes three load-bearing assumptions with evidence (DB rewrite framing, React, 5-family taxonomy) before any design spend |
| 3 | Workflow classification taxonomy + templates | **9/10** | Defines the most visible output (the pill) and the block model Steps 5 & 6 both consume; the block-vs-templates fork is the highest-leverage architecture decision |
| 4 | Annotation & iteration engine | **9/10** | The iteration engine (US4/US5); turns requirements into a converging, agent-participable artifact on the existing stack |
| 5 | HTML-first render (2-min comprehension) | **9/10** | The goal's only measurable headline criterion (SC-001) and most visible output; render is also the origin of stable IDs |
| 7 | Living source-of-truth round-trip | **9/10** | Makes requirements *canonical* rather than *initial*; the payoff that ties Steps 2 + 4 together |
| 6 | Phase-agnostic workflow router | **8/10** | Sets the seam every future family pipeline drops into; 8 because v2 ships stubs and the extraction rests on FR-016 being owner-confirmed |

**Average Impact: 9.0/10**

---

## The One Conflict to Resolve at Plan Review

**Playbook 01 vs Playbook 02 disagree on the canonical store.** This is the single decision the owner
must arbitrate — everything else across the 7 playbooks is mutually consistent.

| | Playbook 01 (prior-art brief) | Playbook 02 (dedicated deep-dive, PRIMARY) |
|---|---|---|
| Recommendation | **Files stay canonical + thin DB sidecar** (versions, comments, routing tables keyed to render-time IDs) | **DB-canonical element rows** (`requirements` table; markdown + HTML both generated renders) |
| Core argument | Lowest migration cost; FR-007 free because the file *is* the contract; imitate Pattern A's convention, not its schema | A row has identity for free (PK); files have identity only by convention; hybrid shadow-parsing is "the worst of both"; FR-007 risk retired by one golden-file test |
| Who agrees | — | Playbooks 04 ("move requirements under Step 2's DB-canonical model"), 05 ("one element model → two projections"), 07 (writes against `spec_elements` rows) all *assume* element rows |

**Recommendation: DB-canonical element rows (Playbook 02's design), with 01's caution absorbed as
guardrails** — the golden-file FR-007 regression test before the flip, the backfill importer, and the
explicit edit-model decision (kill the whole-file textarea overwrite). Rationale: 02 is the dedicated
deep-dive on exactly this question (web + code research); 04/05/07 all design against element rows; and
both playbooks *agree on the real keystone* (stable element identity decoupled from display ordinals) —
02's store makes that identity structural, 01's makes it conventional. The cost difference is bounded
(~5.5 days, one service mirroring `task_service.py`); the ceiling difference is not.

---

## Unanimous Verdicts (every relevant playbook agrees)

1. **NO React/Next.js migration.** Settled on three independent legs: fuzzy text-anchoring disappears
   with stable IDs; all mature annotation libs are vanilla-JS-first; the only genuine SPA-forcer
   (realtime co-editing) is explicitly out of scope. (01, 02, 04, 05)
2. **No annotation library either.** RecogitoJS/Hypothesis solve anchoring in prose you don't control —
   stable element IDs delete that problem. Ship a ~150-line vanilla-JS selection→popover→HTMX layer. (04)
3. **Stable element identity is the keystone, decoupled from display ordinals.** `element_id` surrogate
   (ULID or `req_<goal>_<TYPE>_<NNN>`) ≠ the cosmetic `FR-001` label, which is a render-time projection.
   Comments/diffs/round-trip become foreign keys, not text matching. (all 7)
4. **API-first, same-door agent parity (FR-013).** Build the JSON contract before any UI; content-negotiate
   on `HX-Request` (one handler → HTML fragment for humans, JSON for agents); `author_type` is data, not a
   code branch. (02, 04, 06, 07)
5. **Composable blocks, not 5 rigid templates.** Document = ~6 blocks (`problem/evidence/decision/scope/
   question/open`); a family is a *recipe* selecting blocks. Wrong guess degrades gracefully; adding a
   family is config, not a template rewrite. (03, 05)
6. **The loose family is the default and the floor.** "Random ideas" is a deliberate first-class mode —
   structurally incapable of demanding scope/metrics (the Template-Enforcer guard is structural, not
   discipline). "Stub" is a render-state (prompt-to-begin), never a family. (01, 03, 05)
7. **Code thresholds gate confirm-on-ambiguity, never the model.** Models verbalize uncertainty but don't
   act on it; classify with one Claude strict tool-call, gate at ≥0.9 silent / 0.5–0.9 confirm / <0.5
   forced choice in code. (03)
8. **Propose + notify + gate, never auto-sync.** Silent two-way sync of a source-of-truth doc is worse
   than drift — it's untraceable overwrite of human intent. Graduate trust by blast radius: pure
   additions auto-apply + FYI; modifications gate; conflicts always surface. (07)
9. **Deterministic diffs; LLM narrates, never invents.** Change summaries are structural set arithmetic
   over stable IDs; an LLM may render prose over the diff but the diff is truth. (04, 07)
10. **Reuse beats building.** cast-preso toolkit CSS tokens are byte-identical to the app's existing
    tokens (zero migration); `_rerender_tasks_md` is the render-after-mutate template; `update_manifest_status`
    is the surgical-edit template; `orchestration_service` is the pure-service template; the `needs_attention`
    rail is the notification surface. (01, 02, 05, 06, 07)

---

## Top Recommendations

### 1. Land stable element identity (Step 2) before anything that consumes it
Adopt Playbook 02's three-table schema (`requirements`, `requirement_versions`, `requirement_comments`)
with surrogate `element_id` PKs decoupled from display ordinals. Lock FR-007 with the golden-file test
(render rows → `bin/cast-spec-checker` exits 0 + normalized snapshot diff) *as the sign-off gate*.
This is ~5.5 days of work that converts every downstream feature from fragile text-anchoring to foreign keys.

### 2. Ship the six gbrain refinement upgrades immediately — they're free
Stage-adaptive frameworks (vague→JTBD, specific→Example-Mapping, near-complete→EARS), explicit exit
conditions, a dated Decisions section, an adversarial meta-pass, evidence-quoting for confidence scores,
and scope-mode detection. ~1 day of agent-prompt edits, independent of every build decision, and they
de-risk output quality before the keystone even lands. (Playbook 01)

### 3. Build the parser-renderer as the real Step 5 build; everything visual is reuse
The net-new build is a spec-kit-aware structured parser (`{kind, id, level, family, blocks[]}`) feeding
two pure projections (markdown for agents, HTML for humans) that cannot drift. Goal Card above the fold =
the entire SC-001 surface: pill + L1 job statement + 3–5 L2 assertions, zero clicks. WHAT is never behind
a `<details>`. Gate with an LLM judge pre-screen (cast-preso rubric) before any human timed-read.

### 4. Classify once, consume twice
One Claude strict tool-call returns `{family, confidence, reasoning, alt_family}`; persist as front-matter;
the pill (humans) and the router (agents/Step 6) read the same field. Never classify twice — two
classifications drift. Optional lexical fast-path (4 regexes) handles ~80% of unambiguous cases free. (03)

### 5. Extract only the router's deterministic half
`resolve(family) → WorkflowHandle` as a pure service over a *total* registry dict in `config.py`;
classification stays in the refinement agent. Stubs are Special Case objects that announce their named
steps — never Null Objects, never `STARTER_TASKS` fallback (which is literally the silent generic
fallback FR-015 abolishes). Two typed columns on `goals` record the decision. (06)

### 6. Build round-trip as a change_request entity, prove with a simulated emitter
`change_request{origin, base_version_id}` rows through the same-door endpoint; the
`cast-requirements-writeback` agent is the sole file writer (the delegation contract forbids server file
writes); three-way conflict predicate against `base_version_id`; transactional outbox for atomic
change+notification. v2 proves SC-006 with `synthetic_child.py` — real emitters are later goals. (07)

### 7. Confirm FR-016 (phase-agnostic routing) with the owner before extracting the seam
The entire router extraction rests on "invokable from any phase" being a genuine requirement. If routing
is forever single-caller, inline placement is correct and the seam is YAGNI. One explicit question at
plan review. (06)

---

## Recommended Technology Stack (consolidated)

| Layer | Component | Choice |
|-------|-----------|--------|
| Canonical store | Requirements elements | SQLite element rows (`requirements` + `requirement_versions` + `requirement_comments`/`change_requests`), raw SQL via `db/connection.py`, no ORM |
| Identity | Stable element IDs | Surrogate TEXT PK (`req_<goal>_<TYPE>_<NNN>` or ULID), allocate-once never-reuse; display ordinal `FR-NNN` is a render projection |
| Renders | Markdown (agents) + HTML (humans) | Two pure projections of the element model; markdown keeps spec-kit shape (FR-007 golden-file test); HTML via Jinja2, no build step |
| Frontend | Interaction layer | HTMX (already vendored) + ~150-line vanilla JS; **no React/Next.js, no annotation library, no package.json** |
| Visual system | Hierarchy + tokens | Lift cast-preso `theme.css` level/annotation classes (tokens already byte-identical); native `<details>/<summary>` disclosure |
| Classification | Classifier | One Claude strict tool-call (enum-typed family + confidence + reasoning); code-side confidence gates; optional regex fast-path |
| Document model | Per-family shaping | ~6 composable blocks; `FAMILY_RECIPES` dict (5 family labels + generic fallback, loose `random_idea` default; widen toward ~8 families per corpus evidence) |
| Router | Resolve + record | Pure `workflow_router_service.py` over a total `WORKFLOW_REGISTRY` in `config.py`; Special Case stubs; 2 typed columns on `goals` |
| Round-trip | Write-back | `change_request` entity + W3C PROV columns + transactional outbox + 3-way conflict predicate (sha256 vs `base_version_id`); `cast-requirements-writeback` agent as sole file writer |
| Comments | Anchoring + lifecycle | FK to `element_id`; W3C Web Annotation shape; open/resolved(+orphaned) with append-only event trail; GitHub-style version carry-over |
| Notifications | Surface | Existing `needs_attention`/HX-Trigger toast rail + structured payload; minimal LDN-aligned `/inbox` for agents |
| Quality gates | Verification | FR-007 golden-file pytest; SC-001 LLM judge pre-screen (haiku, cast-preso rubric) → human timed-read; per-family golden HTML snapshots |

---

## Architecture Overview

```
                        ┌────────────────────────────────────────────────┐
   raw writeup ───────▶ │  cast-refine-requirements (upgraded w/ gbrain)  │
                        │   • classify: Claude strict tool-call           │
                        │   • confidence gate (code): silent/confirm/choose│
                        └───────┬──────────────────────────┬─────────────┘
                                │ writes element rows       │ records family
                                ▼                          ▼
   ┌─────────────────────────────────────────┐   ┌─────────────────────────┐
   │  SQLite CANONICAL STORE                  │   │  goals + workflow_family │
   │  requirements (element_id PK ★)          │   │  + routing_handle        │
   │  requirement_versions (append-only)      │   └──────────┬──────────────┘
   │  comments / change_requests / outbox     │              │
   └────────┬───────────────────┬─────────────┘              ▼
            │ rows              │ rows            ┌─────────────────────────┐
            ▼                   ▼                 │ workflow_router_service  │
   ┌────────────────┐  ┌─────────────────────┐    │ resolve(family)→Handle   │
   │ rows→markdown   │  │ rows→HTML            │    │ (pure; total registry;  │
   │ spec-kit shape  │  │ Goal Card + L1/L2/L3 │    │  Special Case stubs)    │
   │ (FR-007 golden) │  │ + blocks per family  │    └─────────────────────────┘
   └───────┬────────┘  │ + id="fr-007" anchors│
           │           └──────────┬───────────┘
           ▼                      ▼
   downstream agents      ┌──────────────────┐     SAME-DOOR API (FR-013)
   (planner, suggester,   │ HTMX + 150-line JS │    POST /api/specs/{slug}/comments
    spec-checker —        │ comments, resolve, │    POST /api/specs/{slug}/versions
    UNCHANGED)            │ versions, deltas   │    POST /api/specs/{slug}/change-requests
                          └─────────┬─────────┘    (HX-Request→HTML | no header→JSON)
                                    │
   downstream phases ──change_request{origin,base}──▶ graduated-trust gate
   (exploration/planning/           │                   add→auto+FYI · mod→gate · conflict→surface
    execution agents)               ▼
                          cast-requirements-writeback agent (SOLE file writer)
                            surgical apply + PROV + version bump + outbox→notification

   ★ = stable element identity: the keystone every box consumes
```

---

## Build Order

| Phase | What | Effort | Delivers |
|-------|------|--------|----------|
| 0 | gbrain refinement upgrades (6 prompt edits) + FR-016 owner confirmation + store sign-off | ~1 day | Better refinement output immediately; the two plan-review decisions locked |
| 1 | Step 2 keystone: schema + `requirement_service` + rows→markdown renderer + golden-file test + backfill importer | ~5.5 days | DB-canonical elements with stable IDs; FR-007 provably preserved; existing goals migrated |
| 2 | Step 5 render: parser → element model, block-recipe engine, Goal Card, disclosure, preso CSS lift, `/goals/{slug}/render` route + LLM pre-screen | ~4 days | The SC-001 surface: 2-minute-comprehension HTML per family |
| 3 | Step 3 classifier: strict tool-call + confidence gate + pill + front-matter; Step 6 router: registry + pure resolver + 2 columns + route | ~3 days | Classification once/consumed twice; phase-agnostic routing with named stubs (SC-005) |
| 4 | Step 4 iteration engine: comment tables + API-first endpoints + vanilla-JS layer + version snapshots + structural diff | ~5 days | Google-Docs-style anchored comments; v2/v3 versions with change summaries (SC-002) |
| 5 | Step 7 round-trip: change_request schema + writeback agent + conflict predicate + outbox + simulated end-to-end (SC-006) | ~5 days | Requirements as living source of truth with provenance + notification |

**Total estimated effort:** ~23-24 working days (solo), with Phase 0 shippable today and each phase independently valuable.

---

## Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| FR-007 regression — downstream agents break on the generated markdown | High | Golden-file pytest (checker exit 0 + normalized snapshot diff) lands *before* the store flip; SC-004 in CI |
| Store decision contested (Playbook 01 vs 02) | High | Surface the conflict explicitly at plan review (this doc, §Conflict); decision-ready trade-off tables exist in both playbooks |
| Edit-model flip silently loses human edits (textarea overwrite vs row-edit) | High | Decide the edit path *before* flipping; remove/repurpose `api_artifacts.py:94` whole-file save; flagged in 3 playbooks |
| Coarse element granularity caps comment/conflict precision | Medium | Push Step 2 to scenario/clause-level surrogates (explicitly requested by Playbooks 04 and 07) |
| Template Enforcer — structure forced onto fuzzy ideation | Medium | Structural guard: `random_idea` recipe has no scope/metric slots to pad; stub = prompt-to-begin render-state |
| Taxonomy tuned to maintainer's corpus (OSS FR-012) | Medium | Corpus skew documented (5 families ≈ 56% coverage); blocks+recipes make family additions config-only; validate against external users before locking |
| Router seam is YAGNI if FR-016 isn't real | Medium | One explicit owner question at plan review before extraction |
| Gate fatigue on round-trip write-backs | Medium | Graduated trust by blast radius (additions auto-apply); per-element policy config, not hardcode |
| LLM-invented changelogs/diffs | Low | Deterministic set-arithmetic diff is truth; LLM narrates only |
| Notification dual-write loses alerts | Low | Transactional outbox; UI dedupes on `change_request_id` |

---

## Reference Implementations

| Project | What | Link |
|---------|------|------|
| W3C Web Annotation Data Model | Comment shape (body + target/selector) | https://www.w3.org/TR/annotation-model/ |
| W3C PROV-DM | Provenance triple (Entity/Activity/Agent) | https://www.w3.org/TR/prov-dm/ |
| W3C Linked Data Notifications | Agent-consumable notification inbox | https://www.w3.org/TR/ldn/ |
| GitHub PR review comments | Versioned anchored comments + bot parity + "outdated" state | (pattern reference) |
| Jama suspect tracking | Flag-on-upstream-change, human clears | https://www.jamasoftware.com/blog/2025/09/13/the-importance-of-suspect-tracking-in-requirements-management/ |
| AWS transactional outbox / AppSync VERSION conflict | Atomic change+notify; optimistic concurrency | https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html |
| Shape Up / Design Docs at Google / Oxide RFD-1 | Loose-by-default authoring; structure accretes | https://basecamp.com/shapeup/1.1-chapter-02 |
| recogito/text-annotator-js, @duckyb/annotator, Hypothesis | Proof annotation never needs React (referenced, not adopted) | https://github.com/recogito/text-annotator-js |
| GitHub issue forms | Typed-field templates + chooser + escape hatch | https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms |
| Diátaxis / Cynefin / Type-1-2 doors | Shape-follows-purpose; doc weight modifiers | https://diataxis.fr/start-here/ |
| **Internal:** `task_service._rerender_tasks_md`, `orchestration_service.py`, `update_manifest_status`, `cast-update-spec`, `cast-preso-visual-toolkit`, `error_memory_service`, gstack `/spec`, taskos-refine-requirements | Working in-repo precedents every playbook builds on | (in-repo) |

---

## All Files

```
exploration/
  steps.ai.md                                      # 7-step decomposition + multi-lens insights + open-question traceability
  summary.ai.md                                    # this file
  research/
    01-learn-from-existing-systems.ai.md           # web: external prior art, gbrain survey, corpus tally
    01-learn-from-existing-systems-code.ai.md      # code: Diecast Pattern A/B, preso toolkit, existing renders
    02-canonical-source-of-truth.ai.md             # web: storage models, stable-ID schemes, versioning patterns
    02-canonical-source-of-truth-code.ai.md        # code: goal/task DB-canonical precedent, schema, render paths
    03-workflow-classification-taxonomy.ai.md      # web: classification axes, genre conventions, classifier patterns
    04-annotation-and-iteration.ai.md              # web: annotation libs, W3C model, GitHub PR pattern, React verdict evidence
    04-annotation-and-iteration-code.ai.md         # code: HTMX/content-negotiation precedents, comment-adjacent tables
    05-html-first-render.ai.md                     # web: IA research, progressive disclosure, visual hierarchy
    05-html-first-render-code.ai.md                # code: structure-blind md render, identical CSS tokens, preso serving
    06-phase-agnostic-router.ai.md                 # web: EIP content-based router, registry pattern, feature-flag lessons
    06-phase-agnostic-router-code.ai.md            # code: orchestration_service precedent, goals schema, dispatch door
    07-living-source-of-truth-roundtrip.ai.md      # web: PROV, outbox, suspect tracking, 3-way merge
    07-living-source-of-truth-roundtrip-code.ai.md # code: output.json carrier, surgical-edit precedent, notification rail
  playbooks/
    01-learn-from-existing-systems.ai.md           # 9/10 — adopt/build/reject verdicts for everything downstream
    02-canonical-source-of-truth.ai.md             # 10/10 — DB-canonical element rows + golden-file FR-007 gate
    03-workflow-classification-taxonomy.ai.md      # 9/10 — blocks+recipes, strict tool-call classifier, code-side gates
    04-annotation-and-iteration.ai.md              # 9/10 — no-React verdict, element-anchored comments, API-first
    05-html-first-render.ai.md                     # 9/10 — parser-renderer build, Goal Card, preso CSS lift
    06-phase-agnostic-router.ai.md                 # 8/10 — pure resolver + total registry + Special Case stubs
    07-living-source-of-truth-roundtrip.ai.md      # 9/10 — propose+notify+gate, PROV, outbox, conflict predicate
```
