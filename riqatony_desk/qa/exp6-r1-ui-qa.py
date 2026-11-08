#!/usr/bin/env python3
"""Dependency-free regression checks for RiqatonyDesk 0.0.4-exp6-r1 UI refinements."""
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
main = (PACKAGE / "widgets/main_window.py").read_text(encoding="utf-8")
ribbon = (PACKAGE / "widgets/shell_ribbon.py").read_text(encoding="utf-8")
editor = (PACKAGE / "widgets/rtf_editor.py").read_text(encoding="utf-8")
editor += '\n' + (PACKAGE / 'widgets' / 'editor_commands_appearance.py').read_text(encoding='utf-8')
page = (PACKAGE / "widgets/editor_page.py").read_text(encoding="utf-8")
config = (PACKAGE / "services/config_service.py").read_text(encoding="utf-8")

def require(value, message):
    if not value:
        raise AssertionError(message)

# Text Colour shortcut is aligned in shell and embedded editor source.
require('self.text_colour_action=self._editor_command("Text Colour…","text_colour_action","Ctrl+Shift+C")' in main, "Shell Text Colour shortcut is not Ctrl+Shift+C")
require('self.text_colour_action=add("Text Colour…",self.choose_text_colour,QKeySequence("Ctrl+Shift+C"))' in editor, "Embedded Text Colour shortcut is not Ctrl+Shift+C")
require('Ctrl+Alt+Shift+C' not in main + editor, "Retired Text Colour shortcut remains")

# Theme order: default first, consistently in AppMenu and Ribbon.
require('for value, label in (\n            ("light", "Light"),\n            ("dark", "Dark"),\n            ("system", "System"),' in main, "Theme QAction creation order is not Light/Dark/System")
for key in ("Ctrl+Alt+Shift+1", "Ctrl+Alt+Shift+2", "Ctrl+Alt+Shift+3"):
    require(key not in main[main.index("current_theme ="):main.index("current_icons =")], f"App Theme still owns {key}")
require('for n in ("light","dark","system"): theme.addAction(self.theme_actions[n])' in main, "App Theme menu order is not Light/Dark/System")
for token in ('("theme_light_action", 1, 0)', '("theme_dark_action", 1, 1)', '("theme_system_action", 1, 2)'):
    require(token in ribbon, f"Ribbon theme order missing {token}")

# Insert AppMenu exact outer order.
insert_sequence = '''        self.insert_menu.addAction(self.image_action)\n        links=self.insert_menu.addMenu("Link"); links.addAction(self.link_action); links.addAction(self.edit_link_action); links.addSeparator(); links.addAction(self.remove_link_action)\n        self.insert_menu.addSeparator(); self.insert_menu.addAction(self.table_action)\n        table=self.insert_menu.addMenu("Table Editing")\n        for a in (self.table_row_above_action,self.table_row_below_action,self.table_delete_row_action,self.table_column_left_action,self.table_column_right_action,self.table_delete_column_action,self.table_delete_action): table.addAction(a)\n        self.insert_menu.addSeparator()\n        for a in (self.date_time_action,self.date_action,self.time_action): self.insert_menu.addAction(a)\n        self.insert_menu.addSeparator(); self.insert_menu.addAction(self.rule_action); self.insert_menu.addAction(self.symbol_action)'''
require(insert_sequence in main, "Insert AppMenu order is not the exp6-r1 contract")

# Insert Ribbon exact reviewed placement.
require('self._group(p, "Images & Links")' in ribbon, "Images & Links group label missing")
for token in (
    '("edit_link_action", 0, 0)', '("remove_link_action", 0, 1)',
    '("image_action", 1, 0)', '("link_action", 1, 1)',
    '("date_action", 0, 0)', '("time_action", 0, 1)', '("clear_formatting_action", 0, 2)',
    '("date_time_action", 1, 0)', '("rule_action", 1, 1)', '("symbol_action", 1, 2)',
):
    require(token in ribbon, f"Insert Ribbon placement missing {token}")

# Ricopad-authoritative dirty marker is visible in the MainWindow title even with tabs hidden.
require('dirty_prefix = "*" if document.dirty else ""' in main, "Dirty title prefix missing")
require('f"{dirty_prefix}{document.filename} — {scope} — {APP_NAME}{lock_suffix}"' in main, "Window title does not use dirty prefix")
update_tab = main.split('def _update_document_tab', 1)[1].split('def _rebind_document_tab', 1)[0]
require('self._update_window_title()' in update_tab and update_tab.index('self._update_window_title()') < update_tab.index('if index < 0:'), "Dirty title refresh still depends on a visible tab")

# Locked Mode confirmation can be suppressed persistently from its own dialog.
require('"confirm_locked_mode_disable": True' in config, "Locked Mode confirmation default missing")
require('managed_locked_mode_prompt_provider=self._confirm_locked_mode_disable' in page, "Managed Locked Mode confirmation provider missing")
require('managed_locked_mode_prompt_setter=self._set_confirm_locked_mode_disable' in page, "Managed Locked Mode confirmation setter missing")
require('QCheckBox("Don\'t ask again when disabling Locked Mode",dialog)' in editor, "Locked Mode checkbox missing")
require('dialog.setCheckBox(dont_ask)' in editor, "Locked Mode checkbox not attached to dialog")
require('if dont_ask.isChecked()' in editor and 'prompt_setter(False)' in editor, "Locked Mode checkbox does not persist suppression")

# Previously reviewed exp5-r1 placement contracts remain intact.
require('self.workspace_menu.addAction(self.manage_workspaces_action)\n        self.workspace_menu.addSeparator()' in main, "Workspace management placement regressed")
require('self.workspace_menu.addAction(self.new_window_action)' not in main, "New Window must not remain inside Workspace(s)")
require('self.view_menu.addAction(self.collapsed_mode_action)' not in main, "Focused Mode returned to View")

print("PASS: exp6-r1 UI/shortcut/title regression QA")
