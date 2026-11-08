#!/usr/bin/env python3
"""x3.0 insertion/clipboard extraction: baseline AST and unchanged host contracts."""
import ast, hashlib, json
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HOST=ROOT/'widgets/rtf_editor.py'
INS=ROOT/'widgets/rwpyn/editor_insertion.py'
FMT=ROOT/'widgets/rwpyn/editor_formatting.py'
BASELINE=json.loads((ROOT/'qa/x3-method-fingerprints.json').read_text(encoding='utf-8'))
parse=lambda path: ast.parse(path.read_text(encoding='utf-8'))
host=parse(HOST); ext=parse(INS); fmt=parse(FMT)
cls=next(n for n in host.body if isinstance(n,ast.ClassDef) and n.name=='RicopadEditorWidget')
insert=next(n for n in ext.body if isinstance(n,ast.ClassDef) and n.name=='EditorInsertionMixin')
formatting=next(n for n in fmt.body if isinstance(n,ast.ClassDef) and n.name=='EditorFormattingMixin')
assert [ast.unparse(n) for n in cls.bases]==['EditorFileLifecycleMixin','EditorCommandsAppearanceMixin','EditorPreferencesMixin','EditorPrintingMixin', 'EditorSearchViewMixin', 'EditorFormattingMixin', 'EditorInsertionMixin', 'QWidget']
get_methods=lambda cls: {n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
search_tree=parse(ROOT/('widgets/rwpyn/editor_search_view.py' if (ROOT/'widgets/rwpyn/editor_search_view.py').exists() else 'editor_search_view.py'))
search=next(n for n in search_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorSearchViewMixin')
printing_tree=parse(ROOT/'widgets/rwpyn/editor_printing.py')
printing=next(n for n in printing_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorPrintingMixin')
pref_tree=ast.parse((__import__('pathlib').Path(__file__).resolve().parents[1]/"widgets/rwpyn/editor_preferences.py").read_text(encoding='utf-8'))
pref_cls=next(n for n in pref_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorPreferencesMixin')
command_tree=parse(ROOT/'widgets/editor_commands_appearance.py')
command_cls=next(n for n in command_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorCommandsAppearanceMixin')
lifecycle_cls=next(n for n in parse(ROOT/('editor_lifecycle.py' if 'riqatonypad.py' in str(HOST) else 'widgets/rwpyn/editor_lifecycle.py')).body if isinstance(n,ast.ClassDef) and n.name=='EditorFileLifecycleMixin')
separate=[get_methods(lifecycle_cls),get_methods(cls),get_methods(insert),get_methods(formatting),get_methods(search),get_methods(printing),get_methods(pref_cls),get_methods(command_cls)]
assert len(separate[2])==39 and set(separate[2])==set(BASELINE['moved'])
assert len(set.union(*(set(group) for group in separate)))==sum(len(group) for group in separate),'duplicate editing methods'
joined={name:node for group in separate for name,node in group.items()}
actual={name:hashlib.sha256(normalize_identity_dump(ast.dump(node,include_attributes=False)).encode()).hexdigest() for name,node in joined.items()}
assert actual==BASELINE['methods'],'original x2.0 editor method changed/lost/added'
for name in BASELINE['helper_functions']:
    assert not any(isinstance(n,ast.FunctionDef) and n.name==name for n in host.body), f'{name} still defined in host'
    new=next(n for n in ext.body if isinstance(n,ast.FunctionDef) and n.name==name)
    # Frozen x1.0 AST hash is checked by x1-widget-extraction-qa.
    assert new is not None
for name in BASELINE['moved_constants']:
    assert any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets) for n in ext.body)
    assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets) for n in host.body)
assert any(isinstance(n,ast.ImportFrom) and any(alias.name=='EditorInsertionMixin' for alias in n.names) for n in host.body)
print('PASS: x3.0 39 insertion/clipboard methods AST-unchanged, preserved host interface')
