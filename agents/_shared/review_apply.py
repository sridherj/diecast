"""Sub-phase review-delegation primitives (B4).

Exposes the deterministic pieces of the post-execution review flow used by
cast-subphase-runner so they can be unit-tested without spawning Claude.

Three callables:

* `classify_subphase(plan_text)` — applies the heuristic in
  `docs/reference/subphase-coding-classifier.ai.md`. Returns
  ``"coding" | "non-coding" | "ambiguous"``.
* `is_path_under(path, allowed_roots)` — path-traversal guard. Resolves to an
  absolute path (no symlink traversal) and confirms the result sits under one
  of the allowed root directories.
* `process_review_payload(payload, plan_path, allowed_roots)` — walks the
  cast-review-code payload, auto-applies high-confidence Edit-applicable issues
  whose target path is under an allowed root, and records everything else into
  ``<plan_path>.followup.md``. Returns a dict summarizing what happened.

The processor is restricted to a single contract: ``confidence: high`` AND the
issue carries ``old_string``/``new_string`` AND the target path resolves under
``allowed_roots``. Anything else lands in followup. This is intentionally
narrow — multi-line patches, file creation, and rename/delete operations are
not auto-applied (per sp3d plan).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Literal


Classification = Literal["coding", "non-coding", "ambiguous"]


_RESEARCH_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bresearch\b",
        r"\bresearches\b",
        r"\bresearched\b",
        r"\bexplore\b",
        r"\bexplores\b",
        r"\bexploration\b",
        r"\bdecompose\b",
        r"\bdecomposition\b",
        r"\bsynthesize\b",
        r"\bsynthesis\b",
    )
)

_CODING_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        # Verbs that cleanly imply file mutation. \bedit\b matches "Edit" /
        # "Edit-tool" but NOT "edits" (the descriptive plural noun used in
        # phrases like "no source-file edits").
        r"\bedit\b",
        r"\bwrite\b",
        r"\bcreate\b.{0,40}(file|module|script|migration|schema)",
        r"\bauthor\b.{0,40}(file|module|script|migration|schema|test|fixture)",
        # Direct test signals.
        r"\bpytest\b",
        r"test_[a-z0-9_]+\.py",
        r"tests/[a-z0-9_/]+",
        # File-extension signals tied to source artifacts.
        r"\.py\b",
        r"\.sql\b",
        r"config\.yaml",
        r"schema\.sql",
    )
)

_PLAYBOOK_PATTERN = re.compile(r"\bplaybook\b", re.IGNORECASE)


def classify_subphase(plan_text: str) -> Classification:
    """Classify a sub-phase plan as coding, non-coding, or ambiguous.

    Heuristic mirrors `docs/reference/subphase-coding-classifier.ai.md`:

    1. Coding if verification mentions tests/specific paths or activities use
       Edit/Write/file-creation actions.
    2. Non-coding if activities use research/explore/etc. with NO Edit/Write
       and NO test file authoring.
    3. Ambiguous (hybrid) if both signal sets fire AND a playbook artifact is
       mentioned — that is the canonical "research-then-implement" shape from
       the classifier doc.
    """
    coding_hits = sum(1 for pat in _CODING_PATTERNS if pat.search(plan_text))
    research_hits = sum(1 for pat in _RESEARCH_PATTERNS if pat.search(plan_text))
    playbook = bool(_PLAYBOOK_PATTERN.search(plan_text))

    if coding_hits and research_hits and playbook:
        return "ambiguous"
    if coding_hits >= 1:
        return "coding"
    if research_hits >= 1:
        return "non-coding"
    return "ambiguous"


def is_path_under(candidate: str | Path, allowed_roots: Iterable[str | Path]) -> bool:
    """Return True if `candidate` resolves under any of `allowed_roots`.

    Uses `Path.resolve(strict=False)` so non-existent target paths are still
    normalized (handles ``..`` and symlink-style traversal). The check is
    purely lexical after resolution — callers should never pre-trust paths
    coming from review payloads.
    """
    target = Path(candidate).expanduser().resolve(strict=False)
    for root in allowed_roots:
        root_path = Path(root).expanduser().resolve(strict=False)
        try:
            target.relative_to(root_path)
        except ValueError:
            continue
        return True
    return False


def _is_edit_applicable(issue: dict) -> bool:
    """An issue is Edit-tool-applicable iff it carries both old/new strings.

    Multi-line refactors (no anchor string), file creation (no old_string), or
    file deletion (no new_string) all fall through to followup.
    """
    return bool(issue.get("old_string")) and "new_string" in issue


def process_review_payload(
    payload: dict,
    plan_path: str | Path,
    allowed_roots: Iterable[str | Path],
) -> dict:
    """Process a cast-review-code output JSON, auto-applying or recording.

    Returns a dict::

        {
            "auto_applied": [<issue dicts>],
            "followup": [<issue dicts with reason>],
            "followup_path": <Path>,
        }

    Side effects:
      * Auto-applied issues mutate their target file in place via plain
        text replacement (single occurrence — collisions raise).
      * Non-applied issues are appended to ``<plan_path>.followup.md``.
    """
    plan_path = Path(plan_path)
    followup_path = plan_path.with_name(plan_path.name + ".followup.md")
    auto_applied: list[dict] = []
    followup: list[dict] = []

    issues = _collect_issues(payload)
    for issue in issues:
        confidence = (issue.get("confidence") or "").lower()
        target = issue.get("file") or ""

        # Path-traversal guard always wins, even for high-confidence issues.
        if not is_path_under(target, allowed_roots):
            followup.append({**issue, "_reason": "out-of-tree edit refused"})
            continue

        if confidence != "high":
            followup.append({**issue, "_reason": f"confidence: {confidence or 'unknown'}"})
            continue

        if not _is_edit_applicable(issue):
            followup.append({**issue, "_reason": "not Edit-tool-applicable"})
            continue

        _apply_edit(Path(target), issue["old_string"], issue["new_string"])
        auto_applied.append(issue)

    if followup:
        _write_followup(followup_path, followup)

    return {
        "auto_applied": auto_applied,
        "followup": followup,
        "followup_path": followup_path,
    }


def _collect_issues(payload: dict) -> list[dict]:
    """Pull review-issue objects out of a cast-review-code payload.

    Issues live under ``artifacts[].metadata.issues[]``. Tolerant of missing
    keys — a malformed payload yields an empty list.
    """
    out: list[dict] = []
    for art in payload.get("artifacts") or []:
        meta = art.get("metadata") or {}
        for issue in meta.get("issues") or []:
            if isinstance(issue, dict):
                out.append(issue)
    return out


def _apply_edit(target: Path, old: str, new: str) -> None:
    text = target.read_text()
    if text.count(old) != 1:
        # Conservative: anything other than a single-occurrence replacement
        # falls outside the auto-apply contract.
        raise ValueError(
            f"refusing auto-apply on {target}: old_string not uniquely matched"
        )
    target.write_text(text.replace(old, new, 1))


def _write_followup(path: Path, items: list[dict]) -> None:
    lines = ["# Sub-phase Review Followup", ""]
    for item in items:
        lines.append(f"- file: `{item.get('file', '?')}`  ")
        lines.append(f"  line: {item.get('line', '?')}  ")
        lines.append(f"  confidence: {item.get('confidence', 'unknown')}  ")
        lines.append(f"  reason: {item.get('_reason', '')}  ")
        lines.append(f"  summary: {item.get('summary', '')}  ")
        if item.get("suggested_fix"):
            lines.append(f"  suggested_fix: {item['suggested_fix']}  ")
        lines.append("")
    path.write_text("\n".join(lines))


__all__ = [
    "Classification",
    "classify_subphase",
    "is_path_under",
    "process_review_payload",
]
