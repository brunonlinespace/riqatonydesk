#!/usr/bin/env python3
"""x191 source-bound supplied-icon provenance and exact approved action binding gate."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
reference=json.loads((ROOT/'qa/x191_icon_provenance.json').read_text(encoding='utf-8'))
assert set(reference)=={'ribbon-icons','ribbon-icons-classic','ribbon-icons-original'}
for family,items in reference.items():
    assert len(items)==288,(family,len(items))
    for rel,expected in items.items():
        path=ROOT/'assets'/family/rel
        data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==expected,(family,rel)
        assert data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(64,64),(family,rel)
    for mode in ('light','dark'):
        names={p.stem for p in (ROOT/'assets'/family/mode).glob('*.png')}
        assert {'find','heading-group','link-group','icons-legacy','icons-new','icons-classic','dirty-duplicate-policy','dirty-external-policy',*(f'heading-{n}' for n in range(7))} <= names,(family,mode)
editor=(ROOT/'widgets/editor_commands_appearance.py').read_text(encoding='utf-8')
for label in ('Riqa Icons Harmony','Riqa Icons Humility','Riqa Icons Heritage'):
    assert label in editor,label
for forbidden in ('"Rico Icons Harmony"','"Rico Icons Classic"','"Rico Icons Legacy"'):
    assert forbidden not in editor,forbidden
assert 'self.bind_custom_icon(link_menu.menuAction(),"link-group")' in editor
assert 'self.bind_custom_icon(heading_menu.menuAction(),"heading-group")' in editor
assert 'self.bind_custom_icon(action,f"heading-{level}")' in editor
assert '"new"' in editor and '"classic"' in editor and '"original"' in editor
main=(ROOT/'widgets/main_window.py').read_text(encoding='utf-8')
for token in ('"search_bar_action":"find"','"icon_new_action":"icons-new"','"icon_classic_action":"icons-classic"','"icon_original_action":"icons-legacy"','"paragraph_style_menu_action":"heading-group"','"link_menu_action":"link-group"','"dirty_external_tabbed_action":"dirty-external-policy"','"dirty_duplicate_tabbed_action":"dirty-duplicate-policy"','self._toolbar_icon_path(f"heading-{level}")'):
    assert token in main,token
assert '"editor_icon_set": "new"' in (ROOT/'services/config_service.py').read_text(encoding='utf-8')
assert 'APP_VERSION = "1.0.0-x19.1"' in (ROOT/'__init__.py').read_text(encoding='utf-8')
# Explicit exclusion: this release must not remap the toolbar-layout icons.
assert '"toolbar-tabbed"' not in editor and '"toolbar-classic"' not in editor
print('PASS: supplied family bytes, exact icon wiring, labels and deferred toolbar-layout icons')
