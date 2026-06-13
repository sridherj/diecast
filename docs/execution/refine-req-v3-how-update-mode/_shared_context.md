# Shared Context: refine-req-v3-how-update-mode (HOW Two-Mode + Render-Snapshot Anchoring)

> Read this file at session start before executing any sub-phase plan in this project.

## Source Documents

- **Plan (authoritative):** `docs/plan/2026-06-12-refine-requirements-v3-how-update-mode-render-anchoring.md`
- **Decisions-so-far (binding owner decisions):** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
  (see the tail section "Post-Phase-5 follow-up: HOW CREATE/UPDATE mode + readability-over-verbatim").
- **Spec (the contract this phase reverses + re-spec's):** `docs/specs/cast-requirements-render.collab.md` (**currently v7** on disk).
- **Prior execution context (the seams this phase consumes):**
  `docs/execution/refine-req-v3-phase3/_shared_context.md` (the WHAT→HOW maker pipeline),
  `docs/execution/refine-req-v3-phase4b/_shared_context.md` (comment survival + reanchor v2).

## Project Background

The Phase-5c nine-family sweep published all nine families but flagged three (`bug_fix`,
`pilot_poc`, `random_idea`) as HOW-layer carry-forwards. The owner's diagnosis: the HOW maker
treats CREATE and UPDATE identically — it regenerates the whole page from scratch on every source
edit, which is exactly when it paraphrases lead units and trips the verbatim-carriage gate. The
reframe (decisions-so-far.md, "Post-Phase-5 follow-up"): **verbatim carriage was never the goal —
the most human-readable page is.** Verbatim was only a proxy that kept source-anchored comments
placeable. This phase removes the proxy properly:

1. **HOW gets a two-mode contract.** CREATE = fresh, readability-first, paraphrase leaf text freely.
   UPDATE = start from the prior render, re-render only changed blocks, keep unchanged blocks
   byte-identical. A massive-change threshold flips UPDATE back to CREATE.
2. **Comment anchoring moves from the canonical source to the rendered-page snapshot.** A comment's
   `quoted_text` is minted from / validated against / displacement-checked against / re-anchored
   within the **published render's container text**, with a server-resolved **`block_ref` bridge**
   (the canonical id of the unit container the quote landed in) keeping every comment traceable back
   to source space. UPDATE mode is precisely what keeps render-anchored comments alive across edits.

Planning is done (HOLD SCOPE; the plan body carries an end-of-review **Decisions** appendix with six
executor-level refinements **already applied inline**). This project **executes** the sub-phases.

## Operating Mode

**HOLD SCOPE.** The owner direction is an enumerated feature set: `{two-mode HOW}` + `{relax
leaf-text verbatim for readability}` + `{comment anchoring source→render snapshot}` +
`{massive-change threshold}` + `{regression tests}` + `{re-run the 3 flagged families}`. No extras,
no cuts. The borderline `pilot_poc`/`random_idea` HOW fixes are resolved **IN** (Sub-phase 4) because
the validation target "re-run the 3 flagged families → clean" is unreachable without them. A dedicated
paraphrase-meaning-fidelity checker is explicitly **OUT** (recorded as an Open Question + a spec
known-limitation note).

## ⚠️ The Crux Decision (locked, read first): comments anchor to the render snapshot

A comment's full lifecycle runs against the **published render's text** (the same
`container_text_index` text space `maker_gate` already walks), no longer the canonical `.collab.md`.
A server-resolved `block_ref` (the canonical id of the enclosing labeled unit container) bridges back
to source space. What this **reverses** — flagged loudly because it is the load-bearing call:

- **US16 verbatim-carriage clause** — blanket verbatim carriage is **superseded**. What survives:
  anchor labels (canonical ids printed verbatim exactly once) + the one-unit-one-container DOM rule.
  What's removed: the copy-exact obligation on leaf requirement text in CREATE mode.
- **US8/US12 source-anchoring contract** — quote validation + `displaced = quoted_text not in
  current_text` re-target the **served render artifact** (was the `.collab.md`).
- **US19 survival classification** — reorients to render space: in-block = the quote placed inside a
  labeled unit container on the render it was minted against; survival = it places in the same
  `block_ref`'s container on the next render. UPDATE byte-identity makes survival **structural** for
  unchanged blocks; comments on modified/removed blocks route to re-anchoring instead of blocking.

**Why this is safe to lock without a spike:** placement machinery is *already* render-side
(`requirements_comments.js` does `indexOf` over the rendered DOM; quotes are minted by selecting
rendered text). Only the *validation/displacement* reads point at the source today. The genuinely
unproven assumption is elsewhere — that UPDATE mode can hold unchanged blocks byte-identical — and
that is **Sub-phase 1a's spike** (its verdict selects 3b's mechanism), **not** the anchoring decision.

## The 1a verdict is a dependency, not a formal orchestrator gate (owner-decided)

Sub-phase 1a's PASS/FAIL verdict **selects the Sub-phase 3b UPDATE mechanism** and is binding, but it
is materialized as a **recorded verdict in sp1a's spike note**, NOT a `gate_`/`G`-prefixed orchestrator
stop (owner decision, 2026-06-12). The manifest has **no gate rows**. sp3a and sp3b each list "the 1a
verdict" as a hard dependency and **must read** `docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/verdict.md`
before building the UPDATE prompt section. The two mechanisms:

- **PASS** (≥95% of unchanged containers byte-identical across ≥5 trials/doc) → **gate-enforced LLM
  copy**: HOW emits the full page; a new `check_update_fidelity` gate verifies byte-identity; violations
  take the standard structural retry.
- **FAIL** → **deterministic splice**: the server keeps unchanged container bytes from the prior render
  and splices HOW-rendered changed-block fragments; byte-identity is guaranteed by construction, at the
  cost of a fragment-rendering HOW sub-contract.

If the spike has not been run when sp3a/sp3b start, **stop and run it first** (or surface the missing
verdict) — do not guess the mechanism.

## Owner Principles binding on every fork (from decisions-so-far.md)

- **Surface, don't suppress.** Degraded output ships **flagged + machine-readable**, never a silent
  swap. The `.comment-unplaced` tray badge, the `structural_violation`/`served-by` stamps, and the
  `_note`-on-degrade-to-CREATE discipline are all instances of this.
- **The structural override / deterministic fallback fires ONLY on literal no-output** (crash / timeout
  / no extractable render). A structurally-broken-but-present attempt is served + flagged, never the
  silent swap for the plain deterministic page.
- **Every UPDATE precondition failure degrades to CREATE with a job `_note`** — zero silent failures,
  never a job error. CREATE is always a safe answer.

## Codebase Conventions

- **Pure render package vs. service split.** `cast_server/requirements_render/` is pure (no I/O, DB,
  LLM) — `maker_gate.py` (the gates incl. `check_update_fidelity`), `block_diff.py`, `comment_anchor.py`
  live here. All I/O / DB / subprocess work lives in `cast_server/services/` — `render_job_service.py`
  (mode decision, recovery, prompt assembly, publish-boundary dispatch), `comment_service.py`,
  `requirements_render_service.py`, `requirement_version_service.py`.
- **Single-implementation discipline (HARD).** ONE container-text walker: `container_text_index(html)`
  in `maker_gate.py:259` — **import it; never copy the walk.** ONE markdown stripper:
  `strip_inline_markdown` in `goal_card.py`. ONE deterministic diff engine: `block_diff.diff_blocks` /
  `summarize` / `_key` (FR-024 extend-never-fork — consumed unchanged, never edited).
- **Subagent bare-output carve-out.** `cast-requirements-how` / `cast-requirements-what` /
  `cast-comment-reanchor` are tool-free `claude -p` subagents (`--tools ""` makes "never writes the
  canonical `.collab.md`" structural), bare output (no `.output.json` envelope). Contract extensions are
  **additive supersets** — every new input optional so existing call sites stay byte-valid.
- **Flat service functions, injectable seams.** `comment_service`, `requirement_version_service`,
  `render_job_service` helpers are module-level functions with `*, db_path: Path | None = None` /
  `goals_dir` test seams.
- **Config knobs** follow the `RENDER_*` / `QUALITY_*` env-overridable convention
  (`config.py:183 RENDER_STAGE_TIMEOUTS`, `config.py:233 QUALITY_MAX_ATTEMPTS`). New: `RENDER_UPDATE_MAX_CHANGED_FRACTION`,
  `RENDER_UPDATE_MAX_PRIOR_BYTES`.
- **DB migrations:** additive only; `db/schema.sql` + `tests/test_schema_migration.py` cover every
  column add. Old rows keep a back-compatible default.
- **LLM text into HTML = autoescaped only**, never `innerHTML` / `| safe`.
- **`build/render-jobs/{slug}/{hash12}/` is non-CI runtime state.** This phase makes it carry
  cross-job **recovery** state (`source.md`, `what-doc.md`, prior render). Wiping it only costs UPDATE
  capability for the next render (degrades to CREATE) — never breaks publish.
- **Test prefixes:** default-CI `pytest cast-server/tests/test_*.py`; agent/eval gates use the `eval_`
  prefix (`eval_family_sweep.py`, `eval_sc003_survival.py`, `eval_reanchor.py`) — **not** collected by
  default CI; run them explicitly.
- **No browser in autonomous runs.** Visual / tray / browser e2e is a **static verdict + human-eyeball
  carry-forward**, never a blocking gate (project convention).

## Key File Paths (grounded against the live tree)

| File | Role in this phase |
|------|--------------------|
| `cast-server/cast_server/requirements_render/maker_gate.py` | `container_text_index` (**:259**, shared walker — import), `check_html` (**:573**, drops the blanket verbatim-carriage class in 3b), `check_what_doc` (**:350**), `check_comment_survival` (**:849**, reoriented to render space in 3b), `Container.unit_at` (**:175**). **3b adds `check_update_fidelity`; 4 adds the empty-shell `check_html` class.** |
| `cast-server/cast_server/requirements_render/goal_card.py` | `strip_inline_markdown` (import, never copy) |
| `cast-server/cast_server/requirements_render/block_diff.py` | `diff_blocks` (**:93**), `summarize` (**:174**), `_key` (**:70**) — the deterministic changed-set. **NOT modified** (consumed). |
| `cast-server/cast_server/requirements_render/comment_anchor.py` | `resolve_block_ref(old_content, quoted_text)` (**:29**), `resolve_block_context` (**:52**) — source-space resolvers. **2 adds the render-space resolver path.** |
| `cast-server/cast_server/services/render_job_service.py` | `JobState` (**:247**), `gate_html` (**:670**), `_build_how_prompt` (**:557**), `emit_change_requests` (**:1188**), `_what_doc_job_ref` (**:1125**), `_compare_and_publish` (**:1476**), `reaper_ceiling_seconds` (**:1600**, reads `RENDER_STAGE_TIMEOUTS`), `_start_job` (**:1665**). **3a adds mode decision + recovery + persists `source.md`/`what-doc.md`; 3b wires it live + the publish-boundary reanchor dispatch.** |
| `cast-server/cast_server/services/requirements_render_service.py` | `publish_maker_html` (**:201**, served-by / human-review / source-hash envelope), `current_source_hash` (**:182**), `RenderResolution` (**:256**) |
| `cast-server/cast_server/services/comment_service.py` | `create_comment` (**:92**), `list_comments` (**:125**, derived `displaced`), `resolve_comment` (**:206**), `relocate_comment` (**:244**). **2 re-targets create/list/relocate to render space + adds `block_ref`/`anchor_space`.** |
| `cast-server/cast_server/db/schema.sql` | `requirement_comments` (**:131**, gains `block_ref`/`anchor_space` in 2), `comment_events` (**:146**, migration disposition trail) |
| `cast-server/cast_server/routes/api_requirements.py` | comment/version API; the route-level 422 verbatim-substring relocate backstop (**2 re-targets it for render-space comments; keeps `block_ref` OUT of the POST body — trust boundary**) |
| `cast-server/cast_server/static/requirements_comments.js` | already places against the rendered DOM — **verify only; no placement change** (2) |
| `agents/cast-requirements-how/cast-requirements-how.md` | the HOW prompt — **3b rewrites to the two-mode contract; 4 hardens the zero-ref + empty-shell rules** |
| `agents/cast-requirements-what/cast-requirements-what.md` | the WHAT prompt — **4 adds the zero-ref contract (empty `block_refs` for a ref-less source)** |
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` + `config.yaml` | reanchor subagent — **2 extends to contract v3 (additive render-space context); keeps `sonnet` tier** |
| `cast-server/cast_server/config.py` | `RENDER_STAGE_TIMEOUTS` (**:183**), `QUALITY_*` (**:233**) — **3a adds the two `RENDER_UPDATE_*` knobs** |
| `cast-server/tests/eval_family_sweep.py`, `tests/eval_sc003_survival.py`, `tests/eval_reanchor.py`, `tests/fixtures/family_corpus/` | validation harnesses — **5 extends the SC-003 survival list; re-runs the family sweep** |

## Data Schemas & Contracts (fixed by the plan — copy verbatim, do not re-derive at exec)

### Comment anchoring columns (additive — Sub-phase 2)

```sql
-- requirement_comments gains (both additive, old rows keep the defaults):
block_ref   TEXT NULL,                              -- canonical id of the enclosing labeled unit
                                                     --   container (server-resolved); NULL = cross-boundary
                                                     --   OR a ref-less render (zero anchor labels) — both honest
anchor_space TEXT NOT NULL DEFAULT 'source',        -- 'source' | 'render'
```

- **`block_ref = NULL` on a ref-less render is SUCCESS, not a miss** (plan-review Decision #1). A
  `pilot_poc`/`random_idea` page has zero anchor labels by design → every comment's `block_ref` is NULL
  by construction. Migration and the displacement detector must treat a ref-less-render NULL as a
  normal placed comment, **never** an unplaced miss to retry/badge.
- **`block_ref` is server-resolved from the served artifact, NEVER accepted from the client** (trust
  boundary — a spoofed ref would mis-route a future change-request). Keep it out of the POST body schema.

### Mode decision (pure, unit-testable — Sub-phase 3a)

```text
mode = UPDATE  iff  ALL of:
  - a prior render exists AND it was a CLEAN maker publish
      (served-by: maker, no human-review flag — never UPDATE *from* a flagged/fallback render)
  - the prior source is recoverable (prior job dir, else a requirement_versions content-hash match)
  - changed_fraction <= RENDER_UPDATE_MAX_CHANGED_FRACTION         (config default 0.4)
  - prior_render_bytes <= RENDER_UPDATE_MAX_PRIOR_BYTES            (config; plan-review Decision #6)
  - the goal's workflow_family is unchanged
otherwise: CREATE   (each failure → degrade-to-CREATE with a job `_note`; never an error)

changed_fraction = (added + removed + modified) / max(old_blocks, new_blocks)   # from block_diff.diff_blocks
```

### `cast-comment-reanchor` contract v3 (additive superset of v2 — Sub-phase 2)

- Inputs gain OPTIONAL render-space context: the comment's prior-render container text (by `block_ref`)
  and the candidate new-render container text. Verdict vocabulary (`relocated > resolved >
  orphaned`-when-unsure), safety machinery (orphan-over-guess, 422 verbatim backstop, no-op-on-garbage),
  and the `sonnet` tier carry **untouched**. Every new input optional → every existing call site stays
  byte-valid (same precedent as v2-over-v1).

### `check_update_fidelity` comparison granularity (Sub-phase 3b — plan-review Decision #3)

- **gate-enforced-LLM-copy mode:** compare **NORMALIZED container TEXT** via the shared
  `container_text_index` walker — the **same** text space displacement + survival already use — **NOT
  raw bytes.** A raw-byte gate on LLM output thrashes on insignificant serialization noise
  (whitespace / attribute-order) and would fail an edit that changed nothing.
- **Raw-byte identity is the construction GUARANTEE of *splice* mode** (the server keeps the prior
  bytes verbatim), not a bar to hold LLM output to. The 1a whitespace-only-vs-reworded distinction
  feeds the normalization layer here, exactly as 1a's design note demands.

## Pre-Existing Decisions (binding — decisions-so-far.md + the plan's Decisions appendix)

1. **Comment anchoring moves to the render snapshot** with a server-resolved `block_ref` bridge
   (owner-directed; design locked in the plan; 1b sizes the migration, it does not re-open the decision).
2. **Scope includes all three flagged-family fixes** — forced by "re-run the 3 flagged families → clean".
3. **UPDATE only from clean maker priors**; every UPDATE precondition failure degrades to CREATE, noted,
   never errored.
4. **One spec pass** (Sub-phase 5), never piecemeal edits while code and spec diverge mid-phase.
5. **Verbatim-carriage's survivors:** anchor labels verbatim-once + one-unit-one-container stay hard;
   only the leaf-text copy-exact obligation is removed.
6. **UPDATE SKIPS `emit_change_requests`** entirely (plan-review Decision #2): the gap-CR dedupe
   fingerprint rides `_what_doc_job_ref` keyed by the *current* `source_hash[:12]`; an UPDATE runs under
   a NEW hash, so re-emitting would write a DUPLICATE gap CR the dedupe pre-check can't match. UPDATE
   reuses the prior `gaps-state.json` and re-emits nothing; any diff that would change the gap set has
   already flipped the job to CREATE.

## Relevant Specs

- **`cast-requirements-render.collab.md` (currently v7 on disk)** — `linked_files` overlap heavily
  (maker pipeline, comments, gates). Sub-phase **5** runs the single `/cast-update-spec` pass
  (v7 → **v8**; see the version note below). Sub-phases 2/3a/3b/4 **flag** spec deltas but do not edit the
  spec — Sub-phase 5 records them. Read the spec on-demand only when touching spec-linked files.
- **`cast-requirements-roundtrip.collab.md` (v2)** — comment→change-request flow. **Consumed, not
  modified**; Sub-phase 5 does a one-line cross-reference check ONLY IF its wording references
  source-anchored quotes.

> ⚠️ **Spec version note (reconciliation — read before Sub-phase 5).** The plan body says the spec pass
> is "**v6 → v7**". That numbering is **stale**: it was drafted before Phase 5 (gap-fill) landed its
> own spec bump. The spec on disk is **already v7** (`> **Version:** 7`). This phase's `/cast-update-spec`
> pass is therefore **v7 → v8**. The *contract content* to land is exactly as the plan describes; only
> the version label is corrected. Sub-phase 5 + the manifest use **v8** throughout.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 1a (UPDATE byte-fidelity spike) | Spike (read-only) | None | 3a, 3b (verdict selects mechanism) | 1b |
| 1b (render-anchor dry-run) | Spike (read-only) | None | 2 (sizes migration) | 1a |
| 2 (anchor move) | Sub-phase | 1b | 3b | 3a |
| 3a (two-mode plumbing) | Sub-phase | 1a verdict | 3b | 2 |
| 3b (the flip) | Sub-phase | **2 AND 3a AND 1a verdict** | 4 | — |
| 4 (HOW hardening) | Sub-phase | 3b | 5 | — |
| 5 (proof + spec v8) | Sub-phase | 2, 3b, 4 | — (terminal) | — |

**No decision gates** (owner decision: the 1a verdict is a recorded dependency, not an orchestrator
stop). Sub-phase 5's `/cast-update-spec` is an inline human-approval gate handled within that sub-phase
(review the diff before approval); the browser/tray human-eyeball pass is a non-blocking carry-forward.

## Cross-Phase Hard Edges (do not violate)

- **Shared walker (HARD, no-copy):** import `container_text_index` from `maker_gate.py:259` in every
  place that needs render container text (sp2 displacement, sp3b fidelity). Never re-implement the walk;
  never add a second stripper.
- **`block_diff` is consumed, never edited** (FR-024). sp3a reads `diff_blocks`/`summarize` for the
  changed-set; it does not fork the engine.
- **`render_job_service.py` is edited by both sp2 (no — sp2 is comment_service/anchor) and sp3a/sp3b.**
  Within this phase, sp3a (mode decision + recovery + `_build_how_prompt` UPDATE section, **inert**) and
  sp3b (wire it live + publish-boundary dispatch) touch `render_job_service.py` **sequentially** (3b
  depends on 3a) — no parallel collision. sp2 runs parallel to sp3a but touches `comment_service.py` /
  `comment_anchor.py` / `api_requirements.py` / `schema.sql`, **not** `render_job_service.py`.
- **`agents/cast-requirements-how/cast-requirements-how.md` is edited by sp3b (the flip) then sp4
  (hardening) — SEQUENTIALLY.** sp4 depends on sp3b precisely so the prompt is not edited twice in
  flight. Never edit it in a sub-phase that runs parallel to another HOW-prompt edit.
