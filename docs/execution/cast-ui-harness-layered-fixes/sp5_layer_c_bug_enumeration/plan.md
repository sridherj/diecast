# Sub-phase 5: Layer C — Bug enumeration into Diecast tasks (FR-005)

> **Pre-requisite:** Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` before starting.

## Objective

After Layers A and B are merged, the harness's remaining red list IS the Layer C
backlog — genuine cast-server product bugs surfaced by an honest test. File one
Diecast task per bug under the existing `comprehensive-ui-test` goal, with enough
detail (assertion name, manual repro recipe, root-cause hypothesis) for the future
fixer to start without re-investigating.

This sub-phase delivers FR-005 and SC-005 of the layered-fixes plan. **Bugs are
enumerated here; bugs are NOT fixed here.** Product fixes happen downstream.

## Dependencies
- **Requires completed:** sp1, sp2, sp3, sp4. Layer A and Layer B MUST both be in
  place — otherwise the red list still contains harness/assertion bugs.
- **Human decision gate:** before starting, confirm with the human which entries in
  the post-sp4 red list are genuine product bugs vs. still-mistaken assertions. Only
  the human-classified Layer C items get tasks. Items the human classifies as bad
  assertions go back to sp4.
- **Assumed system state:** the `comprehensive-ui-test` goal exists in Diecast (it
  was created during the original harness build-out). Verify with
  `curl -s http://localhost:8000/api/goals/comprehensive-ui-test`. If absent, halt
  and ask the user — do not invent the goal.

## Scope

**In scope:**
- Re-run the harness (`pytest cast-server/tests/ui/`) after sp4.
- For each entry the human has classified as a real product bug:
  1. Reproduce manually by clicking through the same flow on the dev server at
     `:8005` (preferred) or `:8006`-test.
  2. Capture: failing assertion name + a step-by-step manual repro recipe + a
     one-paragraph root-cause hypothesis (drawn from the test cast-server log
     surfaced by sp2).
  3. File ONE Diecast task on the `comprehensive-ui-test` goal with status
     `'suggested'` (or `'todo'` if the user wants to commit immediately) via the
     `/cast-tasks` skill or the HTTP API:
     `POST /api/tasks` with the goal slug.

**Out of scope (do NOT do these):**
- Do NOT fix any of the bugs. This sub-phase is enumeration.
- Do NOT file the bugs anywhere other than as Diecast tasks under
  `comprehensive-ui-test` (no separate plan docs, no umbrella plan, no GitHub
  issues — per plan-review decision #2).
- Do NOT file an item that's NOT manually reproducible. If the dev-server reproduce
  step fails to surface the bug, kick the entry back to sp4 — it's a test bug.
- Do NOT modify test code, product code, or test agent definitions.
- Do NOT change the harness behavior — the harness is "done" after sp4.

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| (no source files) | -- | This sub-phase produces Diecast tasks via the API/skill, not file edits. |
| `docs/execution/cast-ui-harness-layered-fixes/sp5_layer_c_bug_enumeration/_layer_c_summary.md` | Create | A markdown summary of all tasks filed, with task IDs and a one-line description per. Lives in this sub-phase directory for future reference. |

## Detailed Steps

### Step 5.1: Re-run; capture the post-sp4 red list

```
pytest cast-server/tests/ui/ -x --tb=long > /tmp/uitest-after-B.log 2>&1 || true
```

Then for each child still in `assertions_failed[]`, copy:
- `name` of the failing assertion
- `error` text
- The path to the screenshot artifact under `/tmp/diecast-uitest-debug-*/`
- The relevant tail from the `[test-cast-server stdout]:` section in pytest output
  (sp2's deliverable)

### Step 5.2: Human classification gate

Present the red list to the human. For each entry, the human marks:
- **Layer C — real product bug.** Proceed with task filing.
- **Still a bad assertion / sp4 missed something.** Send back to sp4.
- **Acceptable / known limitation.** Document and skip; do NOT file a task.

Do NOT auto-classify. Wait for the human's call on each entry.

### Step 5.3: Manual reproduction per Layer C item

For each human-classified Layer C entry:

1. Boot the dev server (`bin/cast-server` on `:8005`, the standard dev port — NOT
   `:8000`-prod-style if present).
2. In a real browser, walk through the same flow the failing assertion exercises.
3. Confirm the bug reproduces.
4. Write a step-by-step recipe in the form:
   - "Open `<url>`."
   - "Click `<selector>`."
   - "Observe `<expected>` but get `<actual>`."
5. Form a root-cause hypothesis. Use the test cast-server log (sp2's tempfile) to
   ground the hypothesis. Example: "POST /api/goals returns 500 because
   `services/goal_service.py:create_goal` raises on missing `phase` kwarg — see log
   line 142."

If the bug does NOT reproduce on the dev server, it's a test bug, not a product bug.
Send back to sp4 (or document as "harness-only" and skip).

### Step 5.4: File the Diecast tasks

For each Layer C entry:

```
POST /api/tasks
{
  "goal_slug": "comprehensive-ui-test",
  "title": "<one-line description>",
  "status": "suggested",  // or "todo" if the user prefers
  "description": "
    Failing assertion: <name>

    Manual repro:
    1. ...
    2. ...
    3. Observe <expected> vs. <actual>

    Root-cause hypothesis: <one paragraph>

    Surfaced by: docs/plan/2026-05-01-cast-ui-harness-layered-fixes.collab.md (Layer C)
  "
}
```

Or, equivalently, invoke the `/cast-tasks` skill with a batch-create payload listing
all the Layer C items at once. (The skill is the preferred path; the raw HTTP form
above documents what the skill must produce.)

Capture the returned task IDs.

### Step 5.5: Write the summary doc

Create `_layer_c_summary.md` inside this sub-phase directory listing:

- One row per filed task: `task_id | screen | assertion_name | status` (one-line
  description acceptable in place of the full repro).
- A footer link back to the source plan and to `comprehensive-ui-test`.
- The total counts: how many Layer C items the harness surfaced; how many tasks
  were filed; how many entries were classified as harness-only and bounced.

This summary doc is the deliverable proving SC-005.

## Verification

1. **Diecast UI check:** open `comprehensive-ui-test` in the Diecast UI; confirm
   the new tasks appear with the expected status, titles, and descriptions.
2. **Repro check:** for at least 2 of the filed tasks, hand the manual repro recipe
   to a fresh reader (or yourself in a clean state). The recipe should surface the
   bug without further investigation.
3. **Boundary check:** SC-002's `[test-cast-server stdout]:` evidence is referenced
   in at least one task's root-cause hypothesis (proving sp2 is paying off).
4. **Summary doc check:** `_layer_c_summary.md` exists in this sub-phase directory
   and lists every filed task ID.

## Acceptance Criteria

- Each filed task is on the existing `comprehensive-ui-test` goal (not a new goal,
  not a separate plan doc, not an umbrella plan).
- Each task has: failing assertion name, manual repro recipe, root-cause hypothesis.
- No bugs were fixed in this sub-phase.
- `_layer_c_summary.md` enumerates all filed tasks.
- The harness's remaining red list is fully accounted for: every entry is either
  a filed Layer C task, a "send back to sp4" item, or a documented harness-only
  exception.

## Risk / Notes

- **Resist the urge to fix.** When you find a 500 in the test cast-server log with
  an obvious one-line patch, do NOT apply it. File the task and move on. Mixing
  enumeration with fixes blows the plan's scope and the constraint
  "Plan stays scoped to harness fixes."
- **Watch for goal slug drift.** The existing goal's slug is `comprehensive-ui-test`.
  If for some reason it differs in your environment, halt and ask the user; do NOT
  silently file under a different slug.
- **Repro on `:8005` vs. `:8006`-test.** The dev-server repro is the load-bearing
  signal. The test cast-server's logs are useful for hypothesis-building but the
  bug must be reproducible against a normal dev server. Anything dev-server-clean
  but test-server-broken is a harness bug.
- **Task vs. subtask.** All Layer C items are top-level tasks on
  `comprehensive-ui-test`. Don't nest them as subtasks of an "umbrella" task —
  plan-review decision #2 explicitly chose flat tasks.
