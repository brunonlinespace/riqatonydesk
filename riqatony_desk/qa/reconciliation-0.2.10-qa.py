#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.10 Audit 4/5 gate."""
from __future__ import annotations
import hashlib
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src("__init__.py"); constants=src("app_constants.py"); actions=src("controllers/file_actions.py"); readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.10"' in init,"0.2.10 package identity missing")
req('APP_REVISION = "0.2.10"' in constants,"0.2.10 revision identity missing")
req('Current release: **0.2.10**' in readme,"README current release stale")
for fragment in ('self._prepare_open_editor(stored, operation="rename")','self._prepare_open_editor(stored, operation="remove")','page.handle_backing_path_event()','if page.backing_state == "normal":','if page.backing_state == "missing":','The RTF file changed outside RiqatonyDesk.','if page.document is not document:'):
    req(fragment in actions,f"Audit 4 contract missing: {fragment}")
for fragment in ('else ("current" if page is not None else "saved")','if page is not None and not dirty:','and choice == "current"','and (dirty or page.backing_state != "normal")','payload = page.current_rtf_payload()','payload, _snapshot = read_regular_file('):
    req(fragment in actions,f"Audit 5 contract missing: {fragment}")
for fragment in ('install_new_file_from_temp(temporary, destination)','dirty_duplicate_action','{"ask", "current", "saved"}'):
    req(fragment in actions,f"existing Duplicate contract changed: {fragment}")
protected={'widgets/editor_page.py': '22b504c3ab8d71e09002303998c69b3edea85a598403593e20adfe84e563bf0e', 'controllers/editor_manager.py': 'bbd6f696c4189fe62125270bd7bf6b743989bd865b578546c946e6107d330894', 'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999', 'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad', 'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123', 'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f', 'models/document_state_store.py': '732c432d7071c5944a8f0af75588835fee61f3bf5316b0f2c51d8f781e958fb0', 'services/file_io.py': '96a9f1b8c3f2c559401bcd6dca3cada7df0d043945e72164c5fa6e1494c58a55', 'widgets/main_window.py': '36997f762355cb6a53b0ffe402ad5cf9323130c83d8102d60ba7822d3dedd3d0', 'widgets/navigation.py': '60995adf7c41e2d8ef12a266a3d712b2b59cc5e8535a2e35d1ac2a6cfe468ce6', 'widgets/dashboard.py': 'ca3cb7c8acc4e21270369d15bb6797ed225602cf43f952c9d5aa63140adb3619', 'widgets/folder_dashboard.py': 'c245d1cb1928aee3671d81549c41687161478fa5a0f6f4c63d3bb1b1af61c70f', 'widgets/shell_ribbon.py': '15c1116863af945b3c2eea640e5f79b0d482817c13dd4f8f115c8f2a1259bbd1', 'widgets/rtf_editor.py': '8e45a1e7978487e2d960dae2d7659af75d73d9bf9f3556dd723b77becf578609', 'rtf_codec.py': '34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95', 'rich_text_support.py': '6c6d7152ad306788a72d420401a4563506e72150c389e80a61a5bdbc8d235fdb'}
for r,h in protected.items(): req(sha(r)==h,f"protected out-of-scope 0.2.9 file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.10 check failed:")
    [print(f"- {e}") for e in errors]; raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.10 Audit 4/5 Plus-family file-action convergence contract")
