#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.9 sidebar navigation rollback gate."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
main=src("widgets/main_window.py")
init=src("__init__.py")
constants=src("app_constants.py")
readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.9"' in init, "0.2.9 package identity missing")
req('APP_REVISION = "0.2.9"' in constants, "0.2.9 revision identity missing")
req('Current release: **0.2.9**' in readme, "README current release stale")
pattern=re.search(r'def _open_sidebar_document\(self, path\):.*?return page', main, re.S)
req(pattern is not None, "transactional sidebar wrapper missing")
if pattern:
    body=pattern.group(0)
    for fragment in (
        'page = self.editor_manager.open_document(path)',
        'if page is None:',
        'current = self.editor_manager.current_document',
        'if current is not None and not current.external:',
        'self.navigation.select_document(current.path)',
        'return page',
    ): req(fragment in body, f"sidebar rollback method incomplete: {fragment}")
req('self.navigation.document_requested.connect(self._open_sidebar_document)' in main, "sidebar request does not use transactional wrapper")
req('self.navigation.document_requested.connect(self.editor_manager.open_document)' not in main, "direct optimistic sidebar routing returned")
# This correction must not mutate the navigation widget, move engine, editor manager, search UI, or watcher/scanner core.
protected={
    'widgets/navigation.py': '60995adf7c41e2d8ef12a266a3d712b2b59cc5e8535a2e35d1ac2a6cfe468ce6',
    'controllers/editor_manager.py': 'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894',
    'controllers/file_actions.py': '600159f96519d10df52bd98cc4dee808b11cc0730ab903b2661d15ebc3fba387',
    'widgets/editor_page.py': '22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e',
    'widgets/rtf_editor.py': '8e45a1e7978487e2d960dae2d7659af75d73d9bf9f3556dd723b77becf578609',
    'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
    'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
    'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
    'rtf_codec.py': '34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
    'rich_text_support.py': '6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb',
}
for r,h in protected.items(): req(sha(r)==h, f"protected out-of-scope file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.9 check failed:")
    for e in errors: print(f"- {e}")
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.9 transactional sidebar navigation rollback contract")
