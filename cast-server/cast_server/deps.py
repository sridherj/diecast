"""Shared dependencies — breaks circular imports between app.py and routes."""

from datetime import datetime, timezone

from fastapi.templating import Jinja2Templates

from cast_server.config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _ensure_aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC (backward compat with existing DB data)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _relative_time(iso_str: str | None) -> str:
    """Convert ISO timestamp to relative string like '2m ago', '3h ago'."""
    if not iso_str:
        return ""
    try:
        dt = _ensure_aware(datetime.fromisoformat(iso_str))
    except (ValueError, TypeError):
        return ""
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _duration(start_iso: str | None, end_iso: str | None) -> str:
    """Calculate duration between two ISO timestamps, e.g. '3m 12s'."""
    if not start_iso:
        return ""
    try:
        start = _ensure_aware(datetime.fromisoformat(start_iso))
    except (ValueError, TypeError):
        return ""
    if end_iso:
        try:
            end = _ensure_aware(datetime.fromisoformat(end_iso))
        except (ValueError, TypeError):
            end = datetime.now(timezone.utc)
    else:
        end = datetime.now(timezone.utc)
    seconds = int((end - start).total_seconds())
    if seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def _format_tokens(n: int | None) -> str:
    """Format token count: None→'', 500→'500', 1234→'1.2K', 1234567→'1.2M'."""
    if n is None:
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _format_cost(usd: float | None) -> str:
    """Format USD cost: None→'', 0.0523→'$0.05', 1.234→'$1.23'."""
    if usd is None:
        return ""
    return f"${usd:.2f}"


templates.env.globals["relative_time"] = _relative_time
templates.env.globals["duration"] = _duration
templates.env.globals["format_tokens"] = _format_tokens
templates.env.globals["format_cost"] = _format_cost
