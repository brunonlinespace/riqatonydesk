# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing MainWindow navigation-history methods relocated without behavioural changes."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QTimer


class NavigationHistoryMixin:
    def _queue_navigation_record(self, target: str) -> None:
        if self._navigation_back_in_progress:
            self._navigation_current = target
            self._navigation_pending = None
            return
        self._navigation_pending = target
        if self._navigation_record_scheduled:
            return
        self._navigation_record_scheduled = True
        QTimer.singleShot(0, self._commit_navigation_record)

    def _commit_navigation_record(self) -> None:
        self._navigation_record_scheduled = False
        target = self._navigation_pending
        self._navigation_pending = None
        if not target or target == self._navigation_current:
            return
        if self._navigation_current:
            self._navigation_history.append(self._navigation_current)
            if len(self._navigation_history) > 64:
                del self._navigation_history[:-64]
        self._navigation_current = target

    def _record_dashboard_navigation(self, *_args) -> None:
        self._queue_navigation_record("dashboard")

    def _record_folder_navigation(self, path: str | Path) -> None:
        folder = Path(path).expanduser().resolve(strict=False)
        self._queue_navigation_record(f"folder:{folder}")

    def _record_document_navigation(self, document) -> None:
        path = Path(document.path).expanduser().resolve(strict=False)
        self._queue_navigation_record(f"document:{path}")

    def _navigate_back(self) -> None:
        self._commit_navigation_record()
        while self._navigation_history:
            target = self._navigation_history.pop()
            if target == self._navigation_current:
                continue
            self._navigation_back_in_progress = True
            try:
                if target == "dashboard":
                    if not self.editor_manager.show_dashboard():
                        self._navigation_history.append(target)
                    return
                if target.startswith("folder:"):
                    path = Path(target.split(":", 1)[1]).expanduser().resolve(strict=False)
                    try:
                        path.relative_to(self.library_root)
                    except ValueError:
                        continue
                    if not path.is_dir():
                        continue
                    if self.editor_manager.open_folder(path) is None:
                        self._navigation_history.append(target)
                    return
                if target.startswith("document:"):
                    path = Path(target.split(":", 1)[1]).expanduser().resolve(strict=False)
                    if self.repository.get(path) is None:
                        continue
                    if self.editor_manager.open_document(path) is None:
                        self._navigation_history.append(target)
                    return
            finally:
                self._navigation_back_in_progress = False

