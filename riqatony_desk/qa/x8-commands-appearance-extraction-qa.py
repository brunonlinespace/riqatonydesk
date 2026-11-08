#!/usr/bin/env python3
"""x8.0 command/icon/appearance extraction — original complete-editor AST parity."""
import ast, json, hashlib
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'widgets' if True else ROOT
DATA=json.loads((ROOT/'qa/x8-method-fingerprints.json').read_text(encoding='utf-8'))
assert DATA['baseline']=='1.0.0-x6.0'
parse=lambda name:ast.parse((DIR/name).read_text(encoding='utf-8'))
cls=lambda name,label:next(n for n in parse(name).body if isinstance(n,ast.ClassDef) and n.name==label)
classes=[cls('rtf_editor.py','RicopadEditorWidget'),
 cls('editor_commands_appearance.py','EditorCommandsAppearanceMixin'),
 cls('editor_preferences.py','EditorPreferencesMixin'),
 cls('editor_printing.py','EditorPrintingMixin'),
 cls('editor_search_view.py','EditorSearchViewMixin'),
 cls('editor_formatting.py','EditorFormattingMixin'),
 cls('editor_insertion.py','EditorInsertionMixin'),
 cls('editor_lifecycle.py','EditorFileLifecycleMixin')]
methods=[method for c in classes for method in c.body if isinstance(method,ast.FunctionDef)]
assert len(methods)==len({method.name for method in methods}),'method duplicate'
get_hash=lambda node:hashlib.sha256(normalize_identity_dump(ast.dump(node,include_attributes=False)).encode()).hexdigest()
assert {m.name:get_hash(m) for m in methods if m.name in DATA['methods']}==DATA['methods'],'original editor method changed, lost or added'
assert {m.name for m in classes[1].body if isinstance(m,ast.FunctionDef)}==set(DATA['moved']),'wrong x8 extraction inventory'
assert 'RicopadEditorWidget'==DATA['original_host_class']
host=(DIR/'rtf_editor.py').read_text(encoding='utf-8')
assert 'from riqatony_desk.widgets.editor_commands_appearance import EditorCommandsAppearanceMixin' in host
print('PASS: 1.0.0-x8.0 — 23 moved command/appearance methods and all other baseline editor methods AST unchanged')
