#!/usr/bin/env python3
"""cast-comment-html — serve any HTML with an annotation layer; Submit writes the feedback file.

Mechanical, no reasoning. Input: an HTML file. Output: an annotated-feedback ``.json`` (array of
``{id, quoted_text, section_hint, body, state, ts}`` — the same anchor shape as
``cast-refine-requirements``) plus a sibling ``.md``, written on Submit (or on ``POST /submit``).

Usage (run via uv so stdlib resolves in the project env):
    uv run python tools/comment-html/comment_html.py <input.html> [--out feedback.json] [--port 8077]

Open the printed URL, select text → "+ Comment" → Submit. The output file is written server-side.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def build_page(input_html: str, css: str, anchor_js: str, js: str, cfg: dict) -> str:
    """Inject the layer (config + css + anchor helpers + layer js) right before </body> (or append)."""
    cfg_json = json.dumps(cfg)
    block = (
        "\n<!-- cast-comment-html annotation layer (injected) -->\n"
        f"<style>{css}</style>\n"
        f"<script>{anchor_js}</script>\n"
        f"<script>window.__CCH__={cfg_json};</script>\n"
        f"<script>{js}</script>\n"
    )
    lower = input_html.lower()
    idx = lower.rfind("</body>")
    if idx != -1:
        return input_html[:idx] + block + input_html[idx:]
    return input_html + block


_DISPLAY_CTX = 40  # chars of context shown in the MD; the full unique context stays in the JSON


def context_quote(c: dict) -> str:
    """Render a comment's anchor as ``…prefix⟪quoted⟫suffix…`` so a reader can see exactly which
    spot was commented on — the ⟪ ⟫ markers wrap the selected span, the surrounding context
    disambiguates repeated text.

    The stored prefix/suffix may be long (the capture side grows context until the anchor is
    unique in the document); for the human-readable MD we show only the ``_DISPLAY_CTX`` chars
    nearest the quote. Internal whitespace runs collapse to single spaces, but the boundary space
    between the context and the quote is preserved (it shows the quote does not abut the
    surrounding words). The quoted span itself is stripped, since it is the exact selection.
    """
    collapse = lambda s: re.sub(r"\s+", " ", s or "")  # noqa: E731 — collapse only, keep boundary spaces
    quoted = collapse(c.get("quoted_text") or "").strip()
    prefix = collapse(c.get("prefix") or "")
    suffix = collapse(c.get("suffix") or "")
    if len(prefix) > _DISPLAY_CTX:
        prefix = prefix[-_DISPLAY_CTX:]
    if len(suffix) > _DISPLAY_CTX:
        suffix = suffix[:_DISPLAY_CTX]
    out = ""
    if prefix:
        out += "…" + prefix
    out += "⟪" + quoted + "⟫"
    if suffix:
        out += suffix + "…"
    return out


def render_md(file: str, comments: list) -> str:
    if not comments:
        return "# Feedback\n\n_(no comments yet)_\n"
    lines = ["# Feedback", "", f"_{file}_", ""]
    order: list = []
    groups: dict = {}
    for c in comments:
        sec = c.get("section_hint") or "Document"
        groups.setdefault(sec, [])
        if sec not in order:
            order.append(sec)
        groups[sec].append(c)
    for sec in order:
        lines.append(f"## {sec}")
        for c in groups[sec]:
            if (c.get("quoted_text") or "").strip():
                lines.append("> " + context_quote(c))
            body = c.get("body", "")
            resolved = " _(resolved)_" if c.get("state") == "resolved" else ""
            ts = c.get("ts", "")
            lines.append(f"- {body}{resolved}  `{ts}`")
            lines.append("")
    return "\n".join(lines)


def write_outputs(out_json: str, file_label: str, comments: list) -> dict:
    out_json = os.path.abspath(out_json)
    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(comments, fh, indent=2, ensure_ascii=False)
    out_md = os.path.splitext(out_json)[0] + ".md"
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(render_md(file_label, comments))
    return {"json": out_json, "md": out_md}


def make_handler(page: bytes, input_path: str, out_json: str):
    input_dir = os.path.dirname(input_path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html", "/index"):
                self._send(200, page, "text/html; charset=utf-8")
                return
            # Serve static assets (CSS, JS, images, fonts) from the input HTML's directory.
            rel = path.lstrip("/")
            if rel:
                abs_asset = os.path.normpath(os.path.join(input_dir, rel))
                # Safety: never escape the input directory.
                if abs_asset.startswith(input_dir) and os.path.isfile(abs_asset):
                    mime, _ = mimetypes.guess_type(abs_asset)
                    with open(abs_asset, "rb") as fh:
                        self._send(200, fh.read(), mime or "application/octet-stream")
                    return
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path != "/submit":
                self._send(404, b"not found", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                comments = payload.get("comments", [])
                target = payload.get("out") or out_json
                written = write_outputs(target, input_path, comments)
                body = json.dumps({"ok": True, **written, "count": len(comments)}).encode("utf-8")
                self._send(200, body, "application/json")
                print(f"  ✓ submitted {len(comments)} comment(s) → {written['json']}  (+ .md)")
            except Exception as exc:  # mechanical tool: report, never crash the server
                self._send(500, json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"), "application/json")
                print(f"  ! submit failed: {exc}", file=sys.stderr)

    return Handler


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Serve an HTML file with a comment layer; Submit writes the feedback file.")
    ap.add_argument("input", help="path to the HTML file to annotate")
    ap.add_argument("--out", help="output feedback JSON path (default: <input>.feedback.json next to the input)")
    ap.add_argument("--port", type=int, default=8077)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args(argv)

    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"error: not a file: {input_path}", file=sys.stderr)
        return 2
    out_json = os.path.abspath(args.out) if args.out else (os.path.splitext(input_path)[0] + ".feedback.json")

    css = _read(os.path.join(ASSETS, "comment-layer.css"))
    anchor_js = _read(os.path.join(ASSETS, "anchor.js"))
    js = _read(os.path.join(ASSETS, "comment-layer.js"))
    cfg = {"submit": "/submit", "out": out_json, "file": input_path}
    page = build_page(_read(input_path), css, anchor_js, js, cfg).encode("utf-8")

    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(page, input_path, out_json))
    url = f"http://{args.host}:{args.port}/"
    print(f"cast-comment-html · serving {input_path}")
    print(f"  open   {url}")
    print(f"  annotate → Submit  →  {out_json}  (+ .md)")
    print("  Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
