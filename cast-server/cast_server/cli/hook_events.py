"""Canonical mapping: Claude Code hook event → cast-hook subcommand → handler.

DO NOT duplicate this list anywhere. Both install_hooks.py (settings injection)
and hook.py (runtime dispatch) import from here. Adding a new hook event = one
line in this file.
"""
from pathlib import Path

from cast_server.cli import hook_handlers as _h

# (claude_code_event, cast_hook_subcommand, handler)
HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop),
]

# Absolute path to the cast-hook entry, resolved through the diecast skill
# umbrella symlink that ./setup creates (see bin/_lib.sh::install_diecast_skill_root).
# Hook commands are written into .claude/settings.json with this absolute prefix
# so Claude Code does not have to rely on PATH composition. PATH-based
# resolution was unreliable: Claude Code fires hooks with a restricted shell
# PATH that does not include ~/.local/bin/ or .venv/bin/.
CAST_HOOK_BIN = str(Path.home() / ".claude" / "skills" / "diecast" / "bin" / "cast-hook")

# Derived views — convenience for callers; do not extend this list, extend HOOK_EVENTS.
DISPATCH = {sub: handler for _, sub, handler in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"{CAST_HOOK_BIN} {sub}" for evt, sub, _ in HOOK_EVENTS}
