#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.2 synchronized UI-polish release gate."""
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


main = src("widgets/main_window.py")
dashboard = src("widgets/dashboard.py")
folder = src("widgets/folder_dashboard.py")
nav = src("widgets/navigation.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
init = src("__init__.py")
constants = src("app_constants.py")

req('APP_VERSION = "0.2.2"' in init, "0.2.2 package identity missing")
req('APP_REVISION = "0.2.2"' in constants, "0.2.2 revision identity missing")

# Exact requested command/wording scope.
for fragment in (
    '"New File…", self._new_rtf_file, QKeySequence.StandardKey.New',
    '"Import File into Workspace...", self._import_file_into_workspace, "Ctrl+Alt+Shift+I"',
    '"Open External File...", self._open_external_file, "Ctrl+Alt+Shift+O"',
):
    req(fragment in main, f"0.2.2 command contract missing: {fragment}")
req("New RTF File…" not in main, "old New RTF File command wording remains in MainWindow")

for fragment in (
    'QPushButton("New File")',
    'QPushButton("New Folder")',
    '(self.new_file_button, "new")',
    '(self.new_folder_button, "new-folder")',
    'view_icon = "list-view" if self._view_mode == "grid" else "grid-view"',
):
    req(fragment in dashboard, f"Dashboard polish missing: {fragment}")
req(dashboard.index("controls.addWidget(self.view_toggle_button)") < dashboard.index("controls.addWidget(self.refresh_button)"),
    "Dashboard View toggle does not precede Refresh")

for fragment in (
    'QPushButton("New File")',
    'QPushButton("New Folder")',
    'QPushButton("Delete Folder")',
    '(self.new_file_button, "new")',
    '(self.new_folder_button, "new-folder")',
):
    req(fragment in folder, f"Folder Dashboard wording/icon contract missing: {fragment}")
req("Remove Folder\"" not in folder, "Remove Folder label remains in Folder Dashboard")

# Sidebar order + file/folder visual distinction.
for fragment in (
    'QStyle.StandardPixmap.SP_DirIcon',
    'QStyle.StandardPixmap.SP_FileIcon',
):
    req(fragment in nav, f"folder/file distinction missing: {fragment}")
order = [
    'self.workspace_label = QLabel("<h3>My Workspace</h3>")',
    'self.dashboard_button = DashboardNavigationButton(self)',
    'self.expand_all_button = style_button(',
    'self.tree = NavigationTree(self)',
    'self.refresh_button = style_button(',
]
try:
    positions = [nav.index(fragment) for fragment in order]
    req(positions == sorted(positions), "sidebar order is not My Workspace / Dashboard / tree controls / tree / Refresh Workspace")
except ValueError as exc:
    errors.append(f"sidebar order marker missing: {exc}")

# Root README follows the requested GitHub-facing format and current release.
for fragment in (
    '# RiqatonyDesk',
    '**Friendly. Fast. Focused.**',
    'Current release: **0.2.2**',
    'Ctrl+Alt+Shift+I',
    'Ctrl+Alt+Shift+O',
    '## Building the AppImage',
    '## License',
):
    req(fragment in readme, f"root README contract missing: {fragment}")

# Explicitly protect the just-completed lifecycle/safety work and the later Grid-card scope.
protected = {
    'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
    'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
    'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
    'controllers/editor_manager.py': '82a88e86c1a69a942dd88bc6b09be85a7b54f5f16d24b7f05592d422378b5959',
    'widgets/editor_page.py': '6de5e5858f41813f87ce1591bb3966dc797873e2228e284be119a40395d937b2',
    'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f',
    'widgets/resolve_open_documents_dialog.py': '38657cbfaf21ab286cb58dc2cd8fac43b2b562d270629d98276274d68c17047e',
    'widgets/dashboard_card.py': '18847d35ad1abe76b856a27240e4ff13be4505ea07cc66e6e2f977e87ba6f2ed',
    'widgets/shell_ribbon.py': '4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993',
    'services/config_service.py': 'c2741e48d3b1416d365625a8e7e49acf09db833117fa63827e65e5af0a67d131',
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.2 check failed:")
    for error in errors:
        print("- " + error)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.2 synchronized UI-polish contract")
