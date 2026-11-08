#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.2: byte-exact extraction and predecessor/historical source preservation."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parent
REF = json.loads((PKG/'qa/x132-preservation-reference.json').read_text())
BASE = REF['baseline_sha256_by_path']
OLD, NEW = '1.0.0-x13.1', '1.0.0-x13.2'
MAIN = 'riqatony_desk/widgets/main_window.py'
MIX = 'riqatony_desk/widgets/window_parts/layout_controls.py'
ARCH = 'riqatony_desk/docs/ARCHITECTURE.md'
MANIFEST = 'riqatony_desk/SOURCE_MANIFEST.sha256'
RELEASE = 'riqatony_desk/tools/release_check.py'
NOTES = ('riqatony_desk/docs/RELEASE_NOTES.md', 'riqatony_desk/docs/CHANGELOG.md')
STREAM = REF['appstream_path']
errors=[]
def check(value, message):
    if not value: errors.append(message)
def digest(content): return hashlib.sha256(content).hexdigest()

check(REF['baseline_version']==OLD and REF['new_version']==NEW,'wrong predecessor or release identity')
check(REF['baseline_main_window_sha256']==BASE[MAIN], 'main fingerprint inconsistency')
actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and
          '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'} and
          not (p.relative_to(ROOT).parts[:2] in [('riqatony_desk','build'),('riqatony_desk','dist')])}
expected = set(BASE) | set(REF['new_files'])
check(actual==expected,'source inventory mismatch: added='+str(sorted(actual-expected)[:10])+ '; missing='+str(sorted(expected-actual)[:10]))
allowed=set(REF['metadata_paths']) | {MAIN, ARCH, RELEASE, STREAM, MANIFEST, *NOTES}
for rel, original_hash in BASE.items():
    path=ROOT/rel
    check(path.is_file(), 'missing original file: '+rel)
    if path.is_file() and rel not in allowed:
        check(digest(path.read_bytes())==original_hash,'historical/protected content modified: '+rel)
for rel in [p for p in REF['metadata_paths'] if p != RELEASE]:
    text=(ROOT/rel).read_text()
    check(NEW in text, 'new identity missing: '+rel)
    check(digest(text.replace(NEW, OLD).encode())==BASE[rel], 'unrelated metadata modification: '+rel)
for rel in NOTES:
    data=(ROOT/rel).read_bytes()
    historical_length=REF['historical_document_lengths'][rel]
    check(digest(data[-historical_length:])==BASE[rel], 'historical release record rewritten: '+rel)
    check(digest(data[:-historical_length])==REF['history_prefix_sha256'][rel], 'unexpected new release note: '+rel)
architecture=(ROOT/ARCH).read_bytes()
position=REF['architecture_prefix_length']
check(digest(architecture[:position])==BASE[ARCH],'historical architecture rewritten')
check(digest(architecture[position:])==REF['architecture_added_suffix_sha256'],'unapproved architecture addition')
window=(ROOT/MAIN).read_text()
module=(ROOT/MIX).read_text()
marker='class LayoutControlsMixin:\n'
check(module.count(marker)==1,'layout mixin missing/duplicated')
if module.count(marker)==1:
    body=module.split(marker,1)[1]
    check(digest(body.encode())==REF['relocated_method_block_sha256'], 'layout method bodies differ from predecessor')
    recovered=window.replace('from riqatony_desk.widgets.window_parts.layout_controls import LayoutControlsMixin\n','')
    recovered=recovered.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, QMainWindow):',
        'class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, QMainWindow):')
    recovered=recovered.replace('from riqatony_desk.widgets.workspace.navigation import NavigationWidget\n',
        'from riqatony_desk.widgets.workspace.navigation import NavigationWidget, SIDEBAR_MINIMUM_WIDTH\n')
    anchor='    def _sync_view_actions(self, mode: str) -> None:\n'
    check(recovered.count(anchor)==1,'layout insertion anchor missing')
    recovered=recovered.replace(anchor,body+anchor,1)
    check(digest(recovered.encode())==BASE[MAIN], 'exact original x13.1 MainWindow cannot be reconstructed')
    tree=ast.parse(module)
    win_tree=ast.parse(window)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LayoutControlsMixin'),None)
    main_cls=next((n for n in win_tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow'),None)
    if cls and main_cls:
        methods=[n.name for n in cls.body if isinstance(n,ast.FunctionDef)]
        own=[n.name for n in main_cls.body if isinstance(n,ast.FunctionDef)]
        check(methods==REF['extracted_method_names'] and len(methods)==13,'wrong number or sequence of extracted methods')
        check(not(set(methods)&set(own)),'layout methods duplicated in MainWindow')
        check([getattr(b,'id',None) for b in main_cls.bases]==['DocumentTabsMixin','NavigationHistoryMixin','LayoutControlsMixin','QMainWindow'], 'MainWindow MRO changed unexpectedly')
        check('def eventFilter(' in window and 'def closeEvent(' in window, 'MainWindow Qt event ownership moved')
        check('def _show_quick_tour(' in window, 'Help/Quick Tour extracted before approved x13.3')
        check('self._collapsed_mode_restore: dict[str, object] | None = None' in window, 'Focused Mode state no longer owned by MainWindow')
        check('self.sidebar_position_actions' in window, 'Sidebar actions moved from MainWindow')
        check('self.shell_ribbon' in window,'Ribbon ownership changed')
    else: check(False,'MainWindow or LayoutControlsMixin missing')
for existing in ('document_tabs.py','navigation_history.py'):
    check((PKG/'widgets/window_parts'/existing).is_file(), 'earlier extracted component missing: '+existing)
checker=(ROOT/RELEASE).read_text()
for required in ('x132-layout-controls-convergence-qa.py','x132-layout-controls-headless-qa.py'):
    check(required in checker,'current gate does not run '+required)
check(NEW in checker,'release gate identity unchanged')
stream=(ROOT/STREAM).read_text()
check(stream.count('<release version="'+NEW+'"')==1,'AppStream current edition missing')
check('<release version="'+OLD+'"' not in stream,'AppStream older current release retained')
check('thirteen unchanged MainWindow methods' in stream,'AppStream x13.2 description inaccurate')
if errors:
    print('FAIL RiqatonyDesk x13.2 preservation')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('PASS x13.2: 13 byte-exact layout methods, full x13.1 predecessor reconstruction, historical records preserved')
