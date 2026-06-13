# Spec v7 → v8 change brief — `cast-requirements-render.collab.md`

> **STATUS: AWAITING HUMAN APPROVAL (sub-phase 5, Step 5.3).** This is the reviewable v7→v8 diff for
> the `/cast-update-spec` human-approval gate. The **live spec is untouched** (`> **Version:** 7` on
> disk). Nothing here is landed. Review the change set below; on sign-off, run `/cast-update-spec`
> (or approve the runner to apply this brief) to land v8 + the registry bump, then re-run
> `bin/cast-spec-checker` on the result.
>
> **Why a brief, not a landed edit:** the delegation marks the spec write a HUMAN-APPROVAL GATE and
> forbids self-approval; this run is autonomous (no approver). The runner prepares the complete,
> precise change set and stops at the gate.

This phase (`refine-req-v3-how-update-mode`) is the principal post-sign-off follow-up the v7
changelog named: the **HOW two-mode (CREATE/UPDATE) contract + readability-over-verbatim** rework, plus
the **comment anchoring move from canonical source → published-render snapshot**. The contract content
is exactly as the phase plan describes; only the version label is corrected (the plan body says
"v6→v7"; the spec on disk is already v7, so this pass is **v7 → v8**).

---

## A. Version header (lines 75–87)

**Change `> **Version:** 7` → `> **Version:** 8`** and prepend a new changelog paragraph above the v6
block, dated today:

```
> **Updated:** 2026-06-13 — v8 (Phase-5 follow-up: HOW two-mode + render-snapshot anchoring): the
> HOW maker gains a CREATE/UPDATE two-mode contract (CREATE re-renders fresh + readability-first;
> UPDATE re-renders only changed blocks and keeps unchanged unit containers byte-identical) bounded
> by a massive-change threshold; comment anchoring MOVES from the canonical `.collab.md` to the
> published-render snapshot with a server-resolved `block_ref` bridge + `anchor_space` column; the
> US16 blanket verbatim-carriage clause is SUPERSEDED (anchor labels + one-unit-one-container
> survive; leaf-text copy-exact in CREATE is dropped for readability); US8/US12 displacement +
> US19 survival reorient to render space; the `cast-comment-reanchor` contract steps to v3 (additive
> render-space context) and runs once at the publish boundary for an UPDATE's expected misses; gap
> CRs are idempotent under UPDATE (reuse prior gaps-state, skip emit); + the empty-shell gate check
> and the splice-assembles-the-published-artifact architecture note. (Spike 1a verdict: FAIL →
> deterministic-splice mechanism.)
```

---

## B. User-story edits (mark superseded, never silently rewrite)

The crux move reverses four US clauses. Each keeps its original text and gains an explicit
**SUPERSEDED (v8)** annotation + the replacement scenario — never a silent rewrite (plan-review +
shared-context discipline).

### B1. US16 — Logical id backbone and verbatim carriage (lines 525–551) — **PARTIALLY SUPERSEDED**

Add, immediately under the US16 heading:

> **⚠️ SUPERSEDED in part (v8).** The blanket **verbatim-carriage** obligation on leaf requirement
> text is **removed**. What SURVIVES unchanged and stays HARD: (1) each canonical id printed verbatim
> exactly once as an anchor label (Scenario 1), and (2) one contiguous semantic container per unit —
> the one-unit-one-container DOM rule (Scenario 3). What is REMOVED: the Scenario-2 copy-exact
> obligation that each unit's inline-markdown-stripped source body appear **verbatim and contiguous**
> in CREATE mode — CREATE now optimizes for the most human-readable page and MAY paraphrase / distill
> leaf text. Verbatim carriage was only ever a proxy that kept source-anchored comments placeable;
> v8 moves comment anchoring to the render snapshot (US8/US12/US19 below), so the proxy is retired.
> In **UPDATE** mode unchanged unit containers are kept byte-identical by the splice (a stronger
> guarantee than carriage, by construction). See FR-055/FR-056.

Edit Scenario 2 to scope it to UPDATE byte-identity (the splice's unchanged containers) rather than a
blanket CREATE carriage requirement; leave Scenarios 1 and 3 intact.

### B2. US8 — Same-door comment authoring (lines 308–331) — **RE-TARGET to render space**

Add under the heading:

> **Updated (v8).** A comment's anchor is now minted against / validated against the **published
> render snapshot's container text** (`anchor_space='render'`), not the canonical `.collab.md`. A
> server-resolved `block_ref` (the canonical id of the enclosing labeled unit container) bridges the
> render-space quote back to source space and is **never accepted from the client** (trust boundary).
> The `create_comment` signature gains keyword-only `served_render_html` (a test seam; production
> reads the served `.html` off disk) and stores `block_ref` + `anchor_space`. A `block_ref` of
> `None` on a ref-less render (zero anchor labels — a `pilot_poc`/`random_idea` page by design) is a
> **placed-comment SUCCESS**, never an unplaced miss. See FR-057.

### B3. US12 — Derived displacement surfaced in the tray (lines 417–436) — **RE-TARGET to render space**

Add under the heading, and edit Scenario 1 accordingly:

> **Updated (v8).** Displacement for a `render`-space comment is computed against the **served
> render's container text** (the published artifact the quote was minted against), resolved via the
> shared `container_text_index` walker — not the canonical source. `list_comments` chooses the
> comparison space per the comment's `anchor_space` (`render` → served render text; legacy `source` →
> the `.collab.md`), and a missing render degrades to the source check, never a crash. The detector
> stays read-time / never-stored. See FR-057.

### B4. US19 — Open comments survive the maker render (lines 613–644) — **REORIENT to render space**

Add under the heading:

> **Reoriented (v8).** Survival is now a **render-space** property. *In-block* = the quote placed
> inside a labeled unit container on the render it was minted against; *survival* = it places in the
> same `block_ref`'s container on the next render. In **UPDATE** mode the splice keeps unchanged unit
> containers byte-identical, so survival of a comment on an unchanged block is **structural** (no
> reanchor needed). A comment on a **modified/removed** block is an **expected miss** that routes to
> the ONE publish-boundary `cast-comment-reanchor` v3 dispatch (relocate / resolve / orphan) — never
> blocking the publish, never silently dropped; an expected miss never flips `passed`. The
> DECISION #10 OVERRIDE (an in-block CREATE miss → flagged best-attempt + `.comment-unplaced` badge,
> deterministic page only on literal no-output) carries unchanged. See FR-058/FR-059.

### B5. US13 Scenario 4 / FR-044 — reanchor **contract v3** (line 758, lines 438–471)

Append a **Scenario 5 (contract v3, v8)** to US13 and extend FR-044:

> **Scenario 5 (contract v3, v8):** WHEN `cast-comment-reanchor` is called with the **optional**
> render-space context — the comment's prior-render container text (by `block_ref`) and the candidate
> new-render container text — THE SYSTEM SHALL accept a backward-compatible **superset of v2**: every
> new input is optional, so every existing call site stays byte-valid (same precedent as v2-over-v1).
> The verdict vocabulary (`relocated > resolved > orphaned`-when-unsure), the safety machinery
> (orphan-over-guess, the 422 verbatim backstop, no-op-on-garbage), and the `model: sonnet` bare-JSON
> carve-out are **untouched**. In UPDATE mode the dispatch runs **once at the publish boundary** over
> the job's expected-miss comments.

---

## C. New Functional Requirements (append after FR-054)

```
| FR-055 | The render job decides CREATE vs UPDATE via the pure `render_job_service.decide_mode(...)`.
  UPDATE iff ALL hold: a prior render exists AND was a CLEAN maker publish (`served-by: maker`, no
  human-review); the prior source is recoverable; the goal's `workflow_family` is unchanged;
  `changed_fraction <= RENDER_UPDATE_MAX_CHANGED_FRACTION` (config default 0.4); and
  `prior_render_bytes <= RENDER_UPDATE_MAX_PRIOR_BYTES` (config default 600 000). EVERY precondition
  failure degrades to CREATE with a job `_note` — never an error (CREATE is always safe).
  `changed_fraction = (added+removed+modified)/max(old_blocks,new_blocks)` from the consumed
  `block_diff.diff_blocks` (FR-024 extend-never-fork). The decided `mode` is stamped on the
  `render_jobs` row. | Every UPDATE precondition failure degrades to CREATE, noted, never errored —
  shared-context Owner Principle |
| FR-056 | UPDATE is the **deterministic splice** (Spike 1a verdict: FAIL → splice, not gate-enforced
  LLM copy): the server keeps each unchanged unit container's bytes verbatim from the prior render and
  splices in HOW-rendered changed-block fragments (the `RR-FRAGMENT` sub-contract; HOW emits only
  changed blocks, never a full page). Byte-identity of unchanged containers is a **construction
  guarantee**. `check_update_fidelity` compares **NORMALIZED container TEXT** via the shared
  `container_text_index` walker (NOT raw bytes — raw-byte LLM gating thrashes on serialization noise);
  a changed ref HOW emitted no fragment for is a structural violation taking the standard retry.
  UPDATE REUSES the prior gated WHAT doc (no `run_what`); a WHAT-reuse miss degrades the whole job to
  CREATE. The published artifact in UPDATE mode is **server-assembled** (splice), not a single LLM
  emission. | The splice-assembles-the-published-artifact architecture note; single-walker discipline |
| FR-057 | Comment anchoring lives in the **published-render snapshot** space. `requirement_comments`
  gains two additive columns: `block_ref TEXT NULL` (server-resolved canonical id of the enclosing
  labeled unit container; NULL = cross-boundary OR a ref-less render — both honest) and
  `anchor_space TEXT NOT NULL DEFAULT 'source'` (`'source' | 'render'`). `block_ref` is resolved
  SERVER-SIDE from the served artifact by `comment_anchor.resolve_render_anchor` (the productionized
  1b dry-run, reusing `container_text_index`) and is **NEVER accepted from the client** (a spoofed ref
  would mis-route a future change-request) — it stays out of the POST body schema. A ref-less-render
  NULL `block_ref` is a placed-comment SUCCESS, never an unplaced miss to retry/badge. Old rows keep
  the back-compatible `'source'` default (migration: `db/schema.sql` + `tests/test_schema_migration.py`).
  | The crux move — comments anchor to the render, bridged back to source by a server-resolved ref |
| FR-058 | UPDATE SKIPS `emit_change_requests` entirely and REUSES the prior `gaps-state.json`
  (plan-review Decision #2, LOAD-BEARING): the gap-CR dedupe fingerprint rides
  `origin_artifact_path` keyed by the CURRENT `source_hash[:12]`; an UPDATE runs under a NEW hash, so
  re-emitting would write a DUPLICATE gap CR the dedupe pre-check cannot match. Any diff that would
  change the gap set has already flipped the job to CREATE (WHAT reuse fell back). The prior render's
  `.rr-gap` markers ride along in the unchanged containers the splice preserves. | Gap-CR idempotency
  under UPDATE — guards the source-hash-keyed dedupe duplication risk (SC-024) |
| FR-059 | For an UPDATE's **expected-miss** comments (those on modified/removed blocks), the pipeline
  runs ONE `cast-comment-reanchor` v3 dispatch at the **publish boundary** (`_post_publish_reanchor`,
  after `_finalize` so it never affects the terminal row): a `relocated` verdict re-points the comment
  to a verbatim span of the new render, `resolved` resolves it, anything else (incl. crash / garbage /
  non-verbatim quote) leaves the comment **open + badged** — never silently dropped, never
  auto-resolved. An expected miss never flips survival `passed`. | US19-reoriented; surface, don't
  suppress |
| FR-060 | `maker_gate.check_html` gains an **empty-shell** check: a render whose body carries section
  scaffolding but no actual requirement content (an empty shell) is a structural violation, so a
  degenerate maker emission cannot publish as a clean page. The `cast-requirements-what` zero-ref
  contract (empty `block_refs` for a genuinely ref-less source) and the HOW zero-ref + empty-shell
  hardening pair with it. | Hardens the `pilot_poc`/`random_idea` ref-less path against degenerate output |
| FR-061 | Two config knobs follow the `RENDER_*` env-overridable convention:
  `RENDER_UPDATE_MAX_CHANGED_FRACTION` (default 0.4, `CAST_RENDER_UPDATE_MAX_CHANGED_FRACTION`) and
  `RENDER_UPDATE_MAX_PRIOR_BYTES` (default 600 000, `CAST_RENDER_UPDATE_MAX_PRIOR_BYTES`). The legacy
  `RENDER_UPDATE_ENABLED` flag is **retired as a behaviour gate** (sp3b wired UPDATE live: an UPDATE
  fires whenever `decide_mode` lands `mode='update'`); it survives only as a harmless legacy constant.
  | `RENDER_*`/`QUALITY_*` knob convention; the flag-gate is gone |
```

---

## D. New Success Criteria (append after SC-021)

```
| SC-022 | The two-mode decision is correct + degrade-safe: `decide_mode` returns UPDATE only when
  every precondition holds and degrades to CREATE (with a note) on each individual failure; an UPDATE
  publishes `served_by=maker` keeping unchanged unit containers byte-identical and swapping only
  changed blocks; a ref-less / massive / family-changed / flagged-prior edit re-renders fresh in
  CREATE | `tests/test_render_mode_decision.py` + `tests/test_render_job_service.py` (live UPDATE
  splice + degrade tests) + `tests/test_maker_gate_update_fidelity.py` |
| SC-023 | Comments anchor to the render snapshot with a server-resolved bridge: `create_comment`
  stores `anchor_space='render'` + a server-resolved `block_ref` (never client-supplied); a ref-less
  render yields `block_ref=NULL` treated as SUCCESS; displacement + survival are computed in render
  space; a comment on an unchanged UPDATE block survives structurally, one on a modified block routes
  to the publish-boundary reanchor (relocate/resolve/orphan), never dropped | `tests/test_comment_service.py`
  + `tests/test_comment_anchor_render.py` + `tests/eval_sc003_survival.py` (regressions a–f) |
| SC-024 | Gap CRs are idempotent under UPDATE: an UPDATE-mode re-render of a doc carrying an open gap
  emits ZERO new gap change-requests (reuse prior `gaps-state.json`, skip `emit_change_requests`) —
  the source-hash-keyed dedupe duplication risk is pinned by a regression so a future refactor cannot
  silently reintroduce it | `tests/eval_sc003_survival.py` (regression f) + `tests/test_gap_reconciliation.py` |
```

(Re-run the 3 flagged families clean + the 9-family no-regression aggregate are recorded under SC-020,
which v8 confirms holds with `human_review=0` for all nine — see the sweep evidence; no new SC needed,
SC-020's record is updated to the v8 all-clean result.)

---

## E. Open Questions — append a v8 entry

> - **v8 (Phase-5 follow-up: HOW two-mode + render-snapshot anchoring):** nothing blocking. The HOW
>   maker's CREATE/UPDATE two-mode contract (FR-055/FR-056, Spike-1a verdict FAIL → deterministic
>   splice), the comment anchoring move to the render snapshot (FR-057, US8/US12/US19 reoriented), the
>   US16 verbatim-carriage supersession (anchor labels + one-unit-one-container survive; CREATE
>   leaf-text copy-exact dropped for readability), the reanchor contract v3 (US13 S5 / FR-044), the
>   gap-CR idempotency-under-UPDATE guarantee (FR-058), the empty-shell gate (FR-060), and the two
>   `RENDER_UPDATE_*` knobs (FR-061) are all resolved and recorded above. **One KNOWN LIMITATION (not
>   an open question):** dropping CREATE leaf-text verbatim carriage for readability admits
>   **paraphrase meaning-drift** — a dedicated paraphrase-meaning-fidelity checker is explicitly OUT
>   of scope (HOLD); the `cast-requirements-render-checker` comprehension pass is the only guard, and a
>   future review may add a fidelity dimension. The 1a verdict (UPDATE byte-fidelity spike) is FAIL →
>   the **deterministic splice** mechanism, so the published UPDATE artifact is **server-assembled**,
>   not a single LLM emission (recorded as the architecture note above).

---

## F. Registry bump — `docs/specs/_registry.md`

Bump the `cast-requirements-render.collab.md` row's version column **7 → 8** and append a `**v8**`
clause to its description summarizing the HOW two-mode contract + render-snapshot anchoring + the
US16 supersession (mirroring the prior `**v7**`/`**v6**` clause style), and add the v8 linked files:
`requirements_render/block_splice.py`, `requirements_render/comment_anchor.py` (render resolver),
`tests/test_render_mode_decision.py`, `tests/test_comment_anchor_render.py`,
`tests/test_maker_gate_update_fidelity.py`, `tests/test_maker_gate_empty_shell.py`,
`agents/cast-comment-reanchor/` (v3).

---

## G. Roundtrip spec cross-reference (conditional — Step 5.4)

Check `cast-requirements-roundtrip.collab.md` (v2): IF its comment→change-request bridge wording
references **source-anchored** quotes, apply a one-line cross-reference fix (the anchor space is now
the render snapshot). The roundtrip contract itself (propose/notify/gate) is **untouched**. See the
runner's finding in the sub-phase-5 output.

---

## Reviewer checklist (Step 5.3 acceptance)

- [ ] Every reversed clause (US8 / US12 / US16 / US19) is marked **superseded / reoriented**, not
      silently rewritten.
- [ ] The v2→v3 reanchor compatibility statement is explicit (every new input optional → existing
      call sites byte-valid).
- [ ] `bin/cast-spec-checker` passes on the landed v8.
- [ ] `grep -n "Version" …render.collab.md` → **v8**; `_registry.md` render row → **v8**.
- [ ] The HOW prompt's "CONTRACT SOURCE OF TRUTH" pointer lands on the v8 section.
