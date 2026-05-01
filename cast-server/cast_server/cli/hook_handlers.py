"""Hook handler implementations. Called by `cast-hook <subcommand>`.

Each handler reads JSON from stdin, posts to cast-server, and returns. Any
network/HTTP failure exits silently — never block the user's prompt.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

PROMPT_PATTERN = re.compile(r"^\s*/(cast-[a-z0-9-]+)")


def _base_url() -> str:
    port = os.environ.get("CAST_PORT", "8005")
    host = os.environ.get("CAST_HOST", "127.0.0.1")
    return f"http://{host}:{port}/api/agents"


def _post(path: str, body: dict) -> None:
    try:
        req = urllib.request.Request(
            f"{_base_url()}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2).read()
    except (urllib.error.URLError, TimeoutError, OSError):
        pass  # never block the prompt


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def user_prompt_start() -> None:
    payload = _read_payload()
    prompt = payload.get("prompt", "")
    m = PROMPT_PATTERN.match(prompt)
    if not m:
        return
    _post(
        "/user-invocations",
        {
            "agent_name": m.group(1),
            "prompt": prompt,
            "session_id": payload.get("session_id"),
        },
    )


def user_prompt_stop() -> None:
    payload = _read_payload()
    session_id = payload.get("session_id")
    if not session_id:
        return
    _post("/user-invocations/complete", {"session_id": session_id})
