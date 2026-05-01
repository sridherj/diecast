# Sub-phase 7: Spec Capture via `/cast-update-spec` + Registry + Cross-Link + Spec-Checker

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp6 is committed (UI test agent green; `/cast-pytest-best-practices` findings applied; full suite green).

## Objective

Lock the threaded `/runs` contract as a spec so the next agent that touches the page has a source of truth — not just a plan archive. Run `/cast-update-spec create cast-runs-screen` to author `docs/specs/cast-runs-screen.collab.md`, verify the registry row was added, cross-link from `cast-ui-testing.collab.md`'s "Linked files", then run `/cast-spec-checker` to validate against `templates/cast-spec.template.md`.

The spec is captured AFTER UI tests are green (sp6) so it records actually-shipped behavior, not aspirational plan copy.

## Dependencies

- **Requires completed:** sp6 (UI tests green, pytest-best-practices findings applied).
- **Assumed codebase state:** Pre-sp7 tree at HEAD + sp1 + sp2 + sp3 + sp4 + sp5 + sp6 commits. The `/runs` page renders the threaded layout; the spec does not exist yet.

## Scope

**In scope:**
- INVOKE `Delegate: /cast-update-spec create cast-runs-screen`. The skill produces a diff for `docs/specs/cast-runs-screen.collab.md`. Review and approve.
- VERIFY `docs/specs/_registry.md` has a new row for `cast-runs-screen.collab.md`. The skill adds it automatically; if missing, add manually.
- UPDATE `docs/specs/cast-ui-testing.collab.md` — add `cast-runs-screen.collab.md` to its "Linked files" section so the harness spec cross-references the per-screen contract.
- INVOKE `Delegate: /cast-spec-checker docs/specs/cast-runs-screen.collab.md`. Fix any lint findings before merging.

**Out of scope (do NOT do these):**
- Any code edit. This sub-phase is documentation-only.
- Creating a spec for any other screen (sibling specs are out of scope).
- Editing `docs/specs/cast-delegation-contract.collab.md` — this redesign does not change delegation behavior.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `docs/specs/cast-runs-screen.collab.md` | Create (via `/cast-update-spec`) | Does not exist. |
| `docs/specs/_registry.md` | Modify | No row for `cast-runs-screen`. |
| `docs/specs/cast-ui-testing.collab.md` | Modify | "Linked files" section does not reference `cast-runs-screen.collab.md`. |

## Detailed Steps

### Step 7.1: Read the spec template and existing siblings

Before invoking the skill, skim:

- `templates/cast-spec.template.md` — the structural canon every spec follows.
- `docs/specs/cast-ui-testing.collab.md` — sibling spec that lives near this one; mirror its tone and section ordering.
- `docs/specs/cast-delegation-contract.collab.md` — another sibling, particularly for "Behavior contract" framing.

This ensures the user's eventual review of the skill's diff is informed.

### Step 7.2: Invoke `/cast-update-spec create cast-runs-screen`

```
Delegate: /cast-update-spec create cast-runs-screen
```

The skill expects scope context. Provide:

- **Intent (one paragraph):**
  > "The `/runs` page renders a threaded tree of agent runs, eagerly loaded per page, with rollup signals on parents, ctx-aware highlighting on children, and HTMX polling that does not disturb expand state."

- **Linked files** (the canonical "code that implements this contract"):
  - `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`
  - `cast-server/cast_server/services/agent_service.py`
  - `cast-server/cast_server/routes/api_agents.py` (added by sp5: `/jobs/{id}?include=children` extension; removed `/runs/{id}/children` + `/runs/{id}/row`; recheck/cancel handlers now render via macro)
  - `cast-server/cast_server/templates/macros/run_node.html`
  - `cast-server/cast_server/templates/fragments/run_status_cells.html`
  - `cast-server/cast_server/static/style.css`
  - `cast-server/docs/runs-api.md` (HTTP API reference — must reflect the removed endpoints + the new `?include=children` parameter)
  - `cast-server/tests/ui/agents/cast-ui-test-runs/`

- **User Stories** (locked by the plan's "Spec capture (step 7)" section — preserve verbatim):

  - **US1: Multi-level tree visible without expansion** — a 4-level orchestration renders all four levels on initial load; the user can scan the whole structure without clicking anything.
  - **US2: Failure surfaces from any depth** — a failed grandchild causes the L1 to show `⚠ N failed` rollup, red `has-failure` group border, and the failed-status filter matches the L1.
  - **US3: Rework loops are recognizable** — consecutive same-`(agent_name, task_id)` siblings render `↻ rework #N` tags; their count propagates to the L1 rollup.
  - **US4: Context pressure is scannable** — ctx pill threshold (`<40` green, `40–70` amber, `70+` red) at status-pill prominence; child agent name color tracks the same threshold.
  - **US5: Resume is one click** — every row's line 2 has `⧉` that copies the run's resume command without expanding the row.
  - **US6: Polling preserves user state** — running rows update their status cells every 3s while leaving expand state, thread rail, and group container untouched.
  - **US7: Tree is bounded** — depth cap at 10 prevents runaway-loop trees from DOS-ing the page; truncated trees surface a server-side warning.
  - **US8: Action buttons return macro-shaped fragments** — Recheck and Cancel HTMX handlers (`POST /api/agents/jobs/{id}/recheck`, `POST /api/agents/runs/{id}/cancel`) render via the `run_node` macro and return a `.run-group` fragment, matching the macro's `hx-target="closest .run-group"`. No handler called from a macro-rendered button may return a `.run-row` fragment — that pattern is gone.
  - **US9: Sub-tree fetch is canonical at `/jobs/{id}?include=children`** — agents and external clients that need a single run with its descendant tree call `GET /api/agents/jobs/{id}?include=children`. The legacy `GET /api/agents/runs/{id}/children` (HTML lazy-load) is REMOVED in this release; one-time migration of all known callers (cast-preso-check-coordinator tests, runs-api docs, agent_service prompt-template listing) was completed in sp5. Likewise `GET /api/agents/runs/{id}/row` is REMOVED — its replacement for HTMX poll is `GET /api/agents/runs/{id}/status_cells` (added in sp3).

- **Behavior contract** (locked):
  - `get_runs_tree(...)` return shape (per the function docstring; copy from `_shared_context.md` § "`get_runs_tree(...)` return shape").
  - Severity ordering for `status_rollup`: `failed > stuck > rate_limited > running > pending > scheduled > completed`.
  - Ctx thresholds: `<40 → low`, `40–70 → mid`, `70+ → high`.
  - Rework detection rule: consecutive siblings under the same parent with the same `(agent_name, task_id)`; index starts at 2 for the second instance; counts propagate to all ancestors.
  - HTMX swap-target rule: `hx-*` attributes live on `.run-status-cells`, NEVER on the outer `.run-node`. Outer node carries expand state and must survive polls.
  - Collapse persistence key format: `localStorage["runs:expanded:<run_id>"] = "1"` (presence = expanded; deleted = collapsed).
  - Depth cap: 10 levels; deeper rows are silently dropped + server-warned.
  - **HTMX response-shape rule (added by sp5):** any handler whose only HTMX caller is a `run_node`-rendered button MUST return a `.run-group` fragment via the `run_node` macro. Returning a `.run-row` fragment is a bug — that legacy shape no longer exists in the templates after sp5.
  - **Canonical sub-tree fetch URL (added by sp5):** `GET /api/agents/jobs/{run_id}?include=children`. Returns a single run augmented with a `children` list shaped by `get_run_with_rollups` (depth-capped, rollups attached). When `?include=children` is omitted, the response is the existing single-run shape — backward-compatible with all callers that don't need descendants.
  - **Removed endpoints (release-note):** `GET /api/agents/runs/{id}/children` and `GET /api/agents/runs/{id}/row` are GONE. The first is replaced by `/jobs/{id}?include=children` (canonical sub-tree); the second by `/api/agents/runs/{id}/status_cells` (HTMX poll target). Spec must list these under a "Removed in this release" section so future readers can find the migration path.

- **Out of scope** (mirror the plan's "Out of scope"):
  - Schema columns to cache rollups (deferred).
  - `MAX_DESCENDANTS_PER_GROUP` width cap (deferred).
  - Virtualization / "show 7 more" affordance.
  - Search/filter inside a single group.
  - L1 ctx-pill agent-name tinting (children-only for now).
  - Resume-via-action (the `⧉` copies the command; running it stays manual).
  - `bin/lint-anonymization` integration.

- **Verification**: reference `cast-server/tests/test_runs_tree.py`, `cast-server/tests/test_runs_template.py`, and the `cast-ui-test-runs` agent. Spec doesn't repeat the test list; it cites where the live coverage lives.

The skill produces a diff. Review:
- Tone matches sibling specs (`cast-ui-testing.collab.md`).
- Frontmatter has `name: cast-runs-screen`, `version: 1`, `status: Draft`, `date` set to today.
- All seven user stories appear and match the plan's wording.
- Behavior contract bullets are present and ordered.

If the diff looks right, approve. If something's off, redirect the skill (e.g., "the rework rule should be 'consecutive siblings', not 'any siblings' — please tighten US3").

### Step 7.3: Verify / add the registry row

Read `docs/specs/_registry.md`. Look for a row matching `cast-runs-screen`. The expected shape (mirror neighboring rows):

```
| `cast-runs-screen.collab.md` | cast-runs-screen | cast-server | Threaded /runs page contract: tree fetch, rollups, rework, ctx thresholds, HTMX poll-safety, collapse persistence, depth cap. Linked plan: `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`. | Draft | 1 |
```

If the skill added this automatically: confirm. If not: add it manually using the same column order as neighboring rows. Run a quick sanity-grep to make sure the registry has no duplicate row.

```bash
grep -n 'cast-runs-screen' docs/specs/_registry.md
# Expect: exactly one row.
```

### Step 7.4: Add cross-link from `cast-ui-testing.collab.md`

Open `docs/specs/cast-ui-testing.collab.md`. Find the "Linked files" section (or equivalent — the section name is canonical per the spec template). Append:

```
- `docs/specs/cast-runs-screen.collab.md` — per-screen contract for the threaded /runs page; the harness asserts US1–US7 of this spec via `cast-server/tests/ui/agents/cast-ui-test-runs/`.
```

Bump the `version` field in the frontmatter (the convention is auto-bumped by `/cast-update-spec`, but that skill's scope is `cast-runs-screen`, not `cast-ui-testing` — so the bump for ui-testing is manual). Update the `date` line too.

### Step 7.5: Run `/cast-spec-checker`

```
Delegate: /cast-spec-checker docs/specs/cast-runs-screen.collab.md
```

The checker validates the spec against `templates/cast-spec.template.md`. Possible findings:
- Missing required section.
- Frontmatter field out of canonical order.
- Linked file path doesn't exist on disk.
- "User Stories" section uses a different heading level than the template.

For each finding, fix in place. Re-run the checker until it returns clean.

Optional: run the checker over `cast-ui-testing.collab.md` too — the cross-link addition shouldn't break it, but it's cheap to confirm.

```
Delegate: /cast-spec-checker docs/specs/cast-ui-testing.collab.md
```

### Step 7.6: Final commit

Stage the four changes:

- `docs/specs/cast-runs-screen.collab.md` (new)
- `docs/specs/_registry.md` (modified)
- `docs/specs/cast-ui-testing.collab.md` (modified)
- Any spec-checker fixes that landed in the new spec

Commit message:

```
docs: capture cast-runs-screen spec; cross-link from cast-ui-testing

Locks the threaded /runs contract as a per-screen spec covering tree
fetch shape, rollup semantics, rework detection rules, ctx thresholds,
HTMX poll-safety, collapse persistence, and depth cap. References
live coverage in test_runs_tree.py, test_runs_template.py, and the
cast-ui-test-runs harness agent.
```

## Verification

### Automated Tests (permanent)
- No new tests this sub-phase. Spec correctness is enforced by `/cast-spec-checker`, not pytest.
- Full suite `uv run pytest` — green (no regressions; this is documentation-only).

### Validation Scripts (temporary)

```bash
# 1. Spec exists with correct frontmatter:
head -20 docs/specs/cast-runs-screen.collab.md
# Expect: frontmatter with name/version/status/date/linked_files.

# 2. Registry row present and unique:
grep -n 'cast-runs-screen' docs/specs/_registry.md
# Expect: exactly one row.

# 3. Cross-link in cast-ui-testing:
grep -n 'cast-runs-screen.collab.md' docs/specs/cast-ui-testing.collab.md
# Expect: at least one hit (in "Linked files").

# 4. Spec-checker is clean:
# (Re-run /cast-spec-checker; expect "no findings" or equivalent.)
```

### Manual Checks
- Open `docs/specs/cast-runs-screen.collab.md` in a markdown viewer. Confirm headings render, code blocks render, lists render.
- Click through every "Linked files" path and confirm each file exists on disk at the listed location.

### Success Criteria
- [ ] `docs/specs/cast-runs-screen.collab.md` exists with all 6 required sections (Intent, Linked files, User Stories **US1–US9**, Behavior contract, Out of scope, Verification).
- [ ] Spec includes a **"Removed in this release"** subsection listing `/api/agents/runs/{id}/children` and `/api/agents/runs/{id}/row` with their replacement URLs (`/jobs/{id}?include=children` and `/runs/{id}/status_cells` respectively).
- [ ] Spec's Behavior contract includes the HTMX response-shape rule (handlers wired to macro buttons return `.run-group` fragments).
- [ ] `docs/specs/_registry.md` has the new row.
- [ ] `docs/specs/cast-ui-testing.collab.md` cross-references the new spec.
- [ ] `/cast-spec-checker` returns clean for the new spec.
- [ ] Full test suite green (no regressions from documentation changes).

## Execution Notes

- This sub-phase produces NO code. If you find yourself editing `cast-server/`, stop — you've drifted into another sub-phase's scope.
- The user stories (US1–US7) are locked. If `/cast-update-spec` proposes alternative wording that meaningfully changes meaning, reject and redirect.
- The plan's Decisions block (470 lines) is NOT copied into the spec verbatim. The spec is the contract; the plan is the rationale archive. The spec links the plan via `Linked files`.
- Bumping `cast-ui-testing.collab.md`'s version: small documentation amendment is a minor bump (e.g., `1 → 2`). The spec's date should reflect today's date (per `_shared_context.md` `currentDate: 2026-05-01`).
- If `/cast-spec-checker` does not exist as a skill at the time of execution, fall back to a manual checklist read of `templates/cast-spec.template.md`. The skill is referenced in the plan but the harness for it may not yet be wired — surface to user if missing.

**Spec-linked files:** `docs/specs/cast-ui-testing.collab.md` (modified). Confirm the cross-link addition does not invalidate any of cast-ui-testing's existing SAV claims — it's an additive reference, not a behavioral change.
