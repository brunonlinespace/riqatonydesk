# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
"""Persistent dashboard with fast list/grid switching."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QIcon, QPalette, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QScroller,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from riqatony_desk.models.document import DocumentEntry
from riqatony_desk.models.document_repository import DocumentRepository
from riqatony_desk.models.document_state_store import DocumentStateStore
from riqatony_desk.services.resources import icon_path
from riqatony_desk.widgets.workspace.dashboard_card import DashboardCard
from riqatony_desk.widgets.loading_indicator import LoadingIndicator
from riqatony_desk.widgets.workspace.navigation import external_rtf_paths
from riqatony_desk.widgets.ui_styles import style_button, style_combo_box, style_line_edit


class FlowLayout(QLayout):
    """Lightweight wrapping layout used by the grid dashboard."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        margin: int = 0,
        spacing: int = 12,
    ) -> None:
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []

    def addItem(self, item) -> None:
        self._items.append(item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            if item.isEmpty():
                continue
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        return size

    def replace_widgets(self, widgets: list[QWidget]) -> None:
        """Reorder retained grid items without detaching/recreating Qt widgets.

        Search visibility is handled by hide/show, so this runs only when
        document order or repository membership actually changes.
        """
        retained = {item.widget(): item for item in self._items}
        reordered = []
        for widget in widgets:
            item = retained.pop(widget, None)
            if item is None:
                # Use the base QLayout registration for newly added widgets.
                # Retained entries reuse their existing QWidgetItem objects.
                self.addWidget(widget)
                item = self._items.pop()
            reordered.append(item)
        self._items = reordered
        self.invalidate()

    def clear(self) -> None:
        """Remove layout items without deleting their widgets."""
        while self.count():
            self.takeAt(0)

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        # Cache each sizeHint once per layout pass.
        for item in self._items:
            if item.isEmpty():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + spacing

            if next_x - spacing > rect.right() and x > rect.x():
                x = rect.x()
                y += line_height + spacing
                next_x = x + hint.width() + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y()


class CurrentPageStack(QStackedWidget):
    """Scrollable stack with cached geometry for the unchanged active page.

    Large Dashboard layouts are expensive to measure.  Qt can request the
    current page's hints repeatedly during a single List/Grid transition.
    Retain those measurements until the page requests a new layout, its
    typography changes, or Dashboard contents are rebuilt.  Cache by the
    available width so resizing still recomputes wrapping heights.
    """

    _INVALIDATING_EVENTS = frozenset((
        QEvent.Type.LayoutRequest,
        QEvent.Type.FontChange,
        QEvent.Type.StyleChange,
        QEvent.Type.ContentsRectChange,
    ))

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hint_cache: dict[tuple[QWidget, str, int], QSize] = {}
        self._height_cache: dict[tuple[QWidget, int], int] = {}
        self._tracked_pages: set[QWidget] = set()
        self.currentChanged.connect(self._current_page_changed)

    def addWidget(self, widget: QWidget) -> int:
        index = super().addWidget(widget)
        self._tracked_pages.add(widget)
        widget.installEventFilter(self)
        self.invalidate_measurements()
        return index

    def invalidate_measurements(self) -> None:
        self._hint_cache.clear()
        self._height_cache.clear()

    def eventFilter(self, watched, event) -> bool:
        if watched in self._tracked_pages and event.type() in self._INVALIDATING_EVENTS:
            self.invalidate_measurements()
        return super().eventFilter(watched, event)

    def hasHeightForWidth(self) -> bool:
        widget = self.currentWidget()
        layout = widget.layout() if widget is not None else None
        return bool(layout is not None and layout.hasHeightForWidth())

    def heightForWidth(self, width: int) -> int:
        widget = self.currentWidget()
        if widget is None:
            return super().heightForWidth(width)

        key = (widget, width)
        cached = self._height_cache.get(key)
        if cached is not None:
            return cached
        layout = widget.layout()
        if layout is not None and layout.hasHeightForWidth():
            margins = self.contentsMargins()
            available = max(0, width - margins.left() - margins.right())
            height = (
                layout.heightForWidth(available)
                + margins.top()
                + margins.bottom()
            )
        else:
            height = widget.sizeHint().height()
        # Limit retained widths during repeated interactive window resizing.
        if len(self._height_cache) >= 32:
            self._height_cache.clear()
        self._height_cache[key] = height
        return height

    def _page_hint(self, kind: str) -> QSize:
        widget = self.currentWidget()
        if widget is None:
            return (super().minimumSizeHint() if kind == "minimum" else super().sizeHint())

        width = max(1, self.viewport_width_hint())
        key = (widget, kind, width)
        cached = self._hint_cache.get(key)
        if cached is not None:
            return QSize(cached)

        hint = widget.minimumSizeHint() if kind == "minimum" else widget.sizeHint()
        if self.hasHeightForWidth():
            hint.setHeight(self.heightForWidth(width))
        if len(self._hint_cache) >= 32:
            self._hint_cache.clear()
        self._hint_cache[key] = QSize(hint)
        return hint

    def sizeHint(self) -> QSize:
        return self._page_hint("size")

    def minimumSizeHint(self) -> QSize:
        return self._page_hint("minimum")

    def viewport_width_hint(self) -> int:
        """Return an existing geometry width without querying sizeHint()."""
        ancestor = self.parentWidget()
        while ancestor is not None:
            if isinstance(ancestor, QScrollArea):
                viewport_width = ancestor.viewport().width()
                if viewport_width > 0:
                    return viewport_width
                break
            ancestor = ancestor.parentWidget()

        for candidate in (
            self.width(),
            self.currentWidget().width() if self.currentWidget() else 0,
            self.parentWidget().width() if self.parentWidget() else 0,
        ):
            if candidate > 0:
                return candidate

        # Construction-time fallback only. Never call sizeHint() here because
        # this method is itself used by sizeHint().
        return 800

    def _current_page_changed(self, _index: int) -> None:
        # QStackedWidget has already changed the visible page.  Notify the
        # scroll area's geometry once, not again from set_view_mode().
        # No card reparenting or forced child-layout activation is necessary.
        self.updateGeometry()


class DashboardWidget(QWidget):
    """Dashboard that creates one persistent card per repository document."""

    document_open_requested = pyqtSignal(object)
    document_view_only_requested = pyqtSignal(object)
    document_remove_requested = pyqtSignal(object)
    refresh_requested = pyqtSignal()
    create_file_requested = pyqtSignal()
    create_folder_requested = pyqtSignal()
    sort_mode_changed = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)
    external_files_dropped = pyqtSignal(object)

    SORT_LABELS = {
        "Title (A-Z)": "title_az",
        "Title (Z-A)": "title_za",
        "Last Created": "created",
        "Last Modified": "modified",
    }
    VALID_VIEW_MODES = {"list", "grid"}

    def __init__(
        self,
        repository: DocumentRepository,
        states: DocumentStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.repository = repository
        self.states = states
        self._list_cards: dict[Path, DashboardCard] = {}
        self._grid_cards: dict[Path, DashboardCard] = {}
        self._layout_signatures: dict[Path, tuple[object, ...]] = {}
        # Stable source of truth for layout order and filtered visibility.
        # Cards stay parented in both views; a search changes visibility, not
        # the ownership or order of their QWidget layout items.
        self._layout_paths: tuple[Path, ...] = ()
        self._visible_paths: tuple[Path, ...] = ()
        self._sort_mode = "modified"
        self._view_mode = "list"
        self._query = ""
        self._loading = False
        self._selected_path: Path | None = None

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._apply_filter_and_sort)

        self._build_ui()
        self._connect_repository()

        for document in repository:
            self._add_document(document)
        self._apply_filter_and_sort()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 26)
        root.setSpacing(12)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(10)
        logo_label = QLabel()
        logo = QPixmap(str(icon_path("riqatonydesk.png")))
        if not logo.isNull():
            logo_label.setPixmap(
                logo.scaled(
                    42,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        logo_label.setFixedSize(46, 46)
        heading_row.addWidget(logo_label)
        heading = QLabel("<h1>RiqatonyDesk</h1>")
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        root.addLayout(heading_row)

        tip = QLabel(
            "Tip: Drag and drop RTF (.rtf) files anywhere onto the Dashboard to "
            "import them into your Workspace, or use File → Import File into Workspace..."
        )
        tip.setWordWrap(True)
        root.addWidget(tip)

        self.summary_label = QLabel()
        root.addWidget(self.summary_label)

        # Search occupies its own full-width row.
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search RTF files by title or filename…")
        self.search_input.setClearButtonEnabled(True)
        style_line_edit(self.search_input)
        self.search_input.textChanged.connect(self._schedule_search)
        root.addWidget(self.search_input)

        # All dashboard actions sit on one consistent row below search.
        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.new_file_button = style_button(
            QPushButton("New File"), role="primary"
        )
        self.new_folder_button = style_button(QPushButton("New Folder"))

        self.new_file_button.setToolTip(
            "Create a RTF file in the workspace root"
        )
        self.new_folder_button.setToolTip(
            "Create a subfolder in the workspace root"
        )

        self.new_file_button.clicked.connect(self.create_file_requested)
        self.new_folder_button.clicked.connect(self.create_folder_requested)

        controls.addWidget(self.new_file_button)
        controls.addWidget(self.new_folder_button)
        controls.addStretch(1)

        # Dashboard controls remain right aligned and ordered:
        # Grid/List View | Refresh | Sort.
        self.refresh_button = style_button(
            QPushButton("Refresh"),
            size="compact",
            minimum_width=88,
        )
        self.view_toggle_button = style_button(
            QPushButton("Grid View"),
            size="compact",
            minimum_width=88,
        )
        self.refresh_button.setToolTip("Refresh the workspace")
        self.view_toggle_button.setToolTip(
            "Switch between list and grid views"
        )
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.view_toggle_button.clicked.connect(self.toggle_view_mode)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(self.SORT_LABELS.keys())
        self.sort_combo.setCurrentText("Last Modified")
        style_combo_box(self.sort_combo, minimum_width=132)
        self.sort_combo.setMaximumWidth(150)
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)

        controls.addWidget(self.view_toggle_button)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.sort_combo)
        root.addLayout(controls)
        self._refresh_control_icons()

        self.unsaved_banner = QLabel()
        self.unsaved_banner.setWordWrap(True)
        self.unsaved_banner.setFrameShape(QFrame.Shape.StyledPanel)
        self.unsaved_banner.hide()
        root.addWidget(self.unsaved_banner)

        self.loading_indicator = LoadingIndicator(self, compact=True)
        self.loading_indicator.start(
            "Preparing your workspace…",
            "Scanning folders and RTF files. Large workspaces may take a moment.",
        )

        self.empty_label = QLabel()
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.empty_label.hide()
        root.addWidget(self.empty_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        # Phase 1 touch contract: kinetic scrolling belongs only to the main
        # Dashboard. Stationary touches remain taps; finger movement scrolls
        # the Dashboard and must never become a document drag.
        QScroller.grabGesture(
            self.scroll.viewport(),
            QScroller.ScrollerGestureType.TouchGesture,
        )

        self.view_stack = CurrentPageStack(self.scroll)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.view_stack.addWidget(self.list_host)

        self.grid_host = QWidget()
        self.grid_layout = FlowLayout(self.grid_host, margin=0, spacing=12)
        self.view_stack.addWidget(self.grid_host)

        self.scroll.setWidget(self.view_stack)

        # The content stack is always the expanding part of the Dashboard.
        # Keeping it visible during startup prevents the heading, tip, search,
        # and controls from spreading vertically across the window.
        self.content_stack = QStackedWidget(self)

        loading_page = QWidget(self.content_stack)
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(0)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        loading_layout.addWidget(
            self.loading_indicator,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        loading_layout.addStretch(1)

        self.content_stack.addWidget(loading_page)
        self.content_stack.addWidget(self.scroll)
        root.addWidget(self.content_stack, 1)

    def set_loading(self, loading: bool, message: str | None = None) -> None:
        """Show or hide the in-dashboard workspace preparation panel."""
        self._loading = loading
        for control in (
            self.search_input,
            self.new_file_button,
            self.new_folder_button,
            self.refresh_button,
            self.view_toggle_button,
            self.sort_combo,
        ):
            control.setEnabled(not loading)

        if loading:
            self.loading_indicator.start(
                message or "Preparing your workspace…",
                "Scanning folders and RTF files. Large workspaces may take a moment.",
            )
            self.empty_label.hide()
            self.summary_label.hide()
            self.content_stack.setCurrentIndex(0)
        else:
            self.loading_indicator.stop()
            self.summary_label.show()
            self.content_stack.setCurrentWidget(self.scroll)
            self._apply_filter_and_sort()

    def set_loading_detail(self, detail: str) -> None:
        if self._loading:
            self.loading_indicator.set_detail(detail)

    def _connect_repository(self) -> None:
        self.repository.document_added.connect(self._add_document)
        self.repository.document_removed.connect(self._remove_document)
        self.repository.document_changed.connect(self._update_document)
        self.repository.document_path_changed.connect(self._on_document_path_changed)
        self.repository.repository_reset.connect(self._reset)
        self.repository.dirty_count_changed.connect(self._update_unsaved_banner)

    def _connect_card(self, card: DashboardCard) -> None:
        card.open_requested.connect(self.document_open_requested)
        card.view_only_requested.connect(self.document_view_only_requested)
        card.selected_requested.connect(self._select_card)
        card.remove_requested.connect(self.document_remove_requested)

    def _select_card(self, document: DocumentEntry) -> None:
        self._selected_path = document.path
        for cards in (self._list_cards, self._grid_cards):
            for path, card in cards.items():
                card.set_selected(path == self._selected_path)

    def _control_icon_root(self) -> Path | None:
        app = QApplication.instance()
        if app is None:
            return None
        scheme = "light" if app.palette().color(QPalette.ColorRole.Base).lightness() >= 140 else "dark"
        icon_set = str(app.property("riqatony_desk_icon_set") or "new")
        family = {
            "original": "ribbon-icons-original",
            "classic": "ribbon-icons-classic",
            "aero": "ribbon-icons-aero",
        }.get(icon_set, "ribbon-icons")
        return Path(__file__).resolve().parents[2] / "assets" / family / scheme

    def _refresh_control_icons(self) -> None:
        root = self._control_icon_root()
        if root is None:
            return
        view_icon = "list-view" if self._view_mode == "grid" else "grid-view"
        for button, name in (
            (self.new_file_button, "new"),
            (self.new_folder_button, "new-folder"),
            (self.view_toggle_button, view_icon),
        ):
            path = root / f"{name}.png"
            button.setIcon(QIcon(str(path)) if path.is_file() else QIcon())

    def refresh_theme(self) -> None:
        self._refresh_control_icons()
        for cards in (self._list_cards, self._grid_cards):
            for card in cards.values():
                card.refresh_icons()
                card.update()  # Repaint palette-based surface without recreating card.

    def _add_document(self, document: DocumentEntry) -> None:
        if document.external:
            return
        if document.path in self._list_cards:
            return

        list_card = DashboardCard(
            document,
            self.list_host,
            view_mode="list",
            touch_moves_scroll_only=True,
            palette_surface=True,
        )
        grid_card = DashboardCard(
            document,
            self.grid_host,
            view_mode="grid",
            touch_moves_scroll_only=True,
            palette_surface=True,
        )
        self._connect_card(list_card)
        self._connect_card(grid_card)

        # A newly discovered document may not match the active search.
        list_card.hide()
        grid_card.hide()

        self._list_cards[document.path] = list_card
        self._grid_cards[document.path] = grid_card
        self._layout_signatures[document.path] = self._layout_signature(document)

        state = self.states.ensure(document.path)
        state.dashboard_card = list_card
        state.dashboard_grid_card = grid_card
        self._apply_filter_and_sort()

    def _remove_document(self, document: DocumentEntry) -> None:
        list_card = self._list_cards.pop(document.path, None)
        grid_card = self._grid_cards.pop(document.path, None)
        self._layout_signatures.pop(document.path, None)

        if list_card is not None:
            self.list_layout.removeWidget(list_card)
            list_card.deleteLater()
        if grid_card is not None:
            self.grid_layout.removeWidget(grid_card)
            grid_card.deleteLater()

        self._apply_filter_and_sort()

    def _update_document(self, document: DocumentEntry) -> None:
        """
        Refresh card content without disturbing layout for runtime-only changes.

        Running and dirty state changes are frequent and do not affect Title,
        Created, Modified, or search ordering. Rebuilding hundreds of cards for
        those changes caused the Grid view to jump vertically on Launch/Stop.
        """
        list_card = self._list_cards.get(document.path)
        grid_card = self._grid_cards.get(document.path)
        if list_card is None or grid_card is None:
            self._add_document(document)
            return

        old_signature = self._layout_signatures.get(document.path)
        new_signature = self._layout_signature(document)
        self._layout_signatures[document.path] = new_signature

        list_card.refresh()
        grid_card.refresh()

        if old_signature != new_signature:
            self._apply_filter_and_sort()
        else:
            total = sum(
                1 for document in self.repository if not document.external
            )
            visible_count = sum(
                1
                for document in self.repository.search(self._query)
                if not document.external
            )
            self.summary_label.setText(
                f"Showing {visible_count} of {total} RTF files"
            )
            self._update_unsaved_banner(len(self.repository.dirty))

    def _on_document_path_changed(self, document: DocumentEntry, old_path: Path) -> None:
        """Re-key both persistent presentations after rename or move."""
        old_key = self.repository.normalize_path(old_path)
        self._layout_signatures.pop(old_key, None)
        state = self.states.ensure(document.path)

        list_card = self._list_cards.pop(old_key, None)
        grid_card = self._grid_cards.pop(old_key, None)

        if list_card is None:
            list_card = state.dashboard_card
        if grid_card is None:
            grid_card = state.dashboard_grid_card

        if list_card is None or grid_card is None:
            if list_card is not None:
                list_card.deleteLater()
            if grid_card is not None:
                grid_card.deleteLater()
            self._add_document(document)
            return

        for card in (list_card, grid_card):
            card.document = document
            card.refresh()

        self._list_cards[document.path] = list_card
        self._grid_cards[document.path] = grid_card
        self._layout_signatures[document.path] = self._layout_signature(document)
        state.dashboard_card = list_card
        state.dashboard_grid_card = grid_card
        # Re-key the existing layout/visibility records; they still refer
        # to the same two retained card widgets after a move or rename.
        self._layout_paths = tuple(
            document.path if path == old_key else path for path in self._layout_paths
        )
        self._visible_paths = tuple(
            document.path if path == old_key else path for path in self._visible_paths
        )
        self._apply_filter_and_sort()

    def _reset(self) -> None:
        for card in (
            *self._list_cards.values(),
            *self._grid_cards.values(),
        ):
            card.deleteLater()
        # Reset both views' membership before the next repository snapshot.
        for card in self._list_cards.values():
            self.list_layout.removeWidget(card)
        self._list_cards.clear()
        self._grid_cards.clear()
        self._layout_signatures.clear()
        self.grid_layout.clear()
        self._layout_paths = ()
        self._visible_paths = ()
        self._apply_filter_and_sort()

    @staticmethod
    def _layout_signature(document: DocumentEntry) -> tuple[object, ...]:
        """
        Return only fields capable of changing search or sort placement.

        Transient fields such as dirty and loaded deliberately do not
        participate.
        """
        return (
            document.search_title,
            document.search_filename,
            document.created,
            document.modified,
        )

    def _set_drop_highlight(self, active: bool) -> None:
        if active:
            colour = self.palette().color(QPalette.ColorRole.Highlight).name()
            desired_style = f"DashboardWidget {{ border: 2px solid {colour}; }}"
        else:
            desired_style = ""
        if self.styleSheet() != desired_style:
            self.setStyleSheet(desired_style)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if external_rtf_paths(event.mimeData()):
            self._set_drop_highlight(True)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            self._set_drop_highlight(False)
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if external_rtf_paths(event.mimeData()):
            self._set_drop_highlight(True)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            self._set_drop_highlight(False)
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drop_highlight(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = external_rtf_paths(event.mimeData())
        self._set_drop_highlight(False)
        if not paths:
            event.ignore()
            return
        QTimer.singleShot(
            0,
            lambda dropped=paths: self.external_files_dropped.emit(dropped),
        )
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def _schedule_search(self, text: str) -> None:
        self._query = text.casefold().strip()
        self._search_timer.start()

    def _on_sort_changed(self, label: str) -> None:
        self._sort_mode = self.SORT_LABELS.get(label, "modified")
        self.sort_mode_changed.emit(self._sort_mode)
        self._apply_filter_and_sort()

    def toggle_view_mode(self) -> None:
        self.set_view_mode("grid" if self._view_mode == "list" else "list")

    def set_view_mode(self, mode: str) -> None:
        if mode not in self.VALID_VIEW_MODES:
            mode = "list"
        changed = mode != self._view_mode
        self._view_mode = mode
        self.view_toggle_button.setText(
            "List View" if mode == "grid" else "Grid View"
        )
        self._refresh_control_icons()

        # Both card collections are already laid out. Switching is therefore
        # a constant-time stacked-page change with no card reparenting.
        self.view_stack.setCurrentWidget(
            self.grid_host if mode == "grid" else self.list_host
        )
        # The stack's currentChanged handler already notifies the scroll area.
        if changed:
            self.view_mode_changed.emit(mode)

    def view_mode(self) -> str:
        return self._view_mode


    def set_sort_mode(self, mode: str) -> None:
        if mode not in self.repository.VALID_SORT_MODES:
            mode = "modified"
        self._sort_mode = mode
        for label, value in self.SORT_LABELS.items():
            if value == mode:
                self.sort_combo.blockSignals(True)
                self.sort_combo.setCurrentText(label)
                self.sort_combo.blockSignals(False)
                break
        self._apply_filter_and_sort()

    def set_search_text(self, text: str) -> None:
        self.search_input.setText(text)

    def _detach_all_cards_from_layouts(self) -> None:
        """Legacy full-detach hook, retained for adapter compatibility.

        Search and sorting deliberately never call this: they retain cards
        and update visibility or order. Explicit callers can still request
        the original complete detach without deleting their widgets.
        """
        for card in self._list_cards.values():
            self.list_layout.removeWidget(card)
            card.hide()
        for card in self._grid_cards.values():
            self.grid_layout.removeWidget(card)
            card.hide()
        self.list_layout.invalidate()
        self.grid_layout.invalidate()
        self._layout_paths = ()
        self._visible_paths = ()

    def _sync_card_layout_order(self, paths: tuple[Path, ...]) -> None:
        """Change widget order only when the repository sort order changes.

        The VBox retains native Qt layout semantics. The custom FlowLayout
        can reorder its existing QWidgetItems directly, avoiding another
        complete remove/add cycle for the grid's 700+ widgets.
        """
        for path in self._layout_paths:
            card = self._list_cards.get(path)
            if card is not None:
                self.list_layout.removeWidget(card)
        for path in paths:
            card = self._list_cards.get(path)
            if card is not None:
                self.list_layout.addWidget(card)
        self.grid_layout.replace_widgets([
            self._grid_cards[path]
            for path in paths if path in self._grid_cards
        ])
        self._layout_paths = paths

    def _batch_card_visibility(self, hide_paths: set[Path], show_paths: set[Path]) -> None:
        """Coalesce Qt layout/paint work for bulk Dashboard visibility changes.

        Search reset and initial workspace population can reveal hundreds of
        existing cards in both views. Temporarily suspend layout management
        and host painting while changing QWidget visibility; afterwards Qt
        receives one explicit geometry refresh from the caller. This leaves
        card ownership, retained layout items and source ordering intact.
        """
        layouts = (self.list_layout, self.grid_layout)
        hosts = (self.list_host, self.grid_host)
        layout_enabled = tuple(layout.isEnabled() for layout in layouts)
        host_updates = tuple(host.updatesEnabled() for host in hosts)
        try:
            for host in hosts:
                host.setUpdatesEnabled(False)
            for layout in layouts:
                layout.setEnabled(False)

            for path in hide_paths:
                for cards in (self._list_cards, self._grid_cards):
                    card = cards.get(path)
                    if card is not None:
                        card.hide()
            for path in show_paths:
                for cards in (self._list_cards, self._grid_cards):
                    card = cards.get(path)
                    if card is not None:
                        card.show()
        finally:
            # Restore exact previous states, even if a widget raises.
            for layout, enabled in zip(layouts, layout_enabled):
                layout.setEnabled(enabled)
            for host, updates in zip(hosts, host_updates):
                host.setUpdatesEnabled(updates)

    def _apply_filter_and_sort(self) -> None:
        if self._loading:
            return

        # Keep ordering independent of search. Both layouts contain all
        # documents, with nonmatching cards hidden in place. In particular,
        # clearing a search no longer detaches and reinserts every card.
        all_entries = [
            document for document in self.repository if not document.external
        ]
        ordered_all = self.repository.sorted(all_entries, self._sort_mode)
        all_paths = tuple(document.path for document in ordered_all)
        matched = [
            document for document in self.repository.search(self._query)
            if not document.external
        ]
        ordered_visible = self.repository.sorted(matched, self._sort_mode)
        visible_paths = tuple(document.path for document in ordered_visible)

        order_changed = all_paths != self._layout_paths
        visibility_changed = visible_paths != self._visible_paths
        if order_changed:
            self._sync_card_layout_order(all_paths)

        if order_changed or visibility_changed:
            previously_visible = set(self._visible_paths)
            now_visible = set(visible_paths)
            if previously_visible != now_visible:
                self._batch_card_visibility(
                    previously_visible - now_visible,
                    now_visible - previously_visible,
                )
            self._visible_paths = visible_paths

            # One geometry refresh after the complete structural/visibility
            # change. A repeated query or no-op sort touches no layouts.
            self.view_stack.invalidate_measurements()
            self.list_layout.invalidate()
            self.grid_layout.invalidate()
            self.list_layout.activate()
            self.grid_host.updateGeometry()
            self.grid_host.update()
            self.view_stack.updateGeometry()

        total = sum(1 for document in self.repository if not document.external)
        visible_count = len(ordered_visible)
        self.summary_label.setText(
            f"Showing {visible_count} of {total} RTF files"
        )

        self.scroll.setVisible(True)
        self.empty_label.setVisible(not ordered_visible)
        if total == 0:
            self.empty_label.setText(
                "No RTF files were found in the library."
            )
        elif not ordered_visible:
            self.empty_label.setText(
                "No RTF files match the current search."
            )

        self._update_unsaved_banner(len(self.repository.dirty))

    def _update_unsaved_banner(self, count: int) -> None:
        self.unsaved_banner.setVisible(count > 0)
        if count:
            self.unsaved_banner.setText(
                f"You have unsaved changes in {count} "
                f"document{'s' if count != 1 else ''}."
            )
