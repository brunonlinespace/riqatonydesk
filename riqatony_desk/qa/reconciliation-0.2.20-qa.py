#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.20 Quick Tour/icon refinement gate."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
from _identity_fingerprint import historical_source_sha, normalize_identity_text

PACKAGE=Path(__file__).resolve().parents[1]
ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(rel): return (PACKAGE/rel).read_text(encoding='utf-8')
def sha(rel): return historical_source_sha(PACKAGE/rel)
init=src('__init__.py'); constants=src('app_constants.py'); app=src('app.py'); main=src('widgets/main_window.py'); ribbon=src('widgets/shell_ribbon.py'); readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "1.0.0-x11.2"' in init,'0.2.20 package identity missing')
req('APP_REVISION = "1.0.0-x11.2"' in constants,'0.2.20 revision identity missing')
req('Current release: **1.0.0-x11.2**' in readme,'README current release stale')
req('RIBBON_BUTTON_SIZE = 52' in ribbon,'52x52 ShellRibbon command-button size changed')
req('RIBBON_ICON_SIZE = 36' in ribbon,'36x36 ShellRibbon command-icon size missing')
req('self.quick_start_action=self._command("Quick Tour…",self._show_quick_tour,"Shift+F1")' in main,'Help menu Quick Tour ellipsis missing')
req('wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)' in main,'first-page Back suppression missing')
req('QCheckBox("Don\'t show Quick Tour on startup again", wizard)' in main,'Quick Tour startup checkbox missing')
req('startup_checkbox.setChecked(bool(self.config.get("quick_tour_seen", False)))' in main,'Quick Tour checkbox does not reflect persisted state')
req('lambda checked: self.config.set("quick_tour_seen", bool(checked), save=True)' in main,'Quick Tour checkbox does not persist through existing config path')
# Startup must show while unsuppressed, without marking suppression just because the tour opened.
req('if not bool(config.get("quick_tour_seen", False)):\n        QTimer.singleShot(0, window._show_quick_tour)' in app,'startup Quick Tour trigger drifted')
req('config.set("quick_tour_seen", True, save=True)' not in app,'startup still auto-marks Quick Tour suppressed')
# The existing seven page titles/subtitles/body strings are a hard no-edit boundary.
tree=ast.parse(main)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_show_quick_tour')
rows=[]
for node in ast.walk(fn):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='add_page':
        vals=[]
        for arg in node.args[:3]:
            req(isinstance(arg,ast.Constant) and isinstance(arg.value,str),'Quick Tour title/subtitle/body is no longer a literal string')
            vals.append(arg.value if isinstance(arg,ast.Constant) else None)
        rows.append(vals)
payload=json.dumps([[normalize_identity_text(v) if isinstance(v,str) else v for v in row] for row in rows],ensure_ascii=False,separators=(',',':')).encode('utf-8')
req(len(rows)==7,'Quick Tour page count changed')
req(hashlib.sha256(payload).hexdigest()=='e2b17c0eea655ce5057268fc319fd9241893696c8bba2158dddc189a239eaf17','Quick Tour page titles/subtitles/body content changed')
# Deferred workspace/setup-wizard work and precious editor/lifecycle code must remain untouched.
protected={
 'widgets/editor_page.py':'c5da44a5fbe8d8e493c31aaa1c996a33f6087db5cfbe9e409dbd59f6f68b2f74',
 'controllers/file_actions.py':'3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569',
 'controllers/editor_manager.py':'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894',
 'services/open_document_monitor.py':'25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
 'services/filesystem_watcher.py':'655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
 'services/document_scanner.py':'8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
 'models/document_repository.py':'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f',
 'services/file_io.py':'96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55',
 'rtf_codec.py':'34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
 'rich_text_support.py':'6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb',
 'services/config_service.py':'b4d72c5a9ac37d02b537c3fd8b83892b8ba01e22b5e339a14c4f65273e072e7e',
 'widgets/first_run_dialog.py':'1de90656077d64c8d91818d7060f5cc02a250cf38565d84afd89d7ff1efd1b98',
}
for rel,h in protected.items(): req(sha(rel)==h,f'protected out-of-scope file changed: {rel}')
# rtf_editor.py has since undergone the authorised x1/x2/x3 extractions.
# The x3 AST gate pins all prior editor methods instead of obsolete whole-file bytes.
import runpy
runpy.run_path(str(PACKAGE / "qa" / "x3-insertion-extraction-qa.py"), run_name="__main__")
if errors:
    print('RiqatonyDesk 0.2.20 check failed:')
    [print('- '+e) for e in errors]
    raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.20 bounded Quick Tour/icon refinement contract')
