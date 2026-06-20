# Byte-Compatibility Check — `cast-high-level-planner` glob contract (US6 / FR-009)

**Verifier:** static / contract verification (no live Run-1 tree exists yet — instance check is in
the runbook). **Verdict: PASS (contract) — no shape regression in the md substrate.**

## The contract

`cast-high-level-planner.md` reads three globs, confirmed at execution time at **lines 115-117**
(the plan flagged the `:115-117` citation as possibly drifted — it is **accurate**, under the
heading `### Optional (enriches plan quality)` at `:114`):

```
:115  - exploration/research/*.ai.md   — Research files from 7-angle deep dives
:116  - exploration/playbooks/*.ai.md  — Synthesized playbooks with impact ratings
:117  - exploration/summary.ai.md      — Consolidated exploration summary
```

`:129` "Read exploration/summary.ai.md if present". These are **Optional** inputs — the planner
degrades to "a higher-level plan with more open questions" when exploration is absent rather than
erroring.

## Contract-severity reframing (reviewer correction, honored)

Because the globs are **Optional**, a byte-compat regression does **NOT crash** the planner — it
**silently degrades plan quality** (the planner ingests but produces a thinner plan that ignores the
fan-out). That makes this check **higher-value** and reframes a FAIL as *"ingested-but-ignored /
thinner plan"*, never *"missing-artifact error."* The optional live dispatch (runbook R-C) must
therefore inspect plan **QUALITY** for evidence the M-per-step research was used, not merely assert
"no missing-artifact error."

## Three structural confirmations

**(1) All three globs are bag-style `*.ai.md` and the new fan-out is additive.**
The new N×M research filename is `research/{NN}-{slug}-{hat-id}.ai.md` (`workflow.mjs:29`,
`cast-hat-researcher.md:90`); the old `cast-explore` filename was `research/{NN}-{step-slug}.ai.md`
(`cast-explore.md:201`). **Both match `research/*.ai.md`** — the glob treats the directory as a bag,
so going from 1-note-per-step to M-notes-per-step is purely additive. The planner "skims playbooks
for impact ratings… don't re-read all research" (`cast-high-level-planner.md`), so the research
fan-out lands in a glob it already treats as a bag — no shape assumption is violated by the larger
cardinality.

**(2) `playbooks/*.ai.md` and `summary.ai.md` keep the SAME shape `cast-explore` produces.**
The synthesizer is **UNCHANGED** (US5): `workflow.mjs:184,187` calls `cast-playbook-synthesizer`
(the same pre-existing agent `cast-explore` uses at `cast-explore.md:238`), writing
`playbooks/{NN}-{slug}.ai.md` — **byte-identical path shape** to `cast-explore`'s
`playbooks/{NN}-{step-slug}.ai.md`. `summary.ai.md` FORMAT is **Out-of-Scope to change** and is
assembled by the same synthesizer (`workflow.mjs:210-217`). Headings/shape are therefore preserved
by construction (same agent, same output template).

**(3) No path moved.**
- research dir: `exploration/research/` — same.
- playbooks dir: `exploration/playbooks/` — same.
- summary: `exploration/summary.ai.md` — same.
- Both pipelines write **one level deep**, no date-slug subdir (`cast-explore.md:81-82` forbids it;
  `workflow.mjs` writes the same flat layout). The planner's glob depth assumption holds.

## The one subtlety, explicitly handled

The research glob now matches **M notes per step** instead of 1. This is the only cardinality change.
It is absorbed by the bag-glob semantics (confirmation 1) and does **not** touch the two globs the
planner actually leans on for plan structure (playbooks for impact ratings, summary for the
consolidated read) — both of which keep `cast-explore`'s shape (confirmation 2). **The `-code.ai.md`
caveat:** `cast-explore` ALSO writes `research/{NN}-{slug}-code.ai.md` (`cast-explore.md:221`), so the
research bag already contained non-hat files before this work; the planner has always treated it as a
heterogeneous bag. The fan-out adds more files of the same `*.ai.md` shape to a bag that was never
homogeneous. No regression.

## Verdict

**PASS (contract).** The md substrate stays byte-compatible with `cast-high-level-planner`: all three
globs resolve over the new layout, the two structure-bearing globs (playbooks, summary) keep
`cast-explore`'s exact shape via the unchanged synthesizer, and the only change (research 1→M) is
additive to a glob already treated as a bag. **No upstream revision required.** A real shape
regression in `playbooks/*.ai.md` or `summary.ai.md` would be a **Phase-3a defect** (synthesizer was
to be unchanged) — none is present in the contract.

**Instance confirmation pending Run 1** (runbook R-C): glob-resolve over the real tree + dispatch
`cast-high-level-planner` read-only and confirm the produced `plan.collab.md` **references ≥1 playbook
impact rating or M-per-step research insight** (the "ingested-but-ignored" silent-degradation failure
mode is the real thing to catch, not a hard error).
