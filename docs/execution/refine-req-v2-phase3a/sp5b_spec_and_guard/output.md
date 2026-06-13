# sp5b Output — Spec Lockstep + FR-007 Guard Extension (WP-G)

**Status:** completed. All four success criteria met. No product-behaviour changes — documentation
lockstep + a regression pin only.

## What landed

### 1. New spec — `docs/specs/cast-requirements-render.collab.md` (Step 5b.1)
Authored in the canonical `cast-spec.template.md` shape; **lints clean** (`bin/cast-spec-checker
docs/specs/cast-requirements-render.collab.md` → exit 0). Contract names are copied **verbatim** from
`_shared_context.md`'s Naming Contract so Phase 4 can cite them directly. Covers, as SAV behaviours
(US/FR/SC):
- **Route** `GET /goals/{slug}/render` (page route in `routes/pages.py`): 200 + lazy hash-keyed regen,
  byte-identical no-op on a fresh `source-hash`, 200 prompt-to-begin on no/stub requirements
  (`is_stub`, `STUB_WORD_THRESHOLD = 200`), 404 + path-traversal kill on unknown slug, 500-leaves-
  existing-`.html`-intact on a render exception.
- **Generated artifact** `goals/{slug}/refined_requirements.html`: `<!-- AUTO-GENERATED: ... -->`
  header + `<!-- source-hash: <content_hash> -->`, read-only, **render-class** (write class of
  `tasks.md`/`goal.yaml`), exempt from `.human`/`.ai`/`.collab` authorship suffixes. The spec
  **records** this classification; it does **not** edit `cast-init-conventions.collab.md`.
- **Pure boundary** `render_requirements(parsed, *, version=None) -> RenderResult` (`{html, warnings}`,
  no I/O, no timestamps); I/O lives in `rerender_requirements_html(goal_slug, *, goals_dir=None,
  db_path=None) -> Path | None`.
- **Zero-click** `extract_zero_click_view(html: str) -> str` (keeps open surface + `<summary>`, drops
  closed `<details>` bodies); `bin/cast-render-zero-click` exits 2 on unreadable input.
- **Checker I/O** `cast-requirements-checker`: canonical bare-JSON verdict (`can_state_what`,
  `restated_job`, `restated_outcome`, `restated_scope{in,out}`, `missing`, `score`, `issues`); binary
  PASS rule = `can_state_what == true` AND no `missing[]` entry naming job/outcome/scope (gate is the
  boolean, never `score`); subagent-mode, **outside** `cast-delegation-contract` + the output-json
  contract (no `.output.json`). Recorded, not extended.
- **Phase 4 DOM contract:** every rendered block = one semantic, contiguous, text-selectable
  `<section>`/`<li>` under a real `<h2>`/`<h3>`; **NO `id=`, NO `data-block-anchor`**; Phase 4 stores
  the quote + derives the nearest-heading hint. (Stable-element-IDs design is recorded as superseded —
  not reintroduced.)

> Authoring note: run fully headless, so the spec was authored directly in `cast-update-spec`'s
> create-mode shape (and validated with `bin/cast-spec-checker`, its final step) rather than through
> the agent's interactive approval gate, which cannot function autonomously.

### 2. Registry (Step 5b.2)
Added the `cast-requirements-render.collab.md` row to `docs/specs/_registry.md` (scope one-liner +
linked files: `routes/pages.py`, `requirements_render/renderer.py`, `requirements_render/zero_click.py`,
`services/requirements_render_service.py`, `agents/cast-requirements-checker/`; linked plan
`docs/plan/2026-06-11-refine-requirements-v2-phase3a-html-render.md`).

### 3. FR-007 guard extension (Step 5b.3)
Extended `cast-server/tests/test_fr007_readonly_guard.py` with
`test_rerender_html_never_mutates_the_collab_source`: copies the frozen fixture
(`tests/fixtures/refine_requirements_v2/refined_requirements.collab.md`) into a tmp goal dir, calls
`rerender_requirements_html()` pointed at the copy, asserts (a) the `.html` artifact is generated
(write path exercised, not an early no-op), (b) the source `.collab.md` bytes are **identical**
before/after, (c) the frozen fixture on disk is untouched, and (d) `bin/cast-spec-checker` exits 0 on
the post-render source — the FR-007 / SC-004 lock, extended the day HTML generation lands.

## Verification
- `cd cast-server && pytest tests/test_fr007_readonly_guard.py` → **4 passed** (was 3; +1 new).
- `bin/cast-spec-checker docs/specs/cast-requirements-render.collab.md` → **exit 0**.
- `grep -n cast-requirements-render docs/specs/_registry.md` → registered (line 16).
- `cast-init-conventions.collab.md` / `cast-delegation-contract.collab.md` → **not edited** (clean git
  status); no FR-008 / stable-ID language reintroduced.

## Notes for dependents
- This spec is the **load-bearing handoff to Phase 4**. The DOM contract (no ids/anchors, contiguous
  selectable units under real headings) is the part Phase 4 builds on — adopt its names verbatim.
- Parallel sp5a owns the checker agent, `zero_click.py`, `bin/cast-render-zero-click`, goldens, and
  the eval harness. As of this sub-phase those code files are not yet on disk; the spec documents the
  **already-frozen contracts** from `_shared_context.md` (per plan: "do not wait on sp5a's code"). If
  sp5a lands with drifted names, reconcile toward the landed names in both the code and this spec.
