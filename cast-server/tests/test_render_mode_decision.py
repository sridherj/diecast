"""Pure mode-decision unit tests — HOW-update-mode Sub-phase 3a.

`render_job_service.decide_mode` is the pure, I/O-free CREATE-vs-UPDATE contract (shared-context
"Mode decision" block). UPDATE iff ALL preconditions hold; EVERY failure degrades to CREATE with a
non-empty note — never a job error (CREATE is always a safe answer). These tests pin every threshold
boundary + every independent degrade-to-CREATE path, asserting the note is always present on a CREATE.

They are pure (no DB, no fixture) — the decision function takes only scalars, so the boundaries are
testable without a render job.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

import cast_server.config as config  # noqa: E402
from cast_server.services.render_job_service import decide_mode  # noqa: E402


def _update_kwargs(**overrides) -> dict:
    """The all-preconditions-hold UPDATE happy-path inputs; override one field per test to force a
    single degrade path. Thresholds are passed explicitly so the boundary is unambiguous."""
    base = dict(
        prior_html="<html>prior render</html>",
        prior_served_by="maker",
        prior_human_review=False,
        prior_source="# Goal\n\nprior source text",
        changed_fraction=0.2,
        prior_render_bytes=1000,
        workflow_family_changed=False,
        max_changed_fraction=0.4,
        max_prior_bytes=10_000,
    )
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Happy path                                                                   #
# --------------------------------------------------------------------------- #
def test_update_happy_path_all_preconditions_hold():
    mode, note = decide_mode(**_update_kwargs())
    assert mode == "update"
    assert note is None


# --------------------------------------------------------------------------- #
# Each precondition independently forces CREATE (with a non-empty note)        #
# --------------------------------------------------------------------------- #
def test_missing_prior_render_forces_create():
    mode, note = decide_mode(**_update_kwargs(prior_html=None))
    assert mode == "create"
    assert note  # non-empty


def test_missing_prior_source_forces_create():
    mode, note = decide_mode(**_update_kwargs(prior_source=None))
    assert mode == "create"
    assert note


def test_flagged_prior_served_by_not_maker_forces_create():
    for served_by in ("structural_violation", "fallback", "deterministic", None):
        mode, note = decide_mode(**_update_kwargs(prior_served_by=served_by))
        assert mode == "create", served_by
        assert note


def test_human_review_prior_forces_create():
    # served-by is maker but the prior render was flagged for human review → never UPDATE from it.
    mode, note = decide_mode(**_update_kwargs(prior_served_by="maker", prior_human_review=True))
    assert mode == "create"
    assert note


def test_workflow_family_changed_forces_create():
    mode, note = decide_mode(**_update_kwargs(workflow_family_changed=True))
    assert mode == "create"
    assert note


# --------------------------------------------------------------------------- #
# Threshold boundaries (just under → UPDATE, just over → CREATE)               #
# --------------------------------------------------------------------------- #
def test_changed_fraction_at_threshold_is_update():
    # `<=` boundary is inclusive: exactly at the threshold still UPDATEs.
    mode, note = decide_mode(**_update_kwargs(changed_fraction=0.4, max_changed_fraction=0.4))
    assert mode == "update"
    assert note is None


def test_changed_fraction_just_over_threshold_forces_create():
    mode, note = decide_mode(**_update_kwargs(changed_fraction=0.41, max_changed_fraction=0.4))
    assert mode == "create"
    assert note


def test_prior_render_bytes_at_threshold_is_update():
    mode, note = decide_mode(**_update_kwargs(prior_render_bytes=10_000, max_prior_bytes=10_000))
    assert mode == "update"
    assert note is None


def test_prior_render_bytes_just_over_threshold_forces_create():
    mode, note = decide_mode(**_update_kwargs(prior_render_bytes=10_001, max_prior_bytes=10_000))
    assert mode == "create"
    assert note


# --------------------------------------------------------------------------- #
# Thresholds default from config when not passed                              #
# --------------------------------------------------------------------------- #
def test_thresholds_default_from_config():
    # No explicit thresholds → the config defaults (0.4 / 600_000) apply. A tiny change + small page
    # under both defaults → UPDATE.
    mode, note = decide_mode(
        prior_html="x" * 100,
        prior_served_by="maker",
        prior_human_review=False,
        prior_source="src",
        changed_fraction=0.1,
        prior_render_bytes=100,
        workflow_family_changed=False,
    )
    assert mode == "update"
    assert note is None
    # And the config knobs exist with the documented starting values.
    assert config.RENDER_UPDATE_MAX_CHANGED_FRACTION == 0.4
    assert config.RENDER_UPDATE_MAX_PRIOR_BYTES == 600_000


def test_every_create_carries_a_nonempty_note():
    """The shared-context invariant: every degrade-to-CREATE carries a reason (zero silent
    failures). Exercise each independent CREATE trigger and assert a non-empty note string."""
    create_cases = [
        _update_kwargs(prior_html=None),
        _update_kwargs(prior_served_by="fallback"),
        _update_kwargs(prior_human_review=True),
        _update_kwargs(prior_source=None),
        _update_kwargs(workflow_family_changed=True),
        _update_kwargs(changed_fraction=0.99, max_changed_fraction=0.4),
        _update_kwargs(prior_render_bytes=10_001, max_prior_bytes=10_000),
    ]
    for kwargs in create_cases:
        mode, note = decide_mode(**kwargs)
        assert mode == "create"
        assert isinstance(note, str) and note.strip()
