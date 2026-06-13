"""Single grammar source: re-export bin/cast-spec-checker's compiled regexes.

The checker is the canon for the FR-007 spec-kit shape. Loading its regexes (instead of
copying them) guarantees the parser can never drift from the checker. The checker file is
NEVER modified.

The checker is import-safe by design ("Internal use", module level = regex + dataclass defs;
its argparse/CLI code is guarded behind ``if __name__ == "__main__"``).
"""
import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

# __file__ = cast-server/cast_server/requirements_render/spec_grammar.py
#   parents[0] = requirements_render/   parents[1] = cast_server/
#   parents[2] = cast-server/           parents[3] = repo root
# (verified at build time: parents[3] / "bin" / "cast-spec-checker" resolves to the real file)
_CHECKER_PATH = Path(__file__).resolve().parents[3] / "bin" / "cast-spec-checker"
if not _CHECKER_PATH.exists():
    raise FileNotFoundError(f"spec-kit grammar source not found: {_CHECKER_PATH}")

# The checker has no `.py` suffix, so spec_from_file_location can't infer a loader on its
# own — pass an explicit SourceFileLoader.
_loader = SourceFileLoader("cast_spec_checker", str(_CHECKER_PATH))
_spec = importlib.util.spec_from_file_location(
    "cast_spec_checker", _CHECKER_PATH, loader=_loader
)
_checker = importlib.util.module_from_spec(_spec)
# Register before exec so the checker's `@dataclass` can resolve `cls.__module__`.
sys.modules["cast_spec_checker"] = _checker
_spec.loader.exec_module(_checker)

# All six names verified present in bin/cast-spec-checker with these exact identifiers;
# no aliasing needed.
US_HEADING_RE = _checker.US_HEADING_RE
FR_ID_RE = _checker.FR_ID_RE
SC_ID_RE = _checker.SC_ID_RE
EARS_SCENARIO_RE = _checker.EARS_SCENARIO_RE
SECTION_HEADING_RE = _checker.SECTION_HEADING_RE
NEEDS_CLAR_INLINE_RE = _checker.NEEDS_CLAR_INLINE_RE
# Reuse the checker's section-span algorithm (verified to exist as `_section_spans`):
_section_spans = getattr(_checker, "_section_spans", None)
