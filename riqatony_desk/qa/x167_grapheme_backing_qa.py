#!/usr/bin/env python3
"""x16.7 current gate: actual predecessor integrity and scoped Unicode/warning tests.

Qt is unavailable in the build environment, so interactive behavior is not certified.
Unicode protocol double uses regex \\X as the independent UAX-29 oracle.
"""
from __future__ import annotations
import ast,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF=json.loads((ROOT/'qa/x167-predecessor-integrity.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def methods(path):
 tree=ast.parse(path.read_text());d={}
 def walk(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
   elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    d[prefix+n.name]=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()
 walk(tree.body)
 return d
for rel,h in PROOF['preserved_runtime_file_sha256'].items():
 assert sha(ROOT/rel)==h,('modified protected runtime',rel)
for rel,expected in PROOF['modified_runtime_unchanged_method_sha256'].items():
 actual=methods(ROOT/rel)
 assert set(actual)==set(expected)|set(PROOF['allowed_method_changes'][rel]),('method inventory',rel)
 for method,h in expected.items():assert actual[method]==h,('modified protected method',rel,method)
for rel,h in PROOF['png_sha256'].items():
 assert sha(ROOT/rel)==h,('PNG changed',rel)
assert len(list(ROOT.rglob('*.png')))==652
assert not list(ROOT.rglob('*.svg'))
print('PASS: all 652 PNGs, zero SVGs, unrelated runtime files/methods unchanged')

from pathlib import Path as _Path
# Dynamic extraction of only the real methods under test: no reimplementation of their logic.
def method(rel,cls,name,env=None):
 tree=ast.parse((ROOT/rel).read_text())
 node=next(n for n in next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==cls).body if isinstance(n,ast.FunctionDef) and n.name==name)
 class RemoveImports(ast.NodeTransformer):
  def visit_ImportFrom(self,n):return ast.copy_location(ast.Pass(),n)
 body=RemoveImports().visit(node)
 namespace={'Path':_Path,'DocumentEntry':object,'is_critical_status':lambda s:s.startswith(('Backing file missing;', 'File changed outside ', 'RTF opened with compatibility warnings.', 'Could not save ', 'Could not load ')),'status_sentence':lambda s:s if s.endswith('.') else s+'.'}
 namespace.update(env or {})
 exec(compile(ast.fix_missing_locations(ast.Module(body=[body],type_ignores=[])),'<extracted>','exec'),namespace)
 return namespace[name]

show=method('widgets/rtf_editor.py','RicopadEditorWidget','_show_status_message')
clear=method('widgets/rtf_editor.py','RicopadEditorWidget','_clear_status_message')
state=method('widgets/editor_page.py','EditorPage','_set_backing_state')
backing=method('widgets/editor_page.py','EditorPage','handle_backing_path_event')
repo=method('widgets/editor_page.py','EditorPage','_on_repository_document_changed')
manager=method('controllers/editor_manager.py','EditorManager','_on_open_backing_path_changed',{'EditorPage':object})
class Label:
 def __init__(self):self.value=''
 def setText(self,v):self.value=v
 def setToolTip(self,v):pass
 def clear(self):self.value=''
 def text(self):return self.value
class Timer:
 def __init__(self):self.active=False
 def stop(self):self.active=False
 def start(self,millis):self.active=True
class Signal:
 def __init__(self):self.emitted=[]
 def emit(self,*args):self.emitted.append(args)
class Widget:
 def __init__(self):self.visible=False
 def setEnabled(self,v):pass
 def setText(self,v):pass
 def hide(self):self.visible=False
 def show(self):self.visible=True
class Surface:
 def __init__(self):
  self.status_message_label=Label();self._status_message_timer=Timer();self.status_message=Signal();self.file_disk_signature='original';self.file_path='/tmp/test.rtf'
 _show_status_message=show
 _clear_status_message=clear
class Page:
 def __init__(self):
  self._surface=Surface();self._backing_state='normal';self._external_change_pending=False
  self.external_banner=Widget();self.external_label=Widget();self.reload_external_button=Widget()
  self.document=type('Entry',(),{'path':_Path('/tmp/test.rtf')})()
  self.disk_signature='original';self.transition_calls=0
 def _current_disk_signature(self):return self.disk_signature
 def _refresh_header(self):pass
 def show_editor_status(self,text,timeout=4000,*,warning_kind=None):
  self._surface._show_status_message(text,timeout,warning_kind=warning_kind)
 def on_change(self,*a,**kw):
  self.transition_calls+=1
  return backing(self,*a,**kw)
 _set_backing_state=state
 handle_backing_path_event=on_change
 _on_repository_document_changed=repo
page=Page();surface=page._surface
# Repository event uses same notifying pathway as direct-monitor event.
page.disk_signature=None
page._on_repository_document_changed(page.document)
assert page._backing_state=='missing' and page.external_banner.visible
assert surface._critical_editor_message_kind=='backing_file'
assert len(surface.status_message.emitted)==1
page._on_repository_document_changed(page.document)
assert len(surface.status_message.emitted)==1, 'duplicate repository event'
page.handle_backing_path_event(notify=True)
assert len(surface.status_message.emitted)==1, 'duplicate monitor event'
page.disk_signature='other'
page.handle_backing_path_event(notify=True)
assert page._backing_state=='changed' and len(surface.status_message.emitted)==2
assert surface._critical_editor_message_kind=='backing_file'
page.disk_signature='original'
page._on_repository_document_changed(page.document)
assert page._backing_state=='normal' and not surface.status_message_label.text()
# Unrelated critical messages survive backing recovery; no text-prefix dependency.
surface._show_status_message('RTF opened with compatibility warnings. Review File → Properties before saving.')
page.disk_signature=None;page.handle_backing_path_event(notify=False)
page.disk_signature='original';page.handle_backing_path_event(notify=True)
assert surface._critical_editor_message and surface._critical_editor_message_kind is None
assert surface.status_message_label.text().startswith('RTF opened')
# Routine messages cannot displace unrelated critical warnings.
surface._show_status_message('Replaced 4 occurrences.')
assert surface.status_message_label.text().startswith('RTF opened')
# Current routing change is only delegation to page; both triggers notify.
manager_source=ast.get_source_segment((ROOT/'controllers/editor_manager.py').read_text(),next(
 n for c in ast.parse((ROOT/'controllers/editor_manager.py').read_text()).body if isinstance(c,ast.ClassDef) and c.name=='EditorManager'
 for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_on_open_backing_path_changed'))
assert 'page.handle_backing_path_event(notify=True)' in manager_source
print('PASS: backing state transitions, suppression of duplicates, selective critical warning clearing')

# Protocol-double QtBoundaryFinder runs the actual RiqatonyPad-derived counter.
try:
 import regex
except ImportError:
 print('SKIP: independent regex Unicode oracle unavailable; Qt runtime remains untested')
else:
 class BoundaryType:Grapheme=1
 class QTextBoundaryFinder:
  BoundaryType=BoundaryType
  def __init__(self,mode,text):
   self.stops=[];pos=0
   for x in regex.findall(r'\X',text):pos+=len(x);self.stops.append(pos)
   self.index=0
  def toNextBoundary(self):
   if self.index==len(self.stops):return -1
   at=self.stops[self.index];self.index+=1;return at
 class QTextBlockUserData:pass
 src=(ROOT/'widgets/rwpyn/character_count.py').read_text()
 ns={'QTextBoundaryFinder':QTextBoundaryFinder,'QTextBlockUserData':QTextBlockUserData}
 tree=ast.parse(src)
 code=ast.fix_missing_locations(ast.Module(body=[x for x in tree.body if not isinstance(x,ast.ImportFrom) and not isinstance(x,ast.Expr)],type_ignores=[]))
 exec(compile(code,'<character_count.py>','exec'),ns)
 class Block:
  def __init__(self,text):self.value=text;self.rev=0;self.ud=None;self.follow=None;self.text_reads=0
  def isValid(self):return True
  def text(self):self.text_reads+=1;return self.value
  def revision(self):return self.rev
  def userData(self):return self.ud
  def setUserData(self,data):self.ud=data
  def next(self):return self.follow if self.follow is not None else Invalid()
 class Invalid:
  def isValid(self):return False
 class Doc:
  def __init__(self,lines):
   self.blocks=[Block(t) for t in lines]
   for a,b in zip(self.blocks,self.blocks[1:]):a.follow=b
  def begin(self):return self.blocks[0]
 count=ns['count_visible_characters']
 for lines,n in [([''],0),(['abc'],3),(['e\u0301'],1),(['😀'],1),(['👩‍👩‍👧‍👦'],1),(['first','','😀'],8),(['\ufffc'],1),(['a','b'],3)]:
  d=Doc(lines);assert count(d)==n,(lines,count(d),n)
  reads=sum(x.text_reads for x in d.blocks);assert count(d)==n
  assert sum(x.text_reads for x in d.blocks)==reads,'unchanged block was rescanned'
 d=Doc(['ab','cd']);assert count(d)==5
 d.blocks[0].value='e\u0301';d.blocks[0].rev+=1
 assert count(d)==4
 assert d.blocks[0].text_reads==2 and d.blocks[1].text_reads==1
 print('PASS: grapheme Unicode cases, logical separators, edit invalidation, per-block cache (Qt protocol double)')
