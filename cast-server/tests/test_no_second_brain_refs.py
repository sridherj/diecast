"""Guard test: ``second-brain`` / ``SECOND_BRAIN`` must not appear in the
production cast-server tree.

The naming is a legacy of an older repo layout (``second-brain/cast/``). After
the rename to ``diecast``, the constant was renamed to ``DIECAST_ROOT`` and
its value corrected to ``CAST_ROOT`` itself. This guard exists so the rename
doesn't silently regress.

Scope: ``cast-server/cast_server/`` only — tests, fixtures, audit docs, and
``.cast-bak-*`` snapshots are out of scope by design.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROD_TREE = REPO_ROOT / "cast-server" / "cast_server"

# Match the legacy module-level constant and any path-style reference. The
# patterns are deliberately broad — anything that brings the string back is
# a regression worth surfacing.
FORBIDDEN = re.compile(r"second[-_]brain|SECOND_BRAIN", re.IGNORECASE)


def test_no_second_brain_refs_in_cast_server() -> None:
    """Fail with a list of file:line citations if any production source under
    ``cast-server/cast_server/`` mentions the legacy name."""
    hits: list[tuple[Path, int, str]] = []

    for path in PROD_TREE.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".html", ".txt"}:
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if FORBIDDEN.search(line):
                hits.append((path.relative_to(REPO_ROOT), lineno, line.strip()))

    if hits:
        rendered = "\n".join(f"  {p}:{n}: {ln}" for p, n, ln in hits)
        raise AssertionError(
            "Legacy 'second-brain' references found in cast-server production tree.\n"
            "Rename to DIECAST_ROOT or remove. Hits:\n" + rendered
        )
