#!/usr/bin/env python3
"""Replay edition-pinned x13.3 QA against exact x13.4 MainWindow imports.

Historical QA files are never edited. This test reconstructs the predecessor
source as a virtual Path.read_text response, so their assertions remain intact.
"""
from __future__ import annotations

import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

QA = Path(__file__).resolve().parent
PACKAGE = QA.parent
SOURCE = PACKAGE.parent
REF = json.loads((QA / 'x135-theme-predecessor.json').read_text(encoding='utf-8'))
TESTS = (
    'x133-historical-file-rename-contracts-qa.py',
    'x133-historical-layout-contracts-qa.py',
    'x133-historical-help-contracts-qa.py',
)
MAIN = (PACKAGE / 'widgets/main_window.py').resolve()
OLD_THEME = (PACKAGE / 'widgets/rico_theme.py').resolve()
NEW_THEME = (PACKAGE / 'widgets/theme.py').resolve()
OLD = 'from riqatony_desk.widgets.rico_theme import apply_theme, effective_scheme'
NEW = 'from riqatony_desk.widgets.theme import apply_theme, effective_scheme'


def replay(name: str) -> None:
    if name not in TESTS:
        raise ValueError('Unexpected historical QA name: '+name)
    current = MAIN.read_text(encoding='utf-8')
    assert current.count(NEW) == 1 and OLD not in current, 'Changed import contract'
    original = current.replace(NEW, OLD)
    assert hashlib.sha256(original.encode('utf-8')).hexdigest() == REF['previous_sha256_by_path']['riqatony_desk/widgets/main_window.py'], 'Predecessor MainWindow changed'
    raw_read = Path.read_text

    def virtual_read(path: Path, *args, **kwargs):
        if path.resolve() == MAIN:
            return original
        if path.resolve() == OLD_THEME:
            assert hashlib.sha256(NEW_THEME.read_bytes()).hexdigest() == REF['old_theme_sha256'], 'Theme bytes changed'
            return raw_read(NEW_THEME, *args, **kwargs)
        return raw_read(path, *args, **kwargs)

    with patch.object(Path, 'read_text', virtual_read):
        runpy.run_path(str(QA / name), run_name='__main__')


def main() -> int:
    if len(sys.argv)==3 and sys.argv[1]=='--single':
        replay(sys.argv[2]);return 0
    if len(sys.argv)!=1:
        print('Expected [--single HISTORICAL_TEST]',file=sys.stderr);return 2
    for name in TESTS:
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--single',name],
            cwd=SOURCE,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},
            text=True,capture_output=True,timeout=30,check=False)
        if result.returncode:
            print('FAIL historical QA '+name+': '+(result.stderr or result.stdout));return 1
        print(result.stdout.strip())
    print('PASS x13.5: three unmodified historical suites replayed against exact x13.4 import structure')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
