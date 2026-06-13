# Sub-phase 6: Human-edit guards + FR-007/no-framework pins (the lazy decision)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Lock in the two structural guarantees Phase 4 promised, as tests — **not as new machinery**. WP-F's
defining property is that the human-save path **changes not at all**: displacement is derived at
read time (sp1), and the render route's existing lazy-regen picks up the new content hash on next
view. This sub-phase proves (a) every Phase 4 operation leaves the canonical `.collab.md` bytes
identical (FR-007), and (b) no frontend framework crept in (the `package.json` absence pin).

## Dependencies

- **Requires completed:** sp1 (comment CRUD), sp3 (`create_next`), sp4a (`render_diff` route), sp5
  (the JS layer to scan). These are the operations the guards assert over.
- **Assumed codebase state:** `tests/test_fr007_readonly_guard.py` exists (Phase 1); the frozen
  fixture `.collab.md` is the byte-reference; `bin/cast-spec-checker` runs and exits 0 on the fixture.

## Scope

**In scope:**
- Extend `tests/test_fr007_readonly_guard.py` — comment CRUD + `create_next()` + `render_diff()`
  leave the fixture `.collab.md` bytes identical; `bin/cast-spec-checker` exit 0.
- Create `tests/test_no_frontend_framework.py` — `find cast-server -name package.json` (rglob)
  returns nothing; `requirements_comments.js` contains no framework `import`/`require`.
- Document (in the sp7 spec note hand-off, not here) that the save handler is untouched by design.

**Out of scope (do NOT do these):**
- Any production-code change. **This sub-phase adds zero machinery** — that is the designed outcome
  (decision #1), not an omission. If you find yourself editing `api_artifacts.save_artifact` or a
  service, STOP — the lazy model means the save path is deliberately inert.
- The spec update itself (sp7) and the e2e harness (sp7).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `tests/test_fr007_readonly_guard.py` | Modify | Phase 1 read-only guard exists |
| `tests/test_no_frontend_framework.py` | Create | Does not exist |

## Detailed Steps

### Step 6.1: Extend the FR-007 read-only guard
For the frozen fixture goal, capture the `.collab.md` bytes, then exercise each Phase 4 operation and
re-assert byte-identity after each:
- `create_comment` / `resolve` / `reopen` / `relocate` / `orphan` (comment CRUD).
- `create_next()` (snapshots INTO the DB; reads the file, never writes it).
- `render_diff()` (pure; served fresh, never persisted).
After all operations: the `.collab.md` SHA / bytes are unchanged, and `bin/cast-spec-checker
<fixture>` exits 0. The HTML render may regenerate (it's the disposable artifact) — assert only the
**canonical `.collab.md`** is immutable.

### Step 6.2: The no-frontend-framework pin
```python
# tests/test_no_frontend_framework.py
from pathlib import Path

def test_no_package_json_anywhere_under_cast_server():
    root = Path(__file__).resolve().parents[1]          # cast-server/
    assert list(root.rglob("package.json")) == []

def test_comment_js_imports_no_framework():
    js = (Path(__file__).resolve().parents[1]
          / "cast_server/static/requirements_comments.js").read_text()
    banned = ("import react", "from 'react", 'from "react', "require('react",
              "vue", "angular", "svelte", "annotator", "rangy")
    low = js.lower()
    for b in banned:
        assert b not in low, f"framework/library reference found: {b}"
```
Adjust the banned list to the real annotation libraries the plan rules out (no React, no annotation
library). Keep it a source-scan — htmx (vanilla, already vendored) is allowed.

## Verification

### Automated Tests (permanent)
- `tests/test_fr007_readonly_guard.py` (extended) — green: all Phase 4 ops leave `.collab.md`
  byte-identical; checker exit 0.
- `tests/test_no_frontend_framework.py` — green: no `package.json`; JS clean.

### Validation Scripts (temporary)
```bash
cd cast-server && python -m pytest tests/test_fr007_readonly_guard.py tests/test_no_frontend_framework.py -q
find cast-server -name package.json    # must print nothing
bin/cast-spec-checker tests/fixtures/refine_requirements_v2/refined_requirements.collab.md; echo "exit=$?"
```

### Manual Checks
- Confirm NO production file was modified in this sub-phase (`git diff --name-only` shows only the
  two test files).

### Success Criteria
- [ ] FR-007 guard extended over comment CRUD + `create_next` + `render_diff`; `.collab.md` bytes immutable.
- [ ] `bin/cast-spec-checker` exits 0 in the guard test.
- [ ] `test_no_frontend_framework.py` passes; `find cast-server -name package.json` is empty.
- [ ] Zero production-code changes in this sub-phase.

## Execution Notes

- The whole point of WP-F is the **absence** of save-path machinery. The review value is proving the
  "re-anchor on save" promise is fulfilled lazily (save → next render shows displaced in the tray →
  next `create_next` dispatches the subagent) with the save handler untouched.
- If `package.json` ever appears (e.g. a tooling accident), this pin is the tripwire — keep it strict.

**Spec-linked files:** none modified (tests only). The "lazy + surfaced tray" reinterpretation of
plan.collab.md's "re-anchor on save" wording is recorded in the spec by sp7.
