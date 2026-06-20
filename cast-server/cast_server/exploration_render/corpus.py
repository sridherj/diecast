"""The exploration corpus loader + source digest (the readiness key).

Reads 3a's N×M markdown substrate under `goals/{slug}/exploration/` into the per-step corpus + the
hat matrix, path-validated to the goal's own tree (no `..` escape, no wider-repo read). A step with
a missing/placeholder playbook OR zero present hat notes is DEGRADED (marked, never dropped). The
source digest is over the sorted (relpath, content_hash) set of the CONSUMED md files only.
"""
from __future__ import annotations

import re
from pathlib import Path

from cast_server.requirements_render.hashing import content_hash

#: Always-on hats (never gated). A step missing one of these (a `null`/dropped cell) is a visible
#: degradation, not a checker pass.
ALWAYS_ON_HATS: tuple[str, ...] = ("contrarian", "first-principles", "90-10")

# Filename grammars (3a contract): playbooks `{NN}-{step-slug}.ai.md`,
# research `{NN}-{step-slug}-{hat-id}.ai.md`. The hat-id is the trailing segment.
_PLAYBOOK_RE = re.compile(r"^(\d+)-(.+)\.ai\.md$")
_PLACEHOLDER_MARKERS = ("(placeholder)", "TODO", "TBD", "<!-- placeholder -->")


def _within_exploration_tree(base: Path, path: Path) -> bool:
    """True iff `path` resolves inside the goal's own `exploration/` tree (no `..` escape)."""
    try:
        b = base.resolve()
        rp = path.resolve()
    except OSError:
        return False
    return rp == b or b in rp.parents


def _is_placeholder(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 40:
        return True
    return any(m.lower() in stripped.lower() for m in _PLACEHOLDER_MARKERS)


def _parse_hat_id(stem: str, step_slug: str) -> str | None:
    """Recover the trailing hat-id from a research filename stem `{NN}-{step-slug}-{hat-id}`.

    `Path.stem` strips only the final `.md`, leaving a `.ai` tail on the `.ai.md` files — strip it.
    """
    if stem.endswith(".ai"):
        stem = stem[:-3]
    m = re.match(r"^(\d+)-(.+)$", stem)
    if not m:
        return None
    rest = m.group(2)
    prefix = step_slug + "-"
    if rest.startswith(prefix):
        return rest[len(prefix):] or None
    return rest.rsplit("-", 1)[-1] if "-" in rest else None


def source_digest(consumed: list[tuple[str, str]]) -> str:
    """Digest over the sorted (relpath, content_hash) set of consumed md files — the readiness key."""
    parts = sorted(f"{rel}:{content_hash(text)}" for rel, text in consumed)
    return content_hash("\n".join(parts))[:32]


def load_exploration_corpus(goal_dir: Path) -> tuple[list[dict], dict[str, list[str]], str, str]:
    """Read `goals/{slug}/exploration/` → `(steps, hat_matrix, summary_text, source_digest)`.

    Each step dict is `{nn, slug, name, playbook_text, hat_notes:[{hat_id, text, status}],
    summary_text, degraded}`. A step with a missing/placeholder playbook OR zero PRESENT hat notes
    is DEGRADED (marked, never dropped). Always-on hats are applicable even when their cell is absent
    (surfaced as a `dropped` degradation).
    """
    expl = goal_dir / "exploration"
    playbooks_dir = expl / "playbooks"
    research_dir = expl / "research"
    consumed: list[tuple[str, str]] = []

    summary_text = ""
    summary_path = expl / "summary.ai.md"
    if summary_path.is_file() and _within_exploration_tree(expl, summary_path):
        summary_text = summary_path.read_text(encoding="utf-8")
        consumed.append(("summary.ai.md", summary_text))

    steps: list[dict] = []
    hat_matrix: dict[str, list[str]] = {}
    if playbooks_dir.is_dir():
        for pb in sorted(playbooks_dir.glob("*.ai.md")):
            if not _within_exploration_tree(expl, pb):
                continue
            m = _PLAYBOOK_RE.match(pb.name)
            if not m:
                continue
            nn, slug = m.group(1), m.group(2)
            playbook_text = pb.read_text(encoding="utf-8")
            consumed.append((f"playbooks/{pb.name}", playbook_text))

            hat_notes: list[dict] = []
            applicable: list[str] = []
            cells = sorted(research_dir.glob(f"{nn}-{slug}-*.ai.md")) if research_dir.is_dir() else []
            for rp in cells:
                if not _within_exploration_tree(expl, rp):
                    continue
                hat_id = _parse_hat_id(rp.stem, slug)
                if not hat_id:
                    continue
                text = rp.read_text(encoding="utf-8")
                consumed.append((f"research/{rp.name}", text))
                status = "dropped" if _is_placeholder(text) else "present"
                hat_notes.append({"hat_id": hat_id, "text": text, "status": status})
                applicable.append(hat_id)

            for hat in ALWAYS_ON_HATS:
                if hat not in applicable:
                    applicable.append(hat)
                    hat_notes.append({"hat_id": hat, "text": "", "status": "dropped"})

            present = [h for h in hat_notes if h["status"] == "present"]
            degraded = _is_placeholder(playbook_text) or not present
            steps.append({
                "nn": nn, "slug": slug, "name": slug.replace("-", " ").title(),
                "playbook_text": playbook_text, "hat_notes": hat_notes,
                "summary_text": summary_text, "degraded": degraded,
            })
            hat_matrix[slug] = applicable

    return steps, hat_matrix, summary_text, source_digest(consumed)
