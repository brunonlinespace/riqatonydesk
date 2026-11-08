#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.17 Audit 20 Help-ownership gate."""
from pathlib import Path
import hashlib
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src("__init__.py"); constants=src("app_constants.py"); main=src("widgets/main_window.py"); rtf=src("widgets/rtf_editor.py"); page=src("widgets/editor_page.py"); readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.17"' in init,"0.2.17 package identity missing")
req('APP_REVISION = "0.2.17"' in constants,"0.2.17 revision identity missing")
req('Current release: **0.2.17**' in readme,"README current release stale")
for fragment in (
 'self.shortcuts_action = self._command(', '"Keyboard Shortcuts", self._show_shortcuts, "Ctrl+Shift+/"',
 'self.docs_action = self._command(', '"Documentation", self._open_documentation,',
 'self.quick_start_action=self._command("Quick Tour",self._show_quick_tour,"Shift+F1")',
 'self.github_action = self._command(', 'lambda: self.desktop_launcher.open_url(GITHUB_URL)',
 'self.issue_action = self._command(', 'lambda: self.desktop_launcher.open_url(ISSUES_URL)',
 'self.about_action = self._command(', '"About RiqatonyDesk", self._show_about_dialog',
 'self.help_menu.addAction(self.docs_action)', 'self.help_menu.addAction(self.quick_start_action)',
): req(fragment in main,f"MainWindow Help authority changed: {fragment}")
for fragment in (
 'self.make_help_menu()', 'def make_help_menu(', 'self.documentation_action =', 'self.tutorial_action =',
 'self.shortcuts_action =', 'self.github_action =', 'self.issue_action =', 'self.about_action =',
 'def _documentation_path(', 'def open_documentation(', 'def open_github_repository(',
 'def report_an_issue(', 'def show_tutorial_wizard(', 'def show_keyboard_shortcuts_dialog(',
 'def show_about_dialog(',
): req(fragment not in rtf,f"stale embedded Help implementation remains: {fragment}")
req('def open_documentation(' not in page,"dead EditorPage embedded Documentation bridge remains")
for fragment in ('def _open_host_target(self, target, *, local=False):','def open_document_link(self, href):','hasattr(window, "open_document_link")'):
    req(fragment in rtf,f"live RTF link handling changed: {fragment}")
req(sha("widgets/rtf_editor.py")=="b46fe76824549aa67b5512689a04d5aa5f0e868a745b6a4d15d60861a33c8c2f","rtf_editor.py changed outside exact Audit 20 removal")
req(sha("widgets/editor_page.py")=="c5da44a5fbe8d8e493c31aaa1c996a33f6087db5cfbe9e409dbd59f6f68b2f74","EditorPage changed outside dead Documentation bridge removal")
protected={'widgets/main_window.py': '59d2227e2df86e7dab64bd2caa1d683b13ea8a4cfbdc2f0dc02bab9b194bc4e3', 'widgets/shell_ribbon.py': '38ce2f39ea63ec26cb16220268b8cbd337e73f417158a73886144338a2afa570', 'controllers/file_actions.py': '3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569', 'controllers/editor_manager.py': 'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894', 'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999', 'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad', 'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123', 'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f', 'services/file_io.py': '96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55', 'rtf_codec.py': '34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95', 'rich_text_support.py': '6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb'}
for r,h in protected.items(): req(sha(r)==h,f"protected out-of-scope file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.17 check failed:"); [print("- "+e) for e in errors]; raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.17 Audit 20 MainWindow-only Help ownership contract")
