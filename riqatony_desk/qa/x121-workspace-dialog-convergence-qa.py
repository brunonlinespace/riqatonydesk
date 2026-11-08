#!/usr/bin/env python3
"""Stage 2: compare every x12.1 source file to the frozen issued x12.0 archive.

No historical checks, source fingerprint records, or release text are rewritten.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P.parent
SNAP = json.loads((P/'qa/x121-preservation-reference.json').read_text())
OLD='1.0.0-x12.0'; NEW='1.0.0-x12.1'
assert SNAP['baseline']==OLD
SOURCE=SNAP['baseline_sha256_by_path']
WS=('navigation','dashboard','dashboard_card','folder_dashboard')
DI=('about_dialog','closing_dialog','first_run_dialog','projects_dialog','resolve_open_documents_dialog','shortcuts_dialog')
MOVED={f'riqatony_desk/widgets/{n}.py':f'riqatony_desk/widgets/workspace/{n}.py' for n in WS}
MOVED.update({f'riqatony_desk/widgets/{n}.py':f'riqatony_desk/widgets/dialogs/{n}.py' for n in DI})
VERSION_META={
 'README.md', 'suite-pythoine-component.json', 'riqatony_desk/__init__.py',
 'riqatony_desk/app_constants.py', 'riqatony_desk/riqatonydesk.json',
 'riqatony_desk/widgets/rtf_editor.py',
 'riqatony_desk/packaging/appimage/riqatonydesk.desktop',
 'riqatony_desk/packaging/fedora/build-appimage.sh',
 'riqatony_desk/packaging/fedora/test-appimage.sh',
 'riqatony_desk/packaging/README.md',
}
STREAM='riqatony_desk/packaging/appimage/io.github.brunonlinespace.riqatonydesk.metainfo.xml'
HISTORY=('riqatony_desk/docs/CHANGELOG.md','riqatony_desk/docs/RELEASE_NOTES.md')
ARCH='riqatony_desk/docs/ARCHITECTURE.md'
CURRENT_GATE='riqatony_desk/tools/release_check.py'
MANIFEST='riqatony_desk/SOURCE_MANIFEST.sha256'
NEW_FILES={
 'riqatony_desk/widgets/workspace/__init__.py',
 'riqatony_desk/widgets/dialogs/__init__.py',
 'riqatony_desk/qa/x121-preservation-reference.json',
 'riqatony_desk/qa/x121-current-path-contracts-qa.py',
 'riqatony_desk/qa/x121-workspace-dialog-convergence-qa.py',
 'riqatony_desk/qa/riqatonydesk-x12.1-identity-qa.py',
}
problems=[]
def check(x,desc):
 if not x: problems.append(desc)
def h(blob): return hashlib.sha256(blob).hexdigest()
def restored(txt,rel):
 for n in WS: txt=txt.replace('riqatony_desk.widgets.workspace.'+n,'riqatony_desk.widgets.'+n)
 for n in DI: txt=txt.replace('riqatony_desk.widgets.dialogs.'+n,'riqatony_desk.widgets.'+n)
 if rel=='riqatony_desk/widgets/__init__.py':
  txt=txt.replace('from .workspace.navigation import NavigationWidget','from .navigation import NavigationWidget')
 if rel in {f'riqatony_desk/widgets/{n}.py' for n in ('dashboard','dashboard_card','folder_dashboard')}:
  txt=txt.replace('Path(__file__).resolve().parents[2] / "assets"', 'Path(__file__).resolve().parent.parent / "assets"')
 return txt

# Full byte-level preexisting source preservation, including old QA/fingerprints.
for old,expected in SOURCE.items():
 new=MOVED.get(old,old);p=R/new
 check(p.is_file(),'missing preexisting file '+new)
 if not p.is_file():continue
 if old in (VERSION_META|{STREAM,ARCH,CURRENT_GATE,MANIFEST,*HISTORY}):continue
 raw=p.read_bytes()
 if old.endswith('.py') and old.startswith('riqatony_desk/') and '/qa/' not in old and '/tools/' not in old:
  raw=restored(raw.decode('utf-8'),old).encode('utf-8')
 check(h(raw)==expected,'original source/history changed beyond approved import/icon anchor edits: '+old)
for rel in VERSION_META:
 p=R/rel;txt=p.read_text()
 check(NEW in txt,'stale current identity: '+rel)
 check(h(txt.replace(NEW,OLD).encode())==SOURCE[rel], 'unexpected change in current metadata: '+rel)
# Check AppStream structurally by reversing the two intentional substitutions.
s=(R/STREAM).read_text();check(f'<release version="{NEW}"' in s,'wrong current AppStream release')
old_note='Editor helper modules reorganised into a dedicated rwpyn folder with preserved document safety and workspace functionality.'
new_note='Four workspace UI modules and six dialogs relocated into matching packages; import routes, icon roots, and release validation updated without changing behaviour.'
check(h(s.replace(f'<release version="{NEW}"',f'<release version="{OLD}"').replace(new_note,old_note).encode())==SOURCE[STREAM], 'other AppStream content changed')
for rel in HISTORY:
 raw=(R/rel).read_bytes();orig_len=SNAP['historical_doc_lengths'][rel]
 check(raw.startswith((f'# RiqatonyDesk {NEW}').encode()) and raw.endswith(b''), 'current release note not prepended: '+rel)
 check(h(raw[-orig_len:])==SOURCE[rel], 'historical release text was modified: '+rel)
arch=(R/ARCH).read_bytes()
check(h(arch[:SNAP['arch_prefix_length']])==SOURCE[ARCH], 'historical architecture document rewritten')
for old,new in MOVED.items():check(not (R/old).exists() and (R/new).is_file(),'not an exclusive relocation: '+old)
for name,text in [('workspace','"""RiqatonyDesk workspace navigation and dashboard widgets."""\n'),('dialogs','"""RiqatonyDesk application dialogs."""\n')]:
 check((P/'widgets'/name/'__init__.py').read_text()==text,'unexpected package __init__: '+name)
actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
expected=(set(SOURCE)-set(MOVED))|set(MOVED.values())|NEW_FILES
check(actual==expected, 'file inventory drift: added='+str(sorted(actual-expected)[:9])+', missing='+str(sorted(expected-actual)[:9]))
for f in P.rglob('*.py'):
 if any(seg in f.relative_to(P).parts for seg in ('qa','tools')):continue
 t=f.read_text()
 for n in WS+DI:check('riqatony_desk.widgets.'+n not in t,'stale flat import: '+str(f.relative_to(P))+' / '+n)
 try:ast.parse(t,filename=str(f))
 except SyntaxError as e:problems.append('syntax error: '+str(e))
# Every absolute internal import target must resolve in the relocated package.
resolved=0
for f in P.rglob('*.py'):
 if any(part in ('qa','tools') for part in f.relative_to(P).parts):continue
 tree=ast.parse(f.read_text(), filename=str(f))
 for node in ast.walk(tree):
  targets=[]
  if isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
   targets=[node.module]
  elif isinstance(node,ast.Import):
   targets=[alias.name for alias in node.names]
  for name in targets:
   if name=='riqatony_desk':continue
   if not name.startswith('riqatony_desk.'):continue
   relative=name.split('.')[1:]
   candidate=P.joinpath(*relative)
   check(candidate.with_suffix('.py').is_file() or (candidate/'__init__.py').is_file(),
         'unresolved internal import '+name+' from '+str(f.relative_to(P)))
   resolved+=1
check(resolved>=50, 'unexpected reduction in source import coverage: '+str(resolved))

for n in ('dashboard','dashboard_card','folder_dashboard'):
 t=(P/'widgets/workspace'/f'{n}.py').read_text()
 check(t.count('Path(__file__).resolve().parents[2] / "assets"')==1,'asset root changed: '+n)
 check((P/'assets').is_dir(),'assets root missing')
# Historical x12.0 tests are preserved, not retargeted or falsified.
for rel in ('qa/x12-folder-convergence-qa.py','qa/riqatonydesk-x12.0-identity-qa.py','qa/x12-preservation-reference.json'):
 path='riqatony_desk/'+rel
 check(h((R/path).read_bytes())==SOURCE[path], 'original x12 record modified '+path)
if problems:
 print('FAIL x12.1 exact baseline preservation:')
 for msg in problems:print(' -',msg)
 raise SystemExit(1)
print('PASS: x12.1, 10 exclusive moves; 1510-file frozen predecessor baseline; full source/history preservation, assets and imports')
