#!/usr/bin/env python3
"""spike_id_audit.py — throwaway audit for spike 1a (NOT collected by pytest).

Three audits over the hand-crafted maker HTML, per family:

  1. **id-token set equality** — the set of canonical US-NN / FR-NNN / SC-NNN tokens the
     deterministic engine assigns (parsed structurally from the source `.collab.md`) equals
     the set of canonical id tokens visible in the maker HTML. No missing, no invented.

  2. **FR-003 per-block correspondence** — each id's *anchoring label* (a `<span class="anchor">`
     in the maker) is unique and sits on the block whose SOURCE text it identifies. Encoded as a
     significant-token overlap between the source requirement text and the maker `.req-unit`
     that carries the anchor. Set-equality alone would pass a label on the wrong block; this
     does not. **Phase 3 reuses this as its acceptance pattern — encoded faithfully here.**

  3. **Self-containment grep + zero-`id` grep** — no external src/href beyond the FR-028
     sanctioned two; CSS inline; no `id=` attribute; no `data-block-anchor`.

Run:  python spike_id_audit.py
Source id-set is taken from the parser (the authoritative assigned-id set), never from a
prose regex — so a prose cross-reference like "(this is SC-001)" never inflates the source set.
"""
from __future__ import annotations

import re
import sys
import pathlib

sys.path.insert(0, "/home/sridherj/workspace/diecast/cast-server")
from bs4 import BeautifulSoup  # noqa: E402
from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.blocks import BlockKind  # noqa: E402

SPIKE = pathlib.Path(__file__).resolve().parent
GOAL = SPIKE.parent.parent  # docs/goal/refine-requirements-better-rendering-v3

FAMILIES = {
    "new_initiative": GOAL / "refined_requirements.collab.md",
    "bug_fix": SPIKE / "fixtures" / "goal-card-markdown-leak.collab.md",
}

ID_RE = re.compile(r"\b(?:US-?\d+|FR-\d{3}|SC-\d{3})\b")
# FR-028 sanctioned external references — the ONLY src/href allowed in a self-contained file.
SANCTIONED_SRC = {"/static/htmx.min.js", "/static/requirements_comments.js"}
STOP = set(
    "the a an and or of to for is are in on it its by with that this as be from "
    "when then shall system should not no any per each every can may must only "
    "than into over up out off so but if also which whose them they their there".split()
)


def norm(tok: str) -> str:
    return tok.replace("US-", "US")


def sig_tokens(text: str) -> set[str]:
    """Significant lower-case word tokens (len>=4, non-stopword) for overlap scoring."""
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]+", text.lower())
    return {w for w in words if len(w) >= 4 and w not in STOP}


def _row_desc(body: str) -> str:
    cells = [c.strip() for c in body.strip().strip("|").split("|")]
    cells = [c for c in cells if c]
    return cells[1] if len(cells) >= 2 else (cells[-1] if cells else body)


def source_id_map(text: str) -> dict[str, str]:
    """The authoritative assigned-id -> source-text map, structurally from the parser."""
    parsed = parse_requirements(text)
    out: dict[str, str] = {}
    for b in parsed.blocks:
        if b.kind in (BlockKind.FR, BlockKind.SC) and b.ref:
            out[norm(b.ref)] = _row_desc(b.body)
        elif b.kind is BlockKind.USER_STORY and b.heading:
            m = re.match(r"\s*(US-?\d+)", b.heading)
            if m:
                out[norm(m.group(1))] = b.heading + " " + b.body
    return out


def visible_text(soup: BeautifulSoup) -> str:
    clone = BeautifulSoup(str(soup), "html.parser")
    for tag in clone(["style", "script"]):
        tag.decompose()
    return clone.get_text(" ")


def audit_family(fam: str, src_path: pathlib.Path) -> dict:
    text = src_path.read_text()
    src_map = source_id_map(text)
    src_ids = set(src_map)

    html = (SPIKE / f"{fam}-maker.html").read_text()
    soup = BeautifulSoup(html, "html.parser")

    # ---- Audit 1: id-token set equality (visible text only) ----
    vis_ids = {norm(t) for t in ID_RE.findall(visible_text(soup))}
    missing = sorted(src_ids - vis_ids)
    invented = sorted(vis_ids - src_ids)
    set_equal = not missing and not invented

    # ---- Audit 2: FR-003 per-block correspondence (anchor labels) ----
    # The faithful test of "the label sits on the block whose source text it identifies":
    # the maker block carrying anchor X must overlap id X's SOURCE text MORE than any OTHER
    # id's source text (nearest-source argmax). This is robust to the maker legitimately
    # *distilling* a user story for communication (it never requires verbatim carriage of the
    # WHAT — only of the id) yet still fails a label placed on the wrong block.
    src_tok_map = {cid: sig_tokens(txt) for cid, txt in src_map.items()}
    anchors = soup.select("span.anchor")
    anchor_ids: list[str] = []
    corr_rows = []
    seen: set[str] = set()
    dup_labels = []
    for span in anchors:
        toks = ID_RE.findall(span.get_text())
        if not toks:
            continue
        cid = norm(toks[0])
        anchor_ids.append(cid)
        if cid in seen:
            dup_labels.append(cid)
        seen.add(cid)
        unit = span.find_parent(class_="req-unit") or span.parent
        unit_toks = sig_tokens(unit.get_text(" "))
        own = len(src_tok_map.get(cid, set()) & unit_toks)
        # nearest source over the SAME kind-prefix (US vs FR vs SC) — the discriminating set.
        prefix = re.match(r"[A-Z]+", cid).group(0)
        scored = {
            other: len(toks2 & unit_toks)
            for other, toks2 in src_tok_map.items()
            if other.startswith(prefix)
        }
        best_id = max(scored, key=scored.get)
        best = scored[best_id]
        # pass: this block matches its OWN id best (argmax), strictly beating any other id,
        # with a small absolute floor so a degenerate empty unit cannot pass.
        ok = (own >= 2 and best_id == cid and own > max(
            [v for k, v in scored.items() if k != cid] or [0]
        ))
        corr_rows.append((cid, own, best_id, best, ok))

    anchor_set = set(anchor_ids)
    every_id_labeled = (anchor_set == src_ids)
    corr_pass = bool(corr_rows) and all(r[4] for r in corr_rows) and not dup_labels and every_id_labeled

    # ---- Audit 3a: self-containment ----
    bad_src = []
    for tag in soup.find_all(src=True):
        if tag.get("src") not in SANCTIONED_SRC:
            bad_src.append(tag.get("src"))
    bad_href = [a.get("href") for a in soup.find_all(href=True)]  # any <link>/external href
    has_link = bool(soup.find("link"))
    self_contained = not bad_src and not bad_href and not has_link

    # ---- Audit 3b: zero-id (ATTRIBUTE-based, not substring) ----
    # The DOM contract bans the `id` and `data-block-anchor` *attributes*. The maker may still
    # quote the words "no data-block-anchor" as escaped requirement text (FR-003 source) — that
    # is content, not an attribute, and must not fail the audit. So we count real attributes via
    # the parse tree, and additionally surface a raw substring grep for transparency.
    id_attr_elems = soup.find_all(lambda t: t.has_attr("id"))
    dba_attr_elems = soup.find_all(lambda t: t.has_attr("data-block-anchor"))
    id_attr_count = len(id_attr_elems)
    dba_attr_count = len(dba_attr_elems)
    raw_id_grep = len(re.findall(r"<[^>]*\sid\s*=", html))  # id= only inside a start tag
    raw_dba_grep = html.count("data-block-anchor")  # includes prose/comment mentions
    zero_id = (id_attr_count == 0 and dba_attr_count == 0)

    return dict(
        fam=fam, src_ids=sorted(src_ids), vis_ids=sorted(vis_ids),
        missing=missing, invented=invented, set_equal=set_equal,
        corr_rows=corr_rows, dup_labels=dup_labels,
        every_id_labeled=every_id_labeled, corr_pass=corr_pass,
        bad_src=bad_src, bad_href=bad_href, has_link=has_link, self_contained=self_contained,
        id_attr_count=id_attr_count, dba_attr_count=dba_attr_count,
        raw_id_grep=raw_id_grep, raw_dba_grep=raw_dba_grep, zero_id=zero_id,
        anchor_count=len(anchor_ids),
    )


def main() -> int:
    overall_ok = True
    for fam, src in FAMILIES.items():
        r = audit_family(fam, src)
        print("=" * 78)
        print(f"FAMILY: {fam}")
        print("=" * 78)
        print(f"[1] id-token SET EQUALITY .......... {'PASS' if r['set_equal'] else 'FAIL'}")
        print(f"    source ids ({len(r['src_ids'])}): {r['src_ids']}")
        print(f"    visible ids ({len(r['vis_ids'])}): {r['vis_ids']}")
        if r["missing"]:
            print(f"    MISSING from maker: {r['missing']}")
        if r["invented"]:
            print(f"    INVENTED in maker : {r['invented']}")
        print()
        print(f"[2] FR-003 PER-BLOCK CORRESPONDENCE  {'PASS' if r['corr_pass'] else 'FAIL'}")
        print(f"    anchor labels: {r['anchor_count']}   every id labeled exactly once: {r['every_id_labeled']}")
        if r["dup_labels"]:
            print(f"    DUPLICATE anchor labels: {r['dup_labels']}")
        print("    id        own-overlap  best-source-match  block-match")
        for cid, own, best_id, best, ok in r["corr_rows"]:
            print(f"    {cid:<9} {own:>3}          {best_id:<9}({best:>2})       {'ok' if ok else 'MISMATCH'}")
        print()
        print(f"[3a] SELF-CONTAINMENT .............. {'PASS' if r['self_contained'] else 'FAIL'}")
        print(f"    external src (non-sanctioned): {r['bad_src'] or 'none'}")
        print(f"    <link> tags: {r['has_link']}   stray href: {r['bad_href'] or 'none'}")
        print(f"[3b] ZERO-id / data-block-anchor ... {'PASS' if r['zero_id'] else 'FAIL'}")
        print(f"    elements with id attribute: {r['id_attr_count']}   "
              f"elements with data-block-anchor attribute: {r['dba_attr_count']}")
        print(f"    (raw grep — start-tag 'id=': {r['raw_id_grep']}; "
              f"substring 'data-block-anchor': {r['raw_dba_grep']} "
              f"— prose/comment mentions of the contract, not attributes)")
        print()
        fam_ok = r["set_equal"] and r["corr_pass"] and r["self_contained"] and r["zero_id"]
        print(f"==> {fam}: {'ALL AUDITS PASS' if fam_ok else 'AUDIT FAILURE'}")
        print()
        overall_ok = overall_ok and fam_ok
    print("#" * 78)
    print(f"OVERALL: {'ALL FAMILIES PASS ALL AUDITS' if overall_ok else 'SEE FAILURES ABOVE'}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
