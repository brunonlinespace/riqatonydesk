#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless behavioural tests on the extracted methods (not a Qt GUI test)."""
from __future__ import annotations
import ast
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
tree=ast.parse((PKG/'widgets/window_parts/layout_controls.py').read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LayoutControlsMixin')
class EditorPage:
    def __init__(self): self.header=None;self.status=None
    def set_header_visible(self, visible):self.header=visible
    def set_status_visible(self,visible):self.status=visible
class FakeAction:
    def __init__(self, checked=False):self.checked=checked;self.blocking=[]
    def blockSignals(self,value):self.blocking.append(value)
    def setChecked(self,value):self.checked=value
    def isChecked(self):return self.checked
class Widget:
    def __init__(self,visible=True):self.visible=visible
    def setVisible(self,visible):self.visible=bool(visible)
    def isVisible(self):return self.visible
class Config:
    def __init__(self):self.values={};self.writes=[]
    def set(self,key,value,save=False):self.values[key]=value;self.writes.append((key,value,save))
    def get(self,key,default=None):return self.values.get(key,default)
class Splitter:
    def __init__(self,left,right):self.widgets=[left,right];self.width_value=1300;self.sizes_value=[260,1032];self.stretch={};self.collapsible={}
    def indexOf(self,item):return self.widgets.index(item)
    def sizes(self):return self.sizes_value
    def width(self):return self.width_value
    def handleWidth(self):return 8
    def setSizes(self,sizes):self.sizes_value=list(sizes)
    def insertWidget(self,index,item):self.widgets.remove(item);self.widgets.insert(index,item)
    def setStretchFactor(self,index,value):self.stretch[index]=value
    def setCollapsible(self,index,value):self.collapsible[index]=value
class Ribbon:
    def __init__(self):self._collapsed=False;self.calls=[]
    def set_collapsed(self,value,emit=True):self._collapsed=value;self.calls.append((value,emit))
namespace={'EditorPage':EditorPage,'SIDEBAR_MINIMUM_WIDTH':205}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),'<layout mixin>','exec'),namespace)
Mixin=namespace['LayoutControlsMixin']
class Window(Mixin):
    def __init__(self):
        self.navigation=Widget();self.content_host=Widget();self.splitter=Splitter(self.navigation,self.content_host)
        self._restored_sidebar_width=260;self.config=Config();self.sidebar_position_actions={'left':FakeAction(True),'right':FakeAction()}
        self.sidebar_action=FakeAction(True);self.status_bar_action=FakeAction(True);self.file_header_action=FakeAction(True)
        self._status=Widget();self.states=[('x',type('State',(),{'editor_page':EditorPage()})())]
        self.shell_ribbon=Ribbon();self._collapsed_mode_restore=None;self.icon_sync=0;self.fullscreen=None
    def statusBar(self):return self._status
    def _sync_sidebar_position_icons(self):self.icon_sync+=1
    def showFullScreen(self):self.fullscreen=True
    def showNormal(self):self.fullscreen=False
w=Window()
assert w._sidebar_position()=='left'
w._set_sidebar_position('right')
assert w._sidebar_position()=='right' and w.splitter.indexOf(w.navigation)==1
assert w.config.get('sidebar_position')=='right' and w.icon_sync==1
assert w.sidebar_position_actions['right'].checked and not w.sidebar_position_actions['left'].checked
assert w._logical_splitter_sizes()[0]==260
w._toggle_sidebar_position()
assert w._sidebar_position()=='left' and w.icon_sync==2
assert w.config.get('sidebar_position')=='left'
w._set_splitter_sidebar_width(20)
assert w._logical_splitter_sizes()[0]==205
w._set_splitter_sidebar_width(20000)
assert w._logical_splitter_sizes()[0]<=w.splitter.width()-w.splitter.handleWidth()-420
w._set_status_visible(False,persist=True)
assert not w.statusBar().isVisible() and w.states[0][1].editor_page.status is False
assert w.config.get('show_status_bar') is False
w._toggle_status_bar(True)
assert w.statusBar().isVisible() and w.config.get('show_status_bar') is True
w._set_file_header_visible(False,persist=True)
assert w.states[0][1].editor_page.header is False and w.config.get('show_file_header') is False
w._toggle_file_header(True)
w.file_header_action.setChecked(True)  # Real checkable QAction sets this before invoking its slot.
assert w.states[0][1].editor_page.header is True and w.config.get('show_file_header') is True
previous=len(w.config.writes)
w._toggle_collapsed_mode(True)
assert w._collapsed_mode_restore is not None and not w.navigation.isVisible()
assert not w.statusBar().isVisible() and not w.states[0][1].editor_page.header
assert w.shell_ribbon._collapsed and w.shell_ribbon.calls[-1]==(True,False)
assert len(w.config.writes)==previous,'Focused Mode should not persist temporary layout'
w._toggle_collapsed_mode(False)
assert w._collapsed_mode_restore is None and w.navigation.isVisible()
assert w.statusBar().isVisible() and w.states[0][1].editor_page.header
assert w.shell_ribbon.calls[-1]==(False,False)
assert len(w.config.writes)==previous,'restoring Focused Mode should not persist temporary layout'
w._toggle_fullscreen(True)
assert w.fullscreen
w._toggle_fullscreen(False)
assert w.fullscreen is False
print('PASS x13.2 headless: sidebar position/width/icons, Status, Header, Focused Mode and Full Screen')
