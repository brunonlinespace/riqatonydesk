#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.18 bounded interaction/shortcut gate."""
from pathlib import Path
import ast, hashlib
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding='utf-8')
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src('__init__.py'); constants=src('app_constants.py'); main=src('widgets/main_window.py'); rtf=src('widgets/rtf_editor.py'); readme=(ROOT/'README.md').read_text(encoding='utf-8')
req('APP_VERSION = "0.2.18"' in init,'0.2.18 package identity missing')
req('APP_REVISION = "0.2.18"' in constants,'0.2.18 revision identity missing')
req('Current release: **0.2.18**' in readme,'README current release stale')
# Highlight dialog must use the existing immediate-commit choose/clear paths.
tree=ast.parse(rtf); cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RicopadEditorWidget')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='choose_highlight_colour'); highlight=ast.get_source_segment(rtf,fn) or ''
for fragment in (
    '("Yellow", "#fff200", "Y")','("Pink", "#ff99cc", "P")','("Green", "#92d050", "G")','("Red", "#ff6666", "R")',
    '("Blue", "#5b9bd5", "B")','("Orange", "#f4b183", "O")','("Cyan", "#66ffff", "C")','("Noir", "#000000", "N")',
    'shortcut.setShortcut(QKeySequence(key))','shortcut.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)',
    'shortcut.triggered.connect(lambda _checked=False,value=hex_colour:choose(value))','clear_shortcut.setShortcut(QKeySequence("Backspace"))',
    'clear_shortcut.triggered.connect(clear)','chosen["colour"]=QColor(hex_colour); dialog.accept()','chosen["clear"]=True; dialog.accept()',
): req(fragment in highlight,f'highlight interaction missing: {fragment}')
req('("Black", "#000000"' not in highlight,'highlight Black label remains')
# MainWindow shortcut ownership.
for value,label,key in (
    ('light','Light','Ctrl+Alt+Shift+1'),('dark','Dark','Ctrl+Alt+Shift+2'),('system','System','Ctrl+Alt+Shift+3'),
): req(f'("{value}", "{label}", "{key}")' in main,f'App Theme shortcut missing: {key}')
req('"Toggle List/Grid View",\n            self._toggle_dashboard_view_mode,\n            "Ctrl+Alt+Shift+V",' in main,'List/Grid shortcut is not Ctrl+Alt+Shift+V')
req('"Toggle List/Grid View",\n            self._toggle_dashboard_view_mode,\n            "Ctrl+Alt+Shift+D",' not in main,'old List/Grid Ctrl+Alt+Shift+D remains')
# Explicitly excluded Clear Colour.
colour_fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='choose_text_colour'); colour=ast.get_source_segment(rtf,colour_fn) or ''
req('Clear Colour' not in colour and 'clear_colour' not in colour,'Clear Colour was added despite explicit exclusion')
# Protect all unrelated architecture/lifecycle/editor-support files exactly at 0.2.17.
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
for r,h in protected.items(): req(sha(r)==h,f'protected out-of-scope file changed: {r}')
if errors:
    print('RiqatonyDesk 0.2.18 check failed:'); [print('- '+e) for e in errors]; raise SystemExit(1)
print('PASS: RiqatonyDesk 0.2.18 bounded interaction/shortcut contract')
