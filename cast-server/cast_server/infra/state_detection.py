"""4-state detection algorithm for Claude agent tmux panes."""

import re
from enum import Enum

from .tmux_manager import _has_input_field


class AgentState(Enum):
    WORKING = "working"
    IDLE = "idle"
    SHELL_RETURNED = "shell"
    WAITING_INPUT = "stuck"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


# Rate limit patterns — primary patterns are sufficient alone;
# reset time pattern requires a primary pattern to also be present
# to avoid false positives from agent output mentioning "resets 3pm".
RATE_LIMIT_PRIMARY = [
    re.compile(r"hit your limit", re.IGNORECASE),
    re.compile(r"you've hit your", re.IGNORECASE),
]
RATE_LIMIT_RESET = re.compile(r"resets?\s+(at\s+)?\d+\s*(am|pm)", re.IGNORECASE)

# Permission/input prompt patterns
INPUT_PROMPT_PATTERNS = [
    re.compile(r"\[y/n\]", re.IGNORECASE),
    re.compile(r"\[Y/n\]"),
    re.compile(r"\[yes/no\]", re.IGNORECASE),
]


def detect_agent_state(pane_content: list[str], pane_command: str) -> AgentState:
    """Detection algorithm (validated by spike 2026-03-19):

    1. SHELL_RETURNED — cheapest check, pane_current_command != 'claude'
    2. RATE_LIMITED — check before input field
    3. WAITING_INPUT — [y/n] without input field
    4. Input field detection — border-adjacency check (NON-NEGOTIABLE)
    5. WORKING — has_input_field AND 'esc to interrupt'
    6. IDLE — has_input_field AND no interrupt message
    7. UNKNOWN — fallback
    """
    if not pane_content:
        return AgentState.UNKNOWN

    # 1. SHELL_RETURNED
    if pane_command and pane_command != "claude":
        return AgentState.SHELL_RETURNED

    content_text = "\n".join(pane_content)

    # 2. RATE_LIMITED — require a primary pattern match
    if any(p.search(content_text) for p in RATE_LIMIT_PRIMARY):
        return AgentState.RATE_LIMITED

    # 3. WAITING_INPUT
    if any(p.search(content_text) for p in INPUT_PROMPT_PATTERNS):
        has_field, _ = _has_input_field(pane_content)
        if not has_field:
            return AgentState.WAITING_INPUT

    # 4-6. Input field detection
    has_field, _ = _has_input_field(pane_content)
    if has_field:
        # 5. WORKING
        if "esc to interrupt" in content_text.lower():
            return AgentState.WORKING
        # 6. IDLE
        return AgentState.IDLE

    # 7. UNKNOWN
    return AgentState.UNKNOWN
