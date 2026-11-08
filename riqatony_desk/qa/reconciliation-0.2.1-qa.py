#!/usr/bin/env python3
"""Dependency-free RiqatonyDesk 0.2.1 tabs-lifecycle release gate."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import types
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
errors: list[str] = []


def req(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def src(relative: str) -> str:
    return (PACKAGE / relative).read_text(encoding="utf-8")


def sha(relative: str) -> str:
    return hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()


repo = src("models/document_repository.py")
manager = src("controllers/editor_manager.py")
page = src("widgets/editor_page.py")
monitor = src("services/open_document_monitor.py")
init = src("__init__.py")
constants = src("app_constants.py")


main = src("widgets/main_window.py")
dialog = src("widgets/resolve_open_documents_dialog.py")

for fragment in (
    "def prepare_tabs_disabled(self) -> bool:",
    "targets = [page for page in self._live_pages() if page is not anchor_page]",
    "Tabs Disabled keeps only the current document open.",
    "def _resolve_pages_before_close(self, pages: list[EditorPage], message: str) -> bool:",
    "ResolveOpenDocumentsDialog(at_risk, message, self.stack.window())",
    'if action == "save":',
    'if action == "discard":',
    'if action == "resolve":',
    "def _dispose_editor_page(self, page: EditorPage) -> bool:",
    "not self._tabs_enabled()",
    "and self.current_document.path != document.path",
    "Resolve the documents below before closing RiqatonyDesk.",
    "was_current = self.current_document is old_document or self.stack.currentWidget() is page",
):
    req(fragment in manager, f"0.2.1 document-lifecycle contract missing: {fragment}")

for fragment in (
    "if not enabled and current:",
    "if not self.editor_manager.prepare_tabs_disabled():",
    'self.config.set("tabs_enabled", enabled, save=True)',
):
    req(fragment in main, f"0.2.1 Tabs setting transition missing: {fragment}")
req(
    main.index("if not self.editor_manager.prepare_tabs_disabled():")
    < main.index('self.config.set("tabs_enabled", enabled, save=True)', main.index("def _set_tabs_enabled")),
    "Tabs Disabled is persisted before open documents are safely resolved",
)

for fragment in (
    'self.setWindowTitle("Resolve Open Documents")',
    'self.tree.setHeaderLabels(("Document", "State", "Action"))',
    'chooser.addItem("Save", "save")',
    'chooser.addItem("Discard", "discard")',
    'chooser.addItem("Resolve Individually…", "resolve")',
    'buttons.addButton("Save All"',
    'buttons.addButton("Discard All"',
):
    req(fragment in dialog, f"0.2.1 multi-document resolver missing: {fragment}")

for fragment in (
    "def backing_state(self) -> str:",
    "return self._backing_state",
):
    req(fragment in page, f"0.2.1 EditorPage resolver interface missing: {fragment}")

req(sha("services/open_document_monitor.py") == "25083834d8e85985d72c753e5cd929e40f54080ef5a6e7bcbdd7a38178da9999",
    "open-document monitor changed during 0.2.1")

req('APP_VERSION = "0.2.1"' in init, "0.2.1 package identity missing")
req('APP_REVISION = "0.2.1"' in constants, "0.2.1 revision identity missing")
req("if current is not None and current.loaded:" in repo, "loaded scan-retention rule missing")
req("Workspace discovery does not own the lifetime of a live editor" in repo, "retention rationale missing")

for fragment in (
    "class OpenDocumentMonitor(QObject):",
    "self._watcher = QFileSystemWatcher(self)",
    "self._paths_by_parent: dict[Path, set[Path]]",
    "self._pending_direct: set[Path]",
    "self._pending_parent: set[Path]",
    "info = os.stat(path, follow_symlinks=True)",
    "if path in direct or current != before:",
    "self.path_changed.emit(path)",
):
    req(fragment in monitor, f"shared monitor contract missing: {fragment}")
for forbidden in ("os.scandir(", ".iterdir(", ".rglob(", "request_rescan("):
    req(forbidden not in monitor, f"open-document monitor performs forbidden scanning: {forbidden}")
req(monitor.count("QFileSystemWatcher(self)") == 1, "monitor must own exactly one QFileSystemWatcher")

for fragment in (
    "self.open_document_monitor = OpenDocumentMonitor(self)",
    "self.open_document_monitor.register(document.path)",
    "self.open_document_monitor.rebind(old_path, target.path)",
    "self.open_document_monitor.unregister(closed_path)",
    "repository.document_path_changed.connect(self._on_managed_path_changed)",
    "for _path, state in tuple(self.states):",
    "page.handle_backing_path_event()",
    "if not document.external and not document.path.exists():",
):
    req(fragment in manager, f"EditorManager survival lifecycle missing: {fragment}")

for fragment in (
    'self._backing_state = "normal"',
    'if self._backing_state == "missing":',
    "def handle_backing_path_event(self) -> None:",
    'self._set_backing_state("missing")',
    'self.reload_external_button.setEnabled(False)',
    "This file is no longer available at its original disk path.",
    "def _confirm_close_missing_backing(self) -> bool:",
    '"Save Version As…"',
    '"Recreate Original…"',
    '"Close Without Saving"',
):
    req(fragment in page, f"EditorPage missing-backing contract missing: {fragment}")

# The ordinary workspace scanner is intentionally byte-for-byte unchanged from 0.1.8.
req(sha("services/filesystem_watcher.py") == "655301bed3b2af8d08d2181b8887a1bcdc266a9e789fed902852086d135028ad",
    "workspace filesystem watcher changed during 0.2.1")
req(sha("services/document_scanner.py") == "8cb947e9eb9404a64c1d90c0ff9fb7fcdc0bf6efee2e41be813f5bc41209d123",
    "workspace scanner changed during 0.2.1")

# Execute the pure repository retention rule without requiring PyQt6.
sys.path.insert(0, str(ROOT))
try:
    import PyQt6.QtCore  # noqa: F401
except ModuleNotFoundError:
    class _SignalInstance:
        def __init__(self): self._slots = []
        def connect(self, slot): self._slots.append(slot)
        def emit(self, *args):
            for slot in tuple(self._slots): slot(*args)
    class _SignalDescriptor:
        def __set_name__(self, owner, name): self._name = f"__qa_signal_{name}"
        def __get__(self, obj, owner):
            if obj is None: return self
            signal = getattr(obj, self._name, None)
            if signal is None:
                signal = _SignalInstance(); setattr(obj, self._name, signal)
            return signal
    class _QObject:
        def __init__(self, parent=None): self.parent = parent
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QObject = _QObject
    qtcore.pyqtSignal = lambda *_a, **_k: _SignalDescriptor()
    pyqt6 = types.ModuleType("PyQt6"); pyqt6.QtCore = qtcore
    sys.modules["PyQt6"] = pyqt6; sys.modules["PyQt6.QtCore"] = qtcore

from riqatony_desk.models.document import DocumentEntry
from riqatony_desk.models.document_repository import DocumentRepository

with tempfile.TemporaryDirectory(prefix="riqatonydesk-021-") as directory:
    path = Path(directory) / "survivor.rtf"
    path.write_bytes(b"{\\rtf1\\ansi survivor\\par}")
    info = path.stat()
    repository = DocumentRepository()
    document = repository.add(DocumentEntry(
        path=path, filename=path.name, display_name="Survivor", folder="",
        created=info.st_ctime, modified=info.st_mtime, size=info.st_size,
    ))
    document.loaded = True
    path.unlink()
    repository.replace_all([])
    req(repository.get(path) is document, "actual scan removed a loaded missing document")
    document.loaded = False
    repository.replace_all([])
    req(repository.get(path) is None, "closed missing document did not retire on discovery")

if errors:
    print("RiqatonyDesk 0.2.1 check failed:")
    for error in errors: print("- " + error)
    raise SystemExit(1)
print("PASS: RiqatonyDesk 0.2.1 tabs-lifecycle contract")
