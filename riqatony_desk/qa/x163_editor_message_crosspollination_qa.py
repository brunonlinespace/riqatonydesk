#!/usr/bin/env python3
"""x16.3: narrow source-change and mocked runtime message-delivery contracts."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

P = Path(__file__).resolve().parents[1]
REF = json.loads((P / 'qa/x163_message_source_fingerprints.json').read_text())
assert REF['predecessor_version'] == '1.0.0-x16.2'
assert REF['current_version'] == '1.0.0-x16.3'
changed = {k for k in REF['current'] if REF['current'][k] != REF['predecessor'][k]}
assert changed == {'controllers/editor_manager.py', 'widgets/rtf_editor.py', 'widgets/rwpyn/editor_insertion.py', 'widgets/rwpyn/editor_lifecycle.py', '__init__.py', 'app_constants.py'}, changed
for rel, expected in REF['current'].items():
    assert hashlib.sha256((P / rel).read_bytes()).hexdigest() == expected, f'unapproved production drift: {rel}'


def method(rel, cls, name, scope=None):
    source=(P/rel).read_text()
    tree=ast.parse(source)
    klass=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name==cls)
    fn=next(node for node in klass.body if isinstance(node,ast.FunctionDef) and node.name==name)
    ns=scope or {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),rel,'exec'),ns)
    return ns[name]

# 1. Confirm successful RTF load in the editor, except when compatibility warnings take priority.
source=(P/'widgets/rwpyn/editor_lifecycle.py').read_text()
assert 'else: self._show_status_message(f"Loaded {os.path.basename(self.file_path)}", 3000)' in source
assert 'if self.rtf_compatibility_warnings: self._show_status_message("RTF opened with compatibility warnings.' in source
assert (P/'widgets/rtf_editor.py').read_text().count('self.load_file(initial_file, check_changes=False)') == 1
# Do not manufacture a second "Loaded" message in the parent page or manager.
assert 'Loaded {document.filename}' not in (P/'controllers/editor_manager.py').read_text()
assert 'Loaded {self.document.filename}' not in (P/'widgets/editor_page.py').read_text()
# Execute the exact RTF loading message branch (including its warning priority).
load_tree=ast.parse(source)
load_cls=next(n for n in load_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorFileLifecycleMixin')
load_fn=next(n for n in load_cls.body if isinstance(n,ast.FunctionDef) and n.name=='load_file')
message_branch=next(n for n in load_fn.body[-3:] if isinstance(n,ast.If) and isinstance(n.test,ast.Attribute) and n.test.attr=='rtf_compatibility_warnings')
for warnings, expected in [([],('Loaded example.rtf',3000)), (['unsupported field'],('RTF opened with compatibility warnings. Review File → Properties before saving.',7000))]:
    target=SimpleNamespace(rtf_compatibility_warnings=warnings,file_path='/tmp/example.rtf',messages=[])
    target._show_status_message=lambda *items:target.messages.append(items)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[message_branch],type_ignores=[])),'load_file-final-branch','exec'), {'self':target,'os':__import__('os')})
    assert target.messages==[expected],target.messages

# 2. Empty clipboard feedback, and successful paste unaltered.
class QApplication:
    clipboard_value = ''
    @staticmethod
    def clipboard(): return SimpleNamespace(text=lambda: QApplication.clipboard_value)

paste = method('widgets/rwpyn/editor_insertion.py','EditorInsertionMixin','paste_plain_text',
               {'QApplication':QApplication,'MAX_PASTE_CHARACTERS':1000000,'MAX_DOCUMENT_CHARACTERS':1000000})
class DummyCursor:
    def __init__(self):self.inserted=[]
    def selectionEnd(self):return 0
    def selectionStart(self):return 0
    def insertText(self,txt):self.inserted.append(txt)
class DummyDocument:
    def characterCount(self):return 1
class DummyEditor:
    def __init__(self,cursor):self.cursor=cursor
    def textCursor(self):return self.cursor
    def document(self):return DummyDocument()
class DummySurface:
    def __init__(self):self.messages=[];self.cursor=DummyCursor();self.visual_editor=DummyEditor(self.cursor)
    def document_editing_available(self):return True
    def _show_status_message(self,*args):self.messages.append(args)
for contents, expected in [('',None),('\x00',None),('Hello','Hello')]:
    s=DummySurface();QApplication.clipboard_value=contents
    paste(s)
    if expected is None:
        assert s.messages == [('Clipboard does not contain text that can be pasted.',3500)]
        assert not s.cursor.inserted
    else:
        assert s.messages==[] and s.cursor.inserted==[expected]

# 3. Insert/Overwrite path: original mode and count update retained.
class Qt:
    class Key:
        Key_Insert = 111
class QEvent:
    class Type:
        KeyPress = 22
        Enter = 10
        Leave = 11
class QToolTip:
    @staticmethod
    def hideText():pass
class QWidget:
    @staticmethod
    def eventFilter(*_):return False
class KeyEvent:
    def type(self):return QEvent.Type.KeyPress
    def key(self):return Qt.Key.Key_Insert
class DummyWidget:
    def __init__(self):self.overwrite=False
    def property(self,*_):return False
    def viewport(self):return object()
    def overwriteMode(self):return self.overwrite
    def setOverwriteMode(self,value):self.overwrite=value
class DummyHost:
    def __init__(self):self.visual_editor=DummyWidget();self.messages=[];self.count=0
    def update_status_counts(self):self.count+=1
    def _show_status_message(self,*args):self.messages.append(args)
    view_only=False
filter_key=method('widgets/rtf_editor.py','RicopadEditorWidget','eventFilter',
                  {'Qt':Qt,'QEvent':QEvent,'QToolTip':QToolTip,'QWidget':QWidget})
h=DummyHost();assert filter_key(h,h.visual_editor,KeyEvent()) is True
assert h.messages == [('Overwrite mode enabled.',2500)] and h.count==1 and h.visual_editor.overwrite
assert filter_key(h,h.visual_editor,KeyEvent()) is True
assert h.messages[-1] == ('Insert mode enabled.',2500) and h.count==2 and not h.visual_editor.overwrite

# 4. External targeted monitor: only state transitions, not repeated events.
class EditorPage:
    def __init__(self):self.backing_state='normal';self.next_state='normal';self.messages=[];self.handled=0
    def handle_backing_path_event(self):self.handled+=1;self.backing_state=self.next_state
    def show_editor_status(self,*args):self.messages.append(args)
class EditorManager:
    def __init__(self,page):self.states=SimpleNamespace(get=lambda _p:SimpleNamespace(editor_page=page))
monitor=method('controllers/editor_manager.py','EditorManager','_on_open_backing_path_changed',{'EditorPage':EditorPage,'Path':Path})
page=EditorPage();manager=EditorManager(page)
for state in ('normal','changed','changed','missing','missing','normal','missing'):
    page.next_state=state;monitor(manager,Path('/tmp/sample.rtf'))
assert page.handled == 7
assert page.messages == [
    ('File changed outside RiqatonyDesk.',5000),
    ('Backing file missing; the live RiqatonyDesk document remains protected.',6000),
    ('Backing file missing; the live RiqatonyDesk document remains protected.',6000),
]
# The existing persistent banner remains authoritative for all state transitions.
assert 'self.external_banner.show()' in (P/'widgets/editor_page.py').read_text()
assert 'self.external_banner.hide()' in (P/'widgets/editor_page.py').read_text()
assert 'page.handle_backing_path_event()' in (P/'controllers/file_actions.py').read_text()
print('PASS x16.3: successful-open feedback, empty clipboard, mode toggles, external transitions, narrow production hashes')
