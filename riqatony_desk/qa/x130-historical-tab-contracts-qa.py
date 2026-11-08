#!/usr/bin/env python3
"""Run unchanged earlier UI assertions against the byte-exact x12.1 MainWindow.

The contemporary x13.0 preservation check proves this reconstruction equals
all x12.1 bytes. Only the location of the original tab methods has changed.
No historical QA script or reference is edited or rewritten.
"""
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from unittest.mock import patch

PKG=Path(__file__).resolve().parents[1]
main_path=PKG/'widgets/main_window.py'
mixin_path=PKG/'widgets/window_parts/document_tabs.py'
ref=json.loads((PKG/'qa/x130-preservation-reference.json').read_text())
main=main_path.read_text()
mixin=mixin_path.read_text()
method_block=mixin.split('class DocumentTabsMixin:\n',1)[1]
toggle_i=method_block.index('    def _toggle_tabs_mode(')
block,toggle=method_block[:toggle_i],method_block[toggle_i:]
restored=main.replace('from riqatony_desk.widgets.window_parts.document_tabs import DocumentTabsMixin\n','')
restored=restored.replace('class MainWindow(DocumentTabsMixin, QMainWindow):','class MainWindow(QMainWindow):')
restored=restored.replace('    def _queue_navigation_record(',block+'    def _queue_navigation_record(',1)
restored=restored.replace('    def _sync_app_settings_toggle_actions(',toggle+'    def _sync_app_settings_toggle_actions(',1)
assert hashlib.sha256(restored.encode()).hexdigest()==ref['baseline_main_window_sha256'], 'main source reconstruction mismatch'

# The legacy tests still inspect the same exact original MainWindow source;
# the only adapter is the in-memory source they would have read at x12.1.
original_read=Path.read_text
normalized_main=main_path.resolve()
def read_historical_main(self,*args,**kwargs):
    if self.resolve()==normalized_main:
        return restored
    return original_read(self,*args,**kwargs)
with patch.object(Path,'read_text',read_historical_main):
    for name in ('exp6-r1-ui-qa.py','x121-current-path-contracts-qa.py'):
        runpy.run_path(str(PKG/'qa'/name),run_name='__main__')
print('PASS: historical x12.1 tab-source assertions replayed unchanged against byte-identical reconstructed source')
