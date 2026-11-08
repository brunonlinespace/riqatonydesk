#!/usr/bin/env python3
"""x15.1 predecessor-preservation + headless Dashboard geometry contract QA.

Qt is represented by small stand-ins ONLY for contract testing. Real GUI latency,
painting, native resizing, and scrolling require Fedora/PyQt6 execution.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

PKG = "riqatony_desk"
ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads(Path(__file__).with_name('x151-predecessor-fingerprints.json').read_text())
DASH = ROOT / PKG / 'widgets/workspace/dashboard.py'
ALLOWED_CHANGES = {
    'README.md', 'desk-health-check.json', 'suite-pythoine-component.json',
    PKG + '/__init__.py', PKG + '/app_constants.py',
    PKG + '/' + ('maqaronydesk.json' if PKG=='maqarony_desk' else 'riqatonydesk.json'),
    PKG + '/widgets/workspace/dashboard.py', PKG + '/tools/release_check.py',
    PKG + '/packaging/fedora/build-appimage.sh',
    PKG + '/packaging/fedora/test-appimage.sh',
    PKG + '/packaging/appimage/' + ('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk') + '.desktop',
    PKG + '/packaging/appimage/io.github.brunonlinespace.' + ('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk') + '.metainfo.xml',
    PKG + '/packaging/README.md',
    PKG + '/docs/RELEASE_NOTES.md', PKG + '/docs/CHANGELOG.md',
    PKG + '/docs/BUILDING.md', PKG + '/docs/RELEASE_CHECKLIST.md', PKG + '/docs/README.md',
}
NEW_FILES = {
    PKG + "/docs/RELEASE_CHECKLIST-x15.1.md",
    PKG + '/' + ('tools' if PKG=='maqarony_desk' else 'qa') + '/x151-predecessor-fingerprints.json',
    PKG + '/' + ('tools' if PKG=='maqarony_desk' else 'qa') + '/x151_layout_geometry_qa.py',
}


def verify_preservation():
    old = REFERENCE['files']
    assert REFERENCE['version']=='1.0.0-x15.0'
    current={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
        and p.suffix not in ('.pyc', '.pyo') and p.name!='SOURCE_MANIFEST.sha256'}
    assert set(current)-set(old)==NEW_FILES,(set(current)-set(old))-NEW_FILES
    assert set(old)-set(current)==set(),set(old)-set(current)
    changed={p for p in old if old[p]!=current[p]}
    assert changed<=ALLOWED_CHANGES,sorted(changed-ALLOWED_CHANGES)
    assert PKG+'/widgets/workspace/dashboard.py' in changed
    for p in old:
        if '/qa/' in p and not p.endswith('release_check.py'):
            # The historical QA files, including x15.0's, remain byte-identical.
            assert old[p]==current[p],p
        if 'x150_' in p or 'x150-' in p:
            assert old[p]==current[p],p
    assert (ROOT/'suite-pythoine-component.json').is_file()
    suite=json.loads((ROOT/'suite-pythoine-component.json').read_text())
    health=json.loads((ROOT/'desk-health-check.json').read_text())
    assert suite['version']==health['application']['version']=='1.0.0-x15.1'
    assert health['schema_version']==1
    for rel, digest in health['source_files'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
    return changed


class FakeSignal:
    def __init__(self): self.callbacks=[]
    def connect(self,fn): self.callbacks.append(fn)
    def emit(self,*args):
        for fn in self.callbacks: fn(*args)


class FakeSize:
    def __init__(self, width=0,height=0):
        if isinstance(width,FakeSize):self.w,self.h=width.w,width.h
        else:self.w,self.h=width,height
    def height(self):return self.h
    def setHeight(self,height):self.h=height
    def __repr__(self):return f'FakeSize({self.w},{self.h})'


class FakeScrollArea:
    def __init__(self,width):self.v=SimpleNamespace(width=lambda:width)
    def viewport(self):return self.v
    def parentWidget(self):return None


class FakeStack:
    def __init__(self,parent=None):
        self._parent=parent;self._pages=[];self._current=None
        self.currentChanged=FakeSignal();self.geometry_updates=0
    def addWidget(self,page):
        self._pages.append(page)
        if self._current is None:self._current=page
        return len(self._pages)-1
    def currentWidget(self):return self._current
    def setCurrentWidget(self,page):
        if self._current is not page:
            self._current=page
            self.currentChanged.emit(self._pages.index(page))
    def updateGeometry(self):self.geometry_updates+=1
    def eventFilter(self,watched,event):return False
    def contentsMargins(self):return SimpleNamespace(left=lambda:0,right=lambda:0,top=lambda:0,bottom=lambda:0)
    def parentWidget(self):return self._parent
    def width(self):return 900
    def heightForWidth(self,width):return -1
    def sizeHint(self):return FakeSize(800,600)
    def minimumSizeHint(self):return FakeSize(800,600)


class FakeLayout:
    def __init__(self,wrap):self.wrap=wrap;self.height_queries=0
    def hasHeightForWidth(self):return self.wrap
    def heightForWidth(self,width):
        self.height_queries+=1
        return width*2


class FakePage:
    def __init__(self,wrap=False):
        self._layout=FakeLayout(wrap)
        self.size_queries=0;self.min_queries=0
    def installEventFilter(self,obj):self._filter=obj
    def layout(self):return self._layout
    def sizeHint(self):
        self.size_queries+=1
        return FakeSize(750,200)
    def minimumSizeHint(self):
        self.min_queries+=1
        return FakeSize(400,180)
    def width(self):return 750


def geometry_contract():
    tree=ast.parse(DASH.read_text(encoding='utf-8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CurrentPageStack')
    enum=SimpleNamespace(LayoutRequest=1,FontChange=2,StyleChange=3,ContentsRectChange=4)
    namespace={
        'QStackedWidget': FakeStack,'QSize':FakeSize,'QScrollArea':FakeScrollArea,
        'QEvent':SimpleNamespace(Type=enum),
    }
    program=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),cls],type_ignores=[])
    exec(compile(ast.fix_missing_locations(program),str(DASH),'exec'),namespace)
    cls=namespace['CurrentPageStack']
    scroll=FakeScrollArea(900)
    stack=cls(scroll)
    list_page=FakePage()
    grid_page=FakePage(wrap=True)
    stack.addWidget(list_page); stack.addWidget(grid_page)
    assert stack.sizeHint().height()==200
    assert stack.sizeHint().height()==200
    assert list_page.size_queries==1,'List size-hint cache not working'
    assert stack.minimumSizeHint().height()==180
    assert stack.minimumSizeHint().height()==180
    assert list_page.min_queries==1
    stack.setCurrentWidget(grid_page)
    assert stack.geometry_updates==1,'Switch must notify geometry exactly once'
    for _ in range(8):assert stack.sizeHint().height()==1800
    assert grid_page.size_queries==1 and grid_page.layout().height_queries==1
    scroll.v=SimpleNamespace(width=lambda:640)
    assert stack.sizeHint().height()==1280
    assert grid_page.layout().height_queries==2,'Viewport resize must invalidate width-specific result'
    # An ordinary palette repaint does not alter cached geometry.
    stack.eventFilter(grid_page,SimpleNamespace(type=lambda:99))
    stack.sizeHint()
    assert grid_page.layout().height_queries==2
    # A Qt layout-change event invalidates ALL cached page sizes.
    stack.eventFilter(grid_page,SimpleNamespace(type=lambda:enum.LayoutRequest))
    assert stack.sizeHint().height()==1280
    assert grid_page.layout().height_queries==3
    stack.invalidate_measurements()
    assert stack.sizeHint().height()==1280
    assert grid_page.layout().height_queries==4
    stack.setCurrentWidget(list_page)
    assert stack.geometry_updates==2
    assert stack.sizeHint().height()==200
    # Dashboard should not emit duplicate explicit geometry invalidations.
    dashboard=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DashboardWidget')
    methods={n.name:n for n in dashboard.body if isinstance(n,ast.FunctionDef)}
    setter=methods['set_view_mode']
    calls=[ast.unparse(n.func) for n in ast.walk(setter) if isinstance(n,ast.Call)]
    assert calls.count('self.view_stack.setCurrentWidget')==1
    assert 'self.view_stack.updateGeometry' not in calls
    assert 'self.scroll.widget().updateGeometry' not in calls
    relayout=methods['_apply_filter_and_sort']
    body=ast.unparse(relayout)
    assert body.index('self.view_stack.invalidate_measurements()')<body.index('self._detach_all_cards_from_layouts()')


def main():
    changed=verify_preservation()
    geometry_contract()
    print(f'PASS {PKG} x15.1: predecessor preserved, cached sizes invalidated, one switch notification; changes={len(changed)}')

if __name__=='__main__':main()
