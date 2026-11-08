#!/usr/bin/env python3
"""Current edition x15.2: immutable predecessor and headless Dashboard contracts.

These tests execute the x15.2 search/sort and wrapping layout method bodies
using Qt-free stand-ins. Actual painting/Wayland responsiveness needs Fedora.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

PKG = 'riqatony_desk'
ROOT = Path(__file__).resolve().parents[2]
PREDECESSOR = json.loads(Path(__file__).with_name('x152-predecessor-fingerprints.json').read_text())
DASH = ROOT / PKG / 'widgets/workspace/dashboard.py'

ALLOWED = {
    'README.md', 'desk-health-check.json', 'suite-pythoine-component.json',
    f'{PKG}/__init__.py', f'{PKG}/app_constants.py', f'{PKG}/widgets/workspace/dashboard.py',
    f'{PKG}/tools/release_check.py', f'{PKG}/' + ('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk') + '.json',
    f'{PKG}/packaging/fedora/build-appimage.sh', f'{PKG}/packaging/fedora/test-appimage.sh',
    f'{PKG}/packaging/appimage/' + ('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk') + '.desktop',
    f'{PKG}/packaging/appimage/io.github.brunonlinespace.' + ('maqaronydesk' if PKG=='maqarony_desk' else 'riqatonydesk') + '.metainfo.xml',
    f'{PKG}/packaging/README.md', f'{PKG}/docs/RELEASE_NOTES.md',
    f'{PKG}/docs/CHANGELOG.md', f'{PKG}/docs/README.md', f'{PKG}/docs/BUILDING.md',
    f'{PKG}/docs/RELEASE_CHECKLIST.md',
}
QA_DIR = 'tools' if PKG=='maqarony_desk' else 'qa'
NEW = {
    f'{PKG}/{QA_DIR}/x152_search_sort_qa.py',
    f'{PKG}/{QA_DIR}/x152-predecessor-fingerprints.json',
}
if PKG=='riqatony_desk':
    NEW.add(f'{PKG}/docs/RELEASE_CHECKLIST-x15.2.md')


def preservation_check():
    assert PREDECESSOR['version'] == '1.0.0-x15.1'
    old = PREDECESSOR['files']
    current = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ROOT.rglob('*') if p.is_file() and p.name!='SOURCE_MANIFEST.sha256'
        and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
    assert set(current)-set(old) == NEW, (set(current)-set(old))-NEW
    assert set(old)-set(current) == set(),set(old)-set(current)
    changed={p for p in old if old[p]!=current[p]}
    assert changed <= ALLOWED,sorted(changed-ALLOWED)
    for p in old:
        # No previously issued QA source, archived release notes or fingerprints may change.
        if '/qa/' in p or '/tools/x1' in p and ('_qa.py' in p or 'fingerprints.json' in p):
            assert old[p]==current[p],p
        if '/docs/history/' in p or '/docs/RELEASE_CHECKLIST-x15.1.md' in p:
            assert old[p]==current[p],p
    suite=json.loads((ROOT/'suite-pythoine-component.json').read_text())
    health=json.loads((ROOT/'desk-health-check.json').read_text())
    assert suite['version']==health['application']['version']=='1.0.0-x15.2'
    assert health['schema_version']==1
    for rel,digest in health['source_files'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
    return changed

class FakeCard:
    def __init__(self,path):self.path=path;self.visible=False;self.shows=0;self.hides=0
    def hide(self):self.visible=False;self.hides+=1
    def show(self):self.visible=True;self.shows+=1
    def deleteLater(self):self.deleted=True

class FakeLayout:
    def __init__(self):self.widgets=[];self.adds=0;self.removes=0;self.invalidates=0;self.activates=0
    def addWidget(self,w):
        if w in self.widgets:self.widgets.remove(w)
        self.widgets.append(w);self.adds+=1
    def removeWidget(self,w):
        if w in self.widgets:self.widgets.remove(w)
        self.removes+=1
    def invalidate(self):self.invalidates+=1
    def activate(self):self.activates+=1

class FakeGrid(FakeLayout):
    def __init__(self):super().__init__();self.reorders=0
    def replace_widgets(self,widgets):self.widgets=list(widgets);self.reorders+=1
    def clear(self):self.widgets.clear()

class FakeStack:
    def __init__(self):self.invalidations=0;self.geometry=0
    def invalidate_measurements(self):self.invalidations+=1
    def updateGeometry(self):self.geometry+=1

class FakeWidget:
    def __init__(self):self.visible=None;self.text='';self.geometry=0;self.updates=0
    def setVisible(self,x):self.visible=x
    def setText(self,t):self.text=t
    def updateGeometry(self):self.geometry+=1
    def update(self):self.updates+=1

class Entry:
    def __init__(self,name,modified):self.path=Path('/workspace/'+name);self.name=name;self.modified=modified;self.external=False

class Repository:
    def __init__(self,entries):self.entries=list(entries);self.dirty=set()
    def __iter__(self):return iter(self.entries)
    def search(self,q):return [e for e in self.entries if q in e.name.casefold()]
    def sorted(self,entries,mode):
        if mode=='title_az':return sorted(entries,key=lambda e:e.name)
        if mode=='title_za':return sorted(entries,key=lambda e:e.name,reverse=True)
        return sorted(entries,key=lambda e:e.modified,reverse=True)


def extract_methods():
    tree=ast.parse(DASH.read_text())
    dashboard=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='DashboardWidget')
    methods=[x for x in dashboard.body if isinstance(x,ast.FunctionDef) and x.name in ('_sync_card_layout_order','_apply_filter_and_sort','_reset','_detach_all_cards_from_layouts')]
    assert len(methods)==4
    code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),
          ast.ClassDef(name='DashboardProbe',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])
    env={}
    exec(compile(ast.fix_missing_locations(code),str(DASH),'exec'),env)
    return env['DashboardProbe']

def dashboard_contract():
    Probe=extract_methods()
    repo=Repository([Entry('alpha.md',1),Entry('charlie.md',3),Entry('bravo.md',2)])
    dash=Probe()
    dash._loading=False;dash.repository=repo;dash._sort_mode='modified';dash._query=''
    dash._layout_paths=();dash._visible_paths=()
    dash._list_cards={e.path:FakeCard(e.path) for e in repo}
    dash._grid_cards={e.path:FakeCard(e.path) for e in repo}
    dash._layout_signatures={}
    dash.list_layout=FakeLayout();dash.grid_layout=FakeGrid();dash.view_stack=FakeStack()
    dash.grid_host=FakeWidget();dash.summary_label=FakeWidget();dash.scroll=FakeWidget();dash.empty_label=FakeWidget()
    dash.unsaved_banner_calls=0
    dash._update_unsaved_banner=lambda count:setattr(dash,'unsaved_banner_calls',dash.unsaved_banner_calls+1)
    dash._apply_filter_and_sort()
    assert dash._layout_paths==tuple(e.path for e in sorted(repo.entries,key=lambda e:e.modified,reverse=True))
    assert len(dash.list_layout.widgets)==len(dash.grid_layout.widgets)==3
    assert all(c.visible for c in dash._list_cards.values())
    prev=(dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders,dash.view_stack.invalidations)
    dash._apply_filter_and_sort()   # no-op: no layout notification
    assert prev==(dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders,dash.view_stack.invalidations)
    dash._query='alpha';dash._apply_filter_and_sort()
    assert 'Showing 1 of 3' in dash.summary_label.text
    assert sum(c.visible for c in dash._grid_cards.values())==1
    assert sum(c.visible for c in dash._list_cards.values())==1
    assert (dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders)==prev[:3], 'search cannot detach/reinsert'
    dash._query='';dash._apply_filter_and_sort()
    assert sum(c.visible for c in dash._grid_cards.values())==3
    assert (dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders)==prev[:3], 'search reset cannot detach/reinsert'
    dash._sort_mode='title_az';dash._apply_filter_and_sort()
    assert [w.path.name for w in dash.list_layout.widgets]==['alpha.md','bravo.md','charlie.md']
    assert [w.path.name for w in dash.grid_layout.widgets]==['alpha.md','bravo.md','charlie.md']
    assert dash.grid_layout.reorders==2,'one initial and one changed ordering'
    counts=(dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders,dash.view_stack.invalidations)
    dash._apply_filter_and_sort()
    assert counts==(dash.list_layout.adds,dash.list_layout.removes,dash.grid_layout.reorders,dash.view_stack.invalidations)
    # Membership addition in an existing sorted workspace maintains both views.
    new=Entry('delta.md',4);repo.entries.append(new)
    dash._list_cards[new.path]=FakeCard(new.path);dash._grid_cards[new.path]=FakeCard(new.path)
    dash._apply_filter_and_sort()
    assert len(dash.list_layout.widgets)==len(dash.grid_layout.widgets)==4
    assert dash._list_cards[new.path].visible and dash._grid_cards[new.path].visible
    # Removal must not retain stale layout objects and must respect sorting.
    repo.entries.remove(new)
    dash.list_layout.removeWidget(dash._list_cards.pop(new.path));dash.grid_layout.removeWidget(dash._grid_cards.pop(new.path))
    dash._apply_filter_and_sort()
    assert len(dash.list_layout.widgets)==len(dash.grid_layout.widgets)==3
    # Full repository reset starts with empty layout identity.
    repo.entries.clear();dash._reset()
    assert not dash._layout_paths and not dash._visible_paths
    assert not dash.list_layout.widgets and not dash.grid_layout.widgets

class FakeItem:
    def __init__(self,widget):self._widget=widget
    def widget(self):return self._widget
    def isEmpty(self):return not self._widget.visible
    def sizeHint(self):return SimpleNamespace(width=lambda:40,height=lambda:20)
    def minimumSize(self):return SimpleNamespace(width=lambda:40,height=lambda:20)
    def setGeometry(self,rect):self._widget.rect=rect

class FakeQLayout:
    def __init__(self,parent=None):self.invalidations=0;self._spacing=0
    def setContentsMargins(self,*a):pass
    def setSpacing(self,value):self._spacing=value
    def spacing(self):return self._spacing
    def contentsMargins(self):return SimpleNamespace(left=lambda:0,right=lambda:0,top=lambda:0,bottom=lambda:0)
    def invalidate(self):self.invalidations+=1
    def addWidget(self,w):self.addItem(FakeItem(w))

class FakeQSize:
    def __init__(self,w=0,h=0):self.w=w;self.h=h
    def expandedTo(self,other):return FakeQSize(max(self.w,other.width()),max(self.h,other.height()))
    def __iadd__(self,other):self.w+=other.w;self.h+=other.h;return self
    def width(self):return self.w
    def height(self):return self.h

class FakeRect:
    def __init__(self,*args):
        if len(args)==4:self.xx,self.yy,self.ww,self.hh=args
        else:self.xx,self.yy=args[0];self.ww,self.hh=args[1].width(),args[1].height()
    def x(self):return self.xx
    def y(self):return self.yy
    def right(self):return self.xx+self.ww-1

def flow_contract():
    tree=ast.parse(DASH.read_text())
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='FlowLayout')
    env={'QLayout':FakeQLayout,'QSize':FakeQSize,'QRect':FakeRect,'QPoint':lambda x,y:(x,y),'Qt':SimpleNamespace(Orientation=lambda x:x)}
    code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),cls],type_ignores=[])
    exec(compile(ast.fix_missing_locations(code),str(DASH),'exec'),env)
    flow=env['FlowLayout'](spacing=10)
    a,b,c=(FakeCard(x) for x in ('a','b','c'))
    a.show();b.show();c.hide()
    flow.replace_widgets([a,b,c])
    assert flow.count()==3
    retain={i.widget():i for i in flow._items}
    assert flow.heightForWidth(100)==20,'hidden widget must not participate in wrapping geometry'
    flow.replace_widgets([b,a,c])
    assert flow.count()==3 and all(retain[w] is i for w,i in zip([b,a,c],flow._items))
    c.show()
    assert flow.heightForWidth(100)==50,'revealed third widget must wrap on a second line'
    flow.replace_widgets([a,c])
    assert flow.count()==2 and flow.itemAt(0).widget() is a


def main():
    changes=preservation_check()
    dashboard_contract()
    flow_contract()
    tree=ast.parse(DASH.read_text())
    db=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='DashboardWidget')
    rename=next(x for x in db.body if isinstance(x,ast.FunctionDef) and x.name.startswith('_on_') and x.name.endswith('_path_changed'))
    text=ast.unparse(rename)
    assert 'self._layout_paths = tuple(' in text and 'self._visible_paths = tuple(' in text
    apply = next(x for x in db.body if isinstance(x,ast.FunctionDef) and x.name=='_apply_filter_and_sort')
    assert '_detach_all_cards_from_layouts' not in ast.unparse(apply), 'No legacy full detach during search or sort'
    print(f'PASS {PKG} x15.2: immutable predecessor, filtering, ordering, card identity, reset, hidden FlowLayout geometry; modified={len(changes)}')

if __name__=='__main__':main()
