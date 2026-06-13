# Sub-phase 4b-3 — Spec deltas to record in 4b-4's single `/cast-update-spec` pass

> 4b-3 **flags** these; it does **not** edit `cast-requirements-render.collab.md` (4b-4 owns the
> one spec pass). Each flag below is realized in shipped, test-covered code.

## FR-024 — "byte-for-byte" wording RE-SCOPED

**Was:** `GET …/requirements/changes` returns `summarize(diff_blocks(old, new))` byte-for-byte.

**Now:** the payload gains a **sibling** `narration` key. `counts` and `items` stay **byte-for-byte**
`summarize()`; `narration` is `null` when none was posted. The byte-identity guarantee is re-scoped
to the `counts`/`items` keys (not the whole object).

- Code: `cast-server/cast_server/routes/api_requirements.py` (`changes()` → `{**summary, "narration": …}`).
- Test pin: `tests/test_diff_narration.py::test_changes_counts_items_byte_identical_with_and_without_narration`
  and `tests/test_diff_render.py::test_changes_json_matches_summarize` (updated to the re-scoped shape).

## FR-023 — version-route enumeration GAINS the narration POST

**Add to the route list:** `POST /api/goals/{goal_slug}/requirements/versions/{head}/narration`
— same-door, JSON-only, body `{base, overview, item_notes, created_by|actor}`.

- Slug-validated first (FR-014) → 404; unknown base/head version → 404.
- `save_narration` **recomputes** `summarize(diff_blocks(old, new))` server-side and **422s
  all-or-nothing** on any `item_note` whose `(change, heading_or_ref)` is absent from the
  deterministic set (offending keys echoed); size caps FR-017 (`overview` ≤ 2 KB, each note ≤ 2 KB,
  ≤ 1 note per item).
- `created_by` (the dispatching parent's actor id) rides the body; nothing about the caller is
  privileged (mirrors the resolve/relocate `actor` convention).

## New `linked_files` to add under the spec's `linked_files`

- `cast-server/cast_server/db/schema.sql` (table `version_diff_narrations`)
- `cast-server/cast_server/services/requirement_version_service.py` (`save_narration` / `get_narration`)
- `cast-server/cast_server/routes/api_requirements.py` (narration POST + `/changes` sibling)
- `cast-server/cast_server/templates/fragments/requirements_comments/changes_panel.html`
- `cast-server/cast_server/templates/fragments/requirements_comments/_diff_narration.html` (new partial)
- `cast-server/cast_server/requirements_render/templates/_theme.css.j2` (`.diff-narration` block)

## Invariants the spec should state (now structural in code)

- **"Never shows a change not in the source" is structural at three layers:** the agent prompt rule
  (4b-2) → the 422 recompute-and-validate gate (here) → lookup-only render (the panel iterates the
  deterministic `items`; a note with no matching item renders nothing).
- **Narration is LLM-authored text → autoescaped fragments only** (never `| safe` / `innerHTML`).
- **DB-only:** narration never writes the goal folder (FR-007 read-only guard stays green).
- **`block_diff.py` / `diff_render.py` are byte-untouched** (engine + tracked-changes view unchanged;
  narration is passed into the diff view by the route, not by modifying `diff_render.py`).
