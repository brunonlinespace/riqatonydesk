#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.19 bounded shortcut/highlight-label refinement gate."""
from pathlib import Path
import ast, hashlib
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding='utf-8')
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py'); rtf=src('widgets/rtf_editor.py'); readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "0.2.19"' in init,'0.2.19 package identity missing')
req('APP_REVISION = "0.2.19"' in constants,'0.2.19 revision identity missing')
req('Current release: **0.2.19**' in readme,'README current release stale')
# Highlight dialog: labels expose existing immediate-commit keys; formatting paths remain unchanged.
tree=ast.parse(rtf); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RicopadEditorWidget')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='choose_highlight_colour'); highlight=ast.get_source_segment(rtf,fn) or ''
for fragment in (
    '("Yellow", "#fff200", "Y")','("Pink", "#ff99cc", "P")','("Green", "#92d050", "G")','("Red", "#ff6666", "R")',
    '("Blue", "#5b9bd5", "B")','("Orange", "#f4b183", "O")','("Cyan", "#66ffff", "C")','("Noir", "#000000", "N")',
    'button=QPushButton(f"{name} ({key})",dialog)','clear_button=QPushButton("Clear Highlight (Backspace)",dialog)',
    'shortcut.triggered.connect(lambda _checked=False,value=hex_colour:choose(value))','clear_shortcut.triggered.connect(clear)',
    'chosen["colour"]=QColor(hex_colour); dialog.accept()','chosen["clear"]=True; dialog.accept()',
): req(fragment in highlight,f'highlight contract missing: {fragment}')
req('QPushButton(name,dialog)' not in highlight,'highlight labels do not expose keybinds')
# Theme remains the same action family but has no number shortcuts.
mtree=ast.parse(main); mcls=next(n for n in mtree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow')
mbuild=next(n for n in mcls.body if isinstance(n,ast.FunctionDef) and n.name=='_build_menu_bar'); build=ast.get_source_segment(main,mbuild) or ''
req('for value, label in (\n            ("light", "Light"),\n            ("dark", "Dark"),\n            ("system", "System"),' in build,'App Theme action family changed unexpectedly')
for key in ('Ctrl+Alt+Shift+1','Ctrl+Alt+Shift+2','Ctrl+Alt+Shift+3'):
    req(key not in build,f'App Theme still owns {key}')
req('"Toggle List/Grid View",\n            self._toggle_dashboard_view_mode,\n            "Ctrl+Alt+Shift+V",' in build,'List/Grid shortcut drifted from Ctrl+Alt+Shift+V')
colour_fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='choose_text_colour'); colour=ast.get_source_segment(rtf,colour_fn) or ''
req('Clear Colour' not in colour and 'clear_colour' not in colour,'Clear Colour was added despite explicit exclusion')
protected={
 'widgets/editor_page.py':'c5da44a5fbe8d8e493c31aaa1c996a33f6087db5cfbe9e409dbd59f6f68b2f74',
 'widgets/shell_ribbon.py':'38ce2f39ea63ec26cb16220268b8cbd337e73f417158a73886144338a2afa570',
 'controllers/file_actions.py':'3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569',
 'controllers/editor_manager.py':'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894',
 'services/open_document_monitor.py':'25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
 'services/filesystem_watcher.py':'655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
 'services/document_scanner.py':'8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
 'models/document_repository.py':'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f',
 'services/file_io.py':'96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55',
 'rtf_codec.py':'34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
 'rich_text_support.py':'6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb',
}
for path,h in protected.items(): req(sha(path)==h,f'protected out-of-scope file changed: {path}')
if errors:
    print('RiqatonyDesk 0.2.19 check failed:'); [print('- '+e) for e in errors]; raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.19 bounded shortcut/highlight-label refinement contract')
