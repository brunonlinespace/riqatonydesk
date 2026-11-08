#!/usr/bin/env python3
"""x19.0 Harmony artwork provenance and default family selection contract."""
from pathlib import Path
import hashlib, json, struct
ROOT=Path(__file__).resolve().parents[1]

def checksum(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def check_inventory(root, expected):
    found={p.relative_to(root).as_posix():checksum(p) for p in root.rglob('*.png')}
    assert found==expected, f"Icon inventory/hash differs: missing={sorted(expected.keys()-found.keys())}, extra={sorted(found.keys()-expected.keys())}, changed={sorted(k for k in expected.keys()&found.keys() if found[k]!=expected[k])}"
    for name in expected:
        data=(root/name).read_bytes()
        assert data[:8]==b"\x89PNG\r\n\x1a\n" and len(data)>=24 and struct.unpack(">II",data[16:24])==(64,64),name

harmony=json.loads((ROOT/'qa/x190_harmony_icon_manifest.json').read_text())
assert harmony['family']=='Harmony' and harmony['technical_key']=='new' and harmony['version']=='1.0.0-x19.0'
assert len(harmony['assets'])==296
check_inventory(ROOT/'assets/ribbon-icons',harmony['assets'])
protected=json.loads((ROOT/'qa/x190_preserved_family_manifest.json').read_text())
assert len(protected)==428
actual={}
for fam in ('ribbon-icons-classic','ribbon-icons-original'):
    for p in (ROOT/'assets'/fam).rglob('*.png'):
        actual[p.relative_to(ROOT/'assets').as_posix()]=checksum(p)
assert actual==protected, 'Classic or Legacy PNG bytes/inventory changed'
assert not list((ROOT/'assets').rglob('*.svg')), 'Packaged SVG asset remains'
main=(ROOT/'widgets/main_window.py').read_text()
editor=(ROOT/'widgets/editor_commands_appearance.py').read_text()
helptext=(ROOT/'widgets/window_parts/help_actions.py').read_text()
config=(ROOT/'services/config_service.py').read_text()
for text in (main,editor,helptext):
    assert 'Rico Icons Harmony' in text and 'Rico Icons Modern' not in text
assert '("new", "Rico Icons Harmony")' in main
assert '("new","Rico Icons Harmony")' in editor
assert '"editor_icon_set": "new"' in config
assert '"original": "ribbon-icons-original"' in main
assert '"classic": "ribbon-icons-classic"' in main
assert '}.get(icon_set, "ribbon-icons")' in main
print('PASS: Harmony default, source artwork hashes, PNG-only and Classic/Legacy preservation')
