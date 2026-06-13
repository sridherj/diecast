# Review Summary: refine-req-v2-phase4

**Review mode:** inline SMALL-CHANGE pass (max ~1 issue/section), performed by the planning agent.
The delegation ran fully autonomous (no interactive `/cast-plan-review` child dispatch — a recorded
sensible default; the plan's Open Questions are "None blocking"). Each sub-phase already carries the
plan's per-WP design-review notes folded into its Execution Notes / Success Criteria.

## Open Questions

**None blocking.** The two genuine forks (re-anchor-on-save mechanism; the re-anchor agent's home)
were resolved interactively by the owner on 2026-06-11 — lazy + surfaced tray, and a standalone 4th
agent `cast-comment-reanchor`. Everything else is locked (decisions #1/#7/#8/#9) or inherited from
prior-phase canon. No human input is required to begin execution.

## Cross-cutting decisions recorded during planning (sensible defaults)

1. **WP-B split into sp2 (pure engine) + sp4a (wiring).** Rationale: the plan calls WP-B "fully
   parallel from day one," but its template + `api_requirements.py` edits collide with sp1/sp3/sp5.
   Splitting lets the genuinely-pure `block_diff`/`diff_render` run parallel to sp1, while the
   shared-file wiring serializes after sp3. This is the only deviation from 1:1 WP→sub-phase mapping.
2. **`api_requirements.py` is edited by sp1 → sp3 → sp4a sequentially** (never in parallel). The
   manifest's two parallel pairs (sp1∥sp2, sp4a∥sp4b) are verified file-disjoint.
3. **`_theme.css.j2` diff classes default to sp2** (so `render_diff` is testable end-to-end there);
   sp4a may absorb them instead if sp2 is kept strictly module-only. Either is acceptable; both keep
   the classes token-only and landed before sp4a's golden cut.
4. **Goldens cut twice on `document.html.j2`:** sp4a (toggle) then sp5 (comment layer). The diff
   golden (sp4a) and the render goldens (sp5) are separate sets — keep them distinct.
5. **No `/cast-plan-review` child dispatch** in this autonomous run; inline review used instead.

## Review Notes by Sub-Phase

### sp1 — comment_service + same-door API
- The FR-013 dual-assertion test is the load-bearing gate; it must prove ONE code path, not two
  handlers that happen to write the same row. Test asserts structural row-equality modulo
  `author_kind`/`id`. ✓ captured.
- Watch the import edge: `comment_service.create_comment` calls
  `requirement_version_service.get_current` for the default version; sp3's `create_next` imports
  `comment_service`. Confirm no import cycle at module load (noted in sp3).

### sp2 — block_diff engine
- Partition invariant is the single most important assertion in the whole plan (silent-loss safety
  net). ✓ first-class in the test list.
- The no-LLM/no-IO source pin lives here (engine purity) and is reinforced by sp6's package.json pin.

### sp3 — create_next + archive
- The as-of reconstruction (`_state_as_of`) is the subtle correctness point; pinned with the
  three-version resolve-after-archive scenario. ✓.
- `POST /versions` is JSON-only (agent/loop surface) — negotiation not required, but slug-404
  consistency is. ✓ noted.

### sp4a — diff-view wiring
- Coordination risk: sp4a and sp5 both edit `document.html.j2`. Mitigated by ordering (sp5 depends
  on sp4a) and explicit "add ONLY the toggle here" scope. ✓.
- Canonical-render zero-`id` test must stay green; transient `diff-{n}` ids are diff-view only. ✓.

### sp4b — reanchor agent + loop
- Real risk: the `cast-refine-requirements` ~650-line prompt ceiling. The plan mandates overflow →
  referenced skill doc + flag, never silent trimming. ✓ surfaced as an explicit success-criterion
  branch.
- The agent never writes state; the 422 verbatim backstop + orphan-only fallback guarantee zero
  silent mis-placement. ✓.

### sp5 — vanilla-JS comment layer
- ~150-line budget + package.json pin keep the no-framework promise honest; overflow is escalation
  evidence, not license. ✓.
- No-browser caveat for visual checks recorded (project default: static verdict + human carry-forward).

### sp6 — guards + pins
- The defining property is ZERO production change; a success criterion explicitly asserts
  `git diff --name-only` shows only test files. ✓.

### sp7 — spec + e2e + compliance
- Spec names must match the Naming Contract token-for-token (Phase 5 cites it). ✓ called out.
- Findings route back to the owning sub-phase; sp7 never patches production. ✓.

## Residual risks carried from the plan (no action needed pre-execution)

- Re-anchor subagent mis-placement (accepted cost of decision #1) — mitigated by verbatim
  validation, orphan-preference prompt, `eval_reanchor.py`, and auditable `relocated` events.
- Quote-location across inline tags — TreeWalker concatenation + an e2e case quoting across bold;
  a miss degrades to the tray.
- `block_diff` duplicate-heading mis-pairing — document-order pairing is deterministic and tested;
  worst case is an add+remove instead of a modified (annoying, never lossy).
