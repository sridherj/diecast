# Sub-phase 3: Goal Card + Pill + Disclosure Boundary + WHAT-before-HOW — WP-C + WP-D

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.

## Objective
Land the entire **SC-001 surface**: the zero-click Goal Card (pill + version chip + L1 job statement
+ 3–5 L2 assertions + open scope compare), plus the disclosure boundary (only *depth* collapses;
WHAT is never behind `<details>`) and WHAT-before-HOW (muted, last, omit-not-pad). The deterministic
IA heuristics live in a dedicated `goal_card.py`, unit-tested in isolation (plan-review #3) — this is
the information-architecture core that makes or breaks the 2-minute test.

WP-C and WP-D are merged into one sub-phase because both edit the **same** `document.html.j2` slots +
`renderer.py` wiring; splitting them into parallel sessions would conflict on those files (the plan
itself says "C and D are parallel edits over the same template — coordinate, don't serialize").

## Dependencies
- **Requires completed:** sp2 (`render_requirements()` pipeline + shell slots).
- **Assumed codebase state:** `renderer.py` renders recipe sections + unmodeled sections into the
  sp1 shell; the Goal Card + Directional slots are placeholders awaiting this sub-phase.

## Scope
**In scope (WP-C — Goal Card + pill):**
- `requirements_render/goal_card.py`: `extract_job_statement(...)`, `derive_l2_assertions(...)` —
  pure deterministic heuristics, unit-tested in isolation.
- The Goal Card render: family pill (`FAMILY_PILL_LABELS[family]` text,
  `class="family-pill family-pill--{value}"`, `title="{classification.reasoning}"`), version chip
  (`v{n}` from `requirement_version_service.get_current()`, omitted when no snapshot), the
  `[PENDING Phase 4]` open-comment-count **template slot** (renders nothing until Phase 4), the L1
  job statement, the 3–5 L2 assertions, and the side-by-side **open** scope grid.

**In scope (WP-D — disclosure + WHAT/HOW):**
- Disclosure boundary: only depth (acceptance scenarios, EARS, independent tests, FR/SC tables,
  constraint detail, evidence detail beyond lead, rationale) wraps in closed `<details>`; the WHAT
  (Goal Card, section lead assertions, scope compare) is **always open**.
- A11y/print: every `<summary>` has discernible visible text (the section's assertion heading);
  `@media print` force-open (sp1 CSS) + the "expand all" control (sp1) cover deep review.
- WHAT-before-HOW: the `DIRECTIONAL` block renders **last** in `.question-annotation` muted/italic,
  marked "non-binding — subject to change by exploration"; omitted entirely (never padded) when the
  family makes HOW irrelevant (`data_analysis`, `personal_non_eng`) AND no Directional block exists;
  rendered when an author wrote genuine Directional content even in such families.
- Tentative-vs-decided grammar: `.callout` accent = decided WHAT; `.question-annotation` = open.

**Out of scope (do NOT do these):**
- `is_stub` (Phase 1) and the GENERIC/unrecognized rescues (sp2) — already done.
- Service/route/file I/O (sp4); goldens/checker/eval (sp5a).
- Wiring the live open-comment count (Phase 4) — leave the `[PENDING Phase 4]` slot inert.
- Inventing assertions to fill a sparse card (honest degradation only).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/goal_card.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/renderer.py` | Modify | sp2 pipeline — wire Goal Card + Directional grammar; call `goal_card.py` |
| `cast-server/cast_server/requirements_render/templates/document.html.j2` | Modify | Fill Goal Card slot, scope grid, Directional grammar, `<details>` disclosure |
| `cast-server/tests/test_goal_card.py` | Create | Unit tests for the IA heuristics |
| `cast-server/tests/test_requirements_renderer.py` | Modify | Add disclosure/WHAT-before-HOW structural assertions |

## Detailed Steps

### Step 3.1: `goal_card.py` — `extract_job_statement`
Deterministic priority: the bolded `**Job statement:**` lead inside the `INTENT` block when present;
else the Intent's first sentence; if neither yields a sentence, **emit a render warning** ("no job
statement — SC-001 at risk") and fall back to the H1 title. Return the statement + any warning so
`renderer.py` can thread it into `RenderResult.warnings`.

### Step 3.2: `goal_card.py` — `derive_l2_assertions`
Deterministic priority order, **capped at 5, never padded**: SC rows (criterion text — the
outcomes) → Out-of-Scope bullets (lead phrase, rendered as boundaries) → for families whose recipes
carry neither (`bug_fix`, `random_idea`): the Intent's enumerated thread / numbered-list items.
Fewer than 3 available ⇒ return what exists (a sparse card is honest; an invented assertion is a lie
to the reader).

### Step 3.3: Render the Goal Card (always open, outside any `<details>`)
In `renderer.py`, call the two heuristics and render the Goal Card into its slot: pill (text +
`family-pill--{value}` + `title` reasoning; `family-pill--unclassified` text for the rescue state),
version chip (omit when `get_current()` has no snapshot), the `[PENDING Phase 4]` comment-count slot
(inert), the L1 job statement (`.l1-body`/`.slide-title`), the 3–5 L2 assertions (`.l2-body`).

### Step 3.4: Scope compare — open, side-by-side
Left column = primary outcomes (SC criteria or Intent threads) in `.callout` accent; right column =
Out-of-Scope bullets, muted. Renders **open** (a comparison is never collapsed). Omit the grid
entirely when the family's recipe has no `SCOPE` block.

### Step 3.5: Disclosure boundary
Wrap only depth in closed `<details>` (see In-scope list). Each user story renders heading + story
sentence **open** (L2), depth collapsed (L3). The WHAT is never behind `<details>` — structurally
testable. Every `<summary>` carries the section's assertion heading as visible text.

### Step 3.6: WHAT-before-HOW (Directional)
Render `DIRECTIONAL` last, in `.question-annotation` muted/italic, marked
"non-binding — subject to change by exploration". Omit entirely (never pad) when the family makes HOW
irrelevant AND no Directional block exists; render it when an author wrote genuine Directional
content (the render is not a second enforcement point — Phase 2's checker already WARNs on it).

## Verification

### Automated Tests (permanent)
`cast-server/tests/test_goal_card.py` (IA core, no full render needed):
- `test_job_statement_prefers_bold_lead` / `..._falls_back_to_first_sentence` /
  `..._warns_and_uses_title_when_absent`.
- `test_l2_assertions_priority_order` (SC → out-of-scope → intent threads), `..._caps_at_5`,
  `..._never_pads_when_sparse` (returns <3 when only <3 exist).

`cast-server/tests/test_requirements_renderer.py` (structural additions):
- `test_goal_card_outside_details`: the Goal Card (pill, job statement, assertions, scope compare)
  is NOT inside any `<details>`.
- `test_what_never_collapsed`: section lead assertions + scope compare are open; only depth is in
  `<details>`.
- `test_pill_has_family_class` and `test_unclassified_pill_state` (rescue text + class).
- `test_scope_grid_open_or_omitted`: scope grid renders open when the recipe has `SCOPE`, absent
  otherwise.
- `test_directional_muted_last_or_omitted`: Directional last + `.question-annotation` when present;
  omitted (not padded) for `data_analysis`/`personal_non_eng` with no Directional content; rendered
  when authored.
- `test_every_summary_has_text`: no empty `<summary>`.

### Validation Scripts (temporary)
- Render the full-spec fixture + a sparse-family fixture (`random_idea`) to `/tmp`; eyeball that the
  Goal Card states the WHAT with zero clicks and the sparse card degrades honestly.

### Manual Checks
- Open the rendered HTML and, **without clicking**, try to state the job + primary outcome + in/out
  scope from the Goal Card alone. This is the human dry-run of the SC-001 gate (the automated gate is
  sp5a's checker eval).

### Success Criteria
- [ ] `extract_job_statement` + `derive_l2_assertions` exist in `goal_card.py`, pure + unit-tested.
- [ ] Goal Card renders zero-click, outside any `<details>`: pill (+reasoning title), version chip
      (omittable), inert `[PENDING Phase 4]` slot, L1 job statement, 3–5 L2 assertions.
- [ ] Scope compare renders open side-by-side (or omitted when no `SCOPE` recipe block).
- [ ] Only depth collapses; WHAT never behind `<details>`; every `<summary>` has visible text.
- [ ] Directional muted/italic, last, omit-not-pad; tentative-vs-decided grammar visible.
- [ ] `cd cast-server && pytest tests/test_goal_card.py tests/test_requirements_renderer.py` passes.

## Execution Notes
- The "no job statement" warning is the renderer's only lever on authoring quality — make it loud and
  thread it into `RenderResult.warnings`; sp5a's eval surfaces it per family.
- Honest degradation is a hard rule: never synthesize an assertion to reach 3. The per-family golden
  + checker eval (sp5a) make a weak card *visible per family*, which is the intended signal.
- Keep IA logic in `goal_card.py`; `renderer.py` only *calls* it (plan-review #3) — the SC-001 core
  must be testable without rendering a full document.

**Spec-linked files:** none modified here are spec-linked.
