# Sub-phase 4a: Wire the single v2 caller (`cast-refine-requirements`) + ship `/cast-router`

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package E of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Make `cast-refine-requirements` — the **only** v2 caller — POST to `/api/goals/{slug}/route` right
after it confirms a classification, surface the routed workflow honestly in its summary, surface a
*changed* downstream workflow on reclassification (US6 S4), and fail soft if the server is down. Plus
ship `/cast-router`: a thin, read-only skill+agent that resolves and shows a goal's routed workflow
(the recorded default — ship it; it is the one cuttable item if budget runs short). This closes the
seam: the door (sp3) now has its single intended caller, and no other phase is wired.

## Dependencies
- **Requires completed:** **sp3** — `POST /api/goals/{slug}/route` live. (Transitively sp1a/sp1b/sp2.)
- **Assumed codebase state:** `agents/cast-refine-requirements/cast-refine-requirements.md` exists with
  Phase 2 WP-E's "Step 0 — Classify" (the classifier dispatch, confidence gate, `merge_front_matter`
  call, headless `fallback` policy, question budget). The prompt is near its ~650-line ceiling. The
  route endpoint accepts `{"family": "<value>"}`. `bin/generate-skills` regenerates the skills tree
  from `agents/`.

## Scope

**In scope:**
- Append ~15 lines to the **tail of Phase 2's "Step 0 — Classify"** in `cast-refine-requirements.md`:
  the route POST, the summary surfacing, the US6 S4 reclassification surfacing, and the fail-soft note.
- Create `agents/cast-router/` (skill `.md` + `config.yaml`): read-only, `dispatch_mode: subagent`, no
  `allowed_delegations`; resolves + shows a goal's routed workflow via `POST /route` with no body.
- Run `bin/generate-skills`; verify both generated skills appear and the refine prompt stays under the
  ~650-line ceiling.

**Out of scope (do NOT do these):**
- Wiring **any other phase** (planners/executors) — the endpoint is the door; future callers get wired
  in later per-family pipeline goals. HOLD SCOPE.
- The agent writing the goal columns directly — single-writer discipline: the agent triggers via HTTP;
  the service (sp2) owns the write.
- Duplicating or relocating Phase 2/1b content in the prompt (`## Decisions`, scope-mode, the Step 0
  classify body) — only **append** the routing tail and sequence the existing question budget.
- Re-implementing resolve/record (sp2) or the route (sp3).
- Any `AskUserQuestion` slot beyond the existing classification confirm (the question-budget contract
  with Phases 1b/2 must hold).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | Has Phase 2 Step 0; near ~650-line ceiling |
| `agents/cast-router/cast-router.md` | Create | Does not exist |
| `agents/cast-router/config.yaml` | Create | Does not exist |
| (generated) `.claude/skills/cast-refine-requirements/*`, `.claude/skills/cast-router/*` | Regenerate | Via `bin/generate-skills` |

## Detailed Steps

### Step 4a.1: Append the routing call to Step 0

**After classification is confirmed** (auto/confirm/choose resolved, front-matter merged via
`merge_front_matter`), add one route call:

```bash
curl -s -X POST http://localhost:8005/api/goals/{slug}/route \
  -H 'Content-Type: application/json' -d '{"family": "<family>"}'
```

- This one call performs "write `workflow_family` to the goal" AND "record the routing decision"
  through the single door. The agent **never** writes the goal columns directly.
- **Authority (D2):** `goals.workflow_family` is the authoritative routing record; the front-matter
  `classification.family` written in the same Step 0 is the document's self-description, reconciled to
  the column on each refine. A hand-edited front-matter family takes effect only by re-running
  refinement (which re-routes and overwrites the column). State this so a future maintainer does not
  make front-matter authoritative.

### Step 4a.2: Surface the routed workflow in the summary

Render `status` **honestly** (the user should see it is a stub):

> Routed downstream workflow: `bug_fix` (stub) — steps: logs → RCA → confirm → fix/test

### Step 4a.3: Reclassification surfacing (US6 S4)

On a re-run where the classifier returns a different family, the route response carries `changed: true`
+ `previous_family`:
- **Interactive:** tell the user the downstream workflow changed (old → new, with the new steps) as
  part of the **existing** classification confirm flow — no extra `AskUserQuestion` slot.
- **Headless:** append the Phase 2 WP-E Open Questions note, extended with the routing change.

### Step 4a.4: Fail-soft

Route call fails (server down, non-200) → refinement does **NOT** die:
- Append an Open Questions line: *"classification recorded in front-matter; routing not recorded —
  re-run `/cast-router` or POST /route"* and continue.
- Classification (front-matter) and routing (goal columns) are deliberately **decoupled failure
  domains**.

### Step 4a.5: Ship `/cast-router` (recorded default: ship)

Create `agents/cast-router/` — a thin skill+agent whose entire job is "resolve and show the routed
workflow for a goal slug" via `POST /route` (no body), for humans and future agents alike:
- `config.yaml`: `dispatch_mode: subagent`, read-only, **no** `allowed_delegations`.
- The skill body: take a goal slug → `POST /api/goals/{slug}/route` (no body) → present the handle
  (family, status, steps, message) legibly; on `needs-classification`/`unmatched`, show the handle's
  message (it announces itself).
- → Consult `/cast-agent-design-guide` for the agent/skill file shape and I/O contract conventions;
  review its guidance before writing.
- **Budget note:** if the 1–2 session budget runs short, `/cast-router` is the designated cuttable
  item — **flag it in the run summary, never silently skip** (the refine wiring in 4a.1–4a.4 is NOT
  cuttable).

### Step 4a.6: Regenerate skills + ceiling check

```bash
bin/generate-skills
wc -l agents/cast-refine-requirements/cast-refine-requirements.md   # must stay ≲ 650
ls .claude/skills/cast-router/ .claude/skills/cast-refine-requirements/
```

- Review the refine prompt's routing addition: it must cite the **endpoint**, not direct DB access.

## Verification

### Automated Tests (permanent)
- This sub-phase is prompt/agent wiring — its behavioral guarantees are covered by sp3's E2E route
  tests (the contract the prompt calls). No new pytest module is mandated here.
- If a wiring-pin test exists in the repo for refine-prompt structure (precedent: Phase 2's
  `test_b1_domain_search.py` / Step-0 pins), add a one-line grep-pin asserting the routing `curl`
  cites `/api/goals/{slug}/route` and appears **after** the `merge_front_matter` step.

### Validation Scripts (temporary)
```bash
# Prompt cites the endpoint, not direct DB writes, and routes AFTER classify-confirm:
grep -n "api/goals/{slug}/route\|/route" agents/cast-refine-requirements/cast-refine-requirements.md
! grep -qiE "UPDATE goals|workflow_family *=|sqlite" agents/cast-refine-requirements/cast-refine-requirements.md && echo "no direct DB write in prompt (correct)"
# /cast-router shipped + read-only:
grep -nE "dispatch_mode|allowed_delegations" agents/cast-router/config.yaml
bin/generate-skills && ls .claude/skills/cast-router/
```

### Manual Checks
- The routing tail sits at the **end of Step 0**, after `merge_front_matter`; it does not duplicate
  Phase 2/1b content.
- Summary renders `status` honestly (shows "(stub)").
- Reclassification surfacing rides the existing confirm — no new `AskUserQuestion` slot.
- Fail-soft path appends an Open Questions line, does not abort refinement.
- Prompt line count ≲ 650.

### Success Criteria
- [ ] Step 0 tail POSTs to `/api/goals/{slug}/route` with `{"family": ...}` after classification
      confirm; agent never writes goal columns directly.
- [ ] Summary surfaces the routed workflow with honest `status`; reclassification surfaces old→new
      (interactive) / Open Questions note (headless) with no extra question slot.
- [ ] Fail-soft: a dead server yields an Open Questions note, not a refinement abort.
- [ ] `/cast-router` shipped (`dispatch_mode: subagent`, read-only, no delegations) — OR cut with an
      explicit run-summary flag.
- [ ] `bin/generate-skills` run; both skills present; refine prompt ≲ 650 lines.

## Execution Notes
- **Coordinate with Phase 2 WP-E and Phase 1b** on the shared prompt file: this lands as the *tail* of
  Step 0 — keep the addition ~15 lines; rebase around (never clobber) Phase 1b's `## Decisions`/
  scope-mode edits and Phase 2's Step 0 body. Within Phase 3b only sp4a touches this file.
- The question-budget contract is load-bearing: the routing change surfacing must ride the existing
  classification confirm. Adding a slot would break the worst-case budget shared with Phases 1b/2.
- `/cast-router` is read-only by contract — it POSTs with **no body** (re-resolve from persisted
  state), so even though `/route` can record, the no-body path is a no-op on an already-routed goal and
  `needs-classification` on an un-routed one. It never *originates* a routing decision; that is
  refinement's job.

**Spec-linked files:** sp4b authors `cast-workflow-routing.collab.md` with the single-caller-in-v2
note. If `cast-delegation-contract.collab.md` or `cast-output-json-contract.collab.md` are touched by
the `/cast-router` agent files, read them — but `/cast-router` is subagent-mode and returns text, so it
sits outside those output-envelope contracts (state this, do not "fix" it).
