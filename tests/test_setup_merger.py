import os
from pathlib import Path
import sys

import yaml

_CAST_SERVER = Path(__file__).resolve().parent.parent / "cast-server"
if str(_CAST_SERVER) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER))

from cast_server.bootstrap.setup_flow import _merge_config


def _merge_with_repo_env(cfg: Path, terminal_seed: str) -> dict:
    old_repo = os.environ.get("REPO_DIR")
    os.environ["REPO_DIR"] = str(Path(__file__).resolve().parents[1])
    try:
        _merge_config(cfg, terminal_seed)
    finally:
        if old_repo is None:
            os.environ.pop("REPO_DIR", None)
        else:
            os.environ["REPO_DIR"] = old_repo
    return yaml.safe_load(cfg.read_text())


def test_setup_merger_migrates_terminal_alias(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal": "kitty"}))

    data = _merge_with_repo_env(cfg, "gnome-terminal")

    assert data["terminal_default"] == "kitty"
    assert "terminal" not in data


def test_setup_merger_preserves_terminal_default(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal": "kitty", "terminal_default": "alacritty"}))

    data = _merge_with_repo_env(cfg, "gnome-terminal")

    assert data["terminal_default"] == "alacritty"
    assert "terminal" not in data


def test_setup_merger_uses_seed_for_fresh_config(tmp_path):
    cfg = tmp_path / "config.yaml"

    data = _merge_with_repo_env(cfg, "gnome-terminal")

    assert data["terminal_default"] == "gnome-terminal"
    assert "terminal" not in data
