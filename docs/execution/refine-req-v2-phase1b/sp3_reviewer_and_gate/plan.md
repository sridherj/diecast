# Sub-phase 3: Adversarial Reviewer Subagent + HARD GATE

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1b/_shared_context.md` before starting.

## Objective

Land the **anti-one-shot** edits of Phase 1b (plan activities 8 and 7). A fresh-context
adversarial reviewer subagent scores the draft on five dimensions and feeds fixes back; the
`/spec` HARD GATE forbids first-response persistence and guarantees the user sees the
(fully-reviewed) draft before it is written. Per Decision #2 the reviewer runs **before** the gate
presentation, so the user signs off on the version that actually persists. Per Decision #1 the
gate is interactive-only — headless/HTTP-delegated runs auto-persist after the reviewer.

## Dependencies
- **Requires completed:** sp1 (detection), sp2 (evidence + Decisions). The reviewer reviews the
  draft that includes the Decisions section and evidence-backed confidences; the gate presents it.
- **Assumed codebase state:** sp1+sp2 edits present; prompt around ~500 lines; Workflow section
  and Step 2.1 / Step 1.5 intact.

## Scope

**In scope:**
- Activity 8 — inline (~40-line) adversarial reviewer rubric, dispatched as a **Claude Code
  Agent-tool** general-purpose subagent (NOT Diecast HTTP delegation), prompt = draft document
  only. Five dimensions (Completeness/Consistency/Clarity/Scope/Feasibility), 1–10 each; issues
  per dimension <7. Convergence: fix <7, re-dispatch, max 3 iterations, then log remaining to Open
  Questions. Stub-skip (<200-word / Stage-1). Fail-soft (note "independent review skipped:
  <reason>" and proceed). Run **before** the Step 2.1 final draft presentation.
- Activity 7 — HARD-GATE sentence near the top of the Workflow section; amend Step 1.5's
  "skip to Phase 3" exit; interactive-only behavior with headless auto-persist recording
  `auto-persisted: non-interactive run` in the output contract.

**Out of scope (do NOT do these):**
- Re-introducing the adversarial meta-pass (activity 5 — CUT by Decision #3). Do NOT add a
  second adversarial rubric. Keep activity-5's tombstone reference legible if you touch nearby
  text, but add no meta-pass logic or pin anchor.
- Detection / evidence / Decisions edits (sp1, sp2).
- `bin/generate-skills`, tests (→ sp4). Do NOT regenerate skills here.
- Registering a new `cast-requirements-reviewer` agent — v2 uses the Agent tool inline only.
- Adding `allowed_delegations` to `config.yaml` — the reviewer is NOT an HTTP child.
- Touching `#### Step 2.2.1: Domain Web Search`.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | sp1+sp2 edits present |

## Detailed Steps

### Step 3.1: Add the inline reviewer rubric, run before draft presentation (activity 8, Decision #2)
Insert a reviewer step in the Workflow that runs **before** the Step 2.1 final draft
presentation / go-ahead (the source plan originally numbered it "Step 3.0b after Phase 2, before
persist", then reordered it to precede the final presentation — implement the reordered version).
Keep it compact (~40 lines). It must specify:
- **Dispatch:** a fresh-context **Claude Code Agent tool** subagent (general-purpose), whose
  prompt contains ONLY the draft document — not the conversation. (Rationale in `_shared_context.md`
  §Architecture: interactive session, no `run_id`, no `allowed_delegations`; the office-hours
  value is fresh eyes on only the document.)
- **Rubric:** score 1–10 on five dimensions — **Completeness / Consistency / Clarity / Scope /
  Feasibility** — and return specific issues for each dimension scoring <7.
- **Convergence guard:** fix the <7 issues, re-dispatch; **max 3 iterations**, then proceed with
  remaining issues logged to Open Questions (never exceed the 7-question budget on the reviewer's
  behalf — user-resolvable issues fold into the question budget / Open Questions).
- **Stub-skip (Decision #6):** skip the reviewer entirely when the input is a vague-stage stub
  (<200 words / Stage-1 per the Step 1.3 stage table) and surface
  `review skipped: stub-sized input` exactly like the fail-soft note.
- **Fail-soft:** if the subagent errors or is unavailable, note
  `independent review skipped: <reason>` to the user and proceed — the reviewer must never block
  refinement. (On a skipped/failed reviewer run there is now NO adversarial pass at all — accepted
  per Decision #3; evidence-quoting + Open-Questions invariant still hold.)

### Step 3.2: Add the HARD-GATE sentence (activity 7)
Near the top of the Workflow section, add verbatim:
> Do NOT write `refined_requirements.collab.md` in your first response. Always present the
> (fully reviewed) draft and give the user at least one opportunity to react before persisting —
> even when every section is medium+ confidence.

### Step 3.3: Amend the Step 1.5 "skip to Phase 3" exit (activity 7)
Change Step 1.5's "If all sections are medium+, skip directly to Phase 3" to: "skip the
*questioning loop*, but still run the independent reviewer (Step 3.1), then present the draft and
wait for one go-ahead." This is an intentional behavior change — the prompt previously allowed a
zero-interaction one-shot; the minimum interaction is now one draft-review round-trip. Note the
cost (one extra round-trip on clean runs) is accepted by design.

### Step 3.4: Interactive-only gate + headless auto-persist (activity 7, Decision #1)
Document that the gate applies **only when running interactively**. When `cast-refine-requirements`
is invoked headless / HTTP-delegated (a parent dispatching it as a child, no human to give the
go-ahead), the agent does NOT wait at the gate: after the reviewer subagent it **persists
automatically** and records `auto-persisted: non-interactive run` in its output contract. State
explicitly that headless invocation is **supported**, not a non-goal.

## Verification

### Automated Tests (permanent)
- None here (pins are sp4). Run the existing pin: `pytest tests/test_b1_domain_search.py` → pass.

### Validation Scripts (temporary)
```bash
F=agents/cast-refine-requirements/cast-refine-requirements.md
grep -nq 'Completeness' "$F" && grep -nq 'Feasibility' "$F" && echo "five-dim rubric OK"
grep -niq 'max 3 iteration' "$F" && echo "convergence guard OK"
grep -niq 'review skipped: stub-sized input' "$F" && echo "stub-skip note OK"
grep -niq 'independent review skipped' "$F" && echo "fail-soft note OK"
grep -niq 'Do NOT write .refined_requirements.collab.md. in your first response' "$F" || \
  grep -niq 'in your first response' "$F" && echo "HARD-GATE sentence OK"
grep -niq 'auto-persisted: non-interactive run' "$F" && echo "headless auto-persist OK"
grep -niq 'Agent tool' "$F" && echo "Agent-tool dispatch noted OK"
# Negative checks — meta-pass stays cut; no HTTP child wiring added:
! grep -niq 'meta-pass.*rubric\|adversarial meta-pass scoring' "$F" && echo "no meta-pass logic OK"
wc -l "$F"   # must remain < 650
```

### Manual Checks
- Confirm the reviewer step is positioned **before** the Step 2.1 final draft presentation, not
  after persist.
- Confirm the reviewer is dispatched via the **Agent tool** (general-purpose), not a Diecast HTTP
  trigger, and that `config.yaml` gained no `allowed_delegations`.
- Confirm there is exactly ONE adversarial rubric (no meta-pass twin).

### Success Criteria
- [ ] Inline ~40-line reviewer rubric: five dimensions, 1–10, issues <7, max-3-iteration
      convergence, Open-Questions overflow.
- [ ] Reviewer dispatched via Claude Code Agent tool with draft-only prompt; runs **before** the
      Step 2.1 presentation (Decision #2).
- [ ] Stub-skip (<200-word / Stage-1) and fail-soft notes both present and worded as specified.
- [ ] HARD-GATE sentence present near the top of Workflow; Step 1.5 exit amended to
      reviewer-then-present-then-wait.
- [ ] Interactive-only gate documented; headless auto-persist records
      `auto-persisted: non-interactive run`.
- [ ] No meta-pass logic re-introduced; no HTTP-child wiring / `allowed_delegations` added.
- [ ] `pytest tests/test_b1_domain_search.py` passes; prompt line count < 650.

## Execution Notes
- The prompt-size ceiling matters most here — the reviewer rubric is the largest single addition.
  Keep it a rubric, not an essay (~40 lines). If `wc -l` approaches 650, trim verbose prose in the
  rubric or earlier steps before proceeding.
- The reviewer prompt sees ONLY the draft. Do not let it inherit conversation context — that
  defeats the fresh-context value.
- Do NOT run `bin/generate-skills` here — batched in sp4.
- **Spec-linked files:** none modified in this sub-phase.
