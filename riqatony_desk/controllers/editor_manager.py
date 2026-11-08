# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
"""Coordinates dashboard, folder dashboards, and lazy editor pages."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QDialog, QWidget

from riqatony_desk.models.document import DocumentEntry
from riqatony_desk.models.workspace_folder import WorkspaceFolder
from riqatony_desk.services.open_document_monitor import OpenDocumentMonitor
from riqatony_desk.widgets.workspace.dashboard import DashboardWidget
from riqatony_desk.widgets.editor_page import EditorPage
from riqatony_desk.widgets.workspace.folder_dashboard import FolderDashboard
from riqatony_desk.widgets.dialogs.resolve_open_documents_dialog import ResolveOpenDocumentsDialog


class EditorManager(QObject):
    current_document_changed = pyqtSignal(object)
    current_folder_changed = pyqtSignal(object)
    dashboard_shown = pyqtSignal()
    status_message = pyqtSignal(str)
    external_editor_requested = pyqtSignal(object)
    containing_folder_requested = pyqtSignal(object)
    rename_requested = pyqtSignal(object)
    remove_requested = pyqtSignal(object)
    duplicate_requested = pyqtSignal(object)
    editor_history_changed = pyqtSignal(bool, bool)
    editor_formatting_changed = pyqtSignal()
    editor_preferences_changed = pyqtSignal()
    folder_open_external_requested = pyqtSignal(object)
    folder_rename_requested = pyqtSignal(object)
    folder_remove_requested = pyqtSignal(object)
    create_file_requested = pyqtSignal(object)
    create_folder_requested = pyqtSignal(object)
    external_files_import_requested = pyqtSignal(object, object)
    editor_files_dropped = pyqtSignal(object, object)
    refresh_requested = pyqtSignal()
    sort_mode_changed = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)
    workspace_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    save_and_new_requested = pyqtSignal(object)
    save_and_dashboard_requested = pyqtSignal(object)
    save_and_exit_requested = pyqtSignal(object)
    document_path_rebound = pyqtSignal(object, object)
    document_closed = pyqtSignal(object)
    documents_reset = pyqtSignal()

    def __init__(self, library_root, repository, states, stack, config, parent=None) -> None:
        super().__init__(parent)
        self.library_root = Path(library_root).expanduser().resolve(strict=False)
        self.repository = repository
        self.states = states
        self.stack = stack
        self.config = config
        self.open_document_monitor = OpenDocumentMonitor(self)
        self.open_document_monitor.path_changed.connect(
            self._on_open_backing_path_changed
        )
        self.current_document: DocumentEntry | None = None
        self.current_folder: Path | None = None
        self._folder_pages: dict[Path, FolderDashboard] = {}
        self.dashboard = DashboardWidget(repository, states, stack)
        self.stack.addWidget(self.dashboard)
        self._connect_dashboard()
        states.state_removed.connect(self._on_state_removed)
        repository.document_path_changed.connect(self._on_managed_path_changed)
        repository.repository_reset.connect(self._on_repository_reset)
        self.show_dashboard()

    def _connect_dashboard(self) -> None:
        self.dashboard.document_open_requested.connect(
            lambda document: self.open_document(document, view_only=False)
        )
        self.dashboard.document_view_only_requested.connect(
            lambda document: self.open_document(document, view_only=True)
        )
        self.dashboard.document_remove_requested.connect(self.remove_requested)
        self.dashboard.create_file_requested.connect(
            lambda: self.create_file_requested.emit(self.library_root)
        )
        self.dashboard.create_folder_requested.connect(
            lambda: self.create_folder_requested.emit(self.library_root)
        )
        self.dashboard.refresh_requested.connect(self.refresh_requested)
        self.dashboard.sort_mode_changed.connect(self.sort_mode_changed)
        self.dashboard.view_mode_changed.connect(self.view_mode_changed)
        self.dashboard.external_files_dropped.connect(
            lambda paths: self.external_files_import_requested.emit(
                paths, self.library_root
            )
        )

    def _tabs_enabled(self) -> bool:
        return bool(self.config.get("tabs_enabled", True))

    def _show_dashboard_surface(self) -> None:
        """Show Dashboard without invoking document-lifetime policy."""
        self.current_document = None; self.current_folder = None
        self.stack.setCurrentWidget(self.dashboard)
        self.dashboard_shown.emit()

    def show_dashboard(self) -> bool:
        """Show Dashboard, closing the active document first when tabs are disabled."""
        if not self._tabs_enabled() and self.current_document is not None:
            return self.close_document(self.current_document)
        self._show_dashboard_surface()
        return True

    def _live_pages(self) -> list[EditorPage]:
        pages: list[EditorPage] = []
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, EditorPage):
                pages.append(page)
        return pages

    @staticmethod
    def _resolution_item(page: EditorPage) -> tuple[object, str, str, bool] | None:
        if page.backing_state == "missing":
            state = "Unsaved changes · backing file missing" if page.is_modified else "Backing file missing"
            return page, page.document.filename, state, False
        if page.is_modified and page.backing_state != "normal":
            return page, page.document.filename, "Unsaved changes · file changed on disk", False
        if page.is_modified:
            return page, page.document.filename, "Unsaved changes", True
        return None

    def _resolve_pages_before_close(self, pages: list[EditorPage], message: str) -> bool:
        at_risk = [item for page in pages if (item := self._resolution_item(page)) is not None]
        if not at_risk:
            return True
        if len(at_risk) == 1:
            return bool(at_risk[0][0].can_close())

        dialog = ResolveOpenDocumentsDialog(at_risk, message, self.stack.window())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        for page, action in dialog.decisions():
            if action == "discard":
                continue
            if action == "save":
                if not page.save_to_disk():
                    return False
                continue
            if action == "resolve":
                if not page.can_close():
                    return False
                continue
            return False
        return True

    def _dispose_editor_page(self, page: EditorPage) -> bool:
        """Dispose an already-approved page without showing another close prompt."""
        document = page.document
        state = self.states.get(document.path)
        if state is None or state.editor_page is not page:
            return True
        if self.stack.currentWidget() is page:
            self._show_dashboard_surface()
        closed_path = document.path
        self.open_document_monitor.unregister(closed_path)
        self.stack.removeWidget(page); page.deleteLater(); state.clear_editor()
        document.loaded = False; self.repository.set_dirty(document.path, False)
        if not document.external and not document.path.exists():
            self.repository.remove(document.path)
        else:
            self.document_closed.emit(closed_path)
        return True

    def prepare_tabs_disabled(self) -> bool:
        """Contract a tabbed session to the current document, or to no document."""
        anchor_page = None
        if self.current_document is not None:
            state = self.states.get(self.current_document.path)
            if state is not None and isinstance(state.editor_page, EditorPage):
                anchor_page = state.editor_page
        targets = [page for page in self._live_pages() if page is not anchor_page]
        if not self._resolve_pages_before_close(
            targets,
            "Tabs Disabled keeps only the current document open. Resolve the documents below before disabling tabs.",
        ):
            return False
        for page in targets:
            self._dispose_editor_page(page)
        return True

    def open_folder(self, path) -> FolderDashboard | None:
        folder_path = Path(path).expanduser().resolve(strict=False)
        if not self._tabs_enabled() and self.current_document is not None:
            if not self.close_document(self.current_document):
                return None
        try: folder_path.relative_to(self.library_root)
        except ValueError:
            self.status_message.emit("The selected folder is outside the workspace.")
            return None
        if not folder_path.is_dir():
            self.status_message.emit("The selected folder is no longer available.")
            return None
        page = self._folder_pages.get(folder_path)
        if page is None:
            page = FolderDashboard(WorkspaceFolder(folder_path, self.library_root), self.repository, self.stack)
            page.document_open_requested.connect(
                lambda document: self.open_document(document, view_only=False)
            )
            page.document_view_only_requested.connect(
                lambda document: self.open_document(document, view_only=True)
            )
            page.document_remove_requested.connect(self.remove_requested)
            page.open_external_requested.connect(self.folder_open_external_requested)
            page.rename_folder_requested.connect(self.folder_rename_requested)
            page.remove_folder_requested.connect(self.folder_remove_requested)
            page.create_file_requested.connect(self.create_file_requested)
            page.create_folder_requested.connect(self.create_folder_requested)
            page.external_files_dropped.connect(
                self.external_files_import_requested
            )
            self._folder_pages[folder_path] = page
            self.stack.addWidget(page)
        self.current_document = None; self.current_folder = folder_path
        self.stack.setCurrentWidget(page)
        self.current_folder_changed.emit(folder_path)
        return page

    def open_document(
        self,
        document_or_path,
        *,
        view_only: bool | None = None,
    ) -> EditorPage | None:
        document = self._resolve_document(document_or_path)
        if document is None:
            self.status_message.emit("The selected RTF file is no longer available.")
            return None
        if (
            not self._tabs_enabled()
            and self.current_document is not None
            and self.current_document.path != document.path
        ):
            if not self.close_document(self.current_document):
                return None
        state = self.states.ensure(document.path)
        page = state.editor_page
        if not isinstance(page, EditorPage):
            page = self._create_editor_page(document)
            if not page.loaded_successfully:
                page.deleteLater()
                state.clear_editor()
                document.loaded = False
                return None
            state.editor_page = page; state.editor = page.editor; state.page_created = True
            document.loaded = True
        self.open_document_monitor.register(document.path)
        if view_only is not None:
            self.set_lock_editor(bool(view_only))
        page.set_view_only(bool(self.config.get("lock_editor", False)))
        self.current_folder = None; self.current_document = document
        self.stack.setCurrentWidget(page)
        if page.view_only:
            page.scroll_to_top()
        page.editor.setFocus()
        self.current_document_changed.emit(document)
        return page

    def set_lock_editor(self, enabled: bool) -> None:
        """Persist and apply the editor lock across every live document page."""
        enabled = bool(enabled)
        self.config.set("lock_editor", enabled, save=True)
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, EditorPage):
                page.set_view_only(enabled)

    def open_document_in_view(self, document_or_path, mode: str) -> EditorPage | None:
        return self.open_document(document_or_path, view_only=(mode == "view"))

    def _create_editor_page(self, document) -> EditorPage:
        page = EditorPage(document, self.repository, self.config, self.stack)
        page.external_editor_requested.connect(self.external_editor_requested)
        page.containing_folder_requested.connect(
            self.containing_folder_requested
        )
        page.rename_requested.connect(self.rename_requested)
        page.remove_requested.connect(self.remove_requested)
        page.duplicate_requested.connect(self.duplicate_requested)
        page.undo_redo_changed.connect(self.editor_history_changed)
        page.formatting_state_changed.connect(self.editor_formatting_changed)
        page.preferences_changed.connect(self.apply_editor_preferences)
        page.preferences_changed.connect(self.editor_preferences_changed)
        page.new_requested.connect(self.create_file_requested)
        page.workspace_requested.connect(self.workspace_requested)
        page.dashboard_requested.connect(self.show_dashboard)
        page.exit_requested.connect(self.exit_requested)
        page.save_and_new_requested.connect(self.save_and_new_requested)
        page.save_and_dashboard_requested.connect(
            self.save_and_dashboard_requested
        )
        page.save_and_exit_requested.connect(self.save_and_exit_requested)
        page.external_files_dropped.connect(self.editor_files_dropped)
        page.path_changed.connect(self._rebind_page_path)
        self.stack.addWidget(page)
        return page

    def _rebind_page_path(
        self,
        page: EditorPage,
        old_path: Path,
        new_path: Path,
    ) -> None:
        """Rebind an editor after Save As without importing external files."""
        if old_path == new_path:
            return
        old_document = page.document
        was_current = self.current_document is old_document or self.stack.currentWidget() is page

        try:
            info = new_path.stat()
        except OSError:
            return
        try:
            relative_parent = new_path.parent.relative_to(self.library_root)
            external = False
            folder = "" if str(relative_parent) == "." else relative_parent.as_posix()
        except ValueError:
            external = True
            folder = str(new_path.parent)

        target = self.repository.get(new_path)
        if target is None:
            target = self.repository.add(
                DocumentEntry(
                    path=new_path,
                    filename=new_path.name,
                    display_name=new_path.stem.replace("-", " ").replace("_", " ").title(),
                    folder=folder,
                    created=info.st_ctime,
                    modified=info.st_mtime,
                    size=info.st_size,
                    external=external,
                )
            )

        # Establish the new managed identity before any repository notification
        # about the old document can reach this page.  The surface has already
        # written the target independently and emitted file_path_changed, so the
        # page and embedded editor must now move together as one transaction.
        target.loaded = True
        page.document = target
        page._refresh_header()
        target_state = self.states.ensure(target.path)
        target_state.editor_page = page
        target_state.editor = page.editor
        target_state.page_created = True
        if was_current:
            self.current_document = target
            self.current_folder = None

        old_state = self.states.get(old_path)
        if old_state is not None and old_state.editor_page is page:
            old_state.clear_editor()
        old_document.loaded = False
        self.open_document_monitor.rebind(old_path, target.path)
        self.repository.set_dirty(old_path, False)
        if old_document.external:
            self.repository.remove(old_path)
        self.repository.set_dirty(target.path, False)
        # Rebind presentation identity before announcing the current document so
        # tab views update the existing tab instead of briefly creating a second
        # tab for the Save-As target.
        self.document_path_rebound.emit(old_path, new_path)
        if was_current:
            self.current_document_changed.emit(target)

    def apply_editor_preferences(self) -> None:
        """Apply shared Ricopad editor display preferences to open pages."""
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, EditorPage):
                page.apply_preferences()

    def show_current_editor_status(self, message: str, timeout: int = 4000) -> None:
        """Route an editor-scoped message to the currently open document page."""
        document = self.current_document
        if document is None:
            return
        state = self.states.get(document.path)
        page = state.editor_page if state is not None else None
        if isinstance(page, EditorPage):
            page.show_editor_status(message, timeout)

    def close_document(self, document_or_path) -> bool:
        document = self._resolve_document(document_or_path)
        if document is None: return True
        state = self.states.get(document.path)
        if state is None or not isinstance(state.editor_page, EditorPage): return True
        page = state.editor_page
        if not page.can_close(): return False
        return self._dispose_editor_page(page)

    def close_pages_in_folder(self, folder_path) -> bool:
        folder = Path(folder_path).expanduser().resolve(strict=False)
        targets = []
        for document in self.repository:
            try: document.path.relative_to(folder)
            except ValueError: continue
            state = self.states.get(document.path)
            if state is not None and isinstance(state.editor_page, EditorPage):
                targets.append((document, state, state.editor_page))
        for _document, _state, page in targets:
            if not page.can_close(): return False
        for document, state, page in targets:
            document = page.document
            state = self.states.get(document.path) or state
            if self.stack.currentWidget() is page: self._show_dashboard_surface()
            closed_path = document.path
            self.open_document_monitor.unregister(closed_path)
            self.stack.removeWidget(page); page.deleteLater(); state.clear_editor()
            document.loaded = False; self.repository.set_dirty(document.path, False)
            if not document.external and not document.path.exists():
                self.repository.remove(document.path)
            else:
                self.document_closed.emit(closed_path)
        return True

    def close_folder_page(self, folder_path) -> None:
        path = Path(folder_path).expanduser().resolve(strict=False)
        page = self._folder_pages.pop(path, None)
        if page is not None:
            if self.stack.currentWidget() is page: self._show_dashboard_surface()
            self.stack.removeWidget(page); page.deleteLater()
        if self.current_folder == path: self.current_folder = None

    def can_close_application(self) -> bool:
        pages = self._live_pages()
        return self._resolve_pages_before_close(
            pages,
            "Resolve the documents below before closing RiqatonyDesk.",
        )

    def current_path(self):
        if self.current_document is not None: return self.current_document.path
        return self.current_folder

    def set_sort_mode(self, mode): self.dashboard.set_sort_mode(mode)
    def set_search_text(self, text): self.dashboard.set_search_text(text)
    def set_view_mode(self, mode): self.dashboard.set_view_mode(mode)

    def switch_workspace_root(self, library_root: str | Path) -> None:
        """Dispose only root-bound pages before the shared repository is reset."""
        self._on_repository_reset()
        self.library_root = Path(library_root).expanduser().resolve(strict=False)
        self.current_document = None
        self.current_folder = None

    def _on_managed_path_changed(self, document: DocumentEntry, old_path: Path) -> None:
        """Keep monitoring aligned with deliberate in-app rename/move operations."""
        if document.loaded:
            self.open_document_monitor.rebind(old_path, document.path)

    def _on_open_backing_path_changed(self, path: Path) -> None:
        """Ask only the live page for this path to perform an exact disk check."""
        state = self.states.get(path)
        page = state.editor_page if state is not None else None
        if isinstance(page, EditorPage):
            page.handle_backing_path_event(notify=True)

    def _on_state_removed(self, document, state) -> None:
        """Dispose UI objects after a document is removed externally or internally."""
        self.open_document_monitor.unregister(document.path)
        page = state.editor_page
        if isinstance(page, QWidget):
            if self.stack.currentWidget() is page:
                self._show_dashboard_surface()
            self.stack.removeWidget(page)
            page.deleteLater()
        state.clear_editor()
        self.document_closed.emit(document.path)
        if self.current_document is document:
            self.current_document = None

    def _on_repository_reset(self) -> None:
        self.open_document_monitor.clear()
        self._show_dashboard_surface()
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, QWidget): self.stack.removeWidget(page); page.deleteLater()
            state.clear_editor()
        for page in self._folder_pages.values(): self.stack.removeWidget(page); page.deleteLater()
        self._folder_pages.clear()
        self.documents_reset.emit()

    def _resolve_document(self, value):
        if isinstance(value, DocumentEntry):
            return self.repository.get(value.path) or value
        return self.repository.get(value)
