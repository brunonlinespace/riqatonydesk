#!/usr/bin/env python3
"""x12.0 editor folder convergence gate against frozen x11.2 implementation."""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path

PACKAGE=Path(__file__).resolve().parents[1]
REFERENCE=json.loads((PACKAGE/'qa/x12-preservation-reference.json').read_text(encoding='utf-8'))
MOVED=tuple(Path(path).name for path in REFERENCE['relocated'])
assert REFERENCE['baseline']=='1.0.0-x11.2' and REFERENCE['version']=='1.0.0-x12.0'
assert (PACKAGE/'widgets/rwpyn/__init__.py').is_file()
assert len(MOVED)==7
for file in MOVED:
    assert (PACKAGE/'widgets/rwpyn'/file).is_file(), f'missing relocated editor: {file}'
    assert not (PACKAGE/'widgets'/file).exists(), f'old editor copy remains: {file}'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for relative,expected in REFERENCE['protected_python_sha256'].items():
    assert digest(PACKAGE/relative)==expected, f'protected Desk source changed: {relative}'

from _identity_fingerprint import normalize_identity_dump

def normalised_ast(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    if tree.body and isinstance(tree.body[0],ast.Expr) and isinstance(tree.body[0].value,ast.Constant) and isinstance(tree.body[0].value.value,str):
        tree.body.pop(0)
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module:
            node.module=node.module.replace('riqatony_desk.widgets.rwpyn.','riqatony_desk.widgets.')
        if isinstance(node,ast.Constant) and node.value=='1.0.0-x12.0':
            node.value='1.0.0-x11.2'
        if isinstance(node,ast.FunctionDef) and node.name=='resource_path':
            assignment=next(n for n in node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='script_dir' for t in n.targets))
            desired=ast.parse('script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))').body[0]
            assert ast.dump(assignment,include_attributes=False)==ast.dump(desired,include_attributes=False),'resource resolver anchor changed outside agreed scope'
            node.body[node.body.index(assignment)]=ast.parse('script_dir = os.path.dirname(os.path.abspath(__file__))').body[0]
    return hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()

for old_location,expected in REFERENCE['editor_ast_sha256'].items():
    name=Path(old_location).name
    location=(PACKAGE/'widgets/rwpyn'/name) if name in MOVED else (PACKAGE/old_location)
    assert normalised_ast(location)==expected, f'editor AST diverged beyond approved migration: {name}'

# The relocated resource_path function must find the unchanged source RTF template.
source=PACKAGE/'widgets/rwpyn/editor_preferences.py'
fn=next(n for n in ast.parse(source.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='resource_path')
code=compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec')
scope={'os':os,'__file__':str(source)}
exec(code,scope)
expected=PACKAGE/'assets/templates/default-document.rtf'
assert expected.is_file()
assert Path(scope['resource_path']('templates','default-document.rtf')).resolve()==expected.resolve(), 'RTF default template fails after relocation'
# Dynamic-import target and the sole x12 resource-layout exception are checked above;
# no Qt imports are required for this source-preservation check.
print('PASS: x12.0 seven RTF editor modules relocated, historical AST intact, resource path and Desk scaffold preserved')
