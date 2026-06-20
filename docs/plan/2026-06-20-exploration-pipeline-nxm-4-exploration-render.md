# Exploration Pipeline: N×M Workflow + 90/10 Hat — Sub-phase 4: Exploration WHAT/HOW HTML render (convergence of Tracks A + B)

## Overview

This sub-phase converges Track A (the N×M markdown substrate from 3a) and Track B (the dual md/html
viewer from 2b + Diecast-wide commenting from 3b) into the marquee deliverable: a polished
`exploration.html` that lands in the dual viewer and is commentable. It does so by **cloning the
proven WHAT→HOW→checker maker pipeline** (`render_job_service.py` + the three `cast-requirements-*`
maker agents) — not by extending it — into an exploration-specific render job. The WHAT agent decides
what each section conveys (the per-step opinionated POV + each hat's distinct take), emitting no HTML;
the HOW agent renders one bespoke self-contained page whose **layout keeps hats distinct, never
blended** (the collation principle, FR-017 criterion 3); the render-checker enforces FR-017's 4 locked
criteria. The page lands atomically at `goals/{slug}/exploration/exploration.html` with a `served-by`
stamp, then becomes visible/commentable for free because 2b's `kind="html"` seam and 3b's
`artifact_ref` field already handle any HTML artifact in the `exploration/` glob.

**Key insight from the model:** `render_job_service.py` is a 2400-line apparatus tightly coupled to
requirements concepts (`ParsedRequirements`, `block_diff`/`block_splice` UPDATE mode, gap machinery,
`families.py`, the canonical-id DOM contract). Exploration has *no* canonical-id source, *no* UPDATE
mode this round, *no* gap machinery — its source is a tree of markdown notes. Forking the **pattern**
(named stages, tool-free `claude -p` subagents, `--tools ""`, sentinel extraction, quality loop,
atomic publish, served-by stamp) into a lean parallel module is far cleaner than threading an
exploration branch through every requirements-shaped stage. See the "Extend vs. parallel" decision
below.

## Operating Mode

**HOLD SCOPE** — the parent requirements carry `scope_mode: hold` and the spec's FR-017 rubric is
explicitly *locked* ("Lock exploration render-checker rubric now (4 criteria)" — Decisions table,
2026-06-20). My job is rigorous adherence to the 4 criteria + the WHAT/HOW/checker structure + the
distinct-not-blended principle, with exhaustive edge-case mapping (failed-hat `null` cells, dropped
cells surfaced not suppressed, zero-extractable fallback) — no new hats, no stable anchor-ids (spec
Out of Scope), no UPDATE mode, no extra surfaces.

## Position in Overall Plan

```
        ┌─ 1a (Workflow spike) ─┐
1 ──────┤                       ├─ 2a (hat agent) ─► 3a (Workflow engine) ─┐
(spikes)│                       │                                          ▼
        └─ 1b (viewer spike) ──► 2b (dual viewer) ─► 3b (commenting) ──► [ Sub-phase 4 ] ─► 5 (e2e)
                                                                          THIS PLAN
```

Sub-phase 4 is the convergence node. It is the LAST build sub-phase before end-to-end validation (5).
It is a pure consumer of three upstream contracts and produces one new artifact + three new agents +
one new render-job module.

## Depends On (from prior plans)

| Source | What Sub-phase 4 consumes | Why |
|--------|----------------------------|-----|
| **3a** | `exploration/research/{NN}-{step-slug}-{hat-id}.ai.md` (per surviving cell), `exploration/playbooks/{NN}-{step-slug}.ai.md` (one opinionated playbook per step), `exploration/summary.ai.md`. `hat_id` vocabulary verbatim (always-on `contrarian`/`first-principles`/`90-10`; 5 gateable). Failed cells already dropped to `null` upstream (FR-016/US12). | These md files are the WHAT agent's ONLY content source. The render is a *view* of them, never new content. |
| **2b** | Render-class `.html` served via `<iframe srcdoc sandbox="allow-scripts allow-popups">`; artifact dict's `kind="html"` discriminator (derived from extension); `_add_html_file` collector in `api_goals.py get_phase_tab`; `api_artifacts.py:52` read gate admits `.html`; `authorship=None` (no edit button). | `exploration.html` inherits viewer rendering with ZERO new viewer code — it just has to land in the `exploration/` glob with a `.html` extension. |
| **3b** | `artifact_ref` field (goal-relative path) on the comment create/relocate path; postMessage-to-host bridge binding selection in the iframe; `anchor_space='render'`; verbatim-substring relocation via `container_text_index`. | `exploration.html` inherits commenting for free by being served with `artifact_ref="exploration/exploration.html"`. Sub-phase 4 writes NO comment code. |
| **render_job_service.py** (the model) | The WHAT→HOW→checker orchestration shape: `AgentRunner` Protocol + `ProductionAgentRunner` (`claude -p … --tools ""`, clean child env), sentinel extraction (`extract_render`), the `_quality_loop` (`run_how → gate → run_checker → decide_quality`), `_compare_and_publish`, `publish_maker_html`'s atomic-write + served-by stamp envelope. | Sub-phase 4 mirrors this structure for exploration — same reliability properties, requirements-specific machinery stripped. |

## Extend vs. parallel render-job — DECISION

**Build a parallel, lean exploration render-job module; do NOT extend `render_job_service.py`.**

Evidence the model is requirements-bound and would bloat under an exploration branch:
- Its `JobState` carries `parsed: ParsedRequirements`, `block_diff` UPDATE refs, `gaps_*`, `mode`,
  `prior_html`/`prior_parsed` — none apply to exploration (no canonical ids, no UPDATE this round, no
  gap machinery).
- Its prompts (`_build_what_prompt`, `_build_how_prompt`, `_build_checker_prompt`) inline a
  `block_inventory`, `families.py` recipe, and the canonical-id DOM contract — all requirements-shaped.
- Readiness keys off an embedded `source-hash` of one `.collab.md`; exploration's source is a *tree* of
  md files, so the source identity is a digest of the file set, not a single doc hash.

What IS shared and MUST be reused verbatim (single-helper discipline — do not re-implement):
- `requirements_render_service._atomic_write` (tmp-in-same-dir + `os.replace`) — the atomic publish
  primitive. Promote/import it; do not copy.
- The `AgentRunner` Protocol + `ProductionAgentRunner` subprocess hygiene (`_clean_child_env`,
  `--tools ""`, `_load_agent_md`, per-job cwd). Lift these into a shared module both render-jobs import
  (e.g. `cast_server/render_common/agent_runner.py`), OR import directly from `render_job_service`. The
  spike (design review below) decides which; default = extract to `render_common` so neither job owns
  the other.
- The sentinel-extraction shape (`extract_render`) — same `<!-- BEGIN RENDER -->`/`<!-- END RENDER -->`
  contract, reused so the HOW agent's output protocol is identical to requirements'.

New module: **`cast_server/services/exploration_render_service.py`** (mirrors `render_job_service.py`
but exploration-shaped). New deterministic substrate fallback:
**`cast_server/services/exploration_render_service.py::render_exploration_fallback()`** — a trivial
md-concatenation-to-HTML used ONLY on literal no-output (parity with the requirements deterministic
fallback). New publish helper: **`publish_exploration_html(slug, html, *, source_digest, served_by,
human_review, review_reason)`** — reuses `_atomic_write`, writes the same AUTO-GENERATED + source-digest
+ served-by envelope to `goals/{slug}/exploration/exploration.html`.

## The three new agents (mirror the requirements maker trio)

| Agent | Role | dispatch_mode | Tools | Output |
|-------|------|---------------|-------|--------|
| **`cast-exploration-what`** | Content brain. Reads the per-step md (playbook + surviving hat notes + summary), decides per step the **opinionated POV** (the one thing the reader must take away — drawn from the playbook) and **each hat's distinct take** (one takeaway per surviving hat note). Emits a machine-checkable WHAT doc. NO HTML. | subagent (carve-out, like `cast-requirements-what`) | `--tools ""` | ONE WHAT doc (YAML front matter + md body) as entire final message |
| **`cast-exploration-how`** | Presentation brain. Takes the gated WHAT doc + the source md, renders ONE bespoke self-contained HTML page between sentinels. Lays out each step's POV with the distinct hat takes beneath it. | subagent | `--tools ""` | ONE HTML doc between `<!-- BEGIN RENDER -->`/`<!-- END RENDER -->` |
| **`cast-exploration-render-checker`** | Cold-reader-with-taste gate. Sees ONLY the rendered page + the step/hat-matrix label (never the source md). Grades FR-017's 4 criteria. | subagent | `--tools ""` | ONE bare-JSON verdict (the exploration checker contract) |

These follow the `cast-{noun}-{role}` convention and the `cast-hat-researcher` (2a) naming family.
Each lives at `agents/cast-exploration-{role}/cast-exploration-{role}.md` with a `config.yaml`, and is
surfaced as a SKILL via `bin/generate-skills` (same as the requirements trio).

---

## Sub-phase 4: Exploration WHAT/HOW HTML render

**Outcome:** A completed exploration (3a's md substrate present) produces a polished
`goals/{slug}/exploration/exploration.html` via a WHAT→HOW→checker maker pipeline; the page lays out
each step's opinionated POV with the distinct hat takes beneath it (distinct, NOT blended); it passes
the exploration render-checker's 4 locked criteria (every applicable hat visible per step; per-step
POV legible at zero-click; hats DISTINCT not blended; not AI-slop); and it renders in the dual viewer
(2b) with working comments (3b) via `artifact_ref="exploration/exploration.html"`. The deterministic
fallback serves only on literal no-output; degraded best-attempts are surfaced flagged, never silently
swapped.

**Dependencies:** 3a (md substrate), 2b (dual viewer + `kind` seam), 3b (commenting + `artifact_ref`).
Soft: the model `render_job_service.py` + the requirements maker trio (cloned, not depended on at runtime).

**Estimated effort:** 2–3 sessions.

**Verification:**
- Run the exploration render-job against a real goal that has 3a md output → `exploration.html`
  appears at the canonical path with an AUTO-GENERATED + source-digest + `served-by: maker` envelope
  and atomic write (no partial file on a mid-write crash).
- The render-checker returns a verdict; on a clean run it passes all 4 FR-017 criteria (SC-005).
- Open the phase tab containing both the `.md` artifacts and `exploration.html` → both show, HTML
  rendered in the iframe (SC-006).
- Select text inside `exploration.html` in the viewer → a comment row is created via the same-door API
  with `artifact_ref="exploration/exploration.html"` (SC-007).
- Force one hat note absent (a `null` cell from 3a) → the step still renders, that hat is simply absent
  (criterion 1 = every *applicable* hat visible, and a dropped cell is surfaced in a per-step note, not
  silently swallowed).
- Force the HOW agent to emit no sentinels across all attempts → deterministic fallback serves,
  `status=fallback`, `served-by: deterministic` (parity with requirements).

### Key activities

1. **Stand up `exploration_render_service.py` (the parallel render-job), reusing shared primitives.**
   - Define `ExplorationJobState` (exploration-shaped: `goal_slug`, `source_digest`, the loaded md
     corpus per step `{nn, slug, playbook_text, hat_notes:[{hat_id, text}], summary_text}`, `job_dir`,
     `runner`, the quality-loop counters, `attempts_history`). NO `ParsedRequirements`, NO UPDATE refs,
     NO gap state.
   - **Source identity = a digest of the md file SET** (sorted relative paths + per-file content hash),
     since exploration's source is a tree, not one doc. This is the readiness key embedded in the
     published page (mirrors how requirements embeds `source-hash`). → Delegate the hashing primitive
     reuse: import `content_hash` from `cast_server.requirements_render.hashing`; combine per-file
     hashes into one `source_digest`.
   - Import (or extract-then-import) `AgentRunner`/`ProductionAgentRunner` + `_atomic_write`. **Do not
     copy** — single-helper discipline.
   - Mirror the named-stage loop: `run_what → gate_what → run_how → gate_html → run_checker →
     decide_quality → publish`, minus the gap machinery and UPDATE mode entirely.

2. **Author `cast-exploration-what` (content WHAT agent — no HTML).**
   - Input (inlined by the runner, tool-free): per step the playbook md (the opinionated POV source),
     the surviving hat-note md (one per surviving `(step,hat)` cell, tagged with `hat_id`), and
     `summary.ai.md`; plus the `hat-matrix` (which hats were applicable per step) so the WHAT doc can
     mark a hat that was *gated out* vs. *dropped to null* vs. *present*.
   - It decides, per step: ONE **opinionated POV outcome** (L1 takeaway, drawn from the playbook —
     this is "the collation"), and for each surviving hat a **distinct hat take** (a one-line takeaway
     in that hat's voice, never merged with another hat's). It maps every surviving research note into
     exactly its step's hat list (mirrors the requirements WHAT agent's total-id-mapping invariant,
     adapted: every surviving `(step,hat)` cell must appear under its step, distinct).
   - Invariants (gate-enforced, design review below): sections are named after STEPS (not hat ids);
     each hat take is attributed to its `hat_id` and kept separate; never invents content beyond the md;
     always-on hats (`contrarian`/`first-principles`/`90-10`) present unless the cell was a `null`
     failure (surfaced as such, not omitted silently); `--tools ""` makes "never writes md" structural.
   - Contract: `cast-exploration-what/v1` (YAML front matter: `contract`, `goal_slug`, `source_digest`,
     `steps:[{nn, slug, name, pov_outcome, hats:[{hat_id, take, status: present|dropped|gated}]}]`;
     body = per-step communication-intent prose). → Model on `cast-requirements-what/SKILL.md`; verify
     the WHAT-doc shape is byte-aligned with its Python gate (`gate_what`).

3. **Author `cast-exploration-how` (presentation HOW agent — bespoke HTML, distinct-not-blended layout).**
   - Input: the gated WHAT doc + the source md corpus + the cast-preso visual toolkit (reuse
     `cast-preso-visual-toolkit`'s style tokens so the page is family-shaped, not AI-slop).
   - **The layout contract (the heart of this sub-phase, FR-017 criterion 3):** per step, render the
     opinionated POV as the dominant element (zero-click-legible — criterion 2), then the distinct hat
     takes BENEATH it as visibly separate, individually-attributed units (each hat in its own
     card/column/labelled block, never a blended paragraph). The always-on hats
     (`contrarian`/`first-principles`/`90-10`) get consistent, recognizable treatment across steps. A
     `null`/dropped hat is shown as an explicit "this lens was attempted and dropped" marker (surface,
     don't suppress), and a gated-out hat is simply absent (it was never applicable). See "HTML layout
     decision" below for the concrete archetype.
   - Output protocol: ONE self-contained HTML doc between the SAME `<!-- BEGIN RENDER -->`/`<!-- END
     RENDER -->` sentinels as requirements (so `extract_render` is reused verbatim). Self-contained
     (own `<head>/<style>`) so it renders cleanly in 2b's `<iframe srcdoc>`.
   - **US7 "selectable units, no ids" DOM contract (from `cast-requirements-render.collab.md`):** render
     each hat take / POV as a clean selectable text unit so 3b's verbatim-substring relocation can
     anchor a comment to it. No stable anchor-ids (spec Out of Scope this round). → Verify the DOM
     against the 3b commenting expectations (a selection inside a hat card must yield a clean
     `quoted_text`).
   - → Model on `cast-requirements-how/SKILL.md` + `cast-preso-how`'s archetype approach; verify
     self-containment + the sentinel protocol against the cloned `extract_render`.

4. **Author `cast-exploration-render-checker` (the FR-017 4-criteria gate).**
   - Cold-reader-with-taste, tool-free, sees ONLY the rendered page + a label of the step/hat-matrix
     (the *expected* applicable hats per step, so criterion 1 — "every applicable hat visible" — is
     judgeable WITHOUT the checker seeing the source md). Emits ONE bare-JSON verdict.
   - The 4 locked criteria (FR-017, verbatim):
     1. **every applicable hat is visible per step** — judged against the inlined hat-matrix label.
     2. **the per-step opinionated POV is legible at the zero-click surface** — run on a deterministic
        zero-click extract of the page first (mirror `extract_zero_click_view`; build an
        exploration-flavored equivalent so the POV-at-zero-click test is structural, not a discipline).
     3. **hat perspectives stay DISTINCT (not prematurely blended)** — the exploration-specific check:
        each hat's take is individually attributable, not merged into a synthesized paragraph.
     4. **visual quality / not generic AI-slop** — folds in the requirements checker's visual rubric.
   - Verdict shape: a superset of the requirements checker's `{can_state_what-equivalent, missing[],
     issues[], rework_feedback[], score}` — here `missing[]` uses tokens like `pov`, `distinctness`,
     `hat_coverage`, `visual`. `derive_pass` requires all 4 criteria clear. → Model on
     `cast-requirements-render-checker/SKILL.md`; the rubric is ALREADY LOCKED in FR-017 — do not
     re-derive it, encode exactly those 4.

5. **Wire the quality loop + terminal decision (mirror `_quality_loop`/`decide_quality`).**
   - `run_how → gate_html (structural: sentinels present, self-contained, one-unit-one-container for
     selectable hat takes) → run_checker → decide_quality`. Clean = structurally valid AND checker
     `derive_pass` → `served-by: maker`, no flag. Non-convergent / structural-stop / checker-unavailable
     → serve best-attempt FLAGGED (`human_review=1` + `review_reason`), surface don't suppress. Zero
     extractable across all attempts → deterministic fallback (`status=fallback`). Rationed ONLY by the
     high anti-infinite-loop ceiling (reuse the `QUALITY_*` knob pattern), never by cost/latency.
   - Reuse `_best_attempt` ranking (PREFER VALID, THEN SCORE) and the `AttemptRecord` shape.

6. **Land `exploration.html` atomically with a served-by stamp + wire into viewer/commenting.**
   - `publish_exploration_html` writes the AUTO-GENERATED + `source-digest` + `served-by` (+ optional
     `human-review`/`review-reason`) envelope, then `_atomic_write` to
     `goals/{slug}/exploration/exploration.html`. → Reuse `_atomic_write`; reuse the
     `_compare_and_publish` re-read-source pattern adapted to `source_digest` (if the md set changed
     mid-render → `superseded`, write nothing).
   - **Viewer wiring (2b inheritance, ZERO new viewer code):** confirm `exploration.html` falls inside
     `api_goals.py get_phase_tab`'s `exploration/` glob and that `_add_html_file` tags it `kind="html"`,
     `authorship=None`. The render-class `.html` already renders via `<iframe srcdoc>`. → Verify by
     opening the phase tab; if the glob excludes the file, the fix is a one-line glob/collector tweak in
     the 2b seam (flag a 2b revision only if so — see Suggested Revisions).
   - **Commenting wiring (3b inheritance, ZERO new comment code):** confirm the served
     `exploration.html` carries `artifact_ref="exploration/exploration.html"` into 3b's postMessage
     bridge so a comment knows its artifact. → Verify a selection yields a comment row with the right
     `artifact_ref` and `anchor_space='render'`.

7. **Entrypoint: who triggers the exploration render-job?**
   - The render is the LAST step of a completed exploration. Two options (decide at build, default A):
     **A (default)** — the 3a Workflow's per-step synthesis barrier completes, then the Workflow's final
     stage calls the exploration render-job (a `claude -p` maker pipeline, NOT a visible-terminal
     dispatch — same constraint as requirements: "a page view must never pop a visible terminal").
     **B** — lazy, request-path: first viewer load of a goal whose md set has a newer digest than the
     published `exploration.html` triggers a background render-job (exact parity with requirements'
     `GET /render` single-flight). B gives free staleness handling but adds a request-path module; A is
     simpler and keeps the render inside the Workflow. → This is a `[PENDING build]` seam; default A,
     fall back to B only if the Workflow can't cleanly invoke a background job. Mark in the ledger.

**Design review:**
- **Spec consistency (`cast-requirements-render.collab.md`):** This sub-phase ADDS a second render
  consumer (exploration) to a spec that 2b already updated to describe the dual viewer + exploration
  consumer. ⚠️ Confirm 2b's `/cast-update-spec` actually documented the exploration render path; if it
  only documented the *viewer* and not the *exploration render-job + the 3 exploration maker agents +
  the FR-017 checker rubric*, add a `/cast-update-spec` activity here to record them. → Delegate:
  `/cast-update-spec` on `docs/specs/cast-requirements-render.collab.md` adding the exploration
  WHAT/HOW/checker trio + the `exploration.html` path + the FR-017 4-criteria checker contract, and
  REGISTER the new agents. Review the diff before applying. (US4 "render not authored" + US7 "selectable
  units, no ids" are REUSED unchanged — flag only the additive exploration behavior.)
- **Naming:** `cast-exploration-{what,how,render-checker}` follows `cast-{noun}-{role}` and the
  `cast-hat-researcher` (2a) / `cast-requirements-*` family ✓. Service module
  `exploration_render_service.py` mirrors `render_job_service.py` ✓. Publish helper
  `publish_exploration_html` mirrors `publish_maker_html` ✓.
- **Architecture (single-helper discipline):** `_atomic_write`, `AgentRunner`/`ProductionAgentRunner`,
  `extract_render`, `content_hash` MUST be reused, not re-implemented. ⚠️ Risk: copy-paste drift if they
  stay private to `render_job_service`. Mitigation: extract the truly-shared trio (runner + atomic-write
  + sentinel extraction) into `cast_server/render_common/` so BOTH render-jobs import one copy. This is a
  small refactor of `render_job_service.py` (replace its private defs with imports from `render_common`)
  — keep it behavior-preserving and covered by its existing tests.
- **Error & rescue (FR-016/US12 inheritance):** A `null`/dropped hat cell from 3a must render as an
  explicit "attempted, dropped" marker, never a silent gap (surface, don't suppress — matches the user's
  standing rule). The WHAT doc carries `status: dropped` per hat; the HOW page renders the marker; the
  checker's criterion-1 judges against the *applicable* (non-gated) set, so a dropped always-on hat is a
  visible degradation, not a checker pass. Terminal states mirror requirements: clean / flagged
  best-attempt / deterministic-fallback — no fourth silent path.
- **Security:** The render-job reads md files under `goals/{slug}/exploration/` only — path-validate the
  corpus glob to the goal's own tree (no `..` escape), mirroring the requirements `_CORPUS_FILES`
  allowlist discipline. `<iframe srcdoc sandbox="allow-scripts allow-popups">` with NO
  `allow-same-origin` (2b's null-origin decision) means the page's scripts can't reach the host origin
  except via the 3b postMessage bridge ✓.
- **Cost/loop discipline:** the quality loop is bounded ONLY by the anti-infinite-loop ceiling, never by
  cost or model tier (the model's binding owner decision) ✓ — carry it forward unchanged.

---

## Build Order (within Sub-phase 4)

```
                          ┌─► (2) cast-exploration-what ─┐
(1) render-job skeleton ──┤                              ├─► (5) quality loop ─► (6) atomic publish + viewer/commenting wiring ─► (7) entrypoint
  + shared-primitive      ├─► (3) cast-exploration-how ──┤
  extraction              └─► (4) cast-exploration-       ┘
                              render-checker
```

**Critical path:** (1) skeleton + shared-primitive extraction → the three agents (2/3/4, parallelizable
once the WHAT-doc + sentinel + verdict contracts are pinned by (1)) → (5) quality loop → (6) publish +
inherit viewer/commenting → (7) entrypoint. Activities 2, 3, 4 are **parallel** once (1) fixes the three
inter-agent contracts (WHAT-doc shape, HOW sentinel/DOM, checker verdict shape).

## Design Review Flags

| Flag | Action |
|------|--------|
| Spec: confirm 2b's `/cast-update-spec` covered the exploration RENDER (agents + path + FR-017 checker), not just the viewer | Add `/cast-update-spec` on `cast-requirements-render.collab.md` for the exploration trio + `exploration.html` path + FR-017 contract; register the 3 new agents (activity 6 / design review) |
| Architecture: `_atomic_write` / `AgentRunner` / `extract_render` / `content_hash` must not be copy-pasted | Extract shared trio to `cast_server/render_common/`; both render-jobs import one copy (activity 1) |
| Error: a `null`/dropped hat cell must render as an explicit marker, not a silent gap | WHAT `status: dropped` → HOW renders marker → checker judges against applicable set (activities 2/3/4) |
| Security: corpus glob path-validated to the goal's own `exploration/` tree | Path-validate the md corpus loader (activity 1) |
| Distinctness is the novel checker axis vs. the requirements checker | Encode FR-017 criterion 3 ("hats DISTINCT not blended") as a first-class verdict dimension; do not let it collapse into "visual quality" (activity 4) |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| The HOW agent BLENDS hats into a synthesized paragraph (the exact failure FR-017 c3 guards against) — LLMs love to "synthesize" | High | The layout contract mandates per-hat separate attributed units; the checker's criterion-3 fails a blended page and feeds distinctness rework; the WHAT doc pre-separates takes per `hat_id` so HOW receives them already distinct |
| Cloning `render_job_service.py` drifts the shared primitives (atomic-write / runner / sentinel) | Med | Extract the shared trio to `render_common/`; import, never copy; keep `render_job_service`'s existing tests green through the refactor |
| 2b's viewer glob or 3b's `artifact_ref` doesn't actually pick up `exploration.html` for free | Med | Verify early (activity 6); if the glob excludes it, the fix is a one-line 2b collector tweak (flag as a 2b revision) — the `kind` seam itself is unchanged |
| Source identity: an md *tree* has no single hash, so staleness detection is non-obvious | Med | `source_digest` = digest over the sorted (relpath, content_hash) set; embed it in the published page as the readiness key (mirrors requirements' embedded source-hash) |
| The checker's "POV legible at zero-click" needs a deterministic zero-click extract that an HTML page (not slides) supports | Low | Build an exploration `extract_zero_click_view` equivalent (POV headers + open content, hat takes that are visible without interaction); run criterion-2 on it FIRST, structurally |
| Render-job entrypoint coupling to the 3a Workflow | Low | `[PENDING build]` seam, default A (Workflow final stage calls the job); fallback B (lazy request-path single-flight) reshapes only that one seam |

## Open Questions

- **Entrypoint (A vs B):** does the 3a Workflow's final stage invoke the exploration render-job
  (default A), or is it a lazy request-path single-flight render on first viewer load (B, exact
  requirements parity)? Default A; resolve at build. Captured as a `[PENDING build]` seam.
- **Shared-primitive home:** extract the runner + atomic-write + sentinel trio to a new
  `cast_server/render_common/` (default, cleanest), or import them directly from `render_job_service`
  (smaller diff, but makes the requirements module a dependency of the exploration module)? Default =
  extract to `render_common`.
- **Source identity granularity:** is `source_digest` over the WHOLE `exploration/` tree, or only the
  files the render actually consumes (playbooks + surviving research notes + summary)? Leaning: only the
  consumed set, so an unrelated md write doesn't needlessly invalidate the render.

## Spec References

| Spec | Sections referenced | Conflicts found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` | US4 "render not authored artifact" (atomic, generated-by stamp) — REUSED for `exploration.html`; US7 "selectable units, no ids" DOM contract — REUSED so 3b commenting anchors; the WHAT/HOW/checker maker-pipeline pattern — CLONED | Additive: a SECOND render consumer (exploration) + 3 new exploration maker agents + the FR-017 checker rubric. Action: `/cast-update-spec` (verify 2b didn't already cover the render path; if not, add it here). No conflict with US4/US7 — reused unchanged. |
| `cast-requirements-roundtrip.collab.md` | Same-door comment intake — INHERITED via 3b's `artifact_ref` | None. Write-back of comments to exploration md is explicitly OUT OF SCOPE (exploration.html is a render; comments are feedback only). |
| `refined_requirements.collab.md` (this goal) | FR-009/010, FR-017 (locked 4-criteria rubric), US7, SC-005, the "angles are generative hats, user collates, distinct not blended" principle | None — this sub-phase implements them. |

## Suggested Revisions to Prior Sub-Phases

- **To 2b (dual viewer):** if 2b's `/cast-update-spec` on `cast-requirements-render.collab.md` documented
  only the *viewer* behavior and the exploration consumer at a high level, it should be extended (or this
  sub-phase extends it) to also record the exploration *render-job + the 3 maker agents + the FR-017
  checker contract*. Not a conflict — a completeness gap; flagging so the spec stays the source of truth.
- **To 2b (viewer glob):** Sub-phase 4 assumes `exploration.html` is picked up by `api_goals.py
  get_phase_tab`'s `exploration/` glob for free. If 2b's `_add_html_file` collector only globs specific
  filenames (not `exploration/*.html`), add `exploration.html` to its glob. One-line change; flagged so
  it's owned, not silently assumed.
- **No revision to 3a or 3b** — their contracts (md paths, `artifact_ref`, postMessage bridge) are
  consumed exactly as specified; Sub-phase 4 writes no comment or Workflow code.

## Plan Review Decisions (2026-06-20)

- **Issue #2 (Architecture / DRY) — Decision: 2A (accepted).** Extract to `render_common` the **real shared core**: primitives (runner/atomic/sentinel) + the **stage-loop orchestration skeleton** + `decide_quality` + the **verdict-schema base**. `exploration_render_service` supplies ONLY exploration prompts + `ExplorationJobState` + the corpus loader (target **<500 lines**). **Reject** the direct-import coupling (would make requirements a dependency of exploration). Do the `render_job_service` refactor behind its existing green test suite. Maker PROMPTS stay forked (content genuinely differs) with provenance.
- **Issue #7 (Tests) — Decision: T3 A (accepted).** Add a Phase 4 verification case: feed the render-job a 3a output where **one step is fully degraded** (placeholder playbook, zero hat notes); assert the page renders that step as **explicitly degraded** AND the render-checker does **not false-pass** criterion-1 ("every applicable hat visible per step").
