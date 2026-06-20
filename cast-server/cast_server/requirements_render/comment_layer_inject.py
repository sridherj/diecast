"""Inject the cast-comment-html annotation layer into a served ``.html`` artifact (sp3b).

Diecast-wide in-viewer commenting: the dual viewer (2b) embeds render-class ``.html`` artifacts via
``<iframe srcdoc sandbox="allow-scripts allow-popups">`` (null origin, NO allow-same-origin). This
module appends the SAME ``cast-comment-html`` layer (CSS + pure ``anchor.js`` helpers + the
``comment-layer.js`` UI) the standalone tool uses — verbatim, never a reimplementation — right before
the artifact's ``</body>`` as it is placed into ``srcdoc``. The injected ``window.__CCH__`` config runs
the layer in BRIDGE mode: on Submit it ``postMessage``s the comment batch to the host (the embedding
viewer page), which proxies per-comment same-door POSTs (see ``static/comment-bridge.js``).

Artifact-GENERIC by construction: it takes the artifact bytes + ``goal_slug`` + a goal-relative
``artifact_ref`` and knows nothing about requirements vs exploration. Phase 4's ``exploration.html``
inherits commenting for free — no exploration-specific code.

Stdlib + repo assets only; pure (bytes in → bytes out), so it is trivially unit-testable and has no
DB / network coupling.
"""
from __future__ import annotations

import json
from functools import lru_cache

from cast_server.config import CAST_ROOT

# The single source of truth for the layer assets is the cast-comment-html skill — the SAME files the
# standalone annotation tool serves (no fork, no drift). 1b validated this exact layer inside the 2b
# sandbox config.
_ASSETS_DIR = CAST_ROOT / "agents" / "cast-comment-html" / "assets"


@lru_cache(maxsize=1)
def _layer_assets() -> tuple[str, str, str]:
    """Read (css, anchor_js, layer_js) once. Cached — the files are static per process."""
    css = (_ASSETS_DIR / "comment-layer.css").read_text(encoding="utf-8")
    anchor_js = (_ASSETS_DIR / "anchor.js").read_text(encoding="utf-8")
    layer_js = (_ASSETS_DIR / "comment-layer.js").read_text(encoding="utf-8")
    return css, anchor_js, layer_js


def _layer_block(goal_slug: str, artifact_ref: str | None) -> str:
    """The injected ``<style>+<script>`` block configuring the layer in bridge mode.

    ``__CCH__.bridge=true`` flips ``comment-layer.js``'s Submit transport from a direct ``fetch`` to a
    ``window.parent.postMessage`` (the null-origin srcdoc can't fetch the same-door API). ``goal_slug``
    + ``artifact_ref`` ride the config so the host bridge knows WHERE to route each per-comment POST.
    """
    css, anchor_js, layer_js = _layer_assets()
    cfg = {
        "bridge": True,
        "goal_slug": goal_slug,
        "artifact_ref": artifact_ref,
        # The srcdoc frame is null-origin and cannot target a specific origin → reply/post with "*".
        "targetOrigin": "*",
        # `file` keys the layer's localStorage so per-artifact drafts don't collide across iframes.
        "file": artifact_ref or "refined_requirements.html",
    }
    cfg_json = json.dumps(cfg)
    return (
        "\n<!-- cast-comment-html annotation layer (Diecast bridge mode, sp3b) -->\n"
        f"<style>{css}</style>\n"
        f"<script>{anchor_js}</script>\n"
        f"<script>window.__CCH__={cfg_json};</script>\n"
        f"<script>{layer_js}</script>\n"
    )


def inject_comment_layer(artifact_html: str, goal_slug: str, artifact_ref: str | None) -> str:
    """Return ``artifact_html`` with the bridge-mode comment layer appended before ``</body>``.

    Mirrors ``cast-comment-html``'s ``build_page`` placement (before the LAST ``</body>``, else
    appended). Idempotent guard: if the layer is already present (double-inject), return unchanged —
    a defensive no-op so a re-render or a doubly-wrapped artifact never stacks two layers.
    """
    if "cast-comment-html annotation layer" in artifact_html:
        return artifact_html
    block = _layer_block(goal_slug, artifact_ref)
    lower = artifact_html.lower()
    idx = lower.rfind("</body>")
    if idx != -1:
        return artifact_html[:idx] + block + artifact_html[idx:]
    return artifact_html + block
