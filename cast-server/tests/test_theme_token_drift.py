"""Token-drift pin + hex-literal scan + self-containment tests for the render theme.

Phase 3a, sp1 (WP-A). These are the load-bearing safety net for the *inlining*
deviation: the render theme (`_theme.css.j2`) copies the `:root` design tokens
out of `static/style.css` instead of `<link>`-ing it, so a CI invariant must
guarantee the copy never drifts. `test_theme_tokens_match_style_css` is that
invariant (it replaces Playbook 05's "single copy" property).
"""
from __future__ import annotations

import re
from pathlib import Path

from cast_server.requirements_render.templating import get_environment

_STYLE_CSS = (
    Path(__file__).resolve().parent.parent
    / "cast_server" / "static" / "style.css"
)


def _render_theme() -> str:
    """Render the inline theme partial in isolation."""
    return get_environment().get_template("_theme.css.j2").render()


def _render_shell() -> str:
    """Render the full standalone document shell (empty slots)."""
    return get_environment().get_template("document.html.j2").render()


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _root_token_map(css: str) -> dict[str, str]:
    """Parse every `--name: value;` declaration inside every `:root { ... }`
    block of ``css`` into a name->value dict. `:root` blocks contain no nested
    braces, so a non-greedy brace match is sufficient."""
    clean = _strip_css_comments(css)
    tokens: dict[str, str] = {}
    for block in re.findall(r":root\s*\{([^}]*)\}", clean):
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block):
            tokens[name.strip()] = value.strip()
    return tokens


def test_theme_tokens_match_style_css():
    """Every `:root` token defined in static/style.css is preserved, byte-for-byte
    in value, in the rendered theme. This is the anti-drift invariant: a token
    edited in style.css forces the same edit here, or CI goes red."""
    style_tokens = _root_token_map(_STYLE_CSS.read_text())
    theme_tokens = _root_token_map(_render_theme())

    assert style_tokens, "failed to parse :root tokens from style.css"

    missing = sorted(t for t in style_tokens if t not in theme_tokens)
    assert not missing, f"theme :root is missing style.css tokens: {missing}"

    drifted = {
        name: (style_tokens[name], theme_tokens[name])
        for name in style_tokens
        if theme_tokens[name] != style_tokens[name]
    }
    assert not drifted, f"theme tokens drifted from style.css: {drifted}"


def test_no_hardcoded_hex_outside_root():
    """FR-012: no hex colour literal may appear outside a `:root` token block.
    A one-line OSS rebrand must stay a one-line `:root` override."""
    shell = _render_shell()
    # Remove every :root { ... } block, then scan what remains for hex literals.
    without_root = re.sub(r":root\s*\{[^}]*\}", "", _strip_css_comments(shell))
    hex_literals = re.findall(r"#[0-9a-fA-F]{3,8}\b", without_root)
    assert not hex_literals, f"hex colour literals outside :root: {hex_literals}"


def test_shell_styling_is_self_contained_scripts_are_progressive_enhancement():
    """Styling stays fully inlined (doctype + inline <style>, no external stylesheet);
    the ONLY external scripts are the two sanctioned Phase 4 (sp5) comment-layer assets.

    sp5 deliberately relaxes the Phase 3a "no external script src" property to enable the
    vanilla comment layer: when opened as a bare file:// the two `/static/*` scripts 404 and
    the document stays a perfectly readable read-only render (progressive enhancement). The
    self-contained STYLING guarantee is unchanged — only behaviour is layered on. sp7 records
    this in the render spec."""
    shell = _render_shell()
    assert "<!doctype html>" in shell.lower()
    assert "<style>" in shell
    # Styling is still self-contained — no external stylesheet link.
    assert '<link rel="stylesheet"' not in shell.lower().replace(" ", "")
    assert not re.search(r"<link[^>]+rel=[\"']stylesheet[\"']", shell, re.IGNORECASE)
    # Every external script src is one of the two sanctioned, progressive-enhancement assets.
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", shell, re.IGNORECASE)
    assert srcs == ["/static/htmx.min.js", "/static/requirements_comments.js"], srcs


def test_shell_has_four_body_regions_in_order():
    """Smoke test (Step 1.4): the empty shell renders the four body layers in the
    fixed Goal Card -> recipe -> unmodeled -> directional order, plus the single
    inline expand-all script."""
    shell = _render_shell()
    markers = ["GOAL CARD", "RECIPE SECTIONS", "UNMODELED SECTIONS", "DIRECTIONAL"]
    positions = [shell.find(m) for m in markers]
    assert all(p != -1 for p in positions), f"missing body region markers: {positions}"
    assert positions == sorted(positions), f"body regions out of order: {positions}"
    # Exactly one INLINE script (the expand-all toggle). The sp5 comment-layer scripts are
    # external `<script src=...>` (asserted separately), so the bare `<script>` count stays 1.
    assert shell.count("<script>") == 1
    assert "data-expand-all" in shell


def test_lifted_class_names_present_verbatim():
    """The cast-preso class names transfer verbatim (the checker rubric language
    depends on them) and the family-pill idiom + rescue state exist."""
    theme = _render_theme()
    for cls in (
        ".slide-title", ".l1-body", ".l2-body",
        ".source-citation", ".callout", ".question-annotation",
    ):
        assert cls in theme, f"missing lifted class: {cls}"
    assert ".family-pill--unclassified" in theme
    assert ".family-pill--new_initiative" in theme


def test_print_forces_details_open():
    """@media print must force every <details> open so nothing hides on paper."""
    theme = _render_theme()
    print_block = re.search(r"@media print\s*\{(.*?)\}\s*$", theme, re.DOTALL)
    assert print_block is not None, "no @media print block found"
    assert "details > *" in print_block.group(1)
    assert "display: block" in print_block.group(1)
