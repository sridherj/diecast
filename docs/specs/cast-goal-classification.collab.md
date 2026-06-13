---
feature: cast-goal-classification
module: cast-server
linked_files:
  - cast-server/cast_server/requirements_render/families.py
  - agents/cast-goal-classifier/cast-goal-classifier.md
  - agents/cast-goal-classifier/config.yaml
  - bin/cast-classify-gate
  - bin/cast-spec-checker
  - agents/cast-spec-checker/cast-spec-checker.md
  - agents/cast-refine-requirements/cast-refine-requirements.md
  - templates/cast-spec.template.md
  - cast-server/tests/test_families.py
  - cast-server/tests/test_classify_gate.py
  - cast-server/tests/test_goal_classifier_prompt.py
  - cast-server/tests/test_spec_checker_family.py
  - docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md
last_verified: "2026-06-12"
---

# Cast Goal Classification — Spec

> **Spec maturity:** draft
> **Version:** 1
> **Updated:** 2026-06-12
> **Status:** Draft

## Intent

Refine Requirements v2 makes a requirement document **workflow-aware**: every goal
writeup is sorted into exactly one of nine `WorkFamily` values, and that family — not a
single rigid template — shapes the document via a composable **block-recipe** model. The
load-bearing design floor (exploration Playbook 03) is that `random_idea` is the
**default and the structural floor**, never a failure mode: its recipe is `(PROBLEM,)`,
so a half-formed thought structurally *cannot* acquire padded scope/metric/acceptance
tables — the recipe never offers those slots and the checker errors on them if added.

This spec is the **contract Phases 3a (HTML render) and 3b (router) cite**. It documents,
field by field, the user-facing classification surface that lives in
`cast_server/requirements_render/families.py` and the four executables that consume it:
the `cast-goal-classifier` subagent, the `bin/cast-classify-gate` enforcement point, the
two-level `bin/cast-spec-checker`, and the `cast-refine-requirements` caller (the **only**
v2 caller). The code is authoritative: where this spec and `families.py` ever disagree,
the code wins and this spec is the bug.

Three hard boundaries frame everything below:

- **The family set is LOCKED** — nine values, no lexical fast-path, no extra families, no
  future callers in v2.
- **The gate is code, not the model** (`families.py::gate`) — the classifier emits an
  honest confidence number and never self-gates.
- **The classifier is `dispatch_mode: subagent`** and is deliberately OUTSIDE the
  delegation + output-json contracts — it returns bare JSON as its final assistant
  message and writes no `.output.json` envelope.

## User Stories

### US1 — Every writeup is classified into exactly one locked WorkFamily (Priority: P1)

**As a** user refining a goal writeup, **I want** my work sorted into the single
best-fitting work family with an honest confidence signal, **so that** the document I get
is shaped to the kind of work I am actually doing rather than a one-size template.

**Independent test:**
`cast-server/tests/test_goal_classifier_prompt.py` asserts the nine family strings named
in the classifier prompt are exactly `WorkFamily`'s values; `cast-server/tests/test_families.py`
asserts `validate_classification` coerces any off-taxonomy `family` to `random_idea` and
records the coercion.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the classifier receives a goal `title` + `writeup`, THE SYSTEM
  SHALL emit exactly one bare JSON object `{family, confidence, reasoning,
  uncertainty_factors, alt_family, modifiers}` whose `family` is one of the nine
  `WorkFamily` values: `new_initiative`, `pilot_poc`, `bug_fix`, `data_analysis`,
  `random_idea`, `testing_qa`, `refactor_migration`, `personal_non_eng`, `generic`.
- **Scenario 2:** WHEN the classifier is in genuine doubt between two families, THE
  SYSTEM SHALL resolve the tie to `random_idea` (the structural floor), never pad a
  half-formed thought up into a fuller family.
- **Scenario 3:** WHEN the writeup has real shape but fits none of the eight named
  families, THE SYSTEM SHALL select `generic`; `generic` is **model-selected only** and is
  never a coercion target.
- **Scenario 4:** WHEN the model returns an off-taxonomy or missing `family`, THE SYSTEM
  SHALL coerce it to `random_idea` via `validate_classification` and record the coercion
  in `coercions` — an off-taxonomy label can never enter the system.

### US2 — The resolved classification persists once as document front-matter (Priority: P1)

**As a** downstream phase (3a render / 3b router), **I want** the classification stored as
a structured `classification:` block in the document's YAML front-matter, **so that** I can
consume `classification.family` without ever re-running the classifier.

**Independent test:**
`cast-server/tests/test_families.py` asserts `merge_front_matter` replaces (or appends) only
the `classification:` block while preserving every other front-matter key and the body
byte-for-byte, and that a "persist once, consume twice" read never triggers a re-classify
(Decision D6 — an automated unit test, not a manual grep).

**Acceptance scenarios:**

- **Scenario 1:** WHEN the caller persists a resolved classification, THE SYSTEM SHALL
  merge a `classification:` block carrying `family`, `confidence`, `alt_family`,
  `reasoning`, `uncertainty_factors`, `modifiers` (`{irreversible, unknown_cause}`),
  `confirmed_by`, `classified_at`, and `taxonomy_version` into the existing YAML header via
  `families.py::merge_front_matter()` — NOT by hand-editing YAML.
- **Scenario 2:** WHEN the document already has a top-level `confidence:` (per-section
  authoring confidence) and a `status:` key, THE SYSTEM SHALL preserve them unchanged —
  classification confidence is nested under `classification.confidence`, so there is no key
  collision.
- **Scenario 3:** WHEN a re-classify runs on a later edit, THE SYSTEM SHALL replace the
  prior `classification:` block in place; THE SYSTEM SHALL NOT re-classify on a render or
  route that merely reads the persisted block.

### US3 — The confidence gate decides in code, with a defined headless policy (Priority: P1)

**As a** system designer, **I want** the silent/confirm/choose decision made by
deterministic code from the model's confidence number, **so that** the gate is
unit-testable and the model can never self-gate.

**Independent test:**
`cast-server/tests/test_classify_gate.py` pipes raw JSON through `bin/cast-classify-gate`
and asserts the `action` and `options` for confidences on each side of the `0.9` and `0.5`
boundaries, and that un-parseable stdin exits 2 while off-schema-but-parseable stdin yields
a valid `random_idea` result and exits 0.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `confidence >= GATE_SILENT` (`0.9`), THE SYSTEM SHALL return action
  `auto` with no options; the caller records the family silently with `confirmed_by: auto`.
- **Scenario 2:** WHEN `GATE_CONFIRM <= confidence < GATE_SILENT` (`0.5`–`0.9`), THE SYSTEM
  SHALL return action `confirm` with the model's single pick pre-selected; an interactive
  caller asks one one-click confirm and records `confirmed_by: user`.
- **Scenario 3:** WHEN `confidence < GATE_CONFIRM` (`0.5`), THE SYSTEM SHALL return action
  `choose` with the model pick, the `alt_family`, and the `random_idea` escape hatch
  (label `just notes / not sure yet`); an interactive caller records `confirmed_by: user`.
- **Scenario 4:** WHEN there is no human to answer (headless / HTTP-delegated run), THE
  SYSTEM SHALL resolve `confirm` → accept the pill with `confirmed_by: auto`, and `choose`
  → `random_idea` with `confirmed_by: fallback`, and in BOTH cases append a
  `classification unconfirmed — <family>` clarification line to Open Questions —
  never block, never guess silently.
- **Scenario 5:** WHEN the classifier subagent errors, times out, or returns unparseable
  output, THE SYSTEM SHALL fall soft to the coerced `random_idea` result, record
  `confirmed_by: fallback`, and append the same Open Questions note — refinement never dies
  on classification.

### US4 — A two-level checker validates family-shaped documents (Priority: P1)

**As a** caller persisting a refined document, **I want** one deterministic linter that can
apply both a generic shape check and a per-family profile, **so that** a document is held to
exactly the sections its family requires — no more, no less.

**Independent test:**
`cast-server/tests/test_spec_checker_family.py::test_mirror_matches_families` imports the
real `REQUIRED_SECTIONS_BY_FAMILY` and asserts the checker's mirrored copy equals it as a
FULL mapping (every family's exact section tuple), so the mirror can never silently drift.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `bin/cast-spec-checker` runs with no `--family` flag, THE SYSTEM
  SHALL apply the unchanged full-spec (Level-1) profile — required sections `User Stories`,
  `Functional Requirements`, `Success Criteria`, `Open Questions` — byte-for-byte as before
  v2.
- **Scenario 2:** WHEN the checker runs with `--family <value>`, THE SYSTEM SHALL select
  that family's `REQUIRED_SECTIONS_BY_FAMILY` profile for the Level-2 required-section
  check; the checker obtains the family from the **CLI flag** supplied by the caller, never
  by parsing front-matter (Decision D1 — it has no YAML reader and stays a portable stdlib
  linter).
- **Scenario 3:** WHEN a floor family (`random_idea`, `personal_non_eng`) carries an
  empty-or-placeholder spec-kit depth section (`User Stories` / `Functional Requirements` /
  `Success Criteria` / `Out of Scope`), THE SYSTEM SHALL emit an error (the Template-Enforcer
  guard) — the recipe offers no such depth to pad; present-with-real-content is always fine.
- **Scenario 4:** WHEN `--family` is given a value not in the mirrored mapping, THE SYSTEM
  SHALL exit with an invocation error naming the valid values.

### US5 — Family recipes shape the document via composable blocks (Priority: P1)

**As a** render/author caller, **I want** each family mapped to an ordered recipe of
semantic blocks that realize to concrete H2 sections, **so that** the document is assembled
from a composable model rather than a rigid per-family template.

**Independent test:**
`cast-server/tests/test_families.py` asserts every `FAMILY_RECIPES` entry leads with
`PROBLEM` or `QUESTION`, that `FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)` exactly, and that
every `REQUIRED_SECTIONS_BY_FAMILY` section traces back to a recipe block in that family
while `Open Questions` appears in no family profile.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a family is selected, THE SYSTEM SHALL take `FAMILY_RECIPES[family]`
  (an ordered tuple of `RecipeBlock` values: `problem`, `evidence`, `decision`, `scope`,
  `question`, `open`) as the render skeleton; the first slot is always the mandatory lead
  framing block (`problem` OR `question`, never both — both realize to `## Intent`).
- **Scenario 2:** WHEN realizing a recipe, THE SYSTEM SHALL map each block through
  `RECIPE_REALIZATION` to its H2 headings and parser `BlockKind`s: `problem`/`question` →
  `## Intent`; `evidence` → `## Evidence`; `decision` → `## Decisions` (+ `## User Stories`
  / `## Functional Requirements` / `## Success Criteria` depth where the family requires);
  `scope` → `## Out of Scope` + `## Constraints`; `open` → `## Open Questions`.
- **Scenario 3:** WHEN the `modifiers` carry `irreversible` or `unknown_cause`, THE SYSTEM
  SHALL apply `families.py::modulate()` — `irreversible` ensures a `SCOPE` block,
  `unknown_cause` appends a spike-framed `OPEN` block (NOT `QUESTION`, which would emit a
  second `## Intent`) — deduping at the realization-target (H2) level (Decision D4).
- **Scenario 4:** WHEN the family makes HOW irrelevant (`data_analysis`, `personal_non_eng`),
  THE SYSTEM SHALL omit `## Directional ideas` rather than pad it; the checker WARNs (never
  errors) if directional content is present for those families.

### US6 — Adding a family follows a fixed checklist and bumps the taxonomy version (Priority: P2)

**As a** future maintainer evolving the taxonomy, **I want** a single checklist of every
site that must change, **so that** the nine load-bearing surfaces never drift out of sync.

**Independent test:**
`cast-server/tests/test_families.py` consistency tests fail if a `WorkFamily` value lacks a
`FAMILY_RECIPES` entry, a `REQUIRED_SECTIONS_BY_FAMILY` row, or a `FAMILY_PILL_LABELS`
entry — three of the checklist items are mechanically enforced.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a new family is added, THE SYSTEM SHALL require all six co-located
  edits — (1) the `WorkFamily` enum value, (2) a `FAMILY_RECIPES` recipe, (3) a
  `REQUIRED_SECTIONS_BY_FAMILY` profile row (mirrored into `bin/cast-spec-checker`), (4) a
  classifier prompt line, (5) a `FAMILY_PILL_LABELS` pill label, and (6) a corpus-eval
  fixture — **and** a bump of `taxonomy_version`.
- **Scenario 2:** WHEN the family set changes, THE SYSTEM SHALL bump the front-matter
  `taxonomy_version` (currently `1`) so persisted classifications record which taxonomy
  produced them (FR-012 OSS evolution).

> **Routing extension (Phase 3b — `cast-workflow-routing.collab.md`, Decision D3).** This is
> the ONE canonical add-a-family checklist; the routing spec appends its homes here rather
> than restating a second list. When evolving the taxonomy, also touch the routing layer:
> - **Add-a-family routing home:** add a matching `WORKFLOW_REGISTRY` entry in
>   `cast-server/cast_server/config.py` (string key = the new `WorkFamily` value,
>   `status: "stub"`, non-empty `steps`). The registry/enum key-set pin test
>   (`set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}`) is the CI backstop against a
>   forgotten entry.
> - **Graduate-a-family (`stub → implemented`):** flip that entry's `status` to
>   `"implemented"` and set its `pipeline_ref` — a registry-only diff with no seam change
>   (the seam-not-pipelines rule). The resolver, recorder, `/route` endpoint, and schema stay
>   untouched.
>
> See [`cast-workflow-routing.collab.md`](./cast-workflow-routing.collab.md) for the full
> routing contract; it cites this checklist rather than duplicating it.

### US7 — The classifier sits outside the delegation and output-json contracts (Priority: P2)

**As a** maintainer reading the runtime contracts, **I want** it stated explicitly that the
classifier subagent does not produce a delegation envelope, **so that** nobody "fixes" it to
emit an `.output.json` it was deliberately designed never to write.

**Independent test:**
`cast-server/tests/test_goal_classifier_prompt.py` asserts the classifier prompt declares
bare-JSON-as-final-message output and writes no files; the agent's `config.yaml` pins
`dispatch_mode: subagent`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the classifier is dispatched, THE SYSTEM SHALL invoke it via the
  Agent tool as a `dispatch_mode: subagent` agent (no cast-server dependency, no polling) —
  never via HTTP dispatch.
- **Scenario 2:** WHEN the classifier completes, THE SYSTEM SHALL return its result as a
  single bare JSON object that is its entire final assistant message, with NO `.output.json`
  envelope and NO files written; it is therefore outside both
  `cast-delegation-contract.collab.md` and `cast-output-json-contract.collab.md`.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `WorkFamily(str, Enum)` in `families.py` defines the LOCKED nine values: `new_initiative`, `pilot_poc`, `bug_fix`, `data_analysis`, `random_idea`, `testing_qa`, `refactor_migration`, `personal_non_eng`, `generic`. The enum is the single source of truth; the classifier prompt's nine values are pinned against it by `test_goal_classifier_prompt.py`. | `data_analysis` won the name over the playbook's draft `data_research`. |
| FR-002 | `random_idea` is the DEFAULT and the structural floor: `FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)`. ALL `validate_classification` safety coercions land on `random_idea` (Decision D2). `generic` is model-selected only and is never a coercion target. | The Template-Enforcer anti-pattern is prevented structurally — no slots to pad. |
| FR-003 | The classifier emits exactly one bare JSON object `{family, confidence, reasoning, uncertainty_factors, alt_family, modifiers}` as its entire final message — no prose, no code fences. Input is `title` + `writeup` (+ optional `prior_classification` on re-classify). | I/O contract; `modifiers` = `{irreversible: bool, unknown_cause: bool}`. |
| FR-004 | `validate_classification(raw: dict) -> Classification` never raises: it coerces `family`/`alt_family` to `random_idea`, `confidence` to `0.0`, and `modifiers` to defaults when off-schema, recording every coercion in `coercions`. `confidence` is clamped to `[0.0, 1.0]`; `bool` is rejected as a confidence. | Defence in depth even though the prompt is enum-constrained. |
| FR-005 | The `classification:` front-matter block carries, in canonical order: `family` (a `WorkFamily` value — the ONE field the Phase 3b router consumes), `confidence` (raw model number), `alt_family`, `reasoning`, `uncertainty_factors`, `modifiers` (`{irreversible, unknown_cause}`), `confirmed_by`, `classified_at` (ISO-8601), `taxonomy_version` (currently `1`). | `confirmed_by` ∈ `{auto, user, fallback}`. Nested `confidence` never collides with the top-level per-section `confidence:`. |
| FR-006 | `merge_front_matter(existing_text, classification) -> str` is a deterministic stdlib-only helper (Decision D3) that replaces (or appends) ONLY the `classification:` block, preserving every other front-matter key and the document body byte-for-byte. The caller/gate calls it instead of hand-editing YAML. | Persistence is code, not LLM discipline. Emits keys in `_CLASSIFICATION_KEY_ORDER`, extras sorted after. |
| FR-007 | `GATE_SILENT = 0.9` and `GATE_CONFIRM = 0.5` are constants in `families.py`. `gate(confidence) -> "auto" | "confirm" | "choose"` with boundary semantics `>= 0.9 → auto`, `>= 0.5 → confirm`, else `choose`. The model never self-gates (the plan's gate-in-code requirement). | `choose` is the safe direction — show the chooser. |
| FR-008 | `bin/cast-classify-gate` reads the classifier's raw JSON on stdin, runs `validate_classification` + `gate`, and emits `{classification, action, options}` on stdout. It imports `families.py` on purpose (it is part of the classify orchestration). Exit 0 on any parseable stdin (off-schema still yields a valid `random_idea`); exit 2 on un-parseable stdin (treated as data, never evaluated). | `options`: `auto` → `[]`; `confirm` → the single pick pre-selected; `choose` → pick + `alt_family` + `random_idea` escape hatch (`just notes / not sure yet`), deduped by family. |
| FR-009 | The headless / non-interactive policy: `confirm` → accept the pill, `confirmed_by: auto`; `choose` → `random_idea`, `confirmed_by: fallback`; classifier failure → coerced `random_idea`, `confirmed_by: fallback`. All three append a `classification unconfirmed — <family>` clarification line to Open Questions. | Never block, never guess silently. Mirrors the interactive `auto`/`confirm`/`choose` actions. |
| FR-010 | `bin/cast-spec-checker` is ONE deterministic linter with TWO levels: Level 1 (generic shape) always runs; Level 2 (per-family profile + assertions) is selected by a `--family <value>` CLI flag. No `--family` → the unchanged full-spec path. The checker obtains the family from the flag, never from front-matter (Decision D1) — it has no YAML reader and stays a portable stdlib linter. | One checker, not per-family checker agents (owner Decision #1). |
| FR-011 | The checker keeps a MIRRORED copy of `REQUIRED_SECTIONS_BY_FAMILY` rather than importing `families.py`, because it must run where `cast-server` is not importable (Decision D5). `test_spec_checker_family.py::test_mirror_matches_families` pins the FULL mapping (every family's exact tuple) so the mirror can never drift. This is the OPPOSITE policy from `bin/cast-classify-gate`, which imports `families.py`; the divergence is intentional and documented in both bins' headers. | Do NOT unify the two bins. |
| FR-012 | `FAMILY_RECIPES: dict[WorkFamily, tuple[RecipeBlock, ...]]` is the ordered render skeleton per family. Every recipe's first slot is `PROBLEM` or `QUESTION` (both realize to `## Intent`). `OPEN` in a recipe means *allowed at that position*, NEVER required by the checker for any family. `RECIPE_REALIZATION: dict[RecipeBlock, Realization]` maps each block to its H2 headings + parser `BlockKind`s; only `new_initiative` requires the full `## User Stories` / `## Functional Requirements` / `## Success Criteria` depth of `decision`. | Recipe blocks = semantic doc roles; `BlockKind`s = spec-kit grammar — a deliberate two-layer mapping. |
| FR-013 | `REQUIRED_SECTIONS_BY_FAMILY: dict[WorkFamily, tuple[str, ...]]` is hand-derived from the recipes (NOT auto-computed — `decision`'s realization is family-weighted). A consistency test asserts every required section's source recipe block is in that family's recipe, that `Open Questions` appears in NO family profile, and that `random_idea` requires exactly `("Intent",)`. | `OPEN` is allowed-not-required everywhere. |
| FR-014 | `modulate(recipe, *, irreversible, unknown_cause)` applies reversibility/uncertainty as block-inclusion modifiers, NOT families (Decision D4): `irreversible` ensures a `SCOPE` block; `unknown_cause` appends a spike-framed `OPEN` block (not `QUESTION`). Dedupe is at the realization-target (H2) level so `PROBLEM`/`QUESTION` collapse correctly. The operation is idempotent. | `irreversible`/`unknown_cause` are within-family modifiers, never `WorkFamily` values. |
| FR-015 | The classifier is `dispatch_mode: subagent` (owner Decision #2): invoked via the Agent tool, no cast-server dependency, no polling. It returns its JSON as the final assistant message and writes NO `.output.json` envelope and NO files. It is therefore deliberately OUTSIDE `cast-delegation-contract.collab.md` and `cast-output-json-contract.collab.md`. | Subagent calls are auto-captured as runs (free observability) per `cast-subagent-and-skill-capture.collab.md`. Do not "fix" it to emit an envelope. |
| FR-016 | Adding a new family requires six co-located edits — enum value, `FAMILY_RECIPES` recipe, `REQUIRED_SECTIONS_BY_FAMILY` profile row (mirrored into the checker), classifier prompt line, `FAMILY_PILL_LABELS` pill label, corpus-eval fixture — AND a `taxonomy_version` bump. | The add-a-family checklist; three items are mechanically test-enforced. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | This spec passes `bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md` (no `--family` → full-spec profile) with zero error findings. | `bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md` exits 0. |
| SC-002 | Every `families.py` public name (the nine `WorkFamily` values, `FAMILY_RECIPES`, `RECIPE_REALIZATION`, `REQUIRED_SECTIONS_BY_FAMILY`, `GATE_SILENT`, `GATE_CONFIRM`, `gate`, `validate_classification`, `merge_front_matter`, `modulate`) appears in this spec with matching spelling. | Name-match audit: `grep -oE` over the nine values returns all nine; manual cross-check of dict/function names against `families.py`. |
| SC-003 | The gate's `auto`/`confirm`/`choose` boundaries and the headless `confirm→auto` / `choose→random_idea(fallback)` policy are documented exactly as implemented in `bin/cast-classify-gate` + `cast-refine-requirements`. | `cast-server/tests/test_classify_gate.py` boundary tests are green; the gate spec rows match the code. |
| SC-004 | The two-level checker contract (Level 1 always; Level 2 via `--family`; no flag → full-spec; mirrored mapping with pin test) is documented and matches `bin/cast-spec-checker`. | `cast-server/tests/test_spec_checker_family.py::test_mirror_matches_families` is green. |
| SC-005 | The spec is registered in `docs/specs/_registry.md` with a scope one-liner and linked files. | `grep -c 'cast-goal-classification' docs/specs/_registry.md` ≥ 1. |
| SC-006 | The spec states the classifier sits outside the delegation + output-json contracts, with an explicit "do not fix it to emit an envelope" instruction. | Manual check: the subagent-dispatch requirement, US7, and Out of scope all state it. |

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-11 | One deterministic `bin/cast-spec-checker` with two levels | Per-family checker agents | A portable stdlib linter runs in CI/pre-commit where `cast-server` is not importable; one binary is simpler and deterministic (owner Decision #1). |
| 2026-06-11 | Classifier `dispatch_mode: subagent` | HTTP dispatch with output envelope | No cast-server dependency, no polling; bare-JSON-as-final-message is the seam (owner Decision #2). |
| 2026-06-11 | Checker gets family via `--family` CLI flag | Parsing front-matter in the checker | Keeps the checker a YAML-reader-free portable linter (Decision D1). |
| 2026-06-11 | All safety coercions land on `random_idea`; `generic` model-selected only | Coercing to `generic` | `random_idea` is the structural floor; padding is the failure mode being prevented (Decision D2). |
| 2026-06-11 | `merge_front_matter()` deterministic helper | Hand-editing YAML | Preserves non-`classification` keys + body byte-for-byte; persistence is code, not LLM discipline (Decision D3). |
| 2026-06-11 | `unknown_cause` appends spike-framed `OPEN` | Appending `QUESTION` | `QUESTION` realizes to `## Intent` and would emit a second Intent; dedupe at the H2 level (Decision D4). |
| 2026-06-11 | Checker keeps a mirrored `REQUIRED_SECTIONS_BY_FAMILY` | Importing `families.py` | Portability; a pin test asserts the full mapping so it cannot drift (Decision D5). |

## Out of scope

The following are explicitly NOT covered by this spec.

- **Code changes to `families.py`, the classifier, or the bins.** This spec is documentation
  lockstep; sp1–sp2c already landed and are authoritative. If the spec and code disagree, the
  code wins and the spec is the bug — never silently "fix" code from the spec.
- **A lexical fast-path** for high-signal writeups. The documented future latency lever; one
  classifier subagent dispatch per refinement (including the `auto` path) is accepted in v2.
- **Additional families or future callers.** The family set is LOCKED at nine; in v2 only
  `cast-refine-requirements` calls the classifier.
- **An `.output.json` envelope for the classifier.** It is `dispatch_mode: subagent` and
  deliberately outside the delegation + output-json contracts (FR-015). Do NOT add one.
- **The Phase 3a HTML render and Phase 3b router themselves.** They CITE this contract; their
  behavior is specified in their own phases.

## Cross-references

- Naming-contract source of truth: `cast-server/cast_server/requirements_render/families.py`.
- Classifier sits outside the delegation contract:
  [`cast-delegation-contract.collab.md`](./cast-delegation-contract.collab.md).
- Classifier writes no contract-v2 envelope:
  [`cast-output-json-contract.collab.md`](./cast-output-json-contract.collab.md).
- Subagent classifier calls are auto-captured as runs:
  [`cast-subagent-and-skill-capture.collab.md`](./cast-subagent-and-skill-capture.collab.md).
- Spec shape rules enforced by the checker: `agents/cast-spec-checker/cast-spec-checker.md`.

## Open Questions

- **[USER-DEFERRED]** A lexical fast-path to skip the classifier subagent for high-signal
  writeups (the documented latency lever). Resolver: revisit once corpus-eval latency data
  exists; out of v2 scope.
- **[USER-DEFERRED]** Whether `taxonomy_version` should gate an automatic re-classify of
  documents persisted under an older taxonomy. v2 records the version but does not migrate;
  resolver: a future OSS-evolution pass.
