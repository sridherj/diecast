"""Package-local Jinja environment for the requirements render layer (Phase 3a, sp1).

This module deliberately does **not** reuse the app's request-bound
``Jinja2Templates`` from ``deps.py``. The renderer is a pure function over a
``ParsedRequirements`` (no FastAPI, no request, no I/O), so it needs an
environment that is importable and usable from plain library code and from
unit tests — ``deps.py``'s templates object is tied to the web layer.

The environment loads templates from the package's own ``templates/`` directory
via :class:`jinja2.PackageLoader`, so ``document.html.j2`` / ``_theme.css.j2``
ship with the installed package and resolve regardless of the process CWD.
``autoescape`` is on (the renderer emits HTML from parsed user content).
"""
from __future__ import annotations

import jinja2

_PACKAGE = "cast_server.requirements_render"
_TEMPLATE_DIR = "templates"


def get_environment() -> jinja2.Environment:
    """Return a fresh package-local Jinja ``Environment`` for the render layer.

    Importable and renderable without FastAPI. Autoescaping is enabled because
    the renderer interpolates parsed requirement content into HTML. ``trim_blocks``
    / ``lstrip_blocks`` keep the emitted markup readable (and the goldens stable).
    """
    return jinja2.Environment(
        loader=jinja2.PackageLoader(_PACKAGE, _TEMPLATE_DIR),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
