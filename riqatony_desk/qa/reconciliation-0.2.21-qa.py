#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.21 bounded UI cleanup gate."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(rel): return (PACKAGE/rel).read_text(encoding='utf-8')
def sha(rel): return hashlib.sha256((PACKAGE/rel).read_bytes()).hexdigest()
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py'); ribbon=src('widgets/shell_ribbon.py'); rtf=src('widgets/rtf_editor.py'); readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "0.2.21"' in init,'0.2.21 package identity missing')
req('APP_REVISION = "0.2.21"' in constants,'0.2.21 revision identity missing')
req('Current release: **0.2.21**' in readme,'README current release stale')
# Wording changes.
req('self.paste_plain_action=self._editor_command("Paste as Plain Text","paste_plain_action","Ctrl+Shift+V")' in main,'shell Paste as Plain Text missing')
req('menu,"Paste as Plain Text",self.paste_plain_text' in rtf,'embedded Paste as Plain Text missing')
req('Paste Plain Text' not in main and 'Paste Plain Text' not in rtf,'retired Paste Plain Text label remains')
req('self.replace_action=self._command("Find and Replace", self._focus_replace, "Ctrl+H")' in main,'Find and Replace ellipsis removal missing')
req('Find and Replace…' not in main,'retired Find and Replace ellipsis remains in shell')
# Create & Print swap only.
req('("import_file_action", 0, 3)' in ribbon,'Import File not in former Open File slot')
req('("open_external_file_action", 1, 3)' in ribbon,'Open External File not in former Import slot')
# Sidebar fly-out uses the exact existing AppMenu actions/wording.
for frag in (
    'for value, label in (("left", "Dock to Left"), ("right", "Dock to Right")):',
    'menu_actions=("sidebar_action", None, "left_sidebar_action", "right_sidebar_action")',
    'menu.addAction(self._a(item))',
    'button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)',
    '"sidebar_action","left_sidebar_action","right_sidebar_action","status_bar_action"',
): req(frag in main or frag in ribbon,f'sidebar fly-out/AppMenu contract missing: {frag}')
# Dashboard state tooltip now exposes existing keybind without assigning a duplicate shortcut.
req('f"Dashboard — {\'Grid View\' if dashboard_mode == \'grid\' else \'List View\'} — Ctrl+Alt+Shift+V"' in main,'Dashboard toggle tooltip keybind missing')
req('"Toggle List/Grid View",\n            self._toggle_dashboard_view_mode,\n            "Ctrl+Alt+Shift+V"' in main,'authoritative List/Grid shortcut drifted')
# Quick Tour wrapper only: ellipsis tooltip + footer checkbox. Page content is immutable.
req('self.quick_start_action.setToolTip("Quick Tour… — Shift+F1")' in main,'Quick Tour tooltip ellipsis missing')
for frag in (
    'wizard.setButton(QWizard.WizardButton.CustomButton1, startup_checkbox)',
    'wizard.setOption(QWizard.WizardOption.HaveCustomButton1, True)',
    'QWizard.WizardButton.CustomButton1,',
    'QWizard.WizardButton.Stretch,',
    'QWizard.WizardButton.BackButton,',
    'QWizard.WizardButton.NextButton,',
    'QWizard.WizardButton.FinishButton,',
    'QWizard.WizardButton.CancelButton,',
    'wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)',
): req(frag in main,f'Quick Tour footer/navigation contract missing: {frag}')
tree=ast.parse(main); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow'); fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_show_quick_tour')
calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='add_page']
req(len(calls)==7,'Quick Tour page count changed')
rows=[]
for i,node in enumerate(calls):
    if i==0: req(len(node.args)==3,'startup checkbox is still embedded in first Quick Tour content page')
    vals=[]
    for arg in node.args[:3]:
        req(isinstance(arg,ast.Constant) and isinstance(arg.value,str),'Quick Tour title/subtitle/body is no longer literal')
        vals.append(arg.value if isinstance(arg,ast.Constant) else None)
    rows.append(vals)
payload=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()
req(hashlib.sha256(payload).hexdigest()=='e2b17c0eea655ce5057268fc319fd9241893696c8bba2158dddc189a239eaf17','Quick Tour page titles/subtitles/body content changed')
# Bound current embedded editor to the one approved label change and protect deferred/precious files.
req(sha('widgets/rtf_editor.py')=='50a35d1d60823c13da8c3d17e320b3e3ba7d9cb218e34cb1da359c2e2b31873a','rtf_editor changed outside approved Paste label scope')
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
if errors:
    print('RiqatonyDesk 0.2.21 check failed:')
    [print('- '+e) for e in errors]
    raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.21 bounded UI/fly-out/Quick Tour footer contract')
