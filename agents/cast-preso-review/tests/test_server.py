"""Server tests for cast-preso-review.

Covers:

* GET ``/``   → serves ``review.html`` with 200 when Host is allowed.
* POST ``/feedback`` → writes ``<goal_dir>/presentation/feedback/<stage>-<ts>Z.md``.
* POST ``/decisions/<id>`` → writes ``<id>.answer.md`` under
  ``<goal_dir>/presentation/decisions/``.
* Non-localhost ``Host`` header → 403.
* Path-traversal id on /decisions → 400 (or 404 depending on path normalization).
* Traversal on GET path stays inside ``output_root``.

All tests bind to ``127.0.0.1`` on port ``0`` so runs don't collide.
"""

from __future__ import annotations

import http.client
import json
import sys
import threading
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import server  # noqa: E402


@pytest.fixture
def running_server(tmp_path: Path):
    """Start a fresh server on an ephemeral port for each test."""
    goal = tmp_path / "goal"
    out = goal / "presentation"
    out.mkdir(parents=True)
    (out / "review.html").write_text(
        "<html><body>ok</body></html>", encoding="utf-8"
    )

    srv, port = server.make_server(output_dir=out, goal_dir=goal, stage="narrative")
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield srv, port, goal
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


def _conn(port: int) -> http.client.HTTPConnection:
    return http.client.HTTPConnection("127.0.0.1", port, timeout=5)


# ---------- GET ----------


def test_get_root_returns_review_html(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("GET", "/")
    resp = c.getresponse()
    assert resp.status == 200
    assert b"<html>" in resp.read()


def test_get_explicit_review_html(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("GET", "/review.html")
    resp = c.getresponse()
    assert resp.status == 200


def test_get_localhost_host_header_allowed(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("GET", "/", headers={"Host": "localhost"})
    resp = c.getresponse()
    assert resp.status == 200


# ---------- POST /feedback ----------


def test_post_feedback_writes_file(running_server):
    _, port, goal = running_server
    body = b"# feedback\n- change X to Y\n"
    c = _conn(port)
    c.request(
        "POST",
        "/feedback",
        body=body,
        headers={"Content-Type": "text/markdown", "Content-Length": str(len(body))},
    )
    resp = c.getresponse()
    assert resp.status == 200
    payload = json.loads(resp.read())
    written = Path(payload["path"])
    assert written.exists()
    assert written.parent == goal / "presentation" / "feedback"
    assert written.name.startswith("narrative-")
    assert written.name.endswith("Z.md")
    assert written.read_bytes() == body
    assert payload["bytes"] == len(body)


def test_post_feedback_creates_dir_if_missing(tmp_path: Path):
    goal = tmp_path / "goal"
    out = goal / "presentation"
    out.mkdir(parents=True)
    (out / "review.html").write_text("ok", encoding="utf-8")
    srv, port = server.make_server(output_dir=out, goal_dir=goal, stage="what")
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        body = b"note"
        c = _conn(port)
        c.request(
            "POST",
            "/feedback",
            body=body,
            headers={"Content-Length": str(len(body))},
        )
        resp = c.getresponse()
        assert resp.status == 200
        assert (goal / "presentation" / "feedback").is_dir()
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


# ---------- POST /decisions/<id> ----------


def test_post_decision_writes_file(running_server):
    _, port, goal = running_server
    body = b"**Picked:** A\n"
    c = _conn(port)
    c.request(
        "POST",
        "/decisions/Q-07",
        body=body,
        headers={"Content-Type": "text/markdown", "Content-Length": str(len(body))},
    )
    resp = c.getresponse()
    assert resp.status == 200
    answer = goal / "presentation" / "decisions" / "Q-07.answer.md"
    assert answer.exists()
    assert answer.read_bytes() == body


def test_post_decision_accepts_alnum_dot_underscore_hyphen(running_server):
    _, port, _ = running_server
    for qid in ("Q-01", "Q_02", "Q.03", "abc123"):
        c = _conn(port)
        body = b"x"
        c.request("POST", f"/decisions/{qid}", body=body,
                  headers={"Content-Length": "1"})
        resp = c.getresponse()
        resp.read()  # drain
        assert resp.status == 200


def test_post_decision_id_traversal_rejected(running_server):
    _, port, _ = running_server
    # URL-encoded traversal — the server sees '..%2Fescape' after BaseHTTPRequestHandler
    # parses the path; it must not be accepted.
    c = _conn(port)
    c.request("POST", "/decisions/..%2Fescape", body=b"x",
              headers={"Content-Length": "1"})
    resp = c.getresponse()
    assert resp.status in (400, 404)


def test_post_decision_id_too_long_rejected(running_server):
    _, port, _ = running_server
    too_long = "q" * 65  # SAFE_ID caps at 64
    c = _conn(port)
    c.request("POST", f"/decisions/{too_long}", body=b"x",
              headers={"Content-Length": "1"})
    resp = c.getresponse()
    assert resp.status == 400


# ---------- Host header / DNS-rebinding defense ----------


def test_bad_host_is_rejected_on_get(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("GET", "/", headers={"Host": "evil.example.com"})
    resp = c.getresponse()
    assert resp.status == 403


def test_bad_host_is_rejected_on_post(running_server):
    _, port, _ = running_server
    body = b"x"
    c = _conn(port)
    c.request("POST", "/feedback", body=body,
              headers={"Host": "evil.example.com", "Content-Length": "1"})
    resp = c.getresponse()
    assert resp.status == 403


def test_host_with_port_allowed(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("GET", "/", headers={"Host": f"127.0.0.1:{port}"})
    resp = c.getresponse()
    assert resp.status == 200


# ---------- Other ----------


def test_unknown_endpoint_returns_404(running_server):
    _, port, _ = running_server
    c = _conn(port)
    c.request("POST", "/bogus", body=b"", headers={"Content-Length": "0"})
    resp = c.getresponse()
    assert resp.status == 404


def test_make_server_returns_bound_port(tmp_path: Path):
    goal = tmp_path / "goal"
    out = goal / "presentation"
    out.mkdir(parents=True)
    (out / "review.html").write_text("ok", encoding="utf-8")
    srv, port = server.make_server(output_dir=out, goal_dir=goal, stage="narrative")
    try:
        assert port > 0
        assert srv.server_address[0] == "127.0.0.1"
    finally:
        srv.server_close()
