#!/usr/bin/env python3
"""x2.0 formatting-only extraction parity versus the frozen x1.0 method ASTs."""
import ast, json, hashlib
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
root=Path(__file__).resolve().parents[1]
original=ast.parse((root/'widgets/rtf_editor.py').read_text(encoding='utf-8'))
formatter=ast.parse((root/'widgets/rwpyn/editor_formatting.py').read_text(encoding='utf-8'))
host=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='RicopadEditorWidget')
mixin=next(n for n in formatter.body if isinstance(n,ast.ClassDef) and n.name=='EditorFormattingMixin')
assert [ast.unparse(n) for n in host.bases]==['EditorFileLifecycleMixin','EditorCommandsAppearanceMixin','EditorPreferencesMixin','EditorPrintingMixin', 'EditorSearchViewMixin', 'EditorFormattingMixin', 'EditorInsertionMixin', 'QWidget']
original_methods={n.name:n for n in host.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
extracted_methods={n.name:n for n in mixin.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
insertion=ast.parse((root/'widgets/rwpyn/editor_insertion.py').read_text(encoding='utf-8'))
insertion_mixin=next(n for n in insertion.body if isinstance(n,ast.ClassDef) and n.name=='EditorInsertionMixin')
insertion_methods={n.name:n for n in insertion_mixin.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
search=ast.parse((root/('widgets/rwpyn/editor_search_view.py' if 'widgets' in str(root/'widgets/rwpyn/editor_search_view.py') and (root/'widgets/rwpyn/editor_search_view.py').exists() else 'editor_search_view.py')).read_text(encoding='utf-8'))
search_mixin=next(n for n in search.body if isinstance(n,ast.ClassDef) and n.name=='EditorSearchViewMixin')
search_methods={n.name:n for n in search_mixin.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert not (set(search_methods) & (set(original_methods) | set(extracted_methods) | set(insertion_methods))), 'duplicate search/view methods'
printing=ast.parse((root/'widgets/rwpyn/editor_printing.py').read_text(encoding='utf-8'))
printing_mixin=next(n for n in printing.body if isinstance(n,ast.ClassDef) and n.name=='EditorPrintingMixin')
printing_methods={n.name:n for n in printing_mixin.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert not (set(printing_methods) & (set(original_methods) | set(extracted_methods) | set(insertion_methods) | set(search_methods))), 'duplicate printing methods'
assert len(extracted_methods)==43,len(extracted_methods)
assert not set(original_methods)&set(extracted_methods),'method still duplicated in host'
assert not ((set(original_methods)|set(extracted_methods))&set(insertion_methods)), 'method duplicated in insertion mixin'
pref_tree=ast.parse((__import__('pathlib').Path(__file__).resolve().parents[1]/"widgets/rwpyn/editor_preferences.py").read_text(encoding='utf-8'))
pref_cls=next(n for n in pref_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorPreferencesMixin')
pref_methods={n.name:n for n in pref_cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert not (set(pref_methods)&(set(original_methods)|set(extracted_methods)|set(insertion_methods)|set(search_methods)|set(printing_methods)))
command_tree=ast.parse((root/'widgets/editor_commands_appearance.py').read_text(encoding='utf-8'))
command_cls=next(n for n in command_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorCommandsAppearanceMixin')
command_methods={n.name:n for n in command_cls.body if isinstance(n,ast.FunctionDef)}
assert not set(command_methods) & (set(original_methods)|set(extracted_methods)|set(insertion_methods)|set(search_methods)|set(printing_methods)|set(pref_methods))
expected=json.loads((root/'qa/x2-method-fingerprints.json').read_text(encoding='utf-8'))['methods']
lifecycle_tree=ast.parse((root/'widgets/rwpyn/editor_lifecycle.py').read_text(encoding='utf-8'))
lifecycle_cls=next(n for n in lifecycle_tree.body if isinstance(n,ast.ClassDef) and n.name=='EditorFileLifecycleMixin')
lifecycle_methods={n.name:n for n in lifecycle_cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
actual={name:hashlib.sha256(normalize_identity_dump(ast.dump(node,include_attributes=False)).encode()).hexdigest() for name,node in {**original_methods,**extracted_methods,**insertion_methods,**search_methods,**printing_methods,**pref_methods,**command_methods,**lifecycle_methods}.items()}
assert actual==expected, 'method AST changed, disappeared or was added during extraction'
assert ast.unparse(next(n for n in formatter.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FONT_SIZE_STEPS' for t in n.targets)).value)==ast.unparse(ast.parse("(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 36, 40, 44, 48, 54, 60, 66, 72, 80, 88, 96, 108, 120, 144, 168, 192, 216, 240, 288, 320, 384, 448, 512)",mode='eval').body)
assert len([n for n in original.body if isinstance(n,ast.ImportFrom) and any(k.name=='EditorFormattingMixin' for k in n.names)])==1
print('PASS: x2.0 43-method AST parity, preserved RicopadEditorWidget host interface')
