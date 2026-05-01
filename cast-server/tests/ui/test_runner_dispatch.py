"""Lightweight unit tests for runner.py dispatch logic.

The per-screen `_assert_*` functions require a live UI so they are not unit-tested
here — they're covered by the e2e harness in sp5. These tests pin the public surface
of runner.py: dispatch keys, screen-name normalization, and CLI behavior.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_RUNNER_PATH = Path(__file__).parent / "runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("diecast_ui_runner", _RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


def test_dispatch_keys_are_seven_screens(runner):
    expected = {
        "dashboard",
        "agents",
        "runs",
        "scratchpad",
        "goal_detail",
        "focus",
        "about",
    }
    assert set(runner.SCREEN_DISPATCH.keys()) == expected


def test_norm_screen_dash_to_underscore(runner):
    assert runner._norm_screen("goal-detail") == "goal_detail"
    assert runner._norm_screen("dashboard") == "dashboard"
    assert runner._norm_screen("about") == "about"


def test_main_rejects_unknown_screen(runner, tmp_path):
    out = tmp_path / "x.json"
    rc = runner.main(
        ["--screen=nope", "--goal-slug=x", f"--output={out}"]
    )
    assert rc == 2


def test_user_data_dir_prefix_matches_sweep_pattern(runner):
    """The teardown sweep in sp2 matches the substring 'diecast-uitest'."""
    assert "diecast-uitest" in runner.USER_DATA_DIR_PREFIX


def test_assertion_timeout_is_30s(runner):
    assert runner.ASSERTION_TIMEOUT_MS == 30_000
