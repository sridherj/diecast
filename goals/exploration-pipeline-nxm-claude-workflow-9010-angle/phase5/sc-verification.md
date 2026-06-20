# Sub-Phase 5 — SC-001…SC-009 Verification Matrix

**Goal:** `exploration-pipeline-nxm-claude-workflow-9010-angle`
**Branch:** `feat/exploration-nxm-workflow`
**Run date:** 2026-06-20
**Verifier context:** `cast-subphase-runner` (autonomous subagent — NO Workflow tool, NO live WebSearch, NO Chrome)
**Pytest at verification time:** 365 passed, 1 failed (failure UNRELATED — see note at bottom)

## Mode & honesty disclosure

A true end-to-end **Run 1** (interactive Phase-1 → entrypoint skill → `cast-explore-workflow`
Workflow launch → N×M live web research → synthesis → render) **was NOT performed**. It cannot be:
the Workflow tool is **main-agent-only** and the hat cells require **live WebSearch**, neither of
which is available from this subagent context. The goal dir contains only **spike-1a** artifacts
(`exploration/spike-1a/notes/*.md`, a 2×2 toy), NOT a real `exploration/research/{NN}-{slug}-{hat-id}.ai.md`
tree. Per [[project_diecast_prototype_no_browser_visual_gates]] and [[feedback_surface_dont_suppress]]:
every SC that is **statically/structurally verifiable** is graded against the built code/agents now;
every SC whose evidence **requires the live run** is marked **`[NEEDS-LIVE]`** with the exact runbook
in `RUNBOOK-live-verification.md`. No live run is fabricated.

Legend: **PASS** (static evidence sufficient) · **PASS (static)** (contract/code verified; live
instance still recommended as carry-forward) · **[NEEDS-LIVE]** (cannot be verified without Run 1) ·
**FAIL** (routed to owning phase).

| SC | Verdict | Evidence | If live needed |
|----|---------|----------|----------------|
| SC-001 | **[NEEDS-LIVE]** (contract PASS) | The exact-filename-SET check (`{(nn,slug,hat_id)}` from the persisted hat-matrix == `ls research/*.ai.md` minus FR-016 nulls, minus `-code.ai.md`) requires a real Run-1 tree, which does not exist. **Contract is verified:** `workflow.mjs:29` writes `research/{NN}-{slug}-{hat_id}.ai.md` one-per-cell; `:44,:84-85` pin the surviving-note glob to EXACTLY `{NN}-{slug}-{hat_id}.ai.md` and **exclude `…-code.ai.md`** (the `cast-code-explorer` collision SC-001 warns about). `cast-hat-researcher.md:90` writes the same path. FR-016 dropped cells → loud placeholder + DEGRADED flag in `summary.ai.md` (`workflow.mjs:66,74`), never a silent gap → the count must subtract them. | Runbook step R1: persist emitted hat-matrix JSON; `ls research/*.ai.md \| grep -v -- '-code.ai.md' \| wc -l`; assert set-equality vs matrix minus logged nulls. |
| SC-002 | **PASS (static)** | `cast-hat-researcher.md:16-17` "wear exactly ONE hat … produce exactly ONE research note"; `:49-50` "Load ONLY that hat's prompt block. You MUST NOT see, load, reference, or even mention any other hat"; `:104` "exactly ONE hat_id — never a list"; `:151` "Load exactly one hat block … Never emit another block into context"; `:160` "The 8 hat prompt blocks (load exactly ONE)". The agent is a pure single-hat function; by construction a hat's invocation context carries no sibling-hat framing. Distinctness test `agents/cast-hat-researcher/tests/check-distinctness.sh` exists (2a). | Optional: open 2-3 real invocation records from Run 1 and quote the selected-hat header + assert absence of others. |
| SC-003 | **PASS (static)** | Two halves both verified in source: (a) **90/10 is a first-class always-on hat** — `cast-hat-researcher.md:73,268`; literal `hat_id` `90-10` matching the spec filename `…-90-10.ai.md` (`:75,:90`); its verdict line `RECOMMENDED CUT \| CUT WITH CAUTION \| DO NOT CUT` (README:42). (b) **First-Principles has NO 80/20 content** — explicit CARVE-OUT comment `cast-hat-researcher.md:248-249` "all 80/20 / '20% effort for 80% value' / MVP-laziest-path content has been DELETED from this hat and re-homed in the 90-10 hat. Do not reintroduce it." `:261-263` "MUST NOT reason about '20% of the effort for 80% of the value', MVP / laziest path … belongs to the `90-10` hat." First-principles grep for ABSENT 80/20 content **passes at the agent-definition level**: the only `80/20`/`Pareto`/`20% of` strings in the first-principles block are the **prohibitions** carving it out. | Runbook step R3: for each step, confirm a `*-90-10.ai.md` note exists (count == N); `grep -iE '80/20\|pareto\|20% of (the )?effort' research/*-first-principles.ai.md` → must be EMPTY in real notes; quote one 90/10 verdict line. |
| SC-004 | **[NEEDS-LIVE]** (contract PASS) | Needs a real Run-1 `playbooks/` tree. **Contract verified:** `workflow.mjs:176,194` writes exactly one `playbooks/{NN}-{slug}.ai.md` per step via the **UNCHANGED** `cast-playbook-synthesizer` (`:184,:187`). 1:1 step↔playbook by construction (one synthesis cell per step). | Runbook step R4: `ls playbooks/*.ai.md \| wc -l` == N; confirm slug 1:1. |
| SC-005 | **[NEEDS-LIVE]** (contract PASS) | Needs a real `exploration.html` + a live `cast-exploration-render-checker` verdict. **Contract verified:** `cast-exploration-render-checker.md:61-68` encodes EXACTLY FR-017's **4 LOCKED criteria** — (1) every applicable hat visible per step, (2) per-step POV legible at zero-click, (3) hats DISTINCT not blended (the novel axis, first-class), (4) visual quality / not AI-slop. The gate is **code-owned**: `:80-83` `derive_pass` requires all 4 clear; checker emits ONE bare-JSON verdict, never decides its own gate. Phase-4 publishes `exploration/exploration.html` atomically (498-line service, 336 passed). | Runbook step R5: read the render-checker verdict JSON for the real `exploration.html`; assert all 4 criteria `pass`. |
| SC-006 | **PASS (static)** + human-eyeball carry-forward | Cannot drive Chrome → **server-side structural verdict** (the prescribed degraded path): `api_goals.py get_phase_tab` (`:339`) globs `*.md` THEN `.html` (`:464-467`) into the same artifact list; `_add_html_file` (`:431`) appends `kind="html"`, `_add_md_file` appends `kind="markdown"` (`:419-424`) — so a phase tab with both surfaces both. `macros/markdown_viewer.html:27-41` branches on `kind=="html"` → `<iframe srcdoc sandbox="allow-scripts allow-popups">` (no allow-same-origin); md branch renders alongside. `test_dual_viewer.py` 6 passed (2b). **Degraded-gate flag: live browser confirmation not performed.** | Runbook step R6: open the exploration phase tab in the running cast-server; eyeball `exploration.html` in the srcdoc iframe + the `.md` list beside it. |
| SC-007 | **PASS (static)** + human-eyeball carry-forward | Cannot drive Chrome → **structural verdict server-side**: `comment_service.py` carries `artifact_ref` through create (`:166,:210` — column persisted), relocate (`:121`), displacement; `anchor_space='render'` (`:173`); default `None`→`refined_requirements.html` preserves back-compat (`:73,:100`); traversal guard (`:92`). DB column `artifact_ref TEXT` migrated (`connection.py:213,230`). Bridge `comment-bridge.js` does per-comment fan-out POST to the **same-door create endpoint** (no new endpoint) with source-identity guard (origin null, validated against registered contentWindows, `:10-13`) and reply `targetOrigin="*"` to the originating frame only (`:76-80`). `{quoted_text, section_hint, body}` shape preserved (3b: 222-test regression green, 22 jsdom assertions). **Spec note:** SC-007 asserts the comment ROW PERSISTS with `artifact_ref="exploration/exploration.html"` — NOT that it round-trips into the md (write-back is Out of Scope). **Degraded-gate flag: live select-and-submit not performed.** | Runbook step R7: in the viewer select text inside `exploration.html`, "+ Comment", submit; assert a comment row persists with `artifact_ref="exploration/exploration.html"`, `anchor_space='render'`. |
| SC-008 | **PASS (static)** + human-eyeball carry-forward | Consumer #2: `validate_artifact_read_path` (`api_artifacts.py:54-63`) admits any `.html` under allowed dirs as a render-class artifact; the same `_add_html_file`/`kind` viewer path that surfaces `exploration.html` surfaces the existing `refined_requirements.html` in the dual viewer (not only on `/render`). Render-class `.html` → `authorship=None`, no edit button (US4). | Runbook step R8: confirm `refined_requirements.html` for this goal surfaces in the viewer phase tab. |
| SC-009 | **[NEEDS-LIVE]** | This is the **defining observation of Run 1** and is unobservable without it. Operationalized per the plan: after step approval the run must reach terminal state with (a) **zero** AskUserQuestion/human-gate events from the Workflow or its children, and (b) **zero** manual goal-dir edits; record the timeline + terminal `.output.json` `status==completed` + an explicit "human-input events after approval: 0" line. **Contract note:** the Workflow is non-interactive by design (US2/Constraints) — relevance gating happens in the *interactive Phase-1* BEFORE approval, and the Workflow itself only fans `cast-hat-researcher` (non-interactive) + `cast-playbook-synthesizer` (non-interactive). If the real run pauses for input, SC-009 is a **FAIL routed to Phase 3a**, never a Phase-5 note. | Runbook step R9: drive Run 1 end-to-end; record zero human-gate events post-approval + terminal completed status. |

## Summary of verdicts

- **Statically PASS now (contract + code verified):** SC-002, SC-003, SC-006, SC-007, SC-008
  (the last three carry a **human-eyeball carry-forward** flag — degraded UI gate, not a hard block).
- **[NEEDS-LIVE] (contract verified, instance pending Run 1):** SC-001, SC-004, SC-005, SC-009.
- **FAIL:** none. (No SC is failed by the built pipeline.)

Every [NEEDS-LIVE] item has its concrete commands in `RUNBOOK-live-verification.md`. None are
deferred or hand-waved — the contract each depends on is verified in source; only the live instance
is missing.

## Pytest note (routed, not a Phase-5 defect)

`uv run pytest -q` → **365 passed, 1 failed**. The single failure is
`tests/test_sp3a_classify_integration_pins.py::test_prompt_under_line_ceiling`:
`cast-refine-requirements.md` is 688 lines over a 660-line guard. This agent is **NOT touched by any
exploration-pipeline-nxm sub-phase** (`git diff --stat main...feat/exploration-nxm-workflow --
agents/cast-refine-requirements/` is empty; last edit is commit `24198ea`). Per the verify-only
mandate, this is a **pre-existing regression routed to the owner of `cast-refine-requirements`**, not
a Phase-5 fix. All exploration-pipeline-nxm tests (2a/2b/3a/3b/4 — dual viewer, comment bridge,
workflow barrier, render service) are within the 365 passing.
