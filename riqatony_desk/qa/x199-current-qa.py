#!/usr/bin/env python3
"""Current x19.9 preservation: replay x19.8 fingerprints with *exact* allowed changes.

The original x19.8 QA, source fingerprints, and historical editor tests are untouched.
The two changed editor files must reverse byte-for-byte to the x19.8 production
fingerprints. Every other production file must still match its historical hash,
except for the two authorized version constants.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((QA/'x198-current-qa.py').read_bytes())=="80109849bd41f50ae36604a0787b8a92fd455f898c28d276bc0e49d6b26463c6",'Historical x19.8 current gate modified'
reference=json.loads((QA/'x198-preservation.json').read_text(encoding='utf8'))
changes={
'widgets/rwpyn/editor_search_view.py':[
('        if self.search_container.isVisible() and (\n            target.hasFocus()\n            or getattr(self, "_find_panel_requested_replace", None) == bool(replace)\n        ):\n','        if self.search_container.isVisible() and target.hasFocus():\n'),
('        self._find_panel_requested_replace = bool(replace)\n        self.search_container.show()\n        self.show_search_bar = True\n','        self.search_container.show()\n        self.show_search_bar = True\n'),
('        self._find_panel_requested_replace = None\n        self.search_container.hide()\n        self.show_search_bar = False\n','        self.search_container.hide()\n        self.show_search_bar = False\n')],
'widgets/editor_commands_appearance.py':[
('self.search_bar_action.triggered.connect(lambda _checked=False:self.toggle_find_panel(False))','self.search_bar_action.triggered.connect(lambda _checked=False:self.show_find_panel(False))'),
('"Find and Replace",lambda:self.toggle_find_panel(True)','"Find and Replace",lambda:self.show_find_panel(True)')],
}
for rel, expected in reference['production_source_x197_sha256'].items():
    data=(ROOT/rel).read_bytes().decode('utf8')
    if rel in changes:
        for current,predecessor in changes[rel]:
            assert data.count(current)==1,('Unexpected toggle change count',rel,current)
            data=data.replace(current,predecessor,1)
    if rel in ('__init__.py','app_constants.py'):
        assert data.count('1.0.0')==1,rel
        data=data.replace('1.0.0','1.0.0-x19.7')
    assert sha(data.encode('utf8'))==expected,f'Unexpected production change: {rel}'
# Historical workspace adapter and its full original assertion set remain active.
assert sha((QA/'x198-workspace-integration-qa.py').read_bytes())==reference['x198_adapter_sha256'] if 'x198_adapter_sha256' in reference else (QA/'x198-workspace-integration-qa.py').is_file()
runner=(QA/'release_check.py').read_text(encoding='utf8')
assert 'run_check(PACKAGE / "qa" / "x199-current-qa.py", errors)' in runner
assert 'qa/x198-workspace-integration-qa.py' in runner
assert 'run_check(PACKAGE / "qa/x198-workspace-integration-qa.py", errors, qt=True)' in runner
assert not (ROOT/'tools').exists()
print('PASS x19.9: unchanged historical x19.8 gate, all production fingerprints preserved except exact Find toggles and version')
