"""Stub detection for the requirements thin spine — the canonical Phase 1 home.

`is_stub` answers a single render-state question: *has this goal been refined into
substantive content, or is it still a near-empty skeleton?* It is **not** a work-family
(families classify intent; a stub is a maturity state — decisions doc, line 74) and it is
**not** the hard gate (the gate runs separately and skips sub-threshold stubs — line 55).

This lives in the parser package (plan-review #1: `is_stub` in the Phase 1 pkg) so the
Phase 3a renderer *imports* it and never redefines the threshold locally. The measure is the
rendered-content word count — preamble + every typed block body + any unrecognized section —
i.e. exactly the text a reader would see, ignoring YAML front matter and structural scaffolding.
"""
from __future__ import annotations

from .blocks import ParsedRequirements

# A goal whose visible content is below this many words is still a stub: there is nothing
# to render into the family recipe yet, so the renderer shows a prompt-to-begin card instead
# of an empty skeleton. 200 words is the cross-phase constant (decisions doc, line 55).
STUB_WORD_THRESHOLD = 200


def _content_word_count(parsed: ParsedRequirements) -> int:
    """Count words across the *visible* content: preamble, typed block bodies, and the
    bodies-by-name of unrecognized sections. Front matter and the bare H1 are excluded —
    they are scaffolding, not refined content."""
    parts: list[str] = [parsed.preamble]
    parts.extend(block.body for block in parsed.blocks)
    parts.extend(parsed.unrecognized_sections)
    return sum(len(part.split()) for part in parts)


def is_stub(parsed: ParsedRequirements) -> bool:
    """True when the document's visible content is below ``STUB_WORD_THRESHOLD`` words.

    Pure and deterministic — a function of the parsed content only.
    """
    return _content_word_count(parsed) < STUB_WORD_THRESHOLD
