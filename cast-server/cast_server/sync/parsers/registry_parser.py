"""Parse agents/REGISTRY.md into agent records.

The registry uses a section-based format:
    ## agent-name
    - **Description:** ...
    - **Tags:** [tag1] [tag2]
    - **Triggers:** "phrase1", "phrase2"
    - **Last Tested:** Never | date
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_registry(registry_path: Path) -> list[dict]:
    """Parse REGISTRY.md into a list of agent dicts.

    Returns empty list if file doesn't exist or can't be parsed.
    """
    if not registry_path.exists():
        return []

    try:
        content = registry_path.read_text()
    except OSError:
        return []

    agents = []
    now = datetime.now(timezone.utc).isoformat()

    current_name = None
    current_data: dict = {}

    for line in content.split("\n"):
        # Agent section header: ## agent-name or ## agent-name *(archived)*
        header_match = re.match(r"^## (\S+)(.*)$", line)
        if header_match:
            # Save previous agent if any
            if current_name:
                agents.append(_build_agent_record(current_name, current_data, now))

            current_name = header_match.group(1)
            current_data = {}
            # Check for archived marker
            rest = header_match.group(2).strip()
            if "archived" in rest.lower():
                current_data["archived"] = True
            continue

        if current_name is None:
            continue

        # Parse bullet metadata lines
        line_stripped = line.strip()
        if not line_stripped.startswith("- **"):
            continue

        field_match = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line_stripped)
        if not field_match:
            continue

        field_name = field_match.group(1).strip().lower()
        field_value = field_match.group(2).strip()

        if field_name == "description":
            current_data["description"] = _clean_description(field_value)
        elif field_name == "type":
            current_data["type"] = field_value
        elif field_name == "input":
            current_data["input"] = field_value
        elif field_name == "output":
            current_data["output"] = field_value
        elif field_name == "tags":
            current_data["tags"] = _parse_bracket_tags(field_value)
        elif field_name == "triggers":
            current_data["triggers"] = _parse_quoted_list(field_value)
        elif field_name == "last tested":
            current_data["last_tested"] = field_value if field_value.lower() not in ("never", "n/a", "n/a (archived)") else None

    # Don't forget the last agent
    if current_name:
        agents.append(_build_agent_record(current_name, current_data, now))

    return agents


def _build_agent_record(name: str, data: dict, now: str) -> dict:
    return {
        "name": name,
        "type": data.get("type", ""),
        "description": data.get("description", ""),
        "input": data.get("input", ""),
        "output": data.get("output", ""),
        "tags": json.dumps(data.get("tags", [])),
        "triggers": json.dumps(data.get("triggers", [])),
        "last_tested": data.get("last_tested"),
        "synced_at": now,
    }


def _clean_description(text: str) -> str:
    """Remove strikethrough markers from archived descriptions."""
    return re.sub(r"~~(.+?)~~", r"\1", text)


def _parse_bracket_tags(text: str) -> list[str]:
    """Parse [tag1] [tag2] [tag3] format."""
    return re.findall(r"\[([^\]]+)\]", text)


def _parse_quoted_list(text: str) -> list[str]:
    """Parse "phrase1", "phrase2" format."""
    items = re.findall(r'"([^"]+)"', text)
    if items:
        return items
    # Fallback: N/A or empty
    return []
