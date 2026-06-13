# Sub-phase 5: Proof — Three Families Clean, Survival Regression, Spec v8

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` — the
> **Spec version note** (the plan says "v6→v7" but the spec on disk is already v7; this pass is
> **v7 → v8**), the gap-CR idempotency-under-UPDATE guarantee (plan-review Decisions #2/#5), and the
> "one spec pass, never piecemeal" discipline.

## Objective

The validation target is met and recorded: `bug_fix`, `pilot_poc`, `random_idea` re-render clean
(`served_by=maker`, `human_review=0`); the six previously-clean families don't regress; comment survival
holds under the new anchoring + UPDATE mode; **one `/cast-update-spec` pass** lands every contract change
as `cast-requirements-render.collab.md` **v8**; the goal's decisions-so-far log gains this phase's
outcome section.

## Dependencies

- **Requires completed:** Sub-phases 2, 3b, 4 (the full contract is in place — anchoring moved, the flip
  landed, the families hardened).
- **Terminal sub-phase** — nothing depends on it.
- **Assumed codebase state:** `eval_family_sweep.py`, `eval_sc003_survival.py`, `family_corpus/`
  fixtures; the spec at `docs/specs/cast-requirements-render.collab.md` (**v7** on disk);
  `bin/cast-spec-checker`; `docs/specs/_registry.md`.

## Scope

**In scope:**
- Three-family validation through the production pipeline (clean publishes, not flagged best-attempts) +
  the full nine-family aggregate (no regression); regenerate goldens once, gated.
- Extend `eval_sc003_survival.py` with the survival regressions (a)–(f) below.
- ONE `/cast-update-spec` pass: v7 → **v8** (delegate; review the diff before approval).
- Record the outcome in `decisions-so-far.md` + the goal's signoff record.

**Out of scope (do NOT do these):**
- Do NOT change any contract behavior here — Sub-phase 5 **proves and records**; the code is frozen from
  Sub-phases 2/3b/4.
- Do NOT rewrite the roundtrip spec — only a one-line cross-reference fix IF its wording references
  source-anchored quotes (check; otherwise leave it untouched).
- Do NOT make piecemeal spec edits — this is the single pass for the whole phase.
- Do NOT sample the nine-family sweep — run all nine (cost is explicitly not a constraint).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/eval_sc003_survival.py` | Modify | Add regressions (a)–(f), incl. the **gap-CR-idempotency-under-UPDATE** item (f) |
| `docs/specs/cast-requirements-render.collab.md` | Modify (via `/cast-update-spec`) | v7 → **v8** — the whole contract change set |
| `docs/specs/_registry.md` | Modify (via `/cast-update-spec`) | Bump the render spec row to v8 |
| `docs/specs/cast-requirements-roundtrip.collab.md` | Modify (conditional) | One-line cross-reference fix ONLY IF it references source-anchored quotes |
| `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` | Modify | New "Post-Phase-5 follow-up (executed)" outcome section |
| `docs/goal/refine-requirements-better-rendering-v3/signoff/...` | Modify | This phase supersedes 5d's "principal follow-up" carry-forward |
| Goldens under `signoff/golden/` | Modify | Regenerate once, gated (Phase-2 single-gated-golden-regeneration discipline) |

## Detailed Steps

### Step 5.1: Three-family validation + nine-family no-regression

- Re-run `bug_fix`, `pilot_poc`, `random_idea` through the **production** pipeline; the acceptance bar is
  **clean publishes** (`served_by=maker`, `human_review=0`), not flagged best-attempts.
- Then `eval_family_sweep.py --aggregate --golden` → **9/9 published, 0 flagged** (the gate model's
  happy-path tier all-green this time) — proving paraphrase freedom did not *reduce* quality in the six
  previously-clean families.
- Regenerate goldens **once**, gated.

### Step 5.2: Survival regression (extend `eval_sc003_survival.py`)

Add:
- **(a)** same-source re-render → zero DB changes, all comments place.
- **(b)** small edit → UPDATE mode: comments on unchanged blocks place byte-identically (no reanchor
  dispatch needed).
- **(c)** comment on a modified block → relocated by the publish-boundary v3 dispatch OR left open +
  badged — never silently dropped, never auto-resolved.
- **(d)** massive edit → CREATE mode: survivors place or surface badged.
- **(e)** the trust-boundary check carries forward (server-resolved `block_ref`, never client-supplied).
- **(f) gap-CR idempotency under UPDATE** (plan-review Decisions #2/#5): an UPDATE-mode re-render of a
  doc carrying an **open gap** emits **ZERO new gap change-requests** (the reuse-without-re-emit guarantee
  of Sub-phase 3a; guards the source-hash-keyed dedupe-fingerprint duplication risk). **This regression
  is required** — without it, a future refactor silently reintroduces the duplication.

### Step 5.3: The single spec pass — v7 → v8

**→ Delegate: `/cast-update-spec`** — single pass, `cast-requirements-render.collab.md` **v7 → v8**
(NOT v6→v7 — see the shared-context Spec version note). Land:
- the HOW two-mode contract (CREATE/UPDATE + threshold knobs + `mode` column);
- **US16's verbatim-carriage clause superseded** (anchor labels + one-unit-one-container survive);
- comment anchoring re-spec'd to the render snapshot (US8/US12 re-target, `block_ref`/`anchor_space`
  columns, server-resolved bridge, the migration record, the ref-less-NULL-is-success rule);
- US19 survival reorientation + the publish-boundary re-anchor;
- reanchor **contract v3** (additive superset);
- the **paraphrase-meaning-drift known-limitation** note;
- the **empty-shell gate check** (enforcement detail);
- the `check_update_fidelity` NORMALIZED-text-vs-splice design note (and, IF 1a forced splice, the
  "published artifact is server-assembled in UPDATE mode" architecture note);
- the registry bump to v8.

**Review the `/cast-update-spec` output for:** every reversed clause explicitly marked **superseded**
(not silently rewritten), the v2→v3 reanchor compatibility statement, and that `bin/cast-spec-checker`
passes on v8. **Approve the diff before it lands** (inline approval gate).

### Step 5.4: Conditional roundtrip cross-reference

Check `cast-requirements-roundtrip.collab.md` (v2): IF the comment→change-request bridge wording
references source-anchored quotes, apply a **one-line cross-reference fix** (the render snapshot is now
the anchor space). The roundtrip contract itself (propose/notify/gate) is **untouched**. If no such
wording, leave it.

### Step 5.5: Record the outcome

- `decisions-so-far.md`: a new "Post-Phase-5 follow-up (executed)" section, same format as prior phase
  outcomes.
- The goal's signoff record: this phase supersedes 5d's "principal follow-up" carry-forward.

## Verification

### Automated Tests (permanent / eval)
- **`eval_family_sweep.py --aggregate --golden`** → 9/9 published, 0 flagged.
- **Single-family:** `bug_fix`, `pilot_poc`, `random_idea` each `served_by=maker`, `human_review=0`.
- **`eval_sc003_survival.py`** green incl. regressions (a)–(f) — especially **(f) gap-CR idempotency
  under UPDATE** (zero new gap CRs).
- **Default-CI sweep** (`pytest cast-server/tests/test_*.py`) green — the additive schema + gate changes
  from Sub-phases 2/3a/3b/4 don't regress the suite.
- **`bin/cast-spec-checker`** green on the v8 spec.

### Manual Checks
- `grep -n "Version" docs/specs/cast-requirements-render.collab.md` → confirms **v8** (not v7, not v6→v7).
- `grep -n "requirements-render" docs/specs/_registry.md` → registry row bumped to v8.
- Every reversed US clause (US8/US12/US16/US19) is marked **superseded** in v8, not silently rewritten.
- The HOW prompt's "CONTRACT SOURCE OF TRUTH" pointer (re-aimed in 3b) lands on the v8 section.
- `decisions-so-far.md` + the signoff record carry the executed-outcome section.

### Static / carry-forward (no browser)
- The nine-family visual quality + tray/badge human-eyeball pass is a static verdict + carry-forward
  (no browser in autonomous runs). Never blocks.

### Success Criteria
- [ ] `bug_fix`, `pilot_poc`, `random_idea` publish clean (`served_by=maker`, `human_review=0`).
- [ ] Nine-family aggregate 9/9 published, 0 flagged (six clean families don't regress).
- [ ] `eval_sc003_survival.py` green incl. (a)–(f); the gap-CR-idempotency-under-UPDATE regression (f)
      passes.
- [ ] ONE `/cast-update-spec` pass → **v8**; every reversed clause marked superseded; `bin/cast-spec-checker`
      green; `_registry.md` bumped to v8.
- [ ] Roundtrip spec: one-line cross-reference fix applied ONLY IF needed; contract otherwise untouched.
- [ ] `decisions-so-far.md` + signoff record updated.

## Execution Notes

- **The v7→v8 correction is the easy-to-miss one.** The plan body says "v6→v7" because it was drafted
  before Phase 5 gap-fill bumped the spec to v7. The spec on disk is v7; this pass is **v7→v8**. Land v8.
- **Cost is not a constraint** — run the full nine-family sweep, don't sample (owner stated).
- **Regression (f) is non-optional** (plan-review Decision #5): the reuse-without-re-emit guarantee of
  Sub-phase 3a needs a test pinning it, or a future refactor silently reintroduces duplicate gap CRs.
- **One spec pass, never piecemeal** — Sub-phases 2/3a/3b/4 deliberately left the spec behind the code;
  this pass reconciles all of it at once (the per-phase single-pass discipline from Phases 3/4a/4b/5).
- The `/cast-update-spec` delegation has its own inline approval gate — review the diff before approving.
