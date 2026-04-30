"""Agent error memory extraction, storage, and retrieval."""
import hashlib
import json
import re
import logging
from datetime import datetime, timezone
from taskos.db.connection import get_connection

logger = logging.getLogger(__name__)

# Error category patterns (order matters — first match wins)
CATEGORY_PATTERNS = [
    ("rate_limit", [r"hit your limit", r"rate limit", r"429", r"too many requests"]),
    ("timeout", [r"exceeded", r"timeout", r"deadline", r"timed out"]),
    ("external_service", [r"mcp.*(?:fail|error)", r"web.*fetch.*(?:fail|error)",
                          r"api.*error", r"connection.*refused", r"503", r"502"]),
    ("config", [r"not found", r"missing.*env", r"bad config", r"no such file",
                r"import.*error", r"module.*not found"]),
    ("logic", [r"assertion.*error", r"key.*error", r"type.*error", r"value.*error",
               r"attribute.*error", r"index.*error"]),
]

TRANSIENT_CATEGORIES = {"rate_limit", "timeout", "external_service"}
TRANSIENT_SUPPRESS_DAYS = 7


def categorize_error(error_text: str) -> str:
    """Classify error into category. Returns category string."""
    lower = error_text.lower()
    for category, patterns in CATEGORY_PATTERNS:
        if any(re.search(p, lower) for p in patterns):
            return category
    return "unknown"


def normalize_pattern(error_text: str) -> str:
    """Strip dynamic segments for stable hashing."""
    normalized = error_text
    # Strip timestamps (ISO format, various date formats)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*Z?", "<TIMESTAMP>", normalized)
    # Strip UUIDs
    normalized = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID>", normalized)
    # Strip run IDs (agent-XXXX pattern)
    normalized = re.sub(r"agent-[a-zA-Z0-9_-]+", "agent-<ID>", normalized)
    # Strip file paths with dynamic segments
    normalized = re.sub(r"/tmp/[^\s]+", "<TMPPATH>", normalized)
    # Strip line numbers
    normalized = re.sub(r"line \d+", "line <N>", normalized)
    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def compute_pattern_hash(normalized_pattern: str) -> str:
    """SHA256 hash of normalized pattern, truncated to 12 chars."""
    return hashlib.sha256(normalized_pattern.encode()).hexdigest()[:12]


def extract_and_store_error(agent_name: str, run_id: str, output_json: dict | None, error_message: str | None):
    """Extract error patterns from run output and store in error_memories table."""
    errors_to_process = []

    # Extract from output.json errors list
    if output_json and "errors" in output_json:
        for err in output_json["errors"]:
            if isinstance(err, str):
                errors_to_process.append(err)
            elif isinstance(err, dict) and "message" in err:
                errors_to_process.append(err["message"])

    # Extract from error_message
    if error_message:
        errors_to_process.append(error_message)

    if not errors_to_process:
        return  # No parseable errors

    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    for error_text in errors_to_process:
        normalized = normalize_pattern(error_text)
        pattern_hash = compute_pattern_hash(normalized)
        category = categorize_error(error_text)
        is_transient = 1 if category in TRANSIENT_CATEGORIES else 0
        suppress_days = TRANSIENT_SUPPRESS_DAYS if is_transient else None

        # Upsert on UNIQUE(agent_name, pattern_hash)
        existing = conn.execute(
            "SELECT id, occurrence_count, run_ids FROM agent_error_memories "
            "WHERE agent_name = ? AND pattern_hash = ?",
            (agent_name, pattern_hash)
        ).fetchone()

        if existing:
            mem_id, count, run_ids_json = existing
            run_ids = json.loads(run_ids_json)
            run_ids.append(run_id)

            # Escalation check
            new_count = count + 1
            resolution_status = "unresolved"
            if new_count >= 3:
                resolution_status = "escalated"
                logger.warning(
                    "ESCALATED: Agent %s error pattern recurring (%dx): %s",
                    agent_name, new_count, error_text[:100]
                )

            conn.execute(
                "UPDATE agent_error_memories SET "
                "occurrence_count = ?, last_seen = ?, run_ids = ?, resolution_status = ? "
                "WHERE id = ?",
                (new_count, now, json.dumps(run_ids), resolution_status, mem_id)
            )
        else:
            conn.execute(
                "INSERT INTO agent_error_memories "
                "(agent_name, error_pattern, pattern_hash, error_category, "
                "is_transient, first_seen, last_seen, run_ids, suppress_after_days) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (agent_name, error_text[:500], pattern_hash, category,
                 is_transient, now, now, json.dumps([run_id]), suppress_days)
            )

        conn.commit()


def get_relevant_memories(agent_name: str, limit: int = 10) -> list[dict]:
    """Retrieve active error memories for injection into agent context."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT error_pattern, error_category, occurrence_count, last_seen, resolution
        FROM agent_error_memories
        WHERE agent_name = ?
          AND inject_as_context = 1
          AND resolution_status != 'resolved'
          AND (
            is_transient = 0
            OR julianday('now') - julianday(last_seen) <= suppress_after_days
            OR occurrence_count >= 3
          )
        ORDER BY occurrence_count DESC, last_seen DESC
        LIMIT ?
    """, (agent_name, limit)).fetchall()

    return [
        {
            "pattern": row[0][:200],  # Truncate for context window
            "category": row[1],
            "occurrences": row[2],
            "last_seen": row[3],
            "resolution": row[4],
        }
        for row in rows
    ]


def should_auto_retry(agent_name: str) -> bool:
    """Check if agent has escalated error patterns (3+ occurrences).

    Returns True if auto-retry is safe (no escalated patterns).
    """
    conn = get_connection()
    escalated = conn.execute(
        "SELECT COUNT(*) FROM agent_error_memories "
        "WHERE agent_name = ? AND resolution_status = 'escalated'",
        (agent_name,)
    ).fetchone()[0]
    return escalated == 0


def resolve_memory(memory_id: int, resolution: str):
    """Mark an error memory as resolved."""
    conn = get_connection()
    conn.execute(
        "UPDATE agent_error_memories SET "
        "resolution = ?, resolution_status = 'resolved', inject_as_context = 0 "
        "WHERE id = ?",
        (resolution, memory_id)
    )
    conn.commit()
