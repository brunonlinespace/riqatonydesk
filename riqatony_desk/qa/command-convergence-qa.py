#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.0.5 command-convergence gate."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "widgets" / "main_window.py").read_text(encoding="utf-8")
editor = (root / "widgets" / "rtf_editor.py").read_text(encoding="utf-8")
editor += '\n' + (root / 'widgets' / 'editor_commands_appearance.py').read_text(encoding='utf-8')
ribbon = (root / "widgets" / "shell_ribbon.py").read_text(encoding="utf-8")

expected_main = (
    'self.export_pdf_action = self._command("Export PDF…", lambda: self._editor_call("export_pdf"), "Ctrl+Alt+Shift+P")',
    'self.highlight_colour_action=self._editor_command("Highlight Colour…","highlight_colour_action","Ctrl+Shift+H")',
    'self.paragraph_action=self._editor_command("Paragraph…","paragraph_action","Ctrl+Shift+P")',
    'self.rule_action=self._editor_command("Horizontal Rule","horizontal_rule_action","Ctrl+Alt+Shift+H")',
)
expected_editor = (
    'self.export_pdf_action = self.add_menu_action(menu, "Export PDF…", self.export_pdf, QKeySequence("Ctrl+Alt+Shift+P"))',
    'self.horizontal_rule_action=self.add_menu_action(menu,"Horizontal Rule",self.insert_horizontal_rule,QKeySequence("Ctrl+Alt+Shift+H"))',
    'self.highlight_colour_action=add("Highlight Colour…",self.choose_highlight_colour,QKeySequence("Ctrl+Shift+H"))',
    'self.paragraph_action=add("Paragraph…",self.show_paragraph_dialog,QKeySequence("Ctrl+Shift+P"))',
)
for fragment in expected_main:
    assert fragment in main, fragment
for fragment in expected_editor:
    assert fragment in editor, fragment

old_main = (
    '"Export PDF…", lambda: self._editor_call("export_pdf"), "Ctrl+Shift+P"',
    '"Highlight Colour…","highlight_colour_action","Ctrl+Alt+Shift+H"',
    '"Paragraph…","paragraph_action","Ctrl+Alt+Shift+P"',
    '"Horizontal Rule","horizontal_rule_action","Ctrl+Shift+H"',
)
old_editor = (
    'self.export_pdf_action = self.add_menu_action(menu, "Export PDF…", self.export_pdf, QKeySequence("Ctrl+Shift+P"))',
    'self.horizontal_rule_action=self.add_menu_action(menu,"Horizontal Rule",self.insert_horizontal_rule,QKeySequence("Ctrl+Shift+H"))',
    'self.highlight_colour_action=add("Highlight Colour…",self.choose_highlight_colour,QKeySequence("Ctrl+Alt+Shift+H"))',
    'self.paragraph_action=add("Paragraph…",self.show_paragraph_dialog,QKeySequence("Ctrl+Alt+Shift+P"))',
)
for fragment in old_main:
    assert fragment not in main, fragment
for fragment in old_editor:
    assert fragment not in editor, fragment

menu_order = 'self.view_menu.addAction(self.fullscreen_action); self.view_menu.addAction(self.status_bar_action); self.view_menu.addSeparator()'
assert menu_order in main, menu_order
assert 'self.view_menu.addAction(self.sidebar_action)' not in main
view_control = '("fullscreen_action", 0, 0),\n            ("status_bar_action", 0, 1),\n            ("collapsed_mode_action", 0, 2),'
assert view_control in ribbon, view_control
assert 'g, "sidebar_action", 1, 0,' in ribbon
assert 'menu_actions=("sidebar_action", None, "left_sidebar_action", "right_sidebar_action")' in ribbon

print("PASS: RiqatonyDesk 0.0.5 shared command and View-order convergence")
