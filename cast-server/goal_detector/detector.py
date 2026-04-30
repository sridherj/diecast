"""GoalDetector — builds prompt and parses Claude Code output.

Hybrid approach: deterministic regex pre-filter for explicit intent patterns,
injected as MUST-INCLUDE hints into the LLM prompt, with post-processing fallback.
"""

import json
import re
from pathlib import Path

from taskos.config import GOALS_DIR, SCRATCHPAD_PATH

# Regex patterns for explicit intent detection
_INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("I want to", re.compile(r"I want to\b", re.IGNORECASE)),
    ("I need to", re.compile(r"I need to\b", re.IGNORECASE)),
    ("I should", re.compile(r"I should\b", re.IGNORECASE)),
    ("Want to", re.compile(r"^Want to\b", re.IGNORECASE)),
    ("Need to", re.compile(r"^Need to\b", re.IGNORECASE)),
    ("Goal:", re.compile(r"^Goal:", re.IGNORECASE)),
    ("Build", re.compile(r"^Build\b")),
    ("Create", re.compile(r"^Create\b")),
    ("Launch", re.compile(r"^Launch\b")),
    ("Ship", re.compile(r"^Ship\b")),
]

# Prefixes to strip when extracting titles
_TITLE_PREFIXES = re.compile(
    r"^(I want to|I need to|I should|Want to|Need to|Goal:\s*)\s*",
    re.IGNORECASE,
)

_DATE_HEADER = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})")


def slugify(title: str) -> str:
    """Convert title to URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def extract_intent_lines(scratchpad_text: str) -> list[dict]:
    """Extract lines with explicit intent signals from scratchpad text.

    Returns list of {"date": str, "line": str, "signal": str}.
    """
    results = []
    current_date = "unknown"

    for raw_line in scratchpad_text.splitlines():
        # Track date headers
        date_match = _DATE_HEADER.match(raw_line.strip())
        if date_match:
            current_date = date_match.group(1)
            continue

        # Strip bullet prefix to get the content
        content = raw_line.strip().lstrip("-").strip()
        if not content:
            continue

        # Skip @claude directives
        if content.startswith("@claude"):
            continue

        for signal, pattern in _INTENT_PATTERNS:
            if pattern.search(content):
                results.append({
                    "date": current_date,
                    "line": content,
                    "signal": signal,
                })
                break

    return results


def _extract_title(line: str) -> str:
    """Extract a goal title from an intent line.

    Strips intent prefixes, takes first sentence, caps at 60 chars, title-cases.
    """
    title = _TITLE_PREFIXES.sub("", line).strip()

    # Take first sentence only
    for sep in (".", "!", "?"):
        idx = title.find(sep)
        if idx > 0:
            title = title[:idx]
            break

    # Cap at 60 chars
    if len(title) > 60:
        title = title[:57] + "..."

    # Title case
    title = title.strip()
    if title and title[0].islower():
        title = title[0].upper() + title[1:]

    # Apply title case if the line had a lowercase prefix stripped
    words = title.split()
    if words and words[0][0].islower():
        words[0] = words[0].capitalize()
    title = " ".join(words)

    # If the prefix was stripped, apply smart title case
    if _TITLE_PREFIXES.match(line):
        title = _smart_title_case(title)

    return title


_SMALL_WORDS = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at",
                "to", "in", "of", "by", "up", "is", "it", "as", "so", "no"}


def _smart_title_case(text: str) -> str:
    """Title-case that keeps small words lowercase (except first word)."""
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in _SMALL_WORDS:
            # Preserve all-caps words (acronyms like MVP, DB, EOW)
            if w.isupper() and len(w) > 1:
                result.append(w)
            else:
                result.append(w.capitalize())
        else:
            result.append(w.lower())
    return " ".join(result)


def _filter_existing(
    intent_lines: list[dict],
    existing_slugs: list[str],
) -> list[dict]:
    """Remove intent lines whose slugified form matches existing goal slugs.

    Matches by: substring containment or >50% word overlap.
    """
    if not existing_slugs:
        return list(intent_lines)

    filtered = []
    for il in intent_lines:
        line_slug = slugify(_extract_title(il["line"]))
        line_words = set(line_slug.split("-"))

        is_duplicate = False
        for existing in existing_slugs:
            # Substring match (either direction)
            if line_slug in existing or existing in line_slug:
                is_duplicate = True
                break
            # Word overlap > 50% from either direction
            existing_words = set(existing.split("-"))
            overlap = line_words & existing_words
            line_ratio = len(overlap) / len(line_words) if line_words else 0
            existing_ratio = len(overlap) / len(existing_words) if existing_words else 0
            if line_ratio > 0.5 or existing_ratio > 0.5:
                is_duplicate = True
                break

        if not is_duplicate:
            filtered.append(il)

    return filtered


def ensure_intent_suggestions(
    intent_lines: list[dict],
    llm_suggestions: list[dict],
    existing_slugs: list[str],
) -> list[dict]:
    """Post-processing safety net: ensure regex-matched intents appear in suggestions.

    - If LLM covered an intent line → apply confidence floor of 0.75
    - If LLM missed one → generate fallback suggestion (confidence 0.80)
    - Deduplicates against existing goals and LLM suggestions
    """
    if not intent_lines:
        return llm_suggestions

    result = list(llm_suggestions)

    for il in intent_lines:
        title = _extract_title(il["line"])
        intent_slug = slugify(title)

        # Skip if matches existing goal
        is_existing = False
        intent_words = set(intent_slug.split("-"))
        for es in existing_slugs:
            if intent_slug in es or es in intent_slug:
                is_existing = True
                break
            es_words = set(es.split("-"))
            overlap = intent_words & es_words
            i_ratio = len(overlap) / len(intent_words) if intent_words else 0
            e_ratio = len(overlap) / len(es_words) if es_words else 0
            if i_ratio > 0.5 or e_ratio > 0.5:
                is_existing = True
                break
        if is_existing:
            continue

        # Check if LLM already covered this intent
        covered = False
        for suggestion in result:
            s_slug = suggestion.get("slug", "")
            s_words = set(s_slug.split("-"))
            # Check slug containment or word overlap
            if intent_slug in s_slug or s_slug in intent_slug:
                covered = True
                suggestion["confidence"] = max(suggestion.get("confidence", 0), 0.75)
                break
            overlap = intent_words & s_words
            i_ratio = len(overlap) / len(intent_words) if intent_words else 0
            s_ratio = len(overlap) / len(s_words) if s_words else 0
            if i_ratio > 0.5 or s_ratio > 0.5:
                covered = True
                suggestion["confidence"] = max(suggestion.get("confidence", 0), 0.75)
                break

        if not covered:
            result.append({
                "title": title,
                "slug": intent_slug,
                "rationale": f"Explicit intent detected: \"{il['signal']}\" on {il['date']}",
                "confidence": 0.80,
                "source_dates": [il["date"]],
                "suggested_tags": [],
            })

    return result


def build_detector_prompt(
    scratchpad_path: Path = None,
    goals_dir: Path = None,
) -> tuple[str, list[dict]]:
    """Build the prompt for the GoalDetector Claude Code session.

    Returns (prompt_text, intent_lines) tuple.
    """
    scratchpad_path = scratchpad_path or SCRATCHPAD_PATH
    goals_dir = goals_dir or GOALS_DIR

    # Read scratchpad
    scratchpad_content = ""
    if scratchpad_path.exists():
        scratchpad_content = scratchpad_path.read_text()

    # Read existing goal slugs from DB (source of truth)
    from taskos.services.goal_service import get_all_goals
    existing_slugs = [g["slug"] for g in get_all_goals()]

    # Regex pre-filter for explicit intent
    raw_intent_lines = extract_intent_lines(scratchpad_content)
    intent_lines = _filter_existing(raw_intent_lines, existing_slugs)

    # Build MUST-INCLUDE section if there are intent lines
    must_include = ""
    if intent_lines:
        items = "\n".join(
            f"  - [{il['date']}] \"{il['line']}\" (signal: {il['signal']})"
            for il in intent_lines
        )
        must_include = f"""
**MUST-INCLUDE — these lines contain explicit intent and MUST each appear as a suggestion:**
{items}
Each of the above lines expresses clear intent and MUST be included in your output, even if it only appears on a single date.
"""

    prompt = f"""You are a goal detector. Analyze the scratchpad entries below and identify potential goals.

**Signals to look for (in priority order):**
- Explicit intent: "I want to...", "Goal:", "I need to...", "I should...", or imperative verbs like "Build", "Create", "Launch", "Ship" at the start of a line. A single entry with strong intent is just as valid as a recurring theme.
- Same theme mentioned across 2+ date entries
- Multiple related bullets that form a coherent objective
- Recurring topics that suggest an unspoken goal
{must_include}
**Already existing goals (do NOT suggest duplicates):**
{json.dumps(existing_slugs)}

**Scratchpad entries:**
```
{scratchpad_content}
```

**Output ONLY a JSON array** (no other text) with this schema:
```json
[
  {{
    "title": "Human-readable goal title",
    "slug": "url-safe-slug",
    "rationale": "Why this seems like a goal (which entries, what signals)",
    "confidence": 0.85,
    "source_dates": ["2026-02-20", "2026-02-22"],
    "suggested_tags": ["tag1", "tag2"]
  }}
]
```

If no goals are detected, output an empty array: []
"""

    return prompt, intent_lines


def parse_detector_output(stdout: str) -> list[dict]:
    """Parse Claude Code stdout into goal suggestions.

    Extracts JSON from stdout, handling potential non-JSON prefix/suffix.
    """
    stdout = stdout.strip()

    # Try direct parse first
    try:
        result = json.loads(stdout)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from markdown code block or mixed output
    json_match = re.search(r'\[[\s\S]*\]', stdout)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []
