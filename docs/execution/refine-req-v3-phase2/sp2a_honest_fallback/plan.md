# Sub-phase 2a: Honest Fallback — the Goal Card renders clean, untruncated text

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase2/_shared_context.md` before starting this sub-phase.

## Objective

Make the deterministic fallback render's Goal Card honest: it shows clean plain text — no
literal `**`/`` ` ``/`*`/`[…](…)` markers — and the job statement survives `vs.`, `e.g.`,
`i.e.`, `etc.`, and unit abbreviations like `30 min.` without truncating mid-sentence.
`goal_card.py` stays pure and deterministic. This hardens the substrate that v3 (Phase 3)
later demotes to the true no-output-crash fallback, so the page it falls back to is itself
clean.

## Dependencies

- **Requires completed:** None (parallel with sp2b).
- **Assumed codebase state:** `goal_card.py` and `renderer.py` as they stand on `main`;
  `tests/test_goal_card.py` carries 7 existing tests.

## Scope

**In scope:**
- A pure, exported, import-stable helper `strip_inline_markdown(text) -> str` in `goal_card.py`.
- Applying that helper at every `escape()`-injected card-text production point (job statement,
  L2 assertions ×3 sub-sources, scope grid ×2 in `renderer.py`).
- Replacing `_first_sentence`'s single split with an abbreviation-aware `_split_first_sentence`
  + a module-level `_ABBREVIATIONS` frozenset.
- Amending the `goal_card.py` module docstring so "stripped, not rendered" is explicit.
- New + extended unit tests in `cast-server/tests/test_goal_card.py`.

**Out of scope (do NOT do these):**
- **Do NOT wire `strip_inline_markdown` into `_md_to_html`** or any markdown-pipeline /
  recipe-section / `_render_stub_card` preamble path — those render markdown intentionally
  (plan-review A1 guardrail). Strip only the `escape()` paths.
- No card redesign, no new inline tags (`<strong>`/`<code>`) on the card — strip to plain text.
- No golden regeneration here — that is sub-phase 2c's single, reviewed regen.
- No touching `requirements_comments.js`, `_theme.css.j2`, the spec, or UI tests (that's 2b).
- No consolidation of the two divergent `_strip_leading_marker` definitions (plan-review CQ1:
  left as-is under HOLD SCOPE).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/goal_card.py` | Modify | Has `extract_job_statement`, `derive_l2_assertions`, `_first_sentence`, `_table_cell`, `_enumerated_items`, `_strip_leading_marker`, `_SENTENCE_END_RE` |
| `cast-server/cast_server/requirements_render/renderer.py` | Modify | `_render_scope_grid` builds `outcomes` via `_row_description` and `out_of_scope` via local `_strip_leading_marker`; imports `from .goal_card import derive_l2_assertions, extract_job_statement` (line 41) |
| `cast-server/tests/test_goal_card.py` | Modify | 7 existing tests |

## Detailed Steps

### Step 2a.1: Add the `strip_inline_markdown` helper (pure, exported, import-stable)

Add a **module-level public** function to `goal_card.py`. It is a contract for Phase 3's
`maker_gate.py` — see the hard edge in `_shared_context.md`. Keep it a pure function of its
`str` argument: no I/O, no state, no module globals beyond compiled regexes.

Behavior — conservative, paired-delimiter stripping of inline markers only:
- `**bold**` / `__bold__` → `bold`
- `*em*` / `_em_` → `em`
- `` `code` `` → `code`
- `[text](url)` → `text`

Implementation notes:
- **Paired-delimiter regexes only**, e.g. `re.compile(r"\*\*(.+?)\*\*")`, so a lone literal
  `*`/`_` in prose (`a * b`) is never eaten and an **unbalanced** `**a` passes through unchanged.
- Strong-before-em ordering (`**`/`__` before `*`/`_`) so `**bold**` isn't mis-split by the
  em pass.
- **Link regex (plan-review CQ2):** keep the simple non-greedy `\[(.+?)\]\((.+?)\)`. Do NOT
  attempt balanced-paren URL parsing (YAGNI for requirements prose). Add a one-line code comment
  documenting the known degradation: `[t](http://x(y))` leaves a stray `)`. This limitation is
  pinned by a test (Step 2a.5).
- **Nested / fixpoint (plan-review P1):** handle nested markers (`**a *b* c**` → `a b c`) by
  iterating to a fixpoint, **capped at ≤5 passes** (stop early when a pass makes no change).
  Document the cap in a comment. Negligible cost at card-text scale.

```python
# Inline-markdown markers are *stripped* (not rendered) for Goal-Card display — see the
# module docstring's purity rule. Paired-delimiter regexes only: a lone `*`/`_`/`` ` `` or an
# unbalanced `**a` passes through untouched. Link parsing is deliberately simple
# (non-greedy) — a parenthesized URL like `[t](http://x(y))` leaves a stray `)`; that is an
# accepted, test-pinned degradation (YAGNI for requirements prose).
_STRIP_PASSES = (
    re.compile(r"\*\*(.+?)\*\*"),
    re.compile(r"__(.+?)__"),
    re.compile(r"\*(.+?)\*"),
    re.compile(r"_(.+?)_"),
    re.compile(r"`(.+?)`"),
    re.compile(r"\[(.+?)\]\((.+?)\)"),
)
_MAX_STRIP_PASSES = 5


def strip_inline_markdown(text: str) -> str:
    """Strip inline-markdown markers for Goal-Card plain-text display (pure)."""
    # ... iterate _STRIP_PASSES to a fixpoint, capped at _MAX_STRIP_PASSES.
```

(The link regex has two groups — keep `\1` in its substitution. The others use `\1`.)

### Step 2a.2: Amend the module docstring (purity rule can't drift)

In `goal_card.py`'s "Hard rules" docstring block, change the `no markdown rendering` clause so
it explicitly says inline markers are **stripped** (a pure text transform) for card display,
never rendered. This keeps plan-review's purity flag from reading as drift.

### Step 2a.3: Apply the strip at every card-text production point (explicitly)

Apply `strip_inline_markdown` at each `escape()`-injected production point — **not** hidden
inside `_first_sentence` (the scope-grid path doesn't flow through it). The complete matrix
(plan-review A1 — verified the *only* `escape()` paths):

In `goal_card.py`:
- `extract_job_statement` — strip the returned statement on **both** the bold-lead branch and
  the first-sentence branch. (The title fallback needs no strip; stripping is harmless — apply
  uniformly for one exit path.)
- `derive_l2_assertions` — strip each assertion across all three sub-sources:
  - SC table cells via `_table_cell`,
  - Out-of-Scope leads via `_first_sentence(_strip_leading_marker(...))`,
  - intent-thread enumerated items via `_enumerated_items`.

In `renderer.py` `_render_scope_grid`:
- Strip `outcomes` items (built by `_row_description`) and `out_of_scope` items (built by the
  local `_strip_leading_marker`) **before** they reach `_ul` / `escape`.
- Import the helper: extend the existing `from .goal_card import derive_l2_assertions,
  extract_job_statement` (renderer.py:41) to also import `strip_inline_markdown`. No new
  dependency direction, no cycle (`renderer` → `goal_card` already holds).

Apply at the point where the final card string is produced, so a single strip covers each unit.

### Step 2a.4: Replace `_first_sentence`'s split with abbreviation-aware `_split_first_sentence`

Add a module-level frozenset and a candidate-scan splitter; route `_first_sentence` through it.

```python
# Trailing dotted tokens that look like a sentence boundary but are not. Compared against the
# full whitespace-delimited token ending at the candidate period, lowercased, with leading
# bracket/quote punctuation trimmed (so `(e.g.` matches `e.g.`). Easily extended; frozen so
# goldens stay byte-stable run-to-run. A sentence genuinely ending in one of these (e.g.
# `... etc.`) runs long into the next sentence — an over-long statement is honest; a truncated
# one is wrong (accepted tradeoff).
_ABBREVIATIONS = frozenset({
    "vs.", "e.g.", "i.e.", "etc.", "cf.", "ca.", "approx.",
    "min.", "hr.", "hrs.", "sec.", "no.", "fig.", "al.",
})
_LEADING_TOKEN_PUNCT = "([{\"'"
```

`_split_first_sentence(paragraph) -> str`:
- Iterate `_SENTENCE_END_RE.finditer(paragraph)`.
- For each candidate boundary, take the whitespace-delimited token ending at that period,
  lowercase it, and **(plan-review CQ3)** strip leading bracket/quote punctuation
  (`_LEADING_TOKEN_PUNCT`) before the `_ABBREVIATIONS` membership check (so `(e.g.` → `e.g.`).
  Keep set entries bare.
- **Skip** the candidate when the normalized token is in `_ABBREVIATIONS`.
- The first non-skipped boundary ends the sentence; return text up to it.
- No non-skipped boundary ⇒ return the whole paragraph (current behavior preserved).

Keep `_SENTENCE_END_RE` as-is. Update `_first_sentence` to delegate to `_split_first_sentence`
after its existing `_strip_leading_marker(paragraph)` step. Both functions stay pure (no I/O,
no state).

### Step 2a.5: Write the unit tests

→ Delegate: `/cast-pytest-best-practices` — apply when writing `cast-server/tests/test_goal_card.py`
additions (data-driven `pytest.mark.parametrize` over the abbreviation set; class/method
structure matching the existing file). Review its output for: parametrization over the
abbreviation set, use of the literal dogfooding strings, and no fixture overreach.

Required cases (see Verification for the binary checklist). Use the **actual dogfooding
strings** that surfaced the defects as literal cases so the regression is pinned to reality.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_goal_card.py`

Add these, then run `pytest cast-server/tests/test_goal_card.py`:

- **Markdown strip — job statement (a):** a job statement containing `**bold**` and
  `` `code` `` renders with markers stripped (`bold`, `code`), no literal `*`/`` ` ``.
- **Markdown strip — assertions (b):** assertions sourced from SC table cells containing
  backticks render clean.
- **Abbreviation survival (c):** `vs.` / `e.g.` / `i.e.` / `etc.` / `30 min.` inside a job
  statement do NOT end the sentence; a **real** sentence boundary in the same paragraph still
  does. Data-driven (`parametrize`) over the abbreviation set.
- **CQ3 parenthetical abbreviation:** `(e.g.` opening a parenthetical is normalized and not
  treated as a boundary.
- **Edge — unbalanced (T1):** `**a` (unbalanced) passes through unchanged.
- **Edge — nested (T1):** `**a *b* c**` → `a b c`.
- **Edge — lone marker (T1):** `a * b` is untouched.
- **Edge — CQ2 degradation pinned (T1):** `[t](http://x(y))` produces the known-degraded
  output (assert the literal result, including the stray `)`), so it can't silently worsen.
- **Negative guard — pipeline still renders (T2):** a recipe-section body containing `**bold**`
  still emits `<strong>` (i.e. is NOT stripped). This locks the A1 boundary so a future edit
  can't route section bodies through `strip_inline_markdown`. (If the render of a recipe-section
  body isn't unit-reachable from `goal_card.py`, place this assertion in
  `test_requirements_renderer.py` against the rendered HTML.)
- **Existing 7 tests:** still pass, unchanged in intent.

### Validation Scripts (temporary)

```bash
# Fast check of just this sub-phase's surface (goldens NOT regenerated yet — see 2c):
pytest cast-server/tests/test_goal_card.py -q
# Confirm the helper is importable at its contract location (the 2a → 3b hard edge):
python -c "from cast_server.requirements_render.goal_card import strip_inline_markdown as s; \
print(s('**a *b* c** and `code` and [t](u)'))"   # -> a b c and code and t
```

### Manual Checks

- `git diff cast-server/cast_server/requirements_render/goal_card.py` — confirm the docstring
  amendment landed and no markdown-pipeline path was touched.
- Confirm `renderer.py` imports `strip_inline_markdown` from `goal_card.py` (not a re-defined
  copy) — single-implementation discipline.

### Success Criteria

- [ ] `strip_inline_markdown` exists as a module-level public function in `goal_card.py`, pure,
      importable at `cast_server.requirements_render.goal_card.strip_inline_markdown`.
- [ ] All four marker classes stripped; lone/unbalanced markers pass through; CQ2 degradation
      test-pinned; fixpoint capped ≤5 passes.
- [ ] `_split_first_sentence` + `_ABBREVIATIONS` added; abbreviations don't truncate; real
      boundaries still split; CQ3 leading-punct normalization in place.
- [ ] Strip applied at all 6 `escape()` card-text points (job statement ×2 branches,
      assertions ×3 sub-sources, scope grid ×2) — and **nowhere in the markdown pipeline**.
- [ ] Module docstring amended to "stripped, not rendered".
- [ ] `pytest cast-server/tests/test_goal_card.py` green; existing 7 tests pass unchanged in
      intent; T2 pipeline-still-renders guard passes.
- [ ] `goal_card.py` and `_split_first_sentence` remain pure (no I/O/state); `_ABBREVIATIONS`
      is a frozen module constant.

## Execution Notes

- **The 2a → 3b hard edge is the highest-stakes constraint here.** `strip_inline_markdown` is
  imported by Phase 3's `maker_gate.py` later. Treat its name, signature
  (`(text: str) -> str`), purity, and import location as a frozen contract. Do not make it
  depend on `ParsedRequirements` or any render state.
- `test_requirements_renderer.py` will go **red** after 2a's card-text changes because goldens
  still hold the old (leaked/truncated) text. **That is expected** — 2c regenerates goldens
  once after both 2a and 2b. Do not regen here. If you want a local sanity check, you may run
  `UPDATE_GOLDENS=1` on a throwaway and `git checkout` the goldens, but the canonical regen is
  2c's job.
- Strong-before-em ordering matters: run `**`/`__` passes before `*`/`_` so `**bold**` isn't
  chewed by the single-`*` pass.

**Spec-linked files:** `goal_card.py` and `renderer.py` are linked by
`docs/specs/cast-requirements-render.collab.md`. Per `_shared_context.md`, the spec does **not**
specify card-text formatting at this granularity → **no spec conflict, no `/cast-update-spec`
for 2a.** (The spec change lives in 2b.) No SAV behavior is altered — card text becomes cleaner,
the DOM contract is untouched.
