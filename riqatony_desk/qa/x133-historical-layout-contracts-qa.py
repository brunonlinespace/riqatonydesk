#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Replay x13.2 navigation contract with exact original x13.2 Help methods restored.

No prior QA or release history is modified. The historical path reader sees an
in-memory reconstruction of the original predecessor's MainWindow source.
"""
from __future__ import annotations
import hashlib,json,runpy
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]
ref=json.loads((P/'qa/x133-preservation-reference.json').read_text())
main=P/'widgets/main_window.py'
current=main.read_text()
mixin=(P/'widgets/window_parts/help_actions.py').read_text()
body=mixin.split('class HelpActionsMixin:\n'.replace('\n','\n'),1)[1]
restored=current.replace('from riqatony_desk.widgets.window_parts.help_actions import HelpActionsMixin\n'.replace('\n','\n'),'')
restored=restored.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, QMainWindow):',
 'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):')
restored=restored.replace('    def _update_action_states(self, *_args) -> None:',body+'    def _update_action_states(self, *_args) -> None:',1)
assert hashlib.sha256(restored.encode()).hexdigest()==ref['baseline_main_window_sha256']
old=Path.read_text;name=main.resolve()
def read_historical(self,*args,**kwargs):
 if self.resolve()==name:return restored
 return old(self,*args,**kwargs)
with patch.object(Path,'read_text',read_historical):
 runpy.run_path(str(P/'qa/x132-historical-navigation-contracts-qa.py'),run_name='__main__')
print('PASS x13.3: previous x13.2 historical navigation assertions replayed without source changes')
