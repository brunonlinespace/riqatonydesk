#!/usr/bin/env python3
"""Qt-free x16.4 drop-highlight regression and x16.3 preservation contract."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
ref = json.loads((ROOT / "qa/x164-preservation.json").read_text(encoding="utf-8"))
assert ref["baseline"] == "1.0.0-x16.3" and ref["edition"] == "1.0.0-x16.4"

# All production modules not part of the two approved methods must remain byte-identical.
for rel, digest in ref["unchanged_production_sha256"].items():
    actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    assert actual == digest, f"Unapproved production change in {rel}"

# Version-only modules must retain their exact old content after reversing the edition bump.
for rel, digest in ref["original_version_modules"].items():
    data = (ROOT / rel).read_text(encoding="utf-8")
    assert "1.0.0-x16.4" in data, f"Version not bumped in {rel}"
    old_data = data.replace("1.0.0-x16.4", "1.0.0-x16.3")
    assert hashlib.sha256(old_data.encode()).hexdigest() == digest, f"Other change in {rel}"


def isolated_method(rel: str, class_name: str):
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    candidates = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
    assert len(candidates) == 1, (rel, class_name)
    cls = candidates[0]
    candidates = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "_set_drop_highlight"]
    assert len(candidates) == 1, (rel, "method")
    method = candidates[0]
    # Everything else, including dragEnter/Move/Leave/drop handlers and CSS context, stays identical.
    method.body = [ast.Pass()]
    digest = hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()
    assert digest == ref["modified_method_containers"][rel], f"Unapproved change outside target method in {rel}"
    method = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    method = next(n for c in method.body if isinstance(c, ast.ClassDef) and c.name == class_name
                  for n in c.body if isinstance(n, ast.FunctionDef) and n.name == "_set_drop_highlight")
    assert len(method.args.args) == 2 and method.args.args[0].arg == 'self'
    code = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = {'QPalette': SimpleNamespace(ColorRole=SimpleNamespace(Highlight=7))}
    exec(compile(code, rel, "exec"), namespace)
    return namespace['_set_drop_highlight']


class FakePalette:
    def __init__(self, widget):
        self.widget = widget
    def color(self, role):
        assert role == 7
        return SimpleNamespace(name=lambda: self.widget.highlight_color)


class FakeWidget:
    def __init__(self):
        self.current_style = ""
        self.style_calls = []
        self.highlight_color = "#2277aa"
    def palette(self):
        return FakePalette(self)
    def styleSheet(self):
        return self.current_style
    def setStyleSheet(self, style):
        self.current_style = style
        self.style_calls.append(style)


for rel, klass in [("widgets/workspace/dashboard.py", "DashboardWidget"),
                   ("widgets/workspace/folder_dashboard.py", "FolderDashboard")]:
    call = isolated_method(rel, klass)
    widget = FakeWidget()
    # No-op off-state must not call Qt's stylesheet repolisher.
    for _ in range(1500):
        call(widget, False)
    assert widget.style_calls == [], (klass, "inactive")
    # First valid drag highlights once. Every subsequent drag move is a no-op.
    for _ in range(1500):
        call(widget, True)
    active = f"{klass} {{ border: 2px solid #2277aa; }}"
    assert widget.style_calls == [active], (klass, "drag moves", widget.style_calls)
    # Repainting only if an actual palette-change requires a distinct style.
    widget.highlight_color = "#ee3311"
    call(widget, True)
    assert widget.style_calls == [active, f"{klass} {{ border: 2px solid #ee3311; }}"]
    call(widget, True)
    assert len(widget.style_calls) == 2
    # A drag-leave/drop clears exactly once; subsequent clears do not repolish.
    for _ in range(1500):
        call(widget, False)
    assert widget.style_calls == [active, f"{klass} {{ border: 2px solid #ee3311; }}", ""]
    call(widget, True)
    assert len(widget.style_calls) == 4
    # Guard must preserve the incoming style if no adjustment is necessary.
    widget.current_style = f"{klass} {{ border: 2px solid #ee3311; }}"
    call(widget, True)
    assert len(widget.style_calls) == 4

print("PASS x16.4: only two approved methods changed; repeat drag moves no longer repolish; exact CSS/clear/palette transitions preserved")
