# sp4 Serve + Regenerate (WP-E) — Output

**Status:** ✅ Complete. All Detailed Steps executed, all verification run, every success criterion met.

## What was built

### Step 4.1 — `rerender_requirements_html()`
`cast-server/cast_server/services/requirements_render_service.py` (new). Flat function,
house DB pattern (`db_path: Path | None = None` injectable; `goals_dir` override; mirrors
`goal_service`/`task_service`). Signature adopted **verbatim** from the Naming Contract:

```python
rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None) -> Path | None
```

Logic:
1. Resolve the goal dir (routed `folder_path` wins over `goals_dir/slug`, like `task_service`),
   then `refined_requirements.collab.md`. Missing → `None`.
2. `parsed = parse_requirements_file(path)`; `h = content_hash(parsed.source_text)`.
3. **Lazy staleness:** if `refined_requirements.html` exists and its embedded
   `<!-- source-hash: H -->` equals `h`, return the path **without rewriting** (byte-identical no-op).
4. Else render via the pure `render_requirements(parsed, version=...)` (version pulled from
   `requirement_version_service.get_current()`), then **atomically** write (tmp file in the
   same dir + `os.replace`) with the `<!-- AUTO-GENERATED: ... -->` header + `<!-- source-hash: H -->`.

The service owns ALL file/DB I/O; the renderer stays pure. The `.collab.md` is read-only (FR-007).

### Step 4.2 — `GET /goals/{slug}/render`
Added to `routes/pages.py` (cloned from `preso_review`). Validates the slug via
`goal_service.get_goal()` first → **404** on unknown (this is also the path-traversal kill —
resolving Phase 1's forward-flag; `preso_review` was intentionally **not** touched). Known goal →
`rerender_requirements_html()` (self-healing regen on view) → `HTMLResponse`. No requirements →
**200** prompt-to-begin ("No requirements yet — run requirements refinement to begin"). Render
exception → **500** plain message (no stack trace; any existing `.html` left intact).

### Step 4.3 — "View render" link
One line added to `templates/pages/goal_detail.html` near the status actions:
`<a href="/goals/{{ goal.slug }}/render">View requirements render</a>`. No new UI surface.

## Files
| File | Action |
|---|---|
| `cast-server/cast_server/services/requirements_render_service.py` | Created |
| `cast-server/cast_server/routes/pages.py` | Modified (import + `requirements_render` route) |
| `cast-server/cast_server/templates/pages/goal_detail.html` | Modified (one link line) |
| `cast-server/tests/test_render_route_and_service.py` | Created (12 tests) |

## Verification

**Automated** — `pytest tests/test_render_route_and_service.py` → **12 passed**. Covers:
missing→None, AUTO-GENERATED+source-hash header, fresh-hash no-op (bytes + mtime_ns stable),
stale-hash regen (new source-hash), `.collab.md` never written, atomic write (spied `os.replace`
called once, no `.tmp` debris), unknown-slug 404, path-traversal 404, 200 serve, prompt-to-begin,
500-on-render-exception (no leak), and the goal-page link. Broader suite (`-k render/route/pages/
requirements`) → **134 passed, 0 failures**.

**Live** (server on :8005, port freed first): unknown slug → `404`; `..%2F..%2Fetc%2Fpasswd` → `404`
(no `root:` leak); `refine-requirements-v2` → `200` with AUTO-GENERATED header + source-hash;
generated `refined_requirements.html` written; second view = byte-identical no-op (md5 + mtime stable);
goal page shows the "View requirements render" link. (The validation `refined_requirements.html` was
removed afterward — it self-heals on next view.)

## Success criteria — all met
- [x] Lazy regen on stale, no-op on fresh, `None` on missing; atomic write; AUTO-GENERATED + source-hash header.
- [x] `.collab.md` never written (route-level guard green).
- [x] Route: 200+regen on stale; no-op on fresh; 200 prompt-to-begin on no/stub; **404 on unknown (traversal killed)**; 500-plain on render exception (existing `.html` intact).
- [x] "View render" link present on the goal page.
- [x] `pytest tests/test_render_route_and_service.py` passes (12/12).

## Notes for dependents (sp5a / sp5b)
- The generated artifact contract is fixed: line 1 = `<!-- AUTO-GENERATED: Read-only render of
  refined_requirements.collab.md. Do not edit. -->`, line 2 = `<!-- source-hash: <hex> -->`, then the
  pure render body. sp5b's FR-007 guard / spec should document this exact 2-line prefix.
- The render body beneath the prefix is exactly `RenderResult.html` from sp1–sp3 — unchanged.
- `preso_review` still builds a path from the raw slug without DB validation (same exposure class) —
  a flagged follow-up **outside** this phase; not fixed here per the plan's instruction.
