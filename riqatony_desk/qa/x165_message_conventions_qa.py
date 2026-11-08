#!/usr/bin/env python3
"""Edition-specific status-conventions + predecessor production preservation QA."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
ROOT=PKG.parent
sys.path.insert(0, str(ROOT))
TAG='x165'
PREFIX='R'
REF=json.loads((PKG / 'qa' / (TAG+'-preservation.json')).read_text())

def sha(raw):return hashlib.sha256(raw).hexdigest()

def functions(tree):
    found={}
    def walk(nodes,parent=''):
        for node in nodes:
            if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                key=(parent+'.' if parent else '')+node.name
                if isinstance(node,ast.ClassDef):walk(node.body,key)
                else:found[key]=sha(ast.dump(node,include_attributes=False).encode())
    walk(tree.body)
    return found

for rel,expected in REF['source_production_sha256_frozen'].items():
    assert sha((ROOT/rel).read_bytes())==expected, rel
for rel,rules in REF['changed_production_methods'].items():
    found=functions(ast.parse((ROOT/rel).read_text()))
    for method,expected in rules['unchanged_functions'].items():
        assert found.get(method)==expected, (rel,method)
for rel,expected in REF['drag_highlight_frozen'].items():
    assert sha((ROOT/rel).read_bytes()) == expected, rel

spec=importlib.util.spec_from_file_location('conventions',PKG/'widgets/message_conventions.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.DEFAULT_MESSAGE_DURATION_MS == 4000
assert module.status_sentence('Saved example.md')=='Saved example.md.'
assert module.status_sentence('Refresh underway…')=='Refresh underway.'
assert module.status_sentence('Exported PDF to /tmp/report.pdf')=='Exported PDF to /tmp/report.pdf.'
assert module.is_critical_status('Workspace scan failed: error')
assert module.is_critical_status('Backing file missing; the live document remains protected.')
assert not module.is_critical_status('Renamed old.md to new.md.')

# Invoke real source method bodies using Qt-free spies and the real formatter.
class Signal:
    def __init__(self):self.fn=None;self.received=[]
    def connect(self,fn):self.fn=fn
    def emit(self,text):self.received.append(text)
class Timer:
    def __init__(self,*args):self.timeout=Signal();self.duration=None;self.active=False
    def setSingleShot(self,value):pass
    def start(self,duration):self.duration=duration;self.active=True
    def stop(self):self.active=False
class Label:
    def __init__(self):self.text='';self.tooltip=''
    def setText(self,text):self.text=text
    def setToolTip(self,text):self.tooltip=text
    def clear(self):self.text=''

def method_from_file(rel,clazz,method):
    tree=ast.parse((PKG/rel).read_text())
    parent=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==clazz)
    func=next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name==method)
    class StripQtPackageImport(ast.NodeTransformer):
        def visit_ImportFrom(self,node):
            if node.module and node.module.endswith('.widgets.message_conventions'):
                return ast.copy_location(ast.Pass(),node)
            return node
    func=StripQtPackageImport().visit(func)
    code=compile(ast.fix_missing_locations(ast.Module(body=[func],type_ignores=[])),'<method>','exec')
    ns={'QTimer':Timer,'DEFAULT_MESSAGE_DURATION_MS':4000,'is_critical_status':module.is_critical_status,'status_sentence':module.status_sentence}
    exec(code,ns)
    return ns[method]

prefix='maqarony_desk' if PREFIX=='M' else 'riqatony_desk'
main=method_from_file('widgets/main_window.py','MainWindow','show_status')
class MainSpy:
    def __init__(self):self._status_label=Label()
win=MainSpy()
main(win,'Renamed old.md to new.md')
assert win._status_label.text=='Renamed old.md to new.md.'
assert win._workspace_message_timer.duration==4000
main(win,'Workspace scan failed: disk error')
assert win._status_label.text=='Workspace scan failed: disk error.'
assert not win._workspace_message_timer.active
main(win,'Theme: Dark.')
assert win._status_label.text=='Workspace scan failed: disk error.'
main(win,'Refreshing workspace in background…')
assert win._status_label.text=='Refreshing workspace in background.'
assert win._workspace_message_timer.duration==4000

if PREFIX=='M':
    local=method_from_file('widgets/editor_page.py','EditorMessageStatusBar','showMessage')
    class PageSpy:
        def __init__(self):self.message_label=Label();self._message_timer=Timer()
    page=PageSpy()
    local(page,'Saved as hello.md')
    assert page.message_label.text=='Saved as hello.md.' and page._message_timer.duration==4000
    local(page,'Could not save hello.md: permission denied')
    assert page.message_label.text.endswith('.') and not page._message_timer.active
    local(page,'Replace All finished')
    assert page.message_label.text.startswith('Could not save')
    local(page,'Saved hello.md')
    assert page.message_label.text=='Saved hello.md.' and page._message_timer.active
    f=(PKG/'widgets/mwpyn/editor_source.py').read_text()+(PKG/'widgets/mwpyn/editor_insertion.py').read_text()
    assert "MaqaronyPad's source document safety limit" not in f
    assert "MaqaronyDesk's source document safety limit" in f
    assert 'self.show_status(f"Folder renamed to' not in (PKG/'widgets/main_window.py').read_text()
else:
    local=method_from_file('widgets/rtf_editor.py','RicopadEditorWidget','_show_status_message')
    class PageSpy:
        def __init__(self):self.status_message_label=Label();self._status_message_timer=Timer();self.status_message=Signal()
    page=PageSpy()
    local(page,'Saved as hello.rtf')
    assert page.status_message_label.text=='Saved as hello.rtf.' and page._status_message_timer.duration==4000
    local(page,'RTF opened with compatibility warnings. Review File → Properties before saving.')
    assert page.status_message_label.text.endswith('.') and not page._status_message_timer.active
    local(page,'Replace All finished')
    assert page.status_message_label.text.startswith('RTF opened with compatibility warnings.')
    local(page,'Loaded another.rtf')
    assert page.status_message_label.text=='Loaded another.rtf.' and page._status_message_timer.active
    assert "The current Rico document" not in (PKG/'widgets/editor_page.py').read_text()
    codec=(PKG/'rtf_codec.py').read_text()
    assert 'exceeds Ricopad\'s' not in codec
    assert "RiqatonyDesk's RTF safety limits" in codec

file_actions=(PKG/'controllers/file_actions.py').read_text()
assert 'f"Duplicated as {destination.name}."' in file_actions
assert 'f"Deleted {stored.filename}"' in file_actions
assert 'f"Renamed {old_path.name} to {new_name}"' in file_actions
assert 'f"Deleted folder {folder.name}"' in file_actions
# All explicitly timed editor-status calls must obey the common four-second rule.
for source in PKG.rglob('*.py'):
    if 'qa' in source.relative_to(PKG).parts or 'tools' in source.relative_to(PKG).parts:
        continue
    tree=ast.parse(source.read_text())
    for node in ast.walk(tree):
        if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)):
            continue
        if node.func.attr not in {'_show_status_message','show_editor_status','showMessage','show_current_editor_status'}:
            continue
        if len(node.args)>1 and isinstance(node.args[1],ast.Constant) and type(node.args[1].value) is int:
            assert node.args[1].value == 4000, (source,node.lineno,node.args[1].value)
assert REF['release'] in (PKG/'__init__.py').read_text()
print('PASS:',REF['release'],'message conventions, critical warning precedence and predecessor preservation')
