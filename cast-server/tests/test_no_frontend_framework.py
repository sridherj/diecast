"""No-framework pin (WP-F): the comment layer stays ~150 lines of vanilla JS.

Two tripwires for the HOLD-SCOPE guarantee that no frontend build/framework crept in:
  * **No ``package.json`` anywhere under ``cast-server/``** — the existence of one would mean a
    node toolchain (and, inevitably, a framework) had landed. The plan forbids it outright.
  * **``requirements_comments.js`` imports no framework/annotation library** — a source scan
    (not an import-graph check, since the file ships no build step). htmx is vanilla and already
    vendored as the transport, so it is explicitly allowed; only frameworks + annotation
    libraries are banned.

If either trips, a tooling accident (or a scope-creep PR) has broken the Phase 4 design contract.
Keep both strict.
"""
from __future__ import annotations

from pathlib import Path

# cast-server/tests/<file> -> parents[1] = cast-server/
CAST_SERVER_ROOT = Path(__file__).resolve().parents[1]
COMMENT_JS = CAST_SERVER_ROOT / "cast_server" / "static" / "requirements_comments.js"


def test_no_package_json_anywhere_under_cast_server():
    found = list(CAST_SERVER_ROOT.rglob("package.json"))
    assert found == [], (
        f"a package.json appeared under cast-server/ — the no-framework pin tripped: {found}"
    )


def test_comment_js_imports_no_framework():
    js = COMMENT_JS.read_text().lower()
    banned = (
        "import react", "from 'react", 'from "react', "require('react", 'require("react',
        "vue", "angular", "svelte",          # frameworks
        "annotator", "rangy",                 # annotation libraries the plan rules out
    )
    for term in banned:
        assert term not in js, f"framework/library reference found in comment JS: {term!r}"
