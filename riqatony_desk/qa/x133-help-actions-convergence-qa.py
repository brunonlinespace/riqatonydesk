#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.3: enforce byte-exact five-method extraction and complete x13.2 provenance."""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parent
REF=json.loads((P/'qa/x133-preservation-reference.json').read_text())
BASE=REF['baseline_sha256_by_path'];OLD='1.0.0-x13.2';NEW='1.0.0-x13.3'
MAIN='riqatony_desk/widgets/main_window.py';MIX='riqatony_desk/widgets/window_parts/help_actions.py'
MANIFEST='riqatony_desk/SOURCE_MANIFEST.sha256';RELEASE='riqatony_desk/tools/release_check.py'
NOTES=['riqatony_desk/docs/RELEASE_NOTES.md','riqatony_desk/docs/CHANGELOG.md']
ARCH='riqatony_desk/docs/ARCHITECTURE.md';APPSTREAM=REF['appstream_path']
errors=[]
def digest(b):return hashlib.sha256(b).hexdigest()
def check(ok,why):
 if not ok:errors.append(why)
check((REF['baseline_version'],REF['new_version'])==(OLD,NEW),'wrong version pedigree')
check(REF['baseline_main_window_sha256']==BASE[MAIN],'baseline MainWindow fingerprint mismatch')
actual={f.relative_to(ROOT).as_posix() for f in ROOT.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ('.pyc','.pyo') and f.relative_to(ROOT).parts[:2] not in [('riqatony_desk','dist'),('riqatony_desk','build')]}
expected=set(BASE)|set(REF['new_files'])
check(actual==expected,'source inventory mismatch: added='+str(sorted(actual-expected)[:6])+', missing='+str(sorted(expected-actual)[:6]))
allowed=set(REF['metadata_paths'])|{MAIN,RELEASE,MANIFEST,ARCH,APPSTREAM,*NOTES}
for rel,d in BASE.items():
 f=ROOT/rel
 check(f.is_file(),'missing frozen predecessor path: '+rel)
 if f.is_file() and rel not in allowed:
  check(digest(f.read_bytes())==d,'protected production or historical file rewritten: '+rel)
for rel in REF['metadata_paths']:
 s=(ROOT/rel).read_text()
 check(NEW in s,'new identity missing: '+rel)
 check(digest(s.replace(NEW,OLD).encode())==BASE[rel],'unrelated metadata edit: '+rel)
for rel in NOTES:
 b=(ROOT/rel).read_bytes();oldlen=REF['historical_document_lengths'][rel]
 check(digest(b[-oldlen:])==BASE[rel],'previous release history modified: '+rel)
 check(digest(b[:-oldlen])==REF['history_prefix_sha256'][rel],'new release note modified: '+rel)
b=(ROOT/ARCH).read_bytes();n=REF['architecture_prefix_length']
check(digest(b[:n])==BASE[ARCH],'historical architecture content changed')
check(digest(b[n:])==REF['architecture_suffix_sha256'],'new architecture note changed')
window=(ROOT/MAIN).read_text();mix=(ROOT/MIX).read_text()
marker='class HelpActionsMixin:\n'
check(mix.count(marker)==1,'missing or duplicate HelpActionsMixin')
if mix.count(marker)==1:
 body=mix.split(marker,1)[1]
 check(digest(body.encode())==REF['relocated_method_block_sha256'],'five Help methods changed')
 restored=window.replace('from riqatony_desk.widgets.window_parts.help_actions import HelpActionsMixin\n','')
 restored=restored.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, QMainWindow):',
 'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):')
 anchor=REF['main_insert_anchor']
 check(restored.count(anchor)==1,'original Help insertion point missing')
 restored=restored.replace(anchor,body+anchor,1)
 check(digest(restored.encode())==BASE[MAIN],'original x13.2 MainWindow cannot be reconstructed exactly')
 mx=ast.parse(mix);w=ast.parse(window)
 mixcls=next((c for c in mx.body if isinstance(c,ast.ClassDef) and c.name=='HelpActionsMixin'),None)
 maincls=next((c for c in w.body if isinstance(c,ast.ClassDef) and c.name=='MainWindow'),None)
 if mixcls and maincls:
  names=[f.name for f in mixcls.body if isinstance(f,ast.FunctionDef)]
  other=[f.name for f in maincls.body if isinstance(f,ast.FunctionDef)]
  check(names==REF['method_names'] and len(names)==5,'incorrect five Help method inventory')
  check(not set(names)&set(other),'Help methods duplicated in MainWindow')
  check([getattr(b,'id',None) for b in maincls.bases]==['DocumentTabsMixin','NavigationHistoryMixin','LayoutControlsMixin','HelpActionsMixin','QMainWindow'], 'MainWindow method resolution order changed')
  for method in ('__init__','_connect_signals','eventFilter','closeEvent','_build_menu_bar'):
   check(method in other,'Qt ownership method no longer in MainWindow: '+method)
  for phrase in ('self.about_dialog: AboutDialog | None = None','self.shortcuts_dialog: ShortcutsDialog | None = None','self.quick_tour_dialog: QWizard | None = None'):
   check(phrase in window,'Qt dialog state moved or renamed: '+phrase)
 else:check(False,'Help or MainWindow class missing')
xml=(ROOT/APPSTREAM).read_text()
check('<release version="'+NEW+'"' in xml and '<release version="'+OLD+'"' not in xml,'current-only AppStream metadata not refreshed')
gate=(ROOT/RELEASE).read_text()
for test in ('x133-help-actions-convergence-qa.py','x133-help-actions-headless-qa.py','x133-historical-help-contracts-qa.py'):
 check(test in gate,'current release gate omits '+test)
if errors:
 print('FAIL x13.3 Help extraction:')
 for err in errors:print('-',err)
 raise SystemExit(1)
print('PASS x13.3: five byte-exact Help methods; full x13.2 predecessor and historical records preserved')
