# Refine Requirements — Better Rendering (v3): Phase 2 — Discoverable Commenting & an Honest Fallback

## Overview

This phase ships independently, ahead of the rest of v3 (US6 is explicitly decoupled from
the maker). It does two things: (1) makes commenting discoverable — a first-time reader sees
a visible affordance instead of having to guess the hidden select-text gesture (FR-014, US6,
SC-006); (2) hardens the deterministic renderer that v3 keeps as the true-crash fallback
(FR-006) by fixing the two dogfooding defects — raw inline markdown (`**bold**`, `` `code` ``)
leaking as literal characters onto the Goal Card, and the sentence splitter truncating the job
statement on abbreviations (`vs.`, `e.g.`, `30 min.`). The key insight from code reading: the
leak is confined to the Goal Card text paths (`goal_card.py` heuristics + `renderer.py`'s
scope grid), all of which inject via `escape()` rather than the markdown pipeline the recipe
sections already use — so the fix is a small pure helper, not a renderer redesign.

**Position in Overall Plan:** Phase 2 of the six-phase v3 plan. Runs parallel with Phase 1
(spikes) and shares no files with it — Phase 1 owns maker quality + anchor survival; this
phase must stay out of maker/WHAT/HOW/checker and anchor design. Phase 3 later demotes this
renderer to the fallback branch; these fixes ensure the substrate it falls back to is itself
clean. Nothing downstream blocks on this phase, and this phase blocks nothing.

## Operating Mode

**HOLD SCOPE** — set explicitly by the orchestrator (`scope_mode: hold` in the delegation
context and in `refined_requirements.collab.md` front matter). Rigorous adherence to the four
stated work items; no extras (no card redesign, no comment-UX rework beyond the additive
affordance, no new renderer capabilities).

## Depends On (from prior plans / seed decisions)

- **Fallback policy (binding seed decision):** the deterministic renderer stays in the
  codebase as the true no-output-crash fallback. These fixes *harden* it; nothing here may
  remove it or weaken its determinism/byte-stability.
- **v2 DOM contract (spec, preserved by seed decision):** quote/verbatim-substring anchoring;
  **no `id=`, no `data-block-anchor`** anywhere in the canonical render
  (`cast-requirements-render.collab.md` FR-013/US7). Everything added here must honor it.
- **v2 commenting naming contract:** `static/requirements_comments.js`, the same-door comment
  API at `/api/goals/{slug}/requirements/comments`, the `.comment-pill`/`.comment-composer`/
  `.comment-tray-host` selectors, and the FR-028 progressive-enhancement property (bare
  `file://` open ⇒ scripts 404 ⇒ fully readable read-only document).
- **Golden snapshot machinery:** `tests/test_requirements_renderer.py` byte-compares against
  `tests/golden/requirements_render/*.html`, with `UPDATE_GOLDENS=1` as the documented
  intentional-change path. This phase changes golden bytes (card text + theme CSS) and must
  leave the suite green via that path.

## Sub-phase 2a: Honest Fallback — the Goal Card renders clean, untruncated text

**Outcome:** The fallback render's Goal Card (job statement, L2 assertions, scope-compare
grid) shows clean plain text — no literal `**`/`` ` ``/`*`/`[…](…)` characters — and the job
statement survives `vs.`, `e.g.`, `i.e.`, `etc.`, and unit abbreviations like `30 min.`
without truncating mid-sentence. `goal_card.py` stays pure and deterministic.
**Dependencies:** None (parallel with 2b)
**Estimated effort:** 1 session
**Verification:** New unit tests in `cast-server/tests/test_goal_card.py` pass:
(a) a job statement containing `**bold**` and `` `code` `` renders with markers stripped;
(b) assertions sourced from SC table cells with backticks render clean;
(c) `vs.` / `e.g.` / `30 min.` inside a job statement do NOT end the sentence, while a real
sentence boundary still does; (d) existing 7 goal_card tests still pass unchanged in intent.
`pytest cast-server/tests/test_goal_card.py cast-server/tests/test_requirements_renderer.py`
green after golden regeneration (sub-phase 2c).

Key activities:

- **Defect #1 — markdown leak.** Add an exported pure helper to
  `cast-server/cast_server/requirements_render/goal_card.py`:
  `strip_inline_markdown(text: str) -> str` — conservative, regex-based, paired-delimiter
  stripping of inline markers only: `**bold**`/`__bold__` → bold, `*em*`/`_em_` → em,
  `` `code` `` → code, `[text](url)` → text. Paired-delimiter regexes only (e.g.
  `\*\*(.+?)\*\*`), so a lone literal `*` or `_` in prose (`a * b`) is never eaten. This is
  *stripping*, not markdown rendering — it keeps the module's documented "no markdown
  rendering / pure & deterministic" hard rule intact and keeps card text as contiguous
  escaped plain text (no new inline tags ⇒ zero DOM-contract surface).
- Apply the helper at every card-text production point — explicitly, not hidden inside
  `_first_sentence` (the scope grid path doesn't flow through it):
  - `extract_job_statement` — strip the returned statement (both the bold-lead and
    first-sentence branches; the title fallback needs no strip but stripping is harmless —
    apply uniformly).
  - `derive_l2_assertions` — strip each assertion (SC table cells via `_table_cell`,
    Out-of-Scope leads, intent-thread enumerated items).
  - `renderer.py` `_render_scope_grid` — strip the `outcomes` (`_row_description`) and
    `out_of_scope` (`_strip_leading_marker`) items before they reach `_ul`/`escape`
    (import the helper from `goal_card.py`; renderer already imports that module, so no
    new dependency direction and no cycle).
- **Defect #2 — abbreviation truncation.** Replace the single
  `_SENTENCE_END_RE.split(paragraph, maxsplit=1)` in `_first_sentence` with a candidate-scan
  `_split_first_sentence(paragraph)`: iterate `_SENTENCE_END_RE.finditer`, and **skip** a
  candidate boundary when the whitespace-delimited token ending at that period, lowercased,
  is in a module-level `_ABBREVIATIONS` frozenset — seeded with at least
  `{"vs.", "e.g.", "i.e.", "etc.", "cf.", "ca.", "approx.", "min.", "hr.", "hrs.", "sec.",
  "no.", "fig.", "al."}` (dotted forms compared against the full trailing token, so `e.g.`
  with its internal dot matches as one token). First non-skipped boundary ends the sentence;
  no valid boundary ⇒ the whole paragraph is the sentence (current behavior preserved).
  Documented tradeoff in a code comment: a sentence that *genuinely* ends in `etc.` runs
  long into the next sentence — an over-long statement is honest, a truncated one is wrong.
- Keep both functions pure (no I/O, no state); the abbreviation set is a frozen module
  constant so goldens stay byte-stable run-to-run.
- Write the unit tests listed under Verification, data-driven where natural
  (`pytest.mark.parametrize` over the abbreviation set), following
  `/cast-pytest-best-practices`. Include the *actual dogfooding strings* that surfaced the
  defects as literal test cases so the regression is pinned to reality.

**Design review:**
- **Architecture ✓** — helper lives in `goal_card.py` (the IA-core module), renderer imports
  it; matches the existing dependency direction (`renderer` → `goal_card`, never reverse).
- **Purity rule ✓ (checked, not rubber-stamped)** — `goal_card.py`'s docstring forbids
  "markdown rendering"; stripping markers is a pure text transformation, not rendering. The
  docstring should be amended in the same change to say inline markers are *stripped* for
  card display, so the rule and the code can't drift.
- **Naming** — `strip_inline_markdown` / `_split_first_sentence` / `_ABBREVIATIONS` follow
  the module's existing `_snake` + exported-verb conventions ✓.
- **Error & edge paths** — nested/unbalanced markers (e.g. `**a *b* c**`): apply strip
  passes innermost-first or iterate to fixpoint with a small bound; an unbalanced `**`
  must pass through unchanged (assert in tests). Empty-after-strip text must keep the
  existing "loud on absence" warning behavior of `extract_job_statement`.
- **Spec consistency** — `cast-requirements-render.collab.md` does not specify card text
  formatting at this granularity; no spec conflict, no `/cast-update-spec` needed for 2a.

## Sub-phase 2b: Discoverable Commenting — a visible affordance beside the hidden gesture

**Outcome:** A reader opening a served render sees, without doing anything, a visible
commenting control + hint; the existing select-to-comment pill keeps working unchanged; a
bare `file://` open shows **no** dead comment control (progressive enhancement preserved).
**Dependencies:** None (parallel with 2a)
**Estimated effort:** 1 session
**Verification:** Served render (`GET /goals/{slug}/render`): `.comment-affordance` is
present on load, reads "💬 Comment — select any text to comment", and clicking it reveals/
scrolls to the comment tray; selecting text still shows the `.comment-pill` → composer →
`<mark>` flow (existing UI test stays green). `file://` open of the generated artifact:
no `.comment-affordance` in the DOM. `grep`-level check: no `id=` introduced anywhere in
render output. SC-006 (unprompted first-time-reader usability): static verdict + human
eyeball carry-forward — see Risks.

Key activities:

- **Inject the affordance from `static/requirements_comments.js`, not from the template.**
  In `init()` (which only runs when `data-goal-slug` is present — exactly the condition
  under which commenting works), create a `button.comment-affordance` and insert it into
  the existing `.rr-controls` bar, with visible text `💬 Comment` and an adjacent persistent
  hint span `select any text to comment` (`.comment-affordance__hint`). The hint *states the
  gesture* — that is what makes SC-006 pass for a reader given no instructions.
- Click behavior (additive, minimal): reveal and scroll to the `.comment-tray-host` (where
  existing comments and the displaced/orphaned groups live) and briefly pulse the hint
  (a CSS class toggled for ~1.5 s) to draw the eye to the gesture instruction. No new
  comment-creation path — the same-door API surface is untouched; the affordance teaches
  and surfaces, the selection gesture still creates.
- Style `.comment-affordance` / `.comment-affordance__hint` in
  `requirements_render/templates/_theme.css.j2`, next to the existing `.comment-pill` /
  `.comment-composer` rules (the established home for comment CSS). Class selectors only —
  **no `id=`** (DOM contract).
- Keep all existing behavior byte-identical on the no-slug path: family goldens render
  slug-free, so the JS-injected element never appears in golden HTML; only the `_theme.css.j2`
  additions change golden bytes (handled in 2c).
- **`→ Delegate: /cast-update-spec`** on `docs/specs/cast-requirements-render.collab.md` —
  record the additive affordance: extend the FR-028 / commenting-UX area with "a visible
  `.comment-affordance` control + gesture hint is injected by `requirements_comments.js` on
  served renders (slug present); select-to-comment remains the creation path; bare `file://`
  renders carry no affordance," and add `.comment-affordance` to the SC-009 named-selector
  list. Review output: confirm the diff touches only those clauses and bumps version/date —
  the DOM contract (US7/FR-013) and decision #7's select→pill→composer flow must read as
  *unchanged*.
- Extend the requirements-render UI screen under `cast-server/tests/ui/` with the two new
  assertions (affordance present on load; click reveals the tray) targeting
  `.comment-affordance`, alongside the existing SC-009 selector flows. Runs in
  browser-capable CI only, like the rest of that screen.

**Design review:**
- **Spec consistency ⚠ (resolved in-activity)** — the spec's commenting UX is a locked
  decision (#7: select → pill → composer) and SC-009 enumerates named selectors; an
  affordance is a *user-facing surface change* ⇒ the `/cast-update-spec` activity above is
  mandatory, not optional. The seed constraint confirms: "the comment UI affordance is
  additive; keep select-to-comment path; DOM contract unchanged."
- **Architecture ✓** — JS-injection keeps the affordance on exactly the code path where
  commenting is live, preserves FR-028 progressive enhancement, and keeps golden HTML free
  of served-only chrome — same pattern as the existing convergence chip (`updateCard`).
- **Naming ✓** — `.comment-affordance` follows the `.comment-*` BEM-ish family already in
  the file (`.comment-pill`, `.comment-tray-host`, `.comment-composer__*`).
- **Error & rescue** — if `.rr-controls` is absent (defensive: older cached artifact), the
  injection must no-op silently rather than throw and kill the rest of `init()` (marks,
  tray, composer). Guard with a null check, matching the file's existing defensive style.
- **Security ✓** — affordance text is static; no user input flows through it; no new API
  surface.

## Sub-phase 2c: Green Gate — goldens regenerated once, full suite green

**Outcome:** The deterministic golden-snapshot suite is green with the 2a text fixes and 2b
CSS additions baked into the goldens; the diff between old and new goldens contains *only*
the expected changes; the fallback path remains byte-stable.
**Dependencies:** Sub-phase 2a + Sub-phase 2b
**Estimated effort:** 0.5 session
**Verification:** `pytest cast-server/tests/` green (default CI scope);
`UPDATE_GOLDENS=1` run followed by a clean re-run proves byte-stability; manual review of
`git diff tests/golden/requirements_render/` shows only Goal-Card text changes (stripped
markers, untruncated sentences) and the new `_theme.css.j2` rules — anything else is a
regression to chase before landing.

Key activities:

- Regenerate goldens once for the whole phase:
  `UPDATE_GOLDENS=1 pytest cast-server/tests/test_requirements_renderer.py`, then a plain
  re-run to confirm determinism.
- Eyeball the golden diff per family (13 files) against the expected-change list above —
  the goldens are the regression net for the Phase-3-era fallback path, so an unexplained
  hunk here is load-bearing.
- Run the structural battery + `test_fr007_readonly_guard.py` to confirm the DOM contract
  (no `id=`, contiguous units) and read-only guarantees still hold.
- Record the SC-006 carry-forward: an autonomous run cannot drive a browser for the
  unprompted-usability check, so capture a static verdict (screenshot or rendered-HTML
  walkthrough of the affordance) and list "human eyeballs SC-006 on a served render" as an
  explicit follow-up — never block the phase on it.

**Design review:**
- **No flags** beyond the consolidated golden-churn risk (see table) — this sub-phase exists
  precisely to keep that churn reviewed rather than rubber-stamped.

## Build Order

```
Sub-phase 2a (card text fixes) ──┐
                                 ├──► Sub-phase 2c (golden regen + green gate)
Sub-phase 2b (affordance) ───────┘
```

**Critical path:** 2a → 2c (2a and 2b are independent; both touch golden bytes — 2a via card
text, 2b via theme CSS — so golden regeneration happens exactly once, in 2c, after both).
At 1–2 sessions total, executing 2a then 2b sequentially in one branch is the practical
default; the parallel split exists if two executors pick it up.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 2a | `goal_card.py` purity docstring says "no markdown rendering" — stripping must not read as drift | Amend the docstring in the same change: inline markers are *stripped* (pure text transform), never rendered |
| 2a | Strip regexes could mangle legit prose (`a * b`, unbalanced `**`) | Paired-delimiter regexes only; unbalanced markers pass through; pinned by unit tests |
| 2b | Spec conflict: locked commenting UX (decision #7) + SC-009 selector list predate the affordance | `/cast-update-spec` activity in 2b records the additive affordance + new selector; DOM contract clauses stay verbatim |
| 2b | FR-028 progressive enhancement: a template-placed control would show dead UI on `file://` | Affordance is JS-injected behind the existing slug guard — never in the static artifact |
| 2c | Golden churn can mask an unrelated regression | One regen, manual diff review per family, structural battery re-run |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Abbreviation set is incomplete — a new abbreviation truncates a future job statement | Low | Frozen, easily extended set + data-driven parametrized test; failure mode is visible (truncated card) and one-line to fix |
| A sentence genuinely ending in an abbreviation (`… etc.`) now runs long | Low | Accepted tradeoff, documented in code: over-long beats truncated; the 2-minute SC-001 bar tolerates one long sentence |
| Strip helper alters card text in ways the Phase 4 quote-anchored comments stored against *old* card text no longer match | Med | Displacement is already a derived, surfaced property (spec US12) — any affected comment shows in the "needs re-anchor" tray, never silently lost; note in PR description |
| SC-006 cannot be verified autonomously (no browser in autonomous runs) | Low | Static verdict + explicit human-eyeball carry-forward item (project-standard for visual gates); UI test covers it in browser-capable CI |
| Golden regeneration hides an unintended render change | Med | 2c's manual per-family diff review + structural battery + determinism re-run |

## Open Questions

- None blocking. All forks were auto-decided under the binding seed decisions (see Decisions
  made autonomously below). The goal-level **[USER-DEFERRED]** model-tier knob does not touch
  this phase (no LLM in any Phase 2 path).

## Suggested Revisions to Prior Sub-Phases

- None. No seed decision needed deviation; this phase's constraints (additive affordance,
  fallback hardened-not-removed, DOM contract untouched) were all directly honorable.

## Decisions made autonomously

Per the autonomous-run instruction, these taste-level forks were decided without pausing,
each consistent with the seed decisions and HOLD SCOPE:

1. **Strip, don't convert, inline markdown on the Goal Card.** The high-level plan allowed
   "convert/strip"; chose strip-to-plain-text because it preserves `goal_card.py`'s purity
   rule, keeps card text contiguous escaped plain text (zero new DOM surface under the
   no-`id=` contract), and avoids inline-tag styling questions on the card. Converting to
   `<strong>`/`<code>` remains a trivial later upgrade if wanted.
2. **Strip at each production point, not inside `_first_sentence`.** Explicit call sites
   (job statement, assertions, scope grid) beat an implicit transform buried in a shared
   helper — and the renderer's scope-grid path doesn't flow through `_first_sentence` anyway.
3. **Abbreviation handling via a token-set candidate scan**, not lookbehind regex (Python
   `re` requires fixed-width lookbehind; a scan over `finditer` candidates checking the
   trailing token is simpler, testable, and trivially extensible). Over-long-on-genuine-`etc.`
   accepted as the honest failure mode.
4. **Affordance is JS-injected into `.rr-controls`** (not template-rendered): only path that
   simultaneously satisfies FR-028 progressive enhancement (no dead control on `file://`),
   keeps golden HTML free of served-only chrome, and mirrors the existing convergence-chip
   pattern. CSS still lives in `_theme.css.j2` with the other `.comment-*` rules (single
   style source; unused rules on `file://` are harmless).
5. **Affordance behavior = teach + surface, not a new creation path.** Click reveals the
   tray and pulses the gesture hint; comment creation stays select→pill→composer through the
   same-door API. Anything more (e.g. a click-to-place comment mode) is scope expansion.
6. **One golden regeneration, gated and reviewed (sub-phase 2c)** rather than per-sub-phase
   regens — both sub-phases perturb golden bytes; a single reviewed regen keeps the
   regression net meaningful.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (Draft v2) | US7/FR-012/FR-013 (DOM contract — preserved); FR-028 (progressive enhancement — preserved, pattern reused); US8/FR-015 (same-door comment API — untouched); SC-002 (deterministic goldens — regen path); SC-009 (selector list — extended) | 1 — the visible affordance extends the recorded commenting UX and selector list → `/cast-update-spec` activity in Sub-phase 2b |
| `cast-goal-classification.collab.md` (Draft v1) | `FAMILY_RECIPES` consumption by the renderer (context only — recipe machinery untouched) | None |

## Plan-Review Decisions (cast-plan-review)

Delegated, fully-autonomous review (scope: **BIG CHANGE**, honoring `scope_mode: hold`). All
four sections worked through against the live codebase; every fork auto-decided under the
binding seed decisions, no user pause. Claims in this plan were verified against source:
`.rr-controls` is a real injection target (`templates/document.html.j2:36`), 13 golden families
exist, `tests/test_goal_card.py` carries the 7 referenced tests, the `renderer → goal_card`
dependency direction is real, and the `escape()`-injected vs `_md_to_html`-rendered card-text
split is as the plan describes. **Verdict: plan is sound and implementable as written; the
items below are hardening, not blockers — no Open issue remains.**

| Section | Issues Found | Resolved | Deferred |
|---------|-------------|----------|----------|
| Architecture | 2 | 2 | 0 |
| Code Quality | 3 | 3 | 0 |
| Tests | 3 | 3 | 0 |
| Performance | 2 | 2 | 0 |

- **2026-06-12T08:15:19Z — A1: Is the strip-application matrix complete and correctly scoped?** — Decision: Confirmed complete. The escape()-injected card-text paths are exactly {`extract_job_statement`; `derive_l2_assertions` ×3 sub-sources (SC `_table_cell`, Out-of-Scope `_first_sentence`, intent-thread `_enumerated_items`); `renderer._render_scope_grid` ×2 (`_row_description` outcomes, `_strip_leading_marker` out-of-scope)} — all enumerated by the plan. Rationale: these are the *only* paths that reach the DOM via `escape()`; the `_md_to_html` recipe-section and `_render_stub_card` preamble paths render markdown intentionally and MUST NOT be stripped. Added guardrail: 2a must scope `strip_inline_markdown` to the escape() paths only — never wire it into `_md_to_html`.
- **2026-06-12T08:15:19Z — A2: Does any planned activity have an available skill/agent it should delegate to but doesn't?** — Decision: No gap. Plan already delegates `/cast-update-spec` (2b spec change) and `/cast-pytest-best-practices` (2a tests); the helper, golden-regen, and UI-screen-extension work have no better-fitting agent (UI assertions correctly extend the existing `cast-ui-test-requirements-render` screen). Rationale: Step-3 skill-delegation scan passed; over-delegation would add ceremony without value.
- **2026-06-12T08:15:19Z — CQ1: Consolidate the two divergent `_strip_leading_marker` (goal_card: numbered+bullet; renderer: bullet-only)?** — Decision: No — leave both under HOLD SCOPE. Rationale: a latent DRY smell, but the renderer path only ever sees Out-of-Scope `-`/`*` bullets so there is no functional defect; consolidating is a refactor outside the four stated work items. Noted here so a future phase can fold them.
- **2026-06-12T08:15:19Z — CQ2: Harden the `[text](url)` strip regex against parenthesized URLs?** — Decision: No — keep the simple non-greedy `\[(.+?)\]\((.+?)\)` and document the limitation in a code comment. Rationale: balanced-paren URL parsing is YAGNI for requirements prose; the degradation (`[t](http://x(y))` leaves a stray `)`) is rare and visible. Pin the limitation with one test asserting the known-degraded output so it can't silently worsen.
- **2026-06-12T08:15:19Z — CQ3: Trim surrounding punctuation off the abbreviation-scan token before frozenset lookup?** — Decision: Yes — normalize the comparison token by trimming leading bracket/quote punctuation (`([{"'`) before the `_ABBREVIATIONS` membership check (e.g. `(e.g.` → `e.g.`). Rationale: cheap, in-scope hardening of the *same* Defect-#2 work item; removes the most common false-negative (an abbreviation opening a parenthetical) without expanding the set or scope. Keep set entries bare.
- **2026-06-12T08:15:19Z — T1: Promote the design-review edge cases to named 2a tests?** — Decision: Yes. Add explicit cases: unbalanced `**a` passes through unchanged; nested `**a *b* c**` → `a b c`; lone `a * b` untouched; the CQ2 parenthesized-URL degradation pinned. Rationale: "rather too many tests than too few" — these were prose-only in the design-review block; promoting them to the Verification list pins the regressions to reality.
- **2026-06-12T08:15:19Z — T2: Add a negative guard test that the markdown PIPELINE still renders?** — Decision: Yes (low cost). Assert a recipe-section body containing `**bold**` still emits `<strong>` (i.e. is NOT stripped). Rationale: locks the A1 boundary so a future edit can't route section bodies through `strip_inline_markdown`; likely already implied by goldens but an explicit unit assertion is the cheap insurance.
- **2026-06-12T08:15:19Z — T3: Does the `file://` no-affordance check need a new test harness?** — Decision: No — the existing slug-free golden byte-comparison already IS the progressive-enhancement guard (goldens render with no slug and no JS execution, so the JS-injected affordance can never appear in golden HTML). Rationale: maps an apparent gap to existing coverage; 2c's per-family golden diff review is where this is verified. The browser UI assertion in 2b covers the positive (served-render) case.
- **2026-06-12T08:15:19Z — P1: Bound the `strip_inline_markdown` fixpoint iteration?** — Decision: Yes — cap at a small constant (≤5 passes) and document. Rationale: prevents pathological nested-marker input from looping; negligible cost at card-text scale (one job statement + ≤5 assertions + a handful of scope items, rendered once per source-hash miss).
- **2026-06-12T08:15:19Z — P2: Any perf concern in the abbreviation `finditer` scan replacing `split(maxsplit=1)`?** — Decision: No action. Rationale: O(n) over a single job-statement paragraph either way; card render is cached by source hash. No N+1, no DB, no hot path.
