#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.24 App Settings parent icon synchronization gate."""
from __future__ import annotations
import ast, hashlib
from pathlib import Path
from _identity_fingerprint import historical_source_sha, normalize_identity_text
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(rel): return (PACKAGE/rel).read_text(encoding='utf-8')
def sha(rel): return historical_source_sha(PACKAGE/rel)
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "1.0.0-x11.2"' in init,'0.2.24 package identity missing')
req('APP_REVISION = "1.0.0-x11.2"' in constants,'0.2.24 revision identity missing')
req('Current release: **1.0.0-x11.2**' in readme,'README current release stale')
for label in ('App Dashboard','App Launch Screen','App File Launch'):
    req(f'addMenu("{label}")' in main,f'{label} menu label changed')
for label in ('List View','Grid View','Dashboard','Last File','Tabs Enabled','Tabs Disabled'):
    req(f'"{label}"' in main,f'radio option missing or relabelled: {label}')
tree=ast.parse(main); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
def fn(name): return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
sync=ast.get_source_segment(main,fn('_sync_app_settings_menu_icons')) or ''
req('self.grid_action if self.grid_action.isChecked() else self.list_action' in sync,'App Dashboard parent is not driven by checked radio')
req('self.launch_actions["last_file"] if self.launch_actions["last_file"].isChecked() else self.launch_actions["dashboard"]' in sync,'App Launch Screen parent is not driven by checked radio')
req('self.tabs_disabled_action if self.tabs_disabled_action.isChecked() else self.tabs_enabled_action' in sync,'App File Launch parent is not driven by checked radio')
req('parent.setIcon(selected.icon())' in sync,'App Settings parent does not mirror selected radio icon')
refresh=ast.get_source_segment(main,fn('_refresh_action_icons')) or ''
req('self._sync_app_settings_menu_icons()' in refresh,'icon-family/theme refresh does not resynchronize App Settings parent icons')
# Existing state setters remain authoritative and already route through icon refresh.
for name in ('_set_launch_screen','_set_dashboard_view_mode','_sync_tabs_mode_ui'):
    seg=ast.get_source_segment(main,fn(name)) or ''
    req('self._refresh_action_icons()' in seg,f'{name} no longer refreshes selected-state icons')
# Keep prior App Sidebar synchronization intact.
side=ast.get_source_segment(main,fn('_sync_sidebar_position_icons')) or ''
req('self.sidebar_action.setIcon(icon)' in side and 'self.app_sidebar_menu_action.setIcon(icon)' in side,'0.2.23 App Sidebar icon synchronization regressed')
# Selected radial icon assets remain available across all icon families/schemes.
for family in ('ribbon-icons','ribbon-icons-classic','ribbon-icons-original'):
    for scheme in ('light','dark'):
        for name in ('list-view.png','grid-view.png','launch-dashboard.png','launch-last-file.png','drop-active.png','drop-new-window.png'):
            req((PACKAGE/'assets'/family/scheme/name).is_file(),f'missing App Settings icon asset: {family}/{scheme}/{name}')
req(sha('widgets/main_window.py')=='49bf0fa726cbb3153a17361362a3f34ac8792353968609583cfddb508ecc1a94','main_window.py changed beyond approved 0.2.24 implementation')
protected={
 'widgets/shell_ribbon.py':'07821888e36c7994db62b97350633517d50a4353c86b01540db5806de8b833a1',
 'app.py':'6a7df3b7c7bbe36a9849599baef805a27d8058a27fd484eb3b553acb2c2e9687',
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
    print('RiqatonyDesk 0.2.24 check failed:')
    [print('- '+e) for e in errors]
    raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.24 bounded App Settings parent icon synchronization contract')
