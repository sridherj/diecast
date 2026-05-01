"""Hook handler implementations. Called by `cast-hook <subcommand>`.

Each handler reads JSON from stdin, posts to cast-server, and returns. Any
network/HTTP failure exits silently — never block the user's prompt.
"""
import json
import os
import sys
import urllib.error
import urllib.request

from cast_server.cli._cast_name import AGENT_TYPE_PATTERN, PROMPT_PATTERN


def _base_url() -> str:
    port = os.environ.get("CAST_PORT", "8005")
    host = os.environ.get("CAST_HOST", "127.0.0.1")
    return f"http://{host}:{port}/api/agents"


def _post(path: str, body: dict) -> None:
    """Fire-and-forget POST. Sends the request, then returns without reading
    the response body. The 2s urlopen timeout still bounds the worst case for
    establishing the connection, but the typical path returns as soon as the
    server has accepted the bytes. Server logs any errors; client never sees
    them — the hook never blocks the prompt anyway (FR-010).
    """
    try:
        req = urllib.request.Request(
            f"{_base_url()}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
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


def subagent_start() -> None:
    """SubagentStart hook: open a subagent-invocation row for cast-* subagents.

    Hook-side scope filter via ``AGENT_TYPE_PATTERN`` short-circuits non-cast
    subagents (e.g. built-in ``Explore``) so cast-server never sees the POST.
    Server keeps its own filter as defense in depth.
    """
    payload = _read_payload()
    agent_type = payload.get("agent_type")
    session_id = payload.get("session_id")
    claude_agent_id = payload.get("agent_id")
    if not agent_type or not session_id or not claude_agent_id:
        return  # malformed payload — exit 0, no POST (FR-010)
    if not AGENT_TYPE_PATTERN.match(agent_type):
        return  # non-cast-* — early-return, no POST
    _post(
        "/subagent-invocations",
        {
            "agent_type": agent_type,
            "session_id": session_id,
            "claude_agent_id": claude_agent_id,
            "transcript_path": payload.get("transcript_path"),
        },
    )


def subagent_stop() -> None:
    """SubagentStop hook: close the row whose ``claude_agent_id`` matches."""
    payload = _read_payload()
    claude_agent_id = payload.get("agent_id")
    if not claude_agent_id:
        return  # malformed payload — exit 0, no POST
    _post(
        "/subagent-invocations/complete",
        {"claude_agent_id": claude_agent_id},
    )


def skill_invoke() -> None:
    """PreToolUse(Skill) hook: append the skill to the most-recent running cast-* row.

    The settings.json ``matcher: "Skill"`` should narrow this hook to Skill
    tool calls, but a handler-side ``tool_name`` check is cheap insurance.
    Wire field is ``skill`` (singular) — matches the empirical
    ``tool_input.skill`` payload key, NOT ``skill_name``.
    """
    payload = _read_payload()
    if payload.get("tool_name") != "Skill":
        return
    session_id = payload.get("session_id")
    tool_input = payload.get("tool_input") or {}
    skill = tool_input.get("skill")
    if not session_id or not skill:
        return
    _post(
        "/subagent-invocations/skill",
        {"session_id": session_id, "skill": skill},
    )
