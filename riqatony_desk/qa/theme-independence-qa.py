#!/usr/bin/env python3
"""Validate exp5 application/editor theme independence and legacy migration."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

source = Path(__file__).resolve().parents[2]
if str(source) not in sys.path:
    sys.path.insert(0, str(source))

from riqatony_desk.services.config_service import ConfigService

package = Path(__file__).resolve().parents[1]
main = (package / "widgets/main_window.py").read_text(encoding="utf-8")
page = (package / "widgets/editor_page.py").read_text(encoding="utf-8")
editor = (package / "widgets/rtf_editor.py").read_text(encoding="utf-8")
config_source = (package / "services/config_service.py").read_text(encoding="utf-8")

assert '"app_theme": "light"' in config_source
assert '"editor_canvas_light": True' in config_source
assert '"editor_canvas_follows_app_theme"' not in ConfigService.DEFAULTS
assert 'self.config.set("editor_canvas_light", not bool(checked), save=True)' in main
assert 'self.config.get("editor_canvas_follows_app_theme"' not in main
assert 'self.config.get("editor_canvas_follows_app_theme"' not in page
assert 'managed_canvas_light_provider=self._canvas_is_light' in page
assert 'data["editor_canvas_theme"]' not in editor
assert 'saved_canvas = preference_text(data, "editor_canvas_theme"' not in editor

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "config.json"
    path.write_text(json.dumps({
        "app_theme": "dark",
        "editor_canvas_follows_app_theme": True,
        "editor_canvas_light": None,
    }), encoding="utf-8")
    cfg = ConfigService(path)
    assert cfg.get("app_theme") == "dark", "existing app theme must be preserved"
    assert cfg.get("editor_canvas_light") is True, "legacy null canvas migrates to light"
    assert cfg.get("editor_canvas_follows_app_theme") is None, "retired follow key remains live"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert "editor_canvas_follows_app_theme" not in saved
    assert saved["editor_canvas_light"] is True

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "config.json"
    path.write_text(json.dumps({
        "app_theme": "system",
        "editor_canvas_follows_app_theme": False,
        "editor_canvas_light": False,
    }), encoding="utf-8")
    cfg = ConfigService(path)
    assert cfg.get("app_theme") == "system", "existing app theme must be preserved"
    assert cfg.get("editor_canvas_light") is False, "explicit dark editor must be preserved"

print("Theme independence QA: PASS")
