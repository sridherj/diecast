# sp4b output — `cast-comment-reanchor` agent + iteration loop + eval

**Status: COMPLETE.** All five success criteria met; the decision-#9 live eval gate passes.

## What was built

### 1. New 4th agent — `agents/cast-comment-reanchor/` (decision #2)
- `config.yaml` — the five canonical subagent keys exactly: `model: sonnet`,
  `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `timeout_minutes: 10` (+ `allowed_delegations: []`, correct — it is a leaf worker that
  dispatches nothing, matching the `cast-requirements-checker` precedent).
- `cast-comment-reanchor.md` — bare-JSON verdict worker. Input (from the parent's delegation
  context): displaced open comments `{id, quoted_text, section_hint, body}` + OLD content + NEW
  content. Output: EXACTLY ONE bare JSON object matching the canonical verdict schema in
  `_shared_context.md` (`{verdicts:[{comment_id, verdict, new_quoted_text, new_section_hint,
  confidence, reasoning}]}`), no prose, no fences, no `.output.json` envelope. Prompt invariants
  stated explicitly: never paraphrase/invent; `new_quoted_text` is always a verbatim substring of
  the new doc or `null`; **prefer `orphaned` over a low-confidence relocate** (decision #9's
  asymmetry — an orphan is surfaced & recoverable, a confident mis-placement is not).

### 2. Iteration-mode wiring — `agents/cast-refine-requirements/`
- Added a lean **"Phase 4: Iterate"** section (5-step API-driven loop) to
  `cast-refine-requirements.md`: detect open comments → address & write the `.collab.md` →
  `POST /versions` (read `displaced_comment_ids`) → dispatch `cast-comment-reanchor` (Agent tool,
  subagent mode) → apply verdicts through the same door (`relocate`, with a **422 → orphan
  downgrade**; `orphan`) → resolve what was fixed. A failed/timed-out/garbage dispatch is an
  explicit **no-op** (graceful degrade; comments stay in the tray; next cycle retries).
- Added `cast-comment-reanchor` to `cast-refine-requirements/config.yaml` `allowed_delegations`
  (intent-documenting, like the existing `cast-goal-classifier` entry — subagent dispatch does not
  consult the allowlist, but listing it keeps a future HTTP switch config-only).

  > ⚠️ **PROMPT-CEILING OVERAGE FLAGGED (per Step 4b.2 instruction — not silently trimmed).**
  > `cast-refine-requirements.md` is now **661 lines**, ~11 over the ~650 soft ceiling. No Phase
  > 1b/2 content was removed to make room. The Iteration-mode section is already minimal (the
  > dispatch/poll/apply mechanics are referenced out to `/cast-child-delegation` rather than
  > inlined). If sp7's allow-list re-audit wants the prompt back under 650, the cleanest lever is
  > moving the whole Phase 4 block to a referenced skill doc and leaving a one-line trigger — left
  > to sp7 since it owns the final `cast-refine-requirements` compliance sweep.

### 3. `bin/generate-skills` — run
Regenerated 72 SKILL.md files; `cast-comment-reanchor/SKILL.md` stub now exists under
`~/.claude/skills/`.

### 4. `/cast-agent-compliance` — delegated & reviewed
Verdict: **1 agent audited, 0 violations, 0 critical.** Config keys all exact. The bare-JSON
verdict output is **recognized as the documented carve-out** (classifier/checker precedent), not
flagged. `allowed_delegations: []` is correct (leaf worker, no dispatch) — not the empty-list
footgun. Structure matches the subagent-mode peers (no command wrapper / README / runs / tests,
identical to `cast-goal-classifier` & `cast-requirements-checker`). **Nothing to fix.**

### 5. `tests/eval_reanchor.py` — created, gate PASSES (decision-#9 validate-during-build)
Uses the frozen Phase-1 fixture + the sp2 `refined_requirements.v2-edit.collab.md` sibling with
three pre-seeded comments. Mirrors `eval_classifier_corpus.py` (live `claude -p --tools ""`
dispatch; offline `--verdicts` replay; `--structural-only` fast pre-check). Excluded from default
CI (the `eval_` prefix). Live run result:

```
[PASS] zero invented text (0 relocated verdicts with a non-verbatim quote)
[PASS] reworded comment 101 -> relocated(verbatim)   (FR-001 reworded between versions)
[PASS] deleted comment 102 -> orphaned                (cast-explore exclusion line removed)
[PASS] control comment 103 -> not orphaned            (unchanged Directional-Ideas bullet)
RESULT: PASS
```
The live verdicts were saved to `cast-server/tests/fixtures/reanchor_verdicts.json` for
deterministic offline replay (`--verdicts`). The embedded structural pre-check pins the five config
keys + the allow-list entry (the sp3c footgun) as a fast, model-free gate.

## Scope compliance
- ✅ **No cast-server runtime code touched** — only `agents/` + `cast-server/tests/eval_reanchor.py`
  (a test) + a test fixture. No services, routes, templates, or JS.
- ✅ Did not change the relocate/orphan endpoints (sp1 owns them; this loop only *calls* them).

## Files created / modified
| File | Action |
|------|--------|
| `agents/cast-comment-reanchor/config.yaml` | Create |
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` | Create |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify (+Phase 4 section; **661 lines, overage flagged**) |
| `agents/cast-refine-requirements/config.yaml` | Modify (+`cast-comment-reanchor` delegation) |
| `cast-server/tests/eval_reanchor.py` | Create |
| `cast-server/tests/fixtures/reanchor_verdicts.json` | Create (offline-replay fixture) |

## Handoff to sp7
- Record the `cast-comment-reanchor` I/O contract + bare-JSON carve-out in the spec.
- Re-audit `cast-refine-requirements`'s `allowed_delegations` footgun and decide whether to push
  the prompt back under the 650-line ceiling (move Phase 4 block → referenced skill doc).
