#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""x13.3: execute original Help methods using headless Qt stand-ins."""
from __future__ import annotations
import ast
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1]
source=(P/'widgets/window_parts/help_actions.py').read_text()
cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='HelpActionsMixin')
class Signal:
 def __init__(self):self.cb=[]
 def connect(self,fn):self.cb.append(fn)
 def emit(self,*args):
  for fn in self.cb:fn(*args)
class Stub:
 def __init__(self,*a,**kw):
  self.args=a;self.finished=Signal();self.clicked=Signal();self.toggled=Signal()
  self.shown=0;self.raised=0;self.activated=0
  self.search=SimpleNamespace(setFocus=lambda *a:None)
 def show(self):self.shown+=1
 def raise_(self):self.raised+=1
 def activateWindow(self):self.activated+=1
 def __getattr__(self,k):
  if k.startswith(('set','add')):return lambda *a,**kw:None
  raise AttributeError(k)
class Wizard(Stub):
 WizardStyle=SimpleNamespace(ModernStyle=1)
 WizardOption=SimpleNamespace(NoBackButtonOnStartPage=1,HaveCustomButton1=2)
 WizardButton=SimpleNamespace(CustomButton1=1,Stretch=2,BackButton=3,NextButton=4,FinishButton=5,CancelButton=6)
 def __init__(self,*a):super().__init__(*a);self.pages=[];self.buttons={};self.button_layout=[]
 def addPage(self,page):self.pages.append(page)
 def setButton(self,k,button):self.buttons[k]=button
 def setButtonLayout(self,layout):self.button_layout=list(layout)
class Box(Stub):
 def setChecked(self,value):self.checked=value
class Label(Stub):pass
class Button(Stub):pass
class Layout(Stub):pass
class Page(Stub):pass
class Dialog(Stub):pass
class Action:
 def __init__(self,text,shortcut='',submenu=None):self._text=text;self._shortcut=shortcut;self._menu=submenu
 def text(self):return self._text
 def menu(self):return self._menu
 def shortcut(self):return SimpleNamespace(toString=lambda _fmt:self._shortcut)
class Menu:
 def __init__(self,items):self.items=items
 def actions(self):return self.items
class Config:
 def __init__(self):self.items={};self.calls=[]
 def get(self,key,default=None):return self.items.get(key,default)
 def set(self,key,value,save=False):self.items[key]=value;self.calls.append((key,value,save))
class QMessage:
 calls=[]
 @classmethod
 def information(cls,*args):cls.calls.append(args)
class QTimer:
 @staticmethod
 def singleShot(delay,fn):assert delay==0;fn()
Qt=SimpleNamespace(WidgetAttribute=SimpleNamespace(WA_DeleteOnClose=1),TextFormat=SimpleNamespace(RichText=1),
 AlignmentFlag=SimpleNamespace(AlignLeft=1),FocusReason=SimpleNamespace(ShortcutFocusReason=1))
ns={'QWizard':Wizard,'QWizardPage':Page,'QCheckBox':Box,'QPushButton':Button,'QVBoxLayout':Layout,
 'QLabel':Label,'QMessageBox':QMessage,'QTimer':QTimer,'ShortcutsDialog':Dialog,'AboutDialog':Dialog,
 'QMenu':Menu,'QKeySequence':SimpleNamespace(SequenceFormat=SimpleNamespace(NativeText=1)),
 'Qt':Qt,'Path':Path}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(P/'widgets/window_parts/help_actions.py'),'exec'),ns)
class Host(ns['HelpActionsMixin']):
 def __init__(self):
  self.quick_tour_dialog=None;self.shortcuts_dialog=None;self.about_dialog=None
  self.config=Config();self.package_root=P;self.icon_path=P/'assets/icons/riqatonydesk.png'
  self.runtime_paths=SimpleNamespace(config_path=P/'test_config.json')
  self.desktop_launcher=object();self.launched=[]
  self.menus=[Menu([Action('A','Ctrl+A'),Action('Sub',submenu=Menu([Action('Nested','Ctrl+N')])),Action('No shortcut')]) for _ in range(7)]
  for k,menu in zip(('file_menu','edit_menu','format_menu','insert_menu','view_menu','settings_menu','help_menu'),self.menus):setattr(self,k,menu)
  for k in ('rename_file_action','zoom_reset_action','quick_start_action','close_context_action','open_context_tab_action',
    'next_document_tab_action','previous_document_tab_action','toggle_dashboard_view_action','toggle_sidebar_position_action'):
   setattr(self,k,Action(k,'Ctrl+K'))
 def windowIcon(self):return 'icon'
 def _tabs_enabled(self):return True
 def _current_page(self):return None
 def _launch_new_window(self,path):self.launched.append(path)
h=Host()
h._show_quick_tour();w=h.quick_tour_dialog
assert isinstance(w,Wizard) and len(w.pages)==7 and w.shown==1 and w.raised==1 and w.activated==1
assert list(w.buttons)==[1] and len(w.buttons[1].toggled.cb)==1
assert w.button_layout==[1,2,3,4,5,6]
w.buttons[1].toggled.emit(True)
assert h.config.calls==[('quick_tour_seen',True,True)]
h._show_quick_tour();assert h.quick_tour_dialog is w and w.shown==2 and len(w.pages)==7
w.finished.emit(1);assert h.quick_tour_dialog is None
catalog=h._shortcut_catalog()
assert list(catalog)==['File','Edit','Format','Insert','View','Settings','Help']
assert ('Nested',h.menus[0].items[1]._menu.items[0]) in catalog['File']
assert ('Open Context Tab',h.open_context_tab_action) in catalog['File']
assert ('Next Document Tab',h.next_document_tab_action) in catalog['View']
h._show_shortcuts();d=h.shortcuts_dialog
assert isinstance(d,Dialog) and d.shown==1
h._show_shortcuts();assert h.shortcuts_dialog is d and d.shown==2
d.finished.emit(1);assert h.shortcuts_dialog is None
h._open_documentation();assert h.launched==[P/'docs/Documentation.rtf']
h._show_about_dialog();a=h.about_dialog
assert a.args[0]==P/'assets/icons/riqatonydesk-about.png' and a.args[1]==h.runtime_paths.config_path
h._show_about_dialog();assert h.about_dialog is a and a.shown==2
a.finished.emit(1);assert h.about_dialog is None
print('PASS x13.3 headless: seven-page tour/footer, recursive seven-menu shortcuts, RTF documentation, About lifecycle')
