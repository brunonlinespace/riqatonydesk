#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.11 Audit Item 6 gate."""
from __future__ import annotations
import hashlib
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src("__init__.py"); constants=src("app_constants.py"); actions=src("controllers/file_actions.py"); readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.11"' in init,"0.2.11 package identity missing")
req('APP_REVISION = "0.2.11"' in constants,"0.2.11 revision identity missing")
req('Current release: **0.2.11**' in readme,"README current release stale")
start=actions.index('    def remove_document('); end=actions.index('    def import_files(', start); remove=actions[start:end]
for fragment in ('self._prepare_open_editor(stored, operation="remove")','page = self._editor_page_for(stored)','if page is not None:','page.handle_backing_path_event()','Removed {stored.filename} from disk; open document retained','self.repository.remove(path)','self.document_removed.emit(stored)'):
    req(fragment in remove,f"Item 6 contract missing: {fragment}")
retain=remove.index('if page is not None:', remove.index('path.unlink()'))
repo=remove.index('self.repository.remove(path)')
req(retain < repo,"open-document retention branch must precede repository removal")
req('return True' in remove[retain:repo],"open-document retention branch must return before repository removal")
req('The open document will be retained so it can be saved' in remove,"Delete confirmation must disclose retained live document")
for fragment in ('if current is not None and current.loaded:','continue'):
    req(fragment in src('models/document_repository.py'),f"existing missing-loaded repository lifecycle changed: {fragment}")
for fragment in ('if self._backing_state == "missing":','Save Version As','Recreate Original','handle_backing_path_event'):
    req(fragment in src('widgets/editor_page.py'),f"existing missing-backing protection changed: {fragment}")
protected={'widgets/editor_page.py': '22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e', 'controllers/editor_manager.py': 'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894', 'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999', 'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad', 'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123', 'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f', 'models/document_state_store.py': '732c432d7071c5944a8f0af75588835fee61f3bf5316b0f2c51d8f781e958fb0', 'services/file_io.py': '96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55', 'widgets/main_window.py': '36997f762355cb6a53b0ffe402ad5cf9323130c83d8102d60ba7822d3dedd3d0', 'widgets/navigation.py': '60995adf7c41e2d8ef12a266a3d712b2b59cc5e8535a2e35d1ac2a6cfe468ce6', 'widgets/dashboard.py': 'ca3cb7c8acc4e21270369d15bb6797ed225602cf43f952c9d5aa63140adb3619', 'widgets/folder_dashboard.py': 'c245d1cb1928aee3671d81549c41687161478fa5a0f6f4c63d3bb1b1af61c70f', 'widgets/shell_ribbon.py': '15c1116863af945b3c2eea640e5f79b0d482817c13dd4f8f115c8f2a1259bbd1', 'widgets/rtf_editor.py': '8e45a1e7978487e2d960dae2d7659af75d73d9bf9f3556dd723b77becf578609', 'rtf_codec.py': '34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95', 'rich_text_support.py': '6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb'}
for r,h in protected.items(): req(sha(r)==h,f"protected out-of-scope 0.2.10 file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.11 check failed:")
    [print(f"- {e}") for e in errors]; raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.11 Audit Item 6 open-document Delete preservation contract")
