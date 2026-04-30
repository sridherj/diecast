"""Parse rate limit reset time from Claude CLI pane output."""
import re
from datetime import datetime, timedelta

# Patterns for reset time extraction
RESET_TIME_PATTERNS = [
    # "resets at 3pm", "resets at 3:15pm", "resets 3pm"
    re.compile(r"resets?\s+(?:at\s+)?(\d{1,2}(?::\d{2})?)\s*(am|pm)", re.IGNORECASE),
    # "try again in X minutes"
    re.compile(r"try again in (\d+)\s*min", re.IGNORECASE),
]

FALLBACK_COOLDOWN_MINUTES = 15
BUFFER_MINUTES = 2


def parse_rate_limit_reset(pane_text: str) -> datetime:
    """Parse the rate limit reset time from pane content.

    Returns the datetime when we should resume (reset time + 2min buffer).
    Falls back to now + 15min if unparseable.
    """
    for pattern in RESET_TIME_PATTERNS:
        match = pattern.search(pane_text)
        if match:
            groups = match.groups()

            if len(groups) == 2 and groups[1]:  # "resets at Xam/pm" format
                time_str, ampm = groups
                try:
                    if ":" in time_str:
                        parsed = datetime.strptime(f"{time_str}{ampm}", "%I:%M%p")
                    else:
                        parsed = datetime.strptime(f"{time_str}{ampm}", "%I%p")

                    now = datetime.now()
                    reset_time = now.replace(
                        hour=parsed.hour, minute=parsed.minute,
                        second=0, microsecond=0
                    )
                    # If reset time is in the past, it's tomorrow
                    if reset_time < now:
                        reset_time += timedelta(days=1)

                    return reset_time + timedelta(minutes=BUFFER_MINUTES)
                except ValueError:
                    continue

            elif len(groups) >= 1:  # "try again in X minutes" format
                try:
                    minutes = int(groups[0])
                    return datetime.now() + timedelta(minutes=minutes + BUFFER_MINUTES)
                except ValueError:
                    continue

    # Fallback: fixed cooldown
    return datetime.now() + timedelta(minutes=FALLBACK_COOLDOWN_MINUTES)
