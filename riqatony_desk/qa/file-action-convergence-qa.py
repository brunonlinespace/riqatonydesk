#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk dirty file-action convergence gate."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
controller = (PACKAGE / "controllers" / "file_actions.py").read_text(encoding="utf-8")
page = (PACKAGE / "widgets" / "editor_page.py").read_text(encoding="utf-8")
window = (PACKAGE / "widgets" / "main_window.py").read_text(encoding="utf-8")
config = (PACKAGE / "services" / "config_service.py").read_text(encoding="utf-8")

# Persistent policy defaults match Ricopad 1.0.0.
assert '"dirty_duplicate_action": "ask"' in config
assert '"dirty_external_action": "ask"' in config

# Active Plus duplicate flow distinguishes the in-memory document from disk.
assert '"Duplicate Current Document"' in controller
assert '"Duplicate Last Saved Version"' in controller
assert 'QCheckBox("Remember this choice"' in controller
assert 'self._set_file_policy("dirty_duplicate_action", choice)' in controller
assert 'payload = page.current_rtf_payload()' in controller
assert 'read_regular_file(' in controller
assert 'install_new_file_from_temp(temporary, destination)' in controller
assert 'if path_lexists(destination):' in controller

# The editor page exposes serialization without saving/rebinding the current file.
assert 'def current_rtf_payload(self) -> bytes:' in page
assert 'payload = self._surface._document_payload("rtf")' in page

# External editor makes the dirty choice explicit and uses the protected Save path.
assert '"Save Changes and Open"' in controller
assert '"Open Last Saved Version"' in controller
assert 'self._set_file_policy("dirty_external_action", choice)' in controller
assert 'if page is None or not page.save_to_disk():' in controller
assert 'target = page.document.path' in controller

# Both remembered choices remain user-visible and resettable in Settings.
assert '"Duplicate File with Unsaved Changes"' in window
assert '"Open Externally with Unsaved Changes"' in window
assert '"Ask Every Time"' in window
assert 'self.file_actions.file_policy_changed.connect(self._on_file_policy_changed)' in window

# Managed editor actions still route upward; dormant standalone helpers are not authority.
embedded = (PACKAGE / "widgets" / "rtf_editor.py").read_text(encoding="utf-8")
embedded += '\n' + (PACKAGE / 'widgets' / 'editor_commands_appearance.py').read_text(encoding='utf-8')
assert 'self.external_editor_requested.emit' in embedded
assert 'self.duplicate_requested.emit' in embedded

print("PASS: RiqatonyDesk dirty Duplicate/External Editor file-action convergence")
