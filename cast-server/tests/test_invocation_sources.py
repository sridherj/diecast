"""Unit tests for ``services._invocation_sources``.

The constants and SQL-fragment helper are tiny but load-bearing — both
sibling ``user_invocation_service`` and the new ``subagent_invocation_service``
(sp2) import from this module. Any drift in the literal strings would
silently break ``complete()`` lookups (UPDATE matches no rows, runs leak as
``running``).
"""
from __future__ import annotations

from cast_server.services._invocation_sources import (
    SUBAGENT_START,
    USER_PROMPT,
    source_filter_clause,
)


def test_user_prompt_constant_value() -> None:
    assert USER_PROMPT == "user-prompt"


def test_subagent_start_constant_value() -> None:
    assert SUBAGENT_START == "subagent-start"


def test_source_filter_clause_shape() -> None:
    assert source_filter_clause() == "json_extract(input_params, '$.source') = ?"
