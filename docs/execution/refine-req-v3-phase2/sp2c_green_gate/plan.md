# Sub-phase 2c: Green Gate — goldens regenerated once, full suite green

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase2/_shared_context.md` before starting this sub-phase.

## Objective

Bake the 2a card-text fixes and 2b CSS additions into the golden snapshots with **one**
reviewed regeneration, prove the diff contains *only* the expected changes, and confirm the
fallback path stays byte-stable. The goldens are the regression net for the Phase-3-era
fallback path, so an unexplained hunk here is load-bearing and must be chased before landing.

## Dependencies

- **Requires completed:** Sub-phase 2a **and** Sub-phase 2b.
- **Assumed codebase state:** 2a has changed Goal-Card text (stripped markers, untruncated
  sentences); 2b has added `.comment-affordance` rules to `_theme.css.j2`. Both make the golden
  byte-comparison currently **red** — that is the expected entry state for 2c.

## Scope

**In scope:**
- One `UPDATE_GOLDENS=1` regeneration of `tests/golden/requirements_render/*.html`, then a plain
  re-run to prove determinism / byte-stability.
- Per-family manual diff review (13 families) against the expected-change list.
- Re-running the structural battery + `test_fr007_readonly_guard.py` to confirm the DOM contract
  and read-only guarantees still hold.
- Recording the SC-006 static-verdict carry-forward as an explicit follow-up.

**Out of scope (do NOT do these):**
- No code changes to `goal_card.py` / `renderer.py` / `requirements_comments.js` /
  `_theme.css.j2` — 2c only regenerates goldens and verifies. If the diff review surfaces a
  defect, fix it back in 2a or 2b, then re-run 2c (don't patch in 2c).
- No second regeneration. One regen for the whole phase.
- No new features.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/golden/requirements_render/*.html` | Modify (regenerate) | 13 golden families; currently red vs. 2a/2b changes |

## Detailed Steps

### Step 2c.1: Regenerate goldens once

```bash
UPDATE_GOLDENS=1 pytest cast-server/tests/test_requirements_renderer.py
```

### Step 2c.2: Prove determinism / byte-stability

```bash
pytest cast-server/tests/test_requirements_renderer.py   # plain re-run, must be green
```

A clean re-run after the regen proves the render is byte-stable (no timestamps / nondeterminism
leaked into card text or CSS). If the plain re-run is not green, a non-deterministic value
entered the render — chase it before landing (likely a non-frozen set/dict ordering; `_ABBREVIATIONS`
must be a frozenset and the strip regexes a fixed tuple).

### Step 2c.3: Per-family golden diff review (the load-bearing step)

```bash
git diff cast-server/tests/golden/requirements_render/
```

Eyeball the diff per family (13 files). Every hunk must be **one of** the expected changes:
- **Goal-Card text:** stripped inline markers (`**`/`` ` ``/`*`/`[…](…)` gone), untruncated
  sentences (abbreviations no longer cut the job statement short).
- **`_theme.css.j2` rules:** the new `.comment-affordance` / `.comment-affordance__hint` block.

**Anything else is a regression to chase before landing** — fix it back in 2a/2b and re-run 2c.
Confirm in particular: no `id=` appeared, no contiguous-unit breakage, no recipe-section body
text got stripped (the A1/T2 boundary), and `.comment-affordance` does **not** appear in any
golden HTML (goldens render slug-free, so the JS-injected affordance must be absent — this is
the `file://` progressive-enhancement guard, plan-review T3).

### Step 2c.4: Structural battery + read-only guard

```bash
pytest cast-server/tests/test_fr007_readonly_guard.py
pytest cast-server/tests/   # default CI scope — full suite green
```

Confirm the DOM contract (no `id=`, contiguous units) and read-only guarantees still hold.

### Step 2c.5: Record the SC-006 carry-forward

An autonomous run cannot drive a browser for the unprompted-usability check. Capture a static
verdict (screenshot or rendered-HTML walkthrough of the affordance) and list **"human eyeballs
SC-006 on a served render"** as an explicit follow-up in the output / PR description. **Never
block the phase on it** (project standard for visual gates).

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/` green (default CI scope).
- `pytest cast-server/tests/test_requirements_renderer.py` green after regen.
- `pytest cast-server/tests/test_fr007_readonly_guard.py` green.

### Validation Scripts (temporary)

```bash
# Determinism proof: regen, then a plain re-run must be byte-clean (no further diff).
UPDATE_GOLDENS=1 pytest cast-server/tests/test_requirements_renderer.py
git diff --stat cast-server/tests/golden/requirements_render/   # capture the family churn
pytest cast-server/tests/test_requirements_renderer.py          # green ⇒ byte-stable
git diff cast-server/tests/golden/requirements_render/ | grep -n 'id=' && \
  echo "REGRESSION: id= in goldens" || echo "no id= in goldens — OK"
git diff cast-server/tests/golden/requirements_render/ | grep -n 'comment-affordance' && \
  echo "REGRESSION: served-only affordance leaked into golden" || echo "no affordance in goldens — OK"
```

### Manual Checks

- `git diff cast-server/tests/golden/requirements_render/` reviewed per family (13) — only
  Goal-Card text changes + the new `_theme.css.j2` rules; no unexplained hunks.
- SC-006 static verdict captured; human-eyeball follow-up recorded.

### Success Criteria

- [ ] Goldens regenerated exactly once; plain re-run is green (byte-stable / deterministic).
- [ ] Per-family diff (13 families) contains **only** stripped-marker / untruncated card text
      and the new `.comment-affordance` CSS rules.
- [ ] No `id=` and no `.comment-affordance` element in any golden HTML.
- [ ] `pytest cast-server/tests/` green; `test_fr007_readonly_guard.py` green; structural battery
      green.
- [ ] SC-006 static verdict + human-eyeball follow-up recorded; phase not blocked on it.

## Execution Notes

- 2c is the consolidation point: **both** 2a (card text) and 2b (theme CSS) perturb golden
  bytes, so the single regen here keeps the regression net meaningful. Per-sub-phase regens
  would have muddied which change owns which hunk.
- If a hunk can't be explained by the 2a/2b change list, do **not** rubber-stamp it through the
  `UPDATE_GOLDENS=1` path — that path is for *intentional* changes only. Trace it to its source,
  fix in 2a/2b, re-run 2c.
- The whole point of this sub-phase is to keep the golden churn *reviewed* rather than
  rubber-stamped (the consolidated golden-churn risk from the plan's flag table).

**Spec-linked files:** none modified here (2c only regenerates goldens + verifies). The spec edit
was 2b's `/cast-update-spec`; 2c just confirms the structural guards the spec encodes
(`test_fr007_readonly_guard.py`, no-`id=`) still hold.
