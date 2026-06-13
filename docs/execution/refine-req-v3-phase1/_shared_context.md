# Shared Context: refine-req-v3-phase1 (Validate the Maker & the Anchor Backbone)

> Read this file at the start of **every** sub-phase session before opening the sub-phase plan.

## Source Documents

- **Plan (do not modify):** `docs/plan/2026-06-12-refine-requirements-v3-phase1-spikes.md`
- **Reconciliation report:** `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- **Binding owner decisions:** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
- **High-level plan:** `docs/goal/refine-requirements-better-rendering-v3/plan.collab.md`

## Project Background

Phase 1 is the **de-risking phase** of refine-requirements v3. Before the WHAT→HOW maker
pipeline (Phase 3) is built, two parallel spikes must each pass a gate:

- **1a (maker quality ceiling):** prove *by hand* that an LLM maker working from the
  cast-preso visual toolkit can produce a requirements render that clearly beats the v2
  deterministic page for ≥2 work families, emits every canonical id verbatim on the correct
  block (FR-003), and stays a self-contained single file (FR-007).
- **1b (anchor backbone survival):** attach the **existing, unmodified** v2 comment/version
  layer to a hand-crafted *varying* maker-style HTML and confirm the resolved
  logical-backbone + quote-anchored-DOM approach holds — zero new orphans on a
  regenerate-with-moved-text, with v2's "NO `id=`" DOM contract intact.

**Key grounding insight (sharpens, does not change, the spike design):** the v2
comment/version machinery anchors to the **canonical markdown source**, not to the HTML.
`relocate_comment`'s verbatim backstop (FR-019), `create_next`'s `displaced_comment_ids`
string-find (FR-022), and `block_diff._key`'s `(kind, ref)` matching all run against the
`.collab.md` text — and the maker never writes that file (v3 FR-008). A varying maker render
therefore **cannot orphan a comment at the DB layer by itself**. The genuine risks 1b
instruments are (1) silent `<mark>`-placement loss when the maker paraphrases requirement
text, (2) the implied "anchorable text carried verbatim and contiguous in the DOM" maker
obligation, and (3) source-edit regeneration exercising the full v2 reanchor chain.

## Operating Mode — HOLD SCOPE (binding)

`refined_requirements.collab.md` front-matter pins `scope_mode: hold`. Owner-resolved
decisions in `refine-requirements-better-rendering-v3-decisions-so-far.md` are **binding**.
Phase 1 **validates** the anchor-backbone decision and may only surface a *revisit-trigger* —
**never re-decide it, never change the approach, the DOM contract, or any spec.**

## Codebase Conventions

- **Throwaway DB everywhere:** all v2 services take an injectable `db_path=`. Spikes use a
  scratch SQLite file under `spikes/1b/` — **never the live house DB**, never real goal folders.
- **Spike artifacts live under `docs/goal/refine-requirements-better-rendering-v3/spikes/{1a,1b}/`.**
  **Never** write `goals/{slug}/refined_requirements.html` — that filename is a render-class
  artifact wired to the lazy-regen route and the FR-026 folder invariant; a hand-crafted file
  there would be served live and/or trip `test_fr007_readonly_guard.py`.
- **Spike scripts** are named `spike_*.py` and kept under `spikes/`, **not** under
  `cast-server/tests/` — pytest must never collect them.
- **Phase 1 makes NO spec changes and NO `/cast-update-spec` calls.** Specs are consumed
  read-only. Carry-forward gaps are *recorded*, not acted on.
- **Phase 1 must not touch Phase-2-owned files:** `goal_card.py`, `_first_sentence` /
  `_split_first_sentence`, the comment-affordance UI.

## Key File Paths (existing v2 — consumed, never modified in Phase 1)

| File | Role |
|------|------|
| `cast-server/cast_server/static/requirements_comments.js` | Browser `<mark>` placement: tree-walks a block container's text nodes, runs `indexOf(quoted_text)` on concatenated text. **The algorithm 1b's Python harness must mirror byte-faithfully.** |
| `cast-server/cast_server/services/comment_service.py` | Flat functions w/ injectable `db_path`: `create_comment`, `relocate_comment`, `orphan_comment`, `open_comment_count`, … (FR-020) |
| `cast-server/cast_server/services/requirement_version_service.py` | `create_next(goal_slug, content, created_by, *, db_path=None)` → `{version, convergence, open_comments, displaced_comment_ids}` (FR-021/022) |
| `cast-server/cast_server/requirements_render/block_diff.py` | `diff_blocks` / `summarize` — pure, keyed on `(kind, ref)` for US/FR/SC blocks (FR-024) |
| `cast-server/cast_server/requirements_render/renderer.py` | `render_requirements()` — the v2 deterministic baseline (call purely; do **not** drop files into `goals/{slug}/`) |
| `cast-server/cast_server/requirements_render/zero_click.py` | `extract_zero_click_view` — feeds the SC-001 checker |
| `agents/cast-requirements-checker/` | SC-001 cold-reader gate; bare-JSON verdict. **1a delegation.** |
| `agents/cast-comment-reanchor/` | Reanchor subagent; bare-JSON verdicts, orphan-over-guess (FR-027). **1b delegation.** |
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` + `.v2-edit.collab.md` | The 1b source pair (extend with a heavier edit if needed) |
| `~/.claude/skills/cast-preso-visual-toolkit/` | `visual_toolkit.human.md` style tokens + `templates/slide-archetypes/*.html` (11 archetypes). 1a follows its 8-step *discipline* **by hand**. |

## Data Contracts (verbatim from the plan)

- **`create_next` returns** `{version, convergence, open_comments, displaced_comment_ids}`.
  `displaced_comment_ids` comes from a string-find of the **new source markdown** (not HTML).
- **`cast-comment-reanchor` inputs** `{displaced comments, old_content, new_content}` where
  `new_content` is the **new source markdown** (per the v2 contract), not the maker HTML.
- **FR-019 verbatim backstop:** `relocate` is rejected (422) unless `new_quoted_text` is a
  verbatim substring of the new source. A rejected relocate downgrades to orphan and counts
  **against** the 1b gate.
- **FR-028 progressive enhancement:** the *only* sanctioned script references in an otherwise
  self-contained file are `/static/htmx.min.js`, `/static/requirements_comments.js`, plus a
  `data-goal-slug` attribute. No CDN fonts, CSS inline.
- **FR-012/FR-013 DOM contract:** zero `id=`, zero `data-block-anchor` anywhere; each
  requirement unit one contiguous semantic `<section>`/`<li>` under a real `<h2>`/`<h3>`.

## Relevant Specs (read-only in Phase 1 — do NOT modify)

- `docs/specs/cast-requirements-render.collab.md` (Draft v2) — DOM contract (US7), zero-`id`
  (FR-012/013), relocate backstop (FR-019), `create_next`/displaced (FR-021/022), `block_diff`
  (FR-024), folder invariant (FR-026), reanchor carve-out (FR-027), progressive enhancement
  (FR-028), SC-001 checker gate. **One carry-forward gap** (verbatim-carriage clause) is flagged
  for Phase 3's `/cast-update-spec` — recorded only, not acted on here.
- `docs/specs/cast-goal-classification.collab.md` (Draft v1) — `WorkFamily` nine-value enum;
  `FAMILY_RECIPES`/`RECIPE_REALIZATION` (starting vocabulary for family-appropriate sections).

Sub-phase agents read these specs on-demand only when a step references spec-linked files.
Phase 1 modifies none of them.

## Sub-Phase Dependency Summary

| ID | Type | Depends On | Blocks | Can Parallel With |
|----|------|-----------|--------|-------------------|
| sp1a | Sub-phase | — | G1 | sp1b |
| sp1b | Sub-phase | — | G1 | sp1a |
| G1 | Gate | sp1a, sp1b | Phase 3 (entry) | — |

sp1a and sp1b are **independent** and write **disjoint** directories (`spikes/1a/` vs
`spikes/1b/`). 1b may opportunistically reuse 1a's HTML if ready, but must **not wait** on it —
it hand-crafts its own minimal varying HTML pair otherwise.
