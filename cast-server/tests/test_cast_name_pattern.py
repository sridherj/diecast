"""Positive/negative coverage for the shared cast-name regexes.

Both ``PROMPT_PATTERN`` (slash-prefixed user prompts) and
``AGENT_TYPE_PATTERN`` (bare ``cast-foo`` subagent_type names) live in
``cast_server.cli._cast_name``. The regex IS the contract for "what counts
as cast-*" — the hook handler imports ``PROMPT_PATTERN`` from here, so any
behavioural drift breaks the sibling user-invocation pipeline.
"""
from __future__ import annotations

import pytest

from cast_server.cli._cast_name import AGENT_TYPE_PATTERN, PROMPT_PATTERN


@pytest.mark.parametrize(
    "prompt,expected_name",
    [
        ("/cast-foo", "cast-foo"),
        ("/cast-foo bar baz", "cast-foo"),
        ("  /cast-foo with leading whitespace", "cast-foo"),
        ("/cast-foo-bar-baz extra", "cast-foo-bar-baz"),
        ("/cast-detailed-plan look at this goal", "cast-detailed-plan"),
        ("/cast-a", "cast-a"),
        ("/cast-123", "cast-123"),
    ],
)
def test_prompt_pattern_matches_cast_slash_command(prompt: str, expected_name: str) -> None:
    m = PROMPT_PATTERN.match(prompt)
    assert m is not None
    assert m.group(1) == expected_name


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        "what time is it",
        "Cast-foo",            # leading capital — body is lowercase only
        "/Cast-foo",           # ditto, slash form
        "/cast_foo",           # underscore not hyphen
        "/cast-",              # body must be at least one char
        "not-cast-foo",        # no slash
        "//cast-foo",          # double-slash isn't a slash command
        " cast-foo",           # missing slash, just whitespace
        "/notcastfoo",         # missing the literal "cast-" prefix
    ],
)
def test_prompt_pattern_rejects_non_cast(prompt: str) -> None:
    assert PROMPT_PATTERN.match(prompt) is None


@pytest.mark.parametrize(
    "agent_type",
    [
        "cast-foo",
        "cast-detailed-plan",
        "cast-foo-bar-baz",
        "cast-a",
        "cast-123",
    ],
)
def test_agent_type_pattern_matches_bare_cast_name(agent_type: str) -> None:
    assert AGENT_TYPE_PATTERN.match(agent_type) is not None


@pytest.mark.parametrize(
    "agent_type",
    [
        "",
        "Cast-foo",
        "cast_foo",
        "cast-",
        "Explore",                # non-cast subagent must not match
        "general-purpose",
        "/cast-foo",              # slash-prefixed must NOT match the bare form
        "cast-foo trailing",      # trailing whitespace — anchored regex must reject
        " cast-foo",              # leading whitespace
        "cast-foo ",
    ],
)
def test_agent_type_pattern_rejects_non_cast(agent_type: str) -> None:
    assert AGENT_TYPE_PATTERN.match(agent_type) is None
