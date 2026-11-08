#!/usr/bin/env python3
"""Dependency-free Phase 1 convergence gate for RiqatonyDesk 0.1.0."""
from __future__ import annotations

from pathlib import Path
import ast

PACKAGE = Path(__file__).resolve().parents[1]
errors: list[str] = []


def text(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def require(relative: str, fragment: str, label: str) -> None:
    if fragment not in text(relative):
        errors.append(f"{label}: missing {fragment!r} in {relative}")


def forbid(relative: str, fragment: str, label: str) -> None:
    if fragment in text(relative):
        errors.append(f"{label}: forbidden {fragment!r} remains in {relative}")

# Syntax first, including the new routing surfaces.
for relative in (
    "app.py",
    "widgets/dashboard_card.py",
    "widgets/dashboard.py",
    "widgets/navigation.py",
    "widgets/folder_dashboard.py",
    "controllers/editor_manager.py",
    "widgets/main_window.py",
):
    try:
        ast.parse(text(relative), filename=relative)
    except SyntaxError as exc:
        errors.append(f"syntax error in {relative}: {exc}")

# Touch contract: existing root Dashboard QScroller + explicit non-mouse guard.
require(
    "widgets/dashboard.py",
    "QScroller.ScrollerGestureType.TouchGesture",
    "root Dashboard kinetic gesture",
)
require(
    "widgets/dashboard.py",
    "touch_moves_scroll_only=True",
    "root Dashboard card touch guard",
)
require(
    "widgets/dashboard_card.py",
    "event.deviceType() != QInputDevice.DeviceType.Mouse",
    "touch-origin drag rejection",
)
require(
    "widgets/dashboard_card.py",
    "drag.exec(Qt.DropAction.MoveAction)",
    "genuine mouse managed-file drag retained",
)
for relative in ("widgets/folder_dashboard.py", "widgets/navigation.py"):
    forbid(
        relative,
        "QScroller",
        "kinetic scrolling must remain main-Dashboard-only",
    )
require(
    "widgets/shell_ribbon.py",
    "QScroller",
    "Rico Ribbon touch panning retained",
)

# External RTF import-only routing. The underlying import engine must remain the owner.
require("widgets/navigation.py", "def external_rtf_paths", "external RTF URL filter")
require(
    "widgets/navigation.py",
    "external_files_import_requested = pyqtSignal(object, object)",
    "navigation import signal",
)
require(
    "widgets/folder_dashboard.py",
    "external_files_dropped = pyqtSignal(object, object)",
    "Folder Dashboard import signal",
)
require(
    "controllers/editor_manager.py",
    "page.external_files_dropped.connect(\n                self.external_files_import_requested",
    "Folder Dashboard forwarding",
)
require(
    "widgets/main_window.py",
    "self.navigation.external_files_import_requested.connect(\n            self.file_actions.import_files",
    "navigation routes to existing import engine",
)
require(
    "widgets/main_window.py",
    "manager.external_files_import_requested.connect(\n            self.file_actions.import_files",
    "Folder Dashboard routes to existing import engine",
)
require(
    "widgets/main_window.py",
    "def _handle_app_drop(",
    "application-level import-only handler",
)
require(
    "widgets/main_window.py",
    "self.file_actions.import_files(\n            external,",
    "application-level drop uses import engine",
)
# The drop handler itself must not open documents/tabs/windows after import.
main = text("widgets/main_window.py")
start = main.index("    def _handle_app_drop(")
end = main.find("\n    def ", start + 5)
handler = main[start:end if end != -1 else len(main)]
for forbidden in ("open_document", "queue_open_path", "_new_window", "document_tabs"):
    if forbidden in handler:
        errors.append(f"import-only handler performs forbidden post-import action: {forbidden}")

# Workspace-switch recovery follows the stronger Marko method boundary.
require("widgets/main_window.py", "def _install_watcher(", "watcher install helper")
require(
    "widgets/main_window.py",
    "self._install_watcher(\n                self.library_root, start=True, retire_current=False",
    "failed-switch watcher recovery",
)
require(
    "widgets/main_window.py",
    "The existing Workspace remains active.",
    "failed-switch recovery message",
)

# Manual refresh semantics distinguish explicit refresh from ordinary load.
for fragment in (
    'self.show_status("Refreshing workspace in background…")',
    '"Refreshing your workspace…"',
    'f"Refreshed {count} RTF file(s) in {project_name}."',
    'f"Loaded {count} RTF file(s) in {project_name}."',
):
    require("widgets/main_window.py", fragment, "manual refresh semantics")

# Single-file OS launch only; retain normal single external-session route.
require("app.py", "def requested_open_path(", "single-file startup parser")
require("app.py", "window.queue_open_path(open_path)", "single external open retained")
forbid("app.py", "requested_open_paths", "multi-file parser removed")
forbid("app.py", "_open_path_in_new_window", "broken extra-file branch removed")
require("packaging/appimage/riqatonydesk.desktop", "Exec=riqatonydesk %f", "single-file desktop route")
forbid("packaging/appimage/riqatonydesk.desktop", "Exec=riqatonydesk %F", "multi-file desktop route removed")

if errors:
    print("FAIL: RiqatonyDesk 0.1.0 Phase 1 convergence gate")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print("PASS: RiqatonyDesk 0.1.0 Phase 1 convergence contract")
