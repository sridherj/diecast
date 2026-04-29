"""Local review server for cast-preso-review.

Loopback-only, stdlib-only HTTP server that serves the generated
``review.html`` and accepts POST exports from the client:

* ``POST /feedback``         → writes `<goal_dir>/presentation/feedback/<stage>-<ts>Z.md`
* ``POST /decisions/<q_id>`` → writes `<goal_dir>/presentation/decisions/<q_id>.answer.md`

Security posture (see ``phase-1d-server-and-wrap.md`` §1d.1):

* Bind ``127.0.0.1`` only — no CLI override to expose off-host.
* Reject any request whose ``Host`` header isn't ``localhost`` / ``127.0.0.1``
  (DNS-rebinding defense). No auth otherwise — this is local-only tooling.
* ``translate_path`` is scoped to ``output_root`` so ``..`` traversal on GET
  cannot escape the presentation dir.
* ``SAFE_ID`` rejects path traversal or oversized ids on the decisions route.
"""

from __future__ import annotations

import datetime as dt
import http.server
import json
import re
import socketserver
import threading
import webbrowser
from pathlib import Path

ISO_NO_COLON = "%Y%m%dT%H%M%S"  # filename-safe timestamp
SAFE_ID = re.compile(r"[A-Za-z0-9\-_.]{1,64}$")
ALLOWED_HOSTS = {"localhost", "127.0.0.1"}


class ReviewRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves review.html + static assets; accepts POST feedback/decision answers."""

    # Injected by make_server() via a dynamic subclass before binding.
    output_root: Path
    feedback_root: Path
    decisions_root: Path
    stage: str

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        return host in ALLOWED_HOSTS

    def do_GET(self) -> None:
        if not self._host_ok():
            self.send_error(403, "bad Host header")
            return
        if self.path in ("", "/"):
            self.path = "/review.html"
        super().do_GET()

    def do_POST(self) -> None:
        if not self._host_ok():
            self.send_error(403, "bad Host header")
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else b""

        if self.path == "/feedback":
            self._write_feedback(body)
            return

        m = re.fullmatch(r"/decisions/([^/]+)", self.path)
        if m:
            self._write_decision_answer(m.group(1), body)
            return

        self.send_error(404, "unknown endpoint")

    def _write_feedback(self, body: bytes) -> None:
        ts = dt.datetime.now(dt.timezone.utc).strftime(ISO_NO_COLON)
        path = self.feedback_root / f"{self.stage}-{ts}Z.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        self._send_json(200, {"path": str(path), "bytes": len(body)})

    def _write_decision_answer(self, q_id: str, body: bytes) -> None:
        if not SAFE_ID.fullmatch(q_id):
            self.send_error(400, "bad question id")
            return
        path = self.decisions_root / f"{q_id}.answer.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        self._send_json(200, {"path": str(path), "bytes": len(body)})

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def translate_path(self, path: str) -> str:
        # Scope all GET serving to output_root; strip query/fragment first.
        path = path.split("?", 1)[0].split("#", 1)[0]
        rel = path.lstrip("/") or "review.html"
        target = (self.output_root / rel).resolve()
        # Reject traversal outside output_root.
        try:
            target.relative_to(self.output_root.resolve())
        except ValueError:
            return str(self.output_root / "review.html")
        return str(target)

    def log_message(self, format: str, *args) -> None:  # noqa: A002 — stdlib signature
        # Quiet stderr; signature mirrors BaseHTTPRequestHandler.log_message.
        del format, args


def make_server(
    output_dir: Path,
    goal_dir: Path,
    stage: str,
    port: int = 0,
    bind: str = "127.0.0.1",
) -> tuple[socketserver.TCPServer, int]:
    """Build a bound TCP server. Port 0 ⇒ OS-picked ephemeral."""
    handler_cls = type(
        "BoundReviewHandler",
        (ReviewRequestHandler,),
        {
            "output_root": Path(output_dir).resolve(),
            "feedback_root": Path(goal_dir) / "presentation" / "feedback",
            "decisions_root": Path(goal_dir) / "presentation" / "decisions",
            "stage": stage,
        },
    )
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer((bind, port), handler_cls)
    bound_port = srv.server_address[1]
    return srv, bound_port


def run_foreground(
    output_dir: Path,
    goal_dir: Path,
    stage: str,
    *,
    port: int = 0,
    open_browser: bool = True,
) -> None:
    """Start the server in the foreground until Ctrl-C."""
    srv, bound = make_server(output_dir, goal_dir, stage, port=port)
    url = f"http://127.0.0.1:{bound}/"
    print(f"cast-preso-review serving at {url}")
    print(f"  (fallback file://): file://{output_dir / 'review.html'}")
    print(f"  feedback → {goal_dir / 'presentation' / 'feedback'}/")
    print(f"  decisions → {goal_dir / 'presentation' / 'decisions'}/")
    if open_browser:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down.")
    finally:
        srv.server_close()
