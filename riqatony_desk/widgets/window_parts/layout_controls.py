# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing MainWindow layout-control methods relocated without behavioural changes."""

from __future__ import annotations

from riqatony_desk.widgets.editor_page import EditorPage
from riqatony_desk.widgets.workspace.navigation import SIDEBAR_MINIMUM_WIDTH


class LayoutControlsMixin:
    def _sidebar_position(self) -> str:
        return "right" if self.splitter.indexOf(self.navigation) > self.splitter.indexOf(self.content_host) else "left"

    def _logical_splitter_sizes(self) -> list[int]:
        sizes = list(self.splitter.sizes())
        if len(sizes) != 2:
            return [int(getattr(self, "_restored_sidebar_width", 260)), 1090]
        if self._sidebar_position() == "right":
            return [sizes[1], sizes[0]]
        return sizes

    def _set_splitter_sidebar_width(self, sidebar_width: int) -> None:
        total = max(1, self.splitter.width() - max(1, self.splitter.handleWidth()))
        content_floor = min(420, max(1, total - SIDEBAR_MINIMUM_WIDTH))
        maximum = max(SIDEBAR_MINIMUM_WIDTH, total - content_floor)
        sidebar = max(SIDEBAR_MINIMUM_WIDTH, min(int(sidebar_width), maximum))
        content = max(1, total - sidebar)
        if self._sidebar_position() == "right":
            self.splitter.setSizes([content, sidebar])
        else:
            self.splitter.setSizes([sidebar, content])
        self._restored_sidebar_width = sidebar

    def _set_sidebar_position(self, position: str, *, persist: bool = True) -> None:
        position = "right" if str(position).lower() == "right" else "left"
        current_sizes = self._logical_splitter_sizes()
        sidebar_width = current_sizes[0] if current_sizes and current_sizes[0] > 0 else int(getattr(self, "_restored_sidebar_width", 260))
        target_index = 0 if position == "left" else 1
        if self.splitter.indexOf(self.navigation) != target_index:
            self.splitter.insertWidget(target_index, self.navigation)
        sidebar_index = self.splitter.indexOf(self.navigation)
        content_index = self.splitter.indexOf(self.content_host)
        self.splitter.setStretchFactor(sidebar_index, 0)
        self.splitter.setStretchFactor(content_index, 1)
        self.splitter.setCollapsible(sidebar_index, False)
        self.splitter.setCollapsible(content_index, False)
        for value, action in self.sidebar_position_actions.items():
            action.blockSignals(True)
            action.setChecked(value == position)
            action.blockSignals(False)
        if persist:
            self.config.set("sidebar_position", position, save=True)
        self._set_splitter_sidebar_width(sidebar_width)
        self._sync_sidebar_position_icons()

    def _toggle_sidebar_position(self) -> None:
        current = str(self.config.get("sidebar_position", "left"))
        self._set_sidebar_position("left" if current == "right" else "right")

    def _set_sidebar_visible(self, visible: bool, *, sync_action: bool = True) -> None:
        visible = bool(visible)
        self.navigation.setVisible(visible)
        if sync_action:
            self.sidebar_action.blockSignals(True)
            self.sidebar_action.setChecked(visible)
            self.sidebar_action.blockSignals(False)

    def _toggle_sidebar(self, checked: bool) -> None:
        self._set_sidebar_visible(bool(checked), sync_action=False)

    def _set_status_visible(self, visible: bool, *, persist: bool, sync_action: bool = True) -> None:
        visible = bool(visible)
        self.statusBar().setVisible(visible)
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, EditorPage):
                page.set_status_visible(visible)
        if sync_action:
            self.status_bar_action.blockSignals(True)
            self.status_bar_action.setChecked(visible)
            self.status_bar_action.blockSignals(False)
        if persist:
            self.config.set("show_status_bar", visible, save=True)

    def _toggle_status_bar(self, checked: bool) -> None:
        self._set_status_visible(bool(checked), persist=True, sync_action=False)

    def _set_file_header_visible(self, visible: bool, *, persist: bool, sync_action: bool = True) -> None:
        visible = bool(visible)
        for _path, state in tuple(self.states):
            page = state.editor_page
            if isinstance(page, EditorPage):
                page.set_header_visible(visible)
        if sync_action:
            self.file_header_action.blockSignals(True)
            self.file_header_action.setChecked(visible)
            self.file_header_action.blockSignals(False)
        if persist:
            self.config.set("show_file_header", visible, save=True)

    def _toggle_file_header(self, checked: bool) -> None:
        self._set_file_header_visible(bool(checked), persist=True, sync_action=False)

    def _toggle_collapsed_mode(self, checked: bool) -> None:
        """Temporarily focus the workspace without overwriting view preferences."""
        checked = bool(checked)
        if checked:
            if self._collapsed_mode_restore is None:
                self._collapsed_mode_restore = {
                    "sidebar": self.navigation.isVisible(),
                    "status": self.statusBar().isVisible(),
                    "header": self.file_header_action.isChecked(),
                    "ribbon_collapsed": bool(getattr(self.shell_ribbon, "_collapsed", False)),
                    "splitter_sizes": self._logical_splitter_sizes(),
                }
            self._set_sidebar_visible(False)
            self._set_status_visible(False, persist=False)
            self._set_file_header_visible(False, persist=False)
            # AppMenu-only command: reuse the existing double-click collapse
            # behavior without adding or changing any Ribbon command.
            self.shell_ribbon.set_collapsed(True, emit=False)
            return

        restore = self._collapsed_mode_restore or {
            "sidebar": self.sidebar_action.isChecked(),
            "status": bool(self.config.get("show_status_bar", True)),
            "header": bool(self.config.get("show_file_header", True)),
            "ribbon_collapsed": bool(self.config.get("riqatony_desk_ribbon_collapsed", False)),
        }
        self._set_sidebar_visible(bool(restore.get("sidebar", True)))
        self._set_status_visible(bool(restore.get("status", True)), persist=False)
        self._set_file_header_visible(bool(restore.get("header", True)), persist=False)
        self.shell_ribbon.set_collapsed(bool(restore.get("ribbon_collapsed", False)), emit=False)
        self._collapsed_mode_restore = None

    def _toggle_fullscreen(self, checked: bool) -> None:
        self.showFullScreen() if checked else self.showNormal()

