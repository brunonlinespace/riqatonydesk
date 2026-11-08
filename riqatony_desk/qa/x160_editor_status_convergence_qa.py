#!/usr/bin/env python3
"""1.0.0-x16.0: exact four-field editor status order; no surrounding source modifications."""
from pathlib import Path
import hashlib, ast, json
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'widgets/rtf_editor.py'
src=APP.read_text(encoding='utf-8')
new_order='        self.app_status_bar.addWidget(self.operation_mode_label)\n        self.app_status_bar.addWidget(self.counter_label)\n        self.app_status_bar.addWidget(self.zoom_label)\n        self.app_status_bar.addWidget(self.status_message_label, 1)'
old_order='        self.app_status_bar.addWidget(self.operation_mode_label)\n        self.app_status_bar.addWidget(self.zoom_label)\n        self.app_status_bar.addWidget(self.counter_label)\n        self.app_status_bar.addWidget(self.status_message_label, 1)'
assert src.count(new_order)==1, 'approved status field ordering absent or duplicated'
assert old_order not in src, 'old status field order retained'
restored=src.replace(new_order,old_order).replace('1.0.0-x16.0','1.0.0-x15.3')
assert hashlib.sha256(restored.encode()).hexdigest()=='b4899c1f8a27f07c73bce9aa17f7ff966b769b17b5a098e46de707df841b228f', 'other changes to editor production code'
assert 'self.counter_label.setText(f"Chars {characters:,}")' in src, 'numeric grouping altered'
assert 'self.status_message_label.setToolTip(text)' in src, 'independent messages altered'
assert 'self.status_message_label.setMinimumWidth(0)' in src, 'message field sizing altered'
assert src.count('self.app_status_bar.addWidget(self.status_message_label')==1, 'message ownership changed'
assert src.index(new_order) < src.index('def update_status_counts('), 'unexpected status method relocation'
print('PASS: 1.0.0-x16.0 editor order, preserved formatting, message behavior and original editor source')
