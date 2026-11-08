#!/usr/bin/env python3
"""Execute historical UI assertion logic with only x12.1 source-path remapping.

The historic source files remain byte-for-byte unchanged. No expected values,
feature claims, assertions, or method bodies are rewritten or suppressed.
"""
from __future__ import annotations
import contextlib
import io
from pathlib import Path

HERE=Path(__file__).resolve().parent
LEGACY=(
 'editor-surface-contract-qa.py',
 'exp7-r1-tour-about-qa.py',
 'exp7-r2-about-links-qa.py',
 'phase1-convergence-qa.py',
 'discoverability-integration-qa.py',
)
WORKSPACE=('navigation','dashboard','dashboard_card','folder_dashboard')
DIALOGS=('about_dialog','closing_dialog','first_run_dialog','projects_dialog','resolve_open_documents_dialog','shortcuts_dialog')
for name in LEGACY:
 path=HERE/name
 original=path.read_text(encoding='utf-8')
 current=original
 for module in WORKSPACE:
  current=current.replace('widgets/'+module+'.py','widgets/workspace/'+module+'.py')
  current=current.replace('"widgets" / "'+module+'.py"', '"widgets" / "workspace" / "'+module+'.py"')
 for module in DIALOGS:
  current=current.replace('widgets/'+module+'.py','widgets/dialogs/'+module+'.py')
  current=current.replace('"widgets" / "'+module+'.py"', '"widgets" / "dialogs" / "'+module+'.py"')
 if current==original:
  raise AssertionError('historical test not adapted: '+name)
 namespace={'__file__':str(path),'__name__':'__main__'}
 with contextlib.redirect_stdout(io.StringIO()) as buf:
  exec(compile(current,str(path),'exec'),namespace)
 print('PASS: current-path assertions from '+name+' (historical file untouched)')
print('PASS: five historical UI/workspace contracts re-executed against relocated sources')
