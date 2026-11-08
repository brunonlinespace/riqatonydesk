#!/usr/bin/env python3
"""x15.0 adapter for frozen x13.5 historical MainWindow assertions.

Use the exact predecessor x14.0 MainWindow in-memory for edition-pinned historical
suites. Neither the old tests nor the active production file is rewritten.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import runpy
from unittest.mock import patch

QA=Path(__file__).resolve().parent
ROOT=QA.parent.parent
MAIN=(ROOT/'riqatony_desk/widgets/main_window.py').resolve()
REF=json.loads((QA/'x150-predecessor-fingerprints.json').read_text(encoding='utf-8'))['files']
BEFORE='''        # Hide the large main hierarchy while retaining the small dialog.
        self.editor_manager.dashboard.set_loading(False)
        self.navigation.set_loading(False)
'''
AFTER='''        # Hide the main hierarchy without rebuilding Dashboard cards on exit.
        # The Dashboard is not becoming interactive on a successful close.
        self.navigation.set_loading(False)
'''
ROLLBACK_BEFORE='''        if not scan_stopped:
            self._closing = False
            closing_dialog.close()
            self.centralWidget().show()
'''
ROLLBACK_AFTER='''        if not scan_stopped:
            self._closing = False
            closing_dialog.close()
            # Shutdown was cancelled: restore the normal, usable Dashboard.
            self.editor_manager.dashboard.set_loading(False)
            self.centralWidget().show()
'''

def main() -> int:
    raw_read=Path.read_text
    current=raw_read(MAIN,encoding='utf-8')
    assert current.count(AFTER)==1 and current.count(ROLLBACK_AFTER)==1
    old=current.replace(AFTER,BEFORE).replace(ROLLBACK_AFTER,ROLLBACK_BEFORE)
    assert hashlib.sha256(old.encode('utf-8')).hexdigest()==REF['riqatony_desk/widgets/main_window.py'], 'Cannot reconstruct x14.0 MainWindow'

    # Historical adapter sees only its original x14 MainWindow, and itself
    # reconstructs the exact x13.4 theme-import predecessor as it always did.
    def read_virtual(path: Path,*args,**kwargs):
        if path.resolve()==MAIN:
            return old
        return raw_read(path,*args,**kwargs)

    with patch.object(Path,'read_text',read_virtual):
        replay=runpy.run_path(str(QA/'x135-historical-contracts-qa.py'),run_name='_historic_x135')['replay']
        for name in ('x133-historical-file-rename-contracts-qa.py',
                     'x133-historical-layout-contracts-qa.py',
                     'x133-historical-help-contracts-qa.py'):
            replay(name)
            print('PASS historical replay:',name)
    print('PASS x15.0 current adapter: x13.5 historical source assertions unchanged')
    return 0

if __name__=='__main__':raise SystemExit(main())
