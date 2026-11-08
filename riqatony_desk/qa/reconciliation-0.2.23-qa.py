#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.23 App Sidebar icon synchronization gate."""
from __future__ import annotations
import ast, hashlib
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(rel): return (PACKAGE/rel).read_text(encoding='utf-8')
def sha(rel): return hashlib.sha256((PACKAGE/rel).read_bytes()).hexdigest()
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "0.2.24"' in init,'0.2.23 package identity missing')
req('APP_REVISION = "0.2.24"' in constants,'0.2.23 revision identity missing')
req('Current release: **0.2.24**' in readme,'README current release stale')
# Existing actions/labels remain authoritative.
req('"Show Sidebar", self._toggle_sidebar, "F9", checkable=True' in main,'Show Sidebar action changed')
req('for value, label in (("left", "Dock to Left"), ("right", "Dock to Right")):' in main,'dock action wording changed')
# Dynamic icon contract: icon side follows actual splitter side, not visibility.
tree=ast.parse(main); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_sync_sidebar_position_icons')
segment=ast.get_source_segment(main, fn) or ''
req('"show-sidebar-right" if self._sidebar_position() == "right" else "show-sidebar"' in segment,'dock-side icon selection drifted')
req('self.sidebar_action.setIcon(icon)' in segment,'Show Sidebar/Ribbon shared action is not synchronized')
req('self.app_sidebar_menu_action.setIcon(icon)' in segment,'App Sidebar menu parent is not synchronized')
req('setChecked' not in segment and 'setVisible' not in segment,'icon sync must not change visibility/check state')
# Reapply after icon-family/theme refresh and after any dock-side change.
refresh=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_refresh_action_icons')
refresh_seg=ast.get_source_segment(main, refresh) or ''
req('self._sync_sidebar_position_icons()' in refresh_seg,'theme/icon refresh does not restore dock-side icon')
setpos=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_set_sidebar_position')
setpos_seg=ast.get_source_segment(main, setpos) or ''
req('self._sync_sidebar_position_icons()' in setpos_seg,'dock-side change does not refresh synchronized icons')
# Both icon assets must remain available in every icon family/scheme.
for family in ('ribbon-icons','ribbon-icons-classic','ribbon-icons-original'):
    for scheme in ('light','dark'):
        for name in ('show-sidebar.png','show-sidebar-right.png'):
            req((PACKAGE/'assets'/family/scheme/name).is_file(),f'missing sidebar icon asset: {family}/{scheme}/{name}')
# Exact bounded runtime file plus protected out-of-scope files.
req(sha('widgets/main_window.py')=='66a0aaa77e763f82ef7d715da38e1695bf49e08435b4ae3e536fcc3794ad2f7c','main_window.py changed beyond approved 0.2.23 implementation')
protected={
 'widgets/shell_ribbon.py':'07821888e36c7994db62b97350633517d50a4353c86b01540db5806de8b833a1',
 'app.py':'6a7df3b7c7bbe36a9849599baef805a27d8058a27fd484eb3b553acb2c2e9687',
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
    print('RiqatonyDesk 0.2.23 check failed:')
    [print('- '+e) for e in errors]
    raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.23 bounded App Sidebar dock-side icon synchronization contract')
