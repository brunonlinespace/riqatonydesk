#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.7 Markopad Find/Replace convergence gate."""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors: list[str] = []


def req(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def src(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha(relative: str) -> str:
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()


editor = src("widgets/rtf_editor.py")
main = src("widgets/main_window.py")
ribbon = src("widgets/shell_ribbon.py")
init = src("__init__.py")
constants = src("app_constants.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.7"' in init, "0.2.7 package identity missing")
req('APP_REVISION = "0.2.7"' in constants, "0.2.7 revision identity missing")
req('Current release: **0.2.7**' in readme, "root README current release is stale")

# Same Markopad-visible Find/Replace contract as Marko, adapted only to QTextEdit/RTF.
for fragment in (
    'self.search_container = QFrame(self)',
    'search_layout = QGridLayout(self.search_container)',
    'self.search_entry = QLineEdit(self.search_container); self.search_entry.setPlaceholderText("Find")',
    'self.replace_entry = QLineEdit(self.search_container); self.replace_entry.setPlaceholderText("Replace")',
    'self.search_case_checkbox = QCheckBox("Match case", self.search_container)',
    'self.search_previous_button = QPushButton("Previous", self.search_container)',
    'self.search_next_button = QPushButton("Next", self.search_container)',
    'replace_button = QPushButton("Replace", self.search_container)',
    'replace_all_button = QPushButton("Replace All", self.search_container)',
    'close_button = QPushButton("Close", self.search_container)',
    'search_layout.addWidget(self.search_entry, 0, 0, 1, 3)',
    'search_layout.addWidget(self.replace_entry, 1, 0, 1, 3)',
    'self.search_entry.textChanged.connect(self.refresh_search)',
    'self.search_case_checkbox.toggled.connect(self.refresh_search)',
    'self.search_entry.returnPressed.connect(self.find_next)',
    'close_button.clicked.connect(self.hide_find_panel)',
    'self.search_next_button.setShortcut(QKeySequence("F3"))',
    'self.search_previous_button.setShortcut(QKeySequence("Shift+F3"))',
    'self.search_container.hide()',
    'self.main_layout.addWidget(self.visual_editor, 1)',
    'self.main_layout.addWidget(self.search_container, 0)',
    'self.main_layout.addWidget(self.app_status_bar, 0)',
):
    req(fragment in editor, f"Markopad Find/Replace panel contract missing: {fragment}")
req(editor.index('self.main_layout.addWidget(self.visual_editor, 1)') < editor.index('self.main_layout.addWidget(self.search_container, 0)') < editor.index('self.main_layout.addWidget(self.app_status_bar, 0)'),
    "Find/Replace panel is not at the bottom of the editor above its status bar")
for fragment in (
    'QKeySequence.StandardKey.Find',
    'self.search_bar_action.triggered.connect(lambda _checked=False:self.show_find_panel(False))',
    'self.replace_action=self.add_menu_action(menu,"Find and Replace",lambda:self.show_find_panel(True),QKeySequence("Ctrl+H"))',
    'self.dismiss_find_action=QAction("Close Find/Replace",self)',
    'self.dismiss_find_action.setShortcut(QKeySequence("Esc"))',
    'self.dismiss_find_action.triggered.connect(self.hide_find_panel)',
):
    req(fragment in editor, f"Find/Replace shortcut/focus contract missing: {fragment}")
req('Find and Replace — RiqatonyDesk' not in editor, "retired modeless Find/Replace dialog remains")
req('def _replace_dialog_closed' not in editor, "retired Replace-dialog lifecycle remains")

# Gold-all-matches + real selected current hit; no active/passive rendering.
req('sel.format.setBackground(QColor("#C9A227"))' in editor, "Markopad gold search highlight missing")
req('sel.format.setForeground(QColor("#101010"))' in editor, "Markopad search foreground missing")
for forbidden in ('passive_bg', 'active_bg=QColor("#FFD54F")', 'active_bg = QColor("#FFD54F")'):
    req(forbidden not in editor, f"retired active/passive search rendering remains: {forbidden}")
show = re.search(r"def _show_search_match\(self, index\):.*?return True", editor, re.S)
req(show is not None, "_show_search_match missing")
if show:
    body = show.group(0)
    req('cursor = QTextCursor(self.search_matches[self.current_search_index])' in body, "active result does not use stored QTextCursor match")
    req('self.text_area.setTextCursor(cursor)' in body, "active result is not the real QTextEdit selection")
    req('self.text_area.setFocus' not in body and 'self.visual_editor.setFocus' not in body, "Find navigation improperly steals focus")
req('len(self.search_matches) - 1 if self.current_search_index < 0' in editor, "corrected initial Previous wrap behavior missing")
req('MAX_SEARCH_MATCHES = 10_000' in editor, "10,000-match safety bound missing")
req('self._search_refresh_suspended = True' in editor and 'self._search_refresh_suspended = False' in editor,
    "Replace All search-refresh suspension missing")
req('beginEditBlock()' in editor and 'endEditBlock()' in editor, "one-block RTF Replace All contract missing")
req('MAX_DOCUMENT_CHARACTERS' in editor, "Rico document-size replacement guard missing")
req('if not self.document_editing_available()' in editor, "Locked Mode replacement guard missing")

# Exact settings wording and AppMenu radial labels.
for fragment in (
    'setToolTip("Theme — Light")', 'setToolTip("Theme — Dark")', 'setToolTip("Theme — System")',
    'setToolTip("Dashboard — List View")', 'setToolTip("Dashboard — Grid View")',
    'setToolTip("Sidebar — Dock to Left")', 'setToolTip("Sidebar — Dock to Right")',
    'setToolTip("Launch Screen — Dashboard")', 'setToolTip("Launch Screen — Last File")',
    'setToolTip("File Launch — Tabs Enabled")', 'setToolTip("File Launch — Tabs Disabled")',
    '(("left", "Dock to Left"), ("right", "Dock to Right"))',
    'f"Launch Screen — {\'Dashboard\' if launch == \'dashboard\' else \'Last File\'}"',
    'f"Dashboard — {\'Grid View\' if dashboard_mode == \'grid\' else \'List View\'}"',
    'f"File Launch — Tabs {\'Enabled\' if tabs_enabled else \'Disabled\'}"',
):
    req(fragment in main, f"settings tooltip/radial convergence missing: {fragment}")
req('explicit = (action.toolTip() or "").strip()' in ribbon and 'if explicit:' in ribbon and 'return explicit' in ribbon,
    "Rico Ribbon does not preserve explicit state-qualified tooltips")

# Rico must now have the exact same 40-symbol curation as Marko.
tree = ast.parse(editor)
symbols_value = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in {"show_symbols_dialog", "show_symbols_popup"}:
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"symbols", "items"} for t in child.targets):
                try:
                    symbols_value = ast.literal_eval(child.value)
                except Exception:
                    symbols_value = None
                break
        break
expected_symbols = (
    "©", "®", "™", "°", "•", "·", "—", "–", "…", "→", "←", "↑", "↓", "✓", "✗", "§",
    "£", "€", "$", "¥", "¢", "±", "×", "÷", "≠", "≤", "≥", "≈", "∞", "µ", "¶", "№",
    "★", "☆", "♥", "♦", "♣", "♠", "☐", "☑",
)
req(symbols_value == expected_symbols, "Rico Symbols does not exactly match Marko's 40-symbol curation")

# Status bar is expressly outside this release; preserve Rico 0.2.6 ordering.
for fragment in (
    'self.app_status_bar.addWidget(self.operation_mode_label)',
    'self.app_status_bar.addWidget(self.zoom_label)',
    'self.app_status_bar.addWidget(self.counter_label)',
    'self.app_status_bar.addWidget(self.status_message_label, 1)',
):
    req(fragment in editor, f"out-of-scope Rico editor-status structure changed: {fragment}")

# Protect major file/lifecycle/RTF-codec infrastructure from opportunistic edits.
protected = {
    "controllers/editor_manager.py": "bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894",
    "controllers/file_actions.py": "600159f96519d10df52bd98cc4dee808b11cc0730ab903b2661d15ebc3fba387",
    "services/open_document_monitor.py": "25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
    "services/filesystem_watcher.py": "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "services/document_scanner.py": "8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
    "models/document_repository.py": "e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f",
    "widgets/dashboard.py": "ca3cb7c8acc4e21270369d15bb6797ed225602cf43f952c9d5aa63140adb3619",
    "widgets/dashboard_card.py": "f077cc621e797847435f84de793b685395bdfb2d70a0d1b5229814d4e27bea9e",
    "widgets/navigation.py": "60995adf7c41e2d8ef12a266a3d712b2b59cc5e8535a2e35d1ac2a6cfe468ce6",
    "widgets/resolve_open_documents_dialog.py": "38657cbfaf21ab286cb58dc2cd8fac43b2b562d270629d98276274d68c17047e",
    "services/config_service.py": "b4d72c5a9ac37d02b537c3fd8b83892b8ba01e22b5e339a14c4f65273e072e7e",
    "rtf_codec.py": "34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
    "rich_text_support.py": "6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb",
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.7 check failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.7 Markopad Find/Replace + settings/symbol convergence contract")
