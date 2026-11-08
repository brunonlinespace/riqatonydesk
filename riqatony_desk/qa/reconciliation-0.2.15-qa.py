#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.15 Audit 10 stale embedded file-management removal gate."""
from pathlib import Path
import hashlib

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors = []


def req(condition, message):
    if not condition:
        errors.append(message)


def src(relative):
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha(relative):
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()


init = src("__init__.py")
constants = src("app_constants.py")
rtf = src("widgets/rtf_editor.py")
page = src("widgets/editor_page.py")
manager = src("controllers/editor_manager.py")
main = src("widgets/main_window.py")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

req('APP_VERSION = "0.2.15"' in init, "0.2.15 package identity missing")
req('APP_REVISION = "0.2.15"' in constants, "0.2.15 revision identity missing")
req('Current release: **0.2.15**' in readme, "README current release stale")

# Audit 10 is deletion-only: these embedded standalone implementations must be gone.
stale_methods = (
    "open_external_editor",
    "open_containing_folder",
    "duplicate_current_file",
    "delete_current_file",
    "rename_current_file",
)
for name in stale_methods:
    req(f"def {name}(" not in rtf, f"stale embedded method still exists: {name}")

# The embedded actions must remain request-only; no controller behavior is moved into the editor.
for fragment in (
    'self.external_editor_action = self.add_menu_action(self.more_actions_menu, "Open in External Editor", self.external_editor_requested.emit, QKeySequence("Ctrl+Shift+E"))',
    'self.rename_action = self.add_menu_action(self.more_actions_menu, "Rename…", self.rename_requested.emit, QKeySequence("F2"))',
    'self.delete_file_action = self.add_menu_action(self.more_actions_menu, "Delete File", self.delete_requested.emit)',
    'self.duplicate_file_action = self.add_menu_action(self.more_actions_menu, "Duplicate File", self.duplicate_requested.emit, QKeySequence("Ctrl+Shift+D"))',
    'self.open_folder_action = self.add_menu_action(self.more_actions_menu, "Open Containing Folder", self.containing_folder_requested.emit, QKeySequence("Ctrl+Shift+O"))',
):
    req(fragment in rtf, f"embedded request-only action wiring changed: {fragment}")

# EditorPage forwarding is preserved, including Delete -> remove_requested translation.
for fragment in (
    'self._surface.external_editor_requested.connect(',
    'lambda: self.external_editor_requested.emit(self.document)',
    'self._surface.containing_folder_requested.connect(',
    'lambda: self.containing_folder_requested.emit(self.document)',
    'self._surface.rename_requested.connect(',
    'lambda: self.rename_requested.emit(self.document)',
    'self._surface.delete_requested.connect(',
    'lambda: self.remove_requested.emit(self.document)',
    'self._surface.duplicate_requested.connect(',
    'lambda: self.duplicate_requested.emit(self.document)',
):
    req(fragment in page, f"EditorPage file-action forwarding changed: {fragment}")

# EditorManager forwarding remains unchanged.
for fragment in (
    'page.external_editor_requested.connect(self.external_editor_requested)',
    'page.containing_folder_requested.connect(',
    'self.containing_folder_requested',
    'page.rename_requested.connect(self.rename_requested)',
    'page.remove_requested.connect(self.remove_requested)',
    'page.duplicate_requested.connect(self.duplicate_requested)',
):
    req(fragment in manager, f"EditorManager file-action forwarding changed: {fragment}")

# MainWindow still terminates the chain at the authoritative FileActionsController.
for fragment in (
    'manager.external_editor_requested.connect(\n            self.file_actions.open_external_editor\n        )',
    'manager.containing_folder_requested.connect(\n            self.file_actions.open_document_folder\n        )',
    'manager.rename_requested.connect(self.file_actions.rename_document)',
    'manager.remove_requested.connect(self.file_actions.remove_document)',
    'manager.duplicate_requested.connect(\n            self.file_actions.duplicate_document\n        )',
):
    req(fragment in main, f"MainWindow authoritative file-action route changed: {fragment}")

# Exact resulting embedded-editor hash pins Audit 10 to the approved five-method deletion.
req(
    sha("widgets/rtf_editor.py") == "e67ee7374e3624ce22d2c4830998d90d9df3e6d1cf4e810693d0e0ad0b23eebc",
    "rtf_editor.py changed outside the approved Audit 10 deletion",
)

# No surrounding Plus authority/lifecycle/shell/editor-support implementation may change.
protected = {
    "widgets/editor_page.py": "22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e",
    "controllers/editor_manager.py": "bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894",
    "widgets/main_window.py": "59d2227e2df86e7dab64bd2caa1d683b13ea8a4cfbdc2f0dc02bab9b194bc4e3",
    "controllers/file_actions.py": "3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569",
    "widgets/shell_ribbon.py": "38ce2f39ea63ec26cb16220268b8cbd337e73f417158a73886144338a2afa570",
    "services/open_document_monitor.py": "25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
    "services/filesystem_watcher.py": "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "services/document_scanner.py": "8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
    "models/document_repository.py": "e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f",
    "services/file_io.py": "96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55",
    "rtf_codec.py": "34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95",
    "rich_text_support.py": "6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb",
}
for relative, expected in protected.items():
    req(sha(relative) == expected, f"protected out-of-scope file changed: {relative}")

if errors:
    print("RiqatonyDesk 0.2.15 check failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("PASS: RiqatonyDesk 0.2.15 Audit 10 stale embedded file-management implementations removed")
