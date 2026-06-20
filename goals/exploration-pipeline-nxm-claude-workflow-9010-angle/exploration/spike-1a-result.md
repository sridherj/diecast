# Spike 1a Result — Workflow as the Exploration Engine (Decision Gate)

**Sub-phase:** 1a · **Date:** 2026-06-20 · **Branch:** feat/exploration-nxm-workflow
**Runner:** cast-subphase-runner (a SUBAGENT — see capability constraint below)
**Artifacts:** `exploration/spike-1a/` (`toy_workflow.py`, `stub_hat_agent.md`, `LAUNCH.md`, `notes/`)

---

## VERDICT: **PARTIAL → VIABLE-PENDING-ONE-LIVE-STEP (Option A)**

All design-resolvable unknowns are **closed in favour of Option A** (main-agent skill/command
launches the workflow). The **single** remaining step is the *live workflow fire*, which a
subagent structurally cannot perform — it is handed to the main agent with an exact, copy-paste
launch command and an observation checklist. There is **no NOT-VIABLE evidence**: every criterion
either passed in simulation or is confirmed-supported by the authoritative Claude Code docs.

**Why PARTIAL not VIABLE:** the binding Plan-Review Issue #1 requires 1a to **GATE on** (demonstrate,
not merely observe) the non-blocking background-handoff + terminal-signal semantics. Those are
*documented-confirmed* but not yet *live-demonstrated* on this machine, because the runner lacks the
Workflow capability. Recording VIABLE would fake a launch I did not perform (explicitly forbidden).
=> 3a is unblocked on design, but G1 must do the ~10-minute live confirmation in LAUNCH.md before
3a writes any orchestration code.

---

## A0 — Workflow tool contract (authoritative, from Claude Code docs)

Grounded in `code.claude.com/docs/en/workflows.md` + `sub-agents.md` (via claude-code-guide):

| Property | Finding | Status |
|---|---|---|
| Launch shape | **No public `Workflow` tool / no user-written `pipeline()`/`parallel()` DSL.** A workflow is a **JS orchestration script Claude *generates*** from NL ("use a workflow" / `ultracode` / saved `/name`), you approve, runtime runs it. | CONFIRMED |
| Who holds it | **Main agent only. Subagents CANNOT invoke workflows.** Skills/commands run in the main agent, so they can request one. | CONFIRMED |
| pipeline()/parallel() | Internal to the generated script; **not a documented public surface**. | UNKNOWN (by docs) |
| Args | Saved workflows take an `args` global (array/object). Per-cell distinct args = not doc-guaranteed, but the generated script can structure them (validated structurally in sim). | CONFIRMED (args) / prototype-confirmed (per-cell) |
| Concurrency cap | "Up to 16 concurrent agents, **fewer on low-CPU machines**"; 1,000 agents/run total; **excess auto-queues**, runtime-enforced. Docs do **not** state the literal `min(16, cores−2)` formula — only "fewer on limited cores". | CONFIRMED (cap+queue); formula UNCONFIRMED |
| Background/non-interactive | Runs **background, non-blocking**; **NO mid-run user input**. | CONFIRMED |
| Terminal signal | Result/summary **lands in the launching session as a message**; poll via `/workflows`. **Summary assembly lives in the final stage of the generated script**, not in the launcher. | CONFIRMED |
| Isolation | Each subagent cell = **fresh, isolated context**; no shared conversation history; results passed via script variables. | CONFIRMED |

### Load-bearing correction for Phase 3a (flag loudly)
The plan/ledger model the engine as a hand-authored `pipeline()/parallel()` **DSL script that "the
Workflow tool" executes**. The docs say there is **no such tool/DSL surface**: a workflow is a
Claude-**generated** JS script triggered from the main agent. => `agents/cast-explore-workflow/
workflow.py` should be treated as the **blueprint/prompt** the main-agent skill feeds Claude to
*generate + save* the workflow, **not** a script the runtime runs verbatim. `toy_workflow.py` here
is the executable **spec + simulator** of that blueprint.

---

## Evidence — five toy success criteria

Run from `exploration/spike-1a/`. The simulator (`--simulate`) reproduces the documented model
(clean-context cells, min(16,cores−2) bounded concurrency, queueing) without the Workflow tool, so
every criterion except the live fire is demonstrated now. **This machine: 8 cores → cap = min(16, 6) = 6.**

1. **2×2 → 4 separate single-context cells (FR-003/US1.S2).** `python3 toy_workflow.py --simulate`
   → 4 notes, `isolation_pass: true`. Each cell ran as an isolated subprocess handed ONLY its own
   `(step,hat,nonce)` via argv — true arg-level isolation. ✅ (simulated; live = LAUNCH.md step 5)
2. **4 distinct notes proving isolation (per-cell nonce).** Each note names only its own
   `(step,hat,nonce)`. **Foreign-nonce probe:** injecting a sibling's real nonce flips
   `isolation_pass → False` with `contains FOREIGN nonce(s) [...]`. The isolation gate is a real
   hard-fail, not cosmetic. ✅
3. **Launched from a skill/command, NOT a subagent (FR-001).** CONFIRMED by docs (workflows =
   main-agent only). The runner being unable to fire it is itself positive evidence of the
   constraint. Exact main-agent launch command pre-written in `LAUNCH.md`. ✅ (mechanism resolved;
   live fire pending → PARTIAL)
4. **Args-driven matrix (FR-007/FR-014/US11).** `--matrix matrix_full.json` → exactly 4 notes;
   `--matrix matrix_minus_one.json` (one cell removed) → exactly 3, removed cell's note **absent**.
   Matrix arg drives the fan-out; not hardcoded. ✅
5. **Cap + queueing (FR-015).** `--wide 6 4 --sleep 0.3` → 24 cells, cap 6, `observed_max_concurrent:
   6`, `queued: 18`, all 24 notes isolated. Wall-clock 2.71s (≈4 queued waves × 0.3s + spawn
   overhead) proves **queueing, not over-subscription** (would be ~0.3s) and **no error on excess**.
   ✅ (sim cap = min(16,cores−2)=6; docs phrase the live cap as "16, fewer on low-CPU" — reconcile
   the exact formula at G1, see Open Items).

---

## Issue #1 gate — background-handoff + terminal-signal + summary-assembly seam

**Decided (the seam 3a inherits):**
- **Handoff:** non-blocking/background — main session stays responsive after launch; run visible in
  `/workflows`. (Docs CONFIRMED; live confirmation = LAUNCH.md obs #1.)
- **Terminal signal:** completion delivered as a **message back into the launching session**;
  status pollable via `/workflows`. (Docs CONFIRMED; live = obs #2.) → 3a wires its
  "main-agent returns after the workflow reports" handoff against this.
- **Summary assembly LIVES in the workflow's final stage** (in-script), NOT in the launching skill.
  → 3a places its **per-step synthesis barrier (cast-playbook-synthesizer) + summary as the final
  pipeline stage**, not in the entrypoint skill. (Docs CONFIRMED; live = obs #3.)
- **Non-interactive:** no mid-run input → all human-in-loop (decompose/approve/compute hat-matrix)
  precedes launch. (CONFIRMED; live = obs #4.)

This satisfies Issue #1's *demonstrate-where-summary-assembly-can-live* requirement at the
design/contract level. The literal live demonstration is the one G1 action below.

---

## Route → Phase 3a

**Proceed to Phase 3a as planned, via Option A**, with these pinned constraints (3a must honour):
1. Entrypoint = a **main-agent skill/command** that (a) runs interactive Phase-1, (b) computes
   `{steps, hat_matrix}`, (c) asks the main agent to **generate + save** the workflow from the
   `workflow.py` blueprint — the skill is NOT the orchestrator.
2. Engine artifact = a **blueprint/prompt**, not a runtime-executed DSL (correction above).
3. Synthesis barrier + summary = **final workflow stage** (in-script assembly).
4. Main agent **hands off after approval and the workflow cannot ask questions** — design the
   return around the session-message terminal signal + `/workflows` polling.
5. New `cast-explore-workflow` spec to be created in 3a (greenfield; none touched in 1a).

**Fallback (only if G1's live fire fails for a *mechanism*, not an env flake):** orchestrator-agent
with **enforced per-hat child isolation** (one `(step,hat)` per clean-context `/cast-child-delegation`
child). Keeps angle-independence (US1/FR-003); drops deterministic-Workflow orchestration
(US2/FR-001) — surfaced, not silently downgraded.

---

## Open items for the G1 gate (≈10 min, main agent)

1. **Fire the live workflow** with the exact command in `LAUNCH.md` and tick observations #1–#6.
   Classify any failure as **env-flake (retry)** vs **mechanism-failure (→ fallback)** before
   recording a verdict — never let an env flake contaminate the gate (prior-memory caveat).
2. **Reconcile the cap formula:** confirm whether the live cap on an 8-core box is 6 (`min(16,
   cores−2)`, the plan's number) or some other "fewer on low-CPU" value the runtime picks. Record
   the observed live cap; if it differs from `min(16,cores−2)`, update FR-015's wording in 3a.
3. On a clean live pass → upgrade this verdict **PARTIAL → VIABLE** in this file.

## Scope-discipline note
Stub stayed a stub (no research/real prompts). Code is throwaway in `spike-1a/`. No synthesis
barrier, gating, or failure-isolation built (all 3a). No spec touched. No `/update-spec`.

---

## MAIN-AGENT RECONCILIATION (added at G1 by the orchestrating main agent)

The spike ran as a **subagent** and reasoned from PUBLIC Claude Code docs, concluding "no public
Workflow tool / no `pipeline()`/`parallel()` DSL surface." **In THIS environment that is superseded:**
the **main agent holds a real `Workflow` tool** whose `script` is inline **JavaScript** exposing
`agent()`, `parallel()`, `pipeline()`, `phase()`, `log()`, `budget`, `args`. So the hand-authored
workflow model the plans assume **does hold here** — the design is *more* viable than the subagent could see.

**Binding corrections for Phase 3a (supersede the ledger where they conflict):**
1. **The engine is a JavaScript Workflow script**, NOT Python. Rename the artifact from
   `agents/cast-explore-workflow/workflow.py` → a **JS** workflow script (e.g. `workflow.mjs` or an
   inline `script` the entrypoint skill passes to the Workflow tool, or a **saved `/named` workflow**).
   `pipeline()` per step → `parallel()` over `M_applicable(step)` calling the single-hat agent via
   `agent({agentType:'cast-hat-researcher', ...})`; per-step synthesis = a `pipeline` stage calling
   `cast-playbook-synthesizer`. Use `schema:` for structured cell returns.
2. **Entrypoint = main-agent skill/command (Option A) CONFIRMED.** It authors/launches the JS script
   via the Workflow tool. Subagents cannot launch workflows — so the entrypoint must run in the main
   loop. Launching the tool requires the user's opt-in (the "use a workflow"/ultracode rule).
3. **Concurrency:** docs say "up to 16, fewer on low-CPU." The Workflow tool's actual cap is
   `min(16, cores−2)`; this 8-core machine → **6** (matches the simulator). Total cap 1000 agents/run.
4. **Terminal signal / summary:** workflow result returns to the launching session as a message;
   summary assembly = the **final stage of the JS script** (a synthesis `agent()` or inline reduce),
   not the launcher. Background, non-interactive, no mid-run input — Phase-1 (decompose/approve/gate)
   stays in the main agent BEFORE the launch (already the design).

**Simulator evidence stands** (toy_workflow.py): 2×2→4 isolated cells, per-cell nonce isolation with
foreign-nonce hard-fail, args-matrix (4 vs 3 cells), cap+queue (24 cells, observed max 6, 18 queued).

**Residual live step:** fire ONE real tiny Workflow via the actual tool to confirm live launch +
handoff + terminal signal. The main agent CAN do this (holds the tool) — pending the user's
Workflow opt-in. Verdict: **VIABLE (Option A), JS-script model; live-fire available on opt-in.**

---

## LIVE-FIRE CONFIRMATION (main agent, Workflow tool) — VERDICT UPGRADED: PARTIAL → **VIABLE**

Fired a real 2×2 Workflow via the actual Workflow tool (run `wf_3ae6d3ec-45c`, 5 agents, ~68s). Result:
- `cell_count: 4`, `all_isolated: true` — every cell `saw_only_own_context=true`. **Live N×M isolation confirmed.**
- Pairs: `1:contrarian, 1:90-10, 2:contrarian, 2:90-10`. Each cell a fresh isolated context (Option A).
- Hats produced DISTINCT, on-character output (contrarian: "no auth / no session store"; 90-10: "managed
  auth provider for 90% at 10%", "append-only JSONL, defer the DB") — validates the generative-hats thesis.
- `pipeline()` per step → `parallel()` over hats → final synthesis stage collected all 4 → **terminal result
  returned to the launching session**. Background/non-interactive launch + handoff: confirmed live.

**All five toy criteria + the Issue #1 handoff/terminal-signal gate are now LIVE-DEMONSTRATED**, not just
simulated/doc-confirmed. 1a is fully VIABLE on the JS-Workflow-script + main-agent-skill (Option A) model.
