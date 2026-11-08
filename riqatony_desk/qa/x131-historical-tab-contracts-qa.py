#!/usr/bin/env python3
"""Replay the untouched x13.0 historical-tab adapter against exact x13.0 source.

The old script and old references remain byte-for-byte untouched. The only
adaptation provides the reassembled predecessor MainWindow in memory.
"""
from __future__ import annotations
import hashlib
import json
import runpy
from pathlib import Path
from unittest.mock import patch

PKG=Path(__file__).resolve().parents[1]
main_path=PKG/'widgets/main_window.py'
mixin_path=PKG/'widgets/window_parts/navigation_history.py'
ref=json.loads((PKG/'qa/x131-preservation-reference.json').read_text())
main=main_path.read_text()
body=mixin_path.read_text().split('class NavigationHistoryMixin:\n',1)[1]
restored=main.replace('from riqatony_desk.widgets.window_parts.navigation_history import NavigationHistoryMixin\n','')
restored=restored.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, QMainWindow):',
                          'class MainWindow(DocumentTabsMixin, QMainWindow):')
anchor='    def eventFilter(self, watched, event) -> bool:\n'
assert restored.count(anchor)==1
restored=restored.replace(anchor,body+anchor,1)
assert hashlib.sha256(restored.encode()).hexdigest()==ref['baseline_main_window_sha256']
original=Path.read_text
normalized=main_path.resolve()
def read_as_x130(self,*args,**kwargs):
    if self.resolve()==normalized:return restored
    return original(self,*args,**kwargs)
with patch.object(Path,'read_text',read_as_x130):
    runpy.run_path(str(PKG/'qa/x130-historical-tab-contracts-qa.py'),run_name='__main__')
print('PASS: original x13.0 historical tab assertions replayed on reconstructed predecessor')
