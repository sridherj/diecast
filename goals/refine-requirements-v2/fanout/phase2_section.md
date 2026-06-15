## Phase 2: Classification — Family Detection & Block Recipes
**Outcome:** Every goal is classified into a work **family** with a confidence signal; the
classification is surfaced as a pill and persisted as machine-readable front-matter (humans read the
pill, agents read the field). The requirements document is shaped by a **composable block-recipe**
model, not rigid per-family templates — and the loosest "random idea" family is the structural floor.
**Dependencies:** Phase 1 (block model is what recipes select over).
**Estimated effort:** 2-3 sessions
**Verification:** Classify the maintainer's real writeup corpus across the three workspaces; ≥85%
match a held-out human-assigned family. Audit N `random_idea` renders: **zero** empty/auto-padded
scope/metric/acceptance fields (Template-Enforcer guard holds). A downstream agent reads
`classification.family` from front-matter without re-running the classifier.

Key activities:
- **Define the 6-block document model** (`problem, evidence, decision, scope, question, open`) and
  `FAMILY_RECIPES` as ordered block lists per family. `problem` is always present; `open` is always
  allowed, never required. An unclassifiable goal still emits `problem` — there is no failure state.
- **Build a standalone `cast-goal-classifier` agent** (owner decision at plan review — extract, don't
  embed). Internally it makes the Claude strict tool-call `classify_work_family` returning
  `{family, confidence, reasoning, uncertainty_factors, alt_family}` with an enum-typed `family` (an
  off-taxonomy label is structurally impossible); whitelist-validate in code anyway; off-schema →
  `random_idea`, never crash. Packaging it as its own agent (not a buried step) makes the seam
  **phase-agnostic** so any phase can reclassify later — mirroring the extracted router resolver and
  honoring decision #2 (reclassify-from-any-phase is a core flow). **In v2, only `cast-refine-requirements`
  calls it** (ship the door, not the future callers). Result persists as front-matter, consumed by both
  US2 (document shape) and US6 (routing) — one classification, never run twice.
- **Gate confirm-on-ambiguity in code, not the model** (FR-004): `≥0.9` silent pill · `0.5-0.9`
  pill + one-click confirm · `<0.5` forced top-2 + "just notes / not sure yet" escape hatch. The model
  returns a number; *code* decides whether to ask.
- **Persist one classification, consume it twice:** YAML front-matter on the requirements artifact
  (agents + Phase 3b router) and the pill at the top of the HTML render (Phase 3a). Never classify twice.
- **Lock the ~8-family set + generic fallback** (resolved at plan review): new-initiative, pilot/POC,
  bug-fix, data-analysis, random-idea, **+ testing/QA, refactor/migration, personal/non-eng**, plus a
  generic fallback. **Spike is a within-family modifier, not a family; "stub" is a render-state, not a
  family.** Encode as `FAMILY_RECIPES` entries (config, not new templates). Still validate the
  classifier's accuracy against the corpus, but the family list itself is decided.
- **Encode reversibility/uncertainty as block-inclusion modifiers** (not new families): a never-seen
  bug picks up `question` (spike shape); a one-way-door initiative escalates to include `scope`.
- **Build the Template-Enforcer guard structurally:** the `random_idea` renderer literally has no
  scope/metric/acceptance slots to pad; structure is *offered*, never auto-generated empty.

