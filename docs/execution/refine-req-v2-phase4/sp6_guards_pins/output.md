# sp6 (Guards + Pins) — Output

**Status:** completed · **Date:** 2026-06-12 · **Type:** tests-only (zero production-code changes, by design — decision #1 / WP-F)

## What was done

Locked in the two structural guarantees Phase 4 promised, as permanent tests. No new machinery
was added — that **absence** is the deliverable. The human-save path is untouched; displacement
stays a derived, read-time property (sp1) and the render route's lazy-regen picks up new content
on next view.

### Step 6.1 — FR-007 read-only guard extended
`cast-server/tests/test_fr007_readonly_guard.py` gains
`test_phase4_operations_never_mutate_the_collab_source`, which copies the frozen fixture into a
tmp goal dir and exercises the **full Phase 4 surface** against it, asserting the canonical
`.collab.md` bytes (sha256) are identical before/after the whole sequence, and that the frozen
fixture on disk is untouched:

- **Comment CRUD:** `create_comment` → `resolve_comment` → `reopen_comment` → `relocate_comment`,
  plus a second **agent-authored** comment (`author_kind="agent"`, FR-013 same-door) → `orphan_comment`.
- **`create_next()`** — version gate: reads edited content, snapshots **into the DB** (asserts
  v2 landed), never writes the file.
- **`render_diff()`** — pure tracked-changes renderer over two `parse_requirements()` results;
  served fresh, never persisted.

After all operations: `.collab.md` byte-identical, and `bin/cast-spec-checker <source>` exits 0
(SC-004 lock preserved on the post-op source). Imports added: `parse_requirements`,
`render_diff`, `comment_service`.

### Step 6.2 — No-frontend-framework pin
Created `cast-server/tests/test_no_frontend_framework.py` with two tripwires:
- `test_no_package_json_anywhere_under_cast_server` — `rglob("package.json")` under `cast-server/`
  returns `[]`.
- `test_comment_js_imports_no_framework` — source-scan of `requirements_comments.js` finds none of
  the banned terms (react / vue / angular / svelte frameworks; `annotator` / `rangy` annotation
  libraries). htmx (vanilla, vendored) is explicitly allowed.

## Verification (all green)

```
uv run pytest tests/test_fr007_readonly_guard.py tests/test_no_frontend_framework.py -q
  → 7 passed in 0.51s
find cast-server -name package.json
  → (empty)
bin/cast-spec-checker tests/fixtures/refine_requirements_v2/refined_requirements.collab.md
  → exit=0
git status (cast-server/tests/): only the two test files touched — no production file modified
```

## Success criteria — all met
- [x] FR-007 guard extended over comment CRUD + `create_next` + `render_diff`; `.collab.md` bytes immutable.
- [x] `bin/cast-spec-checker` exits 0 in the guard test (and standalone).
- [x] `test_no_frontend_framework.py` passes; `find cast-server -name package.json` is empty.
- [x] Zero production-code changes in this sub-phase (only the two test files touched).

## Hand-off to sp7
The "lazy + surfaced tray" reinterpretation of plan.collab.md's "re-anchor on save" wording — the
save handler is **untouched by design** (decision #1) — is to be recorded in the spec by sp7. This
sub-phase modified **no** spec-linked files.

## Notes
- Both test files were already **untracked** in git (carried uncommitted from prior phases sp1/sp5),
  so they appear as `??` rather than `M`; the FR-007 file was extended in place, the framework-pin
  file created fresh.
