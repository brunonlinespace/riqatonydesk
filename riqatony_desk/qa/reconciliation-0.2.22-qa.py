#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.22 sidebar placement/Quick Tour tooltip gate."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(rel): return (PACKAGE/rel).read_text(encoding='utf-8')
def sha(rel): return hashlib.sha256((PACKAGE/rel).read_bytes()).hexdigest()
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py'); ribbon=src('widgets/shell_ribbon.py')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "0.2.24"' in init,'0.2.22 package identity missing')
req('APP_REVISION = "0.2.24"' in constants,'0.2.22 revision identity missing')
req('Current release: **0.2.24**' in readme,'README current release stale')
# Underlying shared sidebar actions remain authoritative.
req('self.sidebar_action = self._command(\n            "Show Sidebar", self._toggle_sidebar, "F9", checkable=True\n        )' in main,'Show Sidebar shared action drifted')
req('for value, label in (("left", "Dock to Left"), ("right", "Dock to Right")):' in main,'AppMenu docking wording drifted')
# AppMenu ownership/order.
req('self.view_menu.addAction(self.sidebar_action)' not in main,'Show Sidebar still lives directly in View')
menu_line='sidebar_menu=self.settings_menu.addMenu("App Sidebar"); self.app_sidebar_menu_action=sidebar_menu.menuAction(); sidebar_menu.addAction(self.sidebar_action); sidebar_menu.addSeparator(); sidebar_menu.addAction(self.left_sidebar_action); sidebar_menu.addAction(self.right_sidebar_action)'
req(menu_line in main,'App Sidebar submenu order is not Show Sidebar / separator / Dock to Left / Dock to Right')
# Ribbon position swap and presentation-only App Sidebar label.
req('("collapsed_mode_action", 0, 2)' in ribbon,'Focused Mode is not in former App Sidebar slot')
req('g, "sidebar_action", 1, 0,' in ribbon,'App Sidebar fly-out is not in former Focused Mode slot')
req('menu_actions=("sidebar_action", None, "left_sidebar_action", "right_sidebar_action")' in ribbon,'App Sidebar fly-out does not reuse shared actions')
req('app_sidebar_button.setToolTip("App Sidebar")' in ribbon,'Ribbon App Sidebar presentation label missing')
req('app_sidebar_button.setAccessibleName("App Sidebar")' in ribbon,'Ribbon App Sidebar accessible label missing')
# Quick Tour tooltip/content remain exactly as approved.
req('self.quick_start_action.setToolTip("Quick Tour… — Shift+F1")' in main,'Quick Tour tooltip is not exact')
tree=ast.parse(main); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow'); fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_show_quick_tour')
calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='add_page']
req(len(calls)==7,'Quick Tour page count changed')
rows=[]
for node in calls:
    vals=[]
    for arg in node.args[:3]:
        req(isinstance(arg,ast.Constant) and isinstance(arg.value,str),'Quick Tour title/subtitle/body is no longer literal')
        vals.append(arg.value if isinstance(arg,ast.Constant) else None)
    rows.append(vals)
payload=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()
req(hashlib.sha256(payload).hexdigest()=='e2b17c0eea655ce5057268fc319fd9241893696c8bba2158dddc189a239eaf17','Quick Tour page titles/subtitles/body content changed')
protected={
 'widgets/rtf_editor.py':'50a35d1d60823c13da8c3d17e320b3e3ba7d9cb218e34cb1da359c2e2b31873a',
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
    print('RiqatonyDesk 0.2.22 check failed:')
    [print('- '+e) for e in errors]
    raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.22 bounded sidebar/Quick Tour correction contract')
