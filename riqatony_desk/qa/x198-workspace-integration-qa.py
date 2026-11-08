#!/usr/bin/env python3
"""Current Qt workspace integration: preserve x13.4 adapter and historic test.

Only adapt the two known predecessor contracts in-memory:
  - old shortcuts-dialog import path (the existing x13.4 adapter), and
  - Dashboard Edit button's x19.2 replacement of the historical Open label.
The historical test, preserved adapter and all other assertions stay intact.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import runpy
import sys

QA = Path(__file__).resolve().parent
PKG = QA.parent
REF = json.loads((QA / 'x198-preservation.json').read_text(encoding='utf-8'))
HISTORIC = QA / 'workspace-integration-qa.py'
OLD_LABEL = 'require(card.edit_button.text() == "Open" and card.view_only_button.text() == "View Only", "Dashboard actions changed")'
NEW_LABEL = 'require(card.edit_button.text() == "Edit" and card.view_only_button.text() == "View Only", "Dashboard actions changed")'


def preserved_adapter_source() -> str:
    expected = REF['x197_historical_hashes']
    for filename, key in (
        ('workspace-integration-qa.py', 'historic_workspace'),
        ('x134-workspace-integration-qa.py', 'x134_adapter'),
    ):
        actual = hashlib.sha256((QA / filename).read_bytes()).hexdigest()
        if actual != expected[key]:
            raise AssertionError(f'Protected historical QA modified: {filename}')
    # The x13.4 adapter checks its own historical SHA and changes precisely
    # the original single legacy import. It does not change any assertions.
    original = runpy.run_path(str(QA / 'x134-workspace-integration-qa.py'))['adapted_source']()
    if original.count(OLD_LABEL) != 1 or NEW_LABEL in original:
        raise AssertionError('Unexpected Dashboard card assertion in historic QA')
    adapted = original.replace(OLD_LABEL, NEW_LABEL, 1)
    if adapted.replace(NEW_LABEL, OLD_LABEL, 1) != original:
        raise AssertionError('Current adapter modified more than Dashboard label')
    current_card = (PKG/'widgets/workspace/dashboard_card.py').read_text(encoding='utf-8')
    if 'self.edit_button = self._button("Edit", role="primary", grid=grid)' not in current_card:
        raise AssertionError('Current Dashboard Edit label no longer matches app')
    compile(adapted, str(HISTORIC), 'exec')
    return adapted


def main() -> None:
    source = preserved_adapter_source()
    if '--static' in sys.argv[1:]:
        print('PASS x19.8: historical workspace test preserved; current Dashboard Edit assertion adapted')
        return
    sys.path.insert(0, str(PKG.parent))
    namespace = {'__name__': '__main__', '__file__': str(HISTORIC), '__package__': None}
    exec(compile(source, str(HISTORIC), 'exec'), namespace)


if __name__ == '__main__':
    main()
