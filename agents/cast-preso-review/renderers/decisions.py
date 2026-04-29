"""Decision-mode renderer: parse ``decisions/Q-*.md`` into reviewable slides.

Each question becomes one slide with ``mode="decision"``. The slide's
``blocks[0]`` carries the full ``Question`` payload (as a dict) so
``review.js`` can render the decision card declaratively — topic header,
context, lettered options, references, response UI.

Build-time anti-pattern warnings (from
``.claude/skills/cast-interactive-questions/SKILL.md``) are surfaced both
on stderr (``[WARN decision Q-XX] ...``) and attached to the payload so the
client can render a muted banner on the card. Warnings never fail the build:
reviewers should still see the question so they can push back on the framing.

Structural errors (missing ``## Context`` or ``## Recommended``) are fatal:
the renderer raises ``SystemExit`` with a clear message pointing at the file.
"""

from __future__ import annotations

import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import build
from renderers._markdown import parse_frontmatter, render_markdown


_OPTION_RE = re.compile(
    r"""^\s*-\s*                 # leading bullet
        \*\*Option\s+([A-Z])     # letter in 'Option X'
        \s*[\u2014\u2013\-]\s*   # em/en dash or hyphen
        ([^:]+?):\*\*            # label ending at the first ':'
        \s*(.*)$                 # rest of line
    """,
    re.VERBOSE,
)

# Match a bare level-2 heading. Used to split the post-frontmatter body.
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Reference extractors:
#   - backtick-quoted paths or URLs:   `path/to/file:lines`
#   - file:// URLs
#   - bare path-like tokens with at least one slash and a common extension
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_FILE_URL_RE = re.compile(r"\bfile://[^\s)\]]+")
_BARE_PATH_RE = re.compile(
    r"(?<![`\w/])"                                    # not already inside a backtick or path
    r"((?:[\w.\-]+/)+[\w.\-]+(?:\.[\w]+)?(?::[\d\-]+)?)"
)


@dataclass
class DecisionOption:
    letter: str
    label: str
    rationale: str
    references: list[str]
    recommended: bool


@dataclass
class Question:
    id: str
    topic: str
    stage: str | None
    blocking: bool
    context_markdown: str
    context_references: list[str]
    options: list[DecisionOption]
    references: list[str]
    source_path: str
    warnings: list[str] = field(default_factory=list)


# ---------- Parsing --------------------------------------------------------


def _extract_references(text: str) -> list[str]:
    """Pull backtick-quoted paths, file:// URLs and bare path-like tokens.

    Preserves first-seen order and de-duplicates.
    """
    seen: dict[str, None] = {}
    for match in _BACKTICK_RE.findall(text):
        candidate = match.strip()
        if candidate and ("/" in candidate or candidate.startswith("file://")):
            seen.setdefault(candidate, None)
    for match in _FILE_URL_RE.findall(text):
        seen.setdefault(match.strip(), None)
    for match in _BARE_PATH_RE.findall(text):
        candidate = match.strip().rstrip(",.);:")
        if candidate and candidate not in seen:
            seen[candidate] = None
    return list(seen.keys())


def _split_h2_sections(body: str) -> dict[str, str]:
    """Split a markdown body into a dict of ``{heading_lowercase: section_body}``.

    Headings are compared case-insensitively. Duplicate headings raise the
    ``_MultipleSections`` sentinel so the caller can decide how to surface it.
    """
    positions: list[tuple[str, int, int]] = []
    matches = list(_H2_RE.finditer(body))
    for idx, match in enumerate(matches):
        name = match.group(1).strip().lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        positions.append((name, start, end))

    sections: dict[str, str] = {}
    for name, start, end in positions:
        chunk = body[start:end].strip("\n")
        # Last occurrence wins for dup headings; we check dup separately below.
        sections[name] = chunk
    return sections


def _has_duplicate_h2(body: str) -> bool:
    matches = [m.group(1).strip().lower() for m in _H2_RE.finditer(body)]
    return len(matches) != len(set(matches))


def _parse_options(section_body: str, *, recommended: bool) -> list[DecisionOption]:
    """Parse an option-bullet block into ``DecisionOption`` records.

    Each top-level ``- **Option X — label:** rationale`` is one option. Nested
    lines (indented continuations and sub-bullets) belong to the option above
    them until the next top-level bullet or end of block.
    """
    options: list[DecisionOption] = []
    lines = section_body.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        match = _OPTION_RE.match(lines[i])
        if not match:
            i += 1
            continue
        letter, label, first = match.group(1), match.group(2).strip(), match.group(3).rstrip()
        body_lines = [first] if first else []
        i += 1
        # Consume continuation lines until the next top-level option or EOF.
        while i < n:
            nxt = lines[i]
            if _OPTION_RE.match(nxt):
                break
            # Blank line still belongs to this option (preserves paragraph breaks
            # in the rationale) but we skip trailing blanks at the end.
            body_lines.append(nxt.rstrip())
            i += 1
        rationale = "\n".join(body_lines).strip()
        options.append(
            DecisionOption(
                letter=letter,
                label=label,
                rationale=rationale,
                references=_extract_references(rationale),
                recommended=recommended,
            )
        )
    return options


def parse_question(path: Path) -> Question:
    """Parse a single ``Q-*.md`` file into a ``Question`` instance.

    Raises ``SystemExit`` on structural errors (missing Context or Recommended,
    duplicate frontmatter fences). Anti-pattern warnings are attached to the
    returned ``Question.warnings`` field and also emitted on stderr.
    """
    text = path.read_text(encoding="utf-8")

    if _has_duplicate_frontmatter_fence(text):
        raise SystemExit(
            f"decision file {path}: multiple '---' frontmatter fences — "
            "each file must contain exactly one question"
        )

    meta, body = parse_frontmatter(text)
    if not meta:
        raise SystemExit(
            f"decision file {path}: missing frontmatter (expected --- block with id/topic)"
        )

    if _has_duplicate_h2(body):
        raise SystemExit(
            f"decision file {path}: duplicate ## headings — wall-of-text refuses "
            "multiple questions per slide; split into separate files"
        )

    sections = _split_h2_sections(body)
    missing = [h for h in ("context", "recommended") if h not in sections]
    if missing:
        raise SystemExit(
            f"decision file {path}: missing required sections: {', '.join(missing)}"
        )

    context_md = sections.get("context", "").strip()
    recommended_opts = _parse_options(sections.get("recommended", ""), recommended=True)
    alt_opts = _parse_options(sections.get("alternatives", ""), recommended=False)
    refs_block = _extract_references(sections.get("references", ""))

    qid = meta.get("id", path.stem).strip()
    topic = meta.get("topic", qid).strip()
    stage = meta.get("stage") or None
    blocking = _coerce_bool(meta.get("blocking"))

    question = Question(
        id=qid,
        topic=topic,
        stage=stage,
        blocking=blocking,
        context_markdown=context_md,
        context_references=_extract_references(context_md),
        options=recommended_opts + alt_opts,
        references=refs_block,
        source_path=str(path),
    )
    question.warnings = _collect_warnings(question)
    _emit_warnings(question)
    return question


def _coerce_bool(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"true", "yes", "1", "y"}


def _has_duplicate_frontmatter_fence(text: str) -> bool:
    """Detect two separate '---' frontmatter fences in one file (wall-of-text)."""
    if not text.startswith("---\n"):
        return False
    rest = text[4:]
    closing = rest.find("\n---")
    if closing == -1:
        return False
    tail = rest[closing + 4:]
    # If another fence exists after the first block closes, this file bundles
    # more than one question.
    return re.search(r"(?m)^---\s*$", tail) is not None


# ---------- Warnings -------------------------------------------------------


def _collect_warnings(question: Question) -> list[str]:
    warnings: list[str] = []

    if len(question.options) < 2:
        warnings.append(
            "wall of text: only one option — a decision needs >= 2 options"
        )

    for opt in question.options:
        if not opt.rationale.strip():
            warnings.append(f"ungrounded option {opt.letter}: empty rationale")
        elif not opt.references:
            warnings.append(f"ungrounded option {opt.letter}: no references cited")

    # "Leading question": recommended options have non-empty rationale AND
    # every alternative option has blank rationale.
    rec = [o for o in question.options if o.recommended]
    alts = [o for o in question.options if not o.recommended]
    if rec and alts and all(o.rationale.strip() for o in rec) and all(
        not o.rationale.strip() for o in alts
    ):
        warnings.append("leading question: alternatives have blank rationales")

    if not question.context_references:
        warnings.append(
            "premature question: Context has no artifact references — "
            "was anything read?"
        )

    return warnings


def _emit_warnings(question: Question) -> None:
    for w in question.warnings:
        sys.stderr.write(f"[WARN decision {question.id}] {w}\n")


# ---------- Renderer -------------------------------------------------------


def _question_to_slide(question: Question) -> build.Slide:
    payload: dict[str, Any] = asdict(question)
    # Precompute context HTML so the client doesn't need a markdown renderer.
    payload["context_html"] = render_markdown(question.context_markdown)
    for opt_dict, opt in zip(payload["options"], question.options, strict=True):
        opt_dict["rationale_html"] = render_markdown(opt.rationale)
    payload["id"] = question.id
    payload["topic"] = question.topic

    # The generic block shell expects at least an ``id`` and ``kind``. We stash
    # the structured question payload under the same key so review.js can pick
    # it up in the decision branch.
    block = {
        "id": f"{question.id}/decision",
        "kind": "decision",
        "editable": False,
        **payload,
    }
    return build.Slide(
        id=question.id,
        title=question.topic,
        outcome=None,
        source_path=question.source_path,
        mode="decision",
        blocks=[block],
    )


def _iter_question_files(decisions_dir: Path) -> list[Path]:
    return sorted(p for p in decisions_dir.glob("Q-*.md") if p.is_file())


def _resolve_decisions_dir(goal_dir: Path) -> Path:
    """The source dir may itself be a fixture ``decisions/`` folder OR a goal
    dir containing a ``decisions/`` child. Auto-pick whichever exists.
    """
    if (goal_dir / "decisions").is_dir():
        return goal_dir / "decisions"
    return goal_dir


def render(
    goal_dir: Path,
    stage: str | None = None,
) -> tuple[list[build.Slide], list[build.SidebarEntry], build.BuildResult]:
    """Build slides and sidebar entries from ``decisions/Q-*.md``.

    When invoked directly from ``build.py``, ``goal_dir`` may be:
      - A goal dir containing a ``decisions/`` child (typical case)
      - A dir that IS the ``decisions/`` folder (fixture case: ``--source-dir``
        points straight at the fixtures folder)
    We detect both shapes so fixtures under ``tests/fixtures/decisions/``
    render cleanly without an extra copy step.
    """
    decisions_dir = _resolve_decisions_dir(goal_dir)
    files = _iter_question_files(decisions_dir)
    if not files:
        raise SystemExit(
            f"no decision files found under {decisions_dir} (expected Q-*.md)"
        )

    questions = [parse_question(p) for p in files]
    slides = [_question_to_slide(q) for q in questions]

    # Sidebar grouping: when we're serving as the *primary* renderer, there is
    # no fold, so no group label. The ``maybe_fold_decisions`` helper in
    # build.py re-labels these entries with ``group="Open questions"`` when
    # merging into an edit-mode slide list.
    sidebar_group = "Open questions" if stage == "decisions-fold" else None
    sidebar = [
        build.SidebarEntry(
            slide_id=q.id,
            label=q.topic,
            summary=(q.stage or "decision") if not q.blocking else f"{q.stage or 'decision'} · blocking",
            group=sidebar_group,
        )
        for q in questions
    ]

    source_files = [str(p) for p in files]
    result = build.BuildResult(
        mode="decision",
        stage="decisions" if stage != "decisions-fold" else "decisions-fold",
        slide_count=len(slides),
        source_files=source_files,
        source_hash=build.compute_source_hash(files),
    )
    return slides, sidebar, result


# Auto-register on import.
build.register_renderer("decisions", render)


# ---------- Folding helper (used by build.py when mixing modes) ------------


def fold_into(
    goal_dir: Path,
    primary_slides: list[build.Slide],
    primary_sidebar: list[build.SidebarEntry],
) -> tuple[list[build.Slide], list[build.SidebarEntry]]:
    """Append decision slides to a primary (edit-mode) slide list.

    Called by ``build.py::maybe_fold_decisions`` when the primary renderer is
    ``narrative`` or ``what`` AND the goal dir has a ``decisions/`` sibling.
    Returns a new (slides, sidebar) pair; the original lists are not mutated.
    """
    slides, sidebar, _ = render(goal_dir, stage="decisions-fold")
    return list(primary_slides) + slides, list(primary_sidebar) + sidebar


__all__ = [
    "DecisionOption",
    "Question",
    "parse_question",
    "render",
    "fold_into",
]
