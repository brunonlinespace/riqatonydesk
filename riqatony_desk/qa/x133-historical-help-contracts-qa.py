#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Current-structure replay of frozen predecessor Help and Tour source contracts."""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
ref=json.loads((P/'qa/x133-preservation-reference.json').read_text())
main=(P/'widgets/main_window.py').read_text();mix=(P/'widgets/window_parts/help_actions.py').read_text()
body=mix.split('class HelpActionsMixin:\n',1)[1]
restored=main.replace('from riqatony_desk.widgets.window_parts.help_actions import HelpActionsMixin\n','')
restored=restored.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, QMainWindow):',
 'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):')
restored=restored.replace('    def _update_action_states(self, *_args) -> None:',body+'    def _update_action_states(self, *_args) -> None:',1)
assert hashlib.sha256(restored.encode()).hexdigest()==ref['baseline_main_window_sha256']
cl=next(n for n in ast.parse(restored).body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='_show_quick_tour')
add=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='add_page']
assert len(add)==7
rows=[]
for idx,call in enumerate(add):
 assert len(call.args)==(4 if idx==6 else 3)
 vals=[]
 for x in call.args[:3]:
  assert isinstance(x,ast.Constant) and isinstance(x.value,str)
  vals.append(x.value)
 rows.append(vals)
payload=json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()
assert hashlib.sha256(payload).hexdigest()==ref['quick_tour_content_sha256']
for frag in ('wizard.setButton(QWizard.WizardButton.CustomButton1, startup_checkbox)',
             'wizard.setOption(QWizard.WizardOption.HaveCustomButton1, True)',
             '"RTF interoperability and help"','"Welcome to RiqatonyDesk"',
             'path = self.package_root / "docs" / "Documentation.rtf"',
             'dialog = AboutDialog('):
 assert frag in restored,frag
assert 'self.quick_start_action.setToolTip("Quick Tour… — Shift+F1")' in restored
print('PASS x13.3 historical replay: exact x13.2 MainWindow, seven original tour pages and Help contracts')
