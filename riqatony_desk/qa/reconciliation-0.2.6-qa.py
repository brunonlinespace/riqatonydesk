#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.6 focused convergence release gate."""
from pathlib import Path
PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
init=src("__init__.py"); constants=src("app_constants.py"); main=src("widgets/main_window.py"); ribbon=src("widgets/shell_ribbon.py"); editor=src("widgets/rtf_editor.py"); readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.6"' in init, "0.2.6 package identity missing")
req('APP_REVISION = "0.2.6"' in constants, "0.2.6 revision identity missing")
req('Current release: **0.2.6**' in readme, "root README current release is stale")
# Shift+F9 is a non-menu shortcut over the existing position state.
for f in ('"Toggle Sidebar Position", self._toggle_sidebar_position, "Shift+F9"','def _toggle_sidebar_position(self)','self._set_sidebar_position("left" if current == "right" else "right")','("Toggle Sidebar Position", self.toggle_sidebar_position_action)'):
    req(f in main, f"Shift+F9 sidebar convergence missing: {f}")
# Workspace(s) owns icon/Ribbon menu; Open/Manage stays text-only in its menu.
for f in ('self.workspace_tabbed_action=self.workspace_menu.menuAction()','"workspace_tabbed_action":"manage-workspaces"','"workspace_tabbed_action"'):
    req(f in main, f"Workspace(s) container convergence missing: {f}")
req('"manage_workspaces_action":"manage-workspaces"' not in main, "Open / Manage Workspaces still owns workspace icon")
req('(\"workspace_tabbed_action\", 0, 1)' in ribbon, "Ribbon still uses direct Open / Manage Workspaces action")
req('self.workspace_menu.addAction(self.manage_workspaces_action)' in main, "Open / Manage Workspaces missing from shared Workspace(s) menu")
# Six agreed symbol additions, no Marko-only star additions slipped into Rico.
for symbol in ('♥','♦','♣','♠','☐','☑'):
    req(f'"{symbol}"' in editor, f"missing Symbols addition: {symbol}")
req('"★"' not in editor and '"☆"' not in editor, "unapproved Marko-only star symbols were added to Rico")
# Find parity: fresh success immediately has current index 0 and existing gold painter stays authoritative.
req('self.current_search_index = 0' in editor, "fresh Find does not establish first active result")
req('active_bg=QColor("#FFD54F")' in editor, "gold active Find highlight changed")
req('self.refresh_search_highlights(); self.update_search_counter()' in editor, "Find highlight/counter refresh contract changed")
# Status bar intentionally not part of this release.
req('self.app_status_bar.addWidget(self.operation_mode_label)' in editor, "status-bar structure unexpectedly changed")
if errors:
    print("RiqatonyDesk 0.2.6 check failed:")
    for e in errors: print("- "+e)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.6 focused convergence contract")
