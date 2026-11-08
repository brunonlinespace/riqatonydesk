#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.5 navigation/drag-target release gate."""
from __future__ import annotations
import hashlib
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

init = src("__init__.py")
constants = src("app_constants.py")
main = src("widgets/main_window.py")
nav = src("widgets/navigation.py")
dashboard = src("widgets/dashboard.py")
folder = src("widgets/folder_dashboard.py")
iconqa = src("qa/iconset-qa.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.5"' in init, "0.2.5 package identity missing")
req('APP_REVISION = "0.2.5"' in constants, "0.2.5 revision identity missing")
req('Current release: **0.2.5**' in readme, "root README current release is stale")

req('QStyle.StandardPixmap.SP_DirIcon' in nav, "native folder icon was removed")
req('QStyle.StandardPixmap.SP_FileIcon' not in nav, "file icons remain in workspace tree")
for fragment in (
    'def _set_drop_highlight(self, item, *, root: bool = False)',
    'QPalette.ColorRole.Highlight',
    'QPalette.ColorRole.HighlightedText',
    'def dragLeaveEvent(self, event: QDragLeaveEvent)',
    'self._set_root_drop_highlight(root)',
):
    req(fragment in nav, f"navigation drop-target feedback missing: {fragment}")
for body, label in ((dashboard, "Dashboard"), (folder, "Folder Dashboard")):
    req('QPalette.ColorRole.Highlight' in body, f"{label} palette-aware drop highlight missing")
    req('self._set_drop_highlight(False)' in body, f"{label} drop highlight is not cleared")
req('"app_sidebar_menu_action":"show-sidebar"' in main, "App Sidebar group icon is not show-sidebar")

for family in ('ribbon-icons', 'ribbon-icons-classic', 'ribbon-icons-original'):
    for scheme in ('light', 'dark'):
        for ext in ('png', 'svg'):
            req((PACKAGE / 'assets' / family / (scheme if ext == 'png' else f'svg/{scheme}') / f'show-sidebar-right.{ext}').is_file(),
                f"missing {family}/{scheme} show-sidebar-right.{ext}")
req('PNG_ONLY_INTERIM: set[str] = set()' in iconqa, "Rico icon QA still allows a PNG-only sidebar-right gap")

protected = {
    'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
    'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
    'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
    'controllers/editor_manager.py': 'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894',
    'widgets/editor_page.py': '6de5e5858f41813f87ce1591bb3966dc797873e2228e284be119a40395d937b2',
    'widgets/dashboard_card.py': 'f077cc621e797847435f84de793b685395bdfb2d70a0d1b5229814d4e27bea9e',
    'widgets/shell_ribbon.py': '4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993',
    'services/config_service.py': 'b4d72c5a9ac37d02b537c3fd8b83892b8ba01e22b5e339a14c4f65273e072e7e',
    'controllers/file_actions.py': '600159f96519d10df52bd98cc4dee808b11cc0730ab903b2661d15ebc3fba387',
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.5 check failed:")
    for error in errors:
        print("- " + error)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.5 navigation/drag-target contract")
