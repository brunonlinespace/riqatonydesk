#!/usr/bin/env python3
"""Qt-backed click regression for the actual embedded RiqatonyDesk editor actions."""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE.parent))
from PyQt6.QtWidgets import QApplication
from riqatony_desk.widgets.rtf_editor import RicopadEditorWidget

app = QApplication.instance() or QApplication(['riqatony-desk-x199-toggle-qa'])
with tempfile.TemporaryDirectory(prefix='riqatony-desk-find-toggle-') as config_dir:
    surface = RicopadEditorWidget(config_directory=config_dir)
    surface.show()
    app.processEvents()

    surface.search_bar_action.trigger()
    app.processEvents()
    assert surface.search_container.isVisible(), 'Find action failed to open the panel'
    surface.text_area.setFocus()
    app.processEvents()
    surface.search_bar_action.trigger()
    app.processEvents()
    assert not surface.search_container.isVisible(), 'Find action failed to close after focus loss'

    surface.replace_action.trigger()
    app.processEvents()
    assert surface.search_container.isVisible(), 'Find and Replace action failed to open'
    surface.text_area.setFocus()
    app.processEvents()
    surface.replace_action.trigger()
    app.processEvents()
    assert not surface.search_container.isVisible(), 'Find and Replace action failed to close after focus loss'

    surface.search_bar_action.trigger()
    app.processEvents()
    surface.replace_action.trigger()
    app.processEvents()
    assert surface.search_container.isVisible() and surface.replace_entry.hasFocus(), 'Find to Replace switch failed'
    surface.search_bar_action.trigger()
    app.processEvents()
    assert surface.search_container.isVisible() and surface.search_entry.hasFocus(), 'Replace to Find switch failed'
    surface.search_bar_action.trigger()
    app.processEvents()
    assert not surface.search_container.isVisible(), 'Repeated Find action failed to close'
    surface.close()
print('PASS x19.9: Qt-backed Find/Replace QAction click toggles, focus loss and mode switches')
