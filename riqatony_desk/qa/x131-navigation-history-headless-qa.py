#!/usr/bin/env python3
# RiqatonyDesk
# SPDX-License-Identifier: GPL-3.0-or-later
"""Headless checks for exact extracted history implementation, not Qt GUI testing."""
from __future__ import annotations
import ast
import tempfile
from pathlib import Path

PKG=Path(__file__).resolve().parents[1]
source=(PKG/'widgets/window_parts/navigation_history.py').read_text()
cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='NavigationHistoryMixin')
class Timer:
    pending=[]
    @classmethod
    def singleShot(cls,delay,fn):
        assert delay==0
        cls.pending.append(fn)
    @classmethod
    def drain(cls):
        while cls.pending:cls.pending.pop(0)()
ns={'Path':Path,'QTimer':Timer}
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])), '<RiqatonyDesk history mixin>','exec'),ns)
Mixin=ns['NavigationHistoryMixin']
class Repository:
    def __init__(self):self.items={}
    def get(self,path):return self.items.get(path)
class Manager:
    def __init__(self,owner):self.owner=owner;self.calls=[]
    def show_dashboard(self):
        self.calls.append(('dashboard',None))
        self.owner._record_dashboard_navigation()
        return True
    def open_folder(self,path):
        self.calls.append(('folder',path))
        self.owner._record_folder_navigation(path)
        return object()
    def open_document(self,path):
        self.calls.append(('document',path))
        self.owner._record_document_navigation(type('Doc',(),{'path':path})())
        return object()
class Window(Mixin):
    def __init__(self,root):
        self.library_root=root
        self._navigation_history=[]
        self._navigation_current='dashboard'
        self._navigation_pending=None
        self._navigation_record_scheduled=False
        self._navigation_back_in_progress=False
        self.editor_manager=Manager(self)
        self.repository=Repository()
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp).resolve()
    folder=root/'docs';folder.mkdir()
    doc=folder/'test.rtf';doc.write_bytes(b'{\\rtf1\\ansi test}')
    w=Window(root);w.repository.items[doc]=object()
    w._record_folder_navigation(folder)
    w._record_document_navigation(type('Doc',(),{'path':doc})())
    assert len(Timer.pending)==1,'history coalescing must schedule once'
    Timer.drain()
    assert w._navigation_current==f'document:{doc}'
    assert w._navigation_history==['dashboard']
    w._record_folder_navigation(folder);Timer.drain()
    assert w._navigation_history==['dashboard',f'document:{doc}']
    w._navigate_back()
    assert w.editor_manager.calls==[('document',doc)]
    assert w._navigation_current==f'document:{doc}'
    assert not w._navigation_back_in_progress
    w._navigate_back()
    assert w.editor_manager.calls[-1]==('dashboard',None)
    w._navigation_current='folder:'+str(folder)
    w._navigation_history=['dashboard','folder:'+str(root.parent/'outside')]
    w._navigate_back()
    assert w.editor_manager.calls[-1]==('dashboard',None)
    # Missing file records are skipped; only a stored repository record is valid.
    w._navigation_current='dashboard'
    w._navigation_history=['folder:'+str(folder),'document:'+str(root/'missing.rtf')]
    w._navigate_back()
    assert w.editor_manager.calls[-1]==('folder',folder)
    w=Window(root)
    for i in range(70):
        w._queue_navigation_record('document:'+str(root/f'f{i}.rtf'))
        Timer.drain()
    assert len(w._navigation_history)==64
    w._queue_navigation_record(w._navigation_current);Timer.drain()
    assert len(w._navigation_history)==64
    assert not Timer.pending
print('PASS x13.1 headless: coalesced RTF navigation, Back, invalid targets and 64-record bound')
