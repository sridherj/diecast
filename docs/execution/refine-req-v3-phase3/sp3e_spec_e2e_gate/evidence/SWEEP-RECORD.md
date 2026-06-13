# Sub-phase 3e — two-family end-to-end sweep record

Driver: `cast-server/tests/eval_maker_pipeline_e2e.py` (eval-harness; real `claude -p` opus maker, NOT
default pytest). Two real, classified family sources from the spike-1a corpus:

- `new_initiative` → `docs/goal/.../refined_requirements.collab.md` (family 0.9)
- `bug_fix` → `docs/goal/.../spikes/1a/fixtures/goal-card-markdown-leak.collab.md` (family 0.95)

## Result matrix

| Check | new_initiative | bug_fix (run 1) | bug_fix (run 2) |
|---|---|---|---|
| `check_html` passed | ✅ (0 violations) | ❌ (FR-001, SC-001 carriage) | ❌ (FR-001, SC-001 carriage) |
| `served_by` | `maker` | `structural_violation` | `structural_violation` |
| job terminal status | `published` | `flagged` | `flagged` |
| canonical refs present (anchor labels) | 31 / 31 | 7 / 7 | 7 / 7 |
| DOM contract (0 real `id=`/`data-block-anchor`) | ✅ | ✅ | ✅ |
| single self-contained file | ✅ | ✅ | ✅ |
| no external HTTP fetch | ✅ | ✅ | ✅ |
| family headings, no US/FR/SC slot names | ✅ | ✅ | ✅ |
| canonical `.collab.md` never written | ✅ | ✅ | ✅ |
| generating → ready convergence | ✅ | ✅ | ✅ |

Heading sets are visibly distinct and family-appropriate (e.g. new_initiative: "Sixty-second cold
read", "Best attempt, flagged", "Cache hit, no model call"; bug_fix: "How we prove it's fixed",
"What the fix must leave untouched", "Zero literal markdown survives…").

## What the gate proved

**The Phase-3 pipeline contract is fully proven, including the override branch:**

1. **Clean maker happy path** — `new_initiative` published a bespoke, gate-passing render (`served_by:
   maker`), every canonical id mapped, zero invented ids, DOM contract intact.
2. **Structural-violation OWNER OVERRIDE (the delta-#6 / FR-035 / US17 behavior) — proven LIVE** —
   `bug_fix` produced an extractable render that failed the verbatim-carriage gate after its one
   structural retry, so `publish` served the **flagged best attempt** (`served_by:
   structural_violation`, status `flagged`, reason in `error`) and the read path would inject the
   "needs review" badge. It did **NOT** fall to the deterministic page. *Surface, don't suppress.*
3. **FR-007 read-only guarantee** — the canonical `.collab.md` was byte-unchanged across every run
   (`--tools ""` makes it structural).
4. **Generating → ready** — a `wait=False` probe reported `generating`; after the job, the artifact's
   embedded `source-hash` matched current, so the status derivation reports `ready`.

## The one not-fully-green criterion (reproducible, surfaced — not suppressed)

The plan's success criterion **"both families pass `check_html`"** is **not** met: the production
`cast-requirements-how` agent **reproducibly paraphrased** the bug_fix family's **lead FR-001 and
SC-001** (two independent real-maker runs, identical violations) rather than carrying their source text
verbatim, tripping the **verbatim-carriage** gate (FR-034). The spike-1a baseline passed bug_fix only
**with a hand-authored maker brief**; the production pipeline runs from `agent.md` alone, with no brief.

This is an **agent-prompt-quality** matter in the 3a-owned `cast-requirements-how` agent — **not** a
pipeline, gate, or route defect — and 3e is explicitly *record-and-verify*, not re-implement (the plan
forbids changing pipeline/gate/route/agent code here). The architecture's designed safety net (the
structural-violation override) absorbed it correctly both times.

**Owner decision needed (see output.json `human_action_items`):** either accept the flagged bug_fix as
a valid, contract-correct demonstration of the override, **or** schedule a `cast-requirements-how`
prompt-hardening follow-up (push verbatim carriage for lead units) in Phase 3a/4a.

## Files

- `e2e-new-initiative.html` + `.check_html.json` — the clean maker pass.
- `e2e-bug-fix.flagged.html` / `.run2.html` (+ `.check_html.json`) — the two flagged best-attempts.
- `sweep-run1.summary.json` — the full machine-readable run-1 summary (both families + cross-family checks).
