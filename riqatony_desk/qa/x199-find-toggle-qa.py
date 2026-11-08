#!/usr/bin/env python3
"""Execute RiqatonyDesk's real editor Find/Replace methods without PyQt6.

Both Desk-shell commands and embedded editor QAction connections are verified.
"""
from pathlib import Path
import ast
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1]
src=(P/'widgets/rwpyn/editor_search_view.py').read_text(encoding='utf8')
cls=next(n for n in ast.parse(src).body if isinstance(n,ast.ClassDef) and n.name=='EditorSearchViewMixin')
methods=('toggle_find_panel','show_find_panel','hide_find_panel','show_replace_dialog')
selected=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in methods]
assert len(selected)==len(methods)
module=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='ActualSearch',bases=[],keywords=[],body=selected,decorator_list=[])],type_ignores=[]))
ns={'Qt':SimpleNamespace(FocusReason=SimpleNamespace(ShortcutFocusReason=1))}
exec(compile(module,'<real RiqatonyDesk search methods>','exec'),ns)
class Input:
    def __init__(self,h):self.h=h;self.focus=False
    def hasFocus(self):return self.focus
    def setFocus(self,_reason=None):
        for field in (self.h.search_entry,self.h.replace_entry,self.h.text_area):field.focus=False
        self.focus=True
    def setText(self,_):pass
    def selectAll(self):pass
class TextArea:
    def __init__(self,h):self.h=h;self.focus=False
    def textCursor(self):return SimpleNamespace(selectedText=lambda:'')
    def setFocus(self,_reason=None):
        for field in (self.h.search_entry,self.h.replace_entry,self):field.focus=False
        self.focus=True
class Panel:
    def __init__(self):self.visible=False
    def isVisible(self):return self.visible
    def show(self):self.visible=True
    def hide(self):self.visible=False
class Host(ns['ActualSearch']):
    def __init__(self):
        self.search_container=Panel()
        self.search_entry=Input(self)
        self.replace_entry=Input(self)
        self.text_area=TextArea(self)
        self.show_search_bar=False
        self.refreshes=0
        self.clears=0
    def refresh_search(self):self.refreshes+=1
    def clear_search_results(self):self.clears+=1
h=Host()
assert h.toggle_find_panel(False) is True and h.search_container.isVisible()
h.text_area.setFocus() # Ribbon/menu stole focus
assert h.toggle_find_panel(False) is False and not h.search_container.isVisible()
assert h.clears==1 and h.text_area.focus
assert h.toggle_find_panel(True) is True and h.replace_entry.hasFocus()
h.text_area.setFocus()
assert h.toggle_find_panel(True) is False and not h.search_container.isVisible()
assert h.toggle_find_panel(False) is True
h.text_area.setFocus()
assert h.toggle_find_panel(True) is True and h.replace_entry.hasFocus() and h.search_container.isVisible()
h.text_area.setFocus()
assert h.toggle_find_panel(False) is True and h.search_entry.hasFocus()
assert h.toggle_find_panel(False) is False and not h.search_container.isVisible()
h.show_replace_dialog()
assert h.replace_entry.hasFocus()
h.text_area.setFocus()
assert h.toggle_find_panel(True) is False
assert h.clears>=4
# This is the previously broken route: the embedded editor QAction must toggle.
actions=(P/'widgets/editor_commands_appearance.py').read_text(encoding='utf8')
assert 'self.search_bar_action.triggered.connect(lambda _checked=False:self.toggle_find_panel(False))' in actions
assert '"Find and Replace",lambda:self.toggle_find_panel(True)' in actions
assert 'self.search_bar_action.triggered.connect(lambda _checked=False:self.show_find_panel(False))' not in actions
# The Desk shell already toggles; do not undo that path.
shell=(P/'widgets/main_window.py').read_text(encoding='utf8')
assert 'page.call_editor("toggle_find_panel", False)' in shell
assert 'page.call_editor("toggle_find_panel", True)' in shell
print('PASS x19.9: actual Find/Replace toggle methods, focus loss, mode switches, shell and embedded editor actions')
