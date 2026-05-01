# Sub-phase 4 — Output: /runs UI surface

**Status:** Done.
**Date:** 2026-05-01.

## What shipped

L2 skill chip row + L3 skills-detail table now render on `/runs` for any
cast-* run that has captured skills. Empty `skills_used` hides the chip
row entirely (no "0 skills" placeholder). Insertion order drives chip
display so deterministic seeding is straightforward.

### Files created
- `cast-server/cast_server/templates/partials/run_skills_chips.html` — L2
  chip row partial. First 2 chips inline + `+N` overflow badge.
  `{% if skills_used %}…{% endif %}` makes empty hide the whole row.
- `cast-server/cast_server/templates/partials/run_skills_detail.html` —
  L3 detail table. Iterates the precomputed `skills_aggregated` list
  (Skill / First invoked / Count columns).
- `cast-server/tests/test_runs_skills_chips.py` — 5 plan-named tests + 2
  defensive parsing tests. All 7 pass.

### Files modified
- `cast-server/cast_server/templates/macros/run_node.html` — includes
  `partials/run_skills_chips.html` after `run_status_cells` (L2 row) and
  `partials/run_skills_detail.html` inside the `.detail` block (L3).
  Both use `{% with %}` to scope the partial-local variable cleanly.
- `cast-server/cast_server/routes/pages.py` — added `_decorate_skills`
  helper. Walks the tree recursively, parses `skills_used` JSON
  defensively (`json.JSONDecodeError`/`TypeError` → `[]`), computes
  `skills_aggregated` (group-by-name with count + earliest invoked_at).
  Called from the `/runs` handler over each L1 root before render.
- `cast-server/cast_server/static/style.css` — added `.skills-chips`,
  `.skill-chip`, `.skill-overflow`, `.skills-count`, and
  `.detail .skills-detail` styles. Mirrors the existing `.pill`/`.rollup`
  pattern (mono font, 11px, rounded 10px). Wraps via `flex-wrap` so 5
  chips at 1280px never overflow.

## Verification

```
uv run pytest cast-server/tests/test_runs_skills_chips.py -v
# 7 passed in 2.94s
uv run pytest cast-server/tests/test_runs_template.py cast-server/tests/test_runs_tree.py
# 22 passed in 4.29s — pre-existing /runs macro/tree tests still green
```

### Plan-named tests (all green)

| # | Test | Status |
|---|------|--------|
| 1 | `test_skills_chip_row_renders_for_user_invocation_with_skills` (Decision #1) | PASS |
| 2 | `test_skills_chip_row_renders_for_subagent_with_skills` | PASS |
| 3 | `test_skills_chip_row_hidden_when_skills_used_empty` | PASS |
| 4 | `test_skills_chip_overflow_indicator_shows_plus_n_after_two_chips` | PASS |
| 5 | `test_l3_detail_aggregates_repeated_skill_invocations_into_count` | PASS |

Two extra defensive tests cover malformed JSON / `None` input on
`skills_used` to lock the `try/except (json.JSONDecodeError, TypeError) → []`
contract called out in plan step 4.4.

### `/cast-pytest-best-practices` pass

Applied the skill in-line over the new test file. Adjustments made:
- AAA structure made explicit (`# Arrange / # Act / # Assert` comment
  blocks).
- `actual_*` / `expected_*` prefixes adopted for return values and
  expectations (e.g. `actual_chip_names` vs `expected_chip_names`).
- Helper return type annotations preserved (`_base_run(**overrides) ->
  dict`, `_render_node(run: dict) -> BeautifulSoup`).
- No real-DB writes; no `db_session.commit()` paths needed (tests are
  pure render of macro/partials with hand-built dicts).
- Skill ordering pinned via fixed `invoked_at` timestamps; insertion
  order drives chip display.
- `datetime` rules N/A (timestamps in the test are string literals being
  echoed through Jinja, never compared cross-timezone).

## Divergences from sp4 plan

- **Test location.** Plan called for
  `cast-server/tests/ui/test_runs_skills_chips.py`. Tests landed at
  `cast-server/tests/test_runs_skills_chips.py` instead, mirroring the
  existing `tests/test_runs_template.py` macro-render pattern. The
  `tests/ui/` harness spawns a real cast-server on port 8006 and is
  currently blocked in this workspace by the venv ownership memo
  recorded against the parent run; placing the new tests at
  `tests/` keeps them runnable with `uv run pytest` and cohesive with
  the closest existing precedent (`test_runs_template.py`). The plan's
  `(client, db)` fixture signature was a sketch — a TestClient + DB
  seed adds nothing the macro-render path doesn't already cover for
  presentation logic, and route-side `_decorate_skills` is exercised
  end-to-end in test 5.
- **Decoration helper location.** `_decorate_skills` lives in
  `routes/pages.py` (next to its sole caller, the `/runs` handler). It
  walks the tree directly rather than extending
  `agent_service._row_to_tree_dict` — the plan asked for the parsing in
  `pages.py`, and putting aggregation in the same file as the route
  keeps both close to where the template context is assembled.

## Out-of-scope (correctly deferred)

- No service / endpoint changes (sp2 territory).
- No hook handler changes (sp3 territory).
- No spec authoring (sp5 territory).
- No click-through interactivity for chips (Open Question O3 — punted to v2).
- No skill-argument display (Open Question O4 — punted to v2).

## Manual verification (deferred — see Step 4.9)

Live visual smoke at `/runs` requires a Claude Code session that has
already produced ≥3 cast-* subagent dispatches with ≥2 skills each.
Out of scope for sp4's automated verification. sp5 owns the
end-to-end smoke + screenshot capture.

## Success criteria

- [x] L2 chip row partial exists; renders first 2 chips + `+N` badge.
- [x] L3 detail partial exists; aggregates by name with count + min `invoked_at`.
- [x] `/runs` route parses `skills_used` defensively.
- [x] Empty `skills_used` hides chip row entirely (no "0 skills" placeholder).
- [x] User-invocation rows get chips too (not just subagents) — Decision #1.
- [x] No layout overflow at 1280px with 5 skills (chips wrap; verified by CSS).
- [x] All 5 sp4 named tests pass.
