# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing document-tab behaviour extracted without altering its methods."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QTabBar

from riqatony_desk.models.document import DocumentEntry


class DocumentTabsMixin:
    def _tabs_enabled(self) -> bool:
        return bool(self.config.get("tabs_enabled", True))

    def _sync_tabs_mode_ui(self) -> None:
        enabled = self._tabs_enabled()
        if not enabled:
            self._remove_navigation_tab()
            self.document_tabs.setVisible(False)
        elif self.editor_manager.current_document is not None:
            self._select_document_tab(self.editor_manager.current_document)
        elif self.editor_manager.current_folder is not None:
            self._show_folder_navigation_tab(self.editor_manager.current_folder)
        else:
            self._show_dashboard_navigation_tab()
        for key, action in self.tabs_actions.items():
            action.blockSignals(True)
            action.setChecked((key == "enabled") == enabled)
            action.blockSignals(False)
        self._sync_app_settings_toggle_actions()
        self._refresh_action_icons()

    def _set_tabs_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        current = self._tabs_enabled()
        if enabled == current:
            self._sync_tabs_mode_ui()
            return
        if not enabled and current:
            if not self.editor_manager.prepare_tabs_disabled():
                self._sync_tabs_mode_ui()
                return
        self.config.set("tabs_enabled", enabled, save=True)
        self._sync_tabs_mode_ui()

    def _open_context_navigation_for_path(self, path: str | Path) -> None:
        """Open the temporary navigation surface for a document's location."""
        document_path = Path(path).expanduser().resolve(strict=False)
        parent = document_path.parent
        try:
            parent.relative_to(self.library_root)
        except ValueError:
            self.editor_manager.show_dashboard()
            return
        if parent == self.library_root or not parent.is_dir():
            self.editor_manager.show_dashboard()
            return
        self.editor_manager.open_folder(parent)

    def _open_context_tab(self, _checked=False) -> None:
        """Open/reuse the contextual temporary tab, enabling tabs if needed."""
        document = self.editor_manager.current_document
        document_path = document.path if document is not None else None
        if not self._tabs_enabled():
            self._set_tabs_enabled(True)
        if document_path is not None:
            self._open_context_navigation_for_path(document_path)
            return
        folder = self.editor_manager.current_folder
        if folder is not None:
            self.editor_manager.open_folder(folder)
        else:
            self.editor_manager.show_dashboard()

    def _close_context(self, _checked=False) -> None:
        """Ctrl+W: close the active tab contextually, or show Dashboard."""
        if not self._tabs_enabled():
            self.editor_manager.show_dashboard()
            return
        document = self.editor_manager.current_document
        if document is None:
            self.editor_manager.show_dashboard()
            return
        path = document.path
        if not self.editor_manager.close_document(document):
            return
        self._open_context_navigation_for_path(path)

    def _cycle_context_tab(self, direction: int) -> None:
        if self._tabs_enabled():
            self._cycle_document_tab(direction)
            return
        if hasattr(self, "shell_ribbon"):
            self.shell_ribbon.cycle_tab(direction)

    def _tab_index_for_path(self, path: str | Path) -> int:
        target = str(Path(path).expanduser().resolve(strict=False))
        for index in range(self.document_tabs.count()):
            if self.document_tabs.tabData(index) == target:
                return index
        return -1

    @staticmethod
    def _document_tab_text(document: DocumentEntry) -> str:
        return f"{document.filename}{'*' if document.dirty else ''}"

    _NAV_TAB_PREFIX = "riqatonydesk://navigation/"
    _NAV_DASHBOARD_TOKEN = _NAV_TAB_PREFIX + "dashboard"
    _NAV_FOLDER_PREFIX = _NAV_TAB_PREFIX + "folder/"

    def _navigation_tab_index(self) -> int:
        for index in range(self.document_tabs.count()):
            data = self.document_tabs.tabData(index)
            if isinstance(data, str) and data.startswith(self._NAV_TAB_PREFIX):
                return index
        return -1

    def _remove_navigation_tab(self) -> None:
        index = self._navigation_tab_index()
        if index < 0:
            return
        self.document_tabs.blockSignals(True)
        self.document_tabs.removeTab(index)
        self.document_tabs.blockSignals(False)
        self.document_tabs.setVisible(self._tabs_enabled() and self.document_tabs.count() > 0)

    def _show_navigation_tab(self, text: str, token: str, tooltip: str) -> None:
        if not self._tabs_enabled():
            return
        index = self._navigation_tab_index()
        self.document_tabs.blockSignals(True)
        if index < 0:
            index = self.document_tabs.addTab(text)
        else:
            self.document_tabs.setTabText(index, text)
        self.document_tabs.setTabData(index, token)
        self.document_tabs.setTabToolTip(index, tooltip)
        # Navigation tabs are ephemeral views, not closable document resources.
        self.document_tabs.setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        self.document_tabs.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        self.document_tabs.setCurrentIndex(index)
        self.document_tabs.blockSignals(False)
        self.document_tabs.setVisible(True)

    def _show_dashboard_navigation_tab(self, *_args) -> None:
        self._show_navigation_tab("Dashboard", self._NAV_DASHBOARD_TOKEN, "Dashboard")

    def _show_folder_navigation_tab(self, folder_path: str | Path) -> None:
        path = Path(folder_path).expanduser().resolve(strict=False)
        label = path.name or "Folder"
        self._show_navigation_tab(label, self._NAV_FOLDER_PREFIX + str(path), str(path))

    def _ensure_document_tab(self, document: DocumentEntry) -> int:
        path_text = str(document.path.expanduser().resolve(strict=False))
        index = self._tab_index_for_path(document.path)
        if index < 0:
            self.document_tabs.blockSignals(True)
            index = self.document_tabs.addTab(self._document_tab_text(document))
            self.document_tabs.setTabData(index, path_text)
            self.document_tabs.blockSignals(False)
        else:
            self.document_tabs.setTabText(index, self._document_tab_text(document))
        self.document_tabs.setTabToolTip(index, path_text)
        self.document_tabs.setVisible(self._tabs_enabled() and self.document_tabs.count() > 0)
        return index

    def _select_document_tab(self, document: DocumentEntry) -> None:
        self._remove_navigation_tab()
        index = self._ensure_document_tab(document)
        self.document_tabs.blockSignals(True)
        self.document_tabs.setCurrentIndex(index)
        self.document_tabs.blockSignals(False)

    def _activate_document_tab(self, index: int) -> None:
        if index < 0 or index >= self.document_tabs.count():
            return
        data = self.document_tabs.tabData(index)
        if not data:
            return
        token = str(data)
        if token == self._NAV_DASHBOARD_TOKEN:
            self.editor_manager.show_dashboard()
            return
        if token.startswith(self._NAV_FOLDER_PREFIX):
            self.editor_manager.open_folder(Path(token[len(self._NAV_FOLDER_PREFIX):]))
            return
        path = Path(token)
        document = self.repository.get(path)
        if document is None:
            self._remove_document_tab(path)
            return
        self.editor_manager.open_document(document)

    def _remove_document_tab(self, path: str | Path) -> None:
        index = self._tab_index_for_path(path)
        if index < 0:
            return
        self.document_tabs.blockSignals(True)
        self.document_tabs.removeTab(index)
        self.document_tabs.blockSignals(False)
        self.document_tabs.setVisible(self._tabs_enabled() and self.document_tabs.count() > 0)

    def _close_document_tab(self, index: int) -> None:
        if index < 0 or index >= self.document_tabs.count():
            return
        data = self.document_tabs.tabData(index)
        if not data:
            return
        token = str(data)
        if token.startswith(self._NAV_TAB_PREFIX):
            return
        path = Path(token)
        # Remember the natural adjacent tab before the manager removes the
        # current page; only direct tab-close gestures auto-activate a neighbor.
        neighbor_path: Path | None = None
        if self.document_tabs.count() > 1:
            neighbor_index = index + 1 if index + 1 < self.document_tabs.count() else index - 1
            neighbor_data = self.document_tabs.tabData(neighbor_index)
            if neighbor_data:
                neighbor_path = Path(str(neighbor_data))
        if not self.editor_manager.close_document(path):
            return
        if self.editor_manager.current_document is None and neighbor_path is not None:
            neighbor = self.repository.get(neighbor_path)
            if neighbor is not None:
                self.editor_manager.open_document(neighbor)

    def _cycle_document_tab(self, direction: int) -> None:
        count = self.document_tabs.count()
        if count <= 0:
            return
        current = self.document_tabs.currentIndex()
        if current < 0:
            target = 0 if direction >= 0 else count - 1
        else:
            target = (current + (1 if direction >= 0 else -1)) % count
        self._activate_document_tab(target)

    def _update_document_tab(self, document: DocumentEntry) -> None:
        current = self.editor_manager.current_document
        if current is not None and current.path == document.path:
            self._update_window_title()
        index = self._tab_index_for_path(document.path)
        if index < 0:
            return
        self.document_tabs.setTabText(index, self._document_tab_text(document))
        self.document_tabs.setTabToolTip(index, str(document.path))

    def _rebind_document_tab(self, old_path: str | Path, new_path: str | Path) -> None:
        index = self._tab_index_for_path(old_path)
        if index < 0:
            return
        new_path = Path(new_path).expanduser().resolve(strict=False)
        self.document_tabs.setTabData(index, str(new_path))
        document = self.repository.get(new_path)
        if document is not None:
            self.document_tabs.setTabText(index, self._document_tab_text(document))
            self.document_tabs.setTabToolTip(index, str(new_path))

    def _on_repository_document_path_changed(self, document: DocumentEntry, old_path: Path) -> None:
        self._rebind_document_tab(old_path, document.path)

    def _reset_document_tabs(self) -> None:
        self.document_tabs.blockSignals(True)
        while self.document_tabs.count():
            self.document_tabs.removeTab(0)
        self.document_tabs.blockSignals(False)
        self.document_tabs.setVisible(False)

    def _toggle_tabs_mode(self, _checked=False) -> None:
        self._set_tabs_enabled(not self._tabs_enabled())

