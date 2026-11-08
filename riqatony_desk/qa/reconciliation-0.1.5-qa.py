#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.1.5 reconciliation/small-UX gate."""
from pathlib import Path
import hashlib

PACKAGE = Path(__file__).resolve().parents[1]
main = (PACKAGE / "widgets/main_window.py").read_text(encoding="utf-8")
ribbon = (PACKAGE / "widgets/shell_ribbon.py").read_text(encoding="utf-8")
spec = (PACKAGE / "packaging/pyinstaller/riqatonydesk.spec").read_text(encoding="utf-8")
builder = (PACKAGE / "packaging/fedora/build-appimage.sh").read_text(encoding="utf-8")
documentation = PACKAGE / "docs/Documentation.rtf"
file_actions = PACKAGE / "controllers/file_actions.py"
editor = (PACKAGE / "widgets/rtf_editor.py").read_text(encoding="utf-8")


def require(fragment: str, source: str, label: str) -> None:
    if fragment not in source:
        raise SystemExit(f"FAIL: {label}")


def forbid(fragment: str, source: str, label: str) -> None:
    if fragment in source:
        raise SystemExit(f"FAIL: {label}")


# Find is a plain shell command. The embedded Ricopad action remains the toggle engine.
require('self.search_bar_action=self._command("Find", self._focus_context_search, QKeySequence.StandardKey.Find)', main, "Find shell action")
forbid('self.search_bar_action=self._command("Find Bar"', main, "retired Find Bar shell label")
require('source = self._editor_action("search_bar_action")', main, "Ricopad Find delegation")
require('source.trigger()', main, "Ricopad Find toggle trigger")

# Small File Ribbon work only.
require('("import_file_action", 0, 3)', ribbon, "Import File must end Create & Print line 1")
require('("open_external_file_action", 1, 3)', ribbon, "Open External File must end Create & Print line 2")
require('"open_external_file_action","import_file_action"', main, "Ribbon action supply")

# User-facing Documentation is native RTF and follows the existing external/new-window path.
if not documentation.is_file():
    raise SystemExit("FAIL: bundled Documentation.rtf missing")
payload = documentation.read_bytes()
if not payload.startswith(b"{\\rtf1") or not payload.rstrip().endswith(b"}"):
    raise SystemExit("FAIL: Documentation.rtf is not a complete RTF document")
require('path = self.package_root / "docs" / "Documentation.rtf"', main, "Documentation RTF target")
require('self._launch_new_window(path)', main, "Documentation external/new-window launch")
open_docs = main[main.index('    def _open_documentation'):main.index('\n    def ', main.index('    def _open_documentation') + 5)]
forbid('README.md', open_docs, "user-facing Markdown documentation target")
require('(str(package_root / "docs" / "Documentation.rtf"), "riqatony_desk/docs")', spec, "PyInstaller Documentation.rtf data")
require('$PROGRAM_ROOT/docs/Documentation.rtf', builder, "AppImage Documentation.rtf packaging")
require('Path(resource_path("docs", "Documentation.rtf"))', editor, "embedded documentation resolver")
doc_resolver = editor[editor.index("    def _documentation_path"):editor.index("\n    def ", editor.index("    def _documentation_path") + 5)]
forbid("README.md", doc_resolver, "embedded Markdown documentation target")

# Marko Plus-authoritative grammar and workspace QActionGroup lifecycle.
require('self.show_status(f"{count} RTF file has unsaved changes." if count == 1 else f"{count} RTF files have unsaved changes.")', main, "dirty-status singular/plural grammar")
workspace = main[main.index('    def _rebuild_workspace_menu'):main.index('\n    def ', main.index('    def _rebuild_workspace_menu') + 5)]
for fragment, label in (
    ('for action in tuple(self.workspace_action_group.actions()):', 'reuse existing QActionGroup'),
    ('self.workspace_action_group.removeAction(action)', 'remove old group action'),
    ('self.workspace_menu.removeAction(action)', 'remove old menu action'),
    ('action.deleteLater()', 'delete old workspace action'),
    ('lambda _checked=False, workspace_id=workspace.project_id:', 'Marko-style stable lambda capture'),
):
    require(fragment, workspace, label)
forbid('self.workspace_action_group = QActionGroup', workspace, "recreating QActionGroup during rebuild")

# 0.1.5 deliberately preserves Rico 0.1.4 new-document Duplicate Last Saved implementation.
expected = 'a0a8e5e0ee4ab4f4df612e42f22c68b14bb167c1141eecb2bedd63fc26d2dbbd'
actual = hashlib.sha256(file_actions.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit(f"FAIL: file_actions.py changed from Rico 0.1.4 ({actual})")
require('payload, _snapshot = read_regular_file(', file_actions.read_text(encoding='utf-8'), "saved duplicate payload staging")
forbid('shutil.copy2(stored.path, temporary)', file_actions.read_text(encoding='utf-8'), "filesystem-copy duplicate semantics")

print("PASS: RiqatonyDesk 0.1.5 reconciliation/small-UX contract")
