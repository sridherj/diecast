# Exploration Pipeline (N×M Workflow + 90/10 + HTML): Sub-phase 1a — Spike: Workflow as the Exploration Engine

## Overview

This is a **1–2 session de-risking spike**, not implementation. Its single job: prove (or
disprove) that the starter-exploration entrypoint can launch a Claude **Workflow** that receives
approved steps + a hat-matrix as args and runs an isolated N×M fan-out — each `(step, hat)` cell a
separate single-context agent — within the `min(16, cores−2)` concurrency cap. The spike builds the
**smallest toy that exercises the real launch path**: a 2 steps × 2 hats matrix where each cell is a
distinct clean-context agent that writes one distinct note (4 notes total), launched from a
**skill/command — not a subagent** (the hard constraint from FR-001 + Constraints). The deliverable
of the spike is a **decision** with evidence, recorded in this plan's gate, that unblocks Phase 3a
(the real engine) — or routes to the documented orchestrator-agent fallback.

This is a requirements-only spike: no exploration artifacts exist for it, and it touches no spec'd
behavior contract (the Workflow engine is greenfield; `cast-requirements-render.collab.md` is a
Phase 2b/3b/4 concern, not 1a).

## Operating Mode

**SCOPE REDUCTION** — the parent goal is HOLD SCOPE (`scope_mode: hold` in front-matter), but this
*sub-phase is explicitly a spike* ("Spike — Workflow as the exploration engine", "1–2 sessions",
"de-risking experiment"). The user instruction is emphatic: *"keep the detailed plan PROPORTIONATE
to a 1-2 session de-risking experiment… Do NOT over-engineer a spike into full implementation."*
Every activity below must pass the test: **is this the minimum needed to resolve the launch-mechanism
question and hit the toy success criteria?** Engine hardening, relevance gating, real hat prompts,
synthesis, failure-isolation polish — all DEFERRED to Phase 3a / 2a. The spike produces throwaway or
seed-quality code plus a written decision, not production wiring.

## Position in Overall Plan

```
        ┌─ Sub-phase 1a (THIS SPIKE: Workflow engine) ──────┐
        │                                                   ▼
Phase 1 ┤                                   Sub-phase 2a ─► Sub-phase 3a ─┐
(spikes)│                                  (hat agent)   (Workflow core)  │
        │                                                                 ▼
        └─ Sub-phase 1b (spike: viewer+comment) ─► 2b ─► 3b ─► Phase 4 ─► Phase 5
```

- **Dependencies:** None. Runs in parallel with Sub-phase 1b (independent track).
- **Blocks:** Sub-phase 3a (N×M Workflow engine + entrypoint). 3a's "Build the entrypoint
  (skill/command) per the Phase-1a decision" is a direct consumer of this spike's verdict.
- **Critical path:** Sub-phase 1a is the first node on the critical path (1a → 2a → 3a → 4 → 5).
  Slipping it slips the whole Track A core. This is exactly why it is frontloaded.

## Sub-phase 1a: Spike — Workflow as the Exploration Engine

**Outcome:** We know exactly how the starter-exploration entrypoint launches a Claude Workflow that
receives approved steps + a hat-matrix as args and runs an isolated N×M fan-out within the concurrency
cap — or we know it can't, and precisely why. The launch-mechanism question (main-agent skill/command
vs server-side dispatch) is resolved with a working demonstration, and the decision gate is recorded
in this file with evidence.

**Dependencies:** None.

**Estimated effort:** 1–2 sessions.

**Verification (the toy success criteria — copied from the high-level plan, made concrete):**
1. A toy Workflow runs a **2 steps × 2 hats** matrix → **4 cells**, each cell a **separate
   single-context agent** (no cell sees another cell's content — angle independence, FR-003/US1.S2).
2. The run writes **4 distinct research notes** to a scratch dir, one per cell, with content that
   proves each agent ran in isolation (e.g. each note names only its own `(step, hat)` and contains a
   per-cell nonce passed as an arg).
3. The launch path is demonstrated **from a skill/command, not a subagent** (FR-001, US2.S1,
   Constraints: "Workflows launch via the Workflow tool, not as a dispatchable subagent").
4. Args passing is confirmed: the toy receives `steps` + a `hat-matrix` (step→hats) as Workflow
   **args** (FR-007, FR-014, US11.S1) — not hardcoded inside the script.
5. The `min(16, cores−2)` concurrency cap + queueing is observed: force more cells than the cap (a
   throwaway widened matrix, e.g. 6×4 = 24 stub cells on a machine where the cap < 24) and confirm
   excess cells **queue** rather than over-subscribe or error (FR-015).

### Key activities

These are ordered as an experiment, not a build. Run E1→E2 first (they answer the gating
question); E3→E4 only matter if E1/E2 succeed.

- **A0 — Read the Workflow tool contract (15 min, no code).** Read the system-prompt Workflow tool
  docs end-to-end and write a 1-paragraph note capturing: how a Workflow is launched (the tool call
  shape), how `pipeline()`/`parallel()` compose, how args are passed in, how the `min(16, cores−2)`
  concurrency cap manifests, and the exact non-interactive/background semantics. This note is an input
  to the decision gate. **Do not** reverse-engineer from existing code — the tool docs are
  authoritative.

- **E1 — Toy Workflow script (the fan-out skeleton).** Write a minimal throwaway Workflow script in
  a scratch location (`goals/exploration-pipeline-nxm-claude-workflow-9010-angle/exploration/spike-1a/`)
  that: `pipeline()` over 2 steps → `parallel()` over 2 hats → calls a **stub single-hat agent** per
  cell. The stub agent does NOT do real research — it receives `(step, hat, nonce)` as input and
  writes `spike-1a/notes/{step}-{hat}.md` containing only its own three values. Goal: prove the 2×2
  fan-out shape runs and yields 4 isolated notes. *This is the seed shape for Phase 3a's real script
  (`pipeline() per step → parallel() over hats → synthesis barrier`) — keep it recognizable, but do
  not add the synthesis barrier, gating, or real prompts here.*

- **E2 — Resolve the entrypoint mechanism (the central unknown).** Determine and DEMONSTRATE how the
  "Run starter exploration" step triggers the Workflow tool, given Workflows are non-interactive and
  launched via the tool (not as a dispatchable subagent). Test the two candidate mechanisms head-to-head
  (see "Entrypoint mechanism — options to test" below) and pick the one that launches the E1 toy
  cleanly **from a skill/command surface, not from inside a subagent**. Capture: which mechanism worked,
  the exact launch invocation, and any friction (opt-in prompts, background/non-interactive gotchas,
  how the interactive Phase-1 main agent hands off without itself being the Workflow).

- **E3 — Confirm args passing (steps + hat-matrix).** Extend E1 so `steps` and the `hat-matrix`
  (a `step → [hats]` map) are passed in as Workflow **args** and drive the fan-out (the script reads
  the matrix to decide which `(step, hat)` cells to spawn), rather than being hardcoded. This proves
  the US11 contract: interactive Phase-1 computes the matrix, then the Workflow consumes it as args.
  Verify by running with a hand-authored 2×2 matrix arg and confirming exactly the 4 expected notes
  appear; then run with one cell removed from the matrix and confirm that note is absent.

- **E4 — Observe the concurrency cap + queueing.** Widen the throwaway matrix past the cap (e.g.
  6 steps × 4 hats = 24 stub cells; make each stub sleep briefly so overlap is observable) and confirm
  the Workflow runs at most `min(16, cores−2)` concurrently while the rest queue — no over-subscription,
  no error on excess. Record the observed cap value on this machine and the queueing behavior. This is
  the cheapest possible check of FR-015; do not build queue instrumentation, just observe.

- **A5 — Record the decision gate (see below) in this file.** Write the verdict, the evidence
  (which mechanism, the 4 notes, the observed cap), and the route (3a-as-planned vs fallback). This
  written verdict is the actual deliverable of the spike.

### Entrypoint mechanism — options to test (E2)

The open question this spike closes (plan Open Questions: *"does the 'Run starter exploration'
starter-task launch the Workflow via a new main-agent skill/command or a server-side dispatch?"*).
Two candidate mechanisms; the spike picks one by demonstration. **Recommendation: try Option A
first** — it is the closest fit to the stated constraint (entrypoint = a skill/command) and the
lowest-integration path for a spike.

- **Option A — Main-agent skill/command launches the Workflow tool (Recommended).**
  The interactive Phase-1 runs in the main agent (intent → decompose → approve → compute hat-matrix,
  per US11). When the user approves, a **skill/command** (e.g. a `cast-explore-workflow` skill, name
  TBD in 3a) issues the Workflow **tool** call with `{steps, hat_matrix}` as args. The Workflow then
  runs non-interactively in the background. *Why first:* the Constraints pin the entrypoint to "a
  skill/command", and the Workflow tool is invoked by an agent that has the tool — the main agent
  does. Test: can a skill/command surface issue the Workflow tool call and have it fan out without the
  skill itself becoming the orchestrator?

- **Option B — Server-side dispatch.** A Diecast server endpoint (mirroring the existing
  child-dispatch / `render_job_service` background-job pattern) kicks the Workflow. *Why second:*
  heavier integration than a spike warrants, and it is less obviously compatible with "launched via
  the Workflow tool, not a subagent" — but it is the natural fallback if a skill/command cannot host
  the tool call. Only test B if A hits a wall; capture *why* A failed before moving on.

The spike does **not** need to fully build either path — it needs to demonstrate that **one** of them
can launch the E1 toy from a non-subagent surface. The chosen mechanism becomes a pinned input to
Phase 3a's "Build the entrypoint" activity.

### Decision gate (the deliverable)

Record one of these verdicts in this file at A5, with evidence:

- **VIABLE → proceed to Phase 3a as planned.** All five verification criteria pass: 4 isolated notes
  from 4 single-context cells, launched from a skill/command (not a subagent), args-driven matrix,
  cap respected. Record: the working mechanism (A or B), the launch invocation, and any constraints
  3a must honor (e.g. "main agent must hand off after approval; the Workflow cannot ask questions").

- **NOT VIABLE → fallback: orchestrator-agent with enforced per-hat child isolation.** If the launch
  can't be wired cleanly from a non-subagent surface, or isolation/args/cap can't be satisfied via the
  Workflow tool, fall back to keeping today's `cast-explore`-style **orchestrator agent** but
  **enforcing per-hat child isolation** (each `(step, hat)` dispatched as its own clean-context child
  via `/cast-child-delegation`, one hat per child — NOT today's 7-hats-in-one-context). Record exactly
  *which* criterion failed and why, so Phase 3a re-scopes to the fallback with eyes open. **Note:** the
  fallback still satisfies the *angle-independence* core value (US1/FR-003) — it sacrifices only the
  "deterministic Workflow orchestration" property (US2/FR-001), which is a known, acceptable
  degradation per the plan's risk table. Surface this trade-off explicitly; do not silently downgrade.

### Design review

- **Spec consistency:** No spec'd behavior contract is touched by this spike. The Workflow exploration
  engine is greenfield (no spec exists yet); `cast-requirements-render.collab.md` governs the
  HTML/render track (Phase 2b/3b/4), not 1a. **No `/update-spec` needed for 1a.** (When the real engine
  lands in Phase 3a, a new `cast-explore-workflow` spec should be created — flag for 3a, not here.) ✓
- **Constraint adherence (load-bearing):** The spike's success criteria are written directly against
  the hard constraints — "launched via the Workflow tool, not a subagent" (FR-001), "each hat-agent
  prompt contains ONLY its step + its hat" (FR-003), "`min(16, cores−2)`" (FR-015), "steps + hat-matrix
  as Workflow args" (FR-014). The toy is engineered to *demonstrate* each, not assume it. ✓
- **Isolation correctness:** The per-cell nonce trick is the cheap proof of angle-independence — if any
  note contains another cell's nonce, isolation is broken and that is a hard FAIL, not a warning
  (surface, don't suppress). ✓
- **Scope discipline:** Watch for spike creep. The stub agent must stay a stub (no web research, no
  real hat prompts — those are Phase 2a). The script must stay throwaway-quality in `spike-1a/`. No
  synthesis barrier, no relevance gating, no failure-isolation polish — all Phase 3a. ✓
- **Environment caveat (from prior memory):** Autonomous/headless runs in this environment can't always
  reach a browser, and tmux/dispatch launches occasionally flake. If E2 launch flakes, distinguish a
  *mechanism* failure (real, gates the decision) from an *environment* flake (retry, don't let it
  contaminate the verdict). Log which it was. ✓
- **Error & rescue:** This is a spike — the only "error path" that matters is the decision gate's
  NOT-VIABLE branch, which is already a first-class outcome with a documented fallback. No rollback/retry
  machinery needed in throwaway code. ✓

## Build Order

```
A0 (read tool docs) ─► E1 (toy 2×2 fan-out) ─► E2 (entrypoint mechanism) ─┬─► E3 (args: steps+matrix)
                                                                          └─► E4 (cap + queueing)
                                                                                      │
                                                                                      ▼
                                                                          A5 (record decision gate)
```

**Critical path within the spike:** A0 → E1 → E2 → A5. E3 and E4 are independent refinements that
can run in either order once E2 proves the mechanism; both must land before A5's verdict. If E2 fails
(no clean non-subagent launch), short-circuit to A5 with the NOT-VIABLE verdict and the fallback —
do not burn the second session on E3/E4.

## Design Review Flags

| Sub-phase | Flag | Action |
|-------|------|--------|
| 1a | No spec'd behavior touched; engine is greenfield | No `/update-spec` in 1a. Flag for Phase 3a: create a new `cast-explore-workflow` spec when the real engine lands. |
| 1a | Isolation must be *proven*, not assumed | Use per-cell nonce in args; a note containing a foreign nonce = hard FAIL (surface, don't suppress). |
| 1a | Spike-creep risk (the toy growing into the engine) | Stub agent stays a stub; code stays in throwaway `spike-1a/`; no synthesis/gating/failure-isolation. |
| 1a | Launch flake vs mechanism failure (env caveat) | On E2 launch failure, classify env-flake vs real-mechanism-failure before recording the verdict. |
| 1a | Fallback silently loses the determinism property | If NOT-VIABLE, explicitly record that the orchestrator fallback keeps angle-independence but drops US2 deterministic-Workflow orchestration — surface the trade-off. |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Workflow tool can't be cleanly launched from a non-subagent skill/command surface (the central unknown) | High | This spike exists to find out. Test Option A first, Option B as fallback; if neither, route to the orchestrator-agent fallback with per-hat child isolation. |
| Spike over-engineers into partial Phase-3a implementation, blowing the 1–2 session budget | Med | Hard scope fence: stub agent, throwaway dir, no synthesis/gating. E2 is the gate — short-circuit to the verdict if it fails rather than polishing E3/E4. |
| Cell isolation looks fine but a shared context leaks (false-positive viability) | Med | Per-cell nonce proof; any foreign nonce in a note fails the isolation criterion outright. |
| Environment flake (tmux/dispatch/headless browser) masquerades as a mechanism failure | Med | Per prior memory: retry launch flakes, classify env-vs-mechanism before the verdict; never block the decision on an env flake. |
| Concurrency cap can't be observed cheaply (cap > available stub cells) | Low | Widen the throwaway matrix until cell count exceeds the machine's `min(16, cores−2)`; sleep-stubs make overlap observable. If still unobservable, record cap value from tool docs (A0) and note the limitation. |

## Open Questions

- **Entrypoint mechanism (RESOLVED BY THIS SPIKE):** main-agent skill/command (Option A) vs
  server-side dispatch (Option B)? The spike's E2 + A5 decision gate is the resolution. Recorded here
  on completion. *(This is the sub-phase's reason to exist.)*
- **For Phase 3a, not 1a:** If VIABLE, what is the skill/command's name and where does it live
  (a new `cast-explore-workflow` skill alongside intact `cast-explore`)? — Deferred to Phase 3a;
  the spike only needs *a* working surface, not the final naming.
- **For Phase 3a, not 1a:** Does the interactive Phase-1 main agent hand off to the Workflow and then
  return, or does it block until the Workflow completes? The spike should *observe* the
  non-interactive/background handoff behavior (note it at E2/A5) so 3a can design the hand-off, but
  the spike does not need to finalize the hand-off UX.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` | N/A for 1a — governs the HTML/render track (Phase 2b/3b/4), not the Workflow engine | None (out of scope for this sub-phase) |
| `cast-workflow-routing.collab.md` | Goal already routed `new_initiative`; no routing change | None |
| *(none — Workflow exploration engine)* | Greenfield; no spec exists yet | New `cast-explore-workflow` spec to be created in Phase 3a, NOT 1a |

## Plan Review Decisions (2026-06-20)

- **Issue #1 (Architecture) — Decision: 1A (accepted).** Expand 1a's **E2 success criteria to GATE on (not merely observe)** the non-blocking background-handoff + terminal-signal semantics: the spike must demonstrate HOW the launched Workflow signals completion/terminal state back and WHERE summary assembly can live. 1a is not recorded VIABLE until this is proven — so 3a inherits a fully-decided handoff seam.

## A5 — DECISION GATE (RECORDED 2026-06-20)

**VERDICT: PARTIAL → VIABLE-PENDING-ONE-LIVE-STEP (Option A — main-agent skill/command).**
Full evidence: `goals/exploration-pipeline-nxm-claude-workflow-9010-angle/exploration/spike-1a-result.md`.
Toy artifacts: `…/exploration/spike-1a/` (`toy_workflow.py`, `stub_hat_agent.md`, `LAUNCH.md`, `notes/`).

**What is resolved (no NOT-VIABLE evidence found):**
- Mechanism = **Option A**. Workflows are a **main-agent-only** capability; the entrypoint is a
  skill/command running in the main agent (CONFIRMED by Claude Code docs + by this runner, a
  *subagent*, structurally lacking the Workflow capability — ToolSearch surfaces no Workflow tool).
- **Isolation (FR-003):** 2×2 → 4 distinct notes, each carrying only its own per-cell nonce;
  foreign-nonce injection flips the gate to FAIL (`contains FOREIGN nonce(s)`) — a real hard-fail.
- **Args-driven matrix (FR-007/014):** matrix arg drives fan-out; removing a cell removes exactly
  its note (4 → 3).
- **Cap + queueing (FR-015):** 24-cell wide matrix on an 8-core box → cap 6, 18 queued, no
  over-subscription, no error; wall-clock proves wave-queueing.
- **Issue #1 seam (CONFIRMED by docs, design-decided):** workflow runs **background/non-blocking**;
  terminal signal = **result message back into the launching session** + `/workflows` polling;
  **summary assembly lives in the workflow's FINAL stage (in-script)**, so 3a places its synthesis
  barrier + summary there, not in the launching skill; **no mid-run user input** (all human-in-loop
  precedes launch).

**Why PARTIAL not VIABLE:** the runner is a subagent and **cannot fire the live workflow** (a
subagent does not hold the Workflow capability). Recording VIABLE would fake an unrun launch
(forbidden). The Issue #1 properties are docs-CONFIRMED but not yet *live-demonstrated*.

**The ONE remaining live step (for the G1 gate, ≈10 min, MAIN agent):** run the exact launch
command in `…/spike-1a/LAUNCH.md`, tick observations #1–#6 (background handoff, terminal signal,
in-script summary assembly, non-interactivity, 4-note isolation, live cap), classify any failure as
env-flake (retry) vs mechanism-failure (→ fallback), then upgrade PARTIAL → VIABLE in the result file.

**Load-bearing correction for 3a (flag loudly):** there is **no public `Workflow` tool and no
user-written `pipeline()/parallel()` DSL**. A workflow is a **Claude-generated JS orchestration
script** triggered from the main agent. So `agents/cast-explore-workflow/workflow.py` is the
**blueprint/prompt** the entrypoint skill feeds Claude to *generate + save* the workflow — NOT a
script a runtime executes verbatim. `toy_workflow.py` is the executable **spec + simulator** of that
blueprint.

**Route:** proceed to Phase 3a as planned via Option A with the 5 pinned constraints in the result
file. Fallback (orchestrator-agent + enforced per-hat child isolation) only if G1's live fire fails
for a *mechanism* reason.
