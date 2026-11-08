#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.1 exact x13.0 predecessor preservation and six-method history extraction.

No preceding release, historical QA or fingerprints are rewritten.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parent
REF=json.loads((PKG/'qa/x131-preservation-reference.json').read_text())
BASE=REF['baseline_sha256_by_path']
OLD='1.0.0-x13.0'
NEW='1.0.0-x13.1'
errors=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(x,message):
    if not x:errors.append(message)

main='riqatony_desk/widgets/main_window.py'
mixin='riqatony_desk/widgets/window_parts/navigation_history.py'
arch='riqatony_desk/docs/ARCHITECTURE.md'
manifest='riqatony_desk/SOURCE_MANIFEST.sha256'
release_gate='riqatony_desk/tools/release_check.py'
stream='riqatony_desk/packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml'
metadata={
    'README.md','suite-pythoine-component.json',
    'riqatony_desk/__init__.py', 'riqatony_desk/app_constants.py',
    'riqatony_desk/riqatonydesk.json', 'riqatony_desk/packaging/README.md',
    'riqatony_desk/packaging/fedora/build-appimage.sh',
    'riqatony_desk/packaging/fedora/test-appimage.sh',
    'riqatony_desk/packaging/appimage/riqatonydesk.desktop',
}
history={'riqatony_desk/docs/RELEASE_NOTES.md', 'riqatony_desk/docs/CHANGELOG.md'}
newfiles={mixin,'riqatony_desk/qa/x131-preservation-reference.json',
    'riqatony_desk/qa/x131-navigation-history-convergence-qa.py',
    'riqatony_desk/qa/x131-navigation-history-headless-qa.py',
    'riqatony_desk/qa/x131-historical-tab-contracts-qa.py',
    'riqatony_desk/docs/RELEASE_CHECKLIST-x13.1.md'}
allowed={main,arch,manifest,release_gate,stream}|metadata|history
check(REF['baseline_version']==OLD,'frozen predecessor identity differs')
check(REF['baseline_main_window_sha256']==BASE[main],'original MainWindow hash in reference differs')
current={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if
         p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'} and
         'build' not in p.relative_to(ROOT).parts[:2]}
check(current==set(BASE)|newfiles,'source inventory drift: additions='+str(sorted(current-(set(BASE)|newfiles))[:10])+
      '; missing='+str(sorted((set(BASE)|newfiles)-current)[:10]))
for rel,expected in BASE.items():
    p=ROOT/rel
    check(p.is_file(),'missing baseline file: '+rel)
    if p.is_file() and rel not in allowed:
        check(sha(p.read_bytes())==expected,'protected source/historical record rewritten: '+rel)
for rel in metadata:
    p=ROOT/rel
    if p.is_file():
        content=p.read_text()
        check(NEW in content,'version missing in current metadata: '+rel)
        check(sha(content.replace(NEW,OLD).encode())==BASE[rel],
              'unrelated metadata content changed: '+rel)
for rel in history:
    data=(ROOT/rel).read_bytes()
    size=REF['historical_document_lengths'][rel]
    check(sha(data[-size:])==BASE[rel],'historical release text rewritten: '+rel)
    check(sha(data[:-size])==REF['historical_document_added_prefix_sha256'][rel],
          'current release note has unexpected content: '+rel)
arch_data=(ROOT/arch).read_bytes()
n=REF['architecture_prefix_length']
check(sha(arch_data[:n])==BASE[arch], 'historical architecture content changed')
check(sha(arch_data[n:])==REF['architecture_added_suffix_sha256'],
      'new architecture supplement unexpected')
# Reassemble the exact predecessor bytes; no normalization or altered method allowed.
window=(ROOT/main).read_text()
mixin_text=(ROOT/mixin).read_text()
marker='class NavigationHistoryMixin:\n'
check(mixin_text.count(marker)==1, 'navigation mixin missing/duplicated')
if mixin_text.count(marker)==1:
    body=mixin_text.split(marker,1)[1]
    check(sha(body.encode())==REF['relocated_method_block_sha256'],
          'relocated history block differs byte-for-byte from x13.0')
    recovered=window.replace('from riqatony_desk.widgets.window_parts.navigation_history import NavigationHistoryMixin\n','')
    recovered=recovered.replace('class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, QMainWindow):',
                  'class MainWindow(DocumentTabsMixin, QMainWindow):')
    event_anchor='    def eventFilter(self, watched, event) -> bool:\n'
    check(recovered.count(event_anchor)==1,'eventFilter moved or renamed')
    recovered=recovered.replace(event_anchor,body+event_anchor,1)
    check(sha(recovered.encode())==BASE[main], 'MainWindow cannot reconstruct exact x13.0 source')
    m=ast.parse(mixin_text)
    w=ast.parse(window)
    cls=next((x for x in m.body if isinstance(x,ast.ClassDef) and x.name=='NavigationHistoryMixin'),None)
    maincls=next((x for x in w.body if isinstance(x,ast.ClassDef) and x.name=='MainWindow'),None)
    if cls is not None and maincls is not None:
        extracted=[x.name for x in cls.body if isinstance(x,ast.FunctionDef)]
        direct={x.name for x in maincls.body if isinstance(x,ast.FunctionDef)}
        check(extracted==REF['extracted_method_names'] and len(extracted)==6,
              'not exactly six original history methods')
        check(not (direct & set(extracted)),'history methods duplicated in MainWindow')
        check([getattr(x,'id',None) for x in maincls.bases]==
              ['DocumentTabsMixin','NavigationHistoryMixin','QMainWindow'],
              'MainWindow inheritance precedence changed')
        check('def eventFilter(' in window and 'self._navigate_back()' in window,
              'Back-button event handling changed')
        check('self._navigation_history: list[str] = []' in window and
              'self._navigation_back_in_progress = False' in window,
              'MainWindow history-state ownership changed')
        check('def _toggle_collapsed_mode(' in window and 'def _show_quick_tour(' in window,
              'future Stage 3 methods moved early')
        check('class DocumentTabsMixin' in (PKG/'widgets/window_parts/document_tabs.py').read_text(),
              'x13.0 tab implementation not retained')
    else:check(False,'MainWindow or NavigationHistoryMixin unavailable')
stream_text=(ROOT/stream).read_text()
check(stream_text.count('<release version="'+NEW+'"')==1, 'AppStream current edition missing')
check('<release version="'+OLD+'"' not in stream_text,'AppStream current-only list violated')
release_text=(ROOT/release_gate).read_text()
for s in ('x131-navigation-history-convergence-qa.py','x131-navigation-history-headless-qa.py',
          'x131-historical-tab-contracts-qa.py'):
    check(s in release_text,'release check omits '+s)
if errors:
    print('FAIL RiqatonyDesk x13.1 preservation:')
    for x in errors:print('-',x)
    raise SystemExit(1)
print('PASS x13.1: six byte-exact history methods, x13.0 source and all historical records preserved')
