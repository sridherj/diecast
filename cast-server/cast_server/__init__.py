"""cast-server package init.

Ensures the repo's `agents/` tree is importable so cast-server modules can
re-export from `agents._shared.*`. cast-server is installed via setuptools
with `where=["cast-server"]`, which puts only `cast_server/` on sys.path —
the sibling `agents/` directory at the repo root is invisible without this
small bootstrap.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
