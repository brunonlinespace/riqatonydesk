#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.4 App Sidebar release gate."""
from __future__ import annotations
import hashlib, struct
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
ROOT=PACKAGE.parent
errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding="utf-8")
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
def png_size(p):
    d=p.read_bytes(); return struct.unpack(">II", d[16:24]) if d[:8]==b"\x89PNG\r\n\x1a\n" else (0,0)
main=src("widgets/main_window.py")
manager=src("controllers/editor_manager.py")
config=src("services/config_service.py")
init=src("__init__.py")
constants=src("app_constants.py")
readme=(ROOT/"README.md").read_text(encoding="utf-8")
req('APP_VERSION = "0.2.4"' in init, "0.2.4 package identity missing")
req('APP_REVISION = "0.2.4"' in constants, "0.2.4 revision identity missing")
req('"sidebar_position": "left"' in config, "left sidebar default missing")
for frag in ('addMenu("App Sidebar")','("left", "Left Sidebar")','("right", "Right Sidebar")','def _set_sidebar_position(','self.splitter.insertWidget(target_index, self.navigation)','def _logical_splitter_sizes(','"left_sidebar_action":"show-sidebar"','"right_sidebar_action":"show-sidebar-right"'):
    req(frag in main, f"sidebar contract missing: {frag}")
req(main.index('addMenu("App Dashboard")') < main.index('addMenu("App Sidebar")') < main.index('addMenu("App Launch Screen")'), "App Sidebar is not directly after App Dashboard")
req(manager.count('open_document(document, view_only=False)') >= 2, "Dashboard/Folder Dashboard Open does not explicitly unlock")
req(manager.count('open_document(document, view_only=True)') >= 2, "View Only explicit lock contract changed")
for family in ('ribbon-icons','ribbon-icons-classic','ribbon-icons-original'):
    for scheme in ('light','dark'):
        for name in ('show-sidebar','show-sidebar-right'):
            path=PACKAGE/'assets'/family/scheme/(name+'.png')
            req(path.is_file(), f"missing {family}/{scheme}/{name}.png")
            if path.is_file(): req(png_size(path)==(64,64), f"wrong PNG size: {path}")
req('PNG_ONLY_INTERIM = {"show-sidebar-right"}' in src('qa/iconset-qa.py'), "temporary PNG-only sidebar-right allowance missing")
req('Current release: **0.2.4**' in readme, "root README current release is stale")
protected={'widgets/dashboard_card.py': 'f077cc621e797847435f84de793b685395bdfb2d70a0d1b5229814d4e27bea9e', 'services/open_document_monitor.py': '25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999', 'services/filesystem_watcher.py': '655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad', 'services/document_scanner.py': '8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123', 'widgets/editor_page.py': '6de5e5858f41813f87ce1591bb3966dc797873e2228e284be119a40395d937b2', 'models/document_repository.py': 'e4ed283d92a00ca6b4803b806c76a2f5e9583ef88cf23ef4d64a17a6c2b8fc2f', 'widgets/resolve_open_documents_dialog.py': '38657cbfaf21ab286cb58dc2cd8fac43b2b562d270629d98276274d68c17047e', 'widgets/shell_ribbon.py': '4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993'}
for r,h in protected.items(): req(sha(r)==h, f"protected out-of-scope file changed: {r}")
if errors:
    print("RiqatonyDesk 0.2.4 check failed:")
    [print("- "+e) for e in errors]
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.4 App Sidebar contract")
