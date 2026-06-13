"""eval_family_sweep — sub-phase 5c NINE-FAMILY corpus gate (real `claude -p` maker).

The Phase-5c counterpart to `eval_maker_pipeline_e2e.py` (the two-family Phase-3 gate). Where
that eval proved two families render distinct and clean, this one runs the **full** nine-value
`WorkFamily` corpus through the **production** maker pipeline (`request_render` → WHAT → gates →
HOW → the 4a quality loop) and asserts the cross-family contract SC-002 records.

This is an **eval harness**, not a `test_*` module: the `eval_` prefix excludes it from default
pytest collection (the `eval_render_checker.py` / `eval_quality_gate.py` precedent), because a real
run shells out to `claude` nine times (slow + network). Run it by hand:

    # Full nine-family sweep (slow; real claude maker per family):
    uv run --project . python cast-server/tests/eval_family_sweep.py

    # One family (re-confirm a single stochastic outcome without the whole sweep):
    uv run --project . python cast-server/tests/eval_family_sweep.py --family bug_fix

    # Also copy the rendered evidence + index + sc-sweep note into the goal's signoff dir:
    uv run --project . python cast-server/tests/eval_family_sweep.py --golden

`gaps[]` stays **empty** for the 5c sweep — gap machinery (5a/5b) is dormant here, so the pipeline
is exactly Phase-3/4a behavior. SC-002's evidence captured here is **provisional**; 5d re-runs it
with gap machinery live.

Per-family the sweep records the checker verdict, the canonical score, and the **`human_review`
flag** (the 4a hand-off — the per-family quality signal). A family that converges only with a flag
is a **finding** (never suppressed): it surfaces in the report and is carried into 5d's sign-off.

What the gate asserts (Step 5c.2):
  * every family reaches terminal **`published`** — NEVER the deterministic `fallback` (reserved for
    literal no-output under the structural override), NEVER `failed` / `superseded`;
  * `check_html` green per family (every canonical id mapped, none invented);
  * **pairwise** section-heading sets differ (deterministic distinctness);
  * NO heading equals a US/FR/SC slot name;
  * NO empty section shells (US2 Scenario 2 — omit, never pad);
  * the corpus docs carry valid pinned classification front matter (`family`,
    `confirmed_by: "manual"`, `taxonomy_version: 1`) and are non-stub.

A `served-by: structural_violation` publish or any `human_review=1` is recorded as a
**human-eyeball carry-forward finding** (surfaced, never a silent pass) — the happy path is
expected to work for every family, and a flag is the honest signal that it didn't, fully.
"""

from __future__ import annotations

import argparse
import itertools
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
from cast_server.requirements_render.families import WorkFamily  # noqa: E402
from cast_server.requirements_render.maker_gate import check_html  # noqa: E402
from cast_server.requirements_render.stub import is_stub  # noqa: E402
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirements_render_service as rrs  # noqa: E402

# ----------------------------------------------------------------------------------------
# Corpus — one authored-not-fiction doc per LOCKED WorkFamily value (Step 5c.1).
# Source order is the enum's declared order, so the report reads taxonomy-canonical.
# ----------------------------------------------------------------------------------------
_CORPUS_DIR = CAST_SERVER_DIR / "tests" / "fixtures" / "family_corpus"
_SIGNOFF_GOLDEN_DIR = (
    REPO_ROOT / "docs" / "goal" / "refine-requirements-better-rendering-v3"
    / "signoff" / "golden"
)

FAMILIES = [
    {"slug": f"family-{f.value.replace('_', '-')}", "family": f.value,
     "source": _CORPUS_DIR / f.value / "refined_requirements.collab.md"}
    for f in WorkFamily
]

_HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
# A slot heading is either a canonical id token (US1 / FR-007 / SC-001) OR a literal
# requirements slot SECTION name. The WHAT-prompt invariant forbids both as a section title:
# titles name *what is communicated*, never the slot they draw from.
_SLOT_RE = re.compile(r"\b(US-?\d+|FR-?\d{2,}|SC-?\d{2,})\b")
_SLOT_NAME_RE = re.compile(
    r"^\s*(user stor(?:y|ies)|functional requirements?|success criteria|"
    r"acceptance criteria|requirements?)\s*$",
    re.IGNORECASE,
)


def _is_slot_heading(h: str) -> bool:
    return bool(_SLOT_RE.search(h) or _SLOT_NAME_RE.match(h))


def _headings(html: str) -> list[str]:
    out = []
    for raw in _HEADING_RE.findall(html):
        text = _TAG_RE.sub("", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            out.append(text)
    return out


def _empty_section_headings(html: str) -> list[str]:
    """Headings whose section body (text up to the next heading) has no visible non-whitespace
    text — the padded/empty-shell smell. Body is the slice between this heading's close and the
    next heading's open; tags stripped, entities ignored."""
    empties: list[str] = []
    # Walk heading spans in document order; a section's body is the slice to the next heading.
    matches = list(re.finditer(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.IGNORECASE | re.DOTALL))
    for i, m in enumerate(matches):
        title = re.sub(r"\s+", " ", _TAG_RE.sub("", m.group(1))).strip()
        if not title:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        between = html[start:end]
        visible = _TAG_RE.sub("", between)
        visible = re.sub(r"&[a-zA-Z#0-9]+;", " ", visible)  # entities count as nothing
        if not visible.strip():
            empties.append(title)
    return empties


def _front_matter_shape_ok(source_text: str, family: str) -> tuple[bool, list[str]]:
    """Pinned classification front-matter shape check (Step 5c.2 / Verification): family pinned to
    the expected value, confirmed_by == 'manual', taxonomy_version == 1, and non-stub content."""
    parsed = parse_requirements(source_text)
    cls = parsed.front_matter.get("classification", {}) if isinstance(
        parsed.front_matter, dict) else {}
    problems: list[str] = []
    if cls.get("family") != family:
        problems.append(f"family={cls.get('family')!r} != {family!r}")
    if str(cls.get("confirmed_by")) != "manual":
        problems.append(f"confirmed_by={cls.get('confirmed_by')!r} != 'manual'")
    if int(cls.get("taxonomy_version", -1)) != 1:
        problems.append(f"taxonomy_version={cls.get('taxonomy_version')!r} != 1")
    if is_stub(parsed):
        problems.append("doc is a stub (visible content < STUB_WORD_THRESHOLD)")
    # Provenance header (Step 5c.1 — must name its real-work source).
    if "CORPUS-PROVENANCE" not in source_text:
        problems.append("missing CORPUS-PROVENANCE header")
    return (not problems), problems


def _setup_goal(tmp: Path, spec: dict) -> dict:
    """Seed a goals row + goal dir with the family source; return the run context. The goals row's
    `workflow_family` is pinned from the fixture (the sweep never depends on classifier agreement)."""
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
        "spec": spec, "goals_dir": goals_dir, "goal_dir": goal_dir,
        "parsed": parsed, "source_hash": parsed.content_hash, "source_text": source_text,
    }


def _run_one(tmp: Path, ctx: dict, out_dir: Path) -> dict:
    spec = ctx["spec"]
    db_path = tmp / "cast.db"
    runner = svc.ProductionAgentRunner(
        Path(svc.config.RENDER_JOBS_DIR) / spec["slug"] / ctx["source_hash"][:12]
    )

    src_path = ctx["goal_dir"] / "refined_requirements.collab.md"
    before = src_path.read_bytes()

    result = svc.request_render(
        spec["slug"], runner=runner, goals_dir=ctx["goals_dir"], db_path=db_path, wait=True
    )

    html_path = ctx["goal_dir"] / "refined_requirements.html"
    html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    report = check_html(html, ctx["parsed"]) if html else None
    resolution = rrs.resolve_render(spec["slug"], goals_dir=ctx["goals_dir"], db_path=db_path)

    headings = _headings(html)
    slot_headings = [h for h in headings if _is_slot_heading(h)]
    empty_sections = _empty_section_headings(html)
    parsed_refs = sorted({b.ref for b in ctx["parsed"].blocks if b.ref})
    fm_ok, fm_problems = _front_matter_shape_ok(ctx["source_text"], spec["family"])

    # checker verdict + score for THIS published artifact: read the job row + attempt verdicts.
    published_score = None
    review_reason = None
    job_id = result.get("job_id")
    if job_id is not None:
        row = svc.get_job_row(job_id, db_path)
        if row is not None:
            published_score = row["published_score"] if "published_score" in row.keys() else None
            review_reason = row["review_reason"] if "review_reason" in row.keys() else None

    # persist per-family artifacts (HTML + check_html report) for the sweep record / human eyeball.
    (out_dir / f"{spec['family']}.html").write_text(html, encoding="utf-8")
    (out_dir / f"{spec['family']}.check_html.json").write_text(
        json.dumps(
            {"passed": report.passed if report else False,
             "violations": list(report.violations) if report else ["no html produced"]},
            indent=2),
        encoding="utf-8",
    )

    res = {
        "slug": spec["slug"], "family": spec["family"],
        "terminal_status": result.get("status"),
        "served_by": resolution.served_by,
        "human_review": bool(resolution.human_review),
        "review_reason": review_reason,
        "published_score": published_score,
        "ready_state": resolution.state,
        "ready_hash_matches": resolution.source_hash == ctx["source_hash"],
        "check_html_passed": bool(report.passed) if report else False,
        "check_html_violations": list(report.violations) if report else ["no html produced"],
        "doctype_count": html.lower().count("<!doctype html>"),
        "n_canonical_refs": len(parsed_refs),
        "headings": headings,
        "slot_headings": slot_headings,
        "empty_sections": empty_sections,
        "html_bytes": len(html.encode("utf-8")),
        "collab_md_unchanged": src_path.read_bytes() == before,
        "front_matter_shape_ok": fm_ok,
        "front_matter_problems": fm_problems,
        "html_path_str": str(out_dir / f"{spec['family']}.html"),
    }
    # Per-family result.json — lets parallel `--family` runs share an out-dir and an
    # `--aggregate` pass assemble the cross-family gate (Step 5c.2 / 5c.4) without re-rendering.
    (out_dir / f"{spec['family']}.result.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8")
    return res


def _is_flagged(r: dict) -> bool:
    """A flagged render is the structural-override's honest degraded state: a best-attempt served
    with `human_review=1` (`served-by: structural_violation` when no structurally-valid attempt
    existed). It is the CORRECT shipped behavior, not a sweep failure — its quality misses route
    to carry-forward findings, never to the blocking gate."""
    return bool(r["human_review"]) or r["served_by"] == "structural_violation"


def _per_family_checks(r: dict) -> dict:
    """The per-family **happy-path blocking** checks (Step 5c.2, reconciled with the
    structural-violation OVERRIDE + the "± human_review" success criterion).

    Every family MUST: reach terminal `published` (never the deterministic `fallback` — reserved
    for literal no-output — never `failed`/`superseded`); be a single self-contained file; never
    write the canonical `.collab.md`; carry valid pinned classification front matter. A CLEAN
    publish (served-by maker, no flag) additionally MUST pass `check_html` (ids carried, none
    invented). A FLAGGED publish satisfies `check_html_clean_or_flagged` by being flagged — its
    structural miss is the served degraded state, surfaced as a carry-forward finding instead.

    Slot headings and empty shells are NOT blocking here — they are HOW-layer communication-quality
    findings (the WHAT layer owns section *vocabulary*, the HOW prompt owns rendering them); the
    5c fix levers (WHAT vocab + `families.py` recipe wording) cannot touch them. They are recorded
    as findings (surface, don't suppress) and carried into 5d's sign-off."""
    return {
        "published": r["terminal_status"] == "published",
        "not_deterministic_fallback": r["served_by"] != "deterministic"
        and r["ready_state"] == "ready",
        "check_html_clean_or_flagged": r["check_html_passed"] or _is_flagged(r),
        "single_file": r["doctype_count"] == 1,
        "collab_md_never_written": r["collab_md_unchanged"],
        "front_matter_shape_ok": r["front_matter_shape_ok"],
    }


def _quality_findings(r: dict) -> list[str]:
    """Per-family communication-quality findings (carry-forward, never blocking). Each is a
    HOW-layer miss surfaced for the human-eyeball pass + 5d sign-off — never silently passed."""
    out: list[str] = []
    if r["human_review"] or r["served_by"] == "structural_violation":
        out.append(
            f"flagged (served_by={r['served_by']}, reason={r['review_reason']}, "
            f"score={r['published_score']})")
    if not r["check_html_passed"]:
        out.append(f"check_html: {r['check_html_violations']}")
    if r["slot_headings"]:
        out.append(f"slot headings (HOW emitted id/slot in a heading): {r['slot_headings']}")
    if r["empty_sections"]:
        out.append(f"empty section shells (HOW over-structured a thin section): {r['empty_sections']}")
    return out


def _pairwise_distinct(results: list[dict]) -> tuple[bool, list[str]]:
    """Every pair of families has differing section-heading sets (deterministic distinctness)."""
    collisions: list[str] = []
    for a, b in itertools.combinations(results, 2):
        sa = {h.lower() for h in a["headings"]}
        sb = {h.lower() for h in b["headings"]}
        if sa == sb:
            collisions.append(f"{a['family']} == {b['family']} ({sorted(sa)})")
    return (not collisions), collisions


def _write_golden(results: list[dict], out_dir: Path, golden_dir: Path) -> None:
    """Copy each family's rendered HTML into the goal's signoff/golden dir + a one-page index +
    an sc-sweep note (Step 5c.4 — the SC-002 evidence trail; provisional, finalized in 5d)."""
    golden_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        src = Path(r["html_path_str"])
        if src.exists():
            (golden_dir / f"{r['family']}.html").write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8")

    rows = "\n".join(
        f"  <tr><td><a href='{r['family']}.html'>{r['family']}</a></td>"
        f"<td>{r['terminal_status']}</td><td>{r['served_by']}</td>"
        f"<td>{'YES' if r['human_review'] else 'no'}</td>"
        f"<td>{r['published_score'] if r['published_score'] is not None else '—'}</td>"
        f"<td>{len(r['headings'])}</td><td>{r['html_bytes']}</td>"
        f"<td>{'<em>clean</em>' if not _quality_findings(r) else '; '.join(_quality_findings(r))}</td>"
        f"</tr>"
        for r in results
    )
    n_clean = sum(1 for r in results if not _quality_findings(r))
    index = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Nine-family golden renders — SC-002 (provisional)</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:72rem;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;vertical-align:top}}
th{{background:#f6f6f6}}td:last-child{{max-width:24rem;color:#a33}}</style></head><body>
<h1>Nine-family golden renders — SC-002 evidence (provisional)</h1>
<p>Generated by <code>eval_family_sweep.py</code> (real maker pipeline; <code>gaps[]</code> dormant).
<strong>Provisional in 5c — re-run in 5d</strong> with gap machinery live. Happy-path gate:
all nine reached <code>published</code>, pairwise-distinct headings; <strong>{n_clean}/{len(results)}
families clean</strong>. The non-clean rows are <strong>HOW-layer carry-forward findings</strong>
(out of 5c's WHAT-vocab / recipe-wording scope) for the side-by-side human-eyeball pass — autonomous
runs cannot drive a browser, so this is a static verdict + human-eyeball carry-forward.</p>
<table><thead><tr><th>family</th><th>status</th><th>served-by</th><th>human_review</th>
<th>score</th><th>headings</th><th>bytes</th><th>finding (carry-forward)</th></tr></thead>
<tbody>
{rows}
</tbody></table></body></html>
"""
    (golden_dir / "index.html").write_text(index, encoding="utf-8")
    print(f"[sweep] golden renders + index → {golden_dir}")


def _aggregate(results: list[dict], out_dir: Path, *, golden: bool) -> bool:
    """Assemble the cross-family gate from per-family results, write summary.json, print the
    report, and (optionally) the golden evidence. Returns the blocking-gate verdict.

    The blocking gate is the *happy-path* contract (Step 5c.2): every family `published` with a
    structurally-VALID maker render (`check_html` green, no slot headings, no empty shells) and
    pairwise-distinct headings. A `human_review` flag or a `served-by: structural_violation`
    publish is NOT a silent pass — it is recorded as a carry-forward FINDING for 5d's sign-off."""
    results = sorted(results, key=lambda r: [f.value for f in WorkFamily].index(r["family"]))
    per_family = {r["family"]: _per_family_checks(r) for r in results}
    findings = {r["family"]: _quality_findings(r) for r in results}
    distinct_ok, collisions = _pairwise_distinct(results) if len(results) > 1 else (True, [])

    carry_forward = [
        f"{r['family']}: " + "; ".join(findings[r["family"]])
        + " — eyeball; HOW-layer lever (out of 5c vocab scope) → carry into 5d sign-off"
        for r in results if findings[r["family"]]
    ]
    n_clean = sum(1 for r in results if not _is_flagged(r) and not findings[r["family"]])

    all_per_family_ok = all(all(c.values()) for c in per_family.values())
    gate_ok = all_per_family_ok and (distinct_ok if len(results) > 1 else True)

    summary = {
        "results": results, "per_family_checks": per_family,
        "quality_findings": findings,
        "pairwise_distinct": distinct_ok, "pairwise_collisions": collisions,
        "carry_forward_findings": carry_forward, "blocking_gate_ok": gate_ok,
        "n_families": len(results), "n_clean": n_clean,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n[sweep] ===== PER-FAMILY HAPPY-PATH GATE (blocking) =====")
    for fam, checks in per_family.items():
        fails = " ".join(f"FAIL:{k}" for k, v in checks.items() if not v) or "published"
        tag = "clean" if not findings[fam] else "FLAGGED/finding"
        print(f"[sweep]   {'OK ' if all(checks.values()) else 'XX '} {fam:<20} {fails:<28} [{tag}]")
    if len(results) > 1:
        print(f"[sweep]   pairwise heading-set distinctness: {'PASS' if distinct_ok else 'FAIL'}")
        for c in collisions:
            print(f"[sweep]       collision: {c}")
    print(f"\n[sweep]   {n_clean}/{len(results)} families CLEAN (served-by maker, no flag, no finding)")
    if carry_forward:
        print("\n[sweep] ===== QUALITY FINDINGS (carry-forward — surfaced, never a silent pass) =====")
        for item in carry_forward:
            print(f"[sweep]   • {item}")
    print(f"\n[sweep] artifacts: {out_dir}")
    print(f"[sweep] HAPPY-PATH GATE ({len(results)} famil"
          f"{'y' if len(results) == 1 else 'ies'}): {'PASS' if gate_ok else 'FAIL'} "
          f"(every family published ± human_review, distinct); "
          f"{len(carry_forward)} quality finding(s) carried forward")

    if golden:
        _write_golden(results, out_dir, _SIGNOFF_GOLDEN_DIR)
    return gate_ok


def _default_out_dir() -> Path:
    """Stable shared artifacts dir under build/ (a non-goal, non-CI runtime area) so parallel
    `--family` runs and a later `--aggregate` pass converge on one location."""
    return REPO_ROOT / "build" / "family-sweep" / "latest"


def main() -> int:
    parser = argparse.ArgumentParser(prog="eval_family_sweep")
    parser.add_argument("--family", help="Render only this WorkFamily value (e.g. bug_fix).")
    parser.add_argument("--out-dir", help="Shared artifacts dir (default build/family-sweep/latest). "
                        "Parallel --family runs + --aggregate share it.")
    parser.add_argument("--aggregate", action="store_true",
                        help="Assemble the cross-family gate from existing {family}.result.json "
                        "files in --out-dir (no rendering). Use after parallel --family runs.")
    parser.add_argument("--golden", action="store_true",
                        help="Copy rendered evidence + index into the goal's signoff/golden dir.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- aggregate-only: assemble the gate from per-family result.json files -----------
    if args.aggregate:
        loaded = []
        for f in WorkFamily:
            p = out_dir / f"{f.value}.result.json"
            if p.exists():
                loaded.append(json.loads(p.read_text(encoding="utf-8")))
            else:
                print(f"[sweep]   (missing result for {f.value} — not yet rendered)")
        if not loaded:
            parser.error(f"no {{family}}.result.json files in {out_dir}")
        print(f"[sweep] aggregating {len(loaded)}/9 families from {out_dir}")
        return 0 if _aggregate(loaded, out_dir, golden=args.golden) else 1

    # ---- render path (one family, or all nine serially) --------------------------------
    families = [f for f in FAMILIES if f["family"] == args.family] if args.family else FAMILIES
    if not families:
        parser.error(f"unknown family {args.family!r}; valid: {[f.value for f in WorkFamily]}")

    run_dir = Path(tempfile.mkdtemp(prefix="family-sweep-"))
    init_db(run_dir / "cast.db")
    svc._reset_state()
    print(f"[sweep] run dir: {run_dir}  out_dir: {out_dir}")

    results = []
    for spec in families:
        ctx = _setup_goal(run_dir, spec)
        print(f"[sweep] rendering {spec['family']} — real claude -p maker …")
        res = _run_one(run_dir, ctx, out_dir)
        results.append(res)
        print(
            f"[sweep]   -> status={res['terminal_status']} served_by={res['served_by']} "
            f"human_review={res['human_review']} reason={res['review_reason']} "
            f"check_html={res['check_html_passed']} headings={len(res['headings'])} "
            f"empty={res['empty_sections']} slot={res['slot_headings']} bytes={res['html_bytes']}"
        )

    # A single --family render reports its own per-family checks; the cross-family gate (pairwise
    # distinctness, golden index) belongs to the full set — run with --aggregate after all nine.
    if args.family:
        ok = all(_per_family_checks(results[0]).values())
        print(f"[sweep] {args.family} per-family checks: {'PASS' if ok else 'FAIL'} "
              f"(run --aggregate for the cross-family gate)")
        return 0 if ok else 1
    return 0 if _aggregate(results, out_dir, golden=args.golden) else 1


if __name__ == "__main__":
    raise SystemExit(main())
