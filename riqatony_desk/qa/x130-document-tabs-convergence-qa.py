#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.0 exact x12.1 preservation and 25-method Document Tabs extraction.

Historical source fingerprints are retained as immutable evidence; this active
check validates the current structure without rewriting any earlier QA scripts.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parent
REF=json.loads((PKG/'qa/x130-preservation-reference.json').read_text())
BASE=REF['baseline_sha256_by_path']
OLD='1.0.0-x12.1'
NEW='1.0.0-x13.0'
errors=[]

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def check(ok,why):
    if not ok: errors.append(why)

main='riqatony_desk/widgets/main_window.py'
mixin='riqatony_desk/widgets/window_parts/document_tabs.py'
initializer='riqatony_desk/widgets/window_parts/__init__.py'
gate='riqatony_desk/tools/release_check.py'
manifest='riqatony_desk/SOURCE_MANIFEST.sha256'
stream='riqatony_desk/packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml'
current_identity={
    'README.md', 'suite-pythoine-component.json',
    'riqatony_desk/__init__.py','riqatony_desk/app_constants.py',
    'riqatony_desk/riqatonydesk.json',
    'riqatony_desk/packaging/README.md',
    'riqatony_desk/packaging/fedora/build-appimage.sh',
    'riqatony_desk/packaging/fedora/test-appimage.sh',
    'riqatony_desk/packaging/appimage/riqatonydesk.desktop',
}
history={'riqatony_desk/docs/RELEASE_NOTES.md', 'riqatony_desk/docs/CHANGELOG.md'}
arch='riqatony_desk/docs/ARCHITECTURE.md'
new={initializer,mixin,'riqatony_desk/qa/x130-preservation-reference.json',
     'riqatony_desk/qa/x130-document-tabs-convergence-qa.py',
     'riqatony_desk/docs/RELEASE_CHECKLIST-x13.0.md',
     'riqatony_desk/qa/x130-historical-tab-contracts-qa.py',
     'riqatony_desk/qa/x130-document-tabs-headless-qa.py'}
allowed={main,gate,manifest,stream,arch}|history|current_identity
check(REF['baseline_version']==OLD,'wrong x12.1 predecessor identity')
check(REF['baseline_main_window_sha256']==BASE[main],'frozen original MainWindow fingerprint mismatch')
source_files={f.relative_to(ROOT).as_posix() for f in ROOT.rglob('*') if f.is_file() and
  '__pycache__' not in f.parts and 'build' not in f.relative_to(ROOT).parts[:2] and
  f.suffix not in {'.pyc','.pyo'}}
check(source_files == set(BASE)|new,
      'source inventory drift: added='+str(sorted(source_files-(set(BASE)|new))[:5])+
      '; missing='+str(sorted((set(BASE)|new)-source_files)[:5]))
for rel,h in BASE.items():
    f=ROOT/rel
    check(f.is_file(),'missing baseline source file: '+rel)
    if f.is_file() and rel not in allowed:
        check(sha(f.read_bytes())==h,'protected source or historical QA rewritten: '+rel)
for rel in current_identity:
    content=(ROOT/rel).read_text()
    check(NEW in content, 'current version not found in '+rel)
    check(sha(content.replace(NEW,OLD).encode())==BASE[rel],
          'non-version identity or packaging content changed: '+rel)
for rel in history:
    content=(ROOT/rel).read_bytes()
    size=REF['historical_document_lengths'][rel]
    check(size>0 and sha(content[-size:])==BASE[rel],
          'historical release text rewritten: '+rel)
    check(sha(content[:-size])==REF['added_historical_note_prefix_sha256'][rel],
          'x13.0 historical preface drift: '+rel)
arch_bytes=(ROOT/arch).read_bytes()
old_len=REF['historical_document_lengths'][arch]
check(sha(arch_bytes[:old_len])==BASE[arch], 'earlier architecture text rewritten')
check(sha(arch_bytes[old_len:])==REF['added_architecture_suffix_sha256'],
      'x13.0 architecture supplement drift')
check((ROOT/initializer).read_text()=='"""RiqatonyDesk MainWindow responsibility mixins."""\n',
      'unexpected window_parts initialiser')

mw=(ROOT/main).read_text()
mx=(ROOT/mixin).read_text()
marker='class DocumentTabsMixin:\n'
check(mx.count(marker)==1,'missing or duplicate document tabs mixin')
if mx.count(marker)==1:
    methods=mx.split(marker,1)[1]
    toggle_at=methods.index('    def _toggle_tabs_mode(')
    block=methods[:toggle_at]
    toggle=methods[toggle_at:]
    check(sha(block.encode())==REF['block_sha256'], '24-method tab block was altered')
    check(sha(toggle.encode())==REF['toggle_sha256'], 'toggle-tabs method was altered')
    restore=mw.replace('from riqatony_desk.widgets.window_parts.document_tabs import DocumentTabsMixin\n','')
    restore=restore.replace('class MainWindow(DocumentTabsMixin, QMainWindow):','class MainWindow(QMainWindow):')
    check(restore.count('    def _queue_navigation_record(')==1,'navigation history anchor absent')
    check(restore.count('    def _sync_app_settings_toggle_actions(')==1,'settings anchor absent')
    restore=restore.replace('    def _queue_navigation_record(',block+'    def _queue_navigation_record(',1)
    restore=restore.replace('    def _sync_app_settings_toggle_actions(',toggle+'    def _sync_app_settings_toggle_actions(',1)
    check(sha(restore.encode())==BASE[main], 'could not reconstruct byte-exact x12.1 MainWindow')

    cls_mix=next((n for n in ast.parse(mx).body if isinstance(n,ast.ClassDef) and n.name=='DocumentTabsMixin'),None)
    cls_main=next((n for n in ast.parse(mw).body if isinstance(n,ast.ClassDef) and n.name=='MainWindow'),None)
    if cls_mix is not None and cls_main is not None:
        extracted=[n.name for n in cls_mix.body if isinstance(n,ast.FunctionDef)]
        retained={n.name for n in cls_main.body if isinstance(n,ast.FunctionDef)}
        check(extracted==REF['extracted_method_names'] and len(extracted)==25,
              'extracted method names/order/count changed')
        check(not (set(extracted)&retained),'duplicate tab methods remain in MainWindow')
        check([getattr(x,'id',None) for x in cls_main.bases]==['DocumentTabsMixin','QMainWindow'],
              'MainWindow inheritance order changed')
        check('self.document_tabs = QTabBar(self.content_host)' in mw and
              'self.document_tabs.currentChanged.connect(self._activate_document_tab)' in mw and
              'self.document_tabs.tabCloseRequested.connect(self._close_document_tab)' in mw,
              'Qt tab construction/connections moved out of MainWindow')
        check('def _queue_navigation_record(' in mw and 'def _toggle_collapsed_mode(' in mw and
              'def _show_quick_tour(' in mw,'later Stage 3 scope changed')
        check('riqatonydesk://navigation/' in mx and '_NAV_DASHBOARD_TOKEN' in mx,
              'navigation tab identities changed')
    else: errors.append('MainWindow or tab mixin class missing')
check('x130-document-tabs-convergence-qa.py' in (ROOT/gate).read_text(),
      'new release gate does not execute x13.0 source-preservation test')
check('<release version="'+NEW+'"' in (ROOT/stream).read_text(),
      'current AppStream version missing')
check('Stage 3 document-tabs extraction:' in (ROOT/stream).read_text(),
      'current AppStream release description missing')
if errors:
    print('FAIL x13.0 RiqatonyDesk preservation:')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('PASS: RiqatonyDesk x13.0 25-method exact Document Tabs extraction, unchanged x12.1 history/production, current identity')
