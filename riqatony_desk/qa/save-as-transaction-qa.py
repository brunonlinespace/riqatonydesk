#!/usr/bin/env python3
"""Dependency-free regression checks for RiqatonyDesk exp7 transactional Save As."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
rtf = (PACKAGE / "widgets" / "editor_lifecycle.py").read_text(encoding="utf-8")
page = (PACKAGE / "widgets" / "editor_page.py").read_text(encoding="utf-8")
manager = (PACKAGE / "controllers" / "editor_manager.py").read_text(encoding="utf-8")


def require(value, message):
    if not value:
        raise AssertionError(message)

require(
    "def _write_payload_atomically(self, payload, *, target_path=None):" in rtf,
    "atomic writer is not target-aware",
)
require(
    "destination = os.path.abspath(target_path or self.file_path)" in rtf,
    "atomic writer still depends only on the live file path",
)
require(
    "self._write_payload_atomically(payload, target_path=target_path)" in rtf,
    "Save As does not write the target independently",
)
require(
    "# Save As is a transaction: write the target while the current editor" in rtf,
    "transactional Save As contract is missing",
)
require(
    "previous=(self.file_path,self.file_disk_signature)" not in rtf,
    "legacy mutate-live-path-before-Save-As sequence remains",
)
save_as_start = rtf.index("    def save_as_file(")
save_as_end = len(rtf)
save_as_source = rtf[save_as_start:save_as_end]
require(
    "self.file_path=os.path.abspath(file_path)" not in save_as_source,
    "Save As still mutates the live path before the write",
)
write_pos = rtf.index("self._write_payload_atomically(payload, target_path=target_path)", save_as_start)
adopt_pos = rtf.index("self.file_path = target_path", write_pos)
emit_pos = rtf.index("self.file_path_changed.emit(old_path, target_path)", adopt_pos)
clean_pos = rtf.index("self._synchronise_after_save(", emit_pos)
require(write_pos < adopt_pos < emit_pos < clean_pos, "Save As transaction order regressed")

page_bind = manager.index("page.document = target")
old_clean = manager.index("self.repository.set_dirty(old_path, False)", page_bind)
require(page_bind < old_clean, "old document is notified clean before the page rebinds")
require(
    'if Path(surface_path).resolve(strict=False) != self.document.path.resolve(strict=False):' in page,
    "external-change watcher lacks the page/surface identity guard",
)
require(
    'self._set_backing_state("normal")' in page,
    "successful path rebind does not clear stale external-change UI",
)

print("PASS: exp7 transactional Save As source contract")
