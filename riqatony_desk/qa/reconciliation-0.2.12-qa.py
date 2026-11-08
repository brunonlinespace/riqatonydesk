#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.12 clean-load undo/redo regression gate."""
from __future__ import annotations
import hashlib
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src("__init__.py"); constants=src("app_constants.py"); editor=src("widgets/rtf_editor.py"); readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.12"' in init,"0.2.12 package identity missing")
req('APP_REVISION = "0.2.12"' in constants,"0.2.12 revision identity missing")
req('Current release: **0.2.12**' in readme,"README current release stale")
start=editor.index('    def load_file('); end=editor.index('    @staticmethod\n    def _default_created_file_mode',start); load=editor[start:end]
req('populate_qtextdocument_from_rtf_model(' in load,"direct RTF import path missing")
req('self.visual_editor.setHtml(document_html)' in load,"RTF fallback import path missing")
req('self.visual_editor.document().clearUndoRedoStacks()' in load,"successful RTF load must clear load-generated undo/redo history")
req('self.visual_editor.document().setModified(False)' in load,"successful RTF load must mark document clean")
req(load.index('clearUndoRedoStacks()') < load.index('setModified(False)'),"undo/redo history must be cleared before the document is marked clean")
# 0.2.12 deliberately changes only rtf_editor load history plus release/QA metadata.
protected={
 'controllers/file_actions.py':'3fb8a00cb482041edd5355b48200dd31d2ea2064a60d14250f05cc7fe12a9569',
 'widgets/editor_page.py':'22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e',
 'controllers/editor_manager.py':'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894',
 'services/open_document_monitor.py':'25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999',
 'services/filesystem_watcher.py':'655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
 'services/document_scanner.py':'8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123',
 'models/document_repository.py':'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f',
 'services/file_io.py':'96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55',
 'widgets/main_window.py':'36997f762355cb6a53b0ffe402ad5cf9323130c83d8102d60ba7822d3dedd3d0',
 'widgets/navigation.py':'60995adf7c41e2d8ef12a266a3d712b2b59cc5e8535a2e35d1ac2a6cfe468ce6',
 'rtf_codec.py':'34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
 'rich_text_support.py':'6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb',
}
for r,h in protected.items(): req(sha(r)==h,f"protected out-of-scope 0.2.11 file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.12 check failed:")
    [print(f"- {e}") for e in errors]; raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.12 clean-load undo/redo history contract")
