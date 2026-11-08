#!/usr/bin/env python3
"""x6.0 preferences and new-document defaults extraction: frozen x5.0 AST parity."""
import ast, hashlib, json
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
DIR=APP/"widgets"
DATA=json.loads((APP/'qa/x6-method-fingerprints.json').read_text(encoding='utf-8'))
parse=lambda path:ast.parse(path.read_text(encoding='utf-8'))
cls=lambda path,name:next(n for n in parse(path).body if isinstance(n,ast.ClassDef) and n.name==name)
classes=[cls(DIR/"rtf_editor.py","RicopadEditorWidget"),
 cls(DIR/'editor_commands_appearance.py','EditorCommandsAppearanceMixin'),
 cls(DIR/'rwpyn/editor_preferences.py','EditorPreferencesMixin'),
 cls(DIR/'rwpyn/editor_printing.py','EditorPrintingMixin'),
 cls(DIR/'rwpyn/editor_search_view.py','EditorSearchViewMixin'),
 cls(DIR/'rwpyn/editor_formatting.py','EditorFormattingMixin'),
 cls(DIR/'rwpyn/editor_insertion.py','EditorInsertionMixin'),
 cls(DIR/"rwpyn/editor_lifecycle.py","EditorFileLifecycleMixin"),]
assert [ast.unparse(n) for n in classes[0].bases]==['EditorFileLifecycleMixin','EditorCommandsAppearanceMixin','EditorPreferencesMixin', 'EditorPrintingMixin', 'EditorSearchViewMixin', 'EditorFormattingMixin', 'EditorInsertionMixin', 'QWidget']
methods=[n for c in classes for n in c.body if isinstance(n,ast.FunctionDef)]
assert len(methods)==len({n.name for n in methods}), 'duplicate editor methods'
actual={m.name:hashlib.sha256(normalize_identity_dump(ast.dump(m,include_attributes=False)).encode()).hexdigest() for m in methods}
assert actual==DATA['methods'], 'method lost/added/AST-changed from frozen x5.0'
assert {m.name for m in classes[2].body if isinstance(m,ast.FunctionDef)}==set(DATA['moved'])
source=parse(DIR/'rwpyn/editor_preferences.py')
original=parse(DIR/"rtf_editor.py")
funcs={n.name:n for n in source.body if isinstance(n,ast.FunctionDef)}
for name,expected in DATA['helpers'].items():
    assert name in funcs
    assert hashlib.sha256(normalize_identity_dump(ast.dump(funcs[name],include_attributes=False)).encode()).hexdigest()==expected
    assert not any(isinstance(n,ast.FunctionDef) and n.name==name for n in original.body)
assign=lambda tree,name:next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
assert ast.dump(assign(source,'MAX_CONFIG_FILE_SIZE').value,include_attributes=False)==DATA['max_config']
assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MAX_CONFIG_FILE_SIZE' for t in n.targets) for n in original.body)

print('PASS: x6.0 eleven preferences/defaults methods, three helpers and prior editor ASTs preserved')
