# Code Exploration — Step 1: Learn from Existing Systems & the Maintainer's Corpus

**Goal context:** Refine Requirements v2 — workflow-aware, HTML-first requirements refinement. Before committing to any architecture/taxonomy/render, mine what already exists.
**Codebase:** `/home/sridherj/workspace/diecast` (→ `/data/workspace/diecast`), plus `~/workspace/second-brain`, `~/workspace/linkedout-oss`, and external prior art.
**Date:** 2026-06-11
**Method:** GO-BROAD. Five independent explorers fanned out (Diecast DB pattern · gbrain · cast-preso* · maintainer corpus · external prior art), synthesized here. This brief maps where we ARE so the synthesizer understands the starting point and migration cost — it does **not** constrain recommendations to current code.

> **How to read this:** Sections A–E are the five Step-1 deliverables that later steps cite directly (A→Step 2, B→refinement-agent upgrades, C→Step 5, D→Step 3, E→Steps 2/3/4). The 7-angle code map and Key Takeaways follow.

---

## A. Diecast's DB-Canonical → Generated-Render Pattern (feeds Step 2)

**Verdict up front: the pattern is reusable as *infrastructure convention* but insufficient as-is. It has no element-level identity, no versioning, no change notification, and no file→DB import — exactly the three things requirements-v2 needs most.**

### How it actually works

- **Storage:** raw SQLite via `sqlite3` (no SQLAlchemy ORM). Connection helper `cast-server/cast_server/db/connection.py`; canonical schema `cast-server/cast_server/db/schema.sql`; migrations are a hand-rolled `_run_migrations()` (`ALTER TABLE … ADD COLUMN` in try/except). Alembic exists but only stamps a baseline (`cast-server/alembic/versions/cfe1a46fdefc_baseline.py`).
- **"Models" are Pydantic, not entities:** `cast_server/models/goal.py`, `task.py`, `task_v2.py` are request/response shapes only. There is **no ORM layer**.
- **`goals` table** (`schema.sql` L1–14): `slug TEXT PRIMARY KEY`, title, status, phase, origin, in_focus, timestamps, `tags TEXT` (JSON), `folder_path`, `gstack_dir`, `external_project_dir`.
- **`tasks` table** (`schema.sql` L16–39): `id INTEGER PK AUTOINCREMENT`, `goal_slug` FK, `parent_id` (1-level subtask nesting), title/outcome/action, `task_artifacts TEXT` (JSON paths), `is_spike`, etc.

### DB → file render path (one-way, write-on-mutation)

| Render | Writer fn | File |
|---|---|---|
| `goal.yaml` | `_write_goal_yaml()` / `_update_goal_yaml_fields()` — `goal_service.py:337–395` | full write on create; partial merge on each field update |
| `tasks.md` | `_rerender_tasks_md()` — `task_service.py:389–455` | **full re-render on every task mutation** |

Both files carry a header: `AUTO-GENERATED: Read-only render of DB state. Do not edit directly.` The DB is master; files are derived outputs. `get_all_goals()` / `get_tasks_for_goal()` query SQLite only — **never read the files back.**

### The crucial asymmetry: artifacts are NOT in this pattern

`requirements.human.md`, `refined_requirements.collab.md`, etc. are **created as empty stubs** in `_create_starter_tasks()` (`goal_service.py:325–333`) and thereafter **edited directly on disk** by users/agents via the inline editor (`/api/artifacts/save`, `routes/api_artifacts.py:94`). The server reads them at request time (`pages.py:113`, `api_goals.py:344`). **Their content is never registered in the DB.** So the very documents requirements-v2 is about live entirely *outside* the DB-canonical pattern today — they are file-canonical, opaque blobs to the DB.

### Stable IDs today

- Goals: `slug` (derived once via `_slugify()`, never updated → stable). Goal-level only.
- Tasks: integer PK (stable across edits). No slug/UUID.
- **Artifacts: no IDs at all.** No element/heading/section identity anywhere. This is the single biggest gap for v2.

### Versioning / archival precedent

**None.** No `_version`/`_history`/shadow table. No `v2`/`v3` artifact convention exists yet. The only append-log is immutable `agent_runs` rows — a precedent for *how* an append-only history table could look, but not a reusable mechanism.

### What transfers cleanly vs. what needs new investment

**Transfers:** the `goals/<slug>/` per-goal directory convention; the `PHASE_ARTIFACTS` registry (`config.py:53–58`) that already lists requirements files and serves them in the UI (add `.html` here cheaply); the inline editor save path (extend to `.html`); the `.human/.collab/.ai` authorship suffix convention (`file_utils.py:6–9`).

**Needs new build:** element-level stable IDs (new `requirement_elements` table or HTML heading-anchor convention) · `artifact_versions` table for archival · `artifact_comments` table or a JS annotation library · a change-notification mechanism (none exists; closest analog is the UI-only `HX-Trigger` toast) · any DB awareness of file *content* (currently zero — drift detection needs content hashing or structured parsing).

### Fragilities to inherit knowingly (`diecast` report §7)

1. Files diverge silently if hand-edited — DB unaffected, no checksum.
2. `_update_goal_yaml_fields` reads its own prior output; on missing/corrupt file it logs and no-ops *after* the DB already committed → silent file/DB divergence (no cross-store transaction).
3. `tasks.md` full re-render = write amplification + obliterates external edits.
4. `folder_path` set once; stale if `CAST_GOALS_DIR` changes.
5. Slug collisions → `INSERT OR REPLACE` silently overwrites an older goal.
6. No delete endpoint for goals/tasks (orphaned dirs).

> **Implication for Step 2:** The realistic v2 path is *not* "make requirements a pure DB entity like goals." It is a **hybrid**: keep human-facing content file-canonical (preserves the downstream markdown contract, FR-007, for free), add a thin DB layer (`artifact_versions` + `artifact_comments` keyed to stable element IDs) for the things files can't do — versions, anchored comments, provenance, drift detection. The DB-canonical *convention* (generated-render header, write-on-change, registry) is the template to imitate; the goal/task *schema* is not directly reusable.

---

## B. gbrain (second-brain) Portable Requirements Ideas — Keep/Drop (feeds refinement-agent upgrades)

second-brain runs the same lineage agent (`taskos-refine-requirements`, 3-phase draft→refine→persist, EARS, confidence scoring, 7-question budget) but several refinements are **ahead of** the Diecast `cast-refine-requirements` version. Resolves the open question *"any improvements to refine-requirements from gbrain?"* — **yes, six high-leverage ones.**

| Idea | Source | Verdict | Rationale |
|---|---|---|---|
| **Stage-adaptive framework selection** (vague→JTBD/Impact-Map; specific→Example-Mapping; near-complete→EARS+gap) | `agents/taskos-refine-requirements/…md` ~L151–159 | **KEEP (top)** | Prevents premature EARS structuring on half-formed ideas — directly the "Template Enforcer" guard the spec fears |
| **Explicit exit conditions + log gaps in Open Questions** when budget exhausts | same, L235–243 | **KEEP (top)** | No silent low-confidence sections; the Open-Questions capture is the key bit |
| **Decisions section** (Chose / Over / Because, dated) | `docs/specs/_template.collab.md` | **KEEP (top)** | Captures conversation choices that otherwise vanish; pairs with versioning |
| **Adversarial meta-pass** ("What would an engineer reject?") after per-section checks | `agents/taskos-preso-check-coordinator/…md` | **KEEP (top)** | Surfaces contradictions, unmeasurable constraints, circular open questions |
| **Evidence-quoting mandate for confidence scores** (cite draft text, not assert level) | `agents/taskos-preso-narrative-checker/…md` | **KEEP (top)** | Removes the "didn't bother checking" failure mode |
| **Scope-mode detection from signal words** (MVP / comprehensive / dream) | `agents/taskos-detailed-plan/…md` L319–339 | **KEEP (top)** | Calibrates scenario depth early; aligns with scope-tiered render |
| 7 Socratic question types + "replace 'why' with 'what'" | refine-req agent L46–53 | KEEP | Teachable, codifiable rule |
| 4 cross-questioning techniques (5-Whys, Past-Behavior, Observation, Outcome) | L131–143 | KEEP | Tighter than generic "ask about intent" |
| "Faster horse" resistance script | L144–146 | KEEP | One-sentence handler for a real failure mode |
| Propose-then-approve (show diff, wait, never auto-edit) | `agents/taskos-update-spec/…md` | KEEP | Should be default for durable requirement writes |
| 300-line soft cap + split suggestion | same | KEEP | Concrete anti-bloat heuristic |
| Scope-tiered doc depth (1-pager / 2-pager / full spec) | `tips/.../tips_for_writing_great_prds.md` | KEEP | Feeds per-family render sizing (Step 3/5) |
| Recommendation-first grounded questions | multiple agents | KEEP | Reinforce grounding in already-read artifacts |
| SAV bullets as test-function names | update-spec + spec template | **DROP** | SAV is the downstream *spec* format; mixing into requirements adds wrong-stage complexity |
| Automated spec-drift detection hook (`check_spec_drift.py`) | `dev_tools/check_spec_drift.py` | **DROP for refinement; REVISIT for Step 7** | Needs `linked_files`/`last_verified` front-matter infra — but the *concept* (compare modified-dates of linked files) is a cheap seed for the living-source-of-truth round-trip |
| `.human/.ai/.collab` suffix convention | `CLAUDE.md` L57–62 | DROP | Already in Diecast |

**gbrain does NOT have:** HTML render of requirements, progressive disclosure, annotation/comments, versioned diffs of requirements, or family classification beyond the 3-stage maturity detection. So gbrain is a goldmine for *refinement-agent quality* but offers nothing for the *render / comments / versioning* threads — those are net-new.

---

## C. cast-preso* Transferable Visual Patterns (feeds Step 5)

The cast-preso* toolkit is a **working, CSS-tokenized library of exactly the visual-hierarchy + progressive-disclosure techniques the HTML render needs.** Primary source: `skills/claude-code/cast-preso-visual-toolkit/` (SKILL.md, `visual_toolkit.human.md`, `templates/css/{theme,typography,components}.css`, 11 archetype templates).

### Lift-as-is

**1. CSS token system (`theme.css :root`) + typography scale (`typography.css`).** Drop the `:root` block verbatim into a requirements stylesheet; override only `--color-accent`. Token set includes `--color-bg/text/muted/surface/accent`, callout/question bg+border pairs, mono heading font + sans body font. **Hard rule (enforced by the visual checker): never hardcode hex — always `var(--color-*)`** so per-project brand override is one line.

**2. The L1/L2/L3 hierarchy is already classed:**

| Class | Size/weight/color | Requirements-doc role |
|---|---|---|
| `.slide-title` | mono 1.6em / 700 / text | Section heading = **assertion sentence** |
| `.l1-body` | sans 1.1em / 600 / text | Primary requirement (survives 50% cut) |
| `.l2-body` | sans 0.9em / 400 / muted | Supporting constraint/rationale (first to cut) |
| `.source-citation` | 0.5em / muted | Acceptance criteria / provenance |

Rule: **L2 must never visually compete with L1** (content-checker criterion `l1-l2-hierarchy`).

**3. Two semantic annotation components (`components.css`, `callout-box.html`, `question-annotation.html`):** numbered accent **callout** = "this is decided"; muted italic **question-annotation** ("?") = "this is open / a risk." Maps *perfectly* onto requirements metadata: stated requirements vs. open questions/gaps — instant legibility.

### Patterns / disciplines (zero-cost authoring rules)

**4. Assertion-format headings.** Ban label titles. Validation test: *"Can someone read ONLY the headings and understand the full argument?"* → "Users authenticate via SSO; password login unsupported," not "Authentication." Highest-leverage single rule for 2-minute comprehension.

**5. Write L1 first, fill L2 second** (`cast-preso-what-planner.md`). Hierarchy is a *planning pass*, not just styling.

**6. Hard density limits** (`visual_toolkit.human.md §5`): ≤50 words body / card, ≤15 words / bullet, ≤6 visual elements / unit, ≥30% whitespace. Make these *render constraints* — warn/split when a section exceeds them.

**7. Progressive disclosure via native `<details>/<summary>`** (also confirmed in prior art) — keep the decision summary default-visible, hide rationale/alternatives/edge-cases. The **appendix-as-deep-dive** navigation pattern (core ≤50 words, depth opt-in via links) is the structural answer to "WHAT in 2 minutes."

### Relevant archetypes (`templates/slide-archetypes/`)

- **Consulting-exhibit** → ideal requirement-block shape: assertion title → scope sentence → bold-lead evidence bullets → acceptance-criteria source line.
- **Compare/contrast** (`minmax(0,1fr)` two-col, muted=problem/out-of-scope, accent=solution/in-scope) → scope definition, current-vs-desired.
- **Build-up sequence** → ordered/dependency requirement lists (prior items dimmed, current bolded) — works static, no JS.

### Validation rubric to reuse (Step 5 acceptance + a render checker)

Three independent 0–1.0 checkers (content / visual / tone), each gated. Directly portable criteria: `achieves-stated-outcome`, `one-clear-takeaway` (<5s scan), `l1-l2-hierarchy`, `not-generic` (no "title+bullets+image-right"), `not-ai-aesthetic`, plus the tone checker's anti-slop list ("leverage", "comprehensive", em-dashes, hedging). The 8-pass **compliance checker** (outcome delivery → narrative flow → walk-away → consumption-mode → structure → navigation → rendering → no planning-leakage) is a ready-made template for validating a rendered requirements doc.

### Illustration rules (for diagrams in research/feature families)

SVG-first for architecture/flow; `viewBox="0 0 720 380"`, CSS class names only (no inline hex → obeys token override), ≤5 elements, **text overlaid in HTML not inside the image**, fixed Style-Bible prefix for raster. Only illustrate when it communicates something text can't (decorative fails the checker).

---

## D. Maintainer Corpus — Empirical Family Tally (feeds Step 3 taxonomy validation)

27 real writeups sampled across the three workspaces and bucketed. **Headline finding: the proposed 5 families capture only ~56% of the real corpus cleanly. Three families are missing, and "stub" is a render-state, not a family.**

### Tally

| Family | Count | Examples |
|---|---|---|
| 1 — New Initiative / PRD | 4 | task_os_writeup, agent_run_improvements_v3, cast-subagent-and-skill-capture, product-revamp-diecast |
| 2 — Small Pilot / POC / **Agent-Skill creation** | 6 | starter_exploration_agent, designer_workflow, spec-drift-detection, task_triage_agent, demo-seed-requirements, **refine-requirements-v2 itself** |
| 3 — Bug / Debug | 2 | cast-ui-test-children-completion, spike-session-switcher (full RCA) |
| 4 — Data Analysis / Research / Spike-results | 3 | linkedout_db_indexes, atomic_work_research (303 lines), embedding_spike_results |
| 5 — Fuzzy Ideation / Pre-goal (incl. **stubs**) | 5 | ai_agent_swarm, revamp-diecast, atomic_work, + 2 literal 2-line stubs |
| **6 — Testing / QA charter** *(missing)* | 2 | child-delegation-integration-tests, comprehensive-ui-test |
| **7 — Refactor / Migration / Ops / Naming** *(missing)* | 2 | task_suggestions_v2 (before/after schema), introduction_of_subphase |
| **8 — Personal / Content / Non-eng** *(missing)* | 3 | reachout_intro, cast_presentation_v3, trip-to-bali |

### Taxonomy reality check

- **Add three families** (or treat as first-class subtypes): **Testing/QA charter** (behavior list + tiers + references existing tests — reads like a QA charter, not a bug or feature), **Refactor/Migration** (before/after state, impacted files, migration-safety — fits neither "bug" nor "new initiative"), **Personal/Non-eng** (the tool is used for trips/comms/marketing too; needs entirely different render logic). For an OSS product these are not maintainer-idiosyncratic — Testing and Refactor are universal eng work types (and the external survey confirms "chore" + "spike").
- **Family 2 is really "Small/scoped work *including agent/skill creation*"** — agent/skill specs (Input/Output/Constraints blocks) are a recurring scoped subtype in this corpus.
- **"Stub" is a render state, not a family.** Multiple 2-line "Finish brainstorming" files appear. Detect at render time → show **prompt-to-begin**, not an empty template, across all families.
- **Classification must be inferred, with a confidence signal.** The maintainer *never labels* the family; it's inferable from structural signals (symptom+repro=bug; before/after-schema=refactor; question→data→output=research; empty=stub). This validates the spec's confirm-on-ambiguity design (FR-004) over user-picks-family.

### Style signals (feed the render design directly)

1. **Bimodal length:** either 2–5 line stub/brain-dump or 40–90 line narrative. 100+ line structured specs appear only in *AI-refined `.collab.md`*, never in human writeups → the render must gracefully handle very sparse input.
2. **~70% WHAT, but HOW hints are sprinkled inline** as thinking-aloud notes ("use ptyxis instead of tmux") — **not binding.** The render must NOT elevate these to requirements (validates US1's Directional section + the WHAT/HOW split).
3. **Structure varies by intent:** bug writeups are the *most* structured; ideation/initiative are heading-less bullet narratives; agent specs are semi-formal Input/Output blocks. → per-family templates are justified by real data.
4. **70%+ are reference-heavy** (file paths, sibling-goal links, past-plan links) — the render should treat these as **navigable links**, not raw strings.

---

## E. External Prior Art — Doc Types, Comments, Versioning (feeds Steps 2/3/4)

### Document-type templates (Step 3)

- **PRD:** heavily WHAT (problem, personas, success metrics, scenarios, non-goals, open questions). No ratified schema — every team customizes ("start from template, adapt"). → feature-family skeleton fixed but sections optional.
- **RFC:** WHAT+some HOW; distinctive **Alternatives Considered** section. → that section is the RFC's signature, often missing from PRD-style docs.
- **ADR (Nygard/MADR):** Title/Status/Context/Decision/Consequences. **Immutable once Accepted — a change creates a *new* record that supersedes the old** (old gets only a "Superseded by" link). Gold standard for decision provenance.
- **Google Design Doc:** Context, Goals & **Non-goals**, design + trade-offs, Alternatives, cross-cutting concerns. Explicitly *discourages copying schema/interface code into the doc*. Anti-patterns: implementation-manual, >10–20pp over-scoping, outdated-never-corrected, review-process-for-trivial-changes.
- **Spike (eng + design):** goal is **fact-finding, not decision**. Needs timebox + research-questions(pre) + findings(post) + follow-up-work. **Must NOT have feature acceptance criteria** — conflating investigation with commitment is an anti-pattern.

### GitHub spec-kit (Step 2 file model)

Linear pipeline **Spec → Plan → Tasks → Implement**, each phase a distinct markdown artifact under `specs/<branch>/` (spec.md / plan.md / tasks.md / research.md / data-model.md / contracts/ / quickstart.md). Classifies by **process preset** (AIDE, Canon, Product-Forge, FX→.NET, MAQA), **not by document-type family** — so v2 adds the family-taxonomy layer on top. Worth adopting: **phase-gate checklists** (Simplicity/Anti-Abstraction/Integration gates) before implementation. Anti-pattern: its immutable "constitutional articles" = template-enforcer rigidity. (Diecast already emits `refined_requirements.collab.md` in spec-kit shape → preserving that = FR-007.)

### Work-classification convergence (validates/reshapes Step 3 axis)

Industry has converged on a small universal set: **Feature/Story · Bug · Chore · Spike · Epic(container)**. Shape Up's **Pitch** (Problem / **Appetite** = time budget / fat-marker Solution / Rabbit-holes / No-gos; unpitched ideas die, no backlog) is a strong alternative framing. → External evidence supports a small family set and supplies the **missing Chore (≈Refactor) and Spike** families the corpus also surfaced. Borrow Shape Up's **appetite** field for the feature family.

### Doc + comment + version models (Step 4)

- **Notion:** comments at page/block/text granularity; block IDs are stable anchors; **open/resolved is UI-only, not in the API**; versions don't link to comment state.
- **Google Docs:** anchors to text ranges (`kix.*` ids + start/end index); marks comments **"outdated"** when the range changes; programmatic anchoring is unreliable (known limitation).
- **Confluence:** new version per save + diff view + Change-History macro (version#/author/date/comment); recently AI change-summaries; "Scroll Documents" adds **explicit release snapshots vs. per-edit noise**.
- **GitHub PR review = the most mature anchored-comment model:** comments anchored to file+line; **three-state threads Open → Addressed → Resolved** with distinct actors (reviewer raises/closes, author addresses); outdated flag when the line changes; branch protection can require zero unresolved before merge.

→ **Comment data model for v2:** `{ anchor(element-id + TextQuoteSelector fallback), status(Open/Addressed/Resolved), author, created_at, thread[replies] }`. Use the **three-state** model, not binary. **Explicit version snapshots with required change summaries**, never auto-version-on-save (Google/Confluence noise anti-pattern).

### Anchored-comment tech — the React/Next.js question (Step 4 — DECISIVE)

**Anchored commenting does NOT require React/Next.js.** All four mature options run on **server-rendered HTML**:
- **Hypothesis** — 3 selector types (RangeSelector / TextPositionSelector / **TextQuoteSelector** = exact text + 32-char prefix/suffix); tries all three in order; fuzzy quote survives heavy edits. Browser overlay, standard DOM APIs, no framework.
- **`@duckyb/annotator`** — modern TS, framework-agnostic, same 3-tier fallback, works with SSR HTML/static/SPA.
- **recogito/text-annotator-js** — vanilla JS, `<span class="annotation">` wrappers, server IDs via `overrideId`.
- **Velt SDK** — commercial (free tier), robust DOM element-pin anchoring, works vanilla or React.

**Simplest + most durable: assign `id="req-NNN"` to each requirement block at generation time** (element-ID anchor survives edits to surrounding content entirely), with **TextQuoteSelector as fuzzy fallback**. Anti-pattern: character-offset-only anchoring (any upstream edit shifts everything). → This kills the rewrite premise: the FastAPI+Jinja stack + stable element IDs + a vanilla-JS annotator is sufficient.

### Research/notebook artifacts (Step 3 — research family)

Jupyter/Observable interleave code+prose+output but have **no versioning, no acceptance criteria, cell-order dependency** → architecturally incompatible with specs. The research family should borrow notebooks' **inline-output-in-context display** (read-only chart/table embeds) but keep **spec structure** (question → hypotheses → findings → conclusions → follow-up). Anti-pattern: treating a notebook *as* a spec.

---

## 7-Angle Code Map (current Diecast terrain)

**1. Data Model & Schema** — SQLite, no ORM; `goals`(slug PK) + `tasks`(int PK) in `schema.sql`; Pydantic shapes in `models/`. No version/history/comment/element tables. Artifacts unmodeled (paths-as-strings only).

**2. Existing Implementation** — `cast-refine-requirements` agent produces `refined_requirements.collab.md` (spec-kit shape) consumed by planner/task-suggester/spec-checker. DB→file renderers for goal.yaml/tasks.md (`goal_service.py`, `task_service.py`). Inline artifact editor (`api_artifacts.py`). UI = Jinja2 + HTMX server-rendered.

**3. Gap Analysis** (severity) — *Critical:* no element-level IDs; no artifact versioning/archival; no content-aware DB / drift detection; no change-notification mechanism. *Medium:* file/DB divergence on hand-edit (no checksum/transaction); tasks.md write-amplification; no goal/task delete endpoint. *Low:* dual-format tags parser bandage; stale `folder_path`.

**4. Patterns & Conventions** — flat MVCS (fat service fns w/ inline SQLite + file I/O · thin FastAPI routers · Jinja/HTMX views · Pydantic models). No BaseRepository/BaseService/CRUDRouterFactory. Generated files carry "AUTO-GENERATED, do not edit" header. `.human/.collab/.ai` authorship suffixes. `PHASE_ARTIFACTS`/`PHASES` in `config.py`.

**5. Entry Points & Flow** —
```
create_goal() ──▶ DB INSERT (goals) ──▶ _write_goal_yaml() ──▶ goals/<slug>/goal.yaml
                                    └──▶ _create_starter_tasks() ──▶ empty requirements.human.md stub
user/agent edits ──▶ POST /api/artifacts/save ──▶ file write (NO DB) ──▶ served via f.read_text()
task mutation ──▶ DB ──▶ _rerender_tasks_md() ──▶ full rewrite tasks.md
```
The requirements artifact flow is entirely file-side; the DB is blind to its content.

**6. Tests & Coverage** — conftest at `cast-server/conftest.py`; UI test harness under `tests/ui/`. No tests exist for artifact versioning/comments (features don't exist). Downstream-agent contract (FR-007/SC-004) is the regression surface to protect — define a byte-compat check on the markdown render.

**7. Config & Dependencies** — FastAPI + Jinja2 + HTMX + raw sqlite3 + Alembic(baseline only) + Pydantic; API at `localhost:8005`. No JS framework, no annotation lib, no event bus today. Adding a vanilla-JS annotator (Hypothesis/duckyb/recogito) is additive, no migration.

---

## Key Takeaways (opinionated, cross-cutting)

1. **The rewrite premise is dead — kill it in Step 4.** Element-ID-anchored comments work on the existing FastAPI+Jinja stack with a vanilla-JS annotator (Hypothesis/@duckyb/recogito all SSR-compatible). React/Next.js is *not* required; recommend against it.

2. **Don't make requirements a DB entity like goals — go hybrid.** Files stay canonical (free FR-007 preservation), a thin DB layer (`artifact_versions` + `artifact_comments` keyed to stable element IDs) adds what files can't: versions, anchored comments, provenance, drift detection. Imitate the *convention* (generated-render header, write-on-change, registry), not the goal/task *schema*. This is the lowest-migration-cost answer to Step 2's keystone question.

3. **Stable element IDs are the true keystone (Step 2 §2 confirmed by every angle).** `id="req-NNN"` assigned at generation time + TextQuoteSelector fallback simultaneously powers comments (D/E), version diffs/change-summaries (Step 4), and round-trip provenance (Step 7). Everything downstream consumes it.

4. **The 5-family taxonomy is ~56% right — widen to ~8.** Real corpus + industry convergence both demand **Testing/QA, Refactor/Migration(chore), and a Personal/Non-eng** family, plus **Spike** as first-class (fact-finding, no ACs). "Stub" is a render-state (prompt-to-begin), not a family. Classification should be **inferred with confidence + confirm-on-ambiguity**, never user-labeled (the maintainer never labels). This is the most important correction Step 3 must absorb.

5. **cast-preso* is a ready-to-lift render kit, not just "inspiration."** The `:root` token block, the `.slide-title/.l1-body/.l2-body/.source-citation` scale, the callout-vs-question components, assertion-headings, density limits, `<details>` disclosure, and the 3-checker rubric are concrete artifacts Step 5 can adopt nearly verbatim — the headline-comprehension problem is mostly *already solved* in this repo.

6. **gbrain upgrades the *refinement brain* for free.** Six high-leverage imports (stage-adaptive framework, exit-conditions+Open-Questions, Decisions section, adversarial pass, evidence-quoted confidence, scope-mode detection) sharpen the agent independent of the render/comments/versioning build — quick wins that de-risk the whole goal.

7. **Versioning/notification/round-trip are 100% greenfield — design them on stable IDs + ADR-style immutability.** No precedent exists in Diecast. Adopt ADR semantics (new version supersedes, never in-place after "accepted"), GitHub three-state comment threads, explicit snapshots (not auto-version), and a change-summary = stable-ID element diff. The `agent_runs` append-log is the structural model; `check_spec_drift.py`'s linked-file date-compare is a cheap seed for Step 7's drift detection.

---

## Key Files (read these to ground Steps 2–7)

- `cast-server/cast_server/db/schema.sql` — current schema; where new `artifact_versions`/`artifact_comments` tables would land.
- `cast-server/cast_server/services/goal_service.py:337–395` — DB→file render mechanics + partial-merge footgun.
- `cast-server/cast_server/services/task_service.py:389–455` — full-re-render pattern (and its write-amplification limit).
- `cast-server/cast_server/routes/api_artifacts.py:94` — the artifact save path to extend for `.html` + versioning.
- `cast-server/cast_server/config.py:52–58` — `PHASES` + `PHASE_ARTIFACTS` registry (add HTML render here).
- `cast-server/cast_server/models/goal.py`, `task.py` — Pydantic shape conventions for new artifact/version/comment models.
- `agents/cast-refine-requirements/cast-refine-requirements.md` — the agent to upgrade with gbrain imports (B).
- `~/workspace/second-brain/agents/taskos-refine-requirements/taskos-refine-requirements.md` — stage-adaptive framework + Socratic techniques to port.
- `~/workspace/second-brain/agents/taskos-update-spec/taskos-update-spec.md` — propose-then-approve + 300-line cap.
- `~/workspace/second-brain/docs/specs/_template.collab.md` — Decisions (chose/over/because) section.
- `~/workspace/second-brain/dev_tools/check_spec_drift.py` — drift-detection seed for Step 7.
- `skills/claude-code/cast-preso-visual-toolkit/visual_toolkit.human.md` + `templates/css/{theme,typography,components}.css` — the render kit to lift (C).
- `skills/claude-code/cast-preso-visual-toolkit/templates/slide-archetypes/{consulting-exhibit,compare-contrast,build-up-sequence}.html` — requirement-block layouts.
- `agents/cast-preso-check-{content,visual,tone}.md` + `cast-preso-compliance-checker.md` — render validation rubric for SC-001.

---

## Open-Question Coverage from Step 1

| Open question | Step-1 contribution |
|---|---|
| Canonical source of truth (Step 2) | §A: recommend **hybrid** (file-canonical + thin DB layer); goal/task schema not directly reusable but convention is |
| Archive mechanism (Step 2) | §A + §E: new `artifact_versions` table; ADR-immutability + explicit snapshots, not auto-version |
| Annotation approach / React? (Step 4) | §E: **No React needed** — element-ID anchors + vanilla-JS annotator on SSR HTML; lib options named |
| gbrain improvements (resolved here) | §B: 6 high-leverage keeps + full keep/drop table |
| Classification taxonomy validation (Step 3) | §D + §E: 5 families → ~8; add Testing/Refactor/Personal + first-class Spike; infer-with-confidence |
| Router placement (Step 6) | Not a Step-1 target; noted that routing decision would be *recorded on the goal* (consistent with §A store) |
