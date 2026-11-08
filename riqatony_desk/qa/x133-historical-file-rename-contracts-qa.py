#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Replay unchanged historical file/folder rename QA with x13.2 source shape."""
from __future__ import annotations
import hashlib,json,runpy
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]
ref=json.loads((P/'qa/x133-preservation-reference.json').read_text())
main=P/'widgets/main_window.py'
current=main.read_text()
body=(P/'widgets/window_parts/help_actions.py').read_text().split('class HelpActionsMixin:\n',1)[1]
restored=current.replace('from riqatony_desk.widgets.window_parts.help_actions import HelpActionsMixin\n','')
restored=restored.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, QMainWindow):',
 'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):')
restored=restored.replace('    def _update_action_states(self, *_args) -> None:',
 body+'    def _update_action_states(self, *_args) -> None:',1)
assert hashlib.sha256(restored.encode()).hexdigest()==ref['baseline_main_window_sha256']
orig=Path.read_text;target=main.resolve()
def read_original(self,*a,**kw):
 if self.resolve()==target:return restored
 return orig(self,*a,**kw)
with patch.object(Path,'read_text',read_original):
 runpy.run_path(str(P/'qa/folder-rename-qa.py'),run_name='__main__')
print('PASS x13.3: historical F2 folder-rename QA replayed against exact x13.2 MainWindow')
