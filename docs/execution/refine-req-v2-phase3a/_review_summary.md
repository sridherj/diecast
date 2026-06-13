# Review Summary: refine-req-v2-phase3a

> Self-review pass (autonomous run — the interactive `/cast-plan-review` gate is skipped per the
> delegation's "proceed fully autonomously, ask no questions" directive). Lightweight SMALL-CHANGE
> lens: coverage, file-conflict safety, decision traceability.

## Open Questions
**None blocking.** The plan itself records "Open Questions: None blocking" — the only genuine fork
(how an LLM checker "runs in CI") was resolved by owner decision #1 (golden snapshots in default CI;
checker as an `eval_` harness). Two non-blocking flags carried forward, not questions:
1. **Stale FR-008** in `refined_requirements.collab.md` (superseded by plan-review decision #1 / thin
   spine). The render emits no ids/anchors; goldens assert their absence. Owner may annotate the
   requirements doc at leisure — does not block execution.
2. **`/preso/review` path-validation housekeeping** — the existing route builds a path from the raw
   slug without DB validation. Flagged as a follow-up **outside** this phase; sp4 does the right
   thing for the *new* route (`get_goal()` validation → 404) without touching `preso_review`.

## Work-Package → Sub-Phase Coverage (complete)
| Plan WP | Sub-phase | Covered |
|---|---|---|
| A — Visual theme + document template | sp1 | ✅ |
| B — Block-recipe render engine | sp2 | ✅ |
| C — Goal Card + classification pill | sp3 (merged with D) | ✅ |
| D — Disclosure boundary + WHAT-before-HOW | sp3 (merged with C) | ✅ |
| E — Serve + regenerate | sp4 | ✅ |
| F — Checker + zero-click + goldens + eval | sp5a | ✅ |
| G — Spec lockstep + FR-007 guard | sp5b | ✅ |

## Plan-Review Decision Traceability (#1–#5 all threaded)
- **#1 (`is_stub` in Phase 1 pkg):** captured as an External Precondition + sp2 imports it, never
  redefines. ✅
- **#2 (run `/cast-agent-compliance` on the checker):** sp5a Step 5a.3 (delegation line). ✅
- **#3 (Goal Card heuristics in `goal_card.py`):** sp3 Steps 3.1–3.2 + isolated unit tests. ✅
- **#4 (rescue-path tests + goldens):** sp2 behavioural tests + sp5a rescue goldens (missing/garbage
  classification, stub), each asserting `RenderResult.warnings`. ✅
- **#5 (reuse one `markdown.Markdown()` + `.reset()`):** sp2 Step 2.3 + `test_markdown_instance_reused`. ✅

## Suggested-Revision-to-Prior-Phase preconditions (carried into `_shared_context.md`)
- Phase 2 `validate_classification` must ignore unknown persisted keys (`confirmed_by`,
  `classified_at`, `taxonomy_version`) without phantom coercion warnings.
- Phase 1/2 `EVIDENCE` + `DECISION` BlockKinds must have landed (sp2 hard-stops otherwise).
- Phase 1 `is_stub` + `STUB_WORD_THRESHOLD` canonical home.

## Parallel-Safety
sp5a ∥ sp5b verified file-disjoint (see `_manifest.md` → Parallel-Safety Audit). C and D were
*merged* into sp3 precisely because they edit the same `document.html.j2` + `renderer.py` and could
not be safely parallelized as separate sessions (the plan says "coordinate, don't serialize").

## Review Notes by Sub-Phase
- **sp1:** Token-drift pin + hex-scan tests are the safety net for the inlining deviation from
  Playbook 05 Step 2 — written alongside the CSS, not after. No concerns.
- **sp2:** Determinism (no timestamps) is the golden precondition; `EVIDENCE`/`DECISION` precondition
  flagged. No concerns.
- **sp3:** Honest-degradation rule (never pad a sparse card) and "WHAT never behind `<details>`" are
  structurally testable. No concerns.
- **sp4:** Atomic write + 404-validates-slug (path-traversal kill) + never-writes-`.collab.md`
  all pinned. Port-free-before-serve note added. No concerns.
- **sp5a:** "Zero clicks" enforced as an extractor-input property; gate is the boolean, not the
  score; eval harness excluded from default CI. No concerns.
- **sp5b:** Spec names must match the Naming Contract verbatim (Phase 4 cites it); records the
  generated-render classification + checker carve-out without editing the conventions/delegation
  specs. No concerns.
