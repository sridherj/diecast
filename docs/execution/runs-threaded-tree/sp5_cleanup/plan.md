# Sub-phase 5: Cleanup — Delete Legacy Fragments / Endpoints / Unused CSS

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp3 AND sp4 are committed (the new path — macro + fragment + status_cells endpoint + JS — is fully in place and green on dev).

## Objective

Remove dead code now that the new threaded path ships everything the old flat path did. Three deletions, each grep-gated:

1. The two legacy template fragments: `run_row.html`, `run_children.html`.
2. The two now-superseded API endpoints: `GET /api/agents/runs/{id}/children`, `GET /api/agents/runs/{id}/row`.
3. Legacy CSS classes no longer referenced anywhere: `.run-row*`, `.run-children-container`, `.child-run`, `.child-indent`.

Each deletion is preceded by a `grep -rn` that confirms zero live references. If a reference is found, halt and surface it — do not "clean up" the reference inline; the right call is to investigate why something still depends on the old path.

## Dependencies

- **Requires completed:** sp3 AND sp4. The new path must be fully observable on the running dev server (HTMX poll target works; expand/collapse JS works) before deletion.
- **Assumed codebase state:** Pre-sp5 tree at HEAD + sp1 + sp2 + sp3 + sp4 commits.

## Scope

**In scope:**
- DELETE `cast-server/cast_server/templates/fragments/run_row.html` (after grep confirms zero refs).
- DELETE `cast-server/cast_server/templates/fragments/run_children.html` (after grep confirms zero refs).
- REMOVE `GET /api/agents/runs/{run_id}/children` from `cast-server/cast_server/routes/api_agents.py` (line 211 in pre-sp1 numbering; verify with grep).
- REMOVE `GET /api/agents/runs/{run_id}/row` from `cast-server/cast_server/routes/api_agents.py` (line 234 in pre-sp1 numbering; verify with grep).
- REMOVE legacy CSS classes from `cast-server/cast_server/static/style.css` (after grep confirms zero refs in templates). Specifically: `.run-row`, `.run-row-header`, `.run-row-content`, `.run-children-container`, `.child-run`, `.child-indent`. Other `.run-*` classes added by sp2 stay.

**Out of scope (do NOT do these):**
- Any change to `services/agent_service.py` — `get_all_runs` is still used by other callers (verify via grep, but do NOT delete it unless the grep returns zero non-test references).
- The `cast-ui-test-runs` agent prompt — sp6 owns that.
- Spec capture — sp7.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/templates/fragments/run_row.html` | Delete | Pre-sp5 file in tree. |
| `cast-server/cast_server/templates/fragments/run_children.html` | Delete | Pre-sp5 file in tree. |
| `cast-server/cast_server/routes/api_agents.py` | Modify (remove 2 routes) | Has both legacy routes. |
| `cast-server/cast_server/static/style.css` | Modify (remove legacy class blocks) | Has both threaded styles (sp2) and legacy `.run-row*`. |

## Detailed Steps

### Step 5.1: Grep for refs to the two template fragments

```bash
grep -rn 'run_row\|run_children' \
  cast-server/cast_server/templates/ \
  cast-server/cast_server/routes/ \
  cast-server/cast_server/services/ \
  cast-server/cast_server/main.py \
  cast-server/cast_server/app.py 2>/dev/null

# Also catch any tests that read these template paths:
grep -rn 'run_row\|run_children' cast-server/tests/ 2>/dev/null
```

**Expected output**: only matches inside the two files themselves, plus possibly comments/docstrings.

If any non-self reference exists:
- Halt deletion.
- Report the reference to the user. Investigate WHY something still uses the old fragment.
- Do not "fix" the reference by inlining the new macro — that's an architecture decision that needs explicit alignment.

### Step 5.2: Delete the two template fragments

```bash
git rm cast-server/cast_server/templates/fragments/run_row.html
git rm cast-server/cast_server/templates/fragments/run_children.html
```

(`git rm` over plain `rm` so the deletions stage cleanly.)

### Step 5.3: Grep for refs to the two API endpoints

```bash
# Endpoint paths in the codebase:
grep -rn '/runs/.*/children\|/runs/.*/row' \
  cast-server/cast_server/ \
  cast-server/tests/ \
  skills/claude-code/ \
  agents/ 2>/dev/null

# Also any direct route function names — verify via the route module:
grep -n 'def.*children\|def.*row' cast-server/cast_server/routes/api_agents.py
```

Expected matches:
- Only the route function definitions in `api_agents.py` themselves.
- Possibly the `_old` API documentation in some skill markdown — surface those to the user before deletion.

If a test or skill still calls these URLs, surface to user. The new test path uses `/api/agents/runs/{id}/status_cells`; older agent prompts may need updating (sp6 covers `cast-ui-test-runs` specifically; if a different agent references the URL, list it for the user).

### Step 5.4: Remove the two endpoints

Edit `cast-server/cast_server/routes/api_agents.py`:

- Remove the `@router.get("/runs/{run_id}/children", ...)` decorator + function body.
- Remove the `@router.get("/runs/{run_id}/row", ...)` decorator + function body.
- If the removed functions imported helpers ONLY they used (e.g., a `_render_row_partial` or similar), remove the helper too — but only if grep confirms zero other callers.

After the edit, restart the server. Confirm:

```bash
curl -sw '%{http_code}\n' -o /dev/null http://127.0.0.1:8000/api/agents/runs/anything/children
# Expect: 404

curl -sw '%{http_code}\n' -o /dev/null http://127.0.0.1:8000/api/agents/runs/anything/row
# Expect: 404
```

### Step 5.5: Grep for legacy CSS class refs

```bash
grep -rn 'run-row\|run-children-container\|child-run\|child-indent' \
  cast-server/cast_server/templates/ \
  cast-server/cast_server/static/ 2>/dev/null
```

Expected: only matches inside `style.css` itself (the rule blocks).

If a template still references the class, halt — sp2 should have replaced it with the new macro's classes. Investigate before deleting.

### Step 5.6: Remove legacy CSS rule blocks

In `cast-server/cast_server/static/style.css`, locate the rule blocks for `.run-row`, `.run-row-*` (header/content/etc.), `.run-children-container`, `.child-run`, `.child-indent`. Delete the rule blocks. Keep all blocks in the `/* === threaded /runs (sp2) === */` section. Leave any unrelated `.run-*` classes (e.g. `.run-summary-cards`, `.runs-pagination`) alone — they're still used.

### Step 5.7: Final regression check

```bash
# Full grep — confirm no rotting refs to deleted assets remain:
grep -rn 'run_row\|run_children\|/runs/.*/children\|/runs/.*/row\|run-row\|run-children-container\|child-run\|child-indent' \
  cast-server/cast_server/ \
  cast-server/tests/ 2>/dev/null
# Expect: no output (or only the .git directory if a sparse grep slipped in).
```

Run the full test suite:

```bash
uv run pytest cast-server/tests/
# Expect: green; no skipped/xfail regressions.
```

Restart the server, visit `/runs`, click pagination, expand rows, click `⧉`. Everything must still work.

## Verification

### Automated Tests (permanent)
- Full suite `uv run pytest` green.
- No new tests this sub-phase.

### Validation Scripts (temporary)
- All grep commands in steps 5.1, 5.3, 5.5, and 5.7 return zero non-self matches (after deletions).
- Both legacy endpoints return 404.

### Manual Checks
- Page load + pagination + expand/collapse + clipboard copy + HTMX poll all still work after deletion.
- DevTools Console shows no 404s (e.g., a stale fetch from a cached page); reload to clear.

### Success Criteria
- [ ] `run_row.html` and `run_children.html` no longer exist.
- [ ] `/runs/{id}/children` and `/runs/{id}/row` return 404.
- [ ] Legacy CSS classes removed from `style.css`.
- [ ] No live references to deleted assets anywhere in the codebase.
- [ ] Full test suite green.
- [ ] `/runs` page still functions correctly post-deletion.

## Execution Notes

- The grep-gate is the safety net. **If grep finds a live reference, do NOT proceed with deletion.** Surface to the user and ask whether the reference should be migrated or whether deletion should wait.
- Skill markdown (`skills/claude-code/cast-runs/SKILL.md` if present, or other agent prompts) may include curl examples calling the old endpoints. These are user-facing docs — sp6 will update the `cast-ui-test-runs` agent specifically; for other docs, surface to user.
- A common false-positive in grep: comments. e.g., `# replaces run_row.html` in a sp2 commit message context. Inspect each match; comments may be deletable inline as part of the same commit.
- `get_all_runs` is intentionally not removed in this sub-phase. Run a final grep:

  ```bash
  grep -rn 'get_all_runs' cast-server/cast_server/ cast-server/tests/
  ```

  If grep returns ONLY the function definition + the bottom of `services/agent_service.py`, surface to user — `get_all_runs` could plausibly also be deleted. Otherwise leave it.

**Spec-linked files:** None directly. The deletion of the legacy endpoints is observable by external skills; the spec sp7 captures the new contract, which implicitly makes the old contract obsolete.
