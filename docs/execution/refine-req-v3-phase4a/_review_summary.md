# Review Summary: refine-req-v3-phase4a

`/cast-plan-review` run in **SMALL CHANGE** mode (≤1 issue per section) over each sub-phase, under
**HOLD scope**. Every finding auto-decided against the binding owner decisions in
`decisions-so-far.md` (per the granted autonomy: "make the right decisions at review unless you need
me"). **No finding re-opens an owner-resolved decision** (one checker; loop bounded only by the high
anti-infinite-loop ceiling; the structural-violation OVERRIDE; deterministic only on literal
no-output; prefer-valid terminal ranking).

Summary: **5 issues found / 5 resolved / 0 deferred** (Architecture 2, Code Quality 2, Tests 1).
One resolution was folded back into a plan file (4a-2 prefer-valid precedence); the rest are
clarifications already covered by the written plans, recorded here for traceability.

## Open Questions

**None blocking.** Two deliberate deferrals carried from the source plan (decisions, not omissions):
1. **[USER-DEFERRED → RESOLVED] model tier** — `opus` confirmed 2026-06-12 for the checker; the
   knob is a later tune-down review, zero plan edits.
2. **Human-review consumption surface** — the flagged-renders LIST is **Phase 5d** (owner-resolved);
   4a is recording-only.

## Review Notes by Sub-Phase

### 4a-1 (checker + verdict module)
- **Architecture ✓** — gate computed code-side in `checker_verdict.py`, not trusted from the agent;
  pure module beside `maker_gate.py`. No finding.
- **Code Quality — gated-token matching brittleness.** *Finding:* "a `missing[]` entry containing a
  gated token (`job`/`outcome`/`scope`)" via naive substring could mis-match (e.g. a token embedded
  in an unrelated word). *Resolution:* match against a normalized token set (lowercased, word-bounded)
  pulled from a module constant the test references — already mandated in §4a1.4 ("pull the gated-token
  set out as module constants"); tightened to "word-bounded match," recorded here. No re-open.
- **Tests — the "every error issue contributes ≥1 `rework_feedback`" rule is a PROMPT rule, not a
  code rule.** *Finding:* it can't be unit-tested in `checker_verdict.py`. *Resolution:* correct by
  design — it is asserted at the eval/smoke layer (4a-3 `eval_quality_gate.py` + the 4a-1 smoke run),
  not in the pure-module test. No action.
- **Performance** — n/a (pure parse module).

### 4a-2 (quality loop in the service)
- **Architecture — prefer-valid precedence in the MIXED case (valid-but-unscored + broken-but-scored).**
  *Finding:* the policy table's rows covered "≥1 scored valid", "none valid", and "all unscored" but
  left the cross case (a valid-unscored attempt coexisting with a broken-scored attempt) implicit.
  *Resolution (FOLDED INTO THE PLAN, §4a2.2):* a structurally-valid attempt always outranks a broken
  one regardless of score; among valid, prefer scored > unscored > latest; a valid-but-unscored
  attempt serves with `checker_unavailable`, never `structural_violation`. Consistent with the
  owner-confirmed prefer-valid tiebreak — no re-open.
- **Code Quality — `schema.sql` + migration dual-write consistency.** *Finding:* the four flag
  columns are added in two places (the CREATE TABLE in `schema.sql` and the additive migration).
  *Resolution:* this is the established `test_schema_migration.py` pattern (fresh DB from `schema.sql`
  + existing DB via migration must converge); §4a2.7's migration test asserts exactly that
  convergence. No action.
- **Tests — reaper-extension not directly asserted.** *Finding:* 4a registers the checker stage in
  the stage-timeout list but no test pins that the derived ceiling grew. *Resolution:* low value —
  the reaper formula is Phase 3's and already tested there (3c T3); 4a's contribution is data (one
  more registered stage), not logic. A one-line assertion that the registered stage list contains the
  checker timeout is sufficient and noted in §4a2 manual checks. No blocking action.
- **Performance ✓** — the A2 envelope-stamp keeps the 4s poll off the `render_jobs` table (P1); no
  hot-path DB round-trip reintroduced. No finding.

### 4a-3 (spec + live evals + fault-injection gate)
- **Architecture ✓** — eval imports the production gate (one implementation); live scenarios run
  against scratch state only. No finding.
- **Code Quality ✓** — no copied gate logic; the `eval_` prefix keeps CI from collecting the live
  harness. No finding.
- **Tests / Process — spec text must record the OVERRIDE, not the source plan's RATIFIED fork.**
  *Finding:* the source plan's FR-006 prose pre-dates the owner override; a mechanical
  `/cast-update-spec` could re-record the stale text. *Resolution:* §4a3.5 delta #3 + the Execution
  Notes explicitly require the FR-006 text to reflect the override (literal-no-output-only;
  structurally-broken servable+flagged) and to correct the delta before approving. The inline
  diff-review gate is the backstop. No re-open.
- **Performance** — n/a (spec/eval sub-phase).

## Cross-Cutting Confirmation

- The **FORK RESOLUTION OVERRIDE** is encoded consistently in all three layers it touches: the
  checker treats structurally-broken attempts as scoreable (4a-1 has no structural awareness by
  design — it only judges the artifact), the loop scores+serves+flags them (4a-2 §4a2.2), and the
  spec records the override (4a-3 delta #3). No layer silently re-introduces the deterministic-on-
  structural-failure path.
- **No silent failures:** every row of the `decide_quality` policy table maps to a recorded job
  state + reason; the SC-008 / override / checker-unavailable tests each assert NOT-the-deterministic
  -page directly.
