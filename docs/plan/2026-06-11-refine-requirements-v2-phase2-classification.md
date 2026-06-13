# Refine Requirements v2: Phase 2 — Classification: Family Detection & Block Recipes

## Overview

Every goal gets classified into a work **family** with a confidence signal by a new standalone
`cast-goal-classifier` agent; the result persists ONCE as machine-readable front-matter on
`refined_requirements.collab.md` (humans will read it as a pill in Phase 3a, agents and the Phase 3b
router read the field) and shapes the document via a composable **block-recipe** model instead of
rigid per-family templates. The key insight from exploration (Playbook 03): the loosest family
(`random_idea`) is the **default and the floor**, not a failure mode — and the Template-Enforcer
guard is built *structurally* (the loose recipe has no scope/metric/acceptance slots to pad).

This plan covers ONLY Phase 2 of the high-level plan (`goals/refine-requirements-v2/plan.collab.md`).
It adopts Phase 1's canonical names from `docs/plan/refine-requirements-v2-decisions-so-far.md`:
the `cast_server.requirements_render` package, the `ParsedRequirements` dataclass
(`front_matter` is the persistence site), the parser `BlockKind` vocabulary, and the flat-function
service DB pattern (no DB work is actually needed in this phase — classification persists in
front-matter, not tables).

## Operating Mode

**HOLD SCOPE** — the family set is "LOCKED" and "resolved at plan review", the build boundary is
explicit ("In v2, only `cast-refine-requirements` calls it — ship the door, not the future
callers"), and all nine plan-review decisions are recorded as final. No expansion (no lexical
fast-path, no extra families, no future callers), no reduction (all six delegated activity clusters
are required).

## Decisions Made This Session (owner, 2026-06-11, interactive)

1. **Checker = ONE deterministic `bin/cast-spec-checker` with TWO levels of inspection** (owner
   direction: "there can be two levels of inspection — one generic and one family specific"), not
   per-family checker agents. Level 1 (generic, always runs): front-matter validity, H1 title,
   EARS grammar / FR–SC ID formats / US heading shape *wherever those sections exist*. Level 2
   (family-specific, selected by `classification.family` front-matter): per-family required-section
   profile + per-family assertions (e.g. `random_idea` forbids padded scope/metric/acceptance
   slots). Generic rules are stated once; family deltas are data rows — no duplicated prompts, and
   adding a family stays a config change. Owner also waived backward-compatibility concern; the
   no-family → full-spec profile is kept anyway because `docs/specs/*.collab.md` product specs run
   through the same checker and carry no classification front-matter.
2. **Classifier dispatch = `dispatch_mode: subagent`** (owner: "option 1 is fine for now —
   eventually we'll have a guide agent which will take care of this entire orchestration").
   `cast-refine-requirements` invokes it via the Agent tool; no cast-server dependency, no polling.
   Record the guide-agent note: the classify→gate→confirm orchestration should stay extractable
   (it already is — agent + bin + front-matter contract, no logic buried in the refine prompt).

## Position in Overall Plan

```
Phase 1: Parser & Thin Spine ──► Phase 2: Classification (THIS PLAN) ──┬──► Phase 3a: HTML Render
   (BlockKind model,                 (WorkFamily, FAMILY_RECIPES,      └──► Phase 3b: Router
    front_matter dict)                classification front-matter)            (reads classification.family)
Phase 1b: gbrain upgrades ──────► (shares the cast-refine-requirements prompt + the AskUserQuestion budget)
```

Phase 2 is ON the critical path: 3a consumes `FAMILY_RECIPES` + the pill data; 3b consumes
`classification.family`. Phase 2 also sets the names both of them use (see "Naming Contract" below).

## Depends On (from prior plans)

| Prior deliverable | Where | How Phase 2 consumes it |
|---|---|---|
| `BlockKind(str, Enum)` (intent/user_story/fr/sc/constraint/scope/directional/open_question) | Phase 1 `requirements_render/blocks.py` | `RECIPE_REALIZATION` maps recipe blocks → these parser kinds (two distinct layers — see below) |
| `ParsedRequirements.front_matter: dict` | Phase 1 `requirements_render/blocks.py` | Persistence site: `front_matter["classification"]` — zero parser change needed to read it back |
| `parse_requirements_file()` read-only contract | Phase 1 `parser.py` | Classification is written by the authoring agent, never by the parser |
| `spec_grammar.py` importlib bridge re-exporting checker regexes | Phase 1 | UNTOUCHED — the two-level checker change touches `REQUIRED_SECTIONS` handling only, never the grammar regexes (see Suggested Revisions #2) |
| Dated `## Decisions` section in template + agent prompt | Phase 1b | The `decision` recipe block's primary markdown realization |
| Scope-mode confirm claims one `AskUserQuestion` slot | Phase 1b | Question-budget ordering rule in Work Package E |
| ~650-line prompt ceiling on `cast-refine-requirements.md` | Phase 1b | Step 0 (classify) must stay terse (~60 lines); detail lives in the classifier agent + gate bin |

## Naming Contract (Phase 2 sets these; Phases 3a/3b MUST adopt)

All in **`cast-server/cast_server/requirements_render/families.py`** (new module in the Phase 1
package — classification shapes the document, the render consumes it):

```python
class WorkFamily(str, Enum):                  # the LOCKED ~8-family set + generic fallback
    NEW_INITIATIVE     = "new_initiative"
    PILOT_POC          = "pilot_poc"
    BUG_FIX            = "bug_fix"
    DATA_ANALYSIS      = "data_analysis"      # playbook drafted "data_research"; locked name wins
    RANDOM_IDEA        = "random_idea"        # the DEFAULT and the structural floor
    TESTING_QA         = "testing_qa"
    REFACTOR_MIGRATION = "refactor_migration"
    PERSONAL_NON_ENG   = "personal_non_eng"
    GENERIC            = "generic"            # unmatched fallback (FR-002/003 Scenario 4)

class RecipeBlock(str, Enum):                 # the 6-block DOCUMENT model
    PROBLEM = "problem"; EVIDENCE = "evidence"; DECISION = "decision"
    SCOPE = "scope"; QUESTION = "question"; OPEN = "open"
```

> `RecipeBlock` is deliberately NOT named `Block` (the playbook's draft name) — Phase 1 already owns
> `Block` (the parser dataclass) in this same package. Spike = a within-family **modifier**
> (`unknown_cause`), stub = a render-state — neither is a `WorkFamily` value.

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

**Recipe invariants (unit-tested):** every recipe's first slot is `PROBLEM` or `QUESTION` — the
mandatory *lead framing block* (this is the precise reading of "problem is always present": a goal
always leads with what's wrong or what we're asking; both realize as the `Intent` section, see
mapping). `OPEN` appearing in a recipe means *allowed at that position* — it is NEVER required by
the checker for any family. `FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)` exactly.

**Front-matter key (Phase 3b reads `classification.family`; Phase 3a reads the whole mapping):**

```yaml
classification:
  family: bug_fix                  # a WorkFamily value — the ONE field the router consumes
  confidence: 0.82                 # raw model number; the GATE interpreted it, recorded below
  alt_family: data_analysis
  reasoning: "Describes a 500 error with a repro; no new scope introduced."
  uncertainty_factors: ["no stack trace attached"]
  modifiers: {irreversible: false, unknown_cause: true}
  confirmed_by: user               # auto (>=0.9 silent) | user (confirm/choose answered) | fallback (off-schema or headless default)
  classified_at: "2026-06-11T17:00:00Z"
  taxonomy_version: 1              # bump when the family set changes (FR-012 OSS evolution)
```

Merged into the EXISTING YAML header of `refined_requirements.collab.md` (alongside `status:`,
`confidence:` — no key collision: the existing top-level `confidence` block is per-section
authoring confidence; classification confidence is nested under `classification`).

**Pill data for Phase 3a:** `FAMILY_PILL_LABELS: dict[WorkFamily, str]` in `families.py`
(e.g. `BUG_FIX: "🐛 You are fixing a bug"`); CSS class convention `family-pill family-pill--{value}`
(3a owns the HTML/CSS; Phase 2 owns the label text + the rule that hover shows `reasoning`).

**Recipe → parser-BlockKind realization (the cross-phase mapping the decisions file demands):**

The 6 `RecipeBlock`s and Phase 1's 8 `BlockKind`s are **two distinct layers**: recipe blocks are
*semantic document roles* per family; BlockKinds are the *concrete spec-kit grammar elements* the
parser emits. The bridge, exported as `RECIPE_REALIZATION` in `families.py`:

| RecipeBlock | Markdown realization (H2) | Parser BlockKind(s) | Notes |
|---|---|---|---|
| `problem` | `## Intent` | `INTENT` | Problem-framed Intent (symptom for bug_fix, job statement for initiatives) |
| `question` | `## Intent` | `INTENT` | Question-framed Intent (research question, POC hypothesis) — same section, different treatment; a recipe contains `problem` OR `question` as lead, never both |
| `evidence` | `## Evidence` | `EVIDENCE` **(NEW BlockKind — Suggested Revision #1 to Phase 1)** | Repro, logs, data sources, links |
| `decision` | `## Decisions` (Phase 1b's dated section) + the spec-kit depth `## User Stories` / `## Functional Requirements` / `## Success Criteria` where the family requires them | `DECISION` **(NEW — Suggested Revision #1)**, `USER_STORY`, `FR`, `SC` | US/FR/SC are the *elaboration depth* of decision+scope; only `new_initiative` requires the full depth (see checker profiles) |
| `scope` | `## Out of Scope` + `## Constraints` | `SCOPE`, `CONSTRAINT` | Renders side-by-side, never collapsed (3a) |
| `open` | `## Open Questions` | `OPEN_QUESTION` | Always allowed, never required |

`## Directional ideas` (BlockKind `DIRECTIONAL`) sits OUTSIDE the recipe model: it is governed by
US1/FR-001 (WHAT/HOW separation), allowed for any family, and **omitted — never padded — when the
family makes HOW irrelevant** (`data_analysis`, `personal_non_eng`).

**Per-family checker profiles (level 2), the required-section derivation:**

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

Hand-derived from the recipes (not auto-computed — `DECISION`'s realization is family-weighted), with
a unit test asserting consistency: every required section's source recipe block is in that family's
recipe; `Open Questions` appears in NO family profile; `random_idea` requires exactly `("Intent",)`.
No `classification` front-matter (e.g. `docs/specs/*.collab.md` product specs) → the checker's
existing full-spec `REQUIRED_SECTIONS` applies unchanged.

**Gate thresholds (code, not model — FR-004):** `GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5` in
`families.py`. `gate(confidence) -> "auto" | "confirm" | "choose"` with boundary semantics
`>= 0.9 → auto`, `>= 0.5 → confirm`, else `choose`.

## Sub-phase: Classification — Family Detection & Block Recipes

**Outcome:** A goal writeup fed to `cast-refine-requirements` is classified by the standalone
`cast-goal-classifier` subagent into one of 9 `WorkFamily` values with confidence; code-side gating
decides silent/confirm/choose; the result persists once as `classification.*` front-matter and the
emitted markdown contains exactly the family's recipe sections; the two-level checker validates
per-family shape; a `random_idea` writeup structurally cannot acquire padded scope/metric/acceptance
fields. A downstream consumer reads `classification.family` from front-matter without re-running
the classifier.

**Dependencies:** Phase 1 (parser package, `BlockKind`, `front_matter`); Phase 1b (the `## Decisions`
section the `decision` block realizes to; the shared prompt file + question budget).

**Estimated effort:** 2-3 sessions (A+C ≈ 1, B+E ≈ 1, D+F+G ≈ 1).

**Verification (phase gate):**
- `pytest` green on: recipe invariants (lead-block rule, floor rule, OPEN-never-required);
  gate boundary tests (0.9 → auto, 0.5 → confirm, 0.49 → choose); `validate_classification()`
  off-schema fixtures (garbage family → `random_idea`, missing confidence → 0.0 → choose, never
  raises); checker fixture matrix (one minimal valid doc per family passes; a deliberately padded
  `random_idea` fixture with an empty SC table FAILS — the Template-Enforcer guard as a regression
  test, not a one-time audit); pin tests (classifier prompt lists every `WorkFamily` value; the
  checker's mirrored profile table == `families.py`'s).
- **Corpus eval:** classify the maintainer's labeled writeup corpus across the three workspaces;
  ≥85% top-1 match against held-out human labels (manual/slow — not a CI gate; CI runs the
  deterministic tests above).
- **End-to-end:** refine one real bug writeup → doc contains Intent + Evidence (+ optional Open
  Questions), `classification.family: bug_fix` in front-matter, NO US/FR/SC sections; `grep` the
  front-matter from a second shell to demonstrate the no-reclassify read path.
- Audit 3+ `random_idea` refinements: **zero** empty/auto-padded scope/metric/acceptance fields.

### Work Package A — Taxonomy module (`families.py`)

The keystone; everything else imports it. Build first.

- Create `cast-server/cast_server/requirements_render/families.py` with the full Naming Contract
  above: `WorkFamily`, `RecipeBlock`, `FAMILY_RECIPES`, `RECIPE_REALIZATION`,
  `REQUIRED_SECTIONS_BY_FAMILY`, `FAMILY_PILL_LABELS`, `GATE_SILENT`/`GATE_CONFIRM`.
- `validate_classification(raw: dict) -> Classification` (frozen dataclass mirroring the
  front-matter shape): whitelist-validate `family` against the enum — **off-schema →
  `WorkFamily.RANDOM_IDEA`, never crash** (defence in depth even though the agent prompt is
  enum-constrained); invalid/missing `confidence` → `0.0` (forces the `choose` gate — the safe
  direction); invalid `alt_family` → `RANDOM_IDEA` (**plan-review Decision #2:** ALL safety
  coercions land on the floor — the safe direction; `GENERIC` is only ever *model-selected*, never
  a coercion target — removing the prior coercion asymmetry); missing `modifiers` → all-false.
  Every coercion is recorded in the returned object (`coercions: tuple[str, ...]`) — zero silent
  failures.
- `merge_front_matter(existing_text: str, classification: dict) -> str` (**plan-review Decision
  #3**) — deterministic, stdlib-only: read the existing `---`-delimited header, set the
  `classification.*` keys, **preserve every other key** (`status:`, the top-level `confidence:`
  map, Phase 4 versioning keys) and the document body **byte-for-byte**, re-serialize. The
  authoring agent (and the gate bin) call this instead of hand-editing YAML — front-matter
  persistence is code, not LLM discipline. Round-trip unit test: a doc carrying `status:` +
  `confidence:` → merge `classification:` → assert both survive untouched.
- `gate(confidence: float) -> GateAction` — pure function, thresholds as module constants. The
  `choose` action carries options `[family, alt_family, "just notes / not sure yet" → RANDOM_IDEA]`
  with the model's pick pre-filled (accept = one click, the GitHub template-chooser pattern).
- `modulate(recipe, *, irreversible: bool, unknown_cause: bool) -> tuple[RecipeBlock, ...]` —
  reversibility/uncertainty as block-inclusion modifiers, NOT families: `irreversible` (one-way
  door) appends `SCOPE`; `unknown_cause` (never-seen bug → spike shape) appends **spike-framed
  `OPEN`, NOT `QUESTION`** (**plan-review Decision #4**). Rationale: both `PROBLEM` and `QUESTION`
  realize to `## Intent` (see `RECIPE_REALIZATION`), so appending `QUESTION` to any `PROBLEM`-led
  recipe (e.g. `bug_fix`) would emit **two `## Intent` sections** — the enum-level
  `dict.fromkeys` dedupe can't catch it (distinct enum values, same H2). Realizing the spike as
  framed `OPEN` is idempotent against the `OPEN` most recipes already allow, and the spike
  prompt-framing carries the investigative intent. **Dedupe at the realization-target level**, not
  just the enum level.
- Unit tests per the Verification list, PLUS: a **no-duplicate-H2 test** asserting that for every
  `WorkFamily` × every `(irreversible, unknown_cause)` combination, `modulate()`'s output maps to
  **distinct** `RECIPE_REALIZATION` H2 targets (**Decision #4**); a **merge_front_matter
  round-trip test** (**Decision #3**); and a **no-reclassify read-path test** (**Decision #6**) —
  author a doc with `classification.*` front-matter, call `parse_requirements_file()`, assert
  `front_matter["classification"]["family"]` reads back **without** invoking the classifier (the
  Phase 3a/3b consume-twice contract, previously only a manual grep). → Apply
  `/cast-python-best-practices` + `/cast-pytest-best-practices` while writing; review output for
  compliance.

### Work Package B — `cast-goal-classifier` agent (standalone, phase-agnostic seam)

- Create `agents/cast-goal-classifier/cast-goal-classifier.md` + `config.yaml`
  (`model: sonnet` — triage task; escalate to opus only if the corpus eval misses 85%;
  `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `timeout_minutes: 10`).
- **Input contract:** goal title + raw writeup text (+ prior `classification` mapping when
  re-classifying, so the agent can note a changed family). **Output contract:** EXACTLY ONE bare
  JSON object — `{family, confidence, reasoning, uncertainty_factors, alt_family, modifiers}` —
  no prose, no fences. The prompt embeds the 9 enum values with rich one-line descriptions
  (the playbook's descriptions, extended to the 3 added families) and the instruction that
  `random_idea` is the default when unsure. **Sharpened `generic` vs `random_idea` boundary
  (plan-review Decision #2)** — the prompt must distinguish the two low-structure fallbacks
  crisply or the corpus eval shows them bleeding together: `generic` = "structured, real work that
  fits no specific family" (has shape, wrong bucket); `random_idea` = "not enough signal yet — a
  thought, not a plan" (the floor). When in genuine doubt, pick `random_idea`.
- **"Strict tool-call" realization note (deviation from playbook mechanics, same guarantee):** the
  repo has no `anthropic` SDK usage and agents are Claude Code sessions, so the literal
  `tool_choice`-forced `classify_work_family` call is realized as *prompt-constrained JSON output +
  MANDATORY code validation* (`validate_classification`, Work Package A). The enum-typing guarantee
  lands at the validation boundary: an off-taxonomy label cannot ENTER the system, which is the
  property the playbook was buying. If a future guide agent gains direct API access, swap in the
  real forced tool call without changing any consumer (the front-matter contract is the seam).
- **In v2 ONLY `cast-refine-requirements` calls it** — ship the door, not the future callers. The
  agent is still registered first-class (phase-agnostic seam, mirrors the extracted router
  resolver, honors plan-review decision #6).
- Pin test: `tests/` grep-pins the agent prompt to contain every `WorkFamily` value (precedent:
  `tests/test_b1_domain_search.py` pinning prompt sections) — enum drift between prompt and
  `families.py` fails CI.
- Run `bin/generate-skills` after creating the agent; verify the generated skill appears.

### Work Package C — `bin/cast-classify-gate` (the "code decides" enforcement point)

Without this, "gate in code not the model" would degrade into a prompt instruction — i.e. the model
self-gating, the playbook's named pitfall #2. The bin makes the threshold decision a deterministic,
unit-testable artifact that agents *invoke*, exactly like `bin/cast-spec-checker`.

- Stdin: the classifier's raw JSON. Stdout: validated classification + gate decision JSON
  (`{classification: {...}, action: "auto"|"confirm"|"choose", options: [...]}`). Exit 0 on any
  parseable input (off-schema input still yields a valid `random_idea` result — never crash);
  exit 2 on unreadable stdin.
- Thin wrapper: `sys.path` bootstrap to import `cast_server.requirements_render.families`, then
  `validate_classification` + `gate`. No logic in the bin itself.
- Tests: golden in/out pairs including off-schema fixtures and both threshold boundaries.

### Work Package D — Two-level family-aware checker (owner decision #1 this session)

- Restructure `bin/cast-spec-checker` rule application into the two levels: **Level 1 generic**
  (runs always): H1 present, US heading shape / `Priority:` / Independent-test
  / EARS grammar / FR–SC ID formats *applied to whichever of those sections exist*. **Level 2
  family** selected by a **`--family <value>` CLI flag (plan-review Decision #1)** — NOT by parsing
  front-matter. The checker has no YAML front-matter reader today and must not grow one: the caller
  (`cast-refine-requirements`, WP-E) already knows the family the moment it classifies, so it
  passes `--family bug_fix`. **No `--family` flag → today's full-spec `REQUIRED_SECTIONS` path,
  byte-for-byte** (product specs in `docs/specs/` and pre-v2 refined docs keep working with zero
  changes). Level 2 then applies the required-section profile (mirrored table of
  `REQUIRED_SECTIONS_BY_FAMILY`) + family assertions: `random_idea`/`personal_non_eng` ERROR on
  empty/placeholder US/FR/SC/Out-of-Scope sections (present-with-real-content is fine — structure
  is *offered*, never auto-generated empty); `bug_fix`/`data_analysis`/`testing_qa` ERROR on
  missing `## Evidence`; `data_analysis`/`personal_non_eng` WARN on a present `## Directional`
  section (US1 S3 says omit, but genuine content shouldn't hard-fail).
- **Mirror rationale + pin test (plan-review Decision #5):** the checker keeps a *mirrored* copy
  of `REQUIRED_SECTIONS_BY_FAMILY` (it does NOT import `families.py`) **deliberately** — it is a
  standalone, stdlib-only lint tool that must run in CI / pre-commit where `cast-server` may not be
  importable. This diverges on purpose from `bin/cast-classify-gate` (WP-C), which DOES `sys.path`-
  bootstrap and import `families` because it is part of the classify orchestration, not a portable
  linter. State this divergence in both bins' headers so neither is "unified" by a later
  maintainer. The pin test must assert the **full mapping** (every family's exact section tuple ==
  `families.py`), not merely key presence — any drift in section content fails CI.
- **The grammar regexes and `_section_spans` are NOT touched** — Phase 1's `spec_grammar.py`
  importlib bridge re-exports them and must keep working unchanged (a Phase 1 test imports the
  bridge; it stays green).
- Update `agents/cast-spec-checker/cast-spec-checker.md` (the documented shape rules) to describe
  the two levels; re-run `bin/generate-skills`.
- Fixture matrix under `tests/fixtures/family_docs/`: one minimal VALID doc per family + the
  padded `random_idea` fixture that must FAIL.

### Work Package E — `cast-refine-requirements` integration (the only v2 caller)

All edits to `agents/cast-refine-requirements/cast-refine-requirements.md` (+ `config.yaml`).
Keep the new section ~60 lines — Phase 1b shares this file and the ~650-line ceiling.

- **New "Step 0 — Classify" (runs FIRST, before any drafting):** dispatch `cast-goal-classifier`
  via the Agent tool (subagent mode) with title + raw writeup → pipe the JSON through
  `bin/cast-classify-gate` → obey `action`:
  - `auto` → record silently (`confirmed_by: auto`).
  - `confirm` → ONE `AskUserQuestion` (per `/cast-interactive-questions`): pre-filled pill +
    one-click accept, with override options (`confirmed_by: user`).
  - `choose` → forced top-2 (`family`, `alt_family`) + the "just notes / not sure yet" escape
    hatch (→ `random_idea`) (`confirmed_by: user`).
- **Question-budget ordering (cross-phase contract with Phase 1b):** classification asks FIRST
  (it shapes everything downstream), the 1b scope-mode confirm second; worst case two one-click
  questions per refinement. `auto` (≥0.9) asks nothing — the common path stays zero-question.
- **Headless/non-interactive policy** (mirrors 1b's auto-persist override): `confirm` → accept the
  pill, `confirmed_by: auto`; `choose` → `random_idea` (the loose default), `confirmed_by:
  fallback`; BOTH append a line to the doc's Open Questions noting the unconfirmed classification.
  Never block, never guess silently.
- **Classifier failure fail-soft:** subagent error/timeout/garbage → `validate_classification`
  coercion path → `random_idea`, `confirmed_by: fallback`, Open Questions note. Refinement never
  dies on classification.
- **Persist ONCE, consume twice:** write the `classification:` mapping into the front-matter via
  `merge_front_matter()` (WP-A, **plan-review Decision #3**) — NOT by hand-editing YAML in the
  prompt — so `status:`, the existing `confidence:` map, and Phase 4 versioning keys survive the
  merge byte-for-byte. The refine agent NEVER re-classifies on render/routing — Phase 3a reads the
  mapping for the pill, Phase 3b reads `classification.family` for routing. Re-classification
  happens only on an explicit re-run of refinement (prior mapping passed to the classifier; a
  changed family is surfaced to the user — the US6 S4 routing consequence is Phase 3b's wiring).
- **Recipe-driven emission:** select `FAMILY_RECIPES[family]`, apply `modulate(modifiers)`, emit
  ONLY the realized sections per the realization table (e.g. `random_idea` → Intent only, ending
  with a "structure is available when you're ready" offer line — an offer, not empty sections).
  Run the checker on the output **with `--family <family>`** (Decision #1) so Level 2 applies the
  right profile; fix errors before persisting.
- `config.yaml`: add `allowed_delegations: [cast-goal-classifier]` (documents intent and makes a
  future HTTP switch config-only, even though subagent dispatch doesn't consult the allowlist).
- Re-run `bin/generate-skills`; verify total prompt length stays under the ~650-line ceiling.

### Work Package F — Spec + template lockstep

- → Delegate: `/cast-update-spec` (create mode) — author
  `docs/specs/cast-goal-classification.collab.md` documenting the new user-facing contracts:
  the `WorkFamily` enum + locked family set, the `classification.*` front-matter schema
  (field-by-field), gate thresholds + the three actions + headless policy, the two-level checker
  contract, `FAMILY_RECIPES`/`RECIPE_REALIZATION` semantics, the add-a-family checklist (enum value
  + recipe + profile row + prompt line + pill label + fixture — and bump `taxonomy_version`).
  Register in `docs/specs/_registry.md`. Review output: the spec must match `families.py` names
  exactly (Phases 3a/3b will cite it).
- `templates/cast-spec.template.md`: add the `## Evidence` section stub + a short "per-family
  shapes" note pointing at the spec (coordinates with Phase 1b's `## Decisions` template edit —
  whichever phase lands second rebases over the other's template change).

### Work Package G — Corpus eval + Template-Enforcer audit

- Assemble the labeled corpus: `requirements.human.md` / raw writeups from the three workspaces
  (this repo's `goals/` has ~17; pull the rest from the maintainer's second-brain/taskos and
  linkedout workspaces — target 25-40 total). **Owner hand-labels each with a held-out family**
  (human action — see Open Questions for the privacy call on committing the corpus).
- `tests/eval_classifier_corpus.py` (manual/slow, excluded from default CI): run the classifier on
  each writeup, compare top-1 to the held-out label, report per-family accuracy + confusion pairs +
  top-2 rate. Gate: ≥85% top-1. **Report the `generic`↔`random_idea` confusion pair explicitly
  (plan-review Decision #2)** — these two low-structure fallbacks are the designed-in ambiguity
  risk; a high cross-rate means the sharpened prompt boundary (WP-B) isn't landing and is the first
  thing to tune. Below the bar → tune the prompt's family descriptions/add few-shot
  examples → re-eval → only then consider `model: opus`. Also report gate calibration (what share
  landed in confirm/choose) to tune the 0.5/0.9 cutoffs later — observability, not a v2 gate.
- Refine 3+ real `random_idea`-shaped writeups end-to-end; audit outputs for zero auto-padded
  fields (the checker's padded-fixture test keeps guarding this forever after).

**Design review:**
- **Spec consistency:** no loaded spec conflicts. New behavior contracts (front-matter schema,
  checker levels, agent I/O) get their own spec via `/cast-update-spec` in Work Package F —
  required because Phases 3a/3b consume these as contracts. The classifier's subagent dispatch
  sits OUTSIDE `cast-delegation-contract.collab.md` (that spec governs HTTP children and output
  files; a subagent returns its JSON as final text, writes no `.output.json`) — stated in the new
  spec so nobody "fixes" the classifier to emit an output envelope.
- **Naming:** `WorkFamily` string values are exactly what Phase 3b's `goals.workflow_family` column
  will store (one vocabulary, two homes); `RecipeBlock` avoids the `Block` collision with Phase 1;
  `data_analysis` deviates from the playbook draft `data_research` (locked family wording wins) —
  flagged so nobody "corrects" it back.
- **Architecture:** `families.py` lives in the Phase 1 package (consistent with parser/blocks);
  the gate-as-bin pattern mirrors `bin/cast-spec-checker` (deterministic code invoked by agents);
  subagent dispatch mirrors the Phase 1b reviewer decision. No DB writes in this phase — the
  Phase 1 service-DB pattern is noted but unused until Phases 3b/4.
- **Error & rescue:** every failure path lands on `random_idea` + recorded coercion + Open
  Questions note — zero silent failures, zero crash states (there is structurally no failure
  state: the floor recipe always renders). Checker on family-less docs falls back to the full-spec
  profile rather than erroring on missing front-matter.
- **Security:** classifier is read-only (consumes text, returns JSON; `interactive: false`, no file
  writes — single-writer stays `cast-refine-requirements`). `bin/cast-classify-gate` treats stdin
  as data only; JSON parse errors exit 2 without evaluating content.

## Build Order

```
A (families.py taxonomy) ──┬──► B (classifier agent) ──┬──► E (refine-requirements integration) ──► G (corpus eval + audit)
                           ├──► C (gate bin) ──────────┤
                           └──► D (two-level checker) ─┘         F (spec + template) — after A-D interfaces settle, parallel with E
```

**Critical path:** A → B/C → E → G. D is needed before E's "run the checker on output" step but can
build in parallel with B/C. F is documentation lockstep — parallel with E.

## Design Review Flags

| Item | Flag | Action |
|---|---|---|
| Checker | Per-family validation vs Phase 1's "checker is NEVER modified" invariant | Owner-approved two-level redesign this session; grammar regexes stay frozen (Suggested Revision #2 narrows the invariant) |
| Parser | `## Evidence` and `## Decisions` would land in `unrecognized_sections` | Suggested Revision #1: add `EVIDENCE` + `DECISION` BlockKinds to Phase 1 (additive) |
| Naming | Playbook's `Block` enum / `data_research` value collide with or deviate from locked names | Renamed `RecipeBlock`; locked `data_analysis`; both stated in the Naming Contract |
| Prompt budget | Step 0 + Phase 1b edits share the ~650-line ceiling on one file | Step 0 capped ~60 lines; logic pushed into agent B and bin C; length check in E |
| Question budget | Classification confirm + 1b scope-mode confirm could stack | Ordering rule (classification first), one-click both, `auto` path asks nothing |
| Subagent capture | Task()-dispatched cast-* subagents are captured as runs per `cast-subagent-and-skill-capture.collab.md` | Free observability for classifier calls; no extra work, noted so E doesn't duplicate tracking |

## Suggested Revisions to Prior Sub-Phases

1. **Phase 1 (parser):** add two BlockKinds — `EVIDENCE = "evidence"` (`## Evidence`, level-1
   whole-section) and `DECISION = "decision"` (`## Decisions`, level-1) — to `blocks.py` and the
   section→kind mapping table. Purely additive; without them, two recipe-realized sections land in
   `unrecognized_sections` and Phase 3a cannot render them typed. (If Phase 1 executes before this
   lands, it's a 10-line follow-up commit, not a rework.)
2. **Phase 1 (invariant wording):** narrow "the checker is NEVER modified" to "the grammar regexes
   and `_section_spans` re-exported by `spec_grammar.py` are never modified." Phase 2's two-level
   checker (owner-approved 2026-06-11) restructures rule application around those frozen primitives.
3. **Phase 1b (coordination, minor):** the `## Decisions` template addition is consumed here as the
   `decision` block's realization; `Decisions` becomes a REQUIRED section only for `pilot_poc` and
   `refactor_migration` profiles — the full-spec/no-family profile does NOT add it (product specs
   shouldn't start failing). No 1b change needed; noted to prevent someone "completing" the checker
   with a global Decisions requirement.

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Classifier accuracy <85% on the corpus | High | Tune enum descriptions / add few-shot examples first; escalate `model: sonnet → opus` second; the playbook's lexical pre-filter stays the deliberate third lever (out of v2 scope per HOLD SCOPE) |
| Enum drift between `families.py`, the classifier prompt, and the checker's mirrored profile table | Medium | Two pin tests (prompt↔enum, mirror↔source) fail CI on any drift |
| Taxonomy cemented to a 3-workspace corpus (FR-012) | Medium | `taxonomy_version` front-matter field + the documented add-a-family checklist make evolution a config change; `generic` fallback + `random_idea` floor absorb unfit work meanwhile |
| Confirm gate becomes friction noise (users click through) | Medium | Pre-filled one-click accept; track the gate-calibration metric in G's eval report; thresholds are module constants — tuning is a 2-character diff |
| Two-level checker breaks product-spec linting | Medium | No-front-matter path is byte-for-byte today's findings; existing checker tests stay green untouched |
| Headless refinement silently mislabels a goal | Low-Med | `confirmed_by: fallback/auto` is recorded AND an Open Questions line is appended — the next human touch sees it; re-classification on re-run is first-class |

## Open Questions

- **Corpus privacy/location:** can the second-brain and linkedout writeups be committed to this
  repo as eval fixtures, or must the corpus live outside the repo (eval script takes a
  `--corpus-dir` path)? Owner call during Work Package G; the eval script supports an external dir
  either way.
- **Classifier model tier:** `sonnet` is the planned default on cost/latency grounds; the corpus
  eval is the designed resolver (escalate to `opus` only on a miss). Not blocking — recorded so the
  eval result, not vibes, decides.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|---|---|---|
| `cast-subagent-and-skill-capture.collab.md` | Task()-dispatched cast-* subagent capture | None — classifier subagent calls are auto-captured as runs (free observability) |
| `cast-delegation-contract.collab.md` | Output-file contract scope | None — classifier is subagent-mode and deliberately outside this contract; stated in the new classification spec |
| `cast-output-json-contract.collab.md` | Contract-v2 envelope | None — classifier returns bare JSON as subagent final text, not an output envelope |
| *(new)* `cast-goal-classification.collab.md` | Created by Work Package F via `/cast-update-spec` | n/a — becomes the contract Phases 3a/3b cite |

## Decisions

> Appended by `cast-plan-review` (2026-06-11). BIG-CHANGE pass over all four sections; 7 issues,
> all resolved. Body of WP-A/B/D/E/G patched inline above to match these decisions.

- **2026-06-11T17:35:00Z — How does `bin/cast-spec-checker` obtain the family for Level-2 selection, given it has no front-matter reader and must not import `families.py`?** — Decision: Pass `--family <value>` as a CLI flag from the caller (`cast-refine-requirements`, which already knows the family post-classify); no `--family` → unchanged full-spec path. Rationale: the checker has no YAML reader today and must stay a portable stdlib-only linter; the caller already holds the family, so no front-matter parsing or `families.py` import is needed. (WP-D, WP-E)
- **2026-06-11T17:36:00Z — How to resolve the `random_idea` vs `generic` overlap and the coercion asymmetry (off-schema family→random_idea but bad alt_family→generic)?** — Decision: Keep both families; sharpen the prompt boundary (`generic` = structured work that fits no family; `random_idea` = the floor / not enough signal); unify ALL `validate_classification` safety coercions to `RANDOM_IDEA` (`GENERIC` is only ever model-selected); add a `generic`↔`random_idea` confusion-pair check to the corpus eval. Rationale: honors the playbook's deliberate two-value design while removing the asymmetry and making the ambiguity measurable. (WP-A, WP-B, WP-G)
- **2026-06-11T17:37:00Z — How is `classification` front-matter persisted/merged so existing keys (`status:`, `confidence:`, Phase 4 versioning) survive a re-run?** — Decision: Add a deterministic stdlib `merge_front_matter()` helper in `requirements_render` that preserves all non-`classification` keys and the body byte-for-byte; the agent/gate calls it instead of hand-editing YAML; add a round-trip unit test. Rationale: front-matter persistence is structured data and must be code, not LLM discipline — the re-run path is exactly where an LLM-regenerated header drops `status:`. (WP-A, WP-E)
- **2026-06-11T17:38:00Z — How does `modulate()` avoid emitting two blocks that realize to the same `## Intent` section (`PROBLEM` + appended `QUESTION`)?** — Decision: `unknown_cause` appends spike-framed `OPEN` (idempotent), not `QUESTION`; dedupe at the realization-target level, not just the enum level; add a no-duplicate-H2 test across every family × modifier combination. Rationale: both `PROBLEM` and `QUESTION` map to `## Intent`, so the enum-level `dict.fromkeys` dedupe can't prevent a duplicate section on any `PROBLEM`-led recipe. (WP-A)
- **2026-06-11T17:39:00Z — How to handle the `REQUIRED_SECTIONS_BY_FAMILY` table being duplicated (checker mirrors it; gate bin imports `families.py`)?** — Decision: Keep the mirror; document the deliberate divergence (checker = portable stdlib-only linter that may run without `cast-server` importable; gate bin = part of the classify orchestration, so it imports) in both bins' headers; harden the pin test to assert the full mapping, not just key presence. Rationale: the DRY exception is justified by the checker's portability contract; the pin test makes the duplication safe, and the documented rationale stops a later maintainer "unifying" it either direction. (WP-D)
- **2026-06-11T17:40:00Z — Should the "persist once, consume twice" no-reclassify read path stay a manual grep check?** — Decision: No — add an automated unit test (author a doc with `classification.*` front-matter, `parse_requirements_file()`, assert `front_matter["classification"]["family"]` reads back without invoking the classifier). Rationale: this is the cross-phase contract Phases 3a/3b depend on; load-bearing invariants belong in CI, not in a manual second-shell grep. (WP-A, WP-G)
- **2026-06-11T17:41:00Z — Is one classifier subagent dispatch per refinement (including the `auto` path) an acceptable performance cost?** — Decision: Accept as-is, no change; record the lexical fast-path as the documented future latency lever. Rationale: no hot loops, no DB, no N+1 — a single added LLM round-trip; the fast-path is deliberately out of scope under HOLD SCOPE, and re-classification on re-run is an intentional US6 feature, so content-hash caching would fight a requirement rather than help. (Performance)
