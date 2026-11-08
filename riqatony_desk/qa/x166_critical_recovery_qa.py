#!/usr/bin/env python3
"""Desk critical-status recovery and Save Version As suggestion correction."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
REF = json.loads((PACKAGE / 'qa' / 'x166-preservation.json').read_text())

def digest(raw): return hashlib.sha256(raw).hexdigest()

def methods_in(text):
    found = {}
    tree = ast.parse(text)
    def walk(nodes, prefix=''):
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                key = (prefix+'.' if prefix else '')+node.name
                if isinstance(node,ast.ClassDef): walk(node.body,key)
                else: found[key] = digest(ast.dump(node, include_attributes=False).encode())
    walk(tree.body)
    return found

for rel, expected in REF['source_production_sha256_frozen'].items():
    assert digest((ROOT/rel).read_bytes())==expected, rel
for rel, rules in REF['changed_production_methods'].items():
    found = methods_in((ROOT/rel).read_text())
    assert set(found)==set(rules['unchanged_functions']) | set(rules['approved_functions']), rel
    for method, expected in {**rules['unchanged_functions'],**rules['approved_functions']}.items():
        assert found[method]==expected,(rel,method)

class Label:
    def __init__(self): self.content=''; self.tooltip=''
    def setText(self,value): self.content=value
    def setToolTip(self,value): self.tooltip=value
    def clear(self): self.content=''
    def text(self): return self.content
class Timer:
    def __init__(self): self.active=False;self.timeout=None
    def start(self,milliseconds): self.active=True; self.timeout=milliseconds
    def stop(self): self.active=False
class Widget:
    def __init__(self):self.visible=False;self.enabled=None;self.text_value=''
    def setEnabled(self,value):self.enabled=value
    def setText(self,value):self.text_value=value
    def show(self):self.visible=True
    def hide(self):self.visible=False
class Signal:
    def __init__(self):self.received=[]
    def emit(self,value):self.received.append(value)

def method(rel,clazz,name):
    tree=ast.parse((PACKAGE/rel).read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==clazz)
    node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    node=ast.fix_missing_locations(node)
    class NoImports(ast.NodeTransformer):
        def visit_ImportFrom(self,node):return ast.copy_location(ast.Pass(),node)
    node=NoImports().visit(node)
    ns={'DEFAULT_MESSAGE_DURATION_MS':4000, 'is_critical_status':lambda s:s.startswith(('Backing file missing;', 'File changed outside ', 'RTF opened with compatibility warnings.', 'Could not save ')),'status_sentence':lambda s:s if s.endswith('.') else s+'.'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<source>','exec'),ns)
    return ns[name]

show=method('widgets/rtf_editor.py','RicopadEditorWidget','_show_status_message')
clear=method('widgets/rtf_editor.py','RicopadEditorWidget','_clear_status_message')
state=method('widgets/editor_page.py','EditorPage','_set_backing_state')
class Status:
    def __init__(self):
        self.status_message_label=Label();self._status_message_timer=Timer();self.status_message=Signal()
    _show_status_message=show
    _clear_status_message=clear
class Page:
    def __init__(self):
        self._surface=Status();self.external_banner=Widget();self.external_label=Widget();self.reload_external_button=Widget();self.refreshed=0
    def _refresh_header(self):self.refreshed+=1
    _set_backing_state=state
page=Page();status=page._surface
page._set_backing_state('missing')
status._show_status_message('Backing file missing; the live RiqatonyDesk document remains protected.')
assert status._critical_editor_message and not status._status_message_timer.active and page.external_banner.visible
status._show_status_message('Replaced 2 occurrence(s).')
assert status.status_message_label.text().startswith('Backing file missing;')
page._set_backing_state('normal')
assert not status.status_message_label.text() and not status._critical_editor_message and not page.external_banner.visible
status._show_status_message('Replaced 2 occurrence(s).')
assert status.status_message_label.text()=='Replaced 2 occurrence(s).' and status._status_message_timer.timeout==4000
page._set_backing_state('changed')
status._show_status_message('File changed outside RiqatonyDesk.')
page._set_backing_state('normal')
assert not status._critical_editor_message and not status.status_message_label.text()
status._show_status_message('RTF opened with compatibility warnings. Review File → Properties before saving.')
page._set_backing_state('missing');page._set_backing_state('normal')
assert status._critical_editor_message and status.status_message_label.text().startswith('RTF opened')
status._clear_status_message()
assert not status._critical_editor_message and status.status_message_label.text()==''
status._show_status_message('Renamed old.rtf to new.rtf.')
assert status.status_message_label.text()=='Renamed old.rtf to new.rtf.'
try: page._set_backing_state('invalid')
except ValueError:pass
else:raise AssertionError('invalid backing state accepted')
for file,needle in [('widgets/editor_page.py',' - Rico Version'),('widgets/rwpyn/editor_lifecycle.py',' - Rico Version')]:
    text=(PACKAGE/file).read_text()
    assert needle not in text
    assert text.count(' - Desk Version')==2
    assert 'f"{source_path.stem} - Desk Version{suffix}"' in text
    assert 'f"{source_path.stem} - Desk Version {counter}{suffix}"' in text


assert REF['release'] in (PACKAGE / '__init__.py').read_text()
print('PASS:',REF['release'],'critical-status recovery, clearing, Desk Version filenames, and strict production scope')
