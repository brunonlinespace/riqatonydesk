#!/usr/bin/env python3
"""x19.2: supplied-only icon inventories and approved Desk action wiring."""
from pathlib import Path
import hashlib,json,struct
P=Path(__file__).resolve().parents[1]
source=P.parent
inventory=json.loads((P/'qa/x192_icon_provenance.json').read_text(encoding='utf-8'))
assert set(inventory)=={'ribbon-icons','ribbon-icons-classic','ribbon-icons-original'}
for family, expected in inventory.items():
    root=P/'assets'/family
    actual={p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}
    assert len(actual)==288,(family,len(actual))
    assert set(actual)==set(expected),(family,sorted(set(actual)-set(expected)),sorted(set(expected)-set(actual)))
    for rel,p in actual.items():
        blob=p.read_bytes()
        assert hashlib.sha256(blob).hexdigest()==expected[rel],(family,rel)
        assert p.suffix=='.png' and blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(64,64)
    for variant in ('dark','light'):
        assert len(list((root/variant).glob('*.png')))==144,(family,variant)
        for obsolete in ('search-toggle','dark-mode','light-theme','markdown-source','open-external-file','paste-markdown','system-theme'):
            assert not (root/variant/(obsolete+'.png')).exists(),(family,variant,obsolete)
main=(P/'widgets/main_window.py').read_text(encoding='utf-8')
card=(P/'widgets/workspace/dashboard_card.py').read_text(encoding='utf-8')
expected_main={
    'import_file_action':'import-file',
    'left_sidebar_action':'dock-left',
    'right_sidebar_action':'dock-right',
    'sidebar_action':'show-sidebar',
    'tabs_enabled_action':'tabs-enabled',
    'tabs_disabled_action':'tabs-disabled',
    'app_dashboard_menu_action':'app-dashboard',
    'app_launch_screen_menu_action':'app-launch-screen',
    'app_file_launch_menu_action':'file-launch',
    'search_bar_action':'find',
    'paragraph_style_menu_action':'heading-group',
    'link_menu_action':'link-group',
    'icon_new_action':'icons-new',
    'icon_classic_action':'icons-classic',
    'icon_original_action':'icons-legacy',
    'dirty_external_tabbed_action':'dirty-external-policy',
    'dirty_duplicate_tabbed_action':'dirty-duplicate-policy',
}
for action,icon in expected_main.items():
    assert f'"{action}":"{icon}"' in main,(action,icon)
assert '"show-sidebar-right" if self._sidebar_position() == "right" else "show-sidebar"' in main
assert 'self.sidebar_action.setIcon(icon)' in main
assert 'self.app_sidebar_menu_action.setIcon(icon)' in main
for icon in ('app-dashboard','app-launch-screen','file-launch'):
    assert f'"{icon}"' in main
assert '"""Keep AppMenu group glyphs stable regardless of radio selection."""' in main
assert 'parent.setIcon(selected.icon())' not in main, 'AppMenu icon overwritten by selected radio'
assert '(self.app_tabs_toggle_action, "tabs-enabled" if bool(self.config.get("tabs_enabled", True)) else "tabs-disabled")' in main
assert 'self.edit_button = self._button("Edit", role="primary", grid=grid)' in card
assert 'self.edit_button.setToolTip("Edit this RTF file")' in card
assert '(self.edit_button, "file-launch"),' in card
assert '(self.edit_button, "open"),' not in card
assert 'self.edit_button.clicked.connect(lambda: self.open_requested.emit(self.document))' in card
assert 'APP_VERSION = "1.0.0-x19.2"' in (P/'__init__.py').read_text(encoding='utf-8')
# No toolbar layout icons wired in this release.
assert '"toolbar-tabbed"' not in main and '"toolbar-classic"' not in main
print('PASS: x19.2 authoritative icon inventory, Desk dashboard, AppMenu/Ribbon, and deferred toolbar icons')
