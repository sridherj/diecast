# sp3_reviewer_and_gate — Output

**Status:** completed
**Checkout edited:** `/data/workspace/diecast` (== `/home/sridherj/workspace/diecast`, same inode via symlink)
**Prompt line count:** 548 / 650 ceiling (was 492 after sp2; +56 lines)

## What was done

Landed the **anti-one-shot** edits of Phase 1b (plan activities 8 and 7) into the
`cast-refine-requirements` agent prompt. All edits target the single file
`agents/cast-refine-requirements/cast-refine-requirements.md`.

### Activity 8 — Independent adversarial reviewer subagent (new Step 2.5)
- Inserted **Step 2.5: Independent Adversarial Review (fresh-context reviewer)** between Step 2.4
  (Exit Conditions) and Phase 3 — i.e. **after** the questioning loop and **before** the final
  draft presentation / persist (Decision #2: user signs off on the reviewed version).
- **Dispatch:** a fresh-context **Claude Code Agent tool** general-purpose subagent whose prompt
  contains **ONLY the draft document**, never the conversation. NOT a Diecast HTTP delegation.
- **Rubric (~36 lines, compact table):** scores 1–10 on five dimensions —
  **Completeness / Consistency / Clarity / Scope / Feasibility** — and returns specific issues
  for every dimension scoring <7.
- **Convergence guard:** fix <7 issues, re-dispatch, **max 3 iterations**, then log remaining <7
  issues to Open Questions as `[NEEDS CLARIFICATION: …]` (never exceeds the 7-question budget on
  the reviewer's behalf).
- **Stub-skip (Decision #6):** `review skipped: stub-sized input` for <200-word / Stage-1 inputs.
- **Fail-soft:** `independent review skipped: <reason>` and proceed — the reviewer never blocks
  refinement. Notes that on a skipped/failed run there is then NO adversarial pass at all (accepted
  per Decision #3) while evidence-quoting + zero-silent-failure invariants still hold.
- Tombstone note kept legible: "the activity-5 meta-pass was cut (Decision #3); do not add a
  second rubric." No meta-pass logic re-introduced.

### Activity 7 — `/spec` HARD GATE (Workflow header + Step 3.0 + Step 1.5 amendment)
- **HARD-GATE sentence** added verbatim near the top of the `## Workflow` section: "Do NOT write
  `refined_requirements.collab.md` in your first response. Always present the (fully reviewed)
  draft and give the user at least one opportunity to react before persisting — even when every
  section is medium+ confidence."
- **Step 3.0: Present the reviewed draft and wait (HARD GATE)** added at the start of Phase 3.
  Interactive runs present the post-Step-2.5 draft and wait for ≥1 go-ahead before writing.
- **Headless / HTTP-delegated runs (Decision #1):** explicitly documented as **supported** — the
  agent does NOT wait at the gate; after the Step 2.5 reviewer it **persists automatically** and
  records `auto-persisted: non-interactive run` in the output contract.
- **Step 1.5 exit amended (Step 3.3):** the old "If all sections are medium+, skip directly to
  Phase 3" now reads "skip the *questioning loop*, but still run the independent reviewer (Step
  2.5), then present the draft and wait for one go-ahead (Step 3.0) before persisting" — the
  zero-interaction one-shot is gone; the one extra round-trip on clean runs is accepted by design.

## Verification (all green)
- Validation greps: five-dim rubric ✓, convergence guard (max 3 iteration) ✓, stub-skip note ✓,
  fail-soft note ✓, HARD-GATE sentence ✓, headless auto-persist ✓, Agent-tool dispatch noted ✓,
  no meta-pass logic ✓.
- `pytest tests/test_b1_domain_search.py` → **8 passed**. Step 2.2.1 (Domain Web Search) untouched
  (confirmed via `git diff`).
- `config.yaml` **git-clean** — no `allowed_delegations` added (the reviewer is an Agent-tool
  subagent, not an HTTP child).
- Step ordering confirmed: Step 2.4 → **Step 2.5 reviewer** → Phase 3 → **Step 3.0 gate** →
  Step 3.1 write. Reviewer runs before the final presentation, not after persist.
- Exactly ONE adversarial rubric (no meta-pass twin).
- Line count **548 / 650** (102 lines of headroom).

## Notes for dependent sub-phases
- **sp4 (regen + pins):** `bin/generate-skills` was **NOT** run here (batched to sp4). New pins in
  `tests/test_phase1b_prompt_pins.py` should anchor the sp3 additions: the five dimension names
  (`Completeness`/`Consistency`/`Clarity`/`Scope`/`Feasibility`), `max 3 iterations`,
  `review skipped: stub-sized input`, `independent review skipped`, the HARD-GATE
  "in your first response" sentence, and `auto-persisted: non-interactive run`.
- **sp5 (live verification):** exercise both the interactive gate (must present + wait) and the
  headless path (must auto-persist + record `auto-persisted: non-interactive run`).
- Files modified (one file): `agents/cast-refine-requirements/cast-refine-requirements.md`.
