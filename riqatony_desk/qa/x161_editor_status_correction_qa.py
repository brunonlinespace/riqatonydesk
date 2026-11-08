#!/usr/bin/env python3
"""Current correction: exactly two status labels, no other editor-source change."""
from pathlib import Path
import hashlib

OLD_BLOCK='        # Keep the persistent editor statistics geometrically stable.  Fixed\n        # fields reserve their longest supported display; the message field\n        # takes (and yields) all remaining horizontal space.  Word count is\n        # deliberately absent: rescanning the full document on every edit made\n        # multi-million-character RTF documents unnecessarily expensive.\n        self.operation_mode_label = QLabel("Insert", self.app_status_bar)\n        self.operation_mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        operation_width = self.operation_mode_label.fontMetrics().horizontalAdvance("Overwrite") + 4\n        self.operation_mode_label.setFixedWidth(operation_width)\n\n        self.zoom_label = QLabel("100%", self.app_status_bar)\n        zoom_width = self.zoom_label.fontMetrics().horizontalAdvance("300%") + 4\n        self.zoom_label.setFixedWidth(zoom_width)\n\n        self.counter_label = QLabel("Chars 0", self.app_status_bar)\n        maximum_counter_text = f"Chars {MAX_DOCUMENT_CHARACTERS:,}"\n        counter_width = self.counter_label.fontMetrics().horizontalAdvance(maximum_counter_text) + 4\n        self.counter_label.setFixedWidth(counter_width)\n\n        self.status_message_label = QLabel("", self.app_status_bar)\n        self.status_message_label.setMinimumWidth(0)\n        self.status_message_label.setSizePolicy(\n            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred\n        )\n        self.status_message_label.setToolTip("")\n\n        self._status_message_timer = QTimer(self)\n        self._status_message_timer.setSingleShot(True)\n        self._status_message_timer.timeout.connect(self._clear_status_message)\n\n        self.app_status_bar.addWidget(self.operation_mode_label)\n        self.app_status_bar.addWidget(self.counter_label)\n        self.app_status_bar.addWidget(self.zoom_label)\n        self.app_status_bar.addWidget(self.status_message_label, 1)'
NEW_BLOCK='        # The flexible message occupies the left; the complete editor indicator\n        # stays together at the right. No independent field-width reservations.\n        self.status_message_label = QLabel("", self.app_status_bar)\n        self.status_message_label.setMinimumWidth(0)\n        self.status_message_label.setSizePolicy(\n            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred\n        )\n        self.status_message_label.setToolTip("")\n        self.status_indicators_label = QLabel("Insert · Chars 0 · 100%", self.app_status_bar)\n        self.status_indicators_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)\n        self.status_indicators_label.setMinimumWidth(0)\n\n        self._status_message_timer = QTimer(self)\n        self._status_message_timer.setSingleShot(True)\n        self._status_message_timer.timeout.connect(self._clear_status_message)\n\n        self.app_status_bar.addWidget(self.status_message_label, 1)\n        self.app_status_bar.addPermanentWidget(self.status_indicators_label)'
OLD_COUNTS='        self.operation_mode_label.setText(\n            "Overwrite" if self.text_area.overwriteMode() else "Insert"\n        )\n        characters = max(0, self.text_area.document().characterCount() - 1)\n        self.zoom_label.setText(f"{self.zoom_percent}%")\n        self.counter_label.setText(f"Chars {characters:,}")'
NEW_COUNTS='        mode = "Overwrite" if self.text_area.overwriteMode() else "Insert"\n        characters = max(0, self.text_area.document().characterCount() - 1)\n        self.status_indicators_label.setText(\n            f"{mode} · Chars {characters:,} · {self.zoom_percent}%"\n        )'
BASELINE_SHA256='36a8093a9a6a2fc0c3fc760ef3936687a49aec260f83846a5766908922590a4b'
OLD_VERSION='1.0.0-x16.0'
NEW_VERSION='1.0.0-x16.1'

def restore_x160_status_source(source):
    assert source.count(NEW_BLOCK)==1 and source.count(NEW_COUNTS)==1, 'approved status code missing'
    restored=source.replace(NEW_BLOCK,OLD_BLOCK).replace(NEW_COUNTS,OLD_COUNTS)
    return restored

def verify_source(source):
    restored=restore_x160_status_source(source).replace(NEW_VERSION,OLD_VERSION)
    assert hashlib.sha256(restored.encode('utf-8')).hexdigest()==BASELINE_SHA256, 'other editor production changes detected'
    assert source.count('addWidget(self.status_message_label')==1, 'left message widget missing'
    assert source.count('addPermanentWidget(self.status_indicators_label)')==1, 'right permanent indicator missing'
    assert source.count('QLabel("Insert · Chars 0 · 100%"')==1, 'not consolidated to one indicator'
    assert 'Chars {characters:,}' in source, 'numerical grouping changed'
    assert '· {self.zoom_percent}%' in source, 'rightmost zoom missing'
    assert 'self.status_message_label.setToolTip(text)' in source, 'message tooltips changed'
    assert 'self._status_message_timer' in source, 'message timer missing'
    assert 'setFixedWidth(' not in source[source.index('self.status_message_label = QLabel(') if 'self.status_message_label = QLabel(' in source else source.index('self.status_message_label=QLabel('):source.index('self._status_message_timer')], 'obsolete fixed widths in status block'
    for obsolete in ('self.operation_mode_label', 'self.counter_label', 'self.zoom_label'):
        assert obsolete not in source, 'old status field survived: '+obsolete

if __name__=='__main__':
    package=Path(__file__).resolve().parents[1]
    editor=package/"widgets/rtf_editor.py"
    verify_source(editor.read_text(encoding='utf-8'))
    print('PASS: 1.0.0-x16.1 two-field editor correction and complete editor preservation')
