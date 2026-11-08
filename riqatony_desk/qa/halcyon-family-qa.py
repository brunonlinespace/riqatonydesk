#!/usr/bin/env python3
"""Edition 1.0.0-x19.5 Halcyon artwork and selection contract."""
from pathlib import Path
import zipfile, hashlib
root=Path(__file__).resolve().parents[1]
outer=root.parent
scheme_set={'dark','light'}
assets=root/'assets'/'ribbon-icons-aero'
assert {p.name for p in assets.iterdir()} == scheme_set
for scheme in scheme_set:
    members=list((assets/scheme).glob('*.png'))
    assert len(members)==144,(scheme,len(members))
    assert (assets/scheme/'app-icons.png').is_file()
source=(root/'widgets/editor_commands_appearance.py').read_text()
assert '("aero","Riqa Icons Halcyon")' in source
assert '"aero": "ribbon-icons-aero"' in source
assert '"aero"' in source
main=(root/'widgets/main_window.py').read_text()
assert '("aero", "Riqa Icons Halcyon")' in main
assert 'for n in ("new","classic","original","aero"):' in main
assert '"icon_aero_action"' not in main
assert '"aero": "ribbon-icons-aero"' in main
for src in ('dashboard_card.py','dashboard.py','folder_dashboard.py'):
    assert '"aero": "ribbon-icons-aero"' in (root/'widgets/workspace'/src).read_text(),src
ribbon=(root/'widgets/shell_ribbon.py').read_text()
assert 'icon_aero_action' not in ribbon
print('PASS Halcyon fourth AppMenu-only family and artwork inventory')
