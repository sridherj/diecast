"""Unit tests for the artifact-generic comment-layer injector (exploration-pipeline-nxm sp3b).

``comment_layer_inject.inject_comment_layer`` appends the bridge-mode cast-comment-html layer to a
served ``.html`` artifact's bytes, before serving them into the dual viewer's ``<iframe srcdoc>``. It
is pure (bytes → bytes) and artifact-generic — these tests pin: the layer + bridge config are
injected; the artifact's own markup is preserved verbatim; injection is idempotent; and the config
carries the goal_slug + artifact_ref the host bridge routes on.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.requirements_render import comment_layer_inject  # noqa: E402

DOC = (
    "<!doctype html><html><head><style>h1{color:#123}</style></head>"
    "<body><h1>Exploration</h1><p>The 90/10 hat.</p></body></html>"
)


def _cfg(html: str) -> dict:
    m = re.search(r"window\.__CCH__=(\{.*?\});", html, re.DOTALL)
    assert m, "expected an injected window.__CCH__ config"
    return json.loads(m.group(1))


def test_injects_layer_and_bridge_config():
    out = comment_layer_inject.inject_comment_layer(DOC, "my-goal", "exploration/exploration.html")
    # layer assets present
    assert "cast-comment-html annotation layer" in out
    assert "window.parent.postMessage" in out  # bridge transport in comment-layer.js
    # bridge config carries the routing keys
    cfg = _cfg(out)
    assert cfg["bridge"] is True
    assert cfg["goal_slug"] == "my-goal"
    assert cfg["artifact_ref"] == "exploration/exploration.html"
    assert cfg["targetOrigin"] == "*"


def test_preserves_artifact_markup_and_placement():
    out = comment_layer_inject.inject_comment_layer(DOC, "g", "a.html")
    # the doc's own head/body survive verbatim
    assert "<style>h1{color:#123}</style>" in out
    assert "<h1>Exploration</h1>" in out
    # layer sits before the artifact's final </body>
    assert out.index("cast-comment-html annotation layer") < out.rindex("</body>")


def test_idempotent_double_inject_is_noop():
    once = comment_layer_inject.inject_comment_layer(DOC, "g", "a.html")
    twice = comment_layer_inject.inject_comment_layer(once, "g", "a.html")
    assert twice == once  # never stacks two layers


def test_default_artifact_ref_none_carried_as_null():
    out = comment_layer_inject.inject_comment_layer(DOC, "g", None)
    cfg = _cfg(out)
    assert cfg["artifact_ref"] is None  # requirements default — host bridge maps NULL → requirements
    # the localStorage key still gets a stable file label so drafts don't collide
    assert cfg["file"] == "refined_requirements.html"


def test_no_body_tag_appends_layer():
    out = comment_layer_inject.inject_comment_layer("<h1>bare fragment</h1>", "g", "x.html")
    assert "<h1>bare fragment</h1>" in out
    assert "cast-comment-html annotation layer" in out
