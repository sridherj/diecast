"""The zero-click view extractor — the SC-001 gate's *input* discipline (Phase 3a, sp5a).

`extract_zero_click_view(html)` walks a rendered `refined_requirements.html` and returns the
plain text a **non-clicking reader** sees: the Goal Card, every heading, all open content, and
the `<summary>` label of each disclosure — but **never** the body of a closed `<details>`.

This is the whole point of the gate (Execution Note, sp5a plan): "zero clicks" is a *structural
property of the checker's input*, not a prompt instruction. The `cast-requirements-checker`
agent judges only this extracted surface, so a render that hides the WHAT behind a collapsed
`<details>` fails the gate **deterministically** — the checker physically cannot see the
collapsed content.

Stdlib only (`html.parser`) so the bin wrapper runs anywhere `cast-server` is importable.

Visibility model
----------------
A `<details>` shows only its `<summary>` until clicked. So a piece of text is visible iff, for
the outermost *closed* `<details>` ancestor (if any), the text lives in that element's direct
`<summary>`. Nesting cuts off: content inside a `<details>` that is itself inside a closed
`<details>` is invisible (you cannot reach it without first expanding the parent) — even its
summary. An open `<details>` (carrying the `open` attribute, as the "Expand all" affordance can
produce) reveals its body normally.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

# Block-level tags around which we emit a newline, so headings / list items / sections land on
# their own lines in the extracted text (readability for the LLM checker). Everything else is
# inline and its text is concatenated as-is.
_BLOCK_TAGS = frozenset(
    {
        "section", "div", "details", "summary", "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "li", "ul", "ol", "main", "aside", "header", "footer", "br", "tr",
    }
)

# Tags whose *content* is never reader-visible text (and must never leak into the gate input).
_DROP_CONTENT_TAGS = frozenset({"style", "script", "head", "title"})


@dataclass
class _DetailsFrame:
    """One `<details>` ancestor on the parse stack."""

    is_open: bool


class _ZeroClickExtractor(HTMLParser):
    """Collect the reader-visible text of a rendered document (see module docstring)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._details_stack: list[_DetailsFrame] = []
        self._in_summary = False
        # Depth of the closest enclosing summary's owning details on the stack at the moment we
        # entered the summary; lets nested details inside a summary (illegal HTML, but be safe)
        # not re-open visibility.
        self._summary_owner_depth = -1
        self._drop_depth = 0  # inside <style>/<script>/<head>/<title>

    # --- visibility -------------------------------------------------------------------
    def _text_visible(self) -> bool:
        """True when the current text node is visible to a non-clicking reader."""
        if self._drop_depth:
            return False
        # The outermost closed details cuts off everything below it except its own summary.
        for depth, frame in enumerate(self._details_stack):
            if frame.is_open:
                continue
            # `depth` is the outermost closed details. Visible only if we are inside *its*
            # direct summary (summary opened while this exact frame was the stack top).
            return self._in_summary and self._summary_owner_depth == depth
        return True

    # --- parser hooks -----------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _DROP_CONTENT_TAGS:
            self._drop_depth += 1
            return
        if tag == "details":
            is_open = any(name == "open" for name, _ in attrs)
            self._details_stack.append(_DetailsFrame(is_open=is_open))
        elif tag == "summary":
            self._in_summary = True
            self._summary_owner_depth = len(self._details_stack) - 1
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Self-closing (e.g. <br/>) — emit a separator if block-level, no stack effect.
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROP_CONTENT_TAGS:
            if self._drop_depth:
                self._drop_depth -= 1
            return
        if tag == "details":
            if self._details_stack:
                self._details_stack.pop()
            if self._summary_owner_depth >= len(self._details_stack):
                self._summary_owner_depth = -1
        elif tag == "summary":
            self._in_summary = False
            self._summary_owner_depth = -1
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        if self._text_visible():
            self._chunks.append(data)

    # --- result -----------------------------------------------------------------------
    def get_text(self) -> str:
        """Collapse the collected chunks into clean, line-oriented text."""
        raw = "".join(self._chunks)
        lines = [" ".join(line.split()) for line in raw.split("\n")]
        out: list[str] = []
        for line in lines:
            if line:
                out.append(line)
        return "\n".join(out) + ("\n" if out else "")


def extract_zero_click_view(html: str) -> str:
    """Return the plain text a non-clicking reader sees in the rendered HTML.

    Keeps the Goal Card, every heading, all open content, and each `<summary>` label; drops the
    body of every closed `<details>` plus all tags, `<style>`, and `<script>` content.

    Args:
        html: a rendered `refined_requirements.html` document (or any HTML fragment).

    Returns:
        Newline-separated visible text. Deterministic and dependency-free.
    """
    parser = _ZeroClickExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()
