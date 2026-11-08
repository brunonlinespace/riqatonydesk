#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.8 Find/Replace keyboard/counter gate."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
editor=src("widgets/rtf_editor.py")
page=src("widgets/editor_page.py")
main=src("widgets/main_window.py")
init=src("__init__.py")
constants=src("app_constants.py")
readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.8"' in init, "0.2.8 package identity missing")
req('APP_REVISION = "0.2.8"' in constants, "0.2.8 revision identity missing")
req('Current release: **0.2.8**' in readme, "README current release stale")
# Accepted bottom-panel/search presentation stays unchanged.
for f in (
    'self.search_container = QFrame(self)', 'self.search_entry.setPlaceholderText("Find")',
    'self.replace_entry.setPlaceholderText("Replace")', 'self.search_entry.returnPressed.connect(self.find_next)',
    'close_button.clicked.connect(self.hide_find_panel)', 'sel.format.setBackground(QColor("#C9A227"))',
    'sel.format.setForeground(QColor("#101010"))',
): req(f in editor, f"accepted Find/Replace contract missing: {f}")
for forbidden in ('passive_bg', 'active_bg = QColor("#FFD54F")', 'Find and Replace — RiqatonyDesk'):
    req(forbidden not in editor, f"retired search model returned: {forbidden}")
# Embedded Ricopad actions remain scrubbed; transient search keys are rebuilt on outer EditorPage.
req('for action in self._surface.findChildren(QAction):' in page and 'action.setShortcut(QKeySequence())' in page,
    'embedded shortcut scrubber changed')
for f in (
    'self.find_next_shortcut_action.setShortcut(QKeySequence("F3"))',
    'self.find_previous_shortcut_action.setShortcut(QKeySequence("Shift+F3"))',
    'self.dismiss_find_shortcut_action.setShortcut(QKeySequence("Esc"))',
    'self.find_next_shortcut_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)',
    'self.find_previous_shortcut_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)',
    'self.dismiss_find_shortcut_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)',
    'self.addAction(self.find_next_shortcut_action)',
    'self.addAction(self.find_previous_shortcut_action)',
    'self.addAction(self.dismiss_find_shortcut_action)',
): req(f in page, f"outer EditorPage shortcut contract missing: {f}")
req('self.search_next_button.setShortcut(QKeySequence("F3"))' not in editor, 'F3 still incorrectly owned by panel button')
req('self.search_previous_button.setShortcut(QKeySequence("Shift+F3"))' not in editor, 'Shift+F3 still incorrectly owned by panel button')
# Ctrl+F/Ctrl+H use the same focus-aware inner toggle.
toggle=re.search(r'def toggle_find_panel\(self, replace=False\):.*?return True', editor, re.S)
req(toggle is not None, 'toggle_find_panel missing')
if toggle:
    body=toggle.group(0)
    req('target = self.replace_entry if replace else self.search_entry' in body, 'toggle does not select requested field')
    req('self.search_container.isVisible() and target.hasFocus()' in body, 'toggle is not focus-aware')
    req('self.hide_find_panel()' in body and 'self.show_find_panel(replace)' in body, 'toggle open/close routing incomplete')
req('page.call_editor("toggle_find_panel", False)' in main, 'Ctrl+F does not route through focus-aware toggle')
req('page.call_editor("toggle_find_panel", True)' in main, 'Ctrl+H does not route through focus-aware toggle')
# X/Y positional counter and first active selected result.
for f in (
    'current = self.current_search_index + 1 if 0 <= self.current_search_index < total else 0',
    'total_text = f"{total:,}+" if self.search_results_truncated else f"{total:,}"',
    'self.search_count_label.setText(f"{current:,}/{total_text}")',
    'self.current_search_index = 0',
    'active_cursor = QTextCursor(self.search_matches[0])',
    'self.update_search_counter()\n        return True',
): req(f in editor, f"X/Y active-position contract missing: {f}")
# Retain exact 40-symbol curation and untouched codec/lifecycle core.
for symbol in ('"★"','"☆"','"♥"','"♦"','"♣"','"♠"','"☐"','"☑"'):
    req(symbol in editor, f"symbol convergence regressed: {symbol}")
protected={
"controllers/editor_manager.py":"bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894",
"controllers/file_actions.py":"600159f96519d10df52bd98cc4dee808b11cc0730ab903b2661d15ebc3fba387",
"services/open_document_monitor.py":"25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
"services/filesystem_watcher.py":"655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
"services/document_scanner.py":"8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
"models/document_repository.py":"e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f",
"services/config_service.py":"b4d72c5a9ac37d02b537c3fd8b83892b8ba01e22b5e339a14c4f65273e072e7e",
"rtf_codec.py":"34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
"rich_text_support.py":"6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb",
}
for r,h in protected.items(): req(sha(r)==h, f"protected out-of-scope file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.8 check failed:")
    for e in errors: print(f"- {e}")
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.8 Find/Replace keyboard + X/Y counter contract")
