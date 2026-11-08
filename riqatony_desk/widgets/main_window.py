# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application window for RiqatonyDesk.

The workspace/lifecycle scaffold follows authoritative Plus implementation; RTF commands are
provided by the active EditorPage, which is the sole managed-editor boundary.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QIcon,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabBar,
    QLabel,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
)

from riqatony_desk import APP_NAME
from riqatony_desk.app_constants import GITHUB_URL, ISSUES_URL, RTF_EXTENSIONS
from riqatony_desk.controllers.editor_manager import EditorManager
from riqatony_desk.controllers.file_actions import FileActionsController
from riqatony_desk.models.document import DocumentEntry
from riqatony_desk.models.document_repository import DocumentRepository
from riqatony_desk.models.document_state_store import DocumentStateStore
from riqatony_desk.services.config_service import ConfigService
from riqatony_desk.services.desktop_launcher import DesktopLauncher
from riqatony_desk.services.filesystem_watcher import FilesystemWatcher
from riqatony_desk.services.project_registry import ProjectRegistry
from riqatony_desk.services.runtime_paths import RuntimePaths
from riqatony_desk.widgets.dialogs.about_dialog import AboutDialog
from riqatony_desk.widgets.dialogs.closing_dialog import ClosingDialog
from riqatony_desk.widgets.editor_page import EditorPage
from riqatony_desk.widgets.workspace.navigation import NavigationWidget
from riqatony_desk.widgets.dialogs.projects_dialog import ProjectsDialog
from riqatony_desk.widgets.dialogs.shortcuts_dialog import ShortcutsDialog
from riqatony_desk.widgets.theme import apply_theme, effective_scheme
from riqatony_desk.widgets.shell_ribbon import ShellRibbon
from riqatony_desk.widgets.window_parts.document_tabs import DocumentTabsMixin
from riqatony_desk.widgets.window_parts.navigation_history import NavigationHistoryMixin
from riqatony_desk.widgets.window_parts.layout_controls import LayoutControlsMixin
from riqatony_desk.widgets.window_parts.help_actions import HelpActionsMixin


SHUTDOWN_PROFILE_ENV = "RIQATONYDESK_PROFILE_SHUTDOWN"


class MainWindow(DocumentTabsMixin, NavigationHistoryMixin, LayoutControlsMixin, HelpActionsMixin, QMainWindow):
    """Assemble the repository, services, controllers and persistent views."""

    def __init__(
        self,
        library_root: str | Path,
        config: ConfigService,
        project_registry: ProjectRegistry,
        runtime_paths: RuntimePaths,
        parent=None,
        *,
        icon_path: str | Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.library_root = Path(library_root).expanduser().resolve(strict=False)
        self.config = config
        self.project_registry = project_registry
        self.runtime_paths = runtime_paths
        self.package_root = Path(__file__).resolve().parent.parent
        self.icon_path = Path(icon_path) if icon_path else (
            self.package_root / "assets" / "icons" / "riqatonydesk.png"
        )
        if self.icon_path.is_file():
            self.setWindowIcon(QIcon(str(self.icon_path)))

        self.repository = DocumentRepository(self)
        self.states = DocumentStateStore(self.repository, self)
        self.watcher = FilesystemWatcher(
            self.library_root, self.repository, parent=self
        )
        self.desktop_launcher = DesktopLauncher(self.runtime_paths, self)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.navigation = NavigationWidget(
            self.library_root, self.repository, self.states, self.splitter
        )

        # Tabs are a thin presentation layer over the existing EditorManager/stack.
        # Open RTF documents receive persistent tabs. Dashboard/folder navigation
        # surfaces use one temporary tab while consulted, then disappear as soon
        # as a document becomes active.
        self.content_host = QWidget(self.splitter)
        self.content_host.setMinimumWidth(0)
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.document_tabs = QTabBar(self.content_host)
        self.document_tabs.setDocumentMode(True)
        self.document_tabs.setMinimumWidth(0)
        self.document_tabs.setTabsClosable(True)
        self.document_tabs.setMovable(False)
        self.document_tabs.setExpanding(False)
        self.document_tabs.setUsesScrollButtons(True)
        self.document_tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.document_tabs.setVisible(False)
        self.stack = QStackedWidget(self.content_host)
        self.stack.setMinimumWidth(0)
        self.content_layout.addWidget(self.document_tabs)
        self.content_layout.addWidget(self.stack, 1)

        self.splitter.setMinimumWidth(0)
        self.splitter.addWidget(self.navigation)
        self.splitter.addWidget(self.content_host)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setHandleWidth(8)
        self.splitter.setOpaqueResize(False)

        # The Plus workspace contract places one shell-owned command surface
        # across the whole window, with the sidebar/content splitter below it.
        # Document editors supply capabilities/state, never application chrome.
        self.central_host = QWidget(self)
        self.central_host.setMinimumSize(0, 0)
        self.central_layout = QVBoxLayout(self.central_host)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.tabbed_container = QWidget(self.central_host)
        self.tabbed_container.setMinimumWidth(0)
        self.tabbed_layout = QVBoxLayout(self.tabbed_container)
        self.tabbed_layout.setContentsMargins(0, 0, 0, 0)
        self.tabbed_layout.setSpacing(0)
        self.central_layout.addWidget(self.tabbed_container)
        self.central_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(self.central_host)

        self.editor_manager = EditorManager(
            self.library_root,
            self.repository,
            self.states,
            self.stack,
            self.config,
            self,
        )
        self.file_actions = FileActionsController(
            self.library_root,
            self.repository,
            self.states,
            self.editor_manager,
            self.desktop_launcher,
            watcher=self.watcher,
            config_directory=self.config.path.parent,
            parent_widget=self,
            parent=self,
        )

        self._closing = False
        self._repair_navigation_after_scan = False
        self._startup_scan_pending = True
        self._startup_open_requested = False
        self._pending_open_path: Path | None = None
        self.about_dialog: AboutDialog | None = None
        self.shortcuts_dialog: ShortcutsDialog | None = None
        self.quick_tour_dialog: QWizard | None = None
        # Temporary F10 viewing mode. The user's independent visibility choices
        # are captured and restored; Focused Mode does not rewrite them.
        self._collapsed_mode_restore: dict[str, object] | None = None
        # Browser-style context history for the dedicated mouse Back button.
        # Navigation signals are coalesced so Tabs Disabled document switches do
        # not expose the EditorManager's internal Dashboard close surface.
        self._navigation_history: list[str] = []
        self._navigation_current = "dashboard"
        self._navigation_pending: str | None = None
        self._navigation_record_scheduled = False
        self._navigation_back_in_progress = False

        self._status_label = QLabel("Ready.")
        status = QStatusBar(self)
        status.addWidget(self._status_label, 1)
        self.setStatusBar(status)

        self._build_menu_bar()
        self._create_tabbed_toolbar()
        self._connect_signals()
        self._sync_tabs_mode_ui()
        self._restore_window_state()
        self._apply_active_project_state()
        self._update_window_title()
        self.watcher.start(initial_scan=True)
        self._update_action_states()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def _command(
        self,
        text: str,
        slot,
        shortcut=None,
        *,
        checkable: bool = False,
    ) -> QAction:
        action = QAction(text, self)
        action.setCheckable(checkable)
        action.triggered.connect(slot)
        if shortcut:
            sequence = shortcut if isinstance(shortcut, QKeySequence) else QKeySequence(shortcut)
            action.setShortcut(sequence)
        clean = text.replace("&", "").replace("…", "").strip()
        rendered = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText).strip()
        action.setToolTip(f"{clean} — {rendered}" if rendered else clean)
        return action

    def _build_menu_bar(self) -> None:
        self.new_action = self._command(
            "New File…", self._new_rtf_file, QKeySequence.StandardKey.New
        )
        self.new_window_action = self._command(
            "New Window…", self._new_window, "Ctrl+Alt+Shift+N"
        )
        self.new_folder_action = self._command(
            "New Folder…", self._new_folder, "Ctrl+Shift+N"
        )
        self.dashboard_action = self._command(
            "Dashboard", self.editor_manager.show_dashboard
        )
        # Context-sensitive tab/navigation shortcuts are window-owned rather
        # than attached to the Dashboard menu command: clicking Dashboard
        # must never close a document tab.
        self.close_context_action = self._command(
            "Close Tab / Dashboard", self._close_context, "Ctrl+W"
        )
        self.open_context_tab_action = self._command(
            "Open Context Tab", self._open_context_tab, "Ctrl+T"
        )
        self.addAction(self.close_context_action)
        self.addAction(self.open_context_tab_action)
        self.manage_workspaces_action = self._command(
            "Open / Manage Workspaces…", self._show_projects,
            QKeySequence.StandardKey.Open,
        )
        self.import_file_action = self._command(
            "Import File into Workspace...", self._import_file_into_workspace, "Ctrl+Alt+Shift+I"
        )
        self.open_external_file_action = self._command(
            "Open External File...", self._open_external_file, "Ctrl+Alt+Shift+O"
        )
        self.refresh_action = self._command(
            "Refresh Workspace", self._refresh_workspace, "Ctrl+Shift+F5"
        )
        self.exit_action = self._command(
            "Exit", self.close, QKeySequence.StandardKey.Quit
        )

        self.list_action = self._command(
            "List View",
            lambda: self._set_dashboard_view_mode("list"),
            checkable=True,
        )
        self.grid_action = self._command(
            "Grid View",
            lambda: self._set_dashboard_view_mode("grid"),
            checkable=True,
        )
        dashboard_group = QActionGroup(self)
        dashboard_group.setExclusive(True)
        dashboard_group.addAction(self.list_action)
        dashboard_group.addAction(self.grid_action)
        self.list_action.setToolTip("Dashboard — List View")
        self.grid_action.setToolTip("Dashboard — Grid View")
        self.toggle_dashboard_view_action = self._command(
            "Toggle List/Grid View",
            self._toggle_dashboard_view_mode,
            "Ctrl+Alt+Shift+V",
        )
        self.sidebar_action = self._command(
            "Show Sidebar", self._toggle_sidebar, "F9", checkable=True
        )
        self.sidebar_action.setChecked(True)
        sidebar_position = str(self.config.get("sidebar_position", "left"))
        if sidebar_position not in {"left", "right"}:
            sidebar_position = "left"
        self.sidebar_position_actions: dict[str, QAction] = {}
        sidebar_position_group = QActionGroup(self)
        sidebar_position_group.setExclusive(True)
        for value, label in (("left", "Dock to Left"), ("right", "Dock to Right")):
            action = self._command(
                label,
                lambda _checked=False, selected=value: self._set_sidebar_position(selected),
                checkable=True,
            )
            action.setChecked(value == sidebar_position)
            sidebar_position_group.addAction(action)
            self.sidebar_position_actions[value] = action
        self.left_sidebar_action = self.sidebar_position_actions["left"]
        self.right_sidebar_action = self.sidebar_position_actions["right"]
        self.left_sidebar_action.setToolTip("Sidebar — Dock to Left")
        self.right_sidebar_action.setToolTip("Sidebar — Dock to Right")
        self.toggle_sidebar_position_action = self._command(
            "Toggle Sidebar Position", self._toggle_sidebar_position, "Shift+F9"
        )
        self.addAction(self.toggle_sidebar_position_action)
        self.status_bar_action = self._command(
            "Show Status", self._toggle_status_bar,
            "Ctrl+Alt+Shift+S", checkable=True,
        )
        self.status_bar_action.setChecked(
            bool(self.config.get("show_status_bar", True))
        )
        self.statusBar().setVisible(self.status_bar_action.isChecked())
        self.fullscreen_action = self._command(
            "Full Screen", self._toggle_fullscreen, "F11", checkable=True
        )

        self.previous_file_action = self._command(
            "Previous File",
            lambda: self.navigation.navigate_adjacent_document(-1),
            "Ctrl+Up",
        )
        self.next_file_action = self._command(
            "Next File",
            lambda: self.navigation.navigate_adjacent_document(1),
            "Ctrl+Down",
        )
        for action in (
            self.previous_file_action,
            self.next_file_action,
            self.toggle_dashboard_view_action,
        ):
            self.addAction(action)

        current_theme = str(self.config.get("app_theme", "light"))
        self.theme_actions: dict[str, QAction] = {}
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        for value, label in (
            ("light", "Light"),
            ("dark", "Dark"),
            ("system", "System"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_theme(selected),
                checkable=True,
            )
            action.setChecked(value == current_theme)
            theme_group.addAction(action)
            self.theme_actions[value] = action
        self.theme_actions["light"].setToolTip("Theme — Light")
        self.theme_actions["dark"].setToolTip("Theme — Dark")
        self.theme_actions["system"].setToolTip("Theme — System")

        current_icons = str(self.config.get("editor_icon_set", "new"))
        QApplication.instance().setProperty("riqatony_desk_icon_set", current_icons)
        self.icon_actions: dict[str, QAction] = {}
        icon_group = QActionGroup(self)
        icon_group.setExclusive(True)
        for value, label in (
            ("original", "Riqa Icons Heritage"),
            ("classic", "Riqa Icons Humility"),
            ("new", "Riqa Icons Harmony"),
            ("aero", "Riqa Icons Halcyon"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_icon_set(selected),
                checkable=True,
            )
            action.setChecked(value == current_icons)
            icon_group.addAction(action)
            self.icon_actions[value] = action

        launch = str(self.config.get("app_launch_screen", "dashboard"))
        self.launch_actions: dict[str, QAction] = {}
        launch_group = QActionGroup(self)
        launch_group.setExclusive(True)
        for value, label in (
            ("dashboard", "Dashboard"),
            ("last_file", "Last File"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_launch_screen(selected),
                checkable=True,
            )
            action.setChecked(value == launch)
            launch_group.addAction(action)
            self.launch_actions[value] = action
        self.launch_actions["dashboard"].setToolTip("Launch Screen — Dashboard")
        self.launch_actions["last_file"].setToolTip("Launch Screen — Last File")

        tabs_enabled = bool(self.config.get("tabs_enabled", True))
        self.tabs_actions: dict[str, QAction] = {}
        tabs_group = QActionGroup(self)
        tabs_group.setExclusive(True)
        for value, label in (
            (True, "Tabs Enabled"),
            (False, "Tabs Disabled"),
        ):
            action = self._command(
                label,
                lambda _checked=False, enabled=value:
                    self._set_tabs_enabled(enabled),
                (None if value else "Ctrl+Alt+Shift+T"),
                checkable=True,
            )
            action.setChecked(value == tabs_enabled)
            tabs_group.addAction(action)
            self.tabs_actions["enabled" if value else "disabled"] = action
        self.tabs_actions["enabled"].setToolTip("File Launch — Tabs Enabled")
        self.tabs_actions["disabled"].setToolTip("File Launch — Tabs Disabled")

        duplicate_policy = str(self.config.get("dirty_duplicate_action", "ask")).lower()
        if duplicate_policy not in {"ask", "current", "saved"}:
            duplicate_policy = "ask"
        self.dirty_duplicate_actions: dict[str, QAction] = {}
        dirty_duplicate_group = QActionGroup(self)
        dirty_duplicate_group.setExclusive(True)
        for value, label in (
            ("ask", "Ask Every Time"),
            ("current", "Duplicate Current Document"),
            ("saved", "Duplicate Last Saved Version"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_dirty_duplicate_action(selected),
                checkable=True,
            )
            action.setChecked(value == duplicate_policy)
            dirty_duplicate_group.addAction(action)
            self.dirty_duplicate_actions[value] = action

        external_policy = str(self.config.get("dirty_external_action", "ask")).lower()
        if external_policy not in {"ask", "save", "saved"}:
            external_policy = "ask"
        self.dirty_external_actions: dict[str, QAction] = {}
        dirty_external_group = QActionGroup(self)
        dirty_external_group.setExclusive(True)
        for value, label in (
            ("ask", "Ask Every Time"),
            ("save", "Save Changes and Open"),
            ("saved", "Open Last Saved Version"),
        ):
            action = self._command(
                label,
                lambda _checked=False, selected=value:
                    self._set_dirty_external_action(selected),
                checkable=True,
            )
            action.setChecked(value == external_policy)
            dirty_external_group.addAction(action)
            self.dirty_external_actions[value] = action

        self.app_launch_toggle_action = self._command(
            "Launch Screen",
            self._toggle_launch_screen_mode,
        )
        self.app_dashboard_toggle_action = self._command(
            "View List / Grid",
            self._toggle_dashboard_view_mode,
        )
        self.app_tabs_toggle_action = self._command(
            "Tabs Enabled / Disabled",
            self._toggle_tabs_mode,
        )

        self.shortcuts_action = self._command(
            "Keyboard Shortcuts", self._show_shortcuts, "Ctrl+Shift+/"
        )
        self.docs_action = self._command(
            "Documentation", self._open_documentation,
            QKeySequence.StandardKey.HelpContents,
        )
        self.github_action = self._command(
            "GitHub Repository",
            lambda: self.desktop_launcher.open_url(GITHUB_URL),
        )
        self.issue_action = self._command(
            "Raise an Issue",
            lambda: self.desktop_launcher.open_url(ISSUES_URL),
        )
        self.about_action = self._command(
            "About RiqatonyDesk", self._show_about_dialog
        )
        self.about_action.setMenuRole(QAction.MenuRole.AboutRole)
        self._build_editor_shell_actions()

        bar = self.menuBar()
        # Ricopad's platform-menu contract is explicit: request the native
        # menu path so Plasma's Global Menu / Menu Only integration can export
        # this one authoritative Plus application menu.
        bar.setNativeMenuBar(True)
        self._build_static_menus(bar)
        bar.show()
        self._refresh_action_icons()

    def _editor_action(self, name: str):
        page = self._current_page()
        return page.editor_action(name) if page is not None else None

    def _trigger_editor_action(self, name: str) -> None:
        page = self._current_page()
        if page is not None:
            page.trigger_editor_action(name)
        self._sync_editor_actions()

    def _editor_call(self, method: str, *args) -> None:
        page = self._current_page()
        if page is not None:
            callback = getattr(page, method, None)
            if callable(callback):
                callback(*args)
            else:
                page.call_editor(method, *args)
        self._sync_editor_actions()

    def adjust_zoom_from_wheel(self, angle_delta_y) -> None:
        self._editor_call("adjust_zoom_from_wheel", angle_delta_y)

    def _focus_context_search(self, _checked=False) -> None:
        """Ctrl+F toggles document Find when focused there, or targets navigation search."""
        page = self._current_page()
        if page is not None:
            page.call_editor("toggle_find_panel", False)
            self._sync_editor_actions()
            return

        search = getattr(self.stack.currentWidget(), "search_input", None)
        if search is not None:
            search.setFocus(Qt.FocusReason.ShortcutFocusReason)
            search.selectAll()
        self._sync_editor_actions()

    def _focus_replace(self, _checked=False) -> None:
        page = self._current_page()
        if page is not None:
            page.call_editor("toggle_find_panel", True)
        self._sync_editor_actions()

    def _editor_command(self, text: str, editor_action: str, shortcut=None, *, checkable=False) -> QAction:
        return self._command(
            text,
            lambda _checked=False, name=editor_action: self._trigger_editor_action(name),
            shortcut,
            checkable=checkable,
        )

    def _build_editor_shell_actions(self) -> None:
        self.save_action = self._command("Save", self._save_current, QKeySequence.StandardKey.Save)
        self.save_as_action = self._command("Save As…", lambda: self._editor_call("save_as_file"))
        self.save_new_action = self._command("Save and New", lambda: self._save_and_new(self._current_page()) if self._current_page() else None, "Ctrl+Shift+S")
        self.save_dashboard_action = self._command("Save and Dashboard", lambda: self._save_and_dashboard(self._current_page()) if self._current_page() else None, "Ctrl+Shift+W")
        self.save_exit_action = self._command("Save and Exit", lambda: self._save_and_exit(self._current_page()) if self._current_page() else None, "Ctrl+Shift+Q")
        self.properties_action = self._command("Properties", lambda: self._editor_call("show_properties_dialog"), "F4")
        self.external_editor_action = self._command("Open in External Editor", self._open_current_external, "Ctrl+Shift+E")
        self.rename_file_action = self._command("Rename File…", self._rename_current, "F2")
        self.delete_file_action = self._command("Delete File", self._delete_current_file)
        self.duplicate_action = self._command("Duplicate File…", self._duplicate_current, "Ctrl+Shift+D")
        self.open_document_folder_action = self._command("Open Containing Folder", self._open_current_document_folder, "Ctrl+Shift+O")
        self.print_action = self._command("Print…", lambda: self._editor_call("print_document"), QKeySequence.StandardKey.Print)
        self.export_pdf_action = self._command("Export PDF…", lambda: self._editor_call("export_pdf"), "Ctrl+Alt+Shift+P")
        self.page_setup_action = self._command("Page Setup…", lambda: self._editor_call("show_page_setup_dialog"))

        self.undo_action=self._editor_command("Undo","undo_action",QKeySequence.StandardKey.Undo)
        self.redo_action=self._editor_command("Redo","redo_action","Ctrl+Y")
        self.cut_action=self._editor_command("Cut","cut_action",QKeySequence.StandardKey.Cut)
        self.copy_action=self._editor_command("Copy","copy_action",QKeySequence.StandardKey.Copy)
        self.paste_action=self._editor_command("Paste","paste_action",QKeySequence.StandardKey.Paste)
        self.paste_plain_action=self._editor_command("Paste as Plain Text","paste_plain_action","Ctrl+Shift+V")
        self.delete_text_action=self._editor_command("Delete","delete_text_action",QKeySequence.StandardKey.Delete)
        self.duplicate_line_action=self._editor_command("Duplicate Line / Selection","duplicate_line_action","Ctrl+D")
        self.delete_line_action=self._editor_command("Delete Line","delete_line_action","Ctrl+Shift+K")
        self.select_all_action=self._editor_command("Select All","select_all_action",QKeySequence.StandardKey.SelectAll)
        self.search_bar_action=self._command("Find", self._focus_context_search, QKeySequence.StandardKey.Find)
        self.replace_action=self._command("Find and Replace", self._focus_replace, "Ctrl+H")

        self.font_dialog_action=self._editor_command("Font…","font_dialog_action","Ctrl+Shift+F")
        self.increase_font_size_action=self._editor_command("Increase Font Size","increase_font_size_action","Ctrl+Shift+]")
        self.decrease_font_size_action=self._editor_command("Decrease Font Size","decrease_font_size_action","Ctrl+Shift+[")
        self.text_colour_action=self._editor_command("Text Colour…","text_colour_action","Ctrl+Shift+C")
        self.highlight_colour_action=self._editor_command("Highlight Colour…","highlight_colour_action","Ctrl+Shift+H")
        self.clear_highlight_action=self._editor_command("Clear Highlight","clear_highlight_action")
        self.bold_action=self._editor_command("Bold","bold_action",QKeySequence.StandardKey.Bold,checkable=True)
        self.italic_action=self._editor_command("Italic","italic_action",QKeySequence.StandardKey.Italic,checkable=True)
        self.underline_action=self._editor_command("Underline","underline_action",QKeySequence.StandardKey.Underline,checkable=True)
        self.strike_action=self._editor_command("Strikethrough","strike_action","Ctrl+Shift+X",checkable=True)
        self.superscript_action=self._editor_command("Superscript","superscript_action","Ctrl+.",checkable=True)
        self.subscript_action=self._editor_command("Subscript","subscript_action","Ctrl+,",checkable=True)
        self.bullet_action=self._editor_command("Bullet List","bulleted_list_action","Ctrl+Shift+L",checkable=True)
        self.indent_action=self._editor_command("Indent","increase_indent_action","Ctrl+]")
        self.outdent_action=self._editor_command("Outdent","decrease_indent_action","Ctrl+[")
        self.paragraph_action=self._editor_command("Paragraph…","paragraph_action","Ctrl+Shift+P")
        self.clear_formatting_action=self._editor_command("Clear Formatting","clear_formatting_action","Ctrl+Space")
        self.alignment_left_action=self._command("Left",lambda:self._set_alignment(Qt.AlignmentFlag.AlignLeft),"Ctrl+L",checkable=True)
        self.alignment_center_action=self._command("Centre",lambda:self._set_alignment(Qt.AlignmentFlag.AlignHCenter),"Ctrl+E",checkable=True)
        self.alignment_right_action=self._command("Right",lambda:self._set_alignment(Qt.AlignmentFlag.AlignRight),"Ctrl+R",checkable=True)
        self.alignment_justify_action=self._command("Justify",lambda:self._set_alignment(Qt.AlignmentFlag.AlignJustify),"Ctrl+J",checkable=True)
        group=QActionGroup(self); group.setExclusive(True)
        for a in (self.alignment_left_action,self.alignment_center_action,self.alignment_right_action,self.alignment_justify_action): group.addAction(a)
        self.heading_actions={}
        heading_group=QActionGroup(self); heading_group.setExclusive(True)
        for level in range(7):
            label="Normal Paragraph" if level==0 else f"Heading {level}"
            action=self._command(label,lambda _checked=False,n=level:self._set_heading(n),f"Ctrl+Shift+{level}",checkable=True); self.heading_actions[level]=action; heading_group.addAction(action)
        self.line_spacing_actions={}
        spacing_group=QActionGroup(self); spacing_group.setExclusive(True)
        for label,value,shortcut in (("1.0",100,"Ctrl+1"),("1.15",115,"Ctrl+2"),("1.5",150,"Ctrl+3"),("2.0",200,"Ctrl+4")):
            action=self._command(label,lambda _checked=False,n=value:self._set_line_spacing(n),shortcut,checkable=True); self.line_spacing_actions[value]=action; spacing_group.addAction(action)

        self.link_action=self._editor_command("Insert Link…","link_action","Ctrl+K")
        self.edit_link_action=self._editor_command("Edit Link…","edit_link_action")
        self.remove_link_action=self._editor_command("Remove Link","remove_link_action")
        self.rule_action=self._editor_command("Horizontal Rule","horizontal_rule_action","Ctrl+Alt+Shift+H")
        self.image_action=self._editor_command("Image…","image_action","Ctrl+Shift+I")
        self.table_action=self._editor_command("Table…","table_action","Ctrl+Shift+T")
        self.table_row_above_action=self._editor_command("Insert Row Above","table_row_above_action")
        self.table_row_below_action=self._editor_command("Insert Row Below","table_row_below_action")
        self.table_delete_row_action=self._editor_command("Delete Row","table_delete_row_action")
        self.table_column_left_action=self._editor_command("Insert Column Left","table_column_left_action")
        self.table_column_right_action=self._editor_command("Insert Column Right","table_column_right_action")
        self.table_delete_column_action=self._editor_command("Delete Column","table_delete_column_action")
        self.table_delete_action=self._editor_command("Delete Table","table_delete_action")
        self.date_time_action=self._editor_command("Date and Time","insert_date_time_action","F5")
        self.date_action=self._editor_command("Date Only","date_action","Ctrl+;")
        self.time_action=self._editor_command("Time Only","time_action","Ctrl+:")
        self.symbol_action=self._editor_command("Symbol…","symbol_action","Shift+F5")

        self.view_only_action=self._command("Locked Mode", self._toggle_lock_editor_current, "F12", checkable=True)
        self.collapsed_mode_action=self._command("Focused Mode", self._toggle_collapsed_mode, "F10", checkable=True)
        self.file_header_action=self._command("File Header", self._toggle_file_header, "Ctrl+Alt+Shift+F", checkable=True)
        self.file_header_action.setChecked(bool(self.config.get("show_file_header", True)))
        self.word_wrap_action=self._editor_command("Word Wrap","wrap_action","Ctrl+Alt+Shift+W",checkable=True)
        self.editor_canvas_theme_action=self._command(
            "Dark Editor", self._toggle_editor_canvas_light,
            "Ctrl+Alt+Shift+E", checkable=True,
        )
        self.editor_canvas_theme_action.setChecked(not self._canvas_is_light())
        self.zoom_in_action=self._editor_command("Zoom In","zoom_in_action",QKeySequence.StandardKey.ZoomIn)
        self.zoom_out_action=self._editor_command("Zoom Out","zoom_out_action",QKeySequence.StandardKey.ZoomOut)
        self.zoom_reset_action=self._editor_command("Reset Zoom","zoom_reset_action","Ctrl+0")
        self.tab_width_action=self._editor_command("Tab Width…","tab_width_action")
        self.default_font_action=self._editor_command("New Document Defaults…","default_font_action")
        self.quick_start_action=self._command("Quick Tour…",self._show_quick_tour,"Shift+F1")
        self.quick_start_action.setToolTip("Quick Tour… — Shift+F1")
        self.next_document_tab_action=self._command("Next Tab",lambda:self._cycle_context_tab(1),"Ctrl+Tab")
        self.previous_document_tab_action=self._command("Previous Tab",lambda:self._cycle_context_tab(-1),"Ctrl+Shift+Tab")
        self.addAction(self.next_document_tab_action); self.addAction(self.previous_document_tab_action)
        self.theme_system_action=self.theme_actions["system"]; self.theme_dark_action=self.theme_actions["dark"]; self.theme_light_action=self.theme_actions["light"]
        self.icon_original_action=self.icon_actions["original"]; self.icon_classic_action=self.icon_actions["classic"]; self.icon_new_action=self.icon_actions["new"]
        self.launch_dashboard_action=self.launch_actions["dashboard"]; self.launch_last_file_action=self.launch_actions["last_file"]
        self.tabs_enabled_action=self.tabs_actions["enabled"]; self.tabs_disabled_action=self.tabs_actions["disabled"]
        self._sync_app_settings_toggle_actions()

    def _build_static_menus(self, bar) -> None:
        self.file_menu=bar.addMenu("&File"); self.edit_menu=bar.addMenu("&Edit"); self.format_menu=bar.addMenu("F&ormat"); self.insert_menu=bar.addMenu("&Insert"); self.view_menu=bar.addMenu("&View"); self.settings_menu=bar.addMenu("&Settings"); self.help_menu=bar.addMenu("&Help")
        for a in (self.new_action,self.new_folder_action): self.file_menu.addAction(a)
        self.file_menu.addSeparator(); self.file_menu.addAction(self.dashboard_action); self.file_menu.addAction(self.next_file_action); self.file_menu.addAction(self.previous_file_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.refresh_action)
        self.workspace_menu=self.file_menu.addMenu("Workspace(s)"); self.workspace_tabbed_action=self.workspace_menu.menuAction(); self.workspace_action_group=QActionGroup(self.workspace_menu); self.workspace_action_group.setExclusive(True); self.workspace_menu.aboutToShow.connect(self._rebuild_workspace_menu); self._rebuild_workspace_menu()
        self.file_menu.addAction(self.import_file_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.open_external_file_action); self.file_menu.addAction(self.new_window_action); self.file_menu.addSeparator()
        for a in (self.save_action,self.save_as_action,self.save_new_action,self.save_dashboard_action): self.file_menu.addAction(a)
        more=self.file_menu.addMenu("More Actions")
        for a in (self.duplicate_action,self.rename_file_action,self.delete_file_action): more.addAction(a)
        more.addSeparator(); more.addAction(self.external_editor_action); more.addAction(self.open_document_folder_action)
        more.addSeparator(); more.addAction(self.properties_action)
        self.file_menu.addSeparator(); self.file_menu.addAction(self.print_action); self.file_menu.addAction(self.export_pdf_action); self.file_menu.addAction(self.page_setup_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action); self.file_menu.addAction(self.save_exit_action)
        self.edit_menu.addAction(self.undo_action); self.edit_menu.addAction(self.redo_action); self.edit_menu.addSeparator()
        for a in (self.cut_action,self.copy_action,self.paste_action,self.paste_plain_action): self.edit_menu.addAction(a)
        self.edit_menu.addSeparator(); self.edit_menu.addAction(self.delete_text_action); self.edit_menu.addSeparator(); self.edit_menu.addAction(self.duplicate_line_action); self.edit_menu.addAction(self.delete_line_action); self.edit_menu.addSeparator(); self.edit_menu.addAction(self.select_all_action); self.edit_menu.addSeparator(); self.edit_menu.addAction(self.search_bar_action); self.edit_menu.addAction(self.replace_action)
        for a in (self.font_dialog_action,self.increase_font_size_action,self.decrease_font_size_action,self.text_colour_action,self.highlight_colour_action): self.format_menu.addAction(a)
        self.format_menu.addSeparator()
        for a in (self.bold_action,self.italic_action,self.underline_action,self.strike_action,self.superscript_action,self.subscript_action): self.format_menu.addAction(a)
        self.format_menu.addSeparator()
        for a in (self.bullet_action,self.indent_action,self.outdent_action): self.format_menu.addAction(a)
        self.format_menu.addSeparator(); self.format_menu.addAction(self.paragraph_action)
        headings=self.format_menu.addMenu("Paragraph Style"); self.paragraph_style_menu_action=headings.menuAction()
        for n in range(7): headings.addAction(self.heading_actions[n])
        alignment=self.format_menu.addMenu("Alignment")
        for a in (self.alignment_left_action,self.alignment_center_action,self.alignment_right_action,self.alignment_justify_action): alignment.addAction(a)
        spacing=self.format_menu.addMenu("Line Spacing")
        for n in (100,115,150,200): spacing.addAction(self.line_spacing_actions[n])
        self.format_menu.addSeparator(); self.format_menu.addAction(self.clear_formatting_action)
        self.insert_menu.addAction(self.image_action)
        links=self.insert_menu.addMenu("Link"); self.link_menu_action=links.menuAction(); links.addAction(self.link_action); links.addAction(self.edit_link_action); links.addSeparator(); links.addAction(self.remove_link_action)
        self.insert_menu.addSeparator(); self.insert_menu.addAction(self.table_action)
        table=self.insert_menu.addMenu("Table Editing")
        for a in (self.table_row_above_action,self.table_row_below_action,self.table_delete_row_action,self.table_column_left_action,self.table_column_right_action,self.table_delete_column_action,self.table_delete_action): table.addAction(a)
        self.insert_menu.addSeparator()
        for a in (self.date_time_action,self.date_action,self.time_action): self.insert_menu.addAction(a)
        self.insert_menu.addSeparator(); self.insert_menu.addAction(self.rule_action); self.insert_menu.addAction(self.symbol_action)
        self.view_menu.addAction(self.fullscreen_action); self.view_menu.addAction(self.status_bar_action); self.view_menu.addSeparator(); self.view_menu.addAction(self.word_wrap_action); self.view_menu.addAction(self.editor_canvas_theme_action); self.view_menu.addSeparator(); self.view_menu.addAction(self.view_only_action); self.view_menu.addSeparator()
        zoom=self.view_menu.addMenu("Editor Zoom"); zoom.addAction(self.zoom_in_action); zoom.addAction(self.zoom_out_action); zoom.addSeparator(); zoom.addAction(self.zoom_reset_action)
        misc=self.view_menu.addMenu("Editor Miscellaneous"); misc.addAction(self.file_header_action); misc.addSeparator(); misc.addAction(self.tab_width_action); misc.addAction(self.default_font_action)
        self.settings_menu.addAction(self.collapsed_mode_action); self.settings_menu.addSeparator()
        theme=self.settings_menu.addMenu("App Theme"); self.app_theme_menu_action=theme.menuAction()
        for n in ("light","dark","system"): theme.addAction(self.theme_actions[n])
        icons=self.settings_menu.addMenu("App Icons"); self.app_icons_menu_action=icons.menuAction()
        for n in ("new","classic","original","aero"): icons.addAction(self.icon_actions[n])
        dash=self.settings_menu.addMenu("App Dashboard"); self.app_dashboard_menu_action=dash.menuAction(); dash.addAction(self.list_action); dash.addAction(self.grid_action)
        sidebar_menu=self.settings_menu.addMenu("App Sidebar"); self.app_sidebar_menu_action=sidebar_menu.menuAction(); sidebar_menu.addAction(self.sidebar_action); sidebar_menu.addSeparator(); sidebar_menu.addAction(self.left_sidebar_action); sidebar_menu.addAction(self.right_sidebar_action)
        self.settings_menu.addSeparator(); launch=self.settings_menu.addMenu("App Launch Screen"); self.app_launch_screen_menu_action=launch.menuAction()
        for n in ("dashboard","last_file"): launch.addAction(self.launch_actions[n])
        file_launch=self.settings_menu.addMenu("App File Launch"); self.app_file_launch_menu_action=file_launch.menuAction()
        file_launch.addAction(self.tabs_enabled_action); file_launch.addAction(self.tabs_disabled_action)
        self.settings_menu.addSeparator()
        dirty_duplicate=self.settings_menu.addMenu("Duplicate File with Unsaved Changes")
        for n in ("ask","current","saved"): dirty_duplicate.addAction(self.dirty_duplicate_actions[n])
        self.dirty_duplicate_tabbed_action = dirty_duplicate.menuAction()
        dirty_external=self.settings_menu.addMenu("Open Externally with Unsaved Changes")
        for n in ("ask","save","saved"): dirty_external.addAction(self.dirty_external_actions[n])
        self.dirty_external_tabbed_action = dirty_external.menuAction()
        self.help_menu.addAction(self.docs_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.quick_start_action); self.help_menu.addAction(self.shortcuts_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.github_action); self.help_menu.addAction(self.issue_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)

    def _toolbar_icon_path(self, name: str) -> Path:
        scheme = effective_scheme(str(self.config.get("app_theme", "light")))
        icon_set = str(self.config.get("editor_icon_set", "new"))
        family = {
            "original": "ribbon-icons-original",
            "classic": "ribbon-icons-classic",
            "aero": "ribbon-icons-aero",
        }.get(icon_set, "ribbon-icons")
        return self.package_root / "assets" / family / scheme / f"{name}.png"

    def _sync_sidebar_position_icons(self) -> None:
        icon_name = "show-sidebar-right" if self._sidebar_position() == "right" else "show-sidebar"
        path = self._toolbar_icon_path(icon_name)
        if not path.is_file():
            return
        # Shared by the Ribbon toggle and the checkable AppMenu entry only.
        # The App Sidebar submenu parent has its own fixed settings icon.
        self.sidebar_action.setIcon(QIcon(str(path)))

    def _sync_app_settings_menu_icons(self) -> None:
        """Keep AppMenu group glyphs stable regardless of radio selection."""
        for attr, icon_name in (
            ("app_dashboard_menu_action", "app-dashboard"),
            ("app_launch_screen_menu_action", "app-launch-screen"),
            ("app_file_launch_menu_action", "file-launch"),
        ):
            action = getattr(self, attr, None)
            if isinstance(action, QAction):
                path = self._toolbar_icon_path(icon_name)
                action.setIcon(QIcon(str(path)) if path.is_file() else QIcon())

    def _refresh_action_icons(self) -> None:
        mapping={
            "new_action":"new", "new_window_action":"new-window", "new_folder_action":"new-folder",
            "workspace_tabbed_action":"manage-workspaces", "dashboard_action":"show-dashboard",
            "import_file_action":"import-file", "open_external_file_action":"open",
            "previous_file_action":"previous", "next_file_action":"next",
            "save_action":"save", "save_as_action":"save-as", "save_new_action":"save-new",
            "save_dashboard_action":"save-dashboard", "save_exit_action":"save-exit",
            "duplicate_action":"duplicate-file", "rename_file_action":"rename",
            "delete_file_action":"delete-file", "open_document_folder_action":"open-folder",
            "external_editor_action":"external-editor", "properties_action":"properties",
            "print_action":"print", "export_pdf_action":"export-pdf", "page_setup_action":"page-setup",
            "exit_action":"exit", "undo_action":"undo", "redo_action":"redo", "cut_action":"cut",
            "copy_action":"copy", "paste_action":"paste", "paste_plain_action":"paste-plain",
            "delete_text_action":"delete-text", "duplicate_line_action":"duplicate-line",
            "delete_line_action":"delete-line", "select_all_action":"select-all",
            "search_bar_action":"find", "replace_action":"replace",
            "font_dialog_action":"font-dialog", "increase_font_size_action":"font-size-increase",
            "decrease_font_size_action":"font-size-decrease", "text_colour_action":"text-color",
            "highlight_colour_action":"highlight", "underline_action":"underline",
            "bold_action":"bold", "italic_action":"italic", "strike_action":"strikethrough",
            "subscript_action":"subscript", "superscript_action":"superscript",
            "bullet_action":"bullet-list", "indent_action":"indent", "outdent_action":"outdent",
            "paragraph_action":"paragraph", "clear_formatting_action":"clear-formatting",
            "alignment_left_action":"align-left", "alignment_center_action":"align-center",
            "alignment_right_action":"align-right", "alignment_justify_action":"justify",
            "link_action":"insert-link", "edit_link_action":"edit-link",
            "remove_link_action":"remove-link", "rule_action":"horizontal-rule",
            "image_action":"insert-image", "table_action":"insert-table",
            "table_delete_action":"delete-table", "table_column_left_action":"insert-column-left",
            "table_column_right_action":"insert-column-right", "table_delete_column_action":"delete-column",
            "table_row_above_action":"insert-row-above", "table_row_below_action":"insert-row-below",
            "table_delete_row_action":"delete-row", "date_time_action":"date-time",
            "date_action":"insert-date", "time_action":"insert-time", "symbol_action":"symbols",
            "fullscreen_action":"full-screen", "view_only_action":"view-only",
            "collapsed_mode_action":"focused-mode", "file_header_action":"file-header",
            "word_wrap_action":"word-wrap", "editor_canvas_theme_action":"editor-canvas",
            "zoom_in_action":"zoom-in", "zoom_out_action":"zoom-out", "zoom_reset_action":"zoom-reset",
            "tab_width_action":"tab-width", "default_font_action":"default-font",
            "sidebar_action":"show-sidebar", "status_bar_action":"status-bar",
            "left_sidebar_action":"dock-left", "right_sidebar_action":"dock-right",
            "theme_system_action":"theme-system", "theme_dark_action":"theme-dark", "theme_light_action":"theme-light",
            "icon_new_action":"icons-new", "icon_classic_action":"icons-classic", "icon_original_action":"icons-legacy",
            "list_action":"list-view", "grid_action":"grid-view",
            "launch_dashboard_action":"launch-dashboard", "launch_last_file_action":"launch-last-file",
            "tabs_enabled_action":"tabs-enabled", "tabs_disabled_action":"tabs-disabled",
            "dirty_external_tabbed_action":"dirty-external-policy", "dirty_duplicate_tabbed_action":"dirty-duplicate-policy",
            "docs_action":"documentation", "quick_start_action":"tutorial",
            "shortcuts_action":"shortcuts", "github_action":"github", "issue_action":"issue",
            "about_action":"about",
            "app_theme_menu_action":"app-theme", "app_icons_menu_action":"app-icons",
            "paragraph_style_menu_action":"heading-group", "link_menu_action":"link-group",
            "app_dashboard_menu_action":"app-dashboard",
            "app_sidebar_menu_action":"sidebar-settings",
            "app_launch_screen_menu_action":"app-launch-screen",
            "app_file_launch_menu_action":"file-launch",
        }
        for attr,name in mapping.items():
            action=getattr(self,attr,None); path=self._toolbar_icon_path(name)
            if isinstance(action,QAction) and path.is_file(): action.setIcon(QIcon(str(path)))

        # AppMenu-only heading actions are shared with the embedded editor and
        # must follow the active Riqa family and app theme.
        for level, action in self.heading_actions.items():
            path = self._toolbar_icon_path(f"heading-{level}")
            if path.is_file():
                action.setIcon(QIcon(str(path)))

        self._sync_sidebar_position_icons()
        self._sync_app_settings_menu_icons()

        # Icon-family selectors use the active family's selector artwork on both
        # AppMenu and Ribbon because they share these QAction instances:
        # Harmony -> icons-new (stable preference key), Humility -> icons-classic, Heritage -> icons-legacy.

        # App Settings ribbon buttons are compact stateful toggles that preview
        # their current choice using the active icon family.
        dashboard_mode = self.editor_manager.dashboard.view_mode()
        dynamic = (
            (self.app_launch_toggle_action, "launch-dashboard" if str(self.config.get("app_launch_screen", "dashboard")) == "dashboard" else "launch-last-file"),
            (self.app_dashboard_toggle_action, "grid-view" if dashboard_mode == "grid" else "list-view"),
            (self.app_tabs_toggle_action, "tabs-enabled" if bool(self.config.get("tabs_enabled", True)) else "tabs-disabled"),
        )
        for action, name in dynamic:
            path = self._toolbar_icon_path(name)
            if path.is_file():
                action.setIcon(QIcon(str(path)))

    def _create_tabbed_toolbar(self) -> None:
        names=("print_action","export_pdf_action","page_setup_action","new_action","new_folder_action","new_window_action","open_external_file_action","import_file_action","previous_file_action","next_file_action","workspace_tabbed_action","dashboard_action","save_as_action","properties_action","delete_file_action","external_editor_action","save_action","rename_file_action","duplicate_action","open_document_folder_action","save_new_action","save_dashboard_action","save_exit_action","exit_action","select_all_action","cut_action","delete_text_action","paste_plain_action","undo_action","redo_action","copy_action","paste_action","increase_font_size_action","decrease_font_size_action","font_dialog_action","text_colour_action","underline_action","strike_action","subscript_action","superscript_action","bold_action","italic_action","highlight_colour_action","bullet_action","alignment_right_action","alignment_justify_action","indent_action","outdent_action","alignment_left_action","alignment_center_action","paragraph_action","clear_formatting_action","replace_action","duplicate_line_action","delete_line_action","date_time_action","symbol_action","date_action","time_action","remove_link_action","image_action","link_action","edit_link_action","table_delete_action","table_column_left_action","table_column_right_action","table_delete_column_action","table_action","table_row_above_action","table_row_below_action","table_delete_row_action","rule_action","fullscreen_action","view_only_action","collapsed_mode_action","file_header_action","word_wrap_action","editor_canvas_theme_action","sidebar_action","left_sidebar_action","right_sidebar_action","status_bar_action","search_bar_action","zoom_in_action","zoom_reset_action","zoom_out_action","tab_width_action","default_font_action","theme_system_action","theme_dark_action","theme_light_action","icon_original_action","icon_classic_action","icon_new_action","app_launch_toggle_action","app_dashboard_toggle_action","app_tabs_toggle_action","dirty_external_tabbed_action","dirty_duplicate_tabbed_action","docs_action","quick_start_action","shortcuts_action","about_action","github_action","issue_action")
        self.shell_ribbon=ShellRibbon({n:getattr(self,n) for n in names},self.tabbed_container); self.tabbed_layout.addWidget(self.shell_ribbon)
        self.shell_ribbon.font_family_selected.connect(lambda font:self._editor_call("set_selected_font",font)); self.shell_ribbon.font_size_selected.connect(lambda text:self._editor_call("set_selected_font_size",text)); self.shell_ribbon.heading_selected.connect(self._set_heading); self.shell_ribbon.line_spacing_selected.connect(self._set_line_spacing)
        self.shell_ribbon.collapsed_changed.connect(lambda v:self.config.set("riqatony_desk_ribbon_collapsed",bool(v),save=True))
        if bool(self.config.get("riqatony_desk_ribbon_collapsed",False)): self.shell_ribbon.set_collapsed(True,emit=False)
        self._sync_editor_actions()

    def _save_current(self) -> None:
        page=self._current_page()
        if page is not None: page.save_to_disk()
    def _rename_current(self) -> None:
        document = self.editor_manager.current_document
        if document is not None:
            self.file_actions.rename_document(document)
            return
        folder = self.editor_manager.current_folder
        if folder is not None and folder != self.library_root:
            self.file_actions.rename_folder(folder)
    def _delete_current_file(self) -> None:
        if self.editor_manager.current_document is not None: self.file_actions.remove_document(self.editor_manager.current_document)
    def _duplicate_current(self) -> None:
        if self.editor_manager.current_document is not None: self.file_actions.duplicate_document(self.editor_manager.current_document)
    def _open_current_document_folder(self) -> None:
        if self.editor_manager.current_document is not None: self.file_actions.open_document_folder(self.editor_manager.current_document)
    def _open_current_external(self) -> None:
        if self.editor_manager.current_document is not None: self.file_actions.open_external_editor(self.editor_manager.current_document)

    def _handle_editor_file_drop(
        self,
        supplied_paths: list[str | Path],
        _context_folder: str | Path | None = None,
    ) -> None:
        """Open supported editor drops in their own RiqatonyDesk windows."""
        seen: set[Path] = set()
        for supplied in supplied_paths:
            path = Path(supplied).expanduser().resolve(strict=False)
            if (
                path in seen
                or not path.is_file()
                or path.suffix.casefold() not in RTF_EXTENSIONS
            ):
                continue
            seen.add(path)
            self._launch_new_window(path)

    def _handle_app_drop(
        self,
        supplied_paths: list[str | Path],
        destination_folder: str | Path | None = None,
    ) -> None:
        """Import external RTF drops without opening them."""
        external: list[Path] = []
        seen: set[Path] = set()
        for supplied in supplied_paths:
            path = Path(supplied).expanduser().resolve(strict=False)
            if (
                path in seen
                or not path.is_file()
                or path.suffix.casefold() not in RTF_EXTENSIONS
            ):
                continue
            seen.add(path)
            try:
                path.relative_to(self.library_root)
            except ValueError:
                external.append(path)

        if not external:
            return

        self.file_actions.import_files(
            external,
            destination_folder or self._creation_folder(),
        )
    def _toggle_lock_editor_current(self, checked: bool) -> None:
        # Preserve Ricopad's protective unlock warning, then make the resulting
        # lock state application-wide so it follows the user across files and
        # survives the next session.
        page = self._current_page()
        if page is None:
            self.view_only_action.blockSignals(True)
            self.view_only_action.setChecked(bool(self.config.get("lock_editor", False)))
            self.view_only_action.blockSignals(False)
            return
        desired = bool(checked)
        source = self._editor_action("view_only_action")
        if source is not None and bool(page.view_only) != desired:
            source.trigger()
        resulting = bool(page.view_only)
        self.editor_manager.set_lock_editor(resulting)
        self._sync_editor_actions()
        self._update_window_title()
    def _set_alignment(self,value) -> None: self._editor_call("set_alignment",value)
    def _set_heading(self,value: int) -> None: self._editor_call("apply_heading",int(value))
    def _set_line_spacing(self,value: int) -> None: self._editor_call("set_line_spacing",int(value))

    def _sync_editor_command_state(self,shell_name: str,engine_name: str) -> None:
        shell=getattr(self,shell_name); source=self._editor_action(engine_name); shell.setEnabled(source is not None and source.isEnabled())
        if shell.isCheckable() and source is not None:
            shell.blockSignals(True); shell.setChecked(source.isChecked()); shell.blockSignals(False)

    def _sync_editor_actions(self,*_args) -> None:
        page=self._current_page(); enabled=page is not None
        if page is not None and hasattr(self, "collapsed_mode_action") and self.collapsed_mode_action.isChecked():
            page.set_status_visible(False)
            page.set_header_visible(False)
        for name in ("save_action","save_as_action","save_new_action","save_dashboard_action","save_exit_action","properties_action","external_editor_action","delete_file_action","duplicate_action","open_document_folder_action","print_action","export_pdf_action","page_setup_action"): getattr(self,name).setEnabled(enabled)
        folder = self.editor_manager.current_folder
        self.rename_file_action.setEnabled(
            enabled or (folder is not None and folder != self.library_root)
        )
        pairs={"undo_action":"undo_action","redo_action":"redo_action","cut_action":"cut_action","copy_action":"copy_action","paste_action":"paste_action","paste_plain_action":"paste_plain_action","delete_text_action":"delete_text_action","duplicate_line_action":"duplicate_line_action","delete_line_action":"delete_line_action","select_all_action":"select_all_action","replace_action":"replace_action","font_dialog_action":"font_dialog_action","increase_font_size_action":"increase_font_size_action","decrease_font_size_action":"decrease_font_size_action","text_colour_action":"text_colour_action","highlight_colour_action":"highlight_colour_action","clear_highlight_action":"clear_highlight_action","bold_action":"bold_action","italic_action":"italic_action","underline_action":"underline_action","strike_action":"strike_action","superscript_action":"superscript_action","subscript_action":"subscript_action","bullet_action":"bulleted_list_action","indent_action":"increase_indent_action","outdent_action":"decrease_indent_action","paragraph_action":"paragraph_action","clear_formatting_action":"clear_formatting_action","link_action":"link_action","edit_link_action":"edit_link_action","remove_link_action":"remove_link_action","rule_action":"horizontal_rule_action","image_action":"image_action","table_action":"table_action","table_row_above_action":"table_row_above_action","table_row_below_action":"table_row_below_action","table_delete_row_action":"table_delete_row_action","table_column_left_action":"table_column_left_action","table_column_right_action":"table_column_right_action","table_delete_column_action":"table_delete_column_action","table_delete_action":"table_delete_action","date_time_action":"insert_date_time_action","date_action":"date_action","time_action":"time_action","symbol_action":"symbol_action","word_wrap_action":"wrap_action","zoom_in_action":"zoom_in_action","zoom_out_action":"zoom_out_action","zoom_reset_action":"zoom_reset_action","tab_width_action":"tab_width_action","default_font_action":"default_font_action"}
        for a,b in pairs.items(): self._sync_editor_command_state(a,b)
        search_source = self._editor_action("search_bar_action")
        if search_source is not None:
            self.search_bar_action.setEnabled(search_source.isEnabled())
        else:
            navigation_search = getattr(self.stack.currentWidget(), "search_input", None)
            self.search_bar_action.setEnabled(navigation_search is not None)
        self.view_only_action.setEnabled(enabled); self.view_only_action.blockSignals(True); self.view_only_action.setChecked(bool(page.view_only) if page else bool(self.config.get("lock_editor", False))); self.view_only_action.blockSignals(False)
        self.editor_canvas_theme_action.blockSignals(True)
        self.editor_canvas_theme_action.setChecked(not self._canvas_is_light())
        self.editor_canvas_theme_action.blockSignals(False)
        for action in [*self.heading_actions.values(),*self.line_spacing_actions.values(),self.alignment_left_action,self.alignment_center_action,self.alignment_right_action,self.alignment_justify_action]: action.setEnabled(enabled)
        if enabled:
            for level,shell in self.heading_actions.items():
                source=page.editor_group_action("heading_actions", level)
                if isinstance(source,QAction):
                    shell.blockSignals(True); shell.setChecked(source.isChecked()); shell.blockSignals(False)
            for value,shell in self.line_spacing_actions.items():
                source=page.editor_group_action("line_spacing_actions", value)
                if isinstance(source,QAction):
                    shell.blockSignals(True); shell.setChecked(source.isChecked()); shell.blockSignals(False)
            for shell_name,editor_name in (("alignment_left_action","alignment_left_action"),("alignment_center_action","alignment_center_action"),("alignment_right_action","alignment_right_action"),("alignment_justify_action","alignment_justify_action")):
                shell=getattr(self,shell_name); source=page.editor_action(editor_name)
                if isinstance(source,QAction):
                    shell.blockSignals(True); shell.setChecked(source.isChecked()); shell.blockSignals(False)
        if hasattr(self,"shell_ribbon"):
            self.shell_ribbon.set_editor_enabled(enabled)
            if page is not None: page.sync_ribbon_selectors(self.shell_ribbon)

    def eventFilter(self, watched, event) -> bool:
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and self.isActiveWindow()
            and event.button() == Qt.MouseButton.BackButton
        ):
            self._navigate_back()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def _open_sidebar_document(self, path):
        """Open a sidebar document transactionally and roll back rejected selection."""
        page = self.editor_manager.open_document(path)
        if page is None:
            current = self.editor_manager.current_document
            if current is not None and not current.external:
                self.navigation.select_document(current.path)
        return page

    def _connect_signals(self) -> None:
        self.document_tabs.currentChanged.connect(self._activate_document_tab)
        self.document_tabs.tabCloseRequested.connect(self._close_document_tab)

        self.navigation.dashboard_requested.connect(
            self.editor_manager.show_dashboard
        )
        self.navigation.refresh_requested.connect(self._refresh_workspace)
        self.navigation.folder_requested.connect(self.editor_manager.open_folder)
        self.navigation.document_requested.connect(self._open_sidebar_document)
        self.navigation.document_move_requested.connect(
            self.file_actions.move_document
        )
        self.navigation.external_files_import_requested.connect(
            self.file_actions.import_files
        )

        manager = self.editor_manager
        manager.dashboard_shown.connect(self.navigation.select_dashboard)
        manager.dashboard_shown.connect(self._record_dashboard_navigation)
        manager.dashboard_shown.connect(self._show_dashboard_navigation_tab)
        manager.dashboard_shown.connect(self._sync_editor_actions)
        manager.dashboard_shown.connect(self._update_action_states)
        manager.current_folder_changed.connect(self.navigation.select_folder)
        manager.current_folder_changed.connect(self._record_folder_navigation)
        manager.current_folder_changed.connect(self._show_folder_navigation_tab)
        manager.current_folder_changed.connect(self._sync_editor_actions)
        manager.current_folder_changed.connect(self._update_action_states)
        manager.current_document_changed.connect(self._select_document_tab)
        manager.current_document_changed.connect(self._record_document_navigation)
        manager.current_document_changed.connect(
            lambda document: (
                self.navigation.select_document(document.path)
                if not document.external else False
            )
        )
        manager.current_document_changed.connect(
            self._remember_last_opened_document
        )
        manager.current_document_changed.connect(self._sync_editor_actions)
        manager.current_document_changed.connect(self._update_action_states)
        manager.external_editor_requested.connect(
            self.file_actions.open_external_editor
        )
        manager.containing_folder_requested.connect(
            self.file_actions.open_document_folder
        )
        manager.rename_requested.connect(self.file_actions.rename_document)
        manager.remove_requested.connect(self.file_actions.remove_document)
        manager.duplicate_requested.connect(
            self.file_actions.duplicate_document
        )
        manager.folder_open_external_requested.connect(
            self.file_actions.open_folder_external
        )
        manager.folder_rename_requested.connect(
            self.file_actions.rename_folder
        )
        manager.folder_remove_requested.connect(
            self.file_actions.remove_folder
        )
        manager.create_file_requested.connect(self.file_actions.create_file)
        manager.create_folder_requested.connect(self._create_folder)
        manager.external_files_import_requested.connect(
            self.file_actions.import_files
        )
        manager.editor_files_dropped.connect(self._handle_editor_file_drop)
        manager.refresh_requested.connect(self._refresh_workspace)
        manager.sort_mode_changed.connect(self._remember_sort_mode)
        manager.view_mode_changed.connect(self._remember_view_mode)
        manager.view_mode_changed.connect(self._sync_view_actions)
        manager.editor_history_changed.connect(self._sync_editor_actions)
        manager.editor_formatting_changed.connect(self._sync_editor_actions)
        manager.editor_preferences_changed.connect(self._sync_editor_actions)
        manager.workspace_requested.connect(self._show_projects)
        manager.exit_requested.connect(self.close)
        manager.save_and_new_requested.connect(self._save_and_new)
        manager.save_and_dashboard_requested.connect(self._save_and_dashboard)
        manager.save_and_exit_requested.connect(self._save_and_exit)
        manager.document_path_rebound.connect(self._rebind_document_tab)
        manager.document_path_rebound.connect(
            lambda _old, _new: self.watcher.request_rescan()
        )
        manager.document_closed.connect(self._remove_document_tab)
        manager.documents_reset.connect(self._reset_document_tabs)

        self.file_actions.folder_renamed.connect(self._on_folder_renamed)
        self.file_actions.folder_removed.connect(
            lambda _path: self.editor_manager.show_dashboard()
        )
        self.file_actions.document_created.connect(self._queue_created_open)
        self.file_actions.file_policy_changed.connect(self._on_file_policy_changed)
        self.repository.document_added.connect(self._open_pending_if_ready)
        self.repository.document_changed.connect(self._update_document_tab)
        self.repository.document_path_changed.connect(
            self._remember_renamed_document_path
        )
        self.repository.document_path_changed.connect(
            self._on_repository_document_path_changed
        )
        self.repository.dirty_count_changed.connect(self._update_dirty_status)

        for source in (manager, self.file_actions):
            source.status_message.connect(self.show_status)
        self.desktop_launcher.status_message.connect(self.show_status)
        self.desktop_launcher.launch_error.connect(
            lambda message: QMessageBox.warning(
                self, "Could Not Open", message
            )
        )
        self._connect_watcher(self.watcher)

    def _connect_watcher(self, watcher: FilesystemWatcher) -> None:
        watcher.scan_started.connect(self._on_scan_started)
        watcher.folders_discovered.connect(self.navigation.set_disk_folders)
        watcher.scan_details.connect(self._on_scan_details)
        watcher.scan_finished.connect(self._on_scan_finished)
        watcher.scan_failed.connect(self._on_scan_failed)

    def _install_watcher(
        self,
        library_root: Path,
        *,
        start: bool,
        retire_current: bool,
    ) -> None:
        previous = self.watcher
        watcher = FilesystemWatcher(library_root, self.repository, parent=self)
        self.watcher = watcher
        self.file_actions.switch_workspace_root(library_root, watcher)
        self._connect_watcher(watcher)
        if start:
            watcher.start(initial_scan=True)
        if retire_current and previous is not watcher:
            previous.deleteLater()

    def _current_page(self) -> EditorPage | None:
        page = self.stack.currentWidget()
        return page if isinstance(page, EditorPage) else None

    def _creation_folder(self) -> Path:
        if self.editor_manager.current_folder is not None:
            return self.editor_manager.current_folder
        document = self.editor_manager.current_document
        if document is not None and not document.external:
            return document.path.parent
        return self.library_root

    def _new_rtf_file(self, _checked=False) -> None:
        self.file_actions.create_file(self._creation_folder())

    def _new_folder(self, _checked=False) -> None:
        self._create_folder(self._creation_folder())

    def _window_launch_command(self, open_path: Path | None = None) -> list[str]:
        if self.runtime_paths.running_as_appimage:
            executable = os.environ.get("APPIMAGE", "").strip()
            command = [executable] if executable else []
        elif self.runtime_paths.running_frozen:
            command = [sys.executable]
        else:
            command = [sys.executable, str(self.runtime_paths.launcher_root / "main.py")]
        if command and open_path is not None:
            command.append(str(Path(open_path).resolve(strict=False)))
        return command

    def _launch_new_window(self, open_path: Path | None = None) -> bool:
        command = self._window_launch_command(open_path)
        if not command:
            QMessageBox.warning(self, "New Window Failed", "RiqatonyDesk could not locate its launcher.")
            return False
        try:
            subprocess.Popen(
                command,
                cwd=str(self.runtime_paths.launcher_root),
                start_new_session=True,
            )
        except OSError as error:
            QMessageBox.warning(
                self,
                "New Window Failed",
                f"RiqatonyDesk could not open a new window:\n\n{error}",
            )
            return False
        return True

    def _new_window(self, _checked=False) -> None:
        self._launch_new_window()

    def _import_file_into_workspace(self, _checked=False) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Import File into Workspace — RiqatonyDesk",
            "",
            "Rich Text Format (*.rtf)",
        )
        if not selected:
            return
        # Reuse the exact external-drop import path: validate as an external
        # RTF, copy into the Workspace root, rescan, and stop without opening.
        self._handle_app_drop([Path(selected)], self.library_root)

    def _open_external_file(self, _checked=False) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Open External File — RiqatonyDesk",
            "",
            "Rich Text Format (*.rtf)",
        )
        if not selected:
            return
        path = Path(selected).expanduser().resolve(strict=False)
        if not path.is_file() or path.suffix.casefold() not in RTF_EXTENSIONS:
            QMessageBox.warning(
                self,
                "Open External File Failed",
                "Choose a supported RTF file (.rtf).",
            )
            return
        try:
            path.relative_to(self.library_root)
        except ValueError:
            self._launch_new_window(path)
            return
        QMessageBox.information(
            self,
            "Managed Workspace File",
            "That file belongs to the active Workspace. Open it from the Workspace instead.",
        )

    def _create_folder(self, parent: str | Path) -> None:
        if self.file_actions.create_folder(parent) is not None:
            QTimer.singleShot(100, self.navigation.rebuild_from_repository)

    def _save_and_new(self, page: EditorPage) -> None:
        if page.save_to_disk():
            self.file_actions.create_file(
                page.document.path.parent
                if not page.document.external else self.library_root
            )

    def _save_and_dashboard(self, page: EditorPage) -> None:
        if page.save_to_disk():
            self.editor_manager.show_dashboard()

    def _save_and_exit(self, page: EditorPage) -> None:
        if page.save_to_disk():
            self.close()

    def _show_projects(self, _checked=False) -> None:
        dialog = ProjectsDialog(self.project_registry, self)
        if (
            dialog.exec() == QDialog.DialogCode.Accepted
            and dialog.selected_project_id
        ):
            self._switch_project(dialog.selected_project_id)
        self._rebuild_workspace_menu()

    def _rebuild_workspace_menu(self) -> None:
        """Build the radio inventory only from the lightweight registry."""
        for action in tuple(self.workspace_action_group.actions()):
            self.workspace_action_group.removeAction(action)
            self.workspace_menu.removeAction(action)
            action.deleteLater()
        self.workspace_menu.clear()
        self.workspace_menu.addAction(self.manage_workspaces_action)
        self.workspace_menu.addSeparator()

        active_id = self.project_registry.active_project_id
        for workspace in self.project_registry.projects:
            action = QAction(workspace.name, self.workspace_menu)
            action.setCheckable(True)
            action.setChecked(workspace.project_id == active_id)
            action.setData(workspace.project_id)
            action.setToolTip(str(workspace.folder))
            action.setStatusTip(str(workspace.folder))
            action.triggered.connect(
                lambda _checked=False, workspace_id=workspace.project_id:
                    self._switch_project(workspace_id)
            )
            self.workspace_action_group.addAction(action)
            self.workspace_menu.addAction(action)

    def _switch_project(self, project_id: str) -> bool:
        project = self.project_registry.get(project_id)
        if project is None:
            return False
        if project.project_id == self.project_registry.active_project_id:
            self._update_window_title()
            self.editor_manager.show_dashboard()
            return True
        if not project.folder.is_dir():
            QMessageBox.warning(
                self,
                "Workspace Folder Unavailable",
                "Relink this Workspace to an available folder before opening it.",
            )
            return False
        try:
            root = self.runtime_paths.ensure_writable_workspace(project.folder)
        except OSError as error:
            QMessageBox.warning(
                self, "Workspace Cannot Be Opened",
                f"RiqatonyDesk could not use this Workspace folder:\n\n{error}",
            )
            return False
        if not self.editor_manager.can_close_application():
            return False

        self._save_active_project_state(save=True)
        stopped = self.watcher.stop(
            timeout_ms=2500,
            pump_events=QApplication.processEvents,
        )
        if not stopped:
            self._install_watcher(
                self.library_root, start=True, retire_current=False
            )
            QMessageBox.warning(
                self,
                "Workspace Switch Cancelled",
                "The current Workspace scanner did not stop safely. "
                "The existing Workspace remains active.",
            )
            return False

        self._pending_open_path = None
        self._repair_navigation_after_scan = False
        self.library_root = root
        self.editor_manager.switch_workspace_root(root)
        self.navigation.switch_workspace_root(root)
        self.repository.clear()
        self.project_registry.set_active(project.project_id)
        self._apply_active_project_state()
        self._install_watcher(root, start=True, retire_current=True)
        self.editor_manager.show_dashboard()
        self._update_action_states()
        self.show_status(f"Opening Workspace: {project.name}")
        return True

    def queue_open_path(self, path: str | Path) -> None:
        """Open a path without importing external OS-open documents."""
        target = Path(path).expanduser().resolve(strict=False)
        if not target.is_file() or target.suffix.casefold() not in RTF_EXTENSIONS:
            return
        self._startup_open_requested = True
        try:
            target.relative_to(self.library_root)
        except ValueError:
            self._open_external_path(target)
            return
        self._pending_open_path = target
        document = self.repository.get(target)
        if document is not None:
            self._open_pending_if_ready(document)
        elif not self._startup_scan_pending:
            self.watcher.request_rescan()

    def _open_external_path(self, path: Path) -> None:
        try:
            info = path.stat()
        except OSError:
            return
        document = self.repository.get(path)
        if document is None:
            document = self.repository.add(
                DocumentEntry(
                    path=path,
                    filename=path.name,
                    display_name=path.stem.replace("-", " ").replace("_", " ").title(),
                    folder=str(path.parent),
                    created=info.st_ctime,
                    modified=info.st_mtime,
                    size=info.st_size,
                    external=True,
                )
            )
        page = self.editor_manager.open_document(document)
        if page is None:
            self.repository.remove(path)
            return
        self._apply_external_verification_mode(page)

    def _apply_external_verification_mode(self, page: EditorPage) -> None:
        """Start an externally launched document in transient Locked + Focused Mode."""
        page.set_view_only(True)
        page.scroll_to_top()
        self._sync_editor_actions()
        self.collapsed_mode_action.blockSignals(True)
        self.collapsed_mode_action.setChecked(True)
        self.collapsed_mode_action.blockSignals(False)
        self._toggle_collapsed_mode(True)
        self._update_action_states()
        self._update_window_title()

    def _queue_created_open(self, path: Path) -> None:
        self._startup_open_requested = True
        self._pending_open_path = Path(path).resolve(strict=False)
        document = self.repository.get(self._pending_open_path)
        if document is not None:
            self._open_pending_if_ready(document)

    def _open_pending_if_ready(self, document: DocumentEntry) -> None:
        if (
            self._pending_open_path is None
            or document.path.resolve(strict=False) != self._pending_open_path
        ):
            return
        self._pending_open_path = None
        self.editor_manager.open_document(document)

    def _canvas_is_light(self) -> bool:
        stored = self.config.get("editor_canvas_light", True)
        return stored if isinstance(stored, bool) else True

    def _toggle_editor_canvas_light(self, checked: bool) -> None:
        # exp5 contract: application chrome and editor canvas are independent.
        # The action is named "Dark Editor", so checked means a dark canvas.
        self.config.set("editor_canvas_light", not bool(checked), save=True)
        self.editor_manager.apply_editor_preferences()
        self.editor_manager.show_current_editor_status(
            "Editor canvas switched to a dark background."
            if bool(checked)
            else "Editor canvas switched to a light background.",
            4000,
        )

    def _set_theme(self, theme: str) -> None:
        if theme not in {"system", "dark", "light"}:
            return
        # exp5 keeps application chrome independent from the editor canvas.
        # Changing System/Dark/Light updates the application palette and icon
        # scheme only; the persisted Dark Editor choice is left untouched.
        self.config.set("app_theme", theme, save=True)
        apply_theme(QApplication.instance(), theme)
        for value, action in self.theme_actions.items():
            action.setChecked(value == theme)
        self._refresh_action_icons()
        if hasattr(self, "shell_ribbon"):
            self.shell_ribbon.refresh_theme()
        self.editor_manager.dashboard.refresh_theme()
        for folder_page in self.editor_manager._folder_pages.values():
            folder_page.refresh_theme()
        for _path, state in self.states:
            if isinstance(state.editor_page, EditorPage):
                state.editor_page.set_editor_app_theme(theme)
                state.editor_page.apply_theme()
        label = "System" if theme == "system" else theme.title()
        self.show_status(f"Theme: {label}.")

    def _set_icon_set(self, icon_set: str) -> None:
        if icon_set not in {"original", "classic", "new", "aero"}:
            return
        self.config.set("editor_icon_set", icon_set, save=True)
        QApplication.instance().setProperty("riqatony_desk_icon_set", icon_set)
        for value, action in self.icon_actions.items():
            action.setChecked(value == icon_set)
        self._refresh_action_icons()
        self.editor_manager.dashboard.refresh_theme()
        for page in self.editor_manager._folder_pages.values():
            page.refresh_theme()
        for _path, state in self.states:
            if isinstance(state.editor_page, EditorPage):
                state.editor_page.set_editor_icon_set(icon_set)

    def _set_launch_screen(self, screen: str) -> None:
        if screen not in {"dashboard", "last_file"}:
            return
        self.config.set("app_launch_screen", screen, save=True)
        for value, action in self.launch_actions.items():
            action.setChecked(value == screen)
        self._sync_app_settings_toggle_actions()
        self._refresh_action_icons()

    def _set_dirty_duplicate_action(self, choice: str) -> None:
        if choice not in {"ask", "current", "saved"}:
            return
        self.config.set("dirty_duplicate_action", choice, save=True)
        self._on_file_policy_changed("dirty_duplicate_action", choice)

    def _set_dirty_external_action(self, choice: str) -> None:
        if choice not in {"ask", "save", "saved"}:
            return
        self.config.set("dirty_external_action", choice, save=True)
        self._on_file_policy_changed("dirty_external_action", choice)

    def _on_file_policy_changed(self, key: str, value: str) -> None:
        actions = (
            self.dirty_duplicate_actions
            if key == "dirty_duplicate_action"
            else self.dirty_external_actions
            if key == "dirty_external_action"
            else {}
        )
        for selected, action in actions.items():
            action.blockSignals(True)
            action.setChecked(selected == value)
            action.blockSignals(False)

    def _sync_view_actions(self, mode: str) -> None:
        self.list_action.setChecked(mode == "list")
        self.grid_action.setChecked(mode == "grid")
        self._sync_app_settings_toggle_actions()

    def _set_dashboard_view_mode(self, mode: str) -> None:
        if mode not in {"list", "grid"}:
            return
        self.editor_manager.set_view_mode(mode)
        self._sync_view_actions(mode)
        self._refresh_action_icons()

    def _toggle_dashboard_view_mode(self, _checked=False) -> None:
        mode = self.editor_manager.dashboard.view_mode()
        self._set_dashboard_view_mode("grid" if mode == "list" else "list")

    def _toggle_launch_screen_mode(self, _checked=False) -> None:
        current = str(self.config.get("app_launch_screen", "dashboard"))
        self._set_launch_screen("last_file" if current == "dashboard" else "dashboard")

    def _sync_app_settings_toggle_actions(self) -> None:
        launch = str(self.config.get("app_launch_screen", "dashboard"))
        dashboard_mode = self.editor_manager.dashboard.view_mode() if hasattr(self, "editor_manager") else "list"
        tabs_enabled = bool(self.config.get("tabs_enabled", True))
        states = (
            (self.app_launch_toggle_action, f"Launch Screen — {'Dashboard' if launch == 'dashboard' else 'Last File'}"),
            (self.app_dashboard_toggle_action, f"Dashboard — {'Grid View' if dashboard_mode == 'grid' else 'List View'} — Ctrl+Alt+Shift+V"),
            (self.app_tabs_toggle_action, f"File Launch — Tabs {'Enabled' if tabs_enabled else 'Disabled'}"),
        )
        for action, text in states:
            if action is None:
                continue
            action.setText(text)
            clean = text.replace("&", "").replace("…", "").strip()
            action.setToolTip(clean)

    def _update_action_states(self, *_args) -> None:
        # Managed-workspace commands have one permanent owner. They must stay
        # available from the Dashboard, sidebar, folders, and active editor;
        # embedded Ribbon duplicates carry no shortcuts.
        self.new_action.setEnabled(True)
        self.manage_workspaces_action.setEnabled(True)
        self.dashboard_action.setEnabled(True)
        self.shortcuts_action.setEnabled(True)
        self._sync_editor_actions()
        self._update_window_title()

    def _update_window_title(self) -> None:
        workspace = self.project_registry.active_project.name.strip()
        document = self.editor_manager.current_document
        if document is not None:
            scope = "External" if document.external else workspace
            page = self._current_page()
            lock_suffix = " — Locked Mode" if page is not None and page.view_only else ""
            dirty_prefix = "*" if document.dirty else ""
            self.setWindowTitle(
                f"{dirty_prefix}{document.filename} — {scope} — {APP_NAME}{lock_suffix}"
            )
        else:
            self.setWindowTitle(f"{workspace} — {APP_NAME}")

    def _remember_last_opened_document(
        self, document: DocumentEntry
    ) -> None:
        if document.external:
            return
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"last_opened_file": str(document.path)},
        )

    def _remember_renamed_document_path(
        self, document: DocumentEntry, old_path: Path
    ) -> None:
        if document.external:
            return
        last = self.project_registry.active_project.state.get(
            "last_opened_file"
        )
        if last and Path(str(last)).resolve(strict=False) == old_path:
            self.project_registry.update_state(
                self.project_registry.active_project_id,
                {"last_opened_file": str(document.path)},
            )

    def _remember_sort_mode(self, mode: str) -> None:
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"dashboard_sort": mode},
        )

    def _remember_view_mode(self, mode: str) -> None:
        self.project_registry.update_state(
            self.project_registry.active_project_id,
            {"dashboard_view": mode},
        )

    def _apply_active_project_state(self) -> None:
        state = self.project_registry.active_project.state
        self.navigation.restore_collapsed_folders(
            state.get("collapsed_folders", [])
            if isinstance(state.get("collapsed_folders", []), list)
            else []
        )
        self.editor_manager.set_sort_mode(
            str(state.get("dashboard_sort", "modified"))
        )
        self.editor_manager.set_search_text(
            str(state.get("dashboard_search", ""))
        )
        mode = str(state.get("dashboard_view", "list"))
        self.editor_manager.set_view_mode(mode)
        self._sync_view_actions(mode)

    def _save_active_project_state(self, *, save: bool) -> None:
        values = {
            "collapsed_folders": sorted(self.navigation.collapsed_folders()),
            "dashboard_sort": self.editor_manager.dashboard._sort_mode,
            "dashboard_search": self.editor_manager.dashboard.search_input.text(),
            "dashboard_view": self.editor_manager.dashboard.view_mode(),
            "last_opened_folder": (
                str(self.editor_manager.current_folder)
                if self.editor_manager.current_folder else None
            ),
        }
        document = self.editor_manager.current_document
        if document is not None and not document.external:
            values["last_opened_file"] = str(document.path)
        self.project_registry.update_state(
            self.project_registry.active_project_id, values, save=save
        )

    def _restore_window_state(self) -> None:
        self.resize(
            self.config.get_int("window_width", 1350, minimum=900),
            self.config.get_int("window_height", 850, minimum=600),
        )
        sizes = self.config.get_int_list(
            "splitter_sizes", [260, 1090], length=2
        )
        self._restored_sidebar_width = sizes[0] or 260
        self._set_sidebar_position(
            str(self.config.get("sidebar_position", "left")), persist=False
        )
        QTimer.singleShot(0, self._restore_splitter_geometry)
        if bool(self.config.get("window_maximized", False)):
            self.showMaximized()

    def _restore_splitter_geometry(self) -> None:
        self._set_splitter_sidebar_width(
            int(getattr(self, "_restored_sidebar_width", 260))
        )

    def _refresh_workspace(self, _checked=False) -> None:
        self._repair_navigation_after_scan = True
        self.show_status("Refreshing workspace in background…")
        self.watcher.request_rescan()

    def _on_scan_started(self) -> None:
        message = (
            "Refreshing your workspace…"
            if self._repair_navigation_after_scan
            else "Preparing your workspace…"
        )
        self.editor_manager.dashboard.set_loading(True, message)
        self.navigation.set_loading(True, "Building folder tree…")
        self.show_status("Scanning workspace in background…")

    def _on_scan_details(self, entries: int, seconds: float) -> None:
        detail = f"Scanned {entries:,} filesystem entries in {seconds:.1f}s."
        self.editor_manager.dashboard.set_loading_detail(detail)
        self.navigation.set_loading_detail(
            f"{sum(1 for document in self.repository if not document.external):,} RTF files found"
        )
        self.show_status(detail)

    def _on_scan_finished(self, count: int) -> None:
        self.editor_manager.dashboard.set_loading(False)
        self.navigation.set_loading(False)
        project_name = self.project_registry.active_project.name
        if self._repair_navigation_after_scan:
            self._repair_navigation_after_scan = False
            self.navigation.rebuild_from_repository()
            self.show_status(
                f"Refreshed {count} RTF file(s) in {project_name}."
            )
        else:
            self.show_status(
                f"Loaded {count} RTF file(s) in {project_name}."
            )
        if self._pending_open_path is not None:
            document = self.repository.get(self._pending_open_path)
            if document is not None:
                self._open_pending_if_ready(document)
        if not self._startup_scan_pending:
            return
        self._startup_scan_pending = False
        if self._startup_open_requested:
            return
        if str(self.config.get("app_launch_screen", "dashboard")) == "last_file":
            last = self.project_registry.active_project.state.get(
                "last_opened_file"
            )
            document = self.repository.get(last) if last else None
            if document is not None:
                self.editor_manager.open_document(document)
                return
        self.editor_manager.show_dashboard()

    def _on_scan_failed(self, message: str) -> None:
        self.editor_manager.dashboard.set_loading(False)
        self.navigation.set_loading(False)
        self.show_status(f"Workspace scan failed: {message}")
        QMessageBox.warning(self, "Workspace Scan Failed", message)

    def _on_folder_renamed(
        self, _old_path: Path, new_path: Path
    ) -> None:
        QTimer.singleShot(
            400, lambda: self.editor_manager.open_folder(new_path)
        )

    def _update_dirty_status(self, count: int) -> None:
        if count:
            self.show_status(f"{count} RTF file has unsaved changes." if count == 1 else f"{count} RTF files have unsaved changes.")

    def show_status(self, message: str) -> None:
        from riqatony_desk.widgets.message_conventions import (
            DEFAULT_MESSAGE_DURATION_MS, is_critical_status, status_sentence,
        )
        text = status_sentence(message)
        critical = is_critical_status(text)
        # An unresolved failure stays visible until a deliberate retry/success
        # or another critical event replaces it. Routine notices cannot hide it.
        recovering = text.startswith((
            "Opening Workspace:", "Refreshing workspace", "Scanning workspace",
            "Refreshed ", "Loaded ",
        ))
        if getattr(self, "_critical_workspace_message", False) and not (critical or recovering):
            return
        self._critical_workspace_message = critical
        self._status_label.setText(text)
        timer = getattr(self, "_workspace_message_timer", None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._status_label.setText("Ready."))
            self._workspace_message_timer = timer
        timer.stop()
        if not is_critical_status(text):
            timer.start(DEFAULT_MESSAGE_DURATION_MS)

    def _write_shutdown_timing(self, timings: dict[str, float]) -> None:
        """Write shutdown diagnostics only when explicitly requested."""
        enabled = os.environ.get(SHUTDOWN_PROFILE_ENV, "").casefold()
        if enabled not in {"1", "true", "yes", "on"}:
            return

        report_path = self.runtime_paths.config_root / "shutdown-timing.jsonl"
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "documents": len(self.repository),
            "timings_ms": {
                key: round(value * 1000.0, 2)
                for key, value in timings.items()
            },
        }
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        except OSError:
            pass

        printable = " · ".join(
            f"{key}={value * 1000.0:.1f} ms"
            for key, value in timings.items()
        )
        print(f"RiqatonyDesk shutdown: {printable}", flush=True)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._closing:
            event.accept()
            return

        started = time.perf_counter()
        timings: dict[str, float] = {}

        unsaved_started = time.perf_counter()
        if not self.editor_manager.can_close_application():
            timings["unsaved_prompt"] = time.perf_counter() - unsaved_started
            event.ignore()
            return
        timings["unsaved_prompt"] = time.perf_counter() - unsaved_started

        self._closing = True

        closing_dialog = ClosingDialog(self)
        closing_dialog.start()
        QApplication.processEvents()

        def stage(detail: str) -> None:
            closing_dialog.set_stage(detail)
            QApplication.processEvents()

        stage("Saving your preferences…")
        config_started = time.perf_counter()
        self._save_active_project_state(save=True)
        splitter_sizes = (
            list(
                self._collapsed_mode_restore.get(
                    "splitter_sizes", self._logical_splitter_sizes()
                )
            )
            if self._collapsed_mode_restore is not None
            else self._logical_splitter_sizes()
        )
        self.config.update(
            {
                "window_width": self.width(),
                "window_height": self.height(),
                "window_maximized": self.isMaximized(),
                "splitter_sizes": splitter_sizes,
                "collapsed_folders": sorted(
                    self.navigation.collapsed_folders()
                ),
                "dashboard_sort": self.editor_manager.dashboard._sort_mode,
                "dashboard_search": (
                    self.editor_manager.dashboard.search_input.text()
                ),
                "dashboard_view": (
                    self.editor_manager.dashboard.view_mode()
                ),
                # Compatibility mirror for the application-level fallback.
                # The per-Workspace value preserved above is authoritative.
                "last_opened_file": self.project_registry.active_project.state.get(
                    "last_opened_file"
                ),
                "last_opened_folder": (
                    str(self.editor_manager.current_folder)
                    if self.editor_manager.current_folder is not None
                    else None
                ),
            },
            save=True,
        )
        timings["save_config"] = time.perf_counter() - config_started

        # Hide the main hierarchy without rebuilding Dashboard cards on exit.
        # The Dashboard is not becoming interactive on a successful close.
        self.navigation.set_loading(False)
        self.centralWidget().hide()
        self.menuBar().hide()
        self.statusBar().hide()
        closing_dialog.adjustSize()
        closing_dialog.move(
            self.frameGeometry().center()
            - closing_dialog.rect().center()
        )
        QApplication.processEvents()

        stage("Stopping the workspace scanner…")
        scanner_started = time.perf_counter()
        scan_stopped = self.watcher.stop(
            timeout_ms=2000,
            pump_events=QApplication.processEvents,
        )
        timings["stop_scanner"] = time.perf_counter() - scanner_started

        if not scan_stopped:
            self._closing = False
            closing_dialog.close()
            # Shutdown was cancelled: restore the normal, usable Dashboard.
            self.editor_manager.dashboard.set_loading(False)
            self.centralWidget().show()
            self.menuBar().show()
            self.statusBar().show()
            self.show_status("Could not cancel the workspace scan yet.")
            event.ignore()
            return

        timings["total_before_exit"] = time.perf_counter() - started
        self._write_shutdown_timing(timings)

        stage("Closing RiqatonyDesk…")
        event.accept()
        QApplication.processEvents()

        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os._exit(0)
