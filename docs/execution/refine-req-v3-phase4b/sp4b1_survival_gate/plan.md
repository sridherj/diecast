# Sub-phase 4b-1: The Survival Gate — Real Comments Provably Place, Misses Surface (Never Block)

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4b/_shared_context.md` before
> starting — especially the **DECISION #10 OVERRIDE** section, which reshapes this sub-phase
> relative to the source-plan body.

## Objective

Add a pure `check_comment_survival` to `maker_gate.py` (reusing 3b's shared `container_text_index`
walker, no copy) and widen `render_job_service`'s `gate_html` stage to fetch the goal's open
comments **at stage entry, re-read per attempt** and run the survival check. Under the OVERRIDE,
an **in-block** miss is a real verbatim-carriage failure → merged into the **existing**
`html_report.violations` channel so the maker gets its one structural retry and, on exhaustion, the
already-shipped `publish()` serves the **best attempt + `structural_violation` flag** (never the
deterministic page). **Cross-boundary** misses are recorded but never flip `passed`. **Every** miss
(in-block or cross-boundary) is surfaced read-time as a `.comment-unplaced` tray badge. SC-003's
"zero new orphans" becomes machine-checked + visibly surfaced at publish time, not hoped for.

## Dependencies

- **Requires completed:** Phase 3 — 3b (`maker_gate.py` with the public `container_text_index`,
  confirmed at `maker_gate.py:238`) and 3c (`render_job_service.py` with `gate_html` line 487 /
  `publish` line 497 carrying the OVERRIDE best-attempt+flag path).
- **HARD no-copy prerequisite (Decisions #12 / C2):** the survival check **imports**
  `container_text_index` from `maker_gate.py`. It does NOT re-implement the walk and does NOT add a
  second markdown stripper (import Phase 2's `strip_inline_markdown` from `goal_card.py`). A
  duplicated walker silently voids "any in-block quote is placeable by construction."
- **Assumed codebase state:** `comment_service.list_comments(goal_slug, *, state="open")` (line 125)
  returns open comment dicts with `id` + `quoted_text`; `parser.Block.ref` + block-body access exist.
- **Parallel with 4b-2 / 4b-3.** Shared file: `_theme.css.j2` (with 4b-3) — additive-append seam.

## Scope

**In scope:**
- Pure `check_comment_survival(html, parsed, comments) -> SurvivalReport` in `maker_gate.py`,
  reusing the single DOM walk + a once-per-pass precompute of stripped block bodies (P1).
- Widen `gate_html` in `render_job_service.py`: fetch open comments at stage entry (re-read per
  attempt), run the survival check after `check_html`, **merge in-block survival violations into
  `state.html_report.violations`**, and write `survival.json` to the job artifact dir.
- `.comment-unplaced` tray badge in `requirements_comments.js` (`placeMarks`) + CSS in `_theme.css.j2`.
- Tests: `cast-server/tests/test_comment_survival.py` (gate) + `render_job_service` integration
  cases (fake runner) + a JS/tray static verdict.

**Out of scope (do NOT do these):**
- Do NOT add a new "survival blocks publish" branch or a survival→deterministic-fallback path. The
  OVERRIDE routes in-block misses through the **existing** structural-gate report + Phase-3
  best-attempt+flag `publish()`. Touch `gate_html` only — never `publish()`'s branch logic.
- Do NOT touch `render_jobs` columns (4a property) — survival observability goes to
  `build/render-jobs/{slug}/{hash12}/survival.json`.
- Do NOT modify `block_diff.py` / `diff_render.py` (logical backbone = existing `Block.ref` space).
- Do NOT re-implement `container_text_index` or `strip_inline_markdown` — import both.
- Do NOT insert stages after `gate_html` (that is 4a-2's seam — see the C3 merge note).
- Do NOT add creation-time quote validation (the lazy + surfaced-tray model already gives the
  honest behavior; verify the existing read-path `displaced` stamping with a test instead).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/maker_gate.py` | Modify | Has `container_text_index`, `check_what_doc`, `check_html`; gains `check_comment_survival` + `SurvivalReport` |
| `cast-server/cast_server/services/render_job_service.py` | Modify | `gate_html` (line 487) gates HTML only; widen to fetch comments + run survival + merge in-block violations + write `survival.json` |
| `cast-server/cast_server/static/requirements_comments.js` | Modify | `placeMarks` (line 51) places marks; collect `highlight()→false` and toggle `.comment-unplaced` |
| `cast-server/cast_server/templates/.../_theme.css.j2` | Modify (append) | Has `.comment-affordance`/`.diff-*`; append a `.comment-unplaced` block (disjoint from 4b-3's `.diff-narration`) |
| `cast-server/tests/test_comment_survival.py` | Create | Does not exist |

> Confirm the `_theme.css.j2` exact path before editing: `grep -rl "comment-affordance" cast-server/cast_server/templates/`.

## Detailed Steps

### Step 4b1.1: `SurvivalReport` + `check_comment_survival` in `maker_gate.py`

Co-locate with the carriage check so it shares the walker. Shape (frozen — copy from shared context):

```python
SurvivalReport = {"passed": bool, "violations": list[str],
                  "unplaced": list[int], "placed": list[int]}

def check_comment_survival(html, parsed, comments) -> SurvivalReport:
    """Pure: does each OPEN comment's quote place on this candidate DOM?
    `comments`: sequence of {id, quoted_text}. I/O-free — the service fetches.
    Single-walk: one container_text_index(html); strip_inline_markdown(block.body) once per pass."""
```

- **Single-walk discipline (P1):** call `container_text_index(html)` **once**; build a
  `{block.ref: strip_inline_markdown(block.body)}` map **once**. Reuse both maps for every comment —
  O(blocks + comments), not O(comments × blocks).
- Per open comment, classify:
  - **in-block:** `quoted_text` is a substring of some block's stripped anchorable text. By the
    verbatim-carriage clause it MUST place — assert it via the container index (concatenated
    descendant text per container + `find()`, hit valid only in that block's container). A miss ⇒
    **violation** string (prompt-ready, names the comment id + truncated anchor + the block's
    container) → appended to `violations`, `passed=False`, id → `unplaced`.
  - **cross-boundary:** quote not within any single block's stripped body. Best-effort whole-document
    find; on a miss → id → `unplaced` only. **Never** appended to `violations`; **never** flips
    `passed` (it can fail on the deterministic substrate too).
  - placed ids (either class) → `placed`.

### Step 4b1.2: Widen `gate_html` in `render_job_service.py` (the OVERRIDE-aware seam)

`gate_html` currently (line 487) sets `state.html_report = check_html(...)`. Widen it — and ONLY it:

1. After `check_html` produces `state.html_report` (skip when `state.html is None`), **fetch the
   goal's open comments at this stage entry**:
   `comment_service.list_comments(state.goal_slug, state="open", db_path=state.db_path, goals_dir=state.goals_dir)`
   (one indexed SELECT; re-read on every `gate_html` entry, so a retry / 4a re-entry sees the current
   comment set — Decision #9). Map to `[{id, quoted_text}]`.
2. `survival = check_comment_survival(state.html, state.parsed, comments)`.
3. Write the **full** `SurvivalReport` to `build/render-jobs/{slug}/{hash12}/survival.json` via the
   existing `_write_artifact` helper (observability — never `render_jobs` columns).
4. **Merge in-block survival violations into the SAME structural channel:** if
   `survival.violations` is non-empty, extend `state.html_report.violations` with them and ensure
   `state.html_report.passed` is `False`. (Cross-boundary-only misses leave `survival.violations`
   empty, so `passed` is untouched — they surface via the badge only.)
   - The `GateReport`/`html_report` is frozen — construct a new merged report rather than mutating
     in place (match how `check_html` returns a fresh frozen dict).
5. **Do nothing else.** The existing `_execute_pipeline` already retries `run_how → gate_html` once
   on a failing `html_report` (line 592 `_how_needs_retry`), and the OVERRIDE `publish()` (line 497)
   already serves best-attempt + `structural_violation` flag when a gate is exhausted. A
   survival-failing attempt therefore flows through the existing flagged-serve path automatically —
   **no new branch.**

> **C3 merge note (for the second-lander of 4a-2 / 4b-1):** 4a-2 inserts `run_checker →
> decide_quality` *after* `gate_html`; this sub-phase only widens `gate_html`'s report. The seams are
> disjoint. 4a wraps "whatever `gate_html` reports", so the merged survival report is absorbed by
> construction. Under the OVERRIDE a survival-failing attempt is a **flagged, servable** structural
> state — NOT a disqualifier from 4a's best-scoring serve. Keep survival evaluated inside `gate_html`
> (before any 4a scoring stage).

### Step 4b1.3: `.comment-unplaced` tray badge (read-time, derived, nothing stored)

In `requirements_comments.js` `placeMarks` (line 51): `highlight()` (line 25) already returns
`false` when the quote is absent from the DOM. Collect the open, non-displaced comments whose
`highlight()` returned `false` and toggle a `.comment-unplaced` badge on their tray `#comment-{id}`
item; clear it for those that placed (so a later render that fixes placement removes the badge).

```js
function placeMarks(comments) {
  clearMarks();
  comments.forEach(function (c) {
    if (c.state !== "open" || c.displaced) return;     // displaced/orphaned ⇒ tray only (unchanged)
    var title = c.author + ": " + String(c.body || "").slice(0, 80);
    var placed = highlight(doc, c.quoted_text, c.id, title);
    setUnplacedBadge(c.id, !placed);                    // NEW: surface a non-displaced open miss
  });
}
```

- `setUnplacedBadge(id, on)` toggles `.comment-unplaced` on `#comment-{id}` in the tray (idempotent;
  must clear when `on` is false). Badge label e.g. "not visible on this render".
- This covers **both** in-block and cross-boundary misses uniformly — exactly the OVERRIDE's
  "surface the loss" for in-block misses on a served flagged render, and the original cross-boundary
  surfacing. Same lazy/derived philosophy as `displaced`.

### Step 4b1.4: Badge CSS in `_theme.css.j2`

Append a `.comment-unplaced` block beside Phase 2's `.comment-affordance` additions (a small muted
"not visible on this render" affordance on the tray item). **Additive, disjoint block** — 4b-3
appends `.diff-narration` separately; whichever lands second appends after the first (no overlap).

### Step 4b1.5: Verify the existing creation-time `displaced` path (no new validation)

Add a test (not new code) confirming that when a comment's `quoted_text` is not a substring of the
canonical source, the existing read-path stamps it `displaced` and routes it to the tray, and the
composer's success handler relies on the existing tray refresh. HOLD: no new creation-time gate.

## Verification

Verification is the heart of this sub-phase. Cover every classification branch and the OVERRIDE seam.

### Automated Tests (permanent)

`pytest cast-server/tests/test_comment_survival.py` green — at least one fixture per class:
- **in-block, placeable** → `passed=True`, id in `placed`.
- **in-block, missing from HTML** → `passed=False`, a prompt-ready `violations` entry, id in
  `unplaced` (the witnessed carriage failure).
- **cross-boundary, spans two blocks** → recorded in `unplaced`, **NOT** a violation, `passed`
  unaffected.
- **cross-boundary, spans an inline-markdown seam** → cross-boundary (not a violation).
- **cross-boundary, quotes maker-added decoration text** → cross-boundary (not a violation).
- **the 1b split-across-inline-elements self-test** replayed through `check_comment_survival` with
  the placement result the spike recorded.
- **Legacy-cutover fixture (proves Key-Risk row 1):** a comment whose quote was selected on the *v2
  deterministic DOM* (carries render decoration / rendered inline-markdown absent from any stripped
  block body) classifies **cross-boundary → surfaced, never a violation**. Without this the
  "legacy comments read as cross-boundary, not failures" mitigation is an unverified claim guarding
  the cutover.
- **Phase-1b fixture pair** (v2 fixture + heavier-edit variant) replays with the spike's placement
  results.
- **Deterministic-fallback trust pin (mirror of Phase 3 T1):** `check_comment_survival` over the
  live `render_requirements()` output passes for in-block quotes — the fallback is published ungated,
  so this proves the substrate never regresses below the gate.

`render_job_service` integration (fake runner) — green:
- **In-block miss flagged-serve (OVERRIDE branch test, replaces the old "blocks publish" test):**
  a fixture HTML that drops one block's carried text → `gate_html` merges the survival violation into
  `html_report` → one structural retry → on exhaustion `publish()` serves the **best attempt with
  `served-by: structural_violation`** (status `flagged`, reason includes the survival violation
  string). It is **NOT** swapped for the deterministic page, and the mark-losing comment is the one
  surfaced by the badge. (This is the override-era assertion of the old T3/"survival-is-structural"
  intent: survival is part of the *surfaced* structural report, servable + flagged.)
- **Cross-boundary-only attempt publishes clean:** an attempt whose only miss is cross-boundary
  passes both gates → `served-by: maker`, `published` (cross-boundary never blocks).
- **Mid-job comment-inclusion latch test (deterministic, mirror of Phase 3 T2):** a comment created
  *after* job start but *before* the `gate_html` stage entry is included in the survival check —
  proving the fetch reads at the gate stage, not at job start. Use a fake-runner latch the test
  releases (no sleep window).
- **`survival.json` written:** the job artifact dir contains the full `SurvivalReport` after a
  `gate_html` pass; no `render_jobs` column was touched by this sub-phase.

### Validation Scripts (temporary)
- One-off: run `check_comment_survival` over a Phase-1 1b evidence HTML with a synthetic comment set
  and print the `SurvivalReport` to confirm violation strings are prompt-ready. Discardable.

### Manual Checks
- `grep -n "def container_text_index\|def strip_inline_markdown" cast-server/cast_server/requirements_render/maker_gate.py` —
  confirm `check_comment_survival` **imports/calls** `container_text_index` and `strip_inline_markdown`,
  defining **neither** a second walker nor a second stripper.
- Confirm `publish()`'s branch logic in `render_job_service.py` is **unchanged** (this sub-phase
  edits `gate_html` only).
- Confirm no `render_jobs` column was added/written by this sub-phase.

### Static / carry-forward (no browser in autonomous runs)
- JS/tray e2e (browser-capable CI per cast-ui-testing) is recorded as a **static verdict +
  human-eyeball carry-forward**: an open, non-displaced comment whose quote is absent from the served
  DOM shows the `.comment-unplaced` badge in the tray. Never blocks the autonomous run.

### Success Criteria
- [ ] `check_comment_survival` is pure (no I/O/DB/LLM); single-walk + once-per-pass strip (P1).
- [ ] In-block misses → `passed=False` + prompt-ready `violations`; cross-boundary misses recorded
      in `unplaced` but never violations, never flip `passed`.
- [ ] `container_text_index` and `strip_inline_markdown` are imported, never re-implemented.
- [ ] `gate_html` fetches open comments at stage entry, re-read per attempt; merges in-block
      violations into `html_report`; writes `survival.json`; touches no `render_jobs` column.
- [ ] OVERRIDE honored: a survival-failing attempt is served best-attempt + `structural_violation`
      flag (never deterministic fallback except literal no-output); `publish()` branch logic
      unchanged.
- [ ] `.comment-unplaced` badge surfaces both in-block and cross-boundary misses; clears when placed.
- [ ] All `test_comment_survival.py` + the `render_job_service` survival cases green.

## Execution Notes

- **The override is the trap.** The source-plan body (4b-1 §, Decisions #4/#10, Key Risks, Design
  Review Flags) repeatedly says an in-block survival miss "blocks publish" / "takes the
  structural-violation branch → deterministic fallback" / "is not a structurally-valid attempt for
  4a's serve." **All of that is superseded** by DECISION #10 OVERRIDE. Implement: merge in-block
  violations into the existing structural report → existing one-retry → existing best-attempt+flag
  serve. Do not add a blocking branch; do not route to deterministic fallback for survival.
- **Single-walk discipline is load-bearing for the "nothing on the view/comment paths" claim.** Do
  not call `strip_inline_markdown` per comment×block or walk the HTML twice.
- The gate stays pure (service fetches, gate computes) — mirrors 3b's no-I/O discipline.
- **Spec-linked files:** the survival gate + `.comment-unplaced` badge are new user-facing behavior
  under `cast-requirements-render.collab.md` (US12 tray grouping, SC-009 selector list). **Flag for
  4b-4's single `/cast-update-spec` pass — do not edit the spec here.**
