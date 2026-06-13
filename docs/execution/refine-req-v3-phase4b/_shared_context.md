# Shared Context: refine-req-v3-phase4b (Comments & Versions Survive the Maker)

> Read this file at session start before executing any sub-phase plan in this project.

## Source Documents

- **Plan (authoritative):** `docs/plan/2026-06-12-refine-requirements-v3-phase4b-comment-survival.md`
- **Reconciliation report:** `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- **Decisions-so-far (binding owner decisions):** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
- **Phase-3 execution context (the seams this phase consumes):** `docs/execution/refine-req-v3-phase3/_shared_context.md`

## Project Background

A maker regenerate must leave every open comment anchored with **zero new orphans** (SC-003).
The shaping insight (Phase 1, sharpened): the comment + version layer is **entirely source-side**
— comments anchor to a verbatim quote validated against `refined_requirements.collab.md`, versions
snapshot the source, `block_diff` diffs parsed *source* versions, displacement is a source-side
string-find. A maker regenerate (same source, new HTML) therefore **cannot** orphan a comment at
the DB layer. The genuine exposure is **silent `<mark>`-placement loss on a paraphrased maker DOM**
(the JS `highlight()` returns `false` and the comment quietly loses its visible mark).

Phase 4b is consequently three surgical additions, not a re-architecture:
1. **A comment-survival gate** (`check_comment_survival`, pure, co-located in `maker_gate.py`) over
   the *real* open comments at maker-publish time, riding the verbatim-carriage clause and reusing
   3b's shared `container_text_index` walker (no copy).
2. **The diff-and-comment-resolution agent** — `cast-comment-reanchor` **extended in place** to a
   backward-compatible **contract v2** that adds diff narration and block-level re-anchoring
   context plus a third `resolved` verdict. Existing verdicts-only call sites stay byte-valid.
3. **A same-door narration surface** — stored once per version cut, structurally validated against
   the deterministic change set, rendered only by attachment to deterministic items, so the UI
   *cannot* show an invented change.

Planning is done; this project **executes** the four sub-phases the plan defines.

## Operating Mode

**HOLD SCOPE.** `refined_requirements.collab.md` front matter pins `scope_mode: hold`. Owner
decisions in `decisions-so-far.md` are binding and not re-opened. The Phase-4a quality checker /
rework loop / `render_jobs` flag columns, and Phase-5 gap-fill asks, are **out of scope** — 4b
consumes their seams read-only and touches `render_job_service` only at the `gate_html` seam.

## ⚠️ The DECISION #10 OVERRIDE (applied throughout — read this first)

The original plan framed an in-block survival miss as a **structural violation that BLOCKS
publish** (retry → deterministic fallback) and made a survival-failing attempt **ineligible** for
4a's best-scoring-valid serve. The owner reconciliation **OVERRODE** this (decisions-so-far.md,
"Post-reconciliation owner decisions → Structural-violation fork OWNER OVERRIDE", and the explicit
"Phase 4b Decision #10" clause):

> **Survival-failing attempts are NO LONGER disqualified from serving.** In-block placement misses
> **SURFACE** as read-time `.comment-unplaced` tray badges rather than blocking. "Never silently
> drop" binds by **surfacing the loss, not hiding it** ("surface, don't suppress").

**What this changes vs. the source plan text (apply the override; the plan body predates it):**

- **No new blocking branch in `render_job_service`.** Survival violations for **in-block** misses
  merge into the **existing** `state.html_report.violations` channel that `gate_html` already
  produces. Phase 3's already-shipped `publish()` then serves **best-attempt + `structural_violation`
  flag** on structural-gate exhaustion (it never falls back to the deterministic page except on
  literal no-output). 4b-1 does **not** add a "survival blocks publish" path — it widens the report;
  the override-era `publish()` does the right thing automatically.
- **The deterministic fallback fires ONLY on literal no-output** (crash/timeout/no extractable
  render). A survival-failing best attempt is **served + flagged**, never swapped for the plain page.
- **The `.comment-unplaced` tray badge covers BOTH in-block and cross-boundary misses.** Read-time,
  derived, nothing stored — the JS `highlight()→false` path already treats them uniformly.
- **The 4a seam contract flips.** Survival-failing attempts ARE servable (flagged), so they are NOT
  excluded from serving. The 4b-4 hand-off note records the override-era contract: survival
  violations are part of the *surfaced* structural report 4a wraps, **not** a disqualifier.
- **Cross-boundary misses are still never violations** (they can fail on the deterministic substrate
  too) — recorded + surfaced via the badge, never merged into `html_report.violations`.

The in-block / cross-boundary classification inside `check_comment_survival` is **retained** — it
decides which misses count toward the surfaced structural report (in-block) vs. badge-only
(cross-boundary). What the override removes is only the **downstream blocking**, not the classifier.

Where any source-plan sentence (4b-1 §, Decisions #4/#10, Design Review Flags, Key Risks) says a
survival violation "blocks publish", "takes the structural-violation branch → deterministic
fallback", or "is not a structurally-valid attempt for 4a's serve", read it through this override.

## Codebase Conventions

- **Pure render package vs. service split.** `cast_server/requirements_render/` is pure (no I/O, DB,
  LLM) — `maker_gate.py` (incl. the new `check_comment_survival`) lives here. All I/O / DB /
  subprocess work lives in `cast_server/services/` — `render_job_service.py` (the `gate_html`
  widening) and `requirement_version_service.py` (narration store) live there.
- **Single-implementation discipline (HARD).** One container-text walker: 3b's public
  `container_text_index(html)` in `maker_gate.py` (already exposed — confirmed at
  `maker_gate.py:238`). 4b-1 **imports it; never copies the walk.** One markdown stripper:
  Phase 2's `strip_inline_markdown` in `goal_card.py`. Copying either is drift by construction.
- **Subagent bare-output carve-out.** `cast-comment-reanchor` stays `dispatch_mode: subagent`,
  bare-JSON output (no `.output.json` envelope), FR-027 carve-out. Contract v2 is a **superset** —
  every new input optional; legacy `{comments, old_content, new_content}` calls get legacy behavior.
- **Flat service functions, injectable `db_path`/`goals_dir`.** `requirement_version_service`,
  `comment_service` are module-level functions with `*, db_path: Path | None = None` test seams.
  Narration functions follow this exactly.
- **DB migration test pattern:** `cast-server/tests/test_schema_migration.py` covers `schema.sql`
  changes. Add the `version_diff_narrations` coverage there.
- **LLM text into HTML = autoescaped fragments only.** Narration is LLM-authored; it MUST flow
  through the escaped Jinja template, never `innerHTML` / `| safe`.
- **`build/` is a non-goal, non-CI runtime area.** Survival observability writes to the job's
  `build/render-jobs/{slug}/{hash12}/survival.json`, never `goals/{slug}/` and never `render_jobs`
  columns (those are 4a property).
- **Test prefixes:** default-CI `pytest cast-server/tests/test_*.py`; the agent eval gate is
  `tests/eval_reanchor.py` (`eval_` prefix — NOT collected by default CI); the SC-003 sweep runs
  via the `eval_` real-pipeline harness.

## Key File Paths

| File | Role |
|------|------|
| `cast-server/cast_server/requirements_render/maker_gate.py` | `container_text_index` (line 238, shared walker — **import**), `check_what_doc`, `check_html`, `GateReport`. **4b-1 adds pure `check_comment_survival`.** |
| `cast-server/cast_server/requirements_render/goal_card.py` | `strip_inline_markdown` (anchorable-text stripper — import) |
| `cast-server/cast_server/requirements_render/parser.py` | `parse_requirements`, `Block.ref` (`US1`/`FR-007`/`SC-001` in-memory ref space) |
| `cast-server/cast_server/requirements_render/block_diff.py` | `diff_blocks`, `summarize` → `{counts, items:[{change, kind, heading_or_ref, excerpt}]}`, `_key`. **NOT modified.** |
| `cast-server/cast_server/requirements_render/diff_render.py` | tracked-changes view (FR-025 transient ids). **NOT modified** (4b-3 passes narration into its panel via the route only). |
| `cast-server/cast_server/services/render_job_service.py` | `gate_html` (line 487), `publish` (line 497, OVERRIDE live), `_execute_pipeline`. **4b-1 widens `gate_html` only.** |
| `cast-server/cast_server/services/comment_service.py` | `list_comments(goal_slug, *, state=...)` (line 125), `resolve_comment`, `relocate_comment`, `reopen` — the v2 state machine |
| `cast-server/cast_server/services/requirement_version_service.py` | `create_next` (`displaced_comment_ids`), `get_version`, `list_versions`. **4b-3 adds `save_narration` / `get_narration`.** |
| `cast-server/cast_server/routes/api_requirements.py` | comment/version API; `GET /changes` (line 290, `summarize` JSON / `changes_panel` fragment). **4b-3 adds the narration POST + the `narration` sibling key.** |
| `cast-server/cast_server/db/schema.sql` | **4b-3 adds `version_diff_narrations` CREATE TABLE.** |
| `cast-server/cast_server/templates/fragments/requirements_comments/changes_panel.html` | "What changed" panel. **4b-3 attaches narration by `(change, heading_or_ref)` lookup.** |
| `cast-server/cast_server/static/requirements_comments.js` | `placeMarks` (line 51), `highlight` (line 25, returns `false` on miss). **4b-1 toggles `.comment-unplaced` on tray items whose `highlight()` returned false.** |
| `cast-server/cast_server/templates/.../_theme.css.j2` | comment/diff CSS. **4b-1 adds `.comment-unplaced`; 4b-3 adds `.diff-narration` — disjoint additive blocks (see manifest seam note).** |
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` + `config.yaml` | the diff/re-anchor subagent. **4b-2 extends to contract v2.** |
| `agents/cast-refine-requirements/` | the Phase-4-loop dispatch site (step 3). **4b-2 passes `change_set` + block context; applies `resolved`; POSTs narration.** |
| `cast-server/tests/eval_reanchor.py` | the agent eval gate (`eval_` prefix). **4b-2 extends.** |

## Data Schemas & Contracts (fixed by the plan — copy verbatim, do not re-derive at exec)

### `SurvivalReport` (frozen — 4b-1, pure)

```python
SurvivalReport = {
    "passed": bool,                 # False IFF >=1 IN-BLOCK miss (cross-boundary never flips this)
    "violations": list[str],        # prompt-ready, IN-BLOCK misses only (merged into html_report)
    "unplaced": list[int],          # comment ids that did NOT place (in-block AND cross-boundary)
    "placed": list[int],            # comment ids that placed
}
```

- `check_comment_survival(html, parsed, comments) -> SurvivalReport`, where `comments` is a plain
  sequence of `{id, quoted_text}` (gate stays I/O-free; the service fetches).
- **Single-walk discipline (P1):** walk the candidate HTML **once** via `container_text_index`;
  precompute each block's `strip_inline_markdown(block.body)` **once per pass**. Both carriage and
  survival read those two maps — cost is O(blocks + comments), never O(comments × blocks) strips or
  a second walk.
- **Classification per open comment:**
  - **in-block** — `quoted_text` is a substring of some block's anchorable text. By the
    verbatim-carriage clause it MUST place; assert with 1b semantics (concatenated descendant text
    per container via `container_text_index` + `find()`, hit valid only in that block's container).
    A miss ⇒ **violation** (real carriage failure, witnessed by data) → counts toward `passed=False`
    and `violations`; also added to `unplaced`.
  - **cross-boundary** — quote not within any single block's anchorable text (spans blocks /
    markdown-strip seam / quotes render decoration). Best-effort whole-document find; **recorded
    either way, NEVER a violation** (it can fail on the deterministic substrate too). Added to
    `unplaced` on a miss, but never to `violations` and never flips `passed`.
- Violation strings are prompt-ready, e.g.
  `"comment 12's anchor 'the maker never writes…' missing from FR-008's container"`.

### `cast-comment-reanchor` contract v2 (4b-2 — backward-compatible superset)

```jsonc
// Inputs (all additions OPTIONAL — legacy {comments, old_content, new_content} ⇒ verdicts-only):
{
  "comments": [{ "id", "quoted_text", "body",
                 "block_ref": "FR-008",                  // OPTIONAL: Block.ref whose OLD body held the quote
                                                          //   (parent resolves via parse_requirements + strip_inline_markdown
                                                          //    substring test; OMIT for cross-boundary quotes — never guess)
                 "block_disposition": "modified|removed|unchanged" }],  // OPTIONAL
  "old_content": "...", "new_content": "...",
  "change_set": { "counts": {...}, "items": [{ "change", "kind", "heading_or_ref", "excerpt" }] }  // OPTIONAL: summarize() dict
}
// Output:
{
  "narration": null | {                                  // emitted ONLY when change_set provided
    "overview": "1-3 sentences",
    "item_notes": [{ "change", "heading_or_ref", "note" }]   // EVERY (change, heading_or_ref) MUST equal a change_set.items entry
  },
  "verdicts": [{ "id", "verdict": "relocated|resolved|orphaned",
                 "new_quoted_text"?, "confidence", "reasoning" }]
}
```

- **Third verdict `resolved`** (the US3-S2 "re-anchor **or** resolve" half): only on a demonstrable
  fix. Bias order is **`relocated` > `resolved` > `orphaned`-when-unsure**. A wrong `resolved` is
  recoverable (reopen + event trail + still visible collapsed in tray); a wrong relocate is not.
- **Anchor-pickability:** `new_quoted_text` must remain a verbatim substring of `new_content`
  (unchanged backstop) and SHOULD avoid inline-markdown markers (`**`, `` ` ``) so it places on the
  stripped-carriage maker DOM (closes the cross-boundary class at its origin).
- **Trust boundary (hard rule):** narration describes ONLY entries of `change_set.items` — never
  merged, added, or reworded keys. If the agent thinks the set is wrong it says so in `overview`
  wording; it never adds an item. The deterministic set is the source of truth; the agent decorates.

### `version_diff_narrations` table (4b-3)

```
id, goal_slug, base_version, head_version,
overview TEXT, item_notes TEXT (JSON),
created_by,                       -- the DISPATCHING PARENT's actor id (e.g. cast-refine-requirements)
created_at,
UNIQUE(goal_slug, base_version, head_version)   -- re-post UPSERTS (a retried loop cycle replaces, never duplicates)
```

- Size caps mirror FR-017: `overview` ≤ 2 KB, each note ≤ 2 KB, ≤ 1 note per item.
- `POST /api/goals/{goal_slug}/requirements/versions/{head}/narration` body `{base, overview,
  item_notes, created_by}` — slug validated via `goal_service.get_goal` first (FR-014), JSON-only.
  `created_by` (the dispatching parent's actor id) rides the body, matching the resolve/relocate
  `actor` convention (same-door; nothing about the caller is privileged).
- `save_narration` **recomputes `summarize(diff_blocks(old, new))` server-side** and validates
  **every** `item_note` keys to a deterministic item; ANY mismatch → **422 all-or-nothing** listing
  the offending keys (no silent note-dropping). 404 on unknown version/slug.
- `GET …/changes` gains a sibling `narration: {...} | null` key; `counts`/`items` stay
  **byte-for-byte** `summarize()` (FR-024 guarantee re-scoped to those keys).

## Pre-Existing Decisions (binding — from decisions-so-far.md)

- **Anchor backbone is logical only**; DOM keeps v2 quote/verbatim-substring anchoring; zero `id=`,
  zero `data-block-anchor` (FR-025 transient-id exception stays diff-view-only).
- **Orphan-over-guess stands.** The LLM may narrate + re-anchor/resolve; a diff must NEVER invent a
  change absent from the source. Canonical source stays `refined_requirements.collab.md`; the maker
  never writes it.
- **Extend `cast-comment-reanchor` in place (contract v2), not replace** — the verdict safety
  machinery (orphan-over-guess, 422 verbatim backstop, no-op-on-garbage) carries untouched.
- **Narration posted same-door by the parent that cut the version**; the server never dispatches an
  LLM on the version path. A human-initiated cut simply has no narration; the deterministic panel is
  the floor.
- **`block_diff` and `diff_render` are NOT modified** — the logical id backbone the diff agent reads
  is the same `Block.ref` space `_key()` already keys on (FR-024 "extend, never fork").
- **Survival gate fetches open comments at `gate_html` stage entry, RE-READ PER ATTEMPT** (Decision
  #9) — a background job under 4a's loop re-enters `gate_html` many times; one indexed SELECT per
  entry keeps the view/comment paths instant.
- **DECISION #10 OVERRIDE** (see the dedicated section above) — survival-failing attempts servable
  + flagged; in-block misses surface as badges, never block.
- **`resolved` application respects the v2 comment state machine** (Decision #11) — if a human
  changed the comment state between dispatch and apply, the resolve POST is a clean no-op/rejection.
- **Model tier:** `cast-comment-reanchor` v2 **keeps its existing tier** (`model: sonnet` in
  `config.yaml`, annotated with the `[USER-DEFERRED]` tuning-knob comment). The four NEW pipeline
  agents are `opus`; the reanchor agent is NOT one of them.

## Relevant Specs

- **`cast-requirements-render.collab.md` (Draft v2)** — `linked_files` overlap. Sub-phase **4b-4**
  runs the single `/cast-update-spec` pass (survival gate + `.comment-unplaced` badge; FR-024
  re-scope + narration surface; FR-027/US13 contract-v2 superset; FR-023 narration route; new
  `linked_files`). Sub-phases 4b-1/4b-2/4b-3 **flag** spec deltas but do not edit the spec — 4b-4
  records them. Read the spec on-demand only when touching spec-linked files.
- **`cast-requirements-roundtrip.collab.md` (Draft v1)** — writeback reanchor dispatch +
  `target_quote_override`. **Consumed, not modified** (the verdicts-only call site stays valid
  under contract v2 by construction).

## Cross-Phase Hard Edges (do not violate)

- **3b walker → 4b-1 (HARD, no-copy):** import `container_text_index` from `maker_gate.py`
  (already public, `maker_gate.py:238`). Never re-implement the walk; never add a second stripper.
- **4a-2 ∥ 4b-1 on `render_job_service.py` (C3 merge note):** disjoint seams — 4b-1 widens
  `gate_html`'s report; 4a-2 inserts `run_checker → decide_quality` *after* `gate_html`. Whichever
  lands second does the **mechanical merge**. 4a wraps "whatever `gate_html` reports", so the
  widened report is absorbed by construction; under the OVERRIDE a survival-failing attempt is a
  *flagged, servable* structural state, not a disqualifier.
- **`_theme.css.j2` shared between 4b-1 and 4b-3:** disjoint, additive, non-overlapping CSS blocks
  (`.comment-unplaced` vs `.diff-narration`); whichever lands second appends after the first.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 4b-1 (survival gate + tray badge) | Sub-phase | Phase 3 (3b `maker_gate`, 3c `render_job_service`) | 4b-4 | 4b-2, 4b-3 (shared `_theme.css.j2` via additive-append) |
| 4b-2 (reanchor contract v2) | Sub-phase | Phase 3 WHAT-doc id-mapping | 4b-3, 4b-4 | 4b-1 |
| 4b-3 (narration store / API / render) | Sub-phase | 4b-2 (the narration schema = the agent's output shape) | 4b-4 | 4b-1 (shared `_theme.css.j2` via additive-append) |
| 4b-4 (spec + SC-003 e2e gate) | Sub-phase | 4b-1, 4b-2, 4b-3 | — (terminal) | — |

No decision gates: the source plan defines none ("Open Questions: None blocking"). 4b-4's
`/cast-update-spec` is an inline skill-approval gate handled within 4b-4 (review the diff before
approval); the human-eyeball browser pass over the tray badge + narration panel is a non-blocking
carry-forward (autonomous runs cannot drive a browser; static verdicts never block).
