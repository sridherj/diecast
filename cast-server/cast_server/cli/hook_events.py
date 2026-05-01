"""Canonical mapping: Claude Code hook event → cast-hook subcommand → handler.

DO NOT duplicate this list anywhere. Both install_hooks.py (settings injection)
and hook.py (runtime dispatch) import from here. Adding a new hook event = one
line in this file.
"""
from cast_server.cli import hook_handlers as _h

# (claude_code_event, cast_hook_subcommand, handler)
HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop),
]

# Derived views — convenience for callers; do not extend this list, extend HOOK_EVENTS.
DISPATCH = {sub: handler for _, sub, handler in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"cast-hook {sub}" for evt, sub, _ in HOOK_EVENTS}
