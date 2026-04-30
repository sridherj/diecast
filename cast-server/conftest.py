"""Test bootstrap for cast-server.

Adds the ``cast-server`` directory to ``sys.path`` so the package
``cast_server`` (which lives at ``cast-server/cast_server/``) is
importable without requiring ``pip install -e .``.

The ``cast-server`` directory itself is named with a hyphen and is
not importable as a Python package, so the inner ``cast_server``
package is the real Python entry point.
"""

import sys
from pathlib import Path

_CAST_SERVER_DIR = Path(__file__).resolve().parent
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))
