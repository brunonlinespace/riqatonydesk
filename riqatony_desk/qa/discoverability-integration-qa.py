#!/usr/bin/env python3
"""RiqatonyDesk 0.1.4 discoverability/integration metadata contract."""
from pathlib import Path
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
main = (PACKAGE / "widgets/main_window.py").read_text(encoding="utf-8")
dashboard = (PACKAGE / "widgets/dashboard.py").read_text(encoding="utf-8")
folder = (PACKAGE / "widgets/folder_dashboard.py").read_text(encoding="utf-8")
meta_path = PACKAGE / "packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml"

def require(fragment: str, label: str) -> None:
    if fragment not in main:
        raise SystemExit(f"FAIL: {label}")

def forbid(fragment: str, label: str) -> None:
    if fragment in main:
        raise SystemExit(f"FAIL: {label}")

for fragment, label in (
    ('"Dashboard", self.editor_manager.show_dashboard', 'Dashboard label'),
    ('"Import File into Workspace...", self._import_file_into_workspace', 'Import File action'),
    ('def _import_file_into_workspace(self, _checked=False) -> None:', 'Import File handler'),
    ('self._handle_app_drop([Path(selected)], self.library_root)', 'Import reuses external-drop path at Workspace root'),
    ('"import_file_action":"drop-active"', 'Import icon wiring'),
    ('"open_external_file_action":"open"', 'Open External icon wiring'),
    ('self.file_menu.addAction(self.dashboard_action); self.file_menu.addAction(self.next_file_action); self.file_menu.addAction(self.previous_file_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.refresh_action)', 'Dashboard/Next/Previous/Refresh order'),
    ('self.file_menu.addAction(self.import_file_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.open_external_file_action); self.file_menu.addAction(self.new_window_action); self.file_menu.addSeparator()', 'Workspace import/external/new-window grouping'),
    ('self.workspace_menu.addAction(self.manage_workspaces_action)\n        self.workspace_menu.addSeparator()', 'Workspace submenu header'),
):
    require(fragment, label)

for fragment, label in (
    ('"Show Dashboard", self.editor_manager.show_dashboard', 'retired Show Dashboard label'),
    ('self.workspace_menu.addAction(self.refresh_action)', 'Refresh remains inside Workspace(s)'),
):
    forbid(fragment, label)

if 'Import File into Workspace...' not in dashboard or 'Drag and drop RTF (.rtf) files' not in dashboard:
    raise SystemExit('FAIL: Dashboard import discoverability text missing')
if 'Drop external RTF files anywhere on this page to import them' not in folder or 'directly into this folder.' not in folder:
    raise SystemExit('FAIL: Folder Dashboard import discoverability text missing')

root = ET.parse(meta_path).getroot()
media = [node.text.strip() for node in root.findall('./provides/mediatype') if node.text]
expected = ['application/rtf', 'text/rtf', 'application/x-rtf']
if media != expected:
    raise SystemExit(f'FAIL: AppStream media types {media!r} != {expected!r}')
print('PASS: RiqatonyDesk 0.1.4 discoverability/integration metadata contract')
