from pathlib import Path
import ast, types, tempfile
source=(Path(__file__).resolve().parents[1] / 'widgets/window_parts/document_tabs.py').read_text()
tree=ast.parse(source)
cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='DocumentTabsMixin')
class FakeTabs:
 class ButtonPosition:
  LeftSide=1;RightSide=2
 def __init__(self):self.tabs=[];self.index=-1;self.visible=False
 def count(self):return len(self.tabs)
 def tabData(self,i):return self.tabs[i]['data']
 def addTab(self,text):self.tabs.append({'text':text,'data':None,'tip':None});return len(self.tabs)-1
 def removeTab(self,i):self.tabs.pop(i);self.index=min(self.index,len(self.tabs)-1)
 def setTabData(self,i,x):self.tabs[i]['data']=x
 def setTabText(self,i,x):self.tabs[i]['text']=x
 def setTabToolTip(self,i,x):self.tabs[i]['tip']=x
 def setTabButton(self,*a):pass
 def setVisible(self,b):self.visible=b
 def blockSignals(self,b):pass
 def setCurrentIndex(self,i):self.index=i
 def currentIndex(self):return self.index
class Doc:
 def __init__(self,path,dirty=False):self.path=Path(path);self.dirty=dirty;self.filename=self.path.name
class Repo:
 def __init__(self,*mods):self.documents={x.path.resolve():x for x in mods}
 def get(self,path):return self.documents.get(Path(path).resolve())
class Config:
 def __init__(self):self.val={'tabs_enabled':True}
 def get(self,k,d):return self.val.get(k,d)
 def set(self,k,v,save=False):self.val[k]=v
class Action:
 def blockSignals(self,b):pass
 def setChecked(self,b):pass
 def setText(self,t):pass
 def setToolTip(self,t):pass
class Manager:
 def __init__(self):self.current_document=None;self.current_folder=None;self.closed=[];self.views=[]
 def show_dashboard(self):self.views.append('dashboard');self.current_document=None;self.current_folder=None
 def open_folder(self,p):self.views.append('folder');self.current_folder=Path(p);self.current_document=None
 def open_document(self,m):self.views.append('module');self.current_document=m
 def close_document(self,m):self.closed.append(m);self.current_document=None;return True
 def prepare_tabs_disabled(self):return True
scope={'Path':Path,'DocumentEntry':Doc,'QTabBar':FakeTabs,'__name__':'offline_test'}
exec(compile(ast.Module(body=[cls],type_ignores=[]),'<extracted mixin>','exec'),scope)
with tempfile.TemporaryDirectory() as d:
 base=Path(d);(base/'folder').mkdir(); a=Doc(base/'folder/a.rtf');b=Doc(base/'folder/b.rtf',True)
 x=scope['DocumentTabsMixin']();x.document_tabs=FakeTabs();x.repository=Repo(a,b);x.config=Config();x.editor_manager=Manager();x.library_root=base;x.tabs_actions={'enabled':Action(),'disabled':Action()};x.app_tabs_toggle_action=Action();x._refresh_action_icons=lambda:None;x._update_window_title=lambda:None;x._sync_app_settings_toggle_actions=lambda:None
 x._ensure_document_tab(a);x._ensure_document_tab(b)
 assert x.document_tabs.count()==2 and x.document_tabs.tabs[1]['text']=='b.rtf*'
 x._select_document_tab(a);assert x.document_tabs.currentIndex()==0
 x._cycle_document_tab(1);assert x.editor_manager.current_document is b
 x._show_folder_navigation_tab(base/'folder');assert x.document_tabs.count()==3
 x._activate_document_tab(x._navigation_tab_index());assert x.editor_manager.current_folder==(base/'folder')
 x._select_document_tab(a);assert x.document_tabs.count()==2
 x._rebind_document_tab(a.path,base/'folder/c.rtf');assert x.document_tabs.tabData(0)==str(base/'folder/c.rtf')
 x._remove_document_tab(b.path);assert x.document_tabs.count()==1
 x._reset_document_tabs();assert x.document_tabs.count()==0 and not x.document_tabs.visible
 x._show_dashboard_navigation_tab();assert x.document_tabs.count()==1
 x._activate_document_tab(0);assert x.editor_manager.views[-1]=='dashboard'
 x._set_tabs_enabled(False);assert x.config.get('tabs_enabled',True) is False and not x.document_tabs.visible
 x._set_tabs_enabled(True);assert x.config.get('tabs_enabled',False) is True
 print('PASS headless tab contract: create/select/cycle/rebind/remove/reset/context navigation/enable-disable')
