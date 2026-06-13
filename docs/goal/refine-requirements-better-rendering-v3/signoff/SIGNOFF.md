# Goal Sign-Off — Refine Requirements Better Rendering v3

> **Closing note for the whole goal.** Full detail (the eighteen-criterion sweep, the integration drift
> sweep, the carry-forward ledger) lives in `signoff/sc-sweep.md`. This note is the one-page verdict.

**Date:** 2026-06-12 · **Sub-phase:** 5d (terminal) · **Operating mode:** HOLD SCOPE · autonomous (no browser)

## Verdict

**The goal ships** — as a customer-facing render pipeline with its remaining apologies **stated
explicitly, never silently dropped**. v3 inverted the requirements render from a deterministic template
to an LLM **maker pipeline** (WHAT → gates → HOW → quality loop), gated it with an LLM comprehension+
visual checker, made comments and versions **survive** a varying render, and — this phase — made the
maker **fill genuine comprehension gaps by asking upstream, never fabricating**, reconciling obtained
detail back to canonical through the **unchanged** v2 change-request gate.

## What's green

- **Full suite:** `pytest cast-server/tests/` → **1067 passed, 9 skipped**, plus the **2 pre-existing
  delegation reds** (environment `goal.yaml`-missing fixtures, unrelated to v3, do-not-touch).
- **All eighteen success criteria swept** (SC-001…SC-018): sixteen fully green; SC-002 green with three
  honestly-surfaced HOW-layer flags; SC-016 advanced by the new flagged-renders list.
- **Gap machinery live and proven:** the `gaps[]` seam activated, the tool-free `cast-requirements-
  gapfill` grounded-or-refuse subagent, server-side `validate_evidence` (the trust boundary — "never
  fabricates" enforced, not promised), GATE-ALL gap-CR reconciliation through the byte-unchanged v2
  gate, the class-based `.rr-gap` markers. `test_gap_reconciliation.py` + `test_fr007_readonly_guard.py`
  full-gap-fill byte-identical extension green.
- **Integration drift sweep clean:** reaper ceiling + heartbeats extend to the gap stages; counters
  independent (A2/C6); C5 knobs landed + read; single-helper discipline holds (one `verbatim_locate`,
  one `strip_inline_markdown`, one `container_text_index`); checker amnesty line present; GATE-ALL
  applied; `change_request_service` byte-unchanged.
- **Specs reconciled:** `cast-requirements-render.collab.md` **v6→v7** (gap contract, marker vocabulary,
  nine-family record, flagged-list pointer resolved, new `linked_files`); `cast-requirements-
  roundtrip.collab.md` **v1→v2** (first real downstream emitter recorded, emitter-side only).
  `_registry.md` bumped; `bin/cast-spec-checker` exits 0 on both.
- **The minimal flagged-renders list shipped:** read-only on `/runs`, sourced from
  `render_job_service.list_flagged_renders()` over the 4a recording-only flag columns — **no new write
  path, no new column** (`git diff` shows no `render_jobs` schema change). It is the honest degraded-page
  signal the structural override makes load-bearing.

## What's flagged (the apologies, stated)

- **3 HOW-layer flagged family renders** — `bug_fix` (verbatim-carriage miss + id-in-headings),
  `pilot_poc` (HOW invented `SC-001`/`SC-002` ids), `random_idea` (HOW over-structured a thin doc into
  empty shells). Each served a flagged best-attempt — the correct shipped degraded state under the
  structural override — and now appears on the flagged-renders list. **None is a WHAT-vocab or
  recipe-shape defect; all three originate in the HOW layer.**
- **Human-eyeball carry-forwards** (non-blocking; autonomous runs can't drive a browser): nine golden
  renders side-by-side; the gated un-mark e2e; SC-006 discoverability; the badge eyeballs; SC-009
  browser-CI flows; SC-004 live kill; SC-005 live repeat-view; SC-012 manual swap.

## What stays deferred

- **`[USER-DEFERRED]` model-tier tune-down** for the four pipeline agents (opus is the confirmed start).
- **The human-review queue/triage UI** (4a open question — a future-goal owner call; the minimal list
  is the whole 5d surface).
- **The v2 human timed-read evaluation** (out of scope under HOLD).

## Principal post-sign-off follow-up — ✅ EXECUTED (2026-06-13)

The owner-recorded direction in `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
— the HOW-layer **CREATE/UPDATE-mode + readability-over-verbatim rework** — was **planned-properly-first
then executed as its own goal** (`refine-req-v3-how-update-mode`, HOLD SCOPE), exactly as decided. It is
no longer an open item.

**The three flagged families are now CLEAN.** The nine-family real-pipeline sweep
(`eval_family_sweep.py --golden`) is **9/9 published, served-by maker, `human_review=0`, `check_html`
green, zero empty shells, pairwise-distinct** — `bug_fix` / `pilot_poc` / `random_idea` re-render clean
and the six previously-clean families did not regress. Goldens under `signoff/golden/` regenerated to the
all-clean result. This **supersedes** the "3 HOW-layer flagged family renders" apology above: those
flags were the correct *interim* degraded state under the structural override; the override still stands
as the safety net, but the happy path is now clean for all nine families.

**What landed:** the two-mode HOW contract (CREATE readability-first / UPDATE deterministic splice;
Spike-1a verdict FAIL → splice), comment anchoring moved source→render-snapshot with a server-resolved
`block_ref` bridge, US16 verbatim-carriage superseded (anchor labels + one-unit-one-container survive),
US8/US12/US19 reoriented to render space, reanchor contract v3, gap-CR idempotency under UPDATE, the
empty-shell gate, and the two `RENDER_UPDATE_*` knobs. Default-CI **1077 passed**;
`eval_sc003_survival.py` green incl. render-anchor + UPDATE survival regressions (a)–(f).

**Spec landed:** the `cast-requirements-render.collab.md` **v7 → v8** pass was owner-approved and
**landed** (2026-06-13) — `bin/cast-spec-checker` exit 0, `_registry.md` render row at v8, the HOW
prompt's contract pointer re-aimed at the v8 section. Reviewed diff:
`docs/plan/2026-06-13-refine-requirements-v3-spec-v8-change-brief.md`. **One known limitation recorded:**
relaxing CREATE leaf-text verbatim carriage admits paraphrase meaning-drift; a dedicated fidelity
checker is OUT (HOLD) — the comprehension checker is the only guard.

---

_Signed off by `cast-subphase-runner` (sp5d), the terminal sub-phase of the whole goal._
_Follow-up executed + recorded by `cast-subphase-runner` (refine-req-v3-how-update-mode sp5), 2026-06-13._
