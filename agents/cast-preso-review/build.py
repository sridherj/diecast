"""Build human-review HTML for the presentation pipeline (P1: edit + decision modes).

CLI entry point for the ``cast-preso-review`` agent. This is a deterministic
``python-script`` agent per ``agents/agent-design-guide/SKILL.md`` §1: it reads
source files from a goal directory, renders slide data, and writes a
self-contained ``review.html``. No LLM reasoning happens here.

Sub-phase 1a ships the scaffold only: no renderers are registered, so any
invocation with real source content exits with a clear "no renderable content"
message. Sub-phases 1b (narrative + what) and 1c (decisions) wire renderers in
via ``RENDERER_REGISTRY``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = Path(__file__).resolve().parent


@dataclass
class Slide:
    id: str
    title: str
    outcome: str | None
    source_path: str
    mode: str                           # "edit" | "decision"
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SidebarEntry:
    slide_id: str
    label: str
    summary: str | None
    group: str | None = None            # e.g., "Open questions"


@dataclass
class BuildResult:
    mode: str
    stage: str
    slide_count: int
    source_files: list[str]
    source_hash: str


# Registry populated by renderer modules (1b, 1c). Each entry:
#   mode_key -> callable(source_dir: Path, stage: str | None) -> tuple[list[Slide], list[SidebarEntry], BuildResult]
RENDERER_REGISTRY: dict[str, Callable[..., tuple[list[Slide], list[SidebarEntry], BuildResult]]] = {}


def register_renderer(mode_key: str, fn: Callable) -> None:
    """Called by each renderer module at import time."""
    RENDERER_REGISTRY[mode_key] = fn


def resolve_goal_dir(goal_slug: str, source_dir: str | None) -> Path:
    if source_dir:
        p = Path(source_dir).resolve()
        if not p.exists():
            raise SystemExit(f"--source-dir does not exist: {p}")
        return p
    candidate = REPO_ROOT / "cast" / "goals" / goal_slug
    if not candidate.exists():
        raise SystemExit(f"goal dir not found: {candidate}")
    return candidate


def detect_mode(goal_dir: Path, forced_stage: str | None) -> str:
    """Return a mode_key. 1a ships an empty registry; 1b/1c register modes."""
    if forced_stage:
        key = f"{forced_stage}"
        if key not in RENDERER_REGISTRY:
            raise SystemExit(
                f"--stage={forced_stage} requested but no renderer is registered. "
                f"Registered modes: {sorted(RENDERER_REGISTRY)}"
            )
        return key
    # Auto-detection order: narrative → what → decisions. See _shared_context.md.
    if (goal_dir / "narrative.collab.md").exists() and "narrative" in RENDERER_REGISTRY:
        return "narrative"
    if (goal_dir / "what").is_dir() and "what" in RENDERER_REGISTRY:
        return "what"
    if (goal_dir / "decisions").is_dir() and "decisions" in RENDERER_REGISTRY:
        return "decisions"
    raise SystemExit(
        "no renderable content detected in source dir, and no --stage override given.\n"
        f"registered modes: {sorted(RENDERER_REGISTRY) or '(none — 1a scaffold only)'}"
    )


def compute_source_hash(files: list[Path]) -> str:
    h = hashlib.sha1()
    for p in sorted(files):
        h.update(p.name.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:10]


def inline_assets() -> tuple[str, str]:
    css = (AGENT_DIR / "static" / "review.css").read_text(encoding="utf-8")
    js = (AGENT_DIR / "static" / "review.js").read_text(encoding="utf-8")
    return css, js


def render_html(slides: list[Slide], sidebar: list[SidebarEntry], meta: dict) -> str:
    template = (AGENT_DIR / "template.html").read_text(encoding="utf-8")
    css, js = inline_assets()
    # Deterministic JSON — sort keys, tight separators, no whitespace churn.
    slides_json = json.dumps([asdict(s) for s in slides], sort_keys=True, separators=(",", ":"))
    sidebar_json = json.dumps([asdict(e) for e in sidebar], sort_keys=True, separators=(",", ":"))
    meta_json = json.dumps(meta, sort_keys=True, separators=(",", ":"))
    return (
        template
        .replace("{{CSS}}", css)
        .replace("{{JS}}", js)
        .replace("{{SLIDES_JSON}}", slides_json)
        .replace("{{SIDEBAR_JSON}}", sidebar_json)
        .replace("{{META}}", meta_json)
    )


def write_run_log(result: BuildResult, output_path: Path) -> None:
    summary = [
        "# Latest run",
        "",
        f"- mode: {result.mode}",
        f"- stage: {result.stage}",
        f"- slide count: {result.slide_count}",
        f"- source hash: {result.source_hash}",
        f"- output: {output_path}",
        "- sources:",
        *[f"  - {s}" for s in result.source_files],
        "",
    ]
    (AGENT_DIR / "runs" / "latest.md").write_text("\n".join(summary), encoding="utf-8")


def build(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(prog="cast-preso-review")
    parser.add_argument("goal_slug")
    parser.add_argument("--stage", choices=["narrative", "what", "decisions"], default=None)
    parser.add_argument("--source-dir", default=None)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="default: <goal_dir>/presentation/",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="After building, start a local server so export POSTs land in the goal dir.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --serve. 0 = OS-picked ephemeral port.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the browser automatically when --serve is used.",
    )
    args = parser.parse_args(argv)

    # Eagerly import renderer modules so they can register themselves.
    # 1a ships zero renderers. 1b/1c add imports to _import_renderers.
    _import_renderers()

    goal_dir = resolve_goal_dir(args.goal_slug, args.source_dir)
    mode_key = detect_mode(goal_dir, args.stage)
    slides, sidebar, result = RENDERER_REGISTRY[mode_key](goal_dir, args.stage)
    slides, sidebar, result = maybe_fold_decisions(goal_dir, mode_key, slides, sidebar, result)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else goal_dir / "presentation"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "review.html"

    meta = {
        "goal_slug": args.goal_slug,
        "mode": result.mode,
        "stage": result.stage,
        "source_hash": result.source_hash,
        "storage_key_prefix": f"{result.stage}-{args.goal_slug}-{result.source_hash}",
    }
    output_path.write_text(render_html(slides, sidebar, meta), encoding="utf-8")
    write_run_log(result, output_path)
    print(f"wrote {output_path}")

    if args.serve:
        # Local import: keeps the core build path deps-free.
        import server  # noqa: PLC0415

        server.run_foreground(
            output_dir=output_path.parent,
            goal_dir=goal_dir,
            stage=result.stage,
            port=args.port,
            open_browser=not args.no_open,
        )

    return output_path


def maybe_fold_decisions(
    goal_dir: Path,
    primary_mode: str,
    slides: list[Slide],
    sidebar: list[SidebarEntry],
    result: BuildResult,
) -> tuple[list[Slide], list[SidebarEntry], BuildResult]:
    """If an edit-mode build also has a ``decisions/`` dir, fold those slides in.

    Decision slides are appended under a sidebar group labelled "Open
    questions". The primary ``BuildResult`` is preserved; a ``folded_groups``
    note is not added here because the client reads the group field directly
    off each sidebar entry.

    When the primary mode is already ``decisions``, returns the inputs
    unchanged. Same when no ``decisions/`` dir exists.
    """
    if primary_mode == "decisions":
        return slides, sidebar, result
    decisions_dir = goal_dir / "decisions"
    if not decisions_dir.is_dir():
        return slides, sidebar, result
    if "decisions" not in RENDERER_REGISTRY:
        return slides, sidebar, result
    # Use the decisions renderer in fold mode so its sidebar entries already
    # carry the "Open questions" group label.
    from renderers import decisions as decisions_module  # local import to avoid cycles

    merged_slides, merged_sidebar = decisions_module.fold_into(goal_dir, slides, sidebar)
    fold_result = BuildResult(
        mode=result.mode,
        stage=result.stage,
        slide_count=len(merged_slides),
        source_files=result.source_files,
        source_hash=result.source_hash,
    )
    return merged_slides, merged_sidebar, fold_result


def _import_renderers() -> None:
    """Import renderer modules so they self-register via ``register_renderer``.

    1a shipped an empty body. 1b adds narrative + what; 1c appends decisions.
    """
    # 1b — edit mode
    from renderers import narrative  # noqa: F401
    from renderers import what       # noqa: F401
    # 1c — decision mode
    from renderers import decisions  # noqa: F401


def main() -> None:
    build(sys.argv[1:])


if __name__ == "__main__":
    # When run as a script (``python build.py ...``), Python loads this file
    # as ``__main__``. Any ``from build import ...`` done by a renderer then
    # reloads this file under the name ``build``, producing a second copy of
    # ``RENDERER_REGISTRY``. Re-dispatching through the named module makes
    # sure registrations and dispatch use the same registry.
    import build as _build  # noqa: PLC0415

    _build.main()
