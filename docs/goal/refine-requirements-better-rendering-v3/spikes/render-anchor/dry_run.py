#!/usr/bin/env python3
"""Sub-phase 1b — render-anchor dry-run (read-only spike).

Measures the placement + ``block_ref``-bridge rate of every existing open comment against the
PUBLISHED RENDER text — the exact render-space procedure Sub-phase 2's migration + creation path
will productionize. No production edits; this whole sub-phase is a spike.

Discipline (matches the shared-walker no-copy rule, _shared_context.md "Cross-Phase Hard Edges"):
  - import ``container_text_index`` (maker_gate.py:259) — the ONE container-text walker; never re-walk.
  - import ``Container.unit_at`` (maker_gate.py:175) for the enclosing-unit bridge.
  - import ``_ID_RE`` / ``_norm_ref`` (maker_gate.py) for the canonical-id (anchor-label) read — the
    same label scan ``check_html`` uses to bridge a render container back to a source ref.

The render-space ``block_ref`` resolver this prototypes (productionized in sp2):
  offset = idx.find(quote)                      # JS concat.indexOf parity (requirements_comments.js)
  unit   = idx.unit_at(offset)                  # innermost enclosing requirement-unit container
  ids    = {_norm_ref(t) for t in _ID_RE.findall(unit.text)}   # anchor labels visible in that unit
  block_ref = the single id in `ids`            # exactly-one  -> the canonical-id bridge
            = None  (zero ids)                  # ref-less container -> NULL BY CONSTRUCTION (success)

Miss classification (plan Step 1b.2):
  - cross-boundary    : quote places in the document concat but is NOT contained within one unit's
                        own text slice (spans containers) OR resolves >1 distinct anchor label.
  - decoration-spanning: quote places only outside every unit container (unit_at -> None): render
                        decoration / hero / section-heading text with no enclosing unit.
  - no-anchor-label   : quote places inside a unit container that carries ZERO anchor labels
                        (ref-less render) -> block_ref NULL by construction (plan-review Decision #1,
                        SUCCESS, never counted as a failure).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent
REPO = SPIKE_DIR.parents[4]  # docs/goal/<slug>/spikes/render-anchor -> repo root
sys.path.insert(0, str(REPO / "cast-server"))

from cast_server.requirements_render.maker_gate import (  # noqa: E402  (path injected above)
    _ID_RE,
    _norm_ref,
    container_text_index,
)

# --- Corpus -------------------------------------------------------------------------------------
# The production DB (~/.cast/diecast.db) carries ZERO comments; there are no live v3-goal comments.
# The only existing comments on disk are the prior-spike-seeded reviewer/maker corpus minted by
# selecting rendered text against the feature-maker render (the realistic stand-in for the v2
# fixture pair). Their CURRENT stored quoted_text is the post-reanchor (v2-space) quote, so the
# "published render" to validate against is feature-maker-v2.html.
COMMENT_DB = SPIKE_DIR.parent / "1b" / "scratch.sqlite"
COMMENT_GOAL = "spike-1b-anchor-survival"
RENDER_HTML = SPIKE_DIR.parent / "1b" / "feature-maker-v2.html"
MEAS_DIR = SPIKE_DIR / "measurements"


def load_comments() -> list[dict]:
    conn = sqlite3.connect(COMMENT_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, goal_slug, quoted_text, section_hint, state, author_kind "
        "FROM requirement_comments WHERE goal_slug=? ORDER BY id",
        (COMMENT_GOAL,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve(idx, quote: str) -> dict:
    """The render-space placement + block_ref bridge for one quote. Returns the measurement dict."""
    offset = idx.find(quote)
    placed = offset >= 0
    out = {
        "placed": placed,
        "offset": offset,
        "block_ref": None,
        "in_block": False,
        "miss_class": None,
        "unit_tag": None,
        "unit_ids": [],
    }
    if not placed:
        # Not on this render at all (a stale/paraphrased quote): the displaced/orphaned route, not a
        # render-space miss-class. Recorded as not-placed so it never inflates the placement rate.
        out["miss_class"] = "not-on-render"
        return out

    unit = idx.unit_at(offset)
    if unit is None:
        # Placed only in non-unit text (hero / section heading / render decoration).
        out["miss_class"] = "decoration-spanning"
        return out

    out["unit_tag"] = unit.tag
    # Spans past the enclosing unit -> the quote crosses a container boundary.
    if quote not in unit.text:
        out["miss_class"] = "cross-boundary"
        return out

    ids = sorted({_norm_ref(t) for t in _ID_RE.findall(unit.text)})
    out["unit_ids"] = ids
    if len(ids) == 1:
        out["block_ref"] = ids[0]
        out["in_block"] = True
        return out
    if len(ids) == 0:
        # Ref-less unit container -> NULL BY CONSTRUCTION (plan-review Decision #1): a SUCCESS, the
        # comment is placed; block_ref is honestly NULL. in_block True (it IS inside a unit), but the
        # bridge yields NULL — not a failure, not retried, not badged.
        out["in_block"] = True
        out["miss_class"] = "no-anchor-label"  # tag for the breakdown; NOT a failure
        return out
    # >1 distinct anchor label inside the innermost unit -> ambiguous: a cross-boundary quote.
    out["miss_class"] = "cross-boundary"
    return out


# --- Resolver-classification probes (synthetic, read-only) --------------------------------------
# The real existing-comment corpus is entirely ref-bearing (every open comment resolves a unique
# canonical id). It therefore never exercises the ref-less / cross-boundary / decoration branches
# that Sub-phase 2's CREATION path must handle. These probes are quotes drawn VERBATIM from the SAME
# published render (feature-maker-v2.html) — NOT comments, never counted in the placement rate —
# that pin each miss-class so sp2 can trust the resolver classifies every branch as designed.
PROBES = [
    {
        "name": "ref-less unit (Not-now bullet)",
        "quote": "Ad-hoc one-off exports triggered manually outside any schedule.",
        "expect_miss": "no-anchor-label",
        "expect_block_ref": None,  # NULL BY CONSTRUCTION — success, never a failure
    },
    {
        "name": "cross-boundary (FR-001 -> FR-002 span)",
        "quote": "validate it before saving.\n      FR-002The system shall run",
        "expect_miss": "cross-boundary",
        "expect_block_ref": None,  # NEVER guessed (orphan-over-guess)
    },
    {
        "name": "decoration-spanning (hero title, outside every unit)",
        "quote": "Export Scheduler",
        "expect_miss": "decoration-spanning",
        "expect_block_ref": None,
    },
]


def run_probes(idx) -> list[dict]:
    out = []
    for p in PROBES:
        m = resolve(idx, p["quote"])
        out.append({
            "name": p["name"],
            "quote": p["quote"],
            "expect_miss": p["expect_miss"],
            "got_miss": m["miss_class"],
            "expect_block_ref": p["expect_block_ref"],
            "got_block_ref": m["block_ref"],
            "ok": m["miss_class"] == p["expect_miss"] and m["block_ref"] == p["expect_block_ref"],
            "placed": m["placed"],
            "unit_tag": m["unit_tag"],
            "unit_ids": m["unit_ids"],
        })
    return out


def main() -> int:
    MEAS_DIR.mkdir(parents=True, exist_ok=True)
    render_html = RENDER_HTML.read_text()
    idx = container_text_index(render_html)

    comments = load_comments()
    measurements: list[dict] = []
    for c in comments:
        m = resolve(idx, c["quoted_text"])
        rec = {
            "id": c["id"],
            "goal_slug": c["goal_slug"],
            "state": c["state"],
            "author_kind": c["author_kind"],
            "section_hint": c["section_hint"],
            "quoted_text": c["quoted_text"],
            **m,
        }
        measurements.append(rec)
        (MEAS_DIR / f"comment-{c['id']:03d}.json").write_text(json.dumps(rec, indent=2) + "\n")

    # --- Aggregate (PASS criterion applies to OPEN comments — the ones a reviewer is watching) ---
    open_recs = [m for m in measurements if m["state"] == "open"]
    placed_open = [m for m in open_recs if m["placed"]]
    in_block_open = [m for m in placed_open if m["in_block"]]
    # A "unique block_ref" resolution = placed in a unit that yielded exactly one canonical id.
    ref_unique = [m for m in in_block_open if m["block_ref"] is not None]
    ref_less_null = [m for m in in_block_open if m["block_ref"] is None]  # NULL by construction = success

    miss_cross = [m for m in placed_open if m["miss_class"] == "cross-boundary"]
    miss_decoration = [m for m in placed_open if m["miss_class"] == "decoration-spanning"]
    miss_no_label = ref_less_null  # no-anchor-label == ref-less NULL by construction

    # PASS iff every OPEN comment places AND every in-block open quote resolves a unique block_ref OR
    # is a classifiable ref-less NULL; no unplaced-open and no mysterious (unclassified) miss.
    unplaced_open = [m for m in open_recs if not m["placed"]]
    mysterious = [
        m for m in placed_open
        if not m["in_block"] and m["miss_class"] not in ("cross-boundary", "decoration-spanning")
    ]
    # --- Resolver-classification probes (synthetic; gate the classifier, not the corpus) ---
    probes = run_probes(idx)
    (SPIKE_DIR / "probes.json").write_text(json.dumps(probes, indent=2) + "\n")
    probes_ok = all(p["ok"] for p in probes)
    verdict_pass = not unplaced_open and not mysterious and probes_ok

    summary = {
        "render": str(RENDER_HTML.relative_to(REPO)),
        "comment_source": str(COMMENT_DB.relative_to(REPO)),
        "total_comments": len(measurements),
        "open_comments": len(open_recs),
        "non_open_comments": [
            {"id": m["id"], "state": m["state"], "placed": m["placed"]}
            for m in measurements if m["state"] != "open"
        ],
        "open_placed": len(placed_open),
        "open_in_block": len(in_block_open),
        "ref_unique": len(ref_unique),
        "ref_less_null_by_construction": len(ref_less_null),
        "miss_cross_boundary": len(miss_cross),
        "miss_decoration_spanning": len(miss_decoration),
        "miss_no_anchor_label": len(miss_no_label),
        "unplaced_open": len(unplaced_open),
        "mysterious_unclassified": len(mysterious),
        "placement_rate": f"{len(placed_open)}/{len(open_recs)}",
        "block_ref_unique_rate": f"{len(ref_unique)}/{len(in_block_open)}",
        "probes_total": len(probes),
        "probes_ok": sum(1 for p in probes if p["ok"]),
        "verdict": "PASS" if verdict_pass else "FAIL",
    }
    (SPIKE_DIR / "aggregate.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print("\n--- resolver probes ---")
    for p in probes:
        print(
            f"  {'OK ' if p['ok'] else 'XX '} {p['name']:<46} "
            f"miss={p['got_miss'] or '-':<19} block_ref={p['got_block_ref'] or 'NULL'}"
        )
    print("\n--- per-comment ---")
    for m in measurements:
        print(
            f"  #{m['id']} [{m['state']:>8}] placed={m['placed']!s:>5} "
            f"block_ref={m['block_ref'] or 'NULL':>7} miss={m['miss_class'] or '-':<19} "
            f":: {m['quoted_text'][:48]!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
