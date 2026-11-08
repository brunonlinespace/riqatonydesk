#!/usr/bin/env python3
"""x4.0 editor Find/Replace and view extraction: exact frozen x3.0 AST parity."""
import ast, hashlib, json
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASELINE=json.loads((ROOT/'qa/x4-method-fingerprints.json').read_text(encoding='utf-8'))
DIR=ROOT/'widgets'
parse=lambda path:ast.parse(path.read_text(encoding='utf-8'))
cls=lambda path,name:next(node for node in parse(path).body if isinstance(node,ast.ClassDef) and node.name==name)
classes=[
 cls(DIR/'rtf_editor.py','RicopadEditorWidget'),
 cls(DIR/'editor_commands_appearance.py','EditorCommandsAppearanceMixin'),
 cls(DIR/'editor_search_view.py','EditorSearchViewMixin'),
 cls(DIR/'editor_formatting.py','EditorFormattingMixin'),
 cls(DIR/'editor_insertion.py','EditorInsertionMixin'),
 cls(DIR/'editor_printing.py','EditorPrintingMixin'),
 cls(DIR/'editor_preferences.py','EditorPreferencesMixin'),
 cls(DIR/'editor_lifecycle.py','EditorFileLifecycleMixin'),
]
assert [ast.unparse(n) for n in classes[0].bases]==['EditorFileLifecycleMixin','EditorCommandsAppearanceMixin','EditorPreferencesMixin','EditorPrintingMixin', 'EditorSearchViewMixin','EditorFormattingMixin','EditorInsertionMixin','QWidget']
methods=[]
for c in classes:
    methods.extend(n for n in c.body if isinstance(n,ast.FunctionDef))
assert len(methods)==len({n.name for n in methods}), 'duplicate method ownership'
actual={n.name:hashlib.sha256(normalize_identity_dump(ast.dump(n,include_attributes=False)).encode()).hexdigest() for n in methods}
assert actual==BASELINE['methods'], 'editor methods changed, added or lost during extraction'
assert {n.name for n in classes[2].body if isinstance(n,ast.FunctionDef)}==set(BASELINE['moved']), 'wrong search/view move'
assert not ({n.name for n in classes[0].body if isinstance(n,ast.FunctionDef)}&set(BASELINE['moved'])), 'moved method remains in host'
search=parse(DIR/'editor_search_view.py')
assign=next(n for n in search.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MAX_SEARCH_MATCHES' for t in n.targets))
assert ast.literal_eval(assign.value)==BASELINE['search_limit']
assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MAX_SEARCH_MATCHES' for t in n.targets) for n in parse(DIR/'rtf_editor.py').body)
print('PASS: x4.0 40 search/view methods AST-unchanged, all editor methods retained')
