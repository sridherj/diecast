# Sub-phase 4: Serve + Regenerate (clone the preso loop) — WP-E

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.

## Objective
Wire the pure renderer into the running app: a flat-function service that lazily regenerates
`goals/{slug}/refined_requirements.html` only when the source hash changes (atomic write,
AUTO-GENERATED header, never touches the canonical `.collab.md`), and a `GET /goals/{slug}/render`
page route cloned from `preso_review` (slug validated against the goals DB → 404 on unknown, which
also kills path traversal). Plus a one-line "View render" link on the goal page.

## Dependencies
- **Requires completed:** sp3 (the renderer is feature-complete: Goal Card + disclosure + Directional).
- **Assumed codebase state:** `render_requirements()` returns a finished `RenderResult`; Phase 1
  `content_hash` + parser are importable; `goal_service.get_goal()` exists.

## Scope
**In scope:**
- `services/requirements_render_service.py` → `rerender_requirements_html(goal_slug, *,
  goals_dir=None, db_path=None) -> Path | None` (flat function, house DB pattern): read
  `goals/{slug}/refined_requirements.collab.md` (missing → `None`); parse; **lazy staleness check**
  against the embedded `source-hash`; if stale, render + **atomically** write (tmp + `os.replace`)
  with the AUTO-GENERATED header + `source-hash` comment. Reads the `.collab.md` only — never writes
  it (FR-007).
- `GET /goals/{slug}/render` in `routes/pages.py` (cloned from `preso_review`): validate slug via
  `goal_service.get_goal()` → 404 on unknown; call `rerender_requirements_html()` (self-healing
  regen on view) → `HTMLResponse(file text)`; goal exists but no/stub requirements → 200
  prompt-to-begin (a legitimate product state, not an error).
- A one-line "View render" link on the goal page near the requirements artifact (SC-003).
- Route/service tests (`test_render_route_and_service.py`).

**Out of scope (do NOT do these):**
- The renderer body / Goal Card / disclosure (sp1–sp3 — done).
- The zero-click extractor, checker agent, goldens, eval harness (sp5a).
- The new spec doc + FR-007 guard extension (sp5b).
- Any write to the canonical `.collab.md` (FR-007 — forbidden; this phase never performs the
  artifact-write the delegation contract constrains).
- New UI surfaces beyond the single link line.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/requirements_render_service.py` | Create | Does not exist |
| `cast-server/cast_server/routes/pages.py` | Modify | Has `preso_review` (≈299–307) to clone; add `GET /goals/{slug}/render` |
| goal-page template (the goal detail page rendering the requirements artifact) | Modify | Add a one-line "View render" link |
| `cast-server/tests/test_render_route_and_service.py` | Create | Route + service behaviour |

## Detailed Steps

### Step 4.1: `rerender_requirements_html()`
Flat function, house DB pattern (`db_path: Path | None = None` injectable + `get_connection`,
mirroring `goal_service.py`/`task_service.py`). Logic:
1. Resolve `goals/{slug}/refined_requirements.collab.md` (honour `goals_dir` override). Missing →
   return `None`.
2. `parsed = parse_requirements_file(path)`; `h = content_hash(parsed.source_text)`.
3. **Lazy staleness:** if `refined_requirements.html` exists and its embedded `<!-- source-hash: H -->`
   equals `h`, return the path **without rewriting** (byte-identical, no-op).
4. Else `result = render_requirements(parsed, version=requirement_version_service.get_current(...))`;
   write atomically (tmp file + `os.replace`) to `goals/{slug}/refined_requirements.html` with the
   `<!-- AUTO-GENERATED: Read-only render of refined_requirements.collab.md. Do not edit. -->`
   header (mirror `_rerender_tasks_md`, `task_service.py:~389`) + the `<!-- source-hash: H -->`
   comment. Return the path.

The service owns ALL file/DB I/O — the renderer stays pure.

### Step 4.2: `GET /goals/{slug}/render`
Clone `preso_review` (`pages.py` ≈299–307). Validate the slug via `goal_service.get_goal()` first —
unknown goal → **404** (this is also the path-traversal kill, resolving Phase 1's forward-flag).
Goal exists → `rerender_requirements_html()` → `HTMLResponse(path.read_text())`. Goal exists but
no/stub requirements → 200 with the prompt-to-begin render. Render exception on GET → 500 with a
plain message, existing `.html` left intact (never a stack trace to the user).

### Step 4.3: "View render" link
Add one template line on the goal page near the requirements artifact linking to
`/goals/{slug}/render`. No new UI surface.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_render_route_and_service.py`
- `test_stale_hash_regenerates`: change the `.collab.md` → `GET /goals/{slug}/render` returns 200 and
  the `.html` is regenerated (new `source-hash`).
- `test_fresh_hash_is_noop`: unchanged source → the `.html` is **byte-identical** and not rewritten
  (assert mtime/bytes unchanged).
- `test_missing_or_stub_requirements_prompt_to_begin`: goal exists, no/stub requirements → 200
  prompt-to-begin (not an error).
- `test_unknown_slug_404`: unknown slug → 404 (also covers path-traversal attempts like
  `../../etc/passwd`).
- `test_collab_md_never_written`: `.collab.md` bytes identical before/after a render request
  (FR-007 — full guard is sp5b, this is the route-level check).
- `test_atomic_write`: simulate/inspect that the write path uses tmp + `os.replace` (no truncated
  artifact on crash).

### Validation Scripts (temporary)
- Start the server (free the port first — `lsof -ti:8005 | xargs -r kill`), `curl -s
  http://localhost:8005/goals/<known-slug>/render | head`; `curl -s -o /dev/null -w '%{http_code}'
  http://localhost:8005/goals/nonexistent/render` → `404`.

### Manual Checks
- Load `/goals/{slug}/render` in a browser; confirm the Goal Card reads zero-click and the "View
  render" link appears on the goal page.

### Success Criteria
- [ ] `rerender_requirements_html()` lazily regenerates on stale hash, no-ops on fresh, returns
      `None` on missing source; atomic write; AUTO-GENERATED + `source-hash` header present.
- [ ] `.collab.md` never written (route-level check green).
- [ ] `GET /goals/{slug}/render`: 200 + regen on stale; no-op on fresh; 200 prompt-to-begin on
      no/stub; **404 on unknown slug** (path-traversal killed); 500-with-plain-message on render
      exception (existing `.html` intact).
- [ ] "View render" link present on the goal page.
- [ ] `cd cast-server && pytest tests/test_render_route_and_service.py` passes.

## Execution Notes
- **Free port 8005 before starting the server** for manual checks (phantom-bug risk otherwise).
- The server writing `.html` is the same write class as `tasks.md`/`goal.yaml` (a generated render),
  NOT the Phase 5 artifact-write the delegation contract constrains — sp5b's spec records this. Do
  not route this write through any artifact-write guard meant for `.collab.md`.
- The existing `/preso/review/{goal_slug}` route builds a path from the raw slug **without** DB
  validation — same exposure class; that is a flagged follow-up **outside** this phase. Do the right
  thing *here* (validate via `get_goal()` first); do not "fix" `preso_review` in this sub-phase.

**Spec-linked files:** `routes/pages.py` behaviour is documented by the **new** spec sp5b creates
(`cast-requirements-render.collab.md`). No existing spec's SAV behaviours are altered here; the
generated-render classification is recorded by sp5b, not by silently extending
`cast-init-conventions.collab.md`.
