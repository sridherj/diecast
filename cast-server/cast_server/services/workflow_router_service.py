"""Workflow router — pure resolution logic + one idempotent recorder.

No LLM, no subprocess, no re-classification. ``resolve`` is a PURE + TOTAL function
of the *persisted* family (it takes the family as an argument and never touches a
classifier), so any caller in any phase gets the same answer for free — this is where
FR-016 (phase-agnosticism) and SC-005 (byte-stability) are *preserved*, not built.
``record_routing_decision`` is the ONE writer of the goal routing columns.

The ``goal.yaml`` mirror is best-effort: the DB is authoritative, and a missing
``goal.yaml`` is logged, not raised (Decision D5).

Module shape mirrors ``orchestration_service.py`` (docstring contract, frozen dataclass
result, CLI hook); the write path uses ``goal_service.py``'s DB pattern
(``get_connection(db_path)``, try/finally close) — structure from one precedent,
persistence from the other.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cast_server.config import GOALS_DIR, WORKFLOW_FAMILIES, WORKFLOW_REGISTRY
from cast_server.db.connection import get_connection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowHandle:
    """The resolved downstream-workflow handle for a goal's family.

    ``status`` is one of "implemented" | "stub" | "unmatched" | "needs-classification".
    The two non-routable statuses ("unmatched", "needs-classification") are *returned
    and announced*, never persisted.
    """

    family: str | None
    status: str
    steps: tuple[str, ...] = ()
    pipeline_ref: str | None = None
    message: str = ""


def resolve(family: str | None) -> WorkflowHandle:
    """Resolve a persisted family to a WorkflowHandle. PURE + TOTAL — no DB, no LLM.

    Total over every input: the 9 registered families, ``None``, and any unknown
    string all return a real ``WorkflowHandle`` (0 exceptions, 0 ``None`` returns).
    ``unmatched`` is a Special Case that *announces itself*, never a silent Null Object.

    Note: ``resolve`` deliberately has no ``db_path`` parameter — its purity is an
    invariant asserted by shape in the tests.
    """
    if family is None:
        return WorkflowHandle(
            None,
            "needs-classification",
            message="Goal not yet classified — run /cast-refine-requirements first; "
            "the router never guesses.",
        )
    entry = WORKFLOW_REGISTRY.get(family)
    if entry is None:
        return WorkflowHandle(
            family,
            "unmatched",
            message=f"No pipeline registered for '{family}' — registry knows: "
            f"{sorted(WORKFLOW_FAMILIES)}.",
        )
    return WorkflowHandle(
        family,
        entry["status"],
        steps=tuple(entry["steps"]),
        pipeline_ref=entry.get("pipeline_ref"),
        message=f"Routed to the {family} workflow ({entry['status']}).",
    )


def record_routing_decision(
    slug: str,
    family: str,
    handle: WorkflowHandle,
    goals_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict:
    """Persist a routing decision on the goal — the ONLY writer of routing columns.

    House DB pattern (``goal_service.py``): ``get_connection(db_path)`` + try/finally
    close. Idempotent: re-recording the same ``{family}:{status}`` is a no-op that
    leaves ``routed_at`` untouched. Mirrors the stamp to ``goal.yaml`` best-effort —
    the DB is authoritative and a missing yaml is logged, not raised (Decision D5).

    Only routable handles are ever recorded: ``family`` must be a known
    ``WORKFLOW_FAMILIES`` member and ``handle.status`` must be "stub" or "implemented";
    anything else (``unmatched``/``needs-classification``) raises ``ValueError``.

    Returns ``{"recorded", "changed", "previous_family", "routing_handle"[, "routed_at"]}``.
    ``changed`` is True only when a *prior* family existed and differed (first-ever
    routing → ``changed: False``, ``previous_family: None``).
    """
    if family not in WORKFLOW_FAMILIES or handle.status not in ("stub", "implemented"):
        raise ValueError(
            f"Refusing to record non-routable handle: "
            f"family={family!r} status={handle.status!r}"
        )

    new_handle = f"{family}:{handle.status}"
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT workflow_family, routing_handle FROM goals WHERE slug = ?",
            (slug,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown goal slug: {slug!r}")
        prior_family = row["workflow_family"]
        if prior_family == family and row["routing_handle"] == new_handle:
            return {
                "recorded": False,
                "changed": False,
                "previous_family": prior_family,
                "routing_handle": new_handle,
            }
        routed_at = _utc_now_iso()
        conn.execute(
            "UPDATE goals SET workflow_family=?, routing_handle=?, routed_at=? WHERE slug=?",
            (family, new_handle, routed_at, slug),
        )
        conn.commit()
    finally:
        conn.close()

    # Best-effort goal.yaml mirror — DB is authoritative; a missing file is logged,
    # not raised (Decision D5). Same resolve-dir path update_status uses, so
    # externally-routed goals render correctly.
    _mirror_to_goal_yaml(slug, family, new_handle, routed_at, goals_dir, db_path)

    return {
        "recorded": True,
        "changed": prior_family is not None and prior_family != family,
        "previous_family": prior_family,
        "routing_handle": new_handle,
        "routed_at": routed_at,
    }


def _utc_now_iso() -> str:
    """ISO-8601 UTC timestamp for the ``routed_at`` stamp."""
    return datetime.now(timezone.utc).isoformat()


def _mirror_to_goal_yaml(
    slug: str,
    family: str,
    routing_handle: str,
    routed_at: str,
    goals_dir: Path | None,
    db_path: Path | None,
) -> None:
    """Best-effort write of the routing stamp into goal.yaml (DB stays authoritative).

    Resolves the goal directory the same way ``goal_service.update_status`` does (honors
    external project routing). A missing/unreadable goal.yaml is logged by
    ``_update_goal_yaml_fields``, never raised.
    """
    # Imported lazily to keep the module's import surface minimal and to make the
    # dependency on goal_service explicit at the one call site that needs it.
    from cast_server.services import goal_service

    goals_dir = goals_dir or GOALS_DIR
    goal = goal_service.get_goal(slug, db_path)
    goal_dir = goal_service._resolve_goal_dir(goal, slug, goals_dir)
    goal_service._update_goal_yaml_fields(
        goal_dir,
        {
            "workflow_family": family,
            "routing_handle": routing_handle,
            "routed_at": routed_at,
        },
    )


def _cli_resolve(family: str) -> None:
    """CLI: resolve a family and print the handle JSON."""
    handle = resolve(None if family == "None" else family)
    print(json.dumps(asdict(handle), indent=2))


def _cli_route(slug: str, family: str | None) -> None:
    """CLI: resolve-from-DB and (when family given) record the decision.

    A server-down escape hatch / test aid; agents use the HTTP door (sp3).
    """
    from cast_server.services import goal_service

    if family is None:
        goal = goal_service.get_goal(slug)
        family = goal["workflow_family"] if goal else None
    handle = resolve(family)
    out = {"handle": asdict(handle)}
    if handle.status in ("stub", "implemented"):
        out["recording"] = record_routing_decision(slug, family, handle)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m cast_server.services.workflow_router_service <command> [args]")
        print("Commands: resolve <family>, route <slug> [family]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "resolve":
        if len(sys.argv) < 3:
            print("Usage: resolve <family>", file=sys.stderr)
            sys.exit(1)
        _cli_resolve(sys.argv[2])
    elif command == "route":
        if len(sys.argv) < 3:
            print("Usage: route <slug> [family]", file=sys.stderr)
            sys.exit(1)
        _cli_route(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
