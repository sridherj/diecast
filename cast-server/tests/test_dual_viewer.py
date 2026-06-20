"""Dual md/html artifact viewer — Phase 2b (exploration-pipeline-nxm).

Phase 2b extends the Diecast phase-tab artifact viewer to render `.html`
render-class artifacts (via `<iframe srcdoc>`) alongside the `.md` it already
renders, without regressing today's md path. These tests pin the extended
viewer seam — the interface Phase 3b (in-iframe commenting) and Phase 4
(exploration render) consume:

* **Read gate** admits `.html`; the **edit gate** still rejects it (US4
  render-class artifacts are read-only).
* **`_add_html_file`** collects `.html` with `kind="html"`, verbatim bytes, and
  `authorship=None`; **`_add_md_file`** carries `kind="markdown"`.
* **Macro dispatch**: `kind="markdown"` is byte-identical to today (default param,
  regression-safe); `kind="html"` emits an `<iframe srcdoc>` whose decoded content
  equals the file bytes and whose sandbox OMITS `allow-same-origin`.
* **Adversarial srcdoc escaping** (plan-review Decision #6): a doc containing
  `</script>`, quotes/backtick, `&`, and a render-marker round-trips byte-exact
  through `srcdoc` and parses to exactly one `<script>`.

Hermetic FastAPI app + ``TestClient`` per the ``test_api_goals_route.py`` pattern.
"""

from __future__ import annotations

import html as _html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _seed_goal(db_path: Path, goals_root: Path, slug: str) -> Path:
    """Insert a goal row whose ``folder_path`` points at a real on-disk dir."""
    from cast_server.db.connection import get_connection

    goal_dir = goals_root / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path, phase) "
            "VALUES (?, ?, ?, ?)",
            (slug, "Dual Viewer Goal", str(goal_dir), "requirements"),
        )
        conn.commit()
    finally:
        conn.close()
    return goal_dir


def _srcdoc_value(rendered: str) -> str:
    """Extract the raw (still-escaped) value of the iframe's srcdoc attribute."""
    m = re.search(r'srcdoc="([^"]*)"', rendered)
    assert m, f"expected a srcdoc attribute in:\n{rendered}"
    return m.group(1)


class _ScriptCounter(HTMLParser):
    """Count <script> start tags and capture sandbox tokens from parsed HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.script_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.script_count += 1


@pytest.fixture
def env(isolated_db: Path, monkeypatch, tmp_path):
    """TestClient over api_goals on a hermetic DB + goals root."""
    pytest.importorskip("cast_server.config")
    from cast_server.db import connection as _connection

    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import api_goals

    app = FastAPI()
    app.include_router(api_goals.router)

    goals_root = tmp_path / "goals"
    goals_root.mkdir()
    return {
        "client": TestClient(app),
        "db_path": isolated_db,
        "goals_root": goals_root,
    }


# --------------------------------------------------------------------------- #
# Read / edit gates
# --------------------------------------------------------------------------- #
def test_read_gate_admits_html_edit_gate_rejects(tmp_path, monkeypatch):
    """`validate_artifact_path_read` accepts `.html`; the edit gate rejects it."""
    from cast_server.routes import api_artifacts

    # Point GOALS_DIR at a tmp tree so the path resolves inside an allowed dir.
    monkeypatch.setattr(api_artifacts, "GOALS_DIR", tmp_path)

    html_file = tmp_path / "refined_requirements.html"
    html_file.write_text("<!doctype html><h1>Render</h1>")

    # READ: admitted.
    resolved = api_artifacts.validate_artifact_path_read(str(html_file))
    assert resolved == html_file.resolve()

    # EDIT: rejected — `.html` renders are read-only (US4).
    with pytest.raises(ValueError):
        api_artifacts.validate_artifact_path(str(html_file))

    # The md edit gate is unchanged: a non-suffixed .md is still not editable,
    # a .collab.md still is.
    collab = tmp_path / "refined_requirements.collab.md"
    collab.write_text("# hi")
    assert api_artifacts.validate_artifact_path(str(collab)) == collab.resolve()


# --------------------------------------------------------------------------- #
# Collector behaviour via the live phase-tab route
# --------------------------------------------------------------------------- #
def test_phase_tab_renders_both_md_and_html(env):
    """A requirements phase tab with both a .md and a .html artifact renders both."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "dual-goal")

    (goal_dir / "refined_requirements.collab.md").write_text(
        "# Refined\n\nMarkdown body here.\n"
    )
    html_doc = (
        "<!doctype html><html><head><style>h1{color:#123}</style></head>"
        "<body><h1>Requirements Render</h1></body></html>"
    )
    (goal_dir / "refined_requirements.html").write_text(html_doc)

    resp = client.get("/api/goals/dual-goal/tab/requirements")
    assert resp.status_code == 200
    body = resp.text

    # md path: rendered into a markdown-body div (unchanged).
    assert 'class="artifact-content markdown-body"' in body
    assert "Markdown body here." in body

    # html path: embedded inside an <iframe srcdoc=...>. sp3b injects the bridge-mode
    # cast-comment-html layer into the served bytes (commenting built ON TOP of 2b), so the
    # srcdoc is no longer byte-identical to the file — but the artifact's own markup is preserved
    # verbatim (head/style/body intact) and the layer is appended before </body>.
    assert "artifact-html-frame" in body
    srcdoc = _html.unescape(_srcdoc_value(body))
    assert "<style>h1{color:#123}</style>" in srcdoc  # the doc's own head survived
    assert "<h1>Requirements Render</h1>" in srcdoc   # the doc's own body survived
    assert "cast-comment-html annotation layer" in srcdoc  # the bridge layer was injected
    assert "window.parent.postMessage" in srcdoc           # bridge transport present
    # The layer sits before the artifact's closing </body> (placement contract).
    assert srcdoc.index("cast-comment-html annotation layer") < srcdoc.rindex("</body>")

    # Render-class: NO edit button on the html artifact (authorship=None).
    # The md artifact (collab) DOES get one — assert exactly one edit button total.
    assert body.count("edit-artifact-btn") == 1


def test_html_sandbox_omits_allow_same_origin(env):
    """The iframe sandbox must NOT include allow-same-origin (null-origin isolation)."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "sandbox-goal")
    (goal_dir / "refined_requirements.html").write_text("<h1>x</h1>")

    body = client.get("/api/goals/sandbox-goal/tab/requirements").text
    m = re.search(r'sandbox="([^"]*)"', body)
    assert m, "expected a sandbox attribute on the iframe"
    tokens = m.group(1).split()
    assert "allow-scripts" in tokens  # Phase 3b bridge needs scripts
    assert "allow-same-origin" not in tokens  # this IS the null origin


def test_md_only_tab_has_no_iframe(env):
    """Regression: a phase tab with only .md artifacts emits no iframe (md path intact)."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "md-only-goal")
    (goal_dir / "refined_requirements.collab.md").write_text("# Only Markdown\n")

    body = client.get("/api/goals/md-only-goal/tab/requirements").text
    assert 'class="artifact-content markdown-body"' in body
    assert "artifact-html-frame" not in body
    assert "Only Markdown" in body


# --------------------------------------------------------------------------- #
# Macro: kind="markdown" default-param regression (byte-identical to today)
# --------------------------------------------------------------------------- #
def test_macro_markdown_default_is_byte_identical():
    """`artifact_content(html)` with no kind == today's markdown-body div, byte-for-byte."""
    from cast_server.deps import templates

    env = templates.env
    src = "{% from 'macros/markdown_viewer.html' import artifact_content %}"
    rendered_default = env.from_string(
        src + "{{ artifact_content(html) }}"
    ).render(html="<p>hello</p>")
    rendered_explicit = env.from_string(
        src + "{{ artifact_content(html, 'markdown') }}"
    ).render(html="<p>hello</p>")

    assert rendered_default == rendered_explicit
    assert "artifact-html-frame" not in rendered_default
    assert "<p>hello</p>" in rendered_default  # |safe pass-through, unchanged


# --------------------------------------------------------------------------- #
# Adversarial srcdoc escaping — plan-review Decision #6 (T2 A)
# --------------------------------------------------------------------------- #
def test_adversarial_srcdoc_roundtrip_and_single_script():
    """An HTML doc with </script>, quotes/backtick, &, and a render-marker round-trips
    byte-exact through srcdoc AND the decoded DOM parses exactly one <script>."""
    from cast_server.deps import templates

    # A pathological render-class doc: the kind of thing Phase 4 / the requirements
    # renderer could emit. Contains every char that naive escaping breaks on.
    adversarial = (
        "<!doctype html><html><head>"
        "<meta name=\"cast-render-marker\" content=\"exploration&amp;2b\">"
        "</head><body>"
        "<h1>Tom &amp; Jerry's \"render\" `test`</h1>"
        "<p>An inline close-tag in text: &lt;/script&gt; should not break embedding.</p>"
        "<script>const s = \"</scr\"+\"ipt>\"; const t = `backtick & 'quote'`; "
        "console.log(s, t, 1 < 2 && 3 > 2);</script>"
        "</body></html>"
    )

    env = templates.env
    src = "{% from 'macros/markdown_viewer.html' import artifact_content %}"
    rendered = env.from_string(
        src + "{{ artifact_content(html, 'html') }}"
    ).render(html=adversarial)

    # 1) Byte-exact round-trip: the escaped srcdoc value, un-escaped, == the source.
    srcdoc_escaped = _srcdoc_value(rendered)
    # The attribute is double-quoted, so a literal " inside the doc MUST have been
    # escaped (else it would have closed the attribute early). Prove that happened:
    assert '"' not in srcdoc_escaped, "unescaped double-quote would break the attribute"
    decoded = _html.unescape(srcdoc_escaped)
    assert decoded == adversarial, "srcdoc must round-trip the doc byte-exact"

    # 2) The decoded DOM parses exactly one <script> (the </script> in text/strings
    #    did not split or inject a second script element).
    counter = _ScriptCounter()
    counter.feed(decoded)
    assert counter.script_count == 1, (
        f"expected exactly one parsed <script>, got {counter.script_count}"
    )

    # 3) The render-marker survived the round-trip (proves no lossy transform).
    assert 'name="cast-render-marker"' in decoded

    # 4) Sandbox isolation holds on the adversarial path too.
    sandbox = re.search(r'sandbox="([^"]*)"', rendered).group(1).split()
    assert "allow-same-origin" not in sandbox
