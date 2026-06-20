# Reconciliation — exploration-pipeline-nxm fan-out detailed planning (8 sub-phases)

**Goal:** `exploration-pipeline-nxm-claude-workflow-9010-angle`
**Reconciliation date:** 2026-06-20
**Inputs:** the cumulative ledger (`exploration-pipeline-nxm-decisions-so-far.md`, Rounds 1–5),
`refined_requirements.collab.md`, `plan.collab.md`, the 8 sub-phase plans, plus spot-checks of
`cast-requirements-render.collab.md` (FR-057, US7/US8) and `cast-requirements-roundtrip.collab.md`.

## Verdict

**COHESIVE — ready for execution.**

The 8 sub-phases were planned against a shared, disciplined ledger and they slot together cleanly.
Every cross-sub-phase interface matches on both sides; naming is canonical throughout (no conflicts
table needed); dependency ordering is sound; the `artifact_ref` generalization (special-focus #9) is
correctly additive, defaulted, same-door, and consumed correctly by Sub-phase 4. The only items found
are **two pre-flagged, self-owned completeness nudges** (a 2b glob check and a 2b spec-extension
completeness note) that the plans themselves already raise and assign owners for — neither blocks
execution. No plan edits are required to begin.

---

## 1. Cross-sub-phase interface table (Produces → Consumed By)

| Sub-phase | Produces (interface / artifact) | Consumed by | Match? |
|-----------|----------------------------------|-------------|--------|
| **1a** | Decision: entrypoint mechanism (Option A skill/command vs B server-dispatch); toy proof of `(approved_steps, hat-matrix)` arg shape + concurrency cap | 3a (single `[PENDING 1a]` entrypoint seam) | ✓ |
| **1b** | Decision: in-iframe commenting (postMessage bridge) vs full-page fallback; `<iframe srcdoc>` viability; viewer seam touchpoints | 2b (embed), 3b (bridge vs fallback `[PENDING 1b]`) | ✓ |
| **2a** | `cast-hat-researcher` pure-fn contract `(step, hat_id, goal_context) → 1 note` at `research/{NN}-{step-slug}-{hat-id}.ai.md` + `.output.json`; hat_id vocabulary (3 always-on + 5 gateable) | 3a (`parallel()` over hats), 5 (filename-set verification) | ✓ |
| **2b** | Dual viewer: artifact-dict `kind` discriminator (`markdown`/`html`); `_add_html_file` collector; `api_artifacts.py:52` gate widened; `macros/markdown_viewer.html` iframe/srcdoc branch; render-class `.html` (US4, `authorship=None`); `/cast-update-spec` on requirements-render | 3b (injects layer into the srcdoc HTML branch), 4 (`exploration.html` inherits viewer with zero new code) | ✓ |
| **3a** | `agents/cast-explore-workflow/workflow.py`; `hat-matrix` arg shape `{goal_slug, goal_context, steps:[{nn,slug,name,hats[]}]}`; md artifacts at `research/`,`playbooks/`,`summary.ai.md`; unchanged `cast-playbook-synthesizer` barrier; new `cast-explore-workflow.collab.md` spec | 4 (WHAT agent's only content source = these md files), 5 (e2e run + SC-001/004/009 + md byte-compat) | ✓ |
| **3b** | Artifact-keyed comment seam: `artifact_ref` field on create/relocate/displacement + nullable `requirement_comments.artifact_ref` column; `_resolve_served_render_html(artifact_ref)`; postMessage `cch:submit`/`cch:submitted` bridge contract; `anchor_space='render'`, verbatim-substring relocation | 4 (`exploration.html` served with `artifact_ref="exploration/exploration.html"`, zero new comment code), 5 (comment e2e SC-007) | ✓ |
| **4** | `cast_server/services/exploration_render_service.py` + `publish_exploration_html(...)` → `goals/{slug}/exploration/exploration.html`; agents `cast-exploration-what` / `cast-exploration-how` / `cast-exploration-render-checker` (FR-017 4-criteria); shared trio lifted to `cast_server/render_common/` | 5 (render-checker verdict SC-005; viewer+comment SC-006/007) | ✓ |
| **5** | Unattended e2e run; SC-001..SC-009 verification matrix; md byte-compat with `cast-high-level-planner`; `parity-notes.md` (4 axes) | User (merge decision) | ✓ |

**Workflow arg-shape chain (1a → 3a → US11/FR-014):** 1a demonstrates `(approved_steps, hat-matrix)`;
3a pins `hat-matrix = {goal_slug, goal_context, steps:[{nn,slug,name,hats:[hat_id…]}]}` with hat_id
drawn verbatim from 2a. Consistent end-to-end.

**`cast-hat-researcher` contract chain (2a → 3a):** 3a's `parallel()` calls 2a's pure-fn at the exact
I/O contract; 1a used a stub at the same contract. Match confirmed. 3a additionally **globs
`research/{NN}-{slug}-*.ai.md` on disk** for the synthesis barrier (not the in-memory return) — a
hardening, contingent on 2a's note write being atomic (see §5 / hidden-dep note).

---

## 2. Canonical naming table

**No conflicts found** — naming is already canonical across all 8 plans. Recording the canonical set
for reference (every plan uses these verbatim; no divergence to resolve):

| Concept | Canonical name | Notes |
|---------|----------------|-------|
| Single-hat research agent | `cast-hat-researcher` | `cast-{noun}-{role}` ✓ |
| Always-on hat ids | `contrarian`, `first-principles`, `90-10` | literal; matches spec `…-90-10.ai.md` |
| Gateable hat ids | `expert-practitioner`, `tool-landscape`, `ai-native`, `community-wisdom`, `framework-methodology` | |
| Workflow script / agent dir | `cast-explore-workflow` (`agents/cast-explore-workflow/workflow.py`) | |
| Content/HOW/checker agents | `cast-exploration-what`, `cast-exploration-how`, `cast-exploration-render-checker` | `cast-{noun}-{role}` ✓ |
| Comment artifact selector field | `artifact_ref` (goal-relative path) | mirrors `block_ref`/`anchor_space` |
| Exploration HTML path | `goals/{slug}/exploration/exploration.html` | |
| Render note paths | `exploration/research/{NN}-{step-slug}-{hat-id}.ai.md`, `exploration/playbooks/{NN}-{step}.ai.md`, `exploration/summary.ai.md` | hard contract w/ `cast-high-level-planner` |
| Viewer discriminator | `kind` (`"markdown"`/`"html"`) | not `type`/`format` |
| postMessage bridge types | `cch:submit` / `cch:submitted` | namespaced under existing `cch` prefix |

---

## 3. Conflicts found (with recommended resolutions)

**None blocking.** Two pre-flagged, self-owned completeness nudges (the plans raise these themselves):

| # | Item | Raised by | Status / recommendation |
|---|------|-----------|--------------------------|
| N1 | **2b viewer glob may not pick up `exploration.html` for free.** Sub-phase 4 assumes `api_goals.py get_phase_tab`'s `exploration/` glob admits `exploration.html`. If 2b's `_add_html_file` globs specific filenames instead of `exploration/*.html`, a one-line glob tweak is needed. | 4 (Suggested Revisions → 2b) + 4 risk table | Self-owned: Sub-phase 4 activity 6 verifies early and, if needed, applies the one-line 2b collector tweak. The `kind` seam is unchanged either way. **No pre-edit required.** Recommend 2b authors glob `exploration/*.html` (and generally `*.html` per subdir) rather than a filename allowlist, which removes the contingency entirely. |
| N2 | **2b spec-extension completeness.** 2b's `/cast-update-spec` on `cast-requirements-render.collab.md` documents the dual-viewer behavior + exploration consumer at a high level; the exploration *render-job + 3 maker agents + FR-017 checker contract* belong in the spec too. | 4 (Suggested Revisions → 2b) | Not a conflict — a completeness gap. Self-owned: Sub-phase 4 extends the spec (it owns those agents). Recommend 4 perform the spec extension at its `/cast-update-spec` step so the spec stays source-of-truth. **No pre-edit required.** |

All other "Suggested Revisions to Prior Sub-Phases" sections read **None required** (1a, 1b, 2a, 2b,
3a*, 3b*, 5) — consistent with the ledger. (*3a and 3b carry forward clarifications, not revisions —
see §5.)

---

## 4. Scope gaps / overlaps (esp. shared-file edits across 2b / 3b / 4)

### Shared-file ownership map — clean, sequenced, no collisions

| File | 2b | 3b | 4 | Collision? |
|------|----|----|---|------------|
| `api_artifacts.py` (`validate_artifact_path_read`, line ~52/55) | **OWNS** — widen read gate to admit `.html` | **REUSES** the same `validate_artifact_path_read` guard to validate `artifact_ref` (no second validator) | — | No — 2b extends; 3b reuses 2b's widened guard. Correct same-validator discipline. |
| `api_goals.py get_phase_tab` glob (~line 422) | **OWNS** — widen glob to `*.html`, add `_add_html_file` collector | — | **DEPENDS** on the glob catching `exploration.html` (N1) | No — single owner (2b); 4 only consumes. |
| `macros/markdown_viewer.html` | **OWNS** — adds `kind` param + iframe/srcdoc branch | **EXTENDS** the HTML-artifact branch to inject the comment layer + bridge into the srcdoc HTML | — | **Sequential, not concurrent** — 3b depends on 2b (dependency-ordered). 3b adds to the branch 2b created. No conflict given 2b→3b ordering. |
| `comment_service.py` (`_resolve_served_render_html`, `create_comment`) | — | **OWNS** — artifact-keyed resolver + `artifact_ref` threading | — | No — single owner (3b). |
| `api_requirements.py` (`CreateCommentRequest`, create handler) | — | **OWNS** — add optional `artifact_ref` field | — | No — single owner (3b). |
| `requirement_comments` table | — | **OWNS** — add nullable `artifact_ref` column (additive migration) | — | No — single owner (3b). |
| `render_job_service.py` / `render_common/` | — | — | **OWNS** — build parallel `exploration_render_service.py`; extract shared trio (runner + atomic-write + sentinel) to `cast_server/render_common/`, refactor `render_job_service.py` to import it | No — 4 is the only writer; refactor keeps existing tests green. |

**Scope gaps:** none. Every capability a later sub-phase needs is produced earlier:
- 4 needs viewer (2b ✓), commenting (3b ✓), md substrate (3a ✓).
- 5 needs full pipeline (1a→3a engine, 2b/3b/4 surface) — all present.
- 3a needs the single-hat agent (2a ✓) and the entrypoint decision (1a ✓).

**Scope overlaps:** none harmful. The only two-toucher files — `api_artifacts.py` and
`markdown_viewer.html` — are touched by 2b (owner) and then **extended** by 3b along the 2b→3b
dependency edge, never concurrently. The `render_common/` extraction is owned solely by 4.

---

## 5. Hidden dependencies / dependency-graph updates

Two carried-forward clarifications surfaced (both already noted in plans, recorded here so they are
owned, not lost):

- **3a → 2a (atomicity).** 3a's synthesis barrier globs research notes off disk (hardening against a
  child that writes then soft-fails). This assumes 2a's note write is atomic (note bytes, then
  `.output.json` terminal signal). **Action:** 2a authors should confirm the note write is atomic
  (temp-then-rename) — a small 2a hardening **only if** the write is currently non-atomic. Contingent,
  not a known defect.
- **5 → 3a (md shape).** Phase 5's `cast-high-level-planner` byte-compat check leans hardest on
  `playbooks/*.ai.md` + `summary.ai.md` being shape-unchanged (US5). If Activity C surfaces a real
  shape regression, that is a **3a defect** (synthesizer was to be unchanged) routed back to 3a — a
  contingent finding, not a known revision.

The published dependency graph from `plan.collab.md` holds unchanged:

```
Phase 1a (spike) ─────────────────► Phase 3a ─┐
Phase 2a (hat agent) ─────────────► Phase 3a  ├─► Phase 4 ─► Phase 5
Phase 1b (spike) ─► 2b ─► 3b ─────────────────┘
```
Critical path: 1a → 2a → 3a → 4 → 5 (Track B 1b→2b→3b lands before Phase 4 convergence). No hidden
edges change this; the 3a→2a and 5→3a items above are *contingency* edges, not new hard deps.

---

## 6. `artifact_ref` assessment (special-focus #9)

**PASS on all three sub-checks.** This is the load-bearing generalization and it is correctly designed.

**(a) Additive + defaulted — existing requirements commenting unaffected.** ✓
- `_resolve_served_render_html(goal_slug, db_path, goals_dir, artifact_ref: str|None=None)`: `None` →
  today's `refined_requirements.html` (backward-compatible default).
- `CreateCommentRequest.artifact_ref: str|None = None` — default preserves the requirements contract
  verbatim; no new endpoint (same-door honored).
- New `requirement_comments.artifact_ref` column is **nullable, NULL = requirements**, additive
  migration, no backfill. 3b mandates **byte-identical regression tests on the default path** before
  touching exploration.

**(b) Consistent with `cast-requirements-render` US7/US8 + `cast-requirements-roundtrip` same-door.** ✓
- Spec FR-057 establishes `block_ref`/`anchor_space` as **server-resolved, never client-trusted**.
  `artifact_ref` is correctly distinguished: it is a *path selector* (must originate client-side to
  say *which* doc the quote came from), so it is client-supplied **but server-validated to path-shape
  only** (`.html`-only, goal-relative, no `..`/absolute) via the existing `validate_artifact_path_read`
  guard. `block_ref`/`anchor_space` remain server-resolved and out of the POST body. This is the right
  trust split, not a violation of the never-client-trust rule.
- US8 same-door preserved: one endpoint, one `create_comment` write path, one new optional field — no
  parallel comment route. US7 "selectable units, no ids" preserved — no anchor-id scheme introduced
  (deferred per spec Out of Scope). Roundtrip same-door intake reused; **no write-back to exploration
  md** (comments are feedback-only — confirmed out of scope by both 3b and 4).
- 3b's Activity G updates the spec (`/cast-update-spec`) to state the render-space anchor is
  **artifact-keyed**, keeping the spec the source of truth — correct convention compliance.

**(c) Consumed correctly by Sub-phase 4.** ✓
- 4 serves `exploration.html` and the commenting "inherits for free" by being served with
  `artifact_ref="exploration/exploration.html"` (4's interface table line 55, activity narrative line
  232, SC-007 line 128). The string matches 3b's worked example exactly. 4 writes **zero comment
  code**. Resolver, relocation, and displacement all re-target against the same artifact the quote was
  minted from (the column stores `artifact_ref` per-row).

**Security note (already handled by 3b):** the bridge POST carries a client-supplied `artifact_ref` →
path-traversal surface. 3b mandates server-side validation via the existing guard and matches the
postMessage event `source` against the specific iframe `contentWindow` (null-origin srcdoc can't be
URL-allowlisted). Correct.

---

## 7. Verification chain (checklist #7)

Phase 5's SC-001..SC-009 matrix covers all 9 SCs with a concrete check each:
- SC-001 (filename-SET equality vs persisted hat-matrix, not just counts), SC-002 (prompt inspection),
  SC-003 (90/10 note exists per step + First-Principles grep for absent 80/20), SC-004 (playbook
  count = N), SC-005 (render-checker verdict on FR-017's 4 criteria), SC-006 (dual-viewer UI),
  SC-007 (comment e2e via same-door + `artifact_ref`), SC-008 (requirements HTML in viewer),
  SC-009 (unattended completion observed during Run 1).
- Plus md-substrate byte-compat with `cast-high-level-planner` and the `parity-notes.md` (4 axes:
  playbook quality, angle sharpness, cost, time). Collision-safe snapshotting of both pipelines'
  output trees before any read.

Each sub-phase's own verification proves its outcome (2a: 8 distinct notes + no-80/20 grep; 3a: full
run + forced-failure null cell; 2b: byte-identical md regression + dual-render; 3b: default-path
byte-identical regression + comment e2e; 4: render-checker verdict + free viewer/comment inheritance).
**Chain is complete.**

---

## 8. Effort / sequencing sanity (checklist #8)

Critical path 1a→2a→3a→4→5 is reasonable; Track B (1b→2b→3b) parallelizes and lands before Phase 4.
No sub-phase is obviously under- or over-scoped: 3a (engine, 3–4 sessions) and 2a (hat agent, 2–3) are
the heaviest on the critical path, which is appropriate. 4's `render_common/` extraction is the one
cross-cutting refactor and is correctly scoped as "extract shared trio, keep existing tests green."

---

## 9. Skill / convention compliance (checklist #10)

- Agent names follow `cast-{noun}-{role}`: `cast-hat-researcher`, `cast-exploration-what/how/render-checker` ✓
- Render-class / US4 honored: 2b sets `.html` `authorship=None`, no edit button, atomic + generated-by stamp ✓
- US7 "selectable units, no ids" honored: no anchor-id scheme (deferred) ✓
- Same-door (US8): one endpoint, one optional field, no parallel route ✓
- `/cast-update-spec` on `cast-requirements-render.collab.md` present in 2b (and extended in 3b/4) ✓
- New `cast-explore-workflow.collab.md` spec created in 3a + registered in `_registry.md` ✓
- "Surface, don't suppress" applied to dropped/queued cells (3a) and bridge POST failures (3b) ✓

---

## Final verdict

**COHESIVE — ready for execution.** No sub-phase plan requires editing before execution begins. The
two self-flagged nudges (N1 glob check, N2 spec-extension completeness) are already owned inside
Sub-phase 4's own activities, and two contingency edges (3a↔2a atomicity, 5↔3a md-shape) are recorded
for awareness. Proceed.
