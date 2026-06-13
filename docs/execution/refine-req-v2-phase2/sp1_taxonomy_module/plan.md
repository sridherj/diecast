# Sub-phase 1: Taxonomy Module (`families.py`) — the keystone

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package A of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Create `cast-server/cast_server/requirements_render/families.py` — the single module every other
Phase 2 sub-phase imports. It holds the LOCKED `WorkFamily` taxonomy, the `RecipeBlock` document
model, the `FAMILY_RECIPES` render skeletons, the recipe→parser-BlockKind realization map, the
per-family checker profiles, the pill labels, the gate thresholds, and four pure functions
(`validate_classification`, `merge_front_matter`, `gate`, `modulate`). This is the keystone: it
encodes the cross-phase Naming Contract that Phases 3a and 3b adopt verbatim. Build it first; every
downstream interface settles here.

## Dependencies
- **Requires completed:** None within Phase 2. **Phase 1 must be landed** (see `_shared_context.md` →
  "Hard Prerequisite") — this module imports `BlockKind` from `requirements_render/blocks.py` and
  is read back via `parse_requirements_file()`.
- **Assumed codebase state:** `cast-server/cast_server/requirements_render/{blocks.py,parser.py,spec_grammar.py}`
  exist. `BlockKind` has values `intent, user_story, fr, sc, constraint, scope, directional, open_question`.

## Scope

**In scope:**
- The Phase-1 additive revision (Suggested Revision #1): add `BlockKind.EVIDENCE = "evidence"` and
  `BlockKind.DECISION = "decision"` to `blocks.py` + the section→kind mapping, **if Phase 1 did not
  already land them**. Verify first; only add if missing.
- New module `families.py` with the full Naming Contract (enums, dicts, constants).
- `validate_classification(raw: dict) -> Classification` (frozen dataclass) with all safety coercions.
- `merge_front_matter(existing_text: str, classification: dict) -> str` (stdlib, deterministic).
- `gate(confidence: float) -> GateAction` (pure, module-constant thresholds).
- `modulate(recipe, *, irreversible, unknown_cause) -> tuple[RecipeBlock, ...]` with H2-level dedupe.
- The full unit-test suite for all of the above (this is where ~30–40% of the effort goes).

**Out of scope (do NOT do these):**
- The classifier agent (sp2a), the gate bin (sp2b), the checker changes (sp2c) — they *import* this
  module but are separate sub-phases.
- Any DB work — classification persists in front-matter, not tables. Do NOT add tables/migrations.
- Any edit to `parser.py` or `spec_grammar.py` — read-only consumers of this module's output.
- Wiring `cast-refine-requirements` (sp3a).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/families.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/blocks.py` | Modify (conditional) | From Phase 1; may already have EVIDENCE/DECISION |
| `cast-server/tests/test_families.py` | Create | Does not exist |

## Detailed Steps

### Step 1.1: Verify (and if needed, add) the two Phase-1 BlockKinds

```bash
grep -nE 'EVIDENCE|DECISION' cast-server/cast_server/requirements_render/blocks.py
```

If `EVIDENCE`/`DECISION` are absent from `BlockKind`, add them (additive, ~10 lines):
- `EVIDENCE = "evidence"` → section heading `## Evidence` (level-1 whole-section).
- `DECISION = "decision"` → section heading `## Decisions` (level-1 whole-section).
- Add both to the section-heading→`BlockKind` mapping table in `blocks.py` so they no longer land in
  `unrecognized_sections`.

If Phase 1 already added them, do nothing here and note it in your output.

### Step 1.2: Create `families.py` — the static taxonomy

Copy the Naming Contract from `_shared_context.md` verbatim: `WorkFamily`, `RecipeBlock`,
`FAMILY_RECIPES`, `RECIPE_REALIZATION`, `REQUIRED_SECTIONS_BY_FAMILY`, `FAMILY_PILL_LABELS`,
`GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5`.

- `RECIPE_REALIZATION: dict[RecipeBlock, tuple[BlockKind, ...]]` (or a richer structure that also
  carries the H2 heading) — encode the realization table. The **H2 target** per RecipeBlock must be
  derivable because `modulate()`'s dedupe (Step 1.6) operates at the H2 level.
- `FAMILY_PILL_LABELS: dict[WorkFamily, str]` — e.g. `BUG_FIX: "🐛 You are fixing a bug"`. Phase 2
  owns the label text + the rule that hover shows `reasoning`; Phase 3a owns the HTML/CSS
  (`family-pill family-pill--{value}`).

### Step 1.3: `validate_classification(raw: dict) -> Classification`

Frozen dataclass `Classification` mirroring the front-matter shape, plus a
`coercions: tuple[str, ...]` field recording every coercion (zero silent failures). Rules:
- `family` not a valid `WorkFamily` value → `WorkFamily.RANDOM_IDEA` (the floor — **Decision D2**:
  ALL safety coercions land on `random_idea`; `GENERIC` is only ever model-selected, never a
  coercion target).
- `confidence` invalid/missing → `0.0` (forces the `choose` gate — the safe direction).
- `alt_family` invalid → `RANDOM_IDEA`.
- `modifiers` missing → `{irreversible: False, unknown_cause: False}`.
- **Never raises** on any input (defence in depth, even though the agent prompt is enum-constrained).

### Step 1.4: `merge_front_matter(existing_text: str, classification: dict) -> str` (Decision D3)

Deterministic, **stdlib-only**:
- Read the existing `---`-delimited YAML header.
- Set the `classification.*` keys from the passed dict.
- **Preserve every other key** (`status:`, the top-level `confidence:` map, Phase 4 versioning keys)
  and the document **body byte-for-byte**.
- Re-serialize. The authoring agent and the gate bin call this — front-matter persistence is code,
  not LLM discipline.

### Step 1.5: `gate(confidence: float) -> GateAction`

Pure function, thresholds from module constants. `>= 0.9 → "auto"`, `>= 0.5 → "confirm"`, else
`"choose"`. The `choose` action carries options
`[family, alt_family, "just notes / not sure yet" → RANDOM_IDEA]` with the model's pick pre-filled
(accept = one click — the GitHub template-chooser pattern).

### Step 1.6: `modulate(recipe, *, irreversible, unknown_cause) -> tuple[RecipeBlock, ...]` (Decision D4)

Reversibility/uncertainty as block-inclusion **modifiers**, not families:
- `irreversible` (one-way door) → append `SCOPE`.
- `unknown_cause` (never-seen bug → spike shape) → append **spike-framed `OPEN`, NOT `QUESTION`**.
  Rationale: both `PROBLEM` and `QUESTION` realize to `## Intent`, so appending `QUESTION` to a
  `PROBLEM`-led recipe (e.g. `bug_fix`) would emit two `## Intent` sections; the enum-level
  `dict.fromkeys` dedupe can't catch it (distinct enum values, same H2).
- **Dedupe at the realization-target (H2) level**, not just the enum level.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_families.py`

Invest the bulk of the effort here. Required cases:
- **Recipe invariants:** every recipe's first slot ∈ {`PROBLEM`, `QUESTION`} (lead-block rule);
  `FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)` (floor rule); `OPEN` is never in any
  `REQUIRED_SECTIONS_BY_FAMILY` profile (OPEN-never-required).
- **Gate boundaries:** `gate(0.9) == "auto"`, `gate(0.5) == "confirm"`, `gate(0.49) == "choose"`.
- **`validate_classification` off-schema fixtures:** garbage family → `random_idea`; missing
  confidence → `0.0` → `choose`; invalid `alt_family` → `random_idea`; never raises; coercions recorded.
- **`merge_front_matter` round-trip (D3):** a doc carrying `status:` + a top-level `confidence:` map
  → merge `classification:` → assert both survive untouched and the body is byte-for-byte identical.
- **No-duplicate-H2 (D4):** for every `WorkFamily` × every `(irreversible, unknown_cause)` combination,
  `modulate()`'s output maps to **distinct** `RECIPE_REALIZATION` H2 targets.
- **Profile consistency:** every required section's source recipe block is in that family's recipe;
  `Open Questions` in NO profile; `random_idea` requires exactly `("Intent",)`.
- **No-reclassify read path (D6):** author a doc string with `classification.*` front-matter, call
  `parse_requirements_file()`, assert `front_matter["classification"]["family"]` reads back
  **without** invoking any classifier (the Phase 3a/3b consume-twice contract).

→ **Delegate:** `/cast-python-best-practices` over `families.py` and
`/cast-pytest-best-practices` over `test_families.py` while writing. Review output for compliance.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_families.py -v
python -c "from cast_server.requirements_render.families import WorkFamily, FAMILY_RECIPES; assert len(WorkFamily) == 9; assert FAMILY_RECIPES[WorkFamily.RANDOM_IDEA] == ('problem',) or len(FAMILY_RECIPES[WorkFamily.RANDOM_IDEA]) == 1"
```

### Manual Checks
- `grep -c '=' ` sanity: `WorkFamily` has exactly 9 values; `RecipeBlock` has exactly 6.
- Confirm `families.py` imports `BlockKind` from `blocks.py` (the realization layer is wired to the
  real parser vocabulary, not a copy).

### Success Criteria
- [ ] `families.py` exists with all 9 `WorkFamily` values, 6 `RecipeBlock` values, and all five
      module-level dicts/constants matching the Naming Contract byte-for-name.
- [ ] `BlockKind.EVIDENCE` and `BlockKind.DECISION` exist in `blocks.py` (verified or added).
- [ ] `validate_classification`, `merge_front_matter`, `gate`, `modulate` implemented and never raise
      on adversarial input.
- [ ] `pytest cast-server/tests/test_families.py` is green, covering every case above.
- [ ] No DB tables, no `parser.py`/`spec_grammar.py` edits.

## Execution Notes
- This module is imported by sp2b (gate bin, via `sys.path` bootstrap) and mirrored by sp2c (checker,
  which deliberately does NOT import it). Treat the public names as a frozen contract once green —
  changing them after sp2a–sp3b start is a cross-sub-phase break.
- `RANDOM_IDEA` value is `"random_idea"`; `FAMILY_RECIPES[RANDOM_IDEA]` is `(PROBLEM,)` — one element.
  Tests sometimes compare against `("problem",)` (the str values) — be consistent with how the enum
  is realized (`str, Enum` members equal their string values).
- The H2 realization layer is the subtle part: `modulate` dedupe must compare H2 *targets*, so
  `RECIPE_REALIZATION` must expose each RecipeBlock's H2 heading (`problem`→`Intent`,
  `question`→`Intent`, `open`→`Open Questions`, etc.). Design the data structure so this is queryable.

**Spec-linked files:** No spec covers `families.py` yet — sp3b authors `cast-goal-classification.collab.md`
documenting it. No SAV behaviors to preserve in this sub-phase.
