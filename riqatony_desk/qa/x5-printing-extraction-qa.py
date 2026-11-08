#!/usr/bin/env python3
"""x5.0 exact frozen x4.0 print, PDF and document properties extraction parity."""
import ast, hashlib, json, re
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
DIR=APP/'widgets'
DATA=json.loads((APP/'qa/x5-method-fingerprints.json').read_text(encoding='utf-8'))
parse=lambda path:ast.parse(path.read_text(encoding='utf-8'))
cls=lambda path,name:next(n for n in parse(path).body if isinstance(n,ast.ClassDef) and n.name==name)
classes=[cls(DIR/'rtf_editor.py','RicopadEditorWidget'),
 cls(DIR/'editor_commands_appearance.py','EditorCommandsAppearanceMixin'),
 cls(DIR/'editor_printing.py','EditorPrintingMixin'),
 cls(DIR/'editor_search_view.py','EditorSearchViewMixin'),
 cls(DIR/'editor_formatting.py','EditorFormattingMixin'),
 cls(DIR/'editor_insertion.py','EditorInsertionMixin'),
 cls(DIR/'editor_preferences.py','EditorPreferencesMixin'),
 cls(DIR/'editor_lifecycle.py','EditorFileLifecycleMixin'),]
assert [ast.unparse(n) for n in classes[0].bases]==['EditorFileLifecycleMixin','EditorCommandsAppearanceMixin','EditorPreferencesMixin','EditorPrintingMixin','EditorSearchViewMixin','EditorFormattingMixin','EditorInsertionMixin','QWidget']
all_methods=[m for c in classes for m in c.body if isinstance(m,ast.FunctionDef)]
assert len(all_methods)==len(set(m.name for m in all_methods)), 'duplicate methods'
actual={m.name:hashlib.sha256(normalize_identity_dump(ast.dump(m,include_attributes=False)).encode()).hexdigest() for m in all_methods}
assert actual==DATA['methods'], 'method AST changed, lost, or added'
assert set(m.name for m in classes[2].body if isinstance(m,ast.FunctionDef))==set(DATA['moved']), 'incorrect printing extraction inventory'
assert not (set(m.name for m in classes[0].body if isinstance(m,ast.FunctionDef))&set(DATA['moved']))
source=parse(DIR/'editor_printing.py')
functions={n.name:n for n in source.body if isinstance(n,ast.FunctionDef)}
assert set(DATA['helpers'])<=set(functions)
for name,expected in DATA['helpers'].items():
    assert hashlib.sha256(normalize_identity_dump(ast.dump(functions[name],include_attributes=False)).encode()).hexdigest()==expected, name
assignment={target.id:node for node in source.body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name)}
assert normalize_identity_dump(ast.literal_eval(assignment['APP_NAME'].value))==DATA['app_name']
assert ast.literal_eval(assignment['_WORD_COUNT_RE'].value.args[0])==DATA['word_regex']
orig=parse(DIR/'rtf_editor.py')
assert not any(isinstance(n,ast.FunctionDef) and n.name in DATA['helpers'] for n in orig.body)
assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('_WORD_COUNT_RE','APP_NAME') for t in n.targets) for n in orig.body)
print('PASS: x5.0 ten printing/properties methods, helper ASTs and all prior editor methods unchanged')
