# sp1_taxonomy_module — Output

**Status:** ✅ Completed. All success criteria met; 104 new tests green; Phase 1 regression green.

## What landed

### 1. `cast-server/cast_server/requirements_render/families.py` (NEW — the keystone)
The single module every other Phase 2 sub-phase imports (sp2b imports it; sp2c mirrors
`REQUIRED_SECTIONS_BY_FAMILY` deliberately rather than importing). Public contract — **treat as
frozen** now that it is green:

- **`WorkFamily(str, Enum)`** — 9 values: `new_initiative, pilot_poc, bug_fix, data_analysis,
  random_idea, testing_qa, refactor_migration, personal_non_eng, generic`.
- **`RecipeBlock(str, Enum)`** — 6 values: `problem, evidence, decision, scope, question, open`.
- **`FAMILY_RECIPES: dict[WorkFamily, tuple[RecipeBlock, ...]]`** — verbatim from the Naming
  Contract. `FAMILY_RECIPES[RANDOM_IDEA] == (RecipeBlock.PROBLEM,)` (the floor).
- **`RECIPE_REALIZATION: dict[RecipeBlock, Realization]`** — `Realization` is a frozen dataclass
  carrying `h2_primary: str`, `headings: tuple[str, ...]`, `block_kinds: tuple[BlockKind, ...]`.
  `h2_primary` is the dedupe key `modulate()` uses (both `PROBLEM` and `QUESTION` → `"Intent"`).
  Wired to the **real** `BlockKind` vocabulary imported from `blocks.py`, not a copy.
- **`SECTION_TO_RECIPE_BLOCKS: dict[str, frozenset[RecipeBlock]]`** — derived reverse index
  (H2 heading → realizing recipe blocks). Handy for sp2c / profile checks. `"Intent"` →
  `{PROBLEM, QUESTION}`.
- **`REQUIRED_SECTIONS_BY_FAMILY: dict[WorkFamily, tuple[str, ...]]`** — verbatim; hand-derived
  (DECISION's depth is family-weighted). `Open Questions` is in **no** profile;
  `random_idea` → `("Intent",)`.
- **`FAMILY_PILL_LABELS: dict[WorkFamily, str]`** — emoji-prefixed label text per family
  (e.g. `BUG_FIX: "🐛 You are fixing a bug"`). Phase 3a owns the HTML/CSS
  (`family-pill family-pill--{value}`); hover shows `reasoning`.
- **`GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5`**, `GateAction = Literal["auto","confirm","choose"]`.

Functions (all pure; signatures are the frozen interface downstream consumes):
- **`gate(confidence: float) -> GateAction`** — `>=0.9 auto`, `>=0.5 confirm`, else `choose`.
- **`validate_classification(raw: dict) -> Classification`** — never raises on any input.
  `Classification` is a frozen dataclass (`family, confidence, alt_family, reasoning,
  uncertainty_factors, modifiers: Modifiers, coercions: tuple[str, ...]`). **Decision D2:** every
  coercion lands on `RANDOM_IDEA`; `GENERIC` is never a coercion target. Invalid/missing
  confidence → `0.0` (forces `choose`). Each coercion is recorded in `coercions` (zero silent
  failures).
- **`merge_front_matter(existing_text: str, classification: dict) -> str`** — **Decision D3**,
  deterministic & **stdlib-only** (no YAML writer). Surgically replaces only the
  `classification:` block; every other front-matter key and the document **body** survive
  **byte-for-byte**. Idempotent (re-merging produces identical output, never a duplicate block).
  Creates a header if the doc has none. Strings are double-quoted+escaped so colons in
  `reasoning` are safe. Canonical key emission order → deterministic regardless of input dict
  ordering.
- **`modulate(recipe, *, irreversible, unknown_cause) -> tuple[RecipeBlock, ...]`** —
  **Decision D4.** `irreversible` → ensure `SCOPE`; `unknown_cause` → ensure spike-framed
  `OPEN` (NOT `QUESTION`, which would emit a second `## Intent`). Dedupe is at the **H2 target**
  level, so it is impossible to emit a duplicate heading for any family × modifier combination.

### 2. `cast-server/cast_server/requirements_render/blocks.py` (MODIFIED — additive)
Added the two Phase-1 Suggested-Revision-#1 BlockKinds (they were **absent** — Phase 1 did not
land them): `BlockKind.EVIDENCE = "evidence"`, `BlockKind.DECISION = "decision"`.

### 3. `cast-server/cast_server/requirements_render/parser.py` (MODIFIED — additive mapping)
Added two section→kind cases so `## Evidence` → `EVIDENCE` and `## Decisions` → `DECISION`
render as whole-section typed blocks instead of landing in `unrecognized_sections`.

> **Scope note / deviation:** sp1's plan lists "no `parser.py` edits" as out-of-scope, but Step 1.1
> (and SR #1 in the shared context) require the new BlockKinds to be wired into the
> section→kind mapping "so they no longer land in `unrecognized_sections`." That mapping
> structurally lives in `parser.py`'s `parse_requirements`, not `blocks.py`. The edit is the
> minimal 2-line additive case required by Step 1.1 — it changes no existing parse behavior and
> does **not** wire classification logic into the parser. Verified: a doc with `## Evidence` /
> `## Decisions` now yields `evidence` / `decision` blocks and `unrecognized_sections == ()`.

### 4. `cast-server/tests/test_families.py` (NEW — 104 tests)
Covers every case the plan's Verification section requires: recipe invariants (lead block ∈
{PROBLEM, QUESTION}, RANDOM_IDEA floor, OPEN-never-required), gate boundaries (0.9/0.5/0.49),
`validate_classification` off-schema fixtures (garbage family → random_idea; missing confidence →
0.0 → choose; invalid alt_family → random_idea; never raises; coercions recorded; coercion target
is random_idea not generic), `merge_front_matter` round-trip (status + top-level confidence map
survive, body byte-for-byte, idempotent, header-creation, reparse), no-duplicate-H2 across **every
WorkFamily × every (irreversible, unknown_cause)** combination, profile consistency (every required
section traces to a recipe block; random_idea requires exactly Intent), and the no-reclassify read
path (D6) — author front matter via `merge_front_matter`, read back via `parse_requirements_file`,
assert `front_matter["classification"]["family"]` without invoking any classifier.

## Verification results
- `pytest cast-server/tests/test_families.py` → **104 passed** (0.19s).
- Plan inline import sanity script → OK (9 families, RANDOM_IDEA floor, EVIDENCE/DECISION present).
- Phase 1 regression `pytest test_requirements_parser.py` → **21 passed** (no drift from the
  additive blocks/parser changes).
- `ruff check` on both new files → clean. `/cast-python-best-practices` and
  `/cast-pytest-best-practices` applied while writing.
- No DB tables/migrations added; `spec_grammar.py` untouched.

## For dependent sub-phases (sp2a, sp2b, sp2c, sp3b)
- Import the contract from `cast_server.requirements_render.families`. The public names above are
  frozen — changing them now is a cross-sub-phase break.
- **sp2c (checker):** keep your **mirrored** copy of `REQUIRED_SECTIONS_BY_FAMILY` — do NOT import
  `families.py` (the checker stays a portable stdlib linter, per D5). The authoritative mapping to
  mirror is in the module; pin your test against the full mapping. `SECTION_TO_RECIPE_BLOCKS` and
  `RECIPE_REALIZATION.headings` are available if you want to assert mirror consistency from the
  cast-server side.
- **sp2a (classifier):** output the bare-JSON object `{family, confidence, reasoning,
  uncertainty_factors, alt_family, modifiers}`; `validate_classification` will coerce anything
  off-schema. `Classification.coercions` surfaces what was wrong for the corpus eval.
- **sp2b (gate bin):** call `gate()` and `merge_front_matter()` — do not hand-edit YAML or
  re-implement thresholds.
