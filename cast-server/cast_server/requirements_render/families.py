"""The classification taxonomy keystone for Refine Requirements v2 — Phase 2.

This module encodes the cross-phase **Naming Contract**: the `WorkFamily` taxonomy, the
`RecipeBlock` document model, the `FAMILY_RECIPES` render skeletons, the recipe→parser-BlockKind
realization map, the per-family checker profiles, the pill labels, the gate thresholds, and four
pure functions (`validate_classification`, `merge_front_matter`, `gate`, `modulate`).

Every other Phase 2 sub-phase consumes these names. sp2b (gate bin) imports this module; sp2c
(checker) deliberately keeps a *mirrored* copy of `REQUIRED_SECTIONS_BY_FAMILY` rather than
importing it, so the checker stays a portable stdlib linter. Once green, treat the public names
as a frozen contract — changing them after sp2a–sp3b start is a cross-sub-phase break.

Design floor (exploration Playbook 03): `RANDOM_IDEA` is the DEFAULT and the structural floor,
not a failure mode. Its recipe is `(PROBLEM,)` — nothing to pad. Every safety coercion in
`validate_classification` lands on `RANDOM_IDEA` (Decision D2); `GENERIC` is only ever
model-selected, never a coercion target.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from .blocks import BlockKind


# ---------------------------------------------------------------------------
# Taxonomy — the LOCKED family set + the document block model
# ---------------------------------------------------------------------------
class WorkFamily(str, Enum):
    """The LOCKED ~8-family set plus the generic fallback (9 values)."""

    NEW_INITIATIVE = "new_initiative"
    PILOT_POC = "pilot_poc"
    BUG_FIX = "bug_fix"
    DATA_ANALYSIS = "data_analysis"  # playbook drafted "data_research"; LOCKED name wins
    RANDOM_IDEA = "random_idea"  # the DEFAULT and the structural floor
    TESTING_QA = "testing_qa"
    REFACTOR_MIGRATION = "refactor_migration"
    PERSONAL_NON_ENG = "personal_non_eng"
    GENERIC = "generic"  # unmatched fallback (FR-002/003 Scenario 4); model-selected only


class RecipeBlock(str, Enum):
    """The 6-block document model. Deliberately NOT named `Block` — Phase 1 owns `Block`
    (the parser dataclass) in this same package."""

    PROBLEM = "problem"
    EVIDENCE = "evidence"
    DECISION = "decision"
    SCOPE = "scope"
    QUESTION = "question"
    OPEN = "open"


# ---------------------------------------------------------------------------
# Render skeletons — the ordered block recipe per family
# ---------------------------------------------------------------------------
FAMILY_RECIPES: dict[WorkFamily, tuple[RecipeBlock, ...]] = {
    WorkFamily.NEW_INITIATIVE: (
        RecipeBlock.PROBLEM,
        RecipeBlock.DECISION,
        RecipeBlock.SCOPE,
        RecipeBlock.OPEN,
    ),
    WorkFamily.PILOT_POC: (RecipeBlock.QUESTION, RecipeBlock.DECISION, RecipeBlock.OPEN),
    WorkFamily.BUG_FIX: (RecipeBlock.PROBLEM, RecipeBlock.EVIDENCE, RecipeBlock.OPEN),
    WorkFamily.DATA_ANALYSIS: (RecipeBlock.QUESTION, RecipeBlock.EVIDENCE, RecipeBlock.OPEN),
    WorkFamily.RANDOM_IDEA: (RecipeBlock.PROBLEM,),  # the floor — nothing to pad
    WorkFamily.TESTING_QA: (
        RecipeBlock.PROBLEM,
        RecipeBlock.EVIDENCE,
        RecipeBlock.SCOPE,
        RecipeBlock.OPEN,
    ),
    WorkFamily.REFACTOR_MIGRATION: (
        RecipeBlock.PROBLEM,
        RecipeBlock.DECISION,
        RecipeBlock.SCOPE,
        RecipeBlock.OPEN,
    ),
    WorkFamily.PERSONAL_NON_ENG: (RecipeBlock.PROBLEM, RecipeBlock.OPEN),
    WorkFamily.GENERIC: (RecipeBlock.PROBLEM, RecipeBlock.OPEN),
}


# ---------------------------------------------------------------------------
# Recipe → parser-BlockKind realization
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Realization:
    """How a `RecipeBlock` realizes as markdown H2 sections + parser `BlockKind`s.

    `h2_primary` is the lead heading and the dedupe key for `modulate()` — both `PROBLEM`
    and `QUESTION` realize to `Intent`, so appending one to a recipe led by the other must
    collapse at the H2 level, not the enum level.
    """

    h2_primary: str
    headings: tuple[str, ...]  # all H2 headings this block renders (primary first)
    block_kinds: tuple[BlockKind, ...]


RECIPE_REALIZATION: dict[RecipeBlock, Realization] = {
    RecipeBlock.PROBLEM: Realization("Intent", ("Intent",), (BlockKind.INTENT,)),
    RecipeBlock.QUESTION: Realization("Intent", ("Intent",), (BlockKind.INTENT,)),
    RecipeBlock.EVIDENCE: Realization("Evidence", ("Evidence",), (BlockKind.EVIDENCE,)),
    RecipeBlock.DECISION: Realization(
        "Decisions",
        ("Decisions", "User Stories", "Functional Requirements", "Success Criteria"),
        (BlockKind.DECISION, BlockKind.USER_STORY, BlockKind.FR, BlockKind.SC),
    ),
    RecipeBlock.SCOPE: Realization(
        "Out of Scope",
        ("Out of Scope", "Constraints"),
        (BlockKind.SCOPE, BlockKind.CONSTRAINT),
    ),
    RecipeBlock.OPEN: Realization(
        "Open Questions", ("Open Questions",), (BlockKind.OPEN_QUESTION,)
    ),
}


def _build_section_index() -> dict[str, frozenset[RecipeBlock]]:
    """Reverse map: H2 heading -> the recipe blocks that realize it. `Intent` maps to both
    `PROBLEM` and `QUESTION`. Used by the profile-consistency check (and sp2c)."""
    index: dict[str, set[RecipeBlock]] = {}
    for block, realization in RECIPE_REALIZATION.items():
        for heading in realization.headings:
            index.setdefault(heading, set()).add(block)
    return {heading: frozenset(blocks) for heading, blocks in index.items()}


# H2 heading -> recipe blocks that can realize it (derived, not hand-maintained).
SECTION_TO_RECIPE_BLOCKS: dict[str, frozenset[RecipeBlock]] = _build_section_index()


# ---------------------------------------------------------------------------
# Per-family checker profiles — the required H2 sections per family
# ---------------------------------------------------------------------------
# Hand-derived from the recipes (NOT auto-computed — DECISION's realization is
# family-weighted: only `new_initiative` requires the full US/FR/SC depth). `Open Questions`
# appears in NO profile (OPEN is allowed-not-required everywhere).
REQUIRED_SECTIONS_BY_FAMILY: dict[WorkFamily, tuple[str, ...]] = {
    WorkFamily.NEW_INITIATIVE: (
        "Intent",
        "User Stories",
        "Functional Requirements",
        "Success Criteria",
        "Out of Scope",
    ),
    WorkFamily.PILOT_POC: ("Intent", "Decisions"),
    WorkFamily.BUG_FIX: ("Intent", "Evidence"),
    WorkFamily.DATA_ANALYSIS: ("Intent", "Evidence"),
    WorkFamily.RANDOM_IDEA: ("Intent",),
    WorkFamily.TESTING_QA: ("Intent", "Evidence", "Out of Scope"),
    WorkFamily.REFACTOR_MIGRATION: ("Intent", "Decisions", "Out of Scope"),
    WorkFamily.PERSONAL_NON_ENG: ("Intent",),
    WorkFamily.GENERIC: ("Intent",),
}


# ---------------------------------------------------------------------------
# Pill labels — Phase 2 owns the label text + the rule that hover shows `reasoning`;
# Phase 3a owns the HTML/CSS (`family-pill family-pill--{value}`).
# ---------------------------------------------------------------------------
FAMILY_PILL_LABELS: dict[WorkFamily, str] = {
    WorkFamily.NEW_INITIATIVE: "🚀 You are starting a new initiative",
    WorkFamily.PILOT_POC: "🧪 You are running a pilot / proof of concept",
    WorkFamily.BUG_FIX: "🐛 You are fixing a bug",
    WorkFamily.DATA_ANALYSIS: "📊 You are analyzing data",
    WorkFamily.RANDOM_IDEA: "💡 You are jotting down an idea",
    WorkFamily.TESTING_QA: "✅ You are testing / QA",
    WorkFamily.REFACTOR_MIGRATION: "♻️ You are refactoring / migrating",
    WorkFamily.PERSONAL_NON_ENG: "🗒️ You are tracking personal / non-engineering work",
    WorkFamily.GENERIC: "📄 You are capturing a goal",
}


# ---------------------------------------------------------------------------
# Gate thresholds (code, not model — FR-004)
# ---------------------------------------------------------------------------
GATE_SILENT = 0.9
GATE_CONFIRM = 0.5

GateAction = Literal["auto", "confirm", "choose"]


def gate(confidence: float) -> GateAction:
    """Map a confidence number to a gate action. Boundary semantics: `>= 0.9 → auto`,
    `>= 0.5 → confirm`, else `choose` (the safe direction — show the chooser)."""
    if confidence >= GATE_SILENT:
        return "auto"
    if confidence >= GATE_CONFIRM:
        return "confirm"
    return "choose"


# ---------------------------------------------------------------------------
# Classification value object + defence-in-depth validation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Modifiers:
    """Within-family block-inclusion modifiers (NOT families — Decision D4)."""

    irreversible: bool = False
    unknown_cause: bool = False


@dataclass(frozen=True)
class Classification:
    """The validated classification value object, mirroring the front-matter shape.

    `coercions` records every safety coercion applied during validation (zero silent
    failures) so callers and the corpus eval can see what the model got wrong.
    """

    family: WorkFamily
    confidence: float
    alt_family: WorkFamily
    reasoning: str
    uncertainty_factors: tuple[str, ...]
    modifiers: Modifiers
    coercions: tuple[str, ...] = field(default_factory=tuple)


def _as_family(value: object) -> WorkFamily | None:
    """Coerce a raw value to a `WorkFamily`, or `None` if it is not a valid member."""
    if isinstance(value, WorkFamily):
        return value
    try:
        return WorkFamily(value)
    except (ValueError, TypeError):
        return None


def _as_confidence(value: object) -> float | None:
    """Coerce a raw value to a confidence in [0.0, 1.0], or `None` if invalid/out of range.
    `bool` is rejected explicitly (it is an `int` subclass and is never a real confidence)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
    else:
        return None
    if 0.0 <= number <= 1.0:
        return number
    return None


def validate_classification(raw: dict) -> Classification:
    """Coerce an arbitrary (possibly off-schema) mapping into a `Classification`.

    Never raises — defence in depth, even though the agent prompt is enum-constrained. Every
    coercion lands on `RANDOM_IDEA` (the floor, Decision D2) and is recorded in `coercions`.
    """
    if not isinstance(raw, dict):
        raw = {}
    coercions: list[str] = []

    family = _as_family(raw.get("family"))
    if family is None:
        coercions.append(f"family {raw.get('family')!r} invalid → random_idea")
        family = WorkFamily.RANDOM_IDEA

    confidence = _as_confidence(raw.get("confidence"))
    if confidence is None:
        coercions.append(f"confidence {raw.get('confidence')!r} invalid → 0.0")
        confidence = 0.0

    alt_family = _as_family(raw.get("alt_family"))
    if alt_family is None:
        coercions.append(f"alt_family {raw.get('alt_family')!r} invalid → random_idea")
        alt_family = WorkFamily.RANDOM_IDEA

    reasoning_raw = raw.get("reasoning")
    reasoning = reasoning_raw if isinstance(reasoning_raw, str) else ""

    factors_raw = raw.get("uncertainty_factors")
    if isinstance(factors_raw, (list, tuple)):
        uncertainty_factors = tuple(str(f) for f in factors_raw)
    else:
        uncertainty_factors = ()

    modifiers = _validate_modifiers(raw.get("modifiers"), coercions)

    return Classification(
        family=family,
        confidence=confidence,
        alt_family=alt_family,
        reasoning=reasoning,
        uncertainty_factors=uncertainty_factors,
        modifiers=modifiers,
        coercions=tuple(coercions),
    )


def _validate_modifiers(raw: object, coercions: list[str]) -> Modifiers:
    """Coerce the `modifiers` mapping; missing/invalid → both flags `False`."""
    if raw is None:
        return Modifiers()
    if not isinstance(raw, dict):
        coercions.append(f"modifiers {raw!r} invalid → defaults")
        return Modifiers()
    irreversible = raw.get("irreversible")
    unknown_cause = raw.get("unknown_cause")
    return Modifiers(
        irreversible=irreversible if isinstance(irreversible, bool) else False,
        unknown_cause=unknown_cause if isinstance(unknown_cause, bool) else False,
    )


# ---------------------------------------------------------------------------
# Block-inclusion modulation (Decision D4)
# ---------------------------------------------------------------------------
def modulate(
    recipe: tuple[RecipeBlock, ...], *, irreversible: bool, unknown_cause: bool
) -> tuple[RecipeBlock, ...]:
    """Apply reversibility/uncertainty as block-inclusion modifiers, not families.

    - `irreversible` (one-way door) → ensure a `SCOPE` block (out-of-scope / constraints).
    - `unknown_cause` (never-seen bug → spike shape) → ensure a spike-framed `OPEN` block,
      NOT `QUESTION` (which realizes to `## Intent` and would emit a second Intent on a
      `PROBLEM`-led recipe). Idempotent.

    Dedupe happens at the realization-target (H2) level, so distinct enum values that share an
    H2 (`PROBLEM`/`QUESTION`) collapse correctly.
    """
    blocks = list(recipe)
    if irreversible:
        blocks.append(RecipeBlock.SCOPE)
    if unknown_cause:
        blocks.append(RecipeBlock.OPEN)
    return _dedupe_by_h2(blocks)


def _dedupe_by_h2(blocks: list[RecipeBlock]) -> tuple[RecipeBlock, ...]:
    """Keep the first block for each distinct primary H2 target, preserving order."""
    seen: set[str] = set()
    deduped: list[RecipeBlock] = []
    for block in blocks:
        h2 = RECIPE_REALIZATION[block].h2_primary
        if h2 in seen:
            continue
        seen.add(h2)
        deduped.append(block)
    return tuple(deduped)


# ---------------------------------------------------------------------------
# Front-matter merge (Decision D3) — deterministic, stdlib-only
# ---------------------------------------------------------------------------
# Canonical emission order for the classification block. Any extra keys are emitted after
# these, sorted, so output is deterministic regardless of input dict ordering.
_CLASSIFICATION_KEY_ORDER = (
    "family",
    "confidence",
    "alt_family",
    "reasoning",
    "uncertainty_factors",
    "modifiers",
    "confirmed_by",
    "classified_at",
    "taxonomy_version",
)

_TOP_LEVEL_KEY_RE = re.compile(r"^\S")


def merge_front_matter(existing_text: str, classification: dict) -> str:
    """Merge a `classification:` block into the document's YAML front matter.

    Deterministic and stdlib-only (Decision D3). Preserves every other front-matter key and
    the document body **byte-for-byte** — only the `classification:` block is replaced (or
    appended if absent). The authoring agent and the gate bin call this instead of
    hand-editing YAML, so persistence is code, not LLM discipline.
    """
    header_lines, body = _split_front_matter(existing_text)
    header_lines = _strip_top_level_key(header_lines, "classification")
    header_lines = header_lines + _emit_classification_lines(classification)
    new_header = "\n".join(header_lines)
    return f"---\n{new_header}\n---\n{body}"


def _split_front_matter(text: str) -> tuple[list[str], str]:
    """Split `text` into (header_lines, body). When there is no `---`-fenced header, the
    whole text is the body and `header_lines` is empty. The body is preserved byte-for-byte
    when reassembled with `---\\n{header}\\n---\\n{body}`."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return [], text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            header_lines = lines[1:idx]
            body = "\n".join(lines[idx + 1 :])
            return header_lines, body
    # Unterminated fence — treat as no header (do not corrupt the body).
    return [], text


def _strip_top_level_key(lines: list[str], key: str) -> list[str]:
    """Remove a top-level `key:` line and its indented children from header lines."""
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    kept: list[str] = []
    idx = 0
    while idx < len(lines):
        if pattern.match(lines[idx]):
            idx += 1
            while idx < len(lines) and lines[idx][:1] in (" ", "\t"):
                idx += 1
            continue
        kept.append(lines[idx])
        idx += 1
    return kept


def _emit_classification_lines(classification: dict) -> list[str]:
    """Emit the `classification:` block as YAML lines in canonical key order."""
    ordered = [k for k in _CLASSIFICATION_KEY_ORDER if k in classification]
    ordered += sorted(k for k in classification if k not in _CLASSIFICATION_KEY_ORDER)
    lines = ["classification:"]
    for key in ordered:
        value = classification[key]
        if isinstance(value, dict):
            lines.append(f"  {key}:")
            for sub_key in sorted(value):
                lines.append(f"    {sub_key}: {_yaml_scalar(value[sub_key])}")
        elif isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"  {key}: []")
            else:
                lines.append(f"  {key}:")
                lines.extend(f"    - {_yaml_scalar(item)}" for item in value)
        else:
            lines.append(f"  {key}: {_yaml_scalar(value)}")
    return lines


def _yaml_scalar(value: object) -> str:
    """Serialize a scalar to YAML. `bool` is checked before `int` (it is an `int` subclass).
    Strings are always double-quoted with backslash/quote escaping so colons and other YAML
    metacharacters in `reasoning` are safe."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
