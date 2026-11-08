#!/usr/bin/env python3
"""x19.8 QA-only hotfix: immutable predecessor, safe adapter, unchanged runtime."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import runpy

PKG = Path(__file__).resolve().parents[1]
QA = PKG/'qa'
reference = json.loads((QA/'x198-preservation.json').read_text(encoding='utf-8'))
sha = lambda b: hashlib.sha256(b).hexdigest()
assert not (PKG/'tools').exists()
assert (QA/'release_check.py').is_file()
for name,key in [('workspace-integration-qa.py','historic_workspace'),
                 ('x134-workspace-integration-qa.py','x134_adapter'),
                 ('x197_tools_to_qa_qa.py','x197_check')]:
    assert sha((QA/name).read_bytes()) == reference['x197_historical_hashes'][key], name
for rel, expected in reference['production_source_x197_sha256'].items():
    source = (PKG/rel).read_bytes()
    if rel in ('__init__.py', 'app_constants.py'):
        source = source.replace(b'1.0.0-x19.8',b'1.0.0-x19.7')
    assert sha(source) == expected, f'Runtime source differs: {rel}'
# The x19.7 current check still validates all sidebar and former tools
# contracts. Replay it in memory with its sole edition-specific version
# expectation advanced; do not rewrite this historical check.
old=(QA/'x197_tools_to_qa_qa.py').read_text(encoding='utf-8')
a='APP_VERSION = "1.0.0-x19.7"'
b='APP_VERSION = "1.0.0-x19.8"'
assert old.count(a)==1
adapted=old.replace(a,b,1)
assert adapted.replace(b,a,1)==old
exec(compile(adapted,str(QA/'x197_tools_to_qa_qa.py'),'exec'),{'__file__':str(QA/'x197_tools_to_qa_qa.py'),'__name__':'x197_historical_replay'})
runner=(QA/'release_check.py').read_text(encoding='utf-8')
assert 'qa/x198-workspace-integration-qa.py' in runner
assert 'run_check(PACKAGE / "qa" / "x198-current-qa.py", errors)' in runner
adapter = runpy.run_path(str(QA/'x198-workspace-integration-qa.py'))['preserved_adapter_source']()
assert 'require(card.edit_button.text() == "Edit" and card.view_only_button.text() == "View Only", "Dashboard actions changed")' in adapter
assert 'require(card.edit_button.text() == "Open" and card.view_only_button.text() == "View Only", "Dashboard actions changed")' not in adapter
print('PASS x19.8: QA-only hotfix, historical files intact, runtime unchanged')
