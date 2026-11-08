#!/usr/bin/env python3
"""Run existing x13.1 historical-tab contract on byte-exact reconstructed x13.1 source.

Does not alter the historical test or its baseline. The current release moves only
LayoutControlsMixin out of the original window.
"""
from __future__ import annotations
import hashlib
import json
import runpy
from pathlib import Path
from unittest.mock import patch

PKG = Path(__file__).resolve().parents[1]
main = PKG/'widgets/main_window.py'
layout = PKG/'widgets/window_parts/layout_controls.py'
ref=json.loads((PKG/'qa/x132-preservation-reference.json').read_text())
window=main.read_text()
body=layout.read_text().split('class LayoutControlsMixin:\n',1)[1]
reconstructed=window.replace('from riqatony_desk.widgets.window_parts.layout_controls import LayoutControlsMixin\n','')
reconstructed=reconstructed.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):',
    'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, QMainWindow):')
reconstructed=reconstructed.replace('from riqatony_desk.widgets.workspace.navigation import NavigationWidget\n',
    'from riqatony_desk.widgets.workspace.navigation import NavigationWidget, SIDEBAR_MINIMUM_WIDTH\n')
anchor='    def _sync_view_actions(self, mode: str) -> None:\n'
assert reconstructed.count(anchor)==1
reconstructed=reconstructed.replace(anchor,body+anchor,1)
assert hashlib.sha256(reconstructed.encode()).hexdigest()==ref['baseline_main_window_sha256']
original=Path.read_text
normal=main.resolve()
def read_old(self,*args,**kwargs):
    if self.resolve()==normal:return reconstructed
    return original(self,*args,**kwargs)
with patch.object(Path,'read_text',read_old):
    runpy.run_path(str(PKG/'qa/x131-historical-tab-contracts-qa.py'),run_name='__main__')
print('PASS: x13.1 archived navigation/tab adapter replayed on x13.1 predecessor')
