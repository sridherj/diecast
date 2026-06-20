"""The strict render-sentinel extraction contract, shared by both render-jobs.

The HOW agent (requirements or exploration) emits exactly one
`<!-- BEGIN RENDER -->` … `<!-- END RENDER -->` block wrapping a self-contained HTML document.
`extract_render` pulls that window out of possibly-chatty output, returning None on any no-output
shape (missing / mis-ordered / duplicate sentinels, empty windows, markup-less chatter).
"""
from __future__ import annotations

# Content = the FIRST `_BEGIN` to the FIRST following `_END`. Anything after the first `_END`
# (e.g. the reserved requirements `GAPS-DETECTED` trailer) is outside the window and byte-ignored.
_BEGIN_SENTINEL = "<!-- BEGIN RENDER -->"
_END_SENTINEL = "<!-- END RENDER -->"


def extract_render(raw: str | None) -> str | None:
    """Content from the FIRST `<!-- BEGIN RENDER -->` to the FIRST following `<!-- END RENDER -->`,
    or None when no such well-formed pair exists.

    None ⇒ no-output for this attempt. Covers missing / mis-ordered (END before BEGIN) / duplicate
    sentinels and empty windows. Anything after the first END is outside the window and byte-ignored.
    """
    if not raw:
        return None
    begin = raw.find(_BEGIN_SENTINEL)
    if begin == -1:
        return None
    end = raw.find(_END_SENTINEL, begin + len(_BEGIN_SENTINEL))
    if end == -1:
        return None
    content = raw[begin + len(_BEGIN_SENTINEL):end].strip()
    if not content or "<" not in content:
        # An empty window or a window with no markup (a chatty/fenced non-render) is no-output.
        return None
    return content
