#!/usr/bin/env python3
"""1.0.0-x19.3: exact, four-file Heritage-only patch, with historic provenance retained."""
from pathlib import Path
from hashlib import sha256
from struct import unpack
import json
ROOT=Path(__file__).resolve().parents[1]
prior=json.loads((ROOT/'qa/x192_icon_provenance.json').read_text(encoding='utf-8'))
replacements={
    "dark/external-editor.png": "f1813b2e7dcb5ac9fb59abab187cf8658fccff307bc8ab5fdc81c3ee124177f4",
    "dark/launch-last-file.png": "4f188dc67d2fe22ace83b768bf66fbdfdc381821f7a3945a6acd740cf5f31aa0",
    "light/external-editor.png": "6eb5fe3025d38b31494e072904b58f96a92c005d456ed24f09db98afca2cefb4",
    "light/launch-last-file.png": "9c8b2b60b1851e2686a1d292c0a391f46ecbbc58e6489bec3d5b68a7d097db99"
}
assert set(replacements)=={'dark/external-editor.png','dark/launch-last-file.png','light/external-editor.png','light/launch-last-file.png'}
for family, old_hashes in prior.items():
    root=ROOT/'assets'/family
    for rel,original_hash in old_hashes.items():
        path=root/rel
        current=path.read_bytes()
        expected=replacements[rel] if family=='ribbon-icons-original' and rel in replacements else original_hash
        assert sha256(current).hexdigest()==expected,(family,rel)
        assert current[:8]==b'\x89PNG\r\n\x1a\n' and unpack('>II',current[16:24])==(64,64),(family,rel)
    assert set(old_hashes) <= {p.relative_to(root).as_posix() for p in root.rglob('*.png')},family
    if family=='ribbon-icons-original':
        assert set(replacements) <= set(old_hashes), 'four updates must replace preexisting Heritage icons'
for rel in replacements:
    assert sha256((ROOT/'assets/ribbon-icons-original'/rel).read_bytes()).hexdigest()==replacements[rel],rel
# Historical exact-hash evidence is retained unchanged rather than rewritten to masquerade as an old release.
assert 'APP_VERSION = "1.0.0-x19.3"' in (ROOT/'__init__.py').read_text(encoding='utf-8')
print('PASS: 1.0.0-x19.3: exact four Heritage PNGs, all other recorded icon bytes unchanged')
