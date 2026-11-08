#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.1.6 drag/drop reconciliation gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def source(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha256(relative: str) -> str:
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()


init = source("__init__.py")
constants = source("app_constants.py")
main = source("widgets/main_window.py")
navigation = source("widgets/navigation.py")
dashboard = source("widgets/dashboard.py")
folder_dashboard = source("widgets/folder_dashboard.py")
editor_page = source("widgets/editor_page.py")
manager = source("controllers/editor_manager.py")
desktop = source("packaging/appimage/riqatonydesk.desktop")
component = json.loads((ROOT / "suite-pythoine-component.json").read_text(encoding="utf-8"))
manifest = json.loads((PACKAGE / "riqatonydesk.json").read_text(encoding="utf-8"))

# Identity and protected Suite contract.
require(component.get("component_kind") == "extension", "Suite component kind changed")
require(component.get("extensions") == [], "Suite routing extensions changed")
require(component.get("capabilities") == {"routing": False, "open": False, "create": False},
        "Suite routing/open/create capabilities changed")
require("Exec=riqatonydesk %f" in desktop and "%F" not in desktop,
        "single-file desktop routing changed")
for mime in ("application/rtf", "text/rtf", "application/x-rtf"):
    require(mime in desktop, f"desktop RTF MIME changed: {mime}")

# Broad MainWindow fallback is removed: drops must land on explicit surfaces.
require("self.setAcceptDrops(True)" not in main,
        "MainWindow still accepts application-wide drops")
require("def dragEnterEvent(" not in main and "def dropEvent(" not in main,
        "MainWindow-wide drag/drop fallback remains")
require("manager.editor_files_dropped.connect(self._handle_editor_file_drop)" in main,
        "editor drops are not routed to the external-open handler")
editor_drop = main.split("    def _handle_editor_file_drop", 1)[1].split("    def _handle_app_drop", 1)[0]
require("self._launch_new_window(path)" in editor_drop,
        "editor drop does not use the existing new-window file-open lifecycle")
require("import_files" not in editor_drop and "_handle_app_drop" not in editor_drop,
        "editor drop still reaches the import path")

# Main Dashboard is an explicit root import surface.
for fragment in (
    "external_files_dropped = pyqtSignal(object)",
    "self.setAcceptDrops(True)",
    "def dragEnterEvent(self, event: QDragEnterEvent)",
    "def dropEvent(self, event: QDropEvent)",
    "self.external_files_dropped.emit(dropped)",
):
    require(fragment in dashboard, f"Main Dashboard root-drop contract missing: {fragment}")
require(
    "self.dashboard.external_files_dropped.connect(" in manager
    and "paths, self.library_root" in manager,
    "Main Dashboard drops are not routed explicitly to Workspace root",
)

# Sidebar tree destination matrix for external imports.
resolver = navigation.split("    def _external_drop_destination", 1)[1].split("    def dragMoveEvent", 1)[0]
for fragment in (
    "if item is None:",
    "return Path(self.parent().library_root).resolve(strict=False)",
    "if kind == self.KIND_FOLDER:",
    "return path",
    'if kind == "document":',
    "return path.parent",
    "return None",
):
    require(fragment in resolver, f"sidebar external destination rule missing: {fragment}")
require(
    "self._external_drop_destination(item) is not None" in navigation,
    "external sidebar drag acceptance is not tied to the explicit destination resolver",
)

# Existing explicit import surfaces remain intact.
require("class DashboardNavigationButton" in navigation,
        "Dashboard sidebar root target missing")
require("self.external_files_dropped.emit(paths)" in navigation,
        "Dashboard sidebar root import signal missing")
require("self.setAcceptDrops(True)" in folder_dashboard and "def dropEvent" in folder_dashboard,
        "Folder Dashboard import target changed")
require("self.external_files_dropped.emit(dropped, destination)" in folder_dashboard,
        "Folder Dashboard no longer emits its explicit folder destination")

# Editor page is an explicit external-open surface. Ricopad itself may continue
# to reject local-file URLs; the parent page catches that ignored event.
require("self.setAcceptDrops(True)" in editor_page,
        "EditorPage is not an explicit file-open drop surface")
require("def _dropped_rtf_paths" in editor_page,
        "EditorPage RTF drop validation missing")
require("self.external_files_dropped.emit(paths, self.document.path.parent)" in editor_page,
        "EditorPage drop does not reach the editor-drop route")
require("page.external_files_dropped.connect(self.editor_files_dropped)" in manager,
        "EditorPage drops are not forwarded by EditorManager")

# Protect the 0.1.5 implementation outside the five routing surfaces.
expected_hashes = {
    "controllers/file_actions.py": "a0a8e5e0ee4ab4f4df612e42f22c68b14bb167c1141eecb2bedd63fc26d2dbbd",
    "models/document_repository.py": "e7e1829d7ee5d71644e5cffdb6fe98b533e44d44b6fe3e4436ad8179e83e6247",
    "services/filesystem_watcher.py": "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "widgets/folder_dashboard.py": "66cda277e6113251540f72ba8842b7e9a03ca6fe893e3a921085890f19360b0a",
    "widgets/shell_ribbon.py": "4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993",
    "rtf_codec.py": "34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
    "services/document_scanner.py": "8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
}
for relative, expected in expected_hashes.items():
    require(sha256(relative) == expected, f"protected 0.1.5 implementation changed: {relative}")

if errors:
    print("RiqatonyDesk 0.1.6 check failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.1.6 drag/drop reconciliation contract")
