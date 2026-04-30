"""Re-export shim — single source of truth is agents/_shared/terminal.py.

Earlier revisions vendored the resolver here because cast-server could not
rely on `agents/` being importable. That gap is now closed by a small
sys.path bootstrap in `cast_server/__init__.py`. All resolver logic lives in
`agents/_shared/terminal.py`; this module exists only so existing imports
(`from cast_server.infra.terminal import ...`) keep working.
"""
from __future__ import annotations

from agents._shared.terminal import (  # noqa: F401
    _SUPPORTED,
    ResolutionError,
    ResolvedTerminal,
    _autodetect,
    _config_default,
    needs_first_run_setup,
    resolve_terminal,
)
