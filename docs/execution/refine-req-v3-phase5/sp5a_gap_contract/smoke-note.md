# sp5a — `cast-requirements-gapfill` smoke note

> Per the sub-phase plan's "Validation Scripts (temporary)" item: a hand-run `claude -p` smoke of
> `cast-requirements-gapfill` over THIS goal's corpus (one answerable gap, one unanswerable),
> producing a parseable grounded-or-refuse doc. Recorded here, **not** in CI.

## Status: offline-verified ✓ · live `claude -p` smoke = human carry-forward

This run was autonomous (no interactive terminal; nested `claude -p` from inside the runner session
risks the `CLAUDECODE`/`CLAUDE_SESSION_ID` recursion the `ProductionAgentRunner._clean_child_env`
guard exists for). Per the standing "no-live-LLM-in-autonomous-gate → static verdict + human
carry-forward, never block" discipline, the **live** model smoke is left as a one-command human
carry-forward (below). The **grounded-or-refuse trust boundary it would exercise is already proven
deterministically** by the permanent suite — the live smoke only confirms the agent emits a
sentinel-wrapped parseable doc, which the parser tests pin from the other side.

### What the permanent tests already prove (the contract the smoke would re-confirm)

`cast-server/tests/test_render_job_service.py` (sp5a block), all green:

- **one answerable gap** → `_gf_supplied` doc parses, evidence verbatim-locates in the corpus
  allowlist, gap resolves `cr-proposed` (provisional) — `test_what_declared_gap_flows_to_gaps_state_cr_proposed`.
- **one unanswerable gap** → `_gf_refused` doc parses, gap resolves `unfilled-cannot-supply` —
  `test_gapfill_refusal_lands_unfilled_cannot_supply`.
- **fabricated evidence** (quote absent from the cited file) → server-side demotion to
  `unfilled-cannot-supply`, `evidence-validation-failed` on the row — `test_fabricated_evidence_demotes_to_cannot_supply`.
- **T2 verbatim-locate parity** (whitespace/smart-quote-only diff validates; substantive diff
  demotes) — `test_T2_*`.
- crash / garbage output → `unfilled-ask-failed`, render proceeds — `test_gapfill_crash_or_garbage_*`.

### Human carry-forward — the live one-shot smoke

When a human has an interactive shell with `claude` on PATH and a goal whose
`requirements.human.md` is present, run the agent tool-free exactly as the runner does:

```bash
GOAL=refine-requirements-better-rendering-v3
AGENT=agents/cast-requirements-gapfill/cast-requirements-gapfill.md
claude -p "$(cat <<'EOF'
Answer each open comprehension gap GROUNDED-OR-REFUSE from the grounding corpus below.
----- BEGIN OPEN GAPS -----
- gap_id: GAP-01
  question: "What upstream artifact does the gap-fill corpus allowlist draw from?"
  section_hint: "Grounding corpus"
- gap_id: GAP-02
  question: "What is the production latency budget of the gapfill subprocess in milliseconds?"
  section_hint: "Performance"
----- END OPEN GAPS -----
----- BEGIN GROUNDING CORPUS (the ONLY admissible evidence) -----
----- BEGIN CORPUS FILE requirements.human.md -----
The grounding corpus is the goal's own upstream artifacts: requirements.human.md,
research_notes.human.md, and an exploration summary when present.
----- END CORPUS FILE requirements.human.md -----
----- END GROUNDING CORPUS -----
Emit ONE YAML list between <!-- BEGIN GAPFILL --> and <!-- END GAPFILL -->, one entry per gap.
EOF
)" --append-system-prompt "$(cat $AGENT)" --model opus --tools ""
```

Expected: `GAP-01` → `supplied: true` with a verbatim `evidence.quote` from the corpus file;
`GAP-02` → `supplied: false` (the corpus states no latency budget — an honest refusal). The output
is one YAML list between the `<!-- BEGIN GAPFILL -->` / `<!-- END GAPFILL -->` sentinels.
