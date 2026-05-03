import subprocess
from pathlib import Path
import yaml
import sys
import re

def test_setup_merger(tmp_path):
    # Extract the inline Python merger script from setup
    setup_script = Path("setup").read_text()
    match = re.search(r"cat > \"\$\{merger\}\" <<'PY'\n(.*?)\nPY", setup_script, re.DOTALL)
    assert match is not None, "Could not find Python merger script in setup"
    py_code = match.group(1)
    
    merger_script = tmp_path / "merger.py"
    merger_script.write_text(py_code)
    
    cfg = tmp_path / "config.yaml"
    
    # Scenario 1: Fresh install, terminal detected
    subprocess.run([sys.executable, str(merger_script), str(cfg), "gnome-terminal"], check=True)
    data = yaml.safe_load(cfg.read_text())
    assert data["terminal_default"] == "gnome-terminal"
    assert "terminal" not in data
    
    # Scenario 2: Legacy config with terminal alias gets migrated cleanly
    cfg.write_text(yaml.safe_dump({"terminal": "kitty"}))
    subprocess.run([sys.executable, str(merger_script), str(cfg), "gnome-terminal"], check=True)
    data = yaml.safe_load(cfg.read_text())
    assert data["terminal_default"] == "kitty"  # migrated!
    assert "terminal" not in data  # old key removed!
    
    # Scenario 3: Legacy config with both terminal and terminal_default keeps terminal_default
    cfg.write_text(yaml.safe_dump({"terminal": "kitty", "terminal_default": "alacritty"}))
    subprocess.run([sys.executable, str(merger_script), str(cfg), "gnome-terminal"], check=True)
    data = yaml.safe_load(cfg.read_text())
    assert data["terminal_default"] == "alacritty"
    assert "terminal" not in data
