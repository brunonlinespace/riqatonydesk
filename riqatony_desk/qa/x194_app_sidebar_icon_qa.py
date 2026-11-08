#!/usr/bin/env python3
"""1.0.0-x19.4: fixed App Sidebar parent, dynamic shared Show Sidebar action."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
main=(ROOT/'widgets/main_window.py').read_text()
tree=ast.parse(main)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
def method(name):
    return ast.get_source_segment(main,next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name))
refresh=method('_refresh_action_icons')
sync=method('_sync_sidebar_position_icons')
group=method('_sync_app_settings_menu_icons')
assert '"app_sidebar_menu_action":"sidebar-settings"' in refresh
assert '"app_sidebar_menu_action":"show-sidebar"' not in refresh
assert '"show-sidebar-right" if self._sidebar_position() == "right" else "show-sidebar"' in sync
assert 'self.sidebar_action.setIcon(QIcon(str(path)))' in sync
assert 'app_sidebar_menu_action' not in sync, 'submenu parent must never inherit the dock-side icon'
assert 'setChecked' not in sync and 'setVisible' not in sync, 'do not modify sidebar check or visibility state'
assert 'self._sync_sidebar_position_icons()' in refresh
assert 'self._sync_sidebar_position_icons()' in (ROOT/'widgets/window_parts/layout_controls.py').read_text()
assert 'self.sidebar_action' in main[main.index('sidebar_menu=self.settings_menu.addMenu("App Sidebar")'):][:280]
assert '"app_sidebar_menu_action"' not in group, 'parent should use fixed mapping'
for fam in ('ribbon-icons','ribbon-icons-classic','ribbon-icons-original'):
    for scheme in ('dark','light'):
        root=ROOT/'assets'/fam/scheme
        for name in ('sidebar-settings','show-sidebar','show-sidebar-right'):
            assert (root/f'{name}.png').is_file(), (fam,scheme,name)
# Repeat x19.3 heritage artwork preservation without executing that edition's
# immutable version-pinned historical QA.
history=ast.parse((ROOT/'qa/x193_heritage_patch_qa.py').read_text())
assign=next(n for n in history.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='replacements' for t in n.targets))
replacements=ast.literal_eval(assign.value)
old=json.loads((ROOT/'qa/x192_icon_provenance.json').read_text())
for fam, records in old.items():
    iconroot=ROOT/'assets'/fam
    actual={p.relative_to(iconroot).as_posix():p for p in iconroot.rglob('*.png')}
    assert set(actual)==set(records),(fam,'icon inventory changed')
    for rel, expected in records.items():
        if fam=='ribbon-icons-original': expected=replacements.get(rel,expected)
        assert hashlib.sha256(actual[rel].read_bytes()).hexdigest()==expected,(fam,rel)
assert 'APP_VERSION = "1.0.0-x19.4"' in (ROOT/'__init__.py').read_text()
print('PASS: x19.4 App Sidebar parent icon fixed; Show Sidebar action remains dynamic and checkable')
