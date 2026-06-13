# Sub-phase 4b-3: Narration Lands Same-Door — Stored Once, Validated Structurally, Rendered by Attachment

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4b/_shared_context.md` before starting.

## Objective

A version cut can carry one stored narration per `(base, head)` pair, posted same-door by whichever
agent cut the version; the server **structurally rejects** any narration referencing a change absent
from the deterministic set (recomputed `summarize()` server-side); the changes panel and
tracked-changes view render narration **only** by attaching notes to deterministic items — so the UI
cannot display an invented change even if the DB were hand-edited. No narration ⇒ the deterministic
panel serves exactly as today.

## Dependencies

- **Requires completed:** **4b-2** (the narration schema this stores is the agent's output shape:
  `{overview, item_notes:[{change, heading_or_ref, note}]}`).
- **Assumed codebase state:** `block_diff.diff_blocks` / `summarize` (`block_diff.py:174`),
  `requirement_version_service.get_version` / `list_versions`, `GET /changes`
  (`api_requirements.py:290`, returns `summarize()` JSON / `changes_panel.html` fragment),
  `goal_service.get_goal` (FR-014 slug validation), `test_schema_migration.py` pattern,
  `test_fr007_readonly_guard.py` sweep, `test_block_diff.py` / `test_diff_render.py`.
- **Parallel with 4b-1.** Shared file: `_theme.css.j2` (additive-append seam — see manifest).

## Scope

**In scope:**
- New table `version_diff_narrations` in `schema.sql` (+ migration-test coverage).
- `save_narration` / `get_narration` flat functions in `requirement_version_service.py`
  (injectable `db_path`); `save_narration` recomputes the diff server-side + all-or-nothing 422
  validation + size caps + upsert-on-repost.
- `POST /api/goals/{goal_slug}/requirements/versions/{head}/narration` in `api_requirements.py`.
- `GET …/changes` gains a sibling `narration: {...} | null` key (`counts`/`items` byte-identical).
- `changes_panel.html` renders the overview (labeled, autoescaped) + per-item notes by lookup;
  `render_diff`'s "What changed" panel gains the same optional strip **via the route only**
  (`diff_render.py` itself NOT modified).
- `.diff-narration` CSS in `_theme.css.j2`.
- `cast-server/tests/test_diff_narration.py` + fragment tests.

**Out of scope (do NOT do these):**
- Do NOT dispatch any LLM on the version path — the server stores + validates; the *parent agent*
  narrates (4b-2). A human-initiated cut simply has no narration.
- Do NOT modify `block_diff.py` or `diff_render.py` logic (the deterministic engine + view stay
  byte-identical; narration is passed into the view by the route).
- Do NOT change `counts`/`items` in the `/changes` payload (FR-024 byte-for-byte re-scoped to those
  keys; `narration` is a **sibling**).
- Do NOT render narration via `innerHTML` / `| safe` — autoescaped fragments only.
- Do NOT write to the goal folder (narration is DB-only — keep the FR-007 read-only guard green).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/schema.sql` | Modify | gains `version_diff_narrations` CREATE TABLE |
| `cast-server/cast_server/services/requirement_version_service.py` | Modify | gains `save_narration` / `get_narration` |
| `cast-server/cast_server/routes/api_requirements.py` | Modify | gains the narration POST; `/changes` gains the `narration` sibling key |
| `cast-server/cast_server/templates/fragments/requirements_comments/changes_panel.html` | Modify | attaches narration by `(change, heading_or_ref)` lookup |
| `cast-server/cast_server/templates/.../_theme.css.j2` | Modify (append) | append `.diff-narration` block (disjoint from 4b-1's `.comment-unplaced`) |
| `cast-server/tests/test_diff_narration.py` | Create | Does not exist |
| `cast-server/tests/test_schema_migration.py` | Modify | add `version_diff_narrations` coverage |

> Locate the tracked-changes view template + its route handler (`grep -rn "render_diff\|render/diff" cast-server/cast_server/routes/`) to add the optional narration strip via the route.

## Detailed Steps

### Step 4b3.1: Schema + migration test

Add to `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS version_diff_narrations (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_slug     TEXT NOT NULL,
  base_version  INTEGER NOT NULL,
  head_version  INTEGER NOT NULL,
  overview      TEXT NOT NULL,
  item_notes    TEXT NOT NULL,          -- JSON [{change, heading_or_ref, note}]
  created_by    TEXT,                   -- the dispatching parent's actor id
  created_at    TEXT NOT NULL,
  UNIQUE(goal_slug, base_version, head_version)
);
```

Add `version_diff_narrations` to the `test_schema_migration.py` coverage (mirror the `render_jobs`
migration-test pattern).

### Step 4b3.2: `save_narration` / `get_narration` (the validation core)

```python
def save_narration(goal_slug, base, head, overview, item_notes, created_by, *, db_path=None):
    """Load both version rows (404 if absent); recompute summarize(diff_blocks(old, new))
    server-side; validate EVERY item_note keys to a deterministic (change, heading_or_ref) item —
    ANY mismatch raises (route → 422) listing the offending keys. Size caps (FR-017): overview
    <= 2 KB, each note <= 2 KB, <= 1 note per item. Upsert on (goal_slug, base, head)."""

def get_narration(goal_slug, base, head, *, db_path=None) -> dict | None: ...
```

- Recompute the diff from the loaded snapshots (never trust the poster). Build the set of valid
  `(change, heading_or_ref)` keys from `summarize()`'s `items`.
- **All-or-nothing:** if any `item_note` key is not in that set, raise with the offending keys listed
  (prompt-ready for the parent's single retry). Never silently drop a note.
- Upsert: a retried loop cycle replaces, never duplicates.

### Step 4b3.3: The narration POST route

`POST /api/goals/{goal_slug}/requirements/versions/{head}/narration`, body `{base, overview,
item_notes, created_by}`:
- **`created_by` rides the request body** (same-door, nothing privileged) — the dispatching parent
  (4b-2) knows its own actor id and sends it, matching the `actor` convention on the resolve/relocate
  POSTs. The server stamps `version_diff_narrations.created_by` from it. (Accept `actor` as an alias
  if that reads more consistently with the existing comment-transition routes.)
- `goal_service.get_goal` slug validation first (FR-014) → 404 on unknown slug.
- JSON-only (agents are the writers; humans read). Same-door: nothing about the caller is privileged.
- Map `save_narration`'s validation raise → **422** with the offending keys; unknown version → 404;
  size-cap violation → 422.

### Step 4b3.4: `/changes` sibling key + panel rendering

- `GET …/changes` JSON gains `narration: get_narration(...) | null` **beside** `counts`/`items` —
  which stay **byte-for-byte** `summarize()`.
- `changes_panel.html`: after the deterministic counts line (unchanged), render an overview paragraph
  **visibly labeled as agent narration** (`.diff-narration`, **autoescaped** — never `| safe`), then
  per-item notes attached by `(change, heading_or_ref)` lookup against the deterministic `items`. A
  narration row with no matching item renders nothing for that note (lookup-only render).
- `render_diff` (tracked-changes view): the **route** passes the matching stored narration into the
  view's "What changed" panel as the same optional strip; the view template stays byte-identical when
  no narration exists. `diff_render.py` is not modified.

### Step 4b3.5: `.diff-narration` CSS

Append a `.diff-narration` block to `_theme.css.j2` following the existing `.diff-*` conventions
(a visibly-distinct "agent narration" affordance). **Additive, disjoint** from 4b-1's
`.comment-unplaced` — whichever lands second appends after.

## Verification

### Automated Tests (permanent)
`pytest cast-server/tests/test_diff_narration.py` green:
- save/get round-trip;
- upsert on re-post (no duplicate row);
- **422 on any `item_note` whose `(change, heading_or_ref)` does not match the recomputed
  `summarize()` items** (all-or-nothing — no silent note-dropping); response lists offending keys;
- 422 on size-cap violations (overview > 2 KB, note > 2 KB, > 1 note per item);
- 404 on unknown version / unknown slug;
- the `GET …/changes` JSON `counts`/`items` stay **byte-identical** to `summarize()` both with
  narration present and absent (the `narration` sibling is the only addition).

Fragment tests:
- `changes_panel.html` renders the overview labeled as agent narration plus per-item notes only on
  items that exist;
- a narration row with no matching item (forced via test seam) renders nothing for that note;
- narration text containing HTML metacharacters is escaped (autoescape proof — no `innerHTML`).

Regression sweeps (must stay green, untouched):
- `test_fr007_readonly_guard.py` (narration is DB-only; no goal-folder writes);
- `test_block_diff.py` / `test_diff_render.py` (the deterministic engine + view did not change);
- `test_schema_migration.py` (now covers `version_diff_narrations`).

### Validation Scripts (temporary)
- One-off: POST a narration with a deliberately wrong key, assert 422 + the offending key echoed;
  POST a valid one, GET `/changes`, confirm `counts`/`items` byte-identical to the no-narration JSON.

### Manual Checks
- `grep -n "safe\|innerHTML" cast-server/cast_server/templates/fragments/requirements_comments/changes_panel.html`
  — narration must NOT be marked safe.
- Confirm `block_diff.py` and `diff_render.py` show **no diff** (engine + view untouched).

### Success Criteria
- [ ] `version_diff_narrations` table + migration-test coverage; `UNIQUE(goal_slug, base, head)`
      upsert-on-repost.
- [ ] `save_narration` recomputes the diff server-side; all-or-nothing 422 listing offending keys;
      size caps enforced; `created_by` = dispatching parent's actor id.
- [ ] Narration POST behind slug validation, JSON-only; 404/422 semantics correct; `created_by`
      taken from the request body and stamped on the row.
- [ ] `/changes` `counts`/`items` byte-identical; `narration` a sibling key.
- [ ] Panel + tracked-changes view render narration by attachment only, autoescaped; deterministic
      panel byte-identical when no narration.
- [ ] `block_diff.py` / `diff_render.py` unchanged; FR-007 read-only guard + block-diff/diff-render
      tests green.

## Execution Notes

- **Validation recomputes the diff rather than trusting the poster** — that, plus attachment-only
  rendering, makes "never shows a change not in the source" structural at three layers (prompt rule
  in 4b-2 → 422 gate here → lookup-only render here).
- **All-or-nothing 422, never silent note-dropping** — silently dropping a non-matching note would
  hide narration drift. Reject whole; the parent retries once then proceeds narration-less.
- **A missing narration is a normal state, not an error** — the deterministic panel is the floor
  (consistent with v2's "re-anchoring runs only at the next agent touchpoint, never on a human save").
- **Spec-linked files:** FR-024's "byte-for-byte" wording + FR-023's version-route enumeration
  change. **Flag for 4b-4's `/cast-update-spec` — do not edit the spec here.**
