"""End-to-end build tests + idempotency for the cast-preso-review CLI.

Earlier revisions of this file held registration smoke-tests; those stayed
under ``test_renderers.py``. This file drives ``build.build(...)`` against
fixture goal dirs and asserts:

* Output ``review.html`` exists under ``<goal_dir>/presentation/``.
* Output is self-contained (no external ``src=file://``/``<link>`` refs).
* Fixture content appears in the rendered HTML.
* Two back-to-back runs produce byte-identical HTML (idempotency).
* The ``runs/latest.md`` log is written with mode/stage fields.
* Mixed-mode (narrative + decisions) folds decision slides under an
  "Open questions" sidebar group.
* Empty / unrenderable source dirs SystemExit with a clear message.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import build  # type: ignore  # noqa: E402


def _sha1(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


# ---------- Registration smoke tests (previously in this file) ----------


def test_import_renderers_registers_all_modes():
    build.RENDERER_REGISTRY.clear()
    build._import_renderers()
    assert "narrative" in build.RENDERER_REGISTRY
    assert "what" in build.RENDERER_REGISTRY
    assert "decisions" in build.RENDERER_REGISTRY


def test_import_renderers_is_idempotent():
    build._import_renderers()
    build._import_renderers()
    assert {"narrative", "what", "decisions"}.issubset(set(build.RENDERER_REGISTRY))


def test_renderers_are_callable():
    build._import_renderers()
    for key in ("narrative", "what", "decisions"):
        assert callable(build.RENDERER_REGISTRY[key])


# ---------- End-to-end builds ----------


def test_build_narrative_end_to_end(copy_fixture, tmp_goal_dir):
    copy_fixture("narrative/narrative.collab.md")
    out = build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    assert out.exists(), "review.html should have been written"
    assert out.name == "review.html"
    assert out.parent == tmp_goal_dir / "presentation"

    html = out.read_text(encoding="utf-8")
    # Self-containment: no external stylesheet/script links.
    assert '<link rel="stylesheet"' not in html
    assert 'src="file:' not in html
    assert 'href="file:' not in html
    # Inline payloads present.
    assert 'id="data-slides"' in html
    assert 'id="data-sidebar"' in html
    assert 'id="data-meta"' in html
    # Fixture content appears somewhere in the embedded slide JSON.
    assert "Agent-Driven Development 101" in html


def test_build_what_end_to_end(copy_fixture, tmp_goal_dir):
    copy_fixture("what")  # copies the whole fixtures/what/ dir
    out = build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    # At least one of the WHAT fixture filenames should surface via source_path.
    assert "01-intro" in html or "02-architecture" in html or "03-roadmap" in html


def test_build_decisions_end_to_end(copy_fixture, tmp_goal_dir):
    copy_fixture("decisions")
    out = build.build(["fixture", "--source-dir", str(tmp_goal_dir), "--stage", "decisions"])
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    # Decision mode emits cards with "Open questions" context; the sidebar
    # JSON carries question ids.
    assert "Q-01" in html
    assert "Q-02" in html
    assert "Q-03" in html


def test_build_mixed_mode_folds_decisions(copy_fixture, tmp_goal_dir):
    """Narrative + decisions/ → single build with folded open-questions group."""
    copy_fixture("narrative/narrative.collab.md")
    copy_fixture("decisions")
    out = build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    # Primary mode stays narrative…
    assert '"mode":"narrative"' in html or "narrative" in html
    # …but the decision questions are present because maybe_fold_decisions ran.
    assert "Q-01" in html


def test_build_emits_runs_log(copy_fixture, tmp_goal_dir):
    copy_fixture("narrative/narrative.collab.md")
    build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    log = AGENT_DIR / "runs" / "latest.md"
    assert log.exists()
    body = log.read_text(encoding="utf-8")
    assert "mode: edit" in body
    assert "stage: narrative" in body


def test_build_empty_source_dir_errors_cleanly(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit) as ei:
        build.build(["fixture", "--source-dir", str(empty)])
    assert "no renderable" in str(ei.value).lower()


# ---------- Idempotency ----------


def test_build_narrative_idempotent(copy_fixture, tmp_goal_dir):
    copy_fixture("narrative/narrative.collab.md")
    out1 = build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    hash1 = _sha1(out1)
    hash2 = _sha1(build.build(["fixture", "--source-dir", str(tmp_goal_dir)]))
    assert hash2 == hash1, "two consecutive builds must produce byte-identical review.html"


def test_build_decisions_idempotent(copy_fixture, tmp_goal_dir):
    copy_fixture("decisions")
    h1 = _sha1(build.build(["fixture", "--source-dir", str(tmp_goal_dir), "--stage", "decisions"]))
    h2 = _sha1(build.build(["fixture", "--source-dir", str(tmp_goal_dir), "--stage", "decisions"]))
    assert h1 == h2


def test_build_isolated_output_dir(copy_fixture, tmp_goal_dir, tmp_path: Path):
    """--output-dir overrides the default <goal_dir>/presentation/ location."""
    copy_fixture("narrative/narrative.collab.md")
    alt = tmp_path / "alt-output"
    out = build.build([
        "fixture",
        "--source-dir", str(tmp_goal_dir),
        "--output-dir", str(alt),
    ])
    assert out == alt / "review.html"
    assert out.exists()
    # Deterministic check: rewriting into the same alt dir is still idempotent.
    h1 = _sha1(out)
    _ = build.build([
        "fixture",
        "--source-dir", str(tmp_goal_dir),
        "--output-dir", str(alt),
    ])
    assert _sha1(out) == h1


def test_build_copied_source_dir_idempotent(copy_fixture, tmp_goal_dir, tmp_path: Path):
    """Re-copying identical source bytes into a new dir yields the same hash.

    Guards against nondeterministic ordering in mixed-mode fold and against
    leaking absolute paths into the emitted JSON.
    """
    copy_fixture("narrative/narrative.collab.md")
    out1 = build.build(["fixture", "--source-dir", str(tmp_goal_dir)])
    content1 = out1.read_bytes()

    other = tmp_path / "goals" / "fixture-goal-2"
    other.mkdir(parents=True)
    shutil.copy2(tmp_goal_dir / "narrative.collab.md", other / "narrative.collab.md")
    out2 = build.build(["fixture", "--source-dir", str(other)])
    content2 = out2.read_bytes()

    # The rendered HTML should not embed the source-dir path, so the two
    # fixtures must hash identically even though they live in different dirs.
    assert content1 == content2
