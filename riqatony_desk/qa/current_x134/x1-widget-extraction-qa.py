#!/usr/bin/env python3
"""AST-parity and import-surface gate for x1.0, pinned to RiqatonyDesk 0.2.24."""
import ast, hashlib
from _identity_fingerprint import normalize_identity_dump
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'widgets/rwpyn/editor_widgets.py').read_text(encoding="utf-8")
original=(ROOT/'widgets/rtf_editor.py').read_text(encoding="utf-8")
classes={x.name:x for x in ast.parse(source).body if isinstance(x,ast.ClassDef)}
expected={'SafeTextDocument': '96fe6df2d82f637828d0de09e5f3e7281a6220beb0568e5e55b6ad5acf2ca71b', 'RichTextEdit': 'aa02a4398295adf033a84eb05c2063058a96e3a0bf06af7046cabb2567ae352f'}
for name,digest in expected.items():
    assert name in classes, f"{name} missing"
    actual=hashlib.sha256(normalize_identity_dump(ast.dump(classes[name],include_attributes=False)).encode()).hexdigest()
    assert actual==digest, f"{name} differs from original RiqatonyDesk 0.2.24 AST"
    assert not any(isinstance(n,ast.ClassDef) and n.name==name for n in ast.parse(original).body), f"duplicate {name} left in original host"
assert 'import' in original and 'editor_widgets' in original
assert 'from ' in source and 'sanitise_qt_html' in source
# All pre-existing host classes/functions outside the extracted widgets are untouched.
original_host_fingerprints={'read_bounded_bytes': '7fa6db18dd1161cc50c3488e31b71a57d286bff226a48d11e7b390fe12d97ffe', 'fsync_directory': 'f98dc002cf0a7480b7d1b46253d1e3c714de515c00abe275d7ab74f2cf09d6af', 'count_words': 'ee79820caeeabc599aa106fb6ff66f3e610dab9359ebe0df94227a33e4aaabbc', 'preference_bool': '84e1e50efff0ff186af497ff60bd89850896ded61f697444e5927b5488b615f8', 'preference_text': '8169dd60eb385ace8959ab3cf69099558ef7d79327f617838d6fe857aef83072', 'normalise_windows_organisation_directory': 'c1d5d59f943817432ecee2838639262e2b33f2d03fe9341ea94e8749c33423d1', 'platform_config_locations': 'ab5330ed1f018882ffc3a6a16b2bf28930a3a30378fe84c7332c9e0df438f371', 'configure_platform_identity': 'ff16238d0a66fe0614a296889b5c67d33b22c4da4ea423a2e1e44b2d16ed0cb0', 'host_process_environment': 'de1668c890fafe3c3afc96892bf67f63e131afde8ef14968135879f813c1d109', 'appimage_theme_resources': 'e48bace21edb2589d4ef0cba8302b2e4ed452c903740b5a33770fd6f9589d5f0', 'resource_path': '5e2019411260a3ba8f53ecfadf59901a4e9f202df3b1fa7a70d39af3b38f0a32', '_EmbeddedMenuRegistry': 'f4eae9782cf6ccb50ce530d1c48f5a3c442fb9c3198cf0a2c92cc98b7d214258', }
pref_nodes=ast.parse((ROOT/"widgets/rwpyn/editor_preferences.py").read_text(encoding='utf-8')).body
print_nodes=ast.parse((ROOT/"widgets/rwpyn/editor_printing.py").read_text(encoding="utf-8")).body
insertion_nodes=ast.parse((ROOT/'widgets/rwpyn/editor_insertion.py').read_text(encoding="utf-8")).body
host_nodes=ast.parse(original).body
host_fingerprints={n.name: hashlib.sha256(normalize_identity_dump(ast.dump(n,include_attributes=False)).encode()).hexdigest() for n in [*host_nodes,*insertion_nodes,*print_nodes,*pref_nodes] if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name not in ('RicopadEditorWidget','EditorInsertionMixin','EditorPrintingMixin','EditorPreferencesMixin')}
assert host_fingerprints==original_host_fingerprints, "host class/function AST changed outside x1.0 scope"
print('PASS: x1.0 widgets/host AST match unmodified baseline, imports preserved')
