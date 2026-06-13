"""Typed block model for the requirements render layer.

Definitions are canon for downstream phases (copied verbatim from the Phase 1 shared
context). A `Block` is a render landmark, NOT a comment anchor: `Block.ref` is parsed in
memory only and is never persisted to a DB column.
"""
from dataclasses import dataclass
from enum import Enum


class BlockKind(str, Enum):
    INTENT = "intent"; USER_STORY = "user_story"; FR = "fr"; SC = "sc"
    CONSTRAINT = "constraint"; SCOPE = "scope"
    DIRECTIONAL = "directional"; OPEN_QUESTION = "open_question"
    # Phase 2 Suggested Revision #1 — additive block kinds the classification recipes
    # realize. `## Evidence` (repro/logs/data sources) and `## Decisions` (decision +
    # spec-kit depth). Without these the sections land in `unrecognized_sections` and
    # Phase 3a cannot render them typed.
    EVIDENCE = "evidence"; DECISION = "decision"


@dataclass(frozen=True)
class Block:
    kind: BlockKind
    level: int            # 1 = whole-section block, 2 = element within a section
    body: str             # exact source slice, byte-faithful
    heading: str | None   # e.g. "US1 — WHAT/HOW separation"; None for bullet blocks
    ref: str | None       # "US1" | "FR-007" | "SC-001" | None — parsed in-memory ONLY;
                          # never persisted to a DB column, never used as a comment anchor
    line_start: int       # 1-indexed in source
    line_end: int


@dataclass(frozen=True)
class ParsedRequirements:
    title: str                    # H1 text
    front_matter: dict            # YAML header (status/confidence/...)
    preamble: str                 # blockquote between H1 and first H2 (spec maturity etc.)
    blocks: tuple[Block, ...]     # source order
    unrecognized_sections: tuple[str, ...]  # H2s the typed model skipped — never silent
    source_text: str              # full original text, untouched
    content_hash: str             # sha256 hex of source_text (UTF-8)
