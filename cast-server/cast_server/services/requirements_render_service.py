"""Requirements HTML render service (Phase 3a / WP-E).

Wires the *pure* renderer (`cast_server.requirements_render.renderer.render_requirements`)
into the running app. This module owns ALL file/DB I/O — the renderer stays a pure,
deterministic function over `ParsedRequirements`.

The generated `refined_requirements.html` is an AUTO-GENERATED render of canonical state
(same write class as `tasks.md` / `goal.yaml`), NOT an authored artifact. It is read-only,
self-contained, and never edits the canonical `.collab.md` (FR-007). Regeneration is lazy:
the file is rewritten only when the source content hash changes.

**Role demotion (refine-requirements-v3 Phase 3c).** The deterministic `render_requirements()`
substrate this module wires up is no longer the primary render path — the WHAT→HOW maker
pipeline in `render_job_service` is. `rerender_requirements_html` is now the **fallback branch**,
served **only on a literal no-output failure** (crash / timeout / nothing extractable). Its
*behavior* is unchanged (atomic write + AUTO-GENERATED header + source-hash cache); only its role
moved. This module also gains the **publish seam** (`publish_maker_html`) the maker pipeline uses
to land clean and flagged renders through the identical write envelope, plus a `served-by:` stamp
3d turns into a reader-visible badge.
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cast_server.config import GOALS_DIR
from cast_server.requirements_render import is_stub, parse_requirements_file
from cast_server.requirements_render.hashing import content_hash
from cast_server.requirements_render.renderer import render_requirements
from cast_server.services import goal_service, requirement_version_service

logger = logging.getLogger(__name__)

_AUTO_GENERATED_HEADER = (
    "<!-- AUTO-GENERATED: Read-only render of refined_requirements.collab.md. Do not edit. -->"
)
_SOURCE_HASH_PREFIX = "<!-- source-hash: "
_SOURCE_HASH_SUFFIX = " -->"
# served-by stamp (3c). Sits beside source-hash in the AUTO-GENERATED header so 3d can derive a
# reader-visible badge ("needs review" for structural_violation) without re-running any gate.
# Allowed values: 'maker' (clean maker render), 'structural_violation' (flagged best-attempt), or
# 'fallback' (deterministic substrate). The deterministic writer below stays UNstamped — only the
# maker publish seam emits this line, so the v2 cache format is unchanged on the fallback path.
_SERVED_BY_PREFIX = "<!-- served-by: "
_SERVED_BY_SUFFIX = " -->"
_VALID_SERVED_BY = frozenset({"maker", "structural_violation", "fallback"})

# human-review stamp (4a-2). The served artifact is the SINGLE source of truth for the flag, exactly
# as the embedded source-hash is for readiness ("the artifact IS the state"). The status poll reads
# the flag off this stamp (the artifact it already stats for `ready`) — never a per-request
# render_jobs query (A2/P1). A clean publish omits both lines (human_review=0 → no churn vs v2).
_HUMAN_REVIEW_PREFIX = "<!-- human-review: "
_HUMAN_REVIEW_SUFFIX = " -->"
_REVIEW_REASON_PREFIX = "<!-- review-reason: "
_REVIEW_REASON_SUFFIX = " -->"


def _resolve_goal_dir(goal_slug: str, goals_dir: Path, db_path) -> Path:
    """Return the authoritative goal directory.

    Mirrors `task_service`: a routed goal's DB ``folder_path`` wins over the default
    ``goals_dir / slug`` when it exists on disk; otherwise fall back to the default.
    """
    goal = goal_service.get_goal(goal_slug, db_path)
    fp = goal.get("folder_path") if goal else None
    if fp and Path(fp).exists():
        return Path(fp)
    return goals_dir / goal_slug


def _embedded_source_hash(html: str) -> str | None:
    """Extract the `<!-- source-hash: H -->` value embedded in an existing render, or None."""
    for line in html.splitlines():
        stripped = line.strip()
        if stripped.startswith(_SOURCE_HASH_PREFIX) and stripped.endswith(_SOURCE_HASH_SUFFIX):
            return stripped[len(_SOURCE_HASH_PREFIX):-len(_SOURCE_HASH_SUFFIX)].strip()
    return None


def _embedded_served_by(html: str) -> str | None:
    """Extract the `<!-- served-by: V -->` stamp from an existing render, or None.

    Only the maker publish seam (`publish_maker_html`) emits this line — the deterministic
    fallback writer leaves it absent. 3d's route turns ``structural_violation`` into a
    reader-visible "needs review" badge; ``maker`` / ``fallback`` / a missing stamp carry no badge.
    """
    for line in html.splitlines():
        stripped = line.strip()
        if stripped.startswith(_SERVED_BY_PREFIX) and stripped.endswith(_SERVED_BY_SUFFIX):
            return stripped[len(_SERVED_BY_PREFIX):-len(_SERVED_BY_SUFFIX)].strip()
    return None


def _embedded_human_review(html: str) -> bool:
    """Whether the served artifact carries a ``<!-- human-review: 1 -->`` stamp (4a-2).

    The status-poll read path (A2/P1): the flag is read off the artifact, never from the latest
    render_jobs row — a newer ``running`` regen for the same hash defaults its row's human_review to
    0, and a latest-row read would silently clear the flag of the *prior flagged* page actually
    being served. A clean publish omits the stamp entirely → ``False``."""
    for line in html.splitlines():
        stripped = line.strip()
        if stripped.startswith(_HUMAN_REVIEW_PREFIX) and stripped.endswith(_HUMAN_REVIEW_SUFFIX):
            return stripped[len(_HUMAN_REVIEW_PREFIX):-len(_HUMAN_REVIEW_SUFFIX)].strip() == "1"
    return False


def _atomic_write(target: Path, text: str) -> None:
    """Write `text` to `target` atomically (tmp file in the same dir + `os.replace`).

    A crash mid-write leaves either the old file or the new file — never a truncated one.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".", suffix=".html.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        # Best-effort cleanup of the temp file on any failure; never leave it behind.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def rerender_requirements_html(
    goal_slug: str, *, goals_dir: Path | None = None, db_path: Path | None = None
) -> Path | None:
    """Lazily (re)generate `goals/{slug}/refined_requirements.html` from its `.collab.md`.

    Reads the canonical `.collab.md` only — never writes it (FR-007). The `.html` is
    rewritten only when the source content hash differs from the embedded `source-hash`;
    on a fresh hash the existing file is returned byte-identical (no-op write).

    Args:
        goal_slug: the goal whose requirements to render.
        goals_dir: optional override of the goals root (test injection).
        db_path: optional override of the DB path (test injection).

    Returns:
        The path to the generated `.html`, or ``None`` if the source `.collab.md` is absent.
    """
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = _resolve_goal_dir(goal_slug, goals_dir, db_path)
    source_path = goal_dir / "refined_requirements.collab.md"
    if not source_path.exists():
        return None

    parsed = parse_requirements_file(source_path)
    h = content_hash(parsed.source_text)

    html_path = goal_dir / "refined_requirements.html"

    # Lazy staleness check: fresh hash → return the existing file untouched (byte-identical).
    if html_path.exists():
        existing = html_path.read_text(encoding="utf-8")
        if _embedded_source_hash(existing) == h:
            return html_path

    current = requirement_version_service.get_current(goal_slug, db_path=db_path)
    version = current.get("version") if current else None
    # Phase 4 (sp4a): the diff toggle renders only when a prior version exists to compare.
    version_count = len(requirement_version_service.list_versions(goal_slug, db_path=db_path))

    result = render_requirements(
        parsed, version=version, goal_slug=goal_slug, version_count=version_count
    )

    document = (
        f"{_AUTO_GENERATED_HEADER}\n"
        f"{_SOURCE_HASH_PREFIX}{h}{_SOURCE_HASH_SUFFIX}\n"
        f"{result.html}"
    )
    _atomic_write(html_path, document)
    return html_path


def current_source_hash(
    goal_slug: str, *, goals_dir: Path | None = None, db_path: Path | None = None
) -> str | None:
    """Return the content hash of the goal's canonical `.collab.md` *right now*, or ``None`` if
    the source is absent.

    The maker pipeline's compare-and-publish step re-reads this at publish time: if the source
    moved while a job was running, the job is marked ``superseded`` and writes nothing (the next
    view starts a fresh job). Reads the source only — never writes it (FR-007).
    """
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = _resolve_goal_dir(goal_slug, goals_dir, db_path)
    source_path = goal_dir / "refined_requirements.collab.md"
    if not source_path.exists():
        return None
    parsed = parse_requirements_file(source_path)
    return content_hash(parsed.source_text)


def publish_maker_html(
    goal_slug: str,
    html: str,
    *,
    source_hash: str,
    served_by: str,
    human_review: bool = False,
    review_reason: str | None = None,
    goals_dir: Path | None = None,
    db_path: Path | None = None,
) -> Path:
    """Publish maker-produced HTML through the SAME atomic-write + AUTO-GENERATED header +
    source-hash cache envelope as the deterministic writer (FR-005 / SC-005), adding a
    ``served-by:`` stamp (+ the 4a-2 ``human-review`` / ``review-reason`` stamps) beside the
    source-hash.

    The publish seam (3c) the maker pipeline lands renders through, reused for the quality-loop
    terminal states (4a-2):

    - a clean maker render that passes ``gate_html`` AND the checker → ``served_by="maker"``,
      ``human_review=False`` (no flag stamp);
    - a flagged best-attempt at a non-clean terminal → ``human_review=True`` with the ``review_reason``
      the loop derived (``non_convergent`` / ``checker_unavailable`` / ``structural_degradation`` /
      ``structural_violation``). ``served_by="maker"`` for a structurally-VALID served attempt,
      ``served_by="structural_violation"`` for a structurally-BROKEN one (the owner OVERRIDE: surface
      the degraded render with a stamp, never silently swap in the deterministic page).

    The artifact stays the single source of truth for BOTH readiness (embedded source-hash) AND the
    human-review flag (A2). A clean publish omits the human-review/review-reason lines, so the v2
    cache format is unchanged on the happy path. Writes ``html`` to
    ``goals/{slug}/refined_requirements.html`` atomically. Never touches the `.collab.md` (FR-007).
    """
    if served_by not in _VALID_SERVED_BY:
        raise ValueError(
            f"served_by must be one of {sorted(_VALID_SERVED_BY)}, got {served_by!r}"
        )
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = _resolve_goal_dir(goal_slug, goals_dir, db_path)
    html_path = goal_dir / "refined_requirements.html"

    lines = [
        _AUTO_GENERATED_HEADER,
        f"{_SOURCE_HASH_PREFIX}{source_hash}{_SOURCE_HASH_SUFFIX}",
        f"{_SERVED_BY_PREFIX}{served_by}{_SERVED_BY_SUFFIX}",
    ]
    if human_review:
        lines.append(f"{_HUMAN_REVIEW_PREFIX}1{_HUMAN_REVIEW_SUFFIX}")
        if review_reason:
            lines.append(f"{_REVIEW_REASON_PREFIX}{review_reason}{_REVIEW_REASON_SUFFIX}")
    document = "\n".join(lines) + f"\n{html}"
    _atomic_write(html_path, document)
    return html_path


@dataclass(frozen=True)
class RenderResolution:
    """The read-side classification of `GET /goals/{slug}/render` (3d).

    The route is a thin dispatch over this. ``state`` is the single discriminator and
    **readiness is derived purely from the artifact** — the embedded ``source-hash`` equals the
    current source hash — so maker, flagged, AND fallback publishes all resolve to ``ready`` with
    zero extra state (no cache-vs-table divergence is possible).

    Fields:
      * ``state`` — one of ``ready`` | ``stub`` | ``missing`` | ``generating``.
      * ``path`` — the servable artifact: the fresh ``.html`` when ``ready``; the **stale** ``.html``
        when ``generating`` and a prior render exists (the stale-render-with-banner flavor); ``None``
        when ``generating`` with no prior render (the dedicated generating page) and for
        ``missing`` / ``stub`` (the route renders those itself).
      * ``source_hash`` — the goal's current ``.collab.md`` content hash (``None`` only for
        ``missing``).
      * ``served_by`` — the artifact's ``served-by`` stamp when ``ready`` (drives the
        ``structural_violation`` "needs review" badge); ``None`` otherwise.
      * ``human_review`` — the artifact's ``human-review`` flag stamp when ``ready`` (4a-2; the
        status endpoint exposes it, read from the artifact NOT a render_jobs row); ``False`` otherwise.
    """

    state: str
    path: Path | None
    source_hash: str | None
    served_by: str | None
    human_review: bool = False


def resolve_render(
    goal_slug: str, *, goals_dir: Path | None = None, db_path: Path | None = None
) -> RenderResolution:
    """Classify the current render state for ``goal_slug`` WITHOUT starting a job or writing a file.

    Pure read over the source ``.collab.md`` and the cached ``.html`` (FR-007 — never writes the
    source). The route uses this to decide whether to serve a fresh file (``ready``), the
    prompt-to-begin / deterministic path (``missing`` / ``stub``), or a live generating state
    (``generating``) — and only on ``generating`` does it ask the job service to ensure a job. A
    fresh-hash view therefore starts **no** job, the load-bearing "cached views stay instant"
    property.
    """
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = _resolve_goal_dir(goal_slug, goals_dir, db_path)
    source_path = goal_dir / "refined_requirements.collab.md"
    if not source_path.exists():
        return RenderResolution(state="missing", path=None, source_hash=None, served_by=None)

    parsed = parse_requirements_file(source_path)
    h = content_hash(parsed.source_text)

    # A stub is a legitimate product state served by the deterministic prompt-to-begin render; the
    # maker is never invoked for it (mirrors render_job_service's stub short-circuit). Classified
    # BEFORE the freshness check so a stub never resolves to ``generating``.
    if is_stub(parsed):
        return RenderResolution(state="stub", path=None, source_hash=h, served_by=None)

    html_path = goal_dir / "refined_requirements.html"
    if html_path.exists():
        existing = html_path.read_text(encoding="utf-8")
        if _embedded_source_hash(existing) == h:
            # Fresh artifact — ready regardless of who published it (maker/flagged/fallback). The
            # human-review flag is read off THIS artifact (A2/P1) — the same bytes already read for
            # the freshness check, so the poll never gains a render_jobs round-trip.
            return RenderResolution(
                state="ready", path=html_path, source_hash=h,
                served_by=_embedded_served_by(existing),
                human_review=_embedded_human_review(existing),
            )
        # A stale render exists → generating-with-banner (serve the old one, regenerate behind it).
        return RenderResolution(state="generating", path=html_path, source_hash=h, served_by=None)

    # No render yet → the dedicated generating page.
    return RenderResolution(state="generating", path=None, source_hash=h, served_by=None)
