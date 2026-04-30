"""GET /api/health — cast-doctor parity (red/yellow/green).

V1 implementation shells out to ``bin/cast-doctor --json`` and returns its
JSON payload directly. The contract is stable: the response is always
``{"red": [...], "yellow": [...], "green": [...]}`` so the ``/cast-doctor``
skill can render it without branching on success/failure.
"""

from __future__ import annotations

import json
import subprocess

from fastapi import APIRouter

from cast_server.config import CAST_ROOT

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health() -> dict:
    """Return the cast-doctor JSON shape: ``{"red", "yellow", "green"}``.

    ``bin/cast-doctor`` exits non-zero when red findings are present — that
    is the expected contract, not an HTTP error. We always parse stdout and
    return 200; the caller (``/cast-doctor`` skill) decides how to render.
    """
    bin_path = CAST_ROOT / "bin" / "cast-doctor"
    proc = subprocess.run(
        [str(bin_path), "--json"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "red": [
                "cast-doctor-shell: could not parse output. "
                f"stderr: {proc.stderr.strip() or '(empty)'}"
            ],
            "yellow": [],
            "green": [],
        }
