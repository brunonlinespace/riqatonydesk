#!/usr/bin/env python3
"""Current x16.2 targeted message-routing and production-preservation checks."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

PKG=Path(__file__).resolve().parents[1]
REF=json.loads((PKG/'qa/x162_message_source_fingerprints.json').read_text(encoding='utf-8'))
changed=['widgets/editor_page.py','widgets/rwpyn/editor_widgets.py','controllers/editor_manager.py']
assert sorted(k for k,v in REF['predecessor'].items() if REF['current'][k]!=v)==sorted(changed)
for rel,expected in REF['current'].items():
    assert hashlib.sha256((PKG/rel).read_bytes()).hexdigest()==expected, 'unapproved production modification '+rel


def method(rel,klass,name,ns):
    tree=ast.parse((PKG/rel).read_text(encoding='utf-8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass)
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),rel,'exec'),ns)
    return ns[name]

class Signal:
    def __init__(self):self.items=[]
    def emit(self,*args):self.items.append(args)

class Surface:
    def __init__(self,path='/tmp/current.rtf',result=True):self.file_path=path;self.result=result
    def save_file(self):return self.result

class Page:
    def __init__(self,path='/tmp/current.rtf',result=True):
        self._surface=Surface(path,result)
        self.document=SimpleNamespace(path=Path(path),filename=Path(path).name)
        self.repository=SimpleNamespace(set_dirty=lambda *args:None)
        self.messages=[];self.status_message=Signal();self.formatting_state_changed=Signal()
        self._backing_state='normal'
    def _set_backing_state(self,state):self._backing_state=state
    def _refresh_metadata(self):pass
    def show_editor_status(self,message,timeout=0):self.messages.append((message,timeout))
    def _has_external_change(self):return False
    def call_editor(self,name):return self._surface.save_as_file()

beeps=[]
class QApplication:
    @staticmethod
    def beep():beeps.append(True)

page=Page()
reject=method('widgets/rwpyn/editor_widgets.py','RichTextEdit','_reject_paste',{'QApplication':QApplication})
class TextArea:
    def parentWidget(self):return SimpleNamespace(_show_status_message=lambda message, timeout: page.show_editor_status(message, timeout))
    def window(self):raise AssertionError('central status must not be requested')
reject(TextArea(),'Clipboard content could not be inserted safely.')
assert page.messages==[('Clipboard content could not be inserted safely.',5000)]
assert len(beeps)==1 and not page.status_message.items

save=method('widgets/editor_page.py','EditorPage','save_to_disk',{})
page=Page()
assert save(page) is True and page.messages==[('Saved current.rtf',0)] and not page.status_message.items
page=Page(result=False)
assert save(page) is False and not page.messages

save_as=method('widgets/editor_page.py','EditorPage','save_as_file',{'Path':Path,'bool':bool})
class AsPage(Page):
    def call_editor(self,name):
        if self._surface.result:
            self._surface.file_path='/tmp/new.rtf'
        return self._surface.result
    def _save_editor_version_as(self):return False
page=AsPage()
assert save_as(page) and page.messages==[('Saved as new.rtf',0)] and not page.status_message.items
page=AsPage(result=False)
assert not save_as(page) and not page.messages
page=AsPage(path='/tmp/new.rtf')
assert save_as(page) and page.messages==[('Saved new.rtf',0)]
page=AsPage()
page._has_external_change=lambda:True
page.handle_backing_path_event=lambda:None
assert not save_as(page) and not page.messages

class QAction:pass
mode=method('widgets/editor_page.py','EditorPage','set_view_only',{'QAction':QAction,'bool':bool})
page=Page()
page._surface.view_only=False;page._surface.persist_view_only=False
page._surface._view_only_prompt_shown=False;page._surface.view_only_action=None
page._surface._update_mode_capabilities=lambda:None
page._surface.update_title=lambda:None
page._surface.update_status_counts=lambda:None
mode(page,True);mode(page,True)
assert page._surface.view_only and not page.messages and not page.status_message.items
assert len(page.formatting_state_changed.items)==2

manager=(PKG/'controllers/editor_manager.py').read_text(encoding='utf-8')
assert 'page.status_message.connect(self.status_message)' not in manager
assert 'page.set_view_only(bool(self.config.get("lock_editor", False)))' in manager
surface=(PKG/'widgets/rtf_editor.py').read_text(encoding='utf-8')
assert 'self._show_status_message("Locked Mode enabled." if checked else "Locked Mode disabled.",3000)' in surface
page_source=(PKG/'widgets/editor_page.py').read_text(encoding='utf-8')
assert 'self.show_editor_status(\n            f"Saved RiqatonyDesk version as' in page_source
assert 'self.status_message.emit(' not in page_source
print('PASS x16.2: local paste, Save/Save As, no false confirmations, no mode-sync duplication, production fingerprints')
