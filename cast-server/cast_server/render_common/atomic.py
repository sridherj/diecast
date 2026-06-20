"""The single atomic-write primitive shared by every render publish seam.

Promoted out of `requirements_render_service` so there is ONE copy: both
`requirements_render_service` and `exploration_render_service` import it from here.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _atomic_write(target: Path, text: str) -> None:
    """Write `text` to `target` atomically (tmp file in the same dir + `os.replace`).

    A crash mid-write leaves either the old file or the new file — never a truncated one.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".", suffix=".html.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        # Best-effort cleanup of the temp file on any failure; never leave it behind.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
