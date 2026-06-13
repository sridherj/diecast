# Shared Context: Refine Requirements v2 — Phase 2 (Classification)

> **Read this file at the start of every sub-phase session.** It is the cross-cutting
> reference — names, contracts, conventions, and decisions — that every `spN_*/plan.md`
> assumes. It is NOT inlined into each sub-phase; read it once, then open your sub-phase file.

## Source Documents
- **Plan:** `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md` (the authoritative spec for this work — read the Work Package that maps to your sub-phase)
- **Cross-phase decisions:** `docs/plan/refine-requirements-v2-decisions-so-far.md` (canonical names/interfaces all phases adopt verbatim)
- **High-level plan:** `goals/refine-requirements-v2/plan.collab.md` (Phase 2 is one of six phases)

## Project Background

Refine Requirements v2 makes requirement documents **workflow-aware** and **HTML-first**. Phase 2
is the **classification** layer: every goal writeup is sorted into one of nine `WorkFamily` values
with a confidence signal, and that classification shapes the document via a composable
**block-recipe** model rather than rigid per-family templates.

The load-bearing design insight (from exploration Playbook 03): the loosest family, `random_idea`,
is the **default and the structural floor** — not a failure mode. The Template-Enforcer anti-pattern
(padding a half-formed thought with empty scope/metric/acceptance tables) is prevented
**structurally**: the loose recipe simply has no such slots to fill. A `random_idea` writeup
*cannot* acquire padded fields because the recipe never offers them and the checker errors on them.

Phase 2 is **ON the critical path**: Phase 3a (HTML render) consumes `FAMILY_RECIPES` +
`RECIPE_REALIZATION` + the pill data; Phase 3b (router) consumes `classification.family`. Phase 2
**sets the names** both downstream phases adopt.

**Operating mode: HOLD SCOPE.** The family set is LOCKED. The build boundary is explicit: ship the
classify *door*, not future callers — in v2 only `cast-refine-requirements` calls the classifier.
No lexical fast-path, no extra families, no future callers. All nine plan-review decisions are final.

## ⚠️ Hard Prerequisite: Phase 1 Must Be Executed First

Phase 2 imports Phase 1's parser package, which **does not exist yet** at planning time
(`cast-server/cast_server/requirements_render/` is absent). Before executing **any** Phase 2
sub-phase, confirm Phase 1 has landed:

```bash
ls cast-server/cast_server/requirements_render/blocks.py    # must exist (BlockKind, Block, ParsedRequirements)
ls cast-server/cast_server/requirements_render/parser.py    # must exist (parse_requirements_file)
ls cast-server/cast_server/requirements_render/spec_grammar.py  # importlib bridge to bin/cast-spec-checker regexes
```

**Phase 2 also requires two additive Phase 1 changes** (Suggested Revision #1 in the plan). If
Phase 1 landed without them, sp1 includes a 10-line follow-up to add them — see sp1's plan:
- `BlockKind.EVIDENCE = "evidence"` (renders `## Evidence`)
- `BlockKind.DECISION = "decision"` (renders `## Decisions`)

Without these two BlockKinds, the `evidence` and `decision` recipe blocks land in
`unrecognized_sections` and Phase 3a cannot render them typed.

## Codebase Conventions

| Convention | Rule |
|---|---|
| **Service DB pattern** | Flat functions, `db_path: Path \| None = None` injectable + `get_connection(db_path)`; modeled on `goal_service.py` / `task_service.py`, **NOT** `orchestration_service.py`. (No DB work in Phase 2 — noted for consistency only.) |
| **Bins** | Stdlib-only executables in `bin/`; deterministic, unit-testable, invoked by agents (precedent: `bin/cast-spec-checker`). A bin that is part of an orchestration MAY `sys.path`-bootstrap and import `cast_server`; a portable linter MUST NOT. |
| **Agents** | Live in `agents/<name>/<name>.md` + `config.yaml`. After creating/editing an agent, run `bin/generate-skills` and verify the generated skill appears. |
| **Specs** | `docs/specs/*.collab.md`, registered in `docs/specs/_registry.md`; authored/edited via `/cast-update-spec`; linted by `bin/cast-spec-checker`. |
| **Prompt ceiling** | `agents/cast-refine-requirements/cast-refine-requirements.md` has a **~650-line ceiling**. Phase 1b and Phase 2 Step 0 share this file. |
| **Python / pytest quality** | Apply `/cast-python-best-practices` + `/cast-pytest-best-practices` when writing code/tests. |

## Key File Paths

| Path | Role | State at Phase 2 start |
|---|---|---|
| `cast-server/cast_server/requirements_render/blocks.py` | `BlockKind`, `Block`, `ParsedRequirements` | From Phase 1 — `front_matter` dict is the classification persistence site |
| `cast-server/cast_server/requirements_render/parser.py` | `parse_requirements_file()` (read-only) | From Phase 1 — never writes the file; classification is written by the agent |
| `cast-server/cast_server/requirements_render/spec_grammar.py` | importlib bridge re-exporting checker regexes | From Phase 1 — **UNTOUCHED by Phase 2** |
| `cast-server/cast_server/requirements_render/families.py` | **NEW (sp1)** — the taxonomy keystone | Does not exist |
| `agents/cast-goal-classifier/` | **NEW (sp2a)** — classifier subagent | Does not exist |
| `bin/cast-classify-gate` | **NEW (sp2b)** — code-side gate enforcement | Does not exist |
| `bin/cast-spec-checker` | Spec linter — **modified (sp2c)** to add two-level inspection | Exists (11.5 KB); grammar regexes stay frozen |
| `agents/cast-spec-checker/cast-spec-checker.md` | Documented shape rules | Exists — sp2c documents the two levels |
| `agents/cast-refine-requirements/cast-refine-requirements.md` (+ `config.yaml`) | The only v2 caller — **modified (sp3a)** | Exists; `config.yaml` has no `allowed_delegations` yet |
| `docs/specs/cast-goal-classification.collab.md` | **NEW (sp3b)** — the contract Phases 3a/3b cite | Does not exist |
| `templates/cast-spec.template.md` | Spec template — `## Evidence` stub added (sp3b) | Exists |

## Data Schemas & Contracts (copy verbatim — the Naming Contract)

All in **`cast-server/cast_server/requirements_render/families.py`** (sp1 creates this):

```python
class WorkFamily(str, Enum):                  # the LOCKED ~8-family set + generic fallback
    NEW_INITIATIVE     = "new_initiative"
    PILOT_POC          = "pilot_poc"
    BUG_FIX            = "bug_fix"
    DATA_ANALYSIS      = "data_analysis"      # playbook drafted "data_research"; LOCKED name wins
    RANDOM_IDEA        = "random_idea"        # the DEFAULT and the structural floor
    TESTING_QA         = "testing_qa"
    REFACTOR_MIGRATION = "refactor_migration"
    PERSONAL_NON_ENG   = "personal_non_eng"
    GENERIC            = "generic"            # unmatched fallback (FR-002/003 Scenario 4)

class RecipeBlock(str, Enum):                 # the 6-block DOCUMENT model
    PROBLEM = "problem"; EVIDENCE = "evidence"; DECISION = "decision"
    SCOPE = "scope"; QUESTION = "question"; OPEN = "open"
```

> `RecipeBlock` is deliberately NOT named `Block` — Phase 1 already owns `Block` (the parser
> dataclass) in this same package. spike = a within-family **modifier** (`unknown_cause`),
> stub = a render-state — neither is a `WorkFamily` value.

```python
FAMILY_RECIPES: dict[WorkFamily, tuple[RecipeBlock, ...]] = {   # ordered render skeleton
    WorkFamily.NEW_INITIATIVE:     (PROBLEM, DECISION, SCOPE, OPEN),
    WorkFamily.PILOT_POC:          (QUESTION, DECISION, OPEN),
    WorkFamily.BUG_FIX:            (PROBLEM, EVIDENCE, OPEN),
    WorkFamily.DATA_ANALYSIS:      (QUESTION, EVIDENCE, OPEN),
    WorkFamily.RANDOM_IDEA:        (PROBLEM,),                    # the floor — nothing to pad
    WorkFamily.TESTING_QA:         (PROBLEM, EVIDENCE, SCOPE, OPEN),
    WorkFamily.REFACTOR_MIGRATION: (PROBLEM, DECISION, SCOPE, OPEN),
    WorkFamily.PERSONAL_NON_ENG:   (PROBLEM, OPEN),
    WorkFamily.GENERIC:            (PROBLEM, OPEN),
}
```

**Recipe invariants (unit-tested):** every recipe's first slot is `PROBLEM` or `QUESTION` (the
mandatory lead framing block — a goal always leads with what's wrong or what we're asking; both
realize to `## Intent`). `OPEN` in a recipe means *allowed at that position* — NEVER required by
the checker for any family. `FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)` exactly.

**Recipe → parser-BlockKind realization (`RECIPE_REALIZATION` in `families.py`):**

| RecipeBlock | Markdown realization (H2) | Parser BlockKind(s) | Notes |
|---|---|---|---|
| `problem` | `## Intent` | `INTENT` | Problem-framed Intent (symptom for bug_fix, job statement for initiatives) |
| `question` | `## Intent` | `INTENT` | Question-framed Intent; a recipe has `problem` OR `question` as lead, never both |
| `evidence` | `## Evidence` | `EVIDENCE` **(NEW BlockKind, Phase 1 SR #1)** | Repro, logs, data sources, links |
| `decision` | `## Decisions` + spec-kit depth (`## User Stories` / `## Functional Requirements` / `## Success Criteria` where the family requires) | `DECISION` **(NEW)**, `USER_STORY`, `FR`, `SC` | US/FR/SC are the *elaboration depth* of decision+scope; only `new_initiative` requires full depth |
| `scope` | `## Out of Scope` + `## Constraints` | `SCOPE`, `CONSTRAINT` | Renders side-by-side, never collapsed (3a) |
| `open` | `## Open Questions` | `OPEN_QUESTION` | Always allowed, never required |

`## Directional ideas` (`BlockKind.DIRECTIONAL`) sits OUTSIDE the recipe model: governed by
US1/FR-001 (WHAT/HOW separation), allowed for any family, **omitted — never padded — when the
family makes HOW irrelevant** (`data_analysis`, `personal_non_eng`).

**Per-family checker profiles (`REQUIRED_SECTIONS_BY_FAMILY` in `families.py`):**

```python
REQUIRED_SECTIONS_BY_FAMILY: dict[WorkFamily, tuple[str, ...]] = {
    WorkFamily.NEW_INITIATIVE:     ("Intent", "User Stories", "Functional Requirements", "Success Criteria", "Out of Scope"),
    WorkFamily.PILOT_POC:          ("Intent", "Decisions"),
    WorkFamily.BUG_FIX:            ("Intent", "Evidence"),
    WorkFamily.DATA_ANALYSIS:      ("Intent", "Evidence"),
    WorkFamily.RANDOM_IDEA:        ("Intent",),
    WorkFamily.TESTING_QA:         ("Intent", "Evidence", "Out of Scope"),
    WorkFamily.REFACTOR_MIGRATION: ("Intent", "Decisions", "Out of Scope"),
    WorkFamily.PERSONAL_NON_ENG:   ("Intent",),
    WorkFamily.GENERIC:            ("Intent",),
}
```

Hand-derived from the recipes (NOT auto-computed — `DECISION`'s realization is family-weighted). Unit
test asserts consistency: every required section's source recipe block is in that family's recipe;
`Open Questions` appears in NO family profile; `random_idea` requires exactly `("Intent",)`.

**Gate thresholds (code, not model — FR-004):** `GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5` in
`families.py`. `gate(confidence) -> "auto" | "confirm" | "choose"`, boundary semantics
`>= 0.9 → auto`, `>= 0.5 → confirm`, else `choose`.

**Front-matter contract** (merged into the EXISTING YAML header of `refined_requirements.collab.md`):

```yaml
classification:
  family: bug_fix                  # a WorkFamily value — the ONE field the Phase 3b router consumes
  confidence: 0.82                 # raw model number; the GATE interpreted it
  alt_family: data_analysis
  reasoning: "Describes a 500 error with a repro; no new scope introduced."
  uncertainty_factors: ["no stack trace attached"]
  modifiers: {irreversible: false, unknown_cause: true}
  confirmed_by: user               # auto (>=0.9 silent) | user (confirm/choose answered) | fallback (off-schema or headless default)
  classified_at: "2026-06-11T17:00:00Z"
  taxonomy_version: 1              # bump when the family set changes (FR-012 OSS evolution)
```

No key collision: the existing top-level `confidence:` is per-section authoring confidence;
classification confidence is nested under `classification`.

**Classifier I/O contract:** input = goal title + raw writeup (+ prior `classification` mapping on
re-classify). Output = EXACTLY ONE bare JSON object —
`{family, confidence, reasoning, uncertainty_factors, alt_family, modifiers}` — no prose, no fences.

## Pre-Existing Decisions (binding — adopt verbatim)

**Owner decisions this session (2026-06-11, interactive):**
1. **Checker = ONE deterministic `bin/cast-spec-checker` with TWO levels** (generic + family-specific),
   not per-family checker agents. Level 1 always runs; Level 2 selected by `--family <value>` CLI flag.
2. **Classifier dispatch = `dispatch_mode: subagent`** (Agent tool, no cast-server dependency, no polling).

**Plan-review decisions (2026-06-11, appended by `cast-plan-review`, all final):**
- **D1:** Checker obtains family via a `--family <value>` **CLI flag** from the caller (not by parsing
  front-matter — the checker has no YAML reader and must stay a portable stdlib linter). No `--family`
  → unchanged full-spec path.
- **D2:** Keep both `generic` and `random_idea`; sharpen the prompt boundary; **ALL** `validate_classification`
  safety coercions land on `RANDOM_IDEA` (`GENERIC` is only ever model-selected). Add a `generic`↔`random_idea`
  confusion-pair check to the corpus eval.
- **D3:** `merge_front_matter()` — deterministic stdlib helper that preserves all non-`classification`
  keys + the body byte-for-byte. The agent/gate call it instead of hand-editing YAML.
- **D4:** `unknown_cause` appends spike-framed `OPEN` (idempotent), NOT `QUESTION` (which would emit a
  second `## Intent`). Dedupe at the realization-target (H2) level, not just the enum level.
- **D5:** Keep the checker's **mirrored** copy of `REQUIRED_SECTIONS_BY_FAMILY` (it does NOT import
  `families.py`); document the deliberate divergence in both bins' headers; pin test asserts the FULL
  mapping, not just key presence.
- **D6:** The "persist once, consume twice" no-reclassify read path is an **automated unit test**, not a
  manual grep.
- **(perf):** One classifier subagent dispatch per refinement (including the `auto` path) is accepted;
  the lexical fast-path is the documented future latency lever (out of v2 scope).

## Relevant Specs

| Spec | Overlap | Note |
|---|---|---|
| `docs/specs/cast-subagent-and-skill-capture.collab.md` | Task()-dispatched cast-* subagent capture | Classifier subagent calls are auto-captured as runs (free observability) — no extra work |
| `docs/specs/cast-delegation-contract.collab.md` | Output-file contract scope | Classifier is subagent-mode and **deliberately outside** this contract (returns JSON as final text, writes no `.output.json`) — sp3b's new spec states this so nobody "fixes" it |
| `docs/specs/cast-output-json-contract.collab.md` | Contract-v2 envelope | Same — classifier returns bare JSON, not an envelope |
| *(new)* `docs/specs/cast-goal-classification.collab.md` | Created by sp3b | Becomes the contract Phases 3a/3b cite |

Do NOT paste spec Behaviors here — read the spec on-demand only when your sub-phase modifies
spec-linked files.

## Sub-Phase Dependency Summary

| Sub-phase | Source WP | Type | Depends On | Blocks | Can Parallel With |
|---|---|---|---|---|---|
| sp1_taxonomy_module | A | Sub-phase | — (Phase 1 landed) | sp2a, sp2b, sp2c, sp3b | — |
| sp2a_classifier_agent | B | Sub-phase | sp1 | sp3a | sp2b, sp2c |
| sp2b_gate_bin | C | Sub-phase | sp1 | sp3a | sp2a, sp2c |
| sp2c_two_level_checker | D | Sub-phase | sp1 | sp3a, sp3b | sp2a, sp2b |
| sp3a_refine_integration | E | Sub-phase | sp2a, sp2b, sp2c | sp4 | sp3b |
| sp3b_spec_template | F | Sub-phase | sp1, sp2a, sp2b, sp2c | — | sp3a |
| sp4_corpus_eval | G | Sub-phase | sp3a | — | — |

No decision gates (HOLD SCOPE — all decisions resolved at plan review).

**Critical path:** sp1 → sp2a/sp2b/sp2c → sp3a → sp4. sp3b (spec/docs) runs parallel with sp3a.
