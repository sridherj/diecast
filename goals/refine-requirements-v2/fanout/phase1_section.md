## Phase 1: Foundation — Spec-Kit Parser & Thin Sidecar Spine
> *(Provisional until the Phase 0 human gate clears — see above.)*
**Outcome:** `refined_requirements.collab.md` parses into an ordered, typed **block model** for
rendering, and a **thin DB spine** exists — comment rows, version snapshots, and content hashes — with
**no deterministic anchoring engine** (comments store a quote + section hint; a subagent re-locates
them). The `.collab.md` file remains byte-canonical (FR-007 untouched). Every later phase consumes this.
**Dependencies:** None (the downscaled keystone — build first).
**Estimated effort:** 1-2 sessions (smaller than the original draft — the anchoring engine is deleted
per the thin-spine decision).
**Verification:** `pytest` — parser produces the expected typed blocks from this goal's own
`refined_requirements.collab.md`; `bin/cast-spec-checker` exits 0 on the file unchanged; a snapshot
test pins the version-snapshot + content-hash behavior.

Key activities:
- **Codify the resolved architecture as a short design note** (`docs/design/` or atop the parser
  module): files-canonical + **thin DB spine** (comment rows / version snapshots / conflict hash), no
  per-element IDs, **no deterministic anchoring engine** — comments are stored with a quote + section
  hint and re-located by a Claude subagent. Record this so future readers don't re-inherit either the
  playbooks' DB-canonical/ULID premise *or* assume a heavy anchor scheme.
- **Build `requirements_render/parser.py`:** read `refined_requirements.collab.md` → ordered typed
  blocks `{kind, level, body}` where `kind ∈ {Intent, UserStory, FR, SC, Constraint, Scope,
  Directional, OpenQuestion}`. Reuse the spec-checker's own regexes (`US_HEADING_RE`, `FR_ID_RE`,
  `SC_ID_RE`, `EARS_SCENARIO_RE`) as the grammar so the parser and the FR-007 contract can never drift.
  This serves the render only — it is **not** a comment-anchoring index.
- **Add the thin DB spine** via the house migration pattern (`db/connection.py` `_run_migrations()` +
  `schema.sql`): `requirement_versions` (file snapshots + a per-version content hash) and
  `requirement_comments` (+ append-only `comment_events` trail). A comment row stores
  `{goal_slug, version, quoted_text, section_hint, state, author, ...}` — **no `block_anchor` column,
  no element surrogate.** Re-location is a runtime subagent step, not a stored key. Defer routing
  columns to Phase 3b and `change_request*` tables to Phase 5.
- **FR-007 read-only guard (golden-file test):** assert that generating the HTML render does **not**
  mutate `.collab.md` bytes and `bin/cast-spec-checker` stays green. Trivial under files-canonical —
  the render only *reads* the file.

