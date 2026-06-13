# Shared Context: refine-req-v2-phase1b (Refinement Brain Upgrades — gbrain imports)

## Source Documents
- Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1b-refinement-brain.md`
- Cross-phase decisions: `docs/plan/refine-requirements-v2-decisions-so-far.md`
- Source mechanics (do NOT re-research): `goals/refine-requirements-v2/exploration/research/01-learn-from-existing-systems.ai.md` §2

## Project Background

Phase 1b ports portable quality upgrades from second-brain's `taskos-refine-requirements`
lineage and the wider gbrain/gstack skill family (`/spec`, `/office-hours`, `/plan-eng-review`)
into the `cast-refine-requirements` agent prompt. **It is a pure agent-prompt phase** — no
cast-server code, no parser, no DB — which lets it run in parallel with Phase 1 and de-risk
output quality before the render/comments/versioning build lands.

Planning corrected the playbook's "six imports" count: **two already exist** in the current
prompt (stage-adaptive framework at Step 1.3; exit conditions at Step 2.4 → these become
*verify-and-sharpen*), the **adversarial meta-pass was CUT** by plan review (Decision #3 — the
reviewer subagent subsumes it), and **three are new builds**: dated `## Decisions` section,
evidence-quoting mandate, scope-mode detection. Two owner-confirmed optional ports are in scope:
the `/spec` HARD GATE and the `/office-hours`-style adversarial reviewer subagent.

The outcome: every refinement run states its detected scope mode with quoted evidence, presents
confidence scores backed by verbatim quotes, records human decisions as dated Chose/Over/Because
rows captured at answer-time, gets a fresh-context adversarial reviewer score **before** the
user's final go-ahead, and never emits the final file without showing the (fully reviewed) draft
first. `bin/cast-spec-checker` still exits 0; the prompt-pinning tests stay green.

## Codebase Conventions

- **Two checkouts exist** — `/data/workspace/diecast` and `/home/sridherj/workspace/diecast`.
  **All Phase 1b edits land in `/home/sridherj/workspace/diecast`** (the external project
  checkout per goal config). The owner reconciles to main as usual. Work only in this checkout.
- **The agent prompt is the deliverable.** Almost every edit targets one file:
  `agents/cast-refine-requirements/cast-refine-requirements.md` (434 lines today).
- **Integrate into existing steps** (1.3, 1.5, 2.1, 2.4, 3.x) — do NOT append parallel sections.
  Hard ceiling: **~650 lines.** If the file passes ~650 lines, stop and trim before adding more.
- **Generated skills:** the user-facing skill is generated. After prompt edits, run
  `bin/generate-skills` so `~/.claude/skills/cast-refine-requirements/SKILL.md` regenerates
  (pre-existing files auto-backup to `.cast-bak-<timestamp>/`).
- **Dates come from the harness** `currentDate` context value — never fabricate timestamps.

## Key File Paths

| File | Role |
|------|------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | The agent prompt — primary edit target (sp1–sp3) |
| `templates/cast-spec.template.md` | Canonical spec shape, checker-enforced — gains `## Decisions` (sp2) |
| `agents/cast-spec-checker/cast-spec-checker.md` | Shape-rules doc — gains a one-line note recognizing `## Decisions` (sp2) |
| `bin/cast-spec-checker` | The deterministic checker — **NEVER modified**; tolerates additive H2s |
| `bin/generate-skills` | Regenerates user-facing SKILL.md from the agent prompt (sp4) |
| `tests/test_b1_domain_search.py` | Existing pin: "Domain Web Search" must survive, numeric caps must NOT reappear |
| `tests/test_phase1b_prompt_pins.py` | NEW pinning test for the Phase 1b anchors (sp4) |

## Current Agent-Prompt Anchors (line numbers approximate — re-grep before editing)

| Anchor | Where |
|--------|-------|
| `#### Step 1.3: Detect Stage and Select Framework` | stage signal table — sp1 verify + add scope-mode table |
| `#### Step 1.5: Run Sufficiency Check` | confidence assignment — sp2 evidence-quoting |
| `#### Step 2.1: Present Draft` | draft presentation — sp1 (scope mode), sp2 (quotes), sp3 (post-reviewer ordering) |
| `#### Step 2.2.1: Domain Web Search (B1, opportunistic)` | **DO NOT TOUCH** — pinned by `test_b1_domain_search.py` |
| `#### Step 2.4: Exit Conditions` | sp1 strengthen budget-exhaustion → zero-silent-failure |
| `#### Step 3.1: Write refined_requirements.collab.md` output template | sp2 insert `## Decisions` between `## Out of Scope` and `## Open Questions` |
| front-matter block (around `confidence:`) | sp1 add `scope_mode:` |

## Data Schemas & Contracts (copy verbatim where used)

- **`## Decisions` table shape:** `| Date | Chose | Over | Because |`, placed between
  `## Out of Scope` and `## Open Questions`. Population = **answer-time buffering**: the moment an
  `AskUserQuestion` fork resolves, append `{date, chose, over, because}` to an in-memory list
  (`date` = harness `currentDate`, `chose` = picked option, `over` = rejected option(s),
  `because` = stated/implied rationale). Render verbatim at persist. Never reconstruct from
  end-of-session memory. Agent-only defaults (the user never saw) do NOT go here — human choices
  only. 0-fork runs emit `*No decisions recorded this refinement.*` (stable section set for
  Phase 1's parser).
- **`scope_mode` front-matter field:** `scope_mode: reduction | hold | expansion` (additive;
  the checker does not lint front-matter keys).
- **Scope-mode vocabulary (identical to `cast-detailed-plan`'s Garry Tan table):**
  - "MVP" / "minimum" / "just enough" / "spike" / "v0" → **SCOPE REDUCTION** (fewer EARS
    scenarios, ruthless Out of Scope, defer-by-default)
  - no signals / balanced → **HOLD SCOPE** (default; scenario depth per the stage table)
  - "comprehensive" / "full-featured" / "dream" / "ideal" / "10x" → **SCOPE EXPANSION**
    (exhaustive edge cases, stretch items in Directional ideas)
- **Reviewer subagent rubric:** five dimensions scored 1–10 — **Completeness / Consistency /
  Clarity / Scope / Feasibility** — returns specific issues per dimension scoring <7. Dispatched
  via the **Claude Code Agent tool** (general-purpose subagent), prompt contains ONLY the draft
  document (not the conversation). Convergence: fix <7 issues, re-dispatch, **max 3 iterations**,
  then log remaining issues to Open Questions. Keep the rubric compact (~40 lines, inline).
- **HARD-GATE sentence (verbatim, near the top of the Workflow section):** "Do NOT write
  `refined_requirements.collab.md` in your first response. Always present the (fully reviewed)
  draft and give the user at least one opportunity to react before persisting — even when every
  section is medium+ confidence."

## Pre-Existing Decisions (from the plan's Decisions appendix — binding)

- **#1 (owner override):** HARD GATE applies on **interactive runs only**. Headless /
  HTTP-delegated runs (no human) auto-persist after the reviewer subagent and record
  `auto-persisted: non-interactive run` in the output contract. Headless is explicitly supported.
- **#2:** The reviewer runs **BEFORE** the HARD-GATE draft presentation, so the user signs off on
  the version that actually persists.
- **#3:** The adversarial meta-pass (activity 5) is **CUT**. The reviewer subagent is the sole
  adversarial pass. Activity number kept as a tombstone for cross-references.
- **#4:** Decisions table is buffered at answer-time, rendered verbatim at persist (no end-of-
  session reconstruction).
- **#5:** Add `tests/test_phase1b_prompt_pins.py` (no meta-pass anchor).
- **#6:** Reviewer **skips <200-word / Stage-1 stub** inputs with a "review skipped: stub-sized
  input" note.

## Relevant Specs

No registered spec in `docs/specs/_registry.md` covers the refinement agent's I/O (verified at
planning time — closest specs are runtime/delegation contracts, unaffected: no HTTP delegation is
added). The behavior contract for the spec surface IS `templates/cast-spec.template.md` +
`agents/cast-spec-checker/cast-spec-checker.md`. The `## Decisions` template change must be
**additive-optional**: `bin/cast-spec-checker` REQUIRED_SECTIONS = exactly four (User Stories,
Functional Requirements, Success Criteria, Open Questions); R1 only asserts required-section
*presence* and never rejects extra H2s (verified). No `/cast-update-spec` run is needed.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1_detection_brain | Sub-phase | — | sp2, sp4, sp5 | none (edits the prompt) |
| sp2_evidence_and_decisions | Sub-phase | sp1 | sp4, sp5 | none (edits the prompt + template) |
| sp3_reviewer_and_gate | Sub-phase | sp2 | sp4, sp5 | none (edits the prompt) |
| sp4_regen_and_pins | Sub-phase | sp3 | sp5 | none |
| sp5_verification_refinements | Sub-phase | sp4 | — | none |

**No parallelism and no decision gates.** sp1–sp3 all mutate the single agent-prompt file, so
they are strictly sequential to avoid edit conflicts; sp4 regenerates/pins what sp1–sp3 wrote;
sp5 exercises the finished prompt live. The plan's Build Order is the source of this ordering.
