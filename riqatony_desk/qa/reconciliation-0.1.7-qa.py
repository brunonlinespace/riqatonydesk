#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.1.7 managed tree-drop hotfix gate."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]; ROOT=PACKAGE.parent; errors=[]
def req(c,m):
    if not c: errors.append(m)
def src(r): return (PACKAGE/r).read_text(encoding='utf-8')
def sha(r): return hashlib.sha256((PACKAGE/r).read_bytes()).hexdigest()
init=src('__init__.py'); const=src('app_constants.py'); nav=src('widgets/navigation.py')
component=json.loads((ROOT/'suite-pythoine-component.json').read_text()); manifest=json.loads((PACKAGE/'riqatonydesk.json').read_text())
resolver=nav.split('    def _external_drop_destination',1)[1].split('    def dragMoveEvent',1)[0]
for f in ('if item is None:','return Path(self.parent().library_root).resolve(strict=False)','if kind == self.KIND_FOLDER:','return path','if kind == "document":','return path.parent'):
    req(f in resolver,f'destination rule missing: {f}')
move=nav.split('    def dragMoveEvent',1)[1].split('    def dropEvent',1)[0]
req('event.mimeData().hasFormat(self.MIME_TYPE)' in move,'managed MIME drag acceptance missing')
req('self._external_drop_destination(item) is not None' in move,'managed drag does not accept explicit file/root destinations')
drop=nav.split('    def dropEvent',1)[1].split('\n\nclass DashboardNavigationButton',1)[0]
req('destination = self._external_drop_destination(item)' in drop,'managed drop does not resolve file/root destination')
req('source_parent == target_folder' in drop and 'samefile(target_folder)' in drop,'same-folder no-op guard changed')
req('self.document_move_dropped.emit(src, dst)' in drop,'managed move signal changed')
expected={
'controllers/file_actions.py':'a0a8e5e0ee4ab4f4df612e42f22c68b14bb167c1141eecb2bedd63fc26d2dbbd',
'models/document_repository.py':'e7e1829d7ee5d71644e5cffdb6fe98b533e44d44b6fe3e4436ad8179e83e6247',
'services/filesystem_watcher.py':'655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad',
'widgets/folder_dashboard.py':'66cda277e6113251540f72ba8842b7e9a03ca6fe893e3a921085890f19360b0a',
'widgets/shell_ribbon.py':'4945541ad7bd6f55f159cc1ecde50f7ee4858bf5bf3d14f50eb907cbd470f993',
'rtf_codec.py':'34be3a47a0d6fe73d092253508d6c165c883523931af0008cb95ff2c1c336c95',
}
for r,h in expected.items(): req(sha(r)==h,f'protected 0.1.6 implementation changed: {r}')
if errors:
    print('RiqatonyDesk 0.1.7 check failed:'); [print('- '+e) for e in errors]; raise SystemExit(1)
print('PASS: RiqatonyDesk 0.1.7 managed tree-drop hotfix contract')
