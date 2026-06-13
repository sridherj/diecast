"""Throwaway 1b structural audit — replays the golden DOM-contract gates on both maker files.

Mirrors the intent of test_requirements_renderer.py's structural assertions (FR-012/013 +
FR-028): zero ``id=`` attributes, zero ``data-block-anchor``, only the two sanctioned scripts,
no inline script, no CDN/http(s) reference, exactly one ``data-goal-slug``. Exit non-zero on any
violation so the spike is replayable as a gate.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANCTIONED = {"/static/htmx.min.js", "/static/requirements_comments.js"}


def audit(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    return dict(
        id_attrs=len(re.findall(r'(?<![\w-])id\s*=', html)),
        block_anchor=len(re.findall(r'data-block-anchor', html)),
        non_sanctioned=[s for s in re.findall(r'<script[^>]*src="([^"]*)"', html)
                        if s not in SANCTIONED],
        inline_script=len(re.findall(r'<script(?![^>]*\bsrc=)[^>]*>', html)),
        cdn=len(re.findall(r'https?://', html)),
        goal_slug=re.findall(r'data-goal-slug="([^"]*)"', html),
    )


def main() -> int:
    failed = False
    for f in ("feature-maker-v1.html", "feature-maker-v2.html"):
        a = audit(HERE / f)
        ok = (a["id_attrs"] == 0 and a["block_anchor"] == 0 and not a["non_sanctioned"]
              and a["inline_script"] == 0 and a["cdn"] == 0 and len(a["goal_slug"]) == 1)
        failed = failed or not ok
        print(f"{f}: {'PASS' if ok else 'FAIL'}  {a}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
