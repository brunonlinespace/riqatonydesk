#!/usr/bin/env python3
"""Static contract for converged Rico external-change safety."""
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
page = (PACKAGE / "widgets/editor_page.py").read_text(encoding="utf-8")
rtf = (PACKAGE / "widgets/rtf_editor.py").read_text(encoding="utf-8") + "\n" + (PACKAGE / "widgets/rwpyn/editor_lifecycle.py").read_text(encoding="utf-8")

required_page = (
    "self.repository.document_changed.connect(",
    "self._on_repository_document_changed",
    "def _on_repository_document_changed(self, changed: DocumentEntry) -> None:",
    "loaded_signature = self._surface.file_disk_signature",
    "disk_signature = self._current_disk_signature()",
    "self.external_banner.show()",
    'QPushButton("Reload from Disk", self.external_banner)',
    'QPushButton("Save Version As…", self.external_banner)',
    "def _has_external_change(self) -> bool:",
    "def _external_change_action(self) -> str:",
    "self._surface.external_change_action_provider = self._external_change_action",
    '"Save Version As…", QMessageBox.ButtonRole.ActionRole',
    '"Overwrite", QMessageBox.ButtonRole.DestructiveRole',
    'return "handled_success" if self._save_editor_version_as() else "cancel"',
    "def _save_editor_version_as(self) -> bool:",
    "forbidden_paths=(source_path,)",
    'dialog_title="Save Version As — RiqatonyDesk"',
    "external disk copy preserved",
)
missing = [fragment for fragment in required_page if fragment not in page]
if missing:
    raise SystemExit("EditorPage external-change contract missing: " + repr(missing))

# The persistent warning is independent of the optional file header.
build_start = page.index("    def _build_ui(self) -> None:")
build_end = page.index("    def _connect_signals(self) -> None:", build_start)
build = page[build_start:build_end]
if "root.addWidget(self.title_label)" not in build or "root.addWidget(self.external_banner)" not in build:
    raise SystemExit("External-change banner is not a separate EditorPage layout surface")
header_start = page.index("    def set_header_visible(self, visible: bool) -> None:")
header_end = page.index("    def set_status_visible", header_start)
if "external_banner" in page[header_start:header_end]:
    raise SystemExit("File-header visibility is incorrectly coupled to external-change warning")

# MainWindow's ordinary Save As route lands on EditorPage, which must convert an
# active conflict into protected Save Version As rather than calling generic Save As.
save_as_start = page.index("    def save_as_file(self) -> bool:")
save_as_end = page.index("    def refresh_editor_icons", save_as_start)
save_as_page = page[save_as_start:save_as_end]
for fragment in (
    "if self._has_external_change():",
    "return self._save_editor_version_as()",
):
    if fragment not in save_as_page:
        raise SystemExit(f"Managed Save As conflict protection missing: {fragment}")

# Embedded editor no longer owns the active Plus UX: it delegates to EditorPage.
for fragment in (
    "self.external_change_action_provider = None",
    'provider = getattr(self, "external_change_action_provider", None)',
    '"save_version_as"',
    '"handled_success"',
    "def _save_version_as(self):",
    "if not forbidden_paths and self._has_external_change():",
    "forbidden_paths=(source_path,)",
):
    if fragment not in rtf:
        raise SystemExit(f"Embedded editor conflict delegation/safety missing: {fragment}")

# The defensive component fallback must use Save Version As, never the stale
# generic Save As choice that could select the externally changed source.
external_start = rtf.index("    def _external_change_action(self):")
external_end = rtf.index("    def _has_external_change(self):", external_start)
external = rtf[external_start:external_end]
if '"Save As…"' in external or 'return "save_as"' in external:
    raise SystemExit("Stale generic Save As external-conflict route remains")
if '"Save Version As…"' not in external:
    raise SystemExit("Defensive conflict fallback lacks protected Save Version As")

# The unsafe old acknowledgement path must not return.
for forbidden in ("Keep My Version", "def _keep_editor_version", "self._surface.file_disk_signature = disk_signature"):
    if forbidden in page:
        raise SystemExit(f"Unsafe external-change preservation path remains: {forbidden}")

print("PASS: RiqatonyDesk converged external-change/save-as contract")
