"""eval_maker_pipeline_e2e — sub-phase 3e two-family END-TO-END gate (real `claude -p` maker).

This is the Phase-3 phase gate, run as an **eval harness** (the `eval_` prefix excludes it from
default pytest, like `eval_render_checker.py`): it invokes the REAL `cast-requirements-what` →
`cast-requirements-how` `claude -p` subagents through the production `request_render` orchestrator —
no fakes — and asserts the maker-happy-path contract this sub-phase records into the spec.

Run it directly (NOT via the default `pytest` collection):

    uv run python tests/eval_maker_pipeline_e2e.py

It renders TWO real, classified families through the pipeline and verifies:
  * both pages pass `maker_gate.check_html` (every canonical id mapped, none invented);
  * the two pages are **visibly distinct** — their section-heading sets differ and contain NO
    US/FR/SC slot names (family-appropriate communication headings);
  * each render is a single self-contained file (one `<!doctype html>`, no external fetches beyond
    the FR-028-sanctioned local scripts);
  * the canonical `.collab.md` is NEVER written by the maker (`--tools ""` made it structural);
  * the generating→ready swap converges (a `wait=False` request reports `generating`, and the
    finished artifact's embedded `source-hash` then matches → the status derivation reports `ready`).

Outputs (HTML + check_html reports + a JSON summary) are written under a run dir and echoed, so the
sweep is auditable and the two renders can be eyeballed side-by-side (the non-blocking human
carry-forward — autonomous runs cannot drive a browser).
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

CAST_SERVER_DIR = Path(__file__).resolve().parent.parent
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

REPO_ROOT = CAST_SERVER_DIR.parent

from cast_server.db.connection import get_connection, init_db  # noqa: E402
from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.maker_gate import (  # noqa: E402
    check_html,
    container_text_index,
)
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirements_render_service as rrs  # noqa: E402

# ----------------------------------------------------------------------------------------
# The two real, classified family sources (the spike-1a validated corpus).
# ----------------------------------------------------------------------------------------
FAMILIES = [
    {
        "slug": "e2e-new-initiative",
        "family": "new_initiative",
        "source": REPO_ROOT
        / "docs/goal/refine-requirements-better-rendering-v3/refined_requirements.collab.md",
    },
    {
        "slug": "e2e-bug-fix",
        "family": "bug_fix",
        "source": REPO_ROOT
        / "docs/goal/refine-requirements-better-rendering-v3/spikes/1a/fixtures/"
        "goal-card-markdown-leak.collab.md",
    },
]

_HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_SLOT_RE = re.compile(r"\b(US-?\d+|FR-?\d{2,}|SC-?\d{2,})\b")


def _headings(html: str) -> list[str]:
    out = []
    for raw in _HEADING_RE.findall(html):
        text = _TAG_RE.sub("", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            out.append(text)
    return out


def _setup_goal(tmp: Path, spec: dict) -> dict:
    """Seed a goals row + goal dir with the family source; return the run context."""
    goals_dir = tmp / "goals"
    goal_dir = goals_dir / spec["slug"]
    goal_dir.mkdir(parents=True, exist_ok=True)
    source_text = spec["source"].read_text(encoding="utf-8")
    (goal_dir / "refined_requirements.collab.md").write_text(source_text, encoding="utf-8")

    conn = get_connection(tmp / "cast.db")
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path, workflow_family) "
            "VALUES (?, ?, ?, ?)",
            (spec["slug"], spec["family"], str(goal_dir), spec["family"]),
        )
        conn.commit()
    finally:
        conn.close()

    parsed = parse_requirements(source_text)
    return {
        "spec": spec,
        "goals_dir": goals_dir,
        "goal_dir": goal_dir,
        "parsed": parsed,
        "source_hash": parsed.content_hash,
    }


def _run_one(tmp: Path, ctx: dict, out_dir: Path) -> dict:
    spec = ctx["spec"]
    db_path = tmp / "cast.db"
    runner = svc.ProductionAgentRunner(
        Path(svc.config.RENDER_JOBS_DIR) / spec["slug"] / ctx["source_hash"][:12]
    )

    # 1) generating-state probe: a wait=False request returns `generating` immediately.
    probe = svc.request_render(
        spec["slug"], runner=runner, goals_dir=ctx["goals_dir"], db_path=db_path, wait=False
    )

    # 2) the real, blocking pipeline run (joins the same single-flight job).
    result = svc.request_render(
        spec["slug"], runner=runner, goals_dir=ctx["goals_dir"], db_path=db_path, wait=True
    )

    html_path = ctx["goal_dir"] / "refined_requirements.html"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

    # check_html gate against the parsed source (every canonical id mapped, none invented).
    report = check_html(html, ctx["parsed"])

    # Readiness derivation (the status endpoint's pure rule): embedded source-hash == current.
    resolution = rrs.resolve_render(
        spec["slug"], goals_dir=ctx["goals_dir"], db_path=db_path
    )

    headings = _headings(html)
    slot_headings = [h for h in headings if _SLOT_RE.search(h)]
    parsed_refs = sorted({b.ref for b in ctx["parsed"].blocks if b.ref})

    # persist artifacts for the sweep record / human eyeball.
    (out_dir / f"{spec['slug']}.html").write_text(html, encoding="utf-8")
    (out_dir / f"{spec['slug']}.check_html.json").write_text(
        json.dumps({"passed": report.passed, "violations": list(report.violations)}, indent=2),
        encoding="utf-8",
    )

    return {
        "slug": spec["slug"],
        "family": spec["family"],
        "probe_state": probe.get("state"),
        "terminal_state": result.get("state"),
        "served_by": resolution.served_by,
        "ready_state": resolution.state,
        "ready_hash_matches": resolution.source_hash == ctx["source_hash"],
        "check_html_passed": report.passed,
        "check_html_violations": list(report.violations),
        "doctype_count": html.lower().count("<!doctype html>"),
        "external_fetch_http": bool(re.search(r'src=["\']https?://', html)),
        "canonical_refs": parsed_refs,
        "n_canonical_refs": len(parsed_refs),
        "headings": headings,
        "slot_headings": slot_headings,
        "html_bytes": len(html.encode("utf-8")),
        "collab_md_unchanged": True,  # filled by the caller (compares mtime/hash)
    }


def main() -> int:
    # Optional single-family filter: `… eval_maker_pipeline_e2e.py <slug>` runs only that family
    # (used to re-confirm a stochastic structural-gate outcome without re-running the whole sweep).
    only = sys.argv[1] if len(sys.argv) > 1 else None
    families = [f for f in FAMILIES if f["slug"] == only] if only else FAMILIES

    run_dir = Path(tempfile.mkdtemp(prefix="maker-e2e-"))
    out_dir = run_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    init_db(run_dir / "cast.db")
    svc._reset_state()

    print(f"[e2e] run dir: {run_dir}")
    results = []
    for spec in families:
        ctx = _setup_goal(run_dir, spec)
        src_path = ctx["goal_dir"] / "refined_requirements.collab.md"
        before = src_path.read_bytes()
        print(f"[e2e] rendering {spec['slug']} ({spec['family']}) — real claude -p maker …")
        res = _run_one(run_dir, ctx, out_dir)
        res["collab_md_unchanged"] = src_path.read_bytes() == before
        results.append(res)
        print(
            f"[e2e]   -> served_by={res['served_by']} check_html={res['check_html_passed']} "
            f"refs={res['n_canonical_refs']} headings={len(res['headings'])} "
            f"bytes={res['html_bytes']} probe={res['probe_state']}"
        )

    # ---- single-family mode: per-family report only (no cross-family gate) ------------
    if len(results) < 2:
        r = results[0]
        print("\n[e2e] ===== SINGLE-FAMILY RESULT =====")
        print(f"[e2e]   slug={r['slug']} served_by={r['served_by']} "
              f"check_html={r['check_html_passed']} violations={r['check_html_violations']}")
        print(f"[e2e]   refs={r['n_canonical_refs']} headings={len(r['headings'])} "
              f"slot_headings={r['slot_headings']} single_file={r['doctype_count'] == 1} "
              f"collab_unchanged={r['collab_md_unchanged']} probe={r['probe_state']} "
              f"ready={r['ready_state']}")
        print(f"[e2e] artifacts: {out_dir}")
        return 0 if r["check_html_passed"] else 1

    # ---- cross-family assertions (the gate) -------------------------------------------
    a, b = results[0], results[1]
    head_a = {h.lower() for h in a["headings"]}
    head_b = {h.lower() for h in b["headings"]}
    distinct = head_a != head_b and bool(head_a ^ head_b)

    checks = {
        "both_check_html_passed": a["check_html_passed"] and b["check_html_passed"],
        "no_slot_headings": not a["slot_headings"] and not b["slot_headings"],
        "heading_sets_differ": distinct,
        "both_single_file": a["doctype_count"] == 1 and b["doctype_count"] == 1,
        "no_external_http_fetch": not a["external_fetch_http"] and not b["external_fetch_http"],
        "collab_md_never_written": a["collab_md_unchanged"] and b["collab_md_unchanged"],
        "both_generating_on_probe": a["probe_state"] == "generating"
        and b["probe_state"] == "generating",
        "both_ready_after": a["ready_state"] == "ready" and b["ready_state"] == "ready"
        and a["ready_hash_matches"] and b["ready_hash_matches"],
        "served_by_maker": a["served_by"] == "maker" and b["served_by"] == "maker",
    }
    summary = {"results": results, "checks": checks, "all_passed": all(checks.values())}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n[e2e] ===== GATE RESULT =====")
    for k, v in checks.items():
        print(f"[e2e]   {'PASS' if v else 'FAIL'}  {k}")
    print(f"[e2e] artifacts: {out_dir}")
    print(f"[e2e] ALL PASSED: {summary['all_passed']}")
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
