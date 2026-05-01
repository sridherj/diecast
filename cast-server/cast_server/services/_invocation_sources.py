"""Source discriminator constants + filter helper for ``agent_runs.input_params``.

Every hook-created ``agent_runs`` row carries an ``input_params.source``
field naming which capture path inserted it. Constants live here so a typo
in the literal can't drift between writer (``register``) and closer
(``complete``). Both sibling ``user_invocation_service`` and the new
``subagent_invocation_service`` (sp2) import from this module.
"""
from __future__ import annotations

USER_PROMPT = "user-prompt"
SUBAGENT_START = "subagent-start"


def source_filter_clause() -> str:
    """SQL fragment matching ``input_params.source`` against a placeholder.

    Returned exactly so callers can splice it into a WHERE clause without
    re-writing the JSON path; the ``?`` is filled in with one of the source
    constants. Subagent ``complete()`` keys on ``claude_agent_id`` so it
    does not need this helper — only the user-invocation closure path does.
    """
    return "json_extract(input_params, '$.source') = ?"
