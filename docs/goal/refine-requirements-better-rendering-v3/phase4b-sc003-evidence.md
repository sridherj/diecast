# Phase 4b — SC-003 Comment-Survival Sign-off Evidence

> Written by sub-phase **4b-4** (terminal). Records the SC-003 evidence that, with open comments
> present, a maker regenerate leaves every comment anchored with **zero new orphans** — and that the
> diff-narration trust boundary holds. Spec of record after this sub-phase:
> `docs/specs/cast-requirements-render.collab.md` **v6** (US19–US20 + US13 S4, FR-041–FR-046,
> SC-017–SC-018).
>
> **Run mode: autonomous (deterministic gate blocks; live LLM is a carry-forward).** Per the
> project's no-live-LLM-block convention (recorded in `phase4a-gate-evidence.md`), the **deterministic
> half** of SC-003 is the blocking gate and is fully exercised here against scratch goals + throwaway
> `db_path` (the 1b test-bed discipline — never the live house DB, never a real goal's
> `refined_requirements.html`). The **live `claude -p` maker** render is a non-blocking human-eyeball
> carry-forward (autonomous runs never gate on a stochastic LLM).

## Why SC-003 is a deterministic property

The shaping insight (Phase 1, sharpened in `_shared_context.md`): the comment + version layer is
**entirely source-side** — comments anchor to a verbatim quote validated against
`refined_requirements.collab.md`, versions snapshot the source, `block_diff` diffs parsed *source*
versions, displacement is a source-side string-find. A maker regenerate (same source, new HTML)
therefore **cannot** orphan a comment at the DB layer. The genuine exposure is silent
`<mark>`-placement loss on a paraphrased maker DOM (the JS `highlight()` returns `false`), closed by
the pure `check_comment_survival` gate. SC-003 is consequently provable deterministically; the live
maker only adds paraphrase-robustness evidence.

## The harness

`cast-server/tests/eval_sc003_survival.py` (the `eval_`-prefixed real-pipeline harness — excluded
from default CI, like `eval_maker_pipeline_e2e.py` / `eval_quality_gate.py`). Every block drives
**real** service / pipeline code; no behaviour is re-implemented. It reuses the proven gate-passing
source + maker markup + `FakeRunner` from `test_render_job_service` (no fork) — the same fixtures
`test_quality_loop` pins the loop with.

    uv run python tests/eval_sc003_survival.py            # deterministic blocking gate
    uv run python tests/eval_sc003_survival.py --live     # + one real claude -p maker (carry-forward)

## Block results (deterministic blocking gate — ALL PASS)

### Block 1 — same-source regenerate (render-only): survival green + zero DB changes

The REAL pipeline (`request_render` → `run_what → gate_what → run_how → gate_html → run_checker →
decide_quality → publish`) runs with the injected fake maker (clean WHAT + the proven passing HOW
HTML) over a goal carrying 2 open in-block comments.

| Check | Result |
|---|---|
| `published_by_maker` (`state == published`) | PASS |
| `survival_recorded` (`survival.json` written by `gate_html`) | PASS |
| `survival_passed` (gate green) | PASS |
| `all_comments_placed` (`placed` == every comment id) | PASS |
| `zero_unplaced` / `zero_violations` | PASS |
| `comment_rows_byte_identical` (full `requirement_comments` + `comment_events` snapshot before/after) | PASS |
| `no_new_version_or_narration` (version + narration row counts unchanged) | PASS |
| `canonical_md_untouched` (`refined_requirements.collab.md` bytes unchanged) | PASS |

→ **The maker render makes zero DB changes of any kind and every in-block mark places on the new DOM.**

### Block 2 — source-edit regenerate (the full loop): zero new orphans beyond the deleted block

Source edited so US1 is reworded+moved, FR-002 deleted, FR-001 untouched; three open comments anchor
one to each.

| Check | Result |
|---|---|
| `displaced_is_reworded_and_deleted` (`create_next.displaced_comment_ids` == {reworded, deleted}) | PASS |
| `untouched_never_displaced` | PASS |
| `relocate_backstop_predicate_holds` (new quote is a verbatim substring of the new source — the route's 422 backstop would accept) | PASS |
| `reworded_relocated_open_not_displaced` (after `relocate` it is open + no longer displaced) | PASS |
| `untouched_open_not_displaced` | PASS |
| `exactly_one_orphan` / `zero_new_orphans_beyond_deleted` (only the deleted-block comment is `orphaned`) | PASS |
| `new_render_survival_green` (`check_comment_survival` over the V2 render) | PASS |
| `relocated_and_untouched_marks_place` (`placed` == {relocated, untouched}) | PASS |

→ **A moved/reworded block is re-anchored (not dropped); only the genuinely-deleted block orphans;
the relocated mark places on the new render.** (The re-anchor *verdict* itself — `relocated` vs
`orphaned` — is the LLM half; the deterministic application + the verbatim backstop predicate are the
gate. The `cast-comment-reanchor` v2 agent producing those verdicts live is the carry-forward.)

### Block 3 — trust boundary: a diff can never show a change absent from the source

`save_narration` recomputes `summarize(diff_blocks(V1, V2))` server-side and validates every note key.

| Check | Result |
|---|---|
| `narration_accepted` (notes for every deterministic item stored) | PASS |
| `server_accepted_equals_recomputed_set` (accepted keys == server-recomputed `summarize().items` keys) | PASS |
| `bogus_key_rejected_all_or_nothing` (a note keyed to an absent change → `NarrationValidationError`, naming the offending key) | PASS |
| `rejection_did_not_persist_partial` (the prior good narration is intact; no partial write) | PASS |
| `has_deterministic_items` (the V1→V2 diff is non-trivial) | PASS |

→ **The posted narration contains only notes keyed to the deterministic items; the rendered panel can
show no change beyond `summarize()`'s items.**

## Regression sweep (default CI)

- `uv run pytest cast-server/tests/test_*.py` → **961 passed** (no regressions from the spec pass or
  the new harness).
- Targeted: `test_comment_survival.py test_schema_migration.py test_render_job_service.py
  test_quality_loop.py` → **70 passed**.
- The 2 pre-existing delegation reds are outside the `tests/test_*.py` default sweep and were **not
  touched** (per the sub-phase constraint).

## Live carry-forward — one real `claude -p` maker render

The live half **ran successfully** this session (the `--live` mode drives `ProductionAgentRunner` —
the real `cast-requirements-what → cast-requirements-how → cast-requirements-render-checker` `claude
-p` subagents through `request_render`). Over the same goal carrying 2 open in-block comments:

```
state = published
survival = { passed: true, violations: [], unplaced: [], placed: [1, 2] }
```

→ **The real, paraphrased maker DOM placed BOTH open comments with zero unplaced and zero violations**
— direct live confirmation of the deterministic claim. This is recorded as a carry-forward (a single
stochastic run is corroboration, not the blocking gate); the deterministic blocks above remain the
gate of record.

## Human-eyeball browser carry-forward (non-blocking)

Autonomous runs cannot drive a browser (project convention; see the no-browser-visual-gate memory).
The following are recorded as **non-blocking** human-eyeball carry-forwards — never a silent pass:

- **`.comment-unplaced` tray badge:** open a served render with an open comment whose quote was
  paraphrased away on the maker DOM; confirm the tray item shows the `.comment-unplaced` badge
  (read-time, derived) and the comment is grouped under "Needs re-anchor", not silently dropped.
- **`.diff-narration` panel:** open the "What changed" panel for a narrated version pair; confirm each
  note renders attached to its deterministic change row and that the panel shows no change row beyond
  `summarize()`'s items.
