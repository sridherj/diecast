"""Single source of truth for cast-* name regexes.

``CAST_NAME_BODY`` is the lowercase-letter / digit / hyphen body that follows
the literal ``cast-`` prefix. Both regexes share this body so changes to the
naming contract land in one place. Used by the user-prompt hook (slash-prefix
match), the SubagentStart hook (bare-name match), and server-side filters.
"""
from __future__ import annotations

import re

CAST_NAME_BODY = r"cast-[a-z0-9-]+"

# Matches a leading ``/cast-foo`` slash command in a user-typed prompt.
# Capture group 1 is the bare cast-* name (no leading slash).
PROMPT_PATTERN = re.compile(rf"^\s*/({CAST_NAME_BODY})")

# Matches a bare ``cast-foo`` agent_type as emitted in SubagentStart payloads.
AGENT_TYPE_PATTERN = re.compile(rf"^{CAST_NAME_BODY}$")
