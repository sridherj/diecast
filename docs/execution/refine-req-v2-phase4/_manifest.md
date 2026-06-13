# Execution Manifest: refine-req-v2-phase4 (Annotation & Versioning Engine)

Faithful split of `docs/plan/2026-06-11-refine-requirements-v2-phase4-annotation-versioning.md`
(HOLD SCOPE). Phases 1/2/3a are LANDED; this plan adopts the verified landed names (see
`_shared_context.md`).

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: *"Read `docs/execution/refine-req-v2-phase4/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase4/spN_name/plan.md`."*
3. After completion, update the Status column below and append to the Progress Log.

Or run the whole thing via `/cast-orchestrate docs/execution/refine-req-v2-phase4`.

## Sub-Phase Overview

| # | Sub-phase | Directory | Depends On | Status | Notes |
|---|-----------|-----------|-----------|--------|-------|
| 1 | Comment service + same-door API (FR-013 forcing function) | `sp1_comment_service_api/` | — | Not Started | WP-A. Parallel with sp2 |
| 2 | `block_diff` pure engine + `diff_render` | `sp2_block_diff_engine/` | — | Not Started | WP-B (pure half). Parallel with sp1 |
| 3 | `create_next()` + carry-forward + convergence + archive | `sp3_versions_archive/` | 1 | Not Started | WP-C. Critical path |
| 4a | Diff-view wiring (route, /changes, toggle, diff CSS) | `sp4a_diff_view_wiring/` | 2, 3 | Not Started | WP-B (wiring half). Parallel with 4b |
| 4b | `cast-comment-reanchor` agent + verdict apply + loop + eval | `sp4b_reanchor_agent/` | 1, 3 | Not Started | WP-D. Critical path. Parallel with 4a |
| 5 | Vanilla-JS comment layer + tray (locked UX) | `sp5_comment_js_layer/` | 1, 4a | Not Started | WP-E. After sp4a (shares template) |
| 6 | Human-edit guards + FR-007/no-framework pins | `sp6_guards_pins/` | 1, 3, 4a, 5 | Not Started | WP-F. Tests only |
| 7 | Spec lockstep + e2e harness + compliance | `sp7_spec_e2e_compliance/` | ALL | Not Started | WP-G. Last (interfaces settled) |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision gates** — plan Open Questions are "None blocking." No human pause points.

## Dependency Graph

```
            ┌──────────────────────────── parallel pair 1 ───────────────┐
  (start) ──┤ sp1 comment_service + same-door API  (WP-A)                 │
            │ sp2 block_diff engine (pure)         (WP-B-pure)            │
            └────────┬───────────────────────────────────┬───────────────┘
                     │ sp1                                 │ sp2
                     ▼                                     │
            sp3 create_next + archive  (WP-C) ◄────────────┤ (sp3 needs sp1)
                     │                                     │
        ┌────────────┴──────────────── parallel pair 2 ────┴──────────────┐
        │ sp4a diff-view wiring  (WP-B-wiring)  [needs sp2 + sp3]         │
        │ sp4b reanchor agent + loop + eval (WP-D)  [needs sp1 + sp3]     │
        └────────┬───────────────────────────────────────────────────────┘
                 │ sp4a
                 ▼
            sp5 vanilla-JS comment layer  (WP-E)  [needs sp1 + sp4a]
                 │
                 ▼
            sp6 guards + pins  (WP-F)  [needs sp1, sp3, sp4a, sp5]
                 │
                 ▼
            sp7 spec + e2e + compliance  (WP-G)  [needs ALL]
```

**File-disjointness of the parallel pairs (verified):**
- **Pair 1 — sp1 ∥ sp2:** sp1 = `comment_service.py`, `api_requirements.py`, `app.py`,
  `fragments/requirements_comments/{tray,thread_item}.html`. sp2 = `block_diff.py`,
  `diff_render.py`, `test_block_diff.py`, the `v2-edit` fixture. **No shared file.**
- **Pair 2 — sp4a ∥ sp4b:** sp4a = `pages.py`, `api_requirements.py` (`/changes`),
  `document.html.j2` (toggle), `_theme.css.j2` (diff CSS), `test_diff_render.py` + diff goldens.
  sp4b = `agents/cast-comment-reanchor/*`, `cast-refine-requirements.md` + its `config.yaml`,
  `eval_reanchor.py`. **No shared file.**
- `api_requirements.py` is edited by sp1 → sp3 → sp4a in that **sequential** order (never in
  parallel). `document.html.j2` + `_theme.css.j2` are edited by sp4a → sp5 **sequentially**.

## Execution Order

### Parallel Group 1 (start — run simultaneously)
1. sp1: Comment service + same-door API
2. sp2: `block_diff` pure engine + `diff_render`

### Sequential Group 2 (after sp1)
3. sp3: `create_next()` + carry-forward + convergence + archive retrieval

### Parallel Group 3 (after sp3; sp4a also needs sp2 — run simultaneously)
4a. sp4a: Diff-view wiring
4b. sp4b: `cast-comment-reanchor` agent + verdict application + loop + eval

### Sequential Group 4 (after sp4a)
5. sp5: Vanilla-JS comment layer + tray

### Sequential Group 5 (after sp5)
6. sp6: Human-edit guards + FR-007/no-framework pins

### Sequential Group 6 (after everything)
7. sp7: Spec lockstep + e2e harness + compliance

## Phase Gate (the whole plan is done when these pass)

```
pytest tests/test_requirements_comments_api.py     # FR-013 dual-assertion (sp1)
pytest tests/test_comment_service.py               # CRUD + in-txn events (sp1)
pytest tests/test_block_diff.py                    # partition invariant + determinism (sp2)
pytest tests/test_requirement_versions.py          # create_next + carry-forward + displaced (sp3, extended)
pytest tests/test_archive_retrieval.py             # US5 S3 as-of reconstruction (sp3)
pytest tests/test_diff_render.py                   # tracked-changes goldens (sp4a)
pytest tests/test_fr007_readonly_guard.py          # bytes-identical guard (sp6, extended)
pytest tests/test_no_frontend_framework.py         # package.json absence pin (sp6)
python tests/eval_reanchor.py                      # decision-#9 build-time gate (sp4b, manual)
# e2e UI harness (cast-server/tests/ui/) + manual SC-002 dry run (sp7)
bin/cast-spec-checker                              # exit 0 (sp6)
```

## Progress Log

_(Update after each sub-phase: date, sub-phase, outcome, deviations recorded.)_

- _Not started._
