#!/usr/bin/env python3
"""x13.4: immutable x13.3 production, authentic x11.2 QA, intact x13.3 adapters."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import ast

PKG = Path(__file__).resolve().parents[1]
SOURCE = PKG.parent
REF = json.loads((PKG / 'qa/x134-preservation-reference.json').read_text(encoding='utf-8'))
BASE = REF['baseline_sha256_by_path']
sha = lambda data: hashlib.sha256(data).hexdigest()
errors=[]
def require(condition: bool, why: str) -> None:
    if not condition: errors.append(why)

require(REF['baseline_version']=='1.0.0-x13.3' and REF['new_version']=='1.0.0-x13.4','wrong edition ancestry')
allowed = set(REF['metadata_paths']) | {
    'riqatony_desk/SOURCE_MANIFEST.sha256', 'riqatony_desk/tools/release_check.py',
    'riqatony_desk/docs/RELEASE_NOTES.md', 'riqatony_desk/docs/CHANGELOG.md',
} | {f'riqatony_desk/qa/{name}' for name in REF['restored_historical_scripts']}
new_files = {f'riqatony_desk/qa/current_x134/{name}' for name in [REF['current_adapter_helper'], *REF['active_current_adapter_scripts']]}
new_files.update({
 'riqatony_desk/qa/x134-preservation-reference.json',
 'riqatony_desk/qa/x134-current-layout-runner.py',
 'riqatony_desk/qa/x134-workspace-integration-qa.py',
 'riqatony_desk/qa/x134-historical-qa-integrity-qa.py',
 'riqatony_desk/docs/RELEASE_CHECKLIST-x13.4.md',
})
actual = {f.relative_to(SOURCE).as_posix() for f in SOURCE.rglob('*') if f.is_file()
          and '__pycache__' not in f.parts and f.suffix not in {'.pyc','.pyo'}
          and f.relative_to(SOURCE).parts[:2] not in {('riqatony_desk','build'),('riqatony_desk','dist')}}
require(actual == set(BASE)|new_files, 'Unexpected additions/deletions: '+str(sorted(actual ^ (set(BASE)|new_files))[:8]))
for rel, expected in BASE.items():
    path = SOURCE / rel
    require(path.is_file(), 'Missing previous file: '+rel)
    if path.is_file() and rel not in allowed:
        require(sha(path.read_bytes())==expected, 'Unapproved predecessor edit: '+rel)
for name in REF['restored_historical_scripts']:
    original = PKG / 'qa' / name
    require(sha(original.read_bytes()) == REF['historic_x112_original_sha256'][name],
            'Historical x11.2 QA was not restored exactly: '+name)
for name in [REF['current_adapter_helper'],*REF['active_current_adapter_scripts']]:
    adapter = PKG / 'qa/current_x134' / name
    require(adapter.is_file() and sha(adapter.read_bytes()) == REF['historic_x133_modified_sha256'][name],
            'x13.3 current-layout adapter changed: '+name)
for rel in REF['metadata_paths']:
    new=(SOURCE/rel).read_text(encoding='utf-8')
    reverted = new.replace('1.0.0-x13.4', '1.0.0-x13.3')
    if rel == 'README.md':
        reverted = reverted.replace('Current corrective source edition:', 'Current experimental extraction:')
    if rel.endswith('.metainfo.xml'):
        reverted = reverted.replace(
            'QA historical-integrity correction: restore original historical QA scripts, preserve relocated-module test coverage in current-only adapters and repair the current workspace-integration test path; application behaviour unchanged.',
            'Stage 3 Help and Quick Tour extraction: five unchanged MainWindow methods moved to HelpActionsMixin, preserving wizard, shortcuts, bundled RTF documentation and About dialog behaviour.'
        )
    require(sha(reverted.encode('utf-8'))==BASE[rel],
            'Metadata change exceeds approved current-edition update: '+rel)
for rel, length in REF['history_lengths'].items():
    new=(PKG/rel).read_bytes()
    require(sha(new[-length:])==BASE['riqatony_desk/'+rel], 'Existing release-history text rewritten: '+rel)
    require(sha(new[:-length])==REF['history_prefix_sha256'][rel], 'New release notes mismatch: '+rel)
for rel in ('riqatony_desk/app.py', 'riqatony_desk/rtf_codec.py',
            'riqatony_desk/widgets/main_window.py',
            'riqatony_desk/widgets/rico_theme.py','riqatony_desk/rich_text_support.py'):
    require(sha((SOURCE/rel).read_bytes())==BASE[rel], 'Production implementation modified: '+rel)
release=(PKG/'tools/release_check.py').read_text()
for name in ('x134-historical-qa-integrity-qa.py','x134-current-layout-runner.py','x134-workspace-integration-qa.py'):
    require(name in release,'Missing current gate check: '+name)
for name in REF['restored_historical_scripts']:
    require((PKG/'qa'/name).is_file(), 'Missing historical QA: '+name)
assert len(REF['restored_historical_scripts'])==22
assert len(REF['active_current_adapter_scripts'])==16
if errors:
    for err in errors: print('FAIL x13.4: '+err)
    raise SystemExit(1)
print('PASS x13.4: exact x11.2 historical QA; unmodified x13.3 production; exact current-layout coverage')
