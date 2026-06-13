# Phase 3 → Phase 4a / 4b / 5 Hand-off

> Written by sub-phase **3e** (the terminal Phase-3 sub-phase). Phase 3 landed the **WHAT→HOW maker
> pipeline** as the render happy path (the deterministic renderer is now the fallback). This note
> records the **seams** Phase 4a/4b/5 plug into so the next phases extend the pipeline rather than
> re-discover it. Spec of record: `docs/specs/cast-requirements-render.collab.md` **v4**
> (US14–US17, FR-029–FR-036, SC-010–SC-013).

## 1. The 4a checker stage slots between `gate_html` and `publish`

The pipeline driver `render_job_service._execute_pipeline` runs the **named stages**:

```
run_what → gate_what → run_how → gate_html → publish
```

Phase 4a inserts its LLM-judged quality gate as **`run_checker → decide_quality` immediately before
`publish`** — a stage *added* to this list, not a rewrite. The structural `gate_html`
(`maker_gate.check_html`) stays where it is and keeps owning the structural contract (id mapping,
verbatim carriage, DOM contract); 4a's checker owns the *comprehension* judgement that replaces the
structural happy-path gate as the quality bar. `publish` already branches on
`(what_ok, html_ok, html is None)` — 4a adds a quality verdict to that decision without touching the
existing three branches.

- **Insertion point:** `_execute_pipeline()` in `cast_server/services/render_job_service.py`.
- **Determinism scope (recorded in spec SC-002, v4):** byte-stable goldens cover the deterministic
  **fallback** substrate only; the happy-path maker render is checked by `maker_gate` + the eval
  harness, and the LLM-judged layer is **explicitly 4a scope, unspecified in v4**.

## 2. Where the human-review flag lands (the `render_jobs` row)

Phase 3 already records degradation **without** 4a's columns, using only machinery it owns:

| Surface | Phase-3 mechanism |
|---|---|
| Job status | a `flagged` value in `render_jobs.status` (set by `publish` Branch 2) |
| Reason | the joined gate violations in the existing `render_jobs.error` column |
| Served-artifact stamp | `served-by: structural_violation` beside `source-hash` in the AUTO-GENERATED header |
| Reader-visible badge | `pages.py` injects a "needs review" badge on the `/render` response from that stamp |

**4a-2 layers its four columns on top** — `human_review`, `review_reason`, `published_attempt`,
`published_score` — via a migration that **only adds** those columns (Phase 3 did **not** create
them; see `db/schema.sql` `render_jobs` CREATE TABLE + the `tests/test_schema_migration.py` pattern).
Readiness is **never** derived from this table — the artifact's embedded `source-hash` is the single
source of truth; the table is the observability / failure-reason / human-review surface. A minimal
flagged-renders list (slug, reason, score, link) is folded into **Phase 5d**, and Phase 3's `flagged`
status + `served-by` stamp are exactly what make those renders discoverable.

## 3. Where the WHAT-doc id mapping lives (for the 4b diff agent)

The canonical `US-NN`/`FR-NNN`/`SC-NNN` ids are assigned upstream by the deterministic parser
(`parser.py`, `Block.ref`) and the WHAT doc carries the **logical, non-DOM backbone** as
`sections[].block_refs` (contract `cast-requirements-what/v1`): every parsed ref maps into exactly one
section, `unmapped_refs` must be empty (the gate fails loudly otherwise). The maker render then prints
each id verbatim **exactly once** as a small visible anchor label — never as `id=`/`data-block-anchor`
(US7/FR-012/FR-013 DOM contract preserved unchanged).

**The 4b diff agent reads the WHAT-doc `sections[].block_refs` mapping** as the structure that ties a
rendered unit back to its canonical id, and the printed anchor labels as the in-DOM trace. It does
**not** introduce element ids.

## 4. The shared `container_text_index` walker (4b-1 imports it — no copy)

`maker_gate.py` exposes the byte-faithful container-text walker as the **public**
`container_text_index(html) -> ContainerTextIndex` helper. It is the single container-text
implementation in the codebase (single-implementation discipline). 3b's `check_html` uses it to
enforce the **verbatim-carriage clause** (FR-034): each unit's anchorable text — its source body with
inline markdown stripped via the single `strip_inline_markdown` (`goal_card.py`) — must appear
verbatim and contiguous in one semantic container.

**4b-1 imports `container_text_index` directly — it must NOT re-implement a second walker.** 4b widens
the `gate_html` report (carriage + survival) on top of the same walker. The rationale recorded with the
clause: the real orphan-exposure risk is silent `<mark>`-placement loss on a *paraphrased* DOM, not DB
orphaning — verbatim carriage is what keeps the v2 quote-anchoring sound under a bespoke maker render.

## 5. The reserved `gaps[]` + `GAPS-DETECTED` trailer seam (Phase 5 activates)

Two paired seams are **defined now, with zero Phase-3 behaviour**:

- **WHAT front matter `gaps: []`** — a RESERVED Phase-5 field (FR-015 lineage). Always empty in
  Phase 3; the gate attaches no behaviour to it.
- **Optional `GAPS-DETECTED` HOW trailer** — the HOW contract permits an optional `GAPS-DETECTED`
  block to appear *after* `<!-- END RENDER -->`, i.e. **outside** the strict extraction window.
  `extract_render` stops at the first `END RENDER`, so the trailer is **byte-ignored** in Phase 3.

**Phase 5 activates both** (gap detection → upstream asks) and registers any new gap stages in the
`RENDER_STAGE_TIMEOUTS` list. Until then, do **not** write parsing/handling code for either — the
seams exist so Phase 5 is additive.

## Quick reference — the files Phase 4a/4b touch

| File | Why 4a/4b returns to it |
|---|---|
| `cast_server/services/render_job_service.py` | `_execute_pipeline` (4a checker stage), `publish` branches, `render_jobs` row |
| `cast_server/requirements_render/maker_gate.py` | `container_text_index` (4b-1 import), `check_html`/`check_what_doc` (4b widens) |
| `cast_server/db/schema.sql` + `tests/test_schema_migration.py` | 4a-2 adds the four flag columns |
| `cast_server/routes/pages.py` | `/render` badge injection, `/render/status` poll, `/render/diff` (4b view) |
| WHAT contract `cast-requirements-what/v1` (`sections[].block_refs`, `gaps[]`) | 4b id mapping, Phase 5 gaps |
| `docs/specs/cast-requirements-render.collab.md` **v4** | the recorded contract 4a/4b/5 cite verbatim |
