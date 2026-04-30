"""Render-fragment tests for the L/XL "consider splitting" affordance (US10).

Phase 3b sp8 — exercise ``fragments/task_item.html`` against a minimal task
shape and assert the ``Split?`` warn renders only when ``estimate_size`` is
``L`` or ``XL``. The dummy task is a plain object whose attribute surface is
a strict subset of what the template touches; ``is defined`` guards in the
template let the missing-field case fall through cleanly.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "cast_server" / "templates"


def _make_task(**overrides):
    defaults = {
        "id": 1,
        "title": "x",
        "status": "pending",
        "phase": None,
        "recommended_agent": None,
        "active_run": None,
        "last_run": None,
        "subtasks": None,
        "tip": None,
        "outcome": None,
        "task_type": None,
        "estimated_time": None,
        "energy": None,
        "assigned_to": None,
        "task_artifacts": None,
        "parent_id": None,
        "goal_slug": "g",
    }
    defaults.update(overrides)
    return type("T", (), defaults)()


def _render(task):
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
    tmpl = env.get_template("fragments/task_item.html")
    return tmpl.render(task=task)


def test_l_renders_warn():
    out = _render(_make_task(estimate_size="L"))
    assert "Split?" in out
    assert ">L<" in out


def test_xl_renders_warn():
    out = _render(_make_task(estimate_size="XL"))
    assert "Split?" in out
    assert ">XL<" in out


def test_m_renders_pill_no_warn():
    out = _render(_make_task(estimate_size="M"))
    assert "Split?" not in out
    assert ">M<" in out


def test_missing_field_renders_neither():
    out = _render(_make_task())
    assert "Split?" not in out
    assert "estimate-pill" not in out
