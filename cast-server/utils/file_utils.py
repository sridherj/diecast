"""File-related utilities."""

import re


def extract_authorship(filename: str) -> str | None:
    """Extract authorship from filename like 'plan.collab.md' -> 'collab'."""
    match = re.match(r'(.+)\.(human|ai|collab)\.md$', filename)
    return match.group(2) if match else None
