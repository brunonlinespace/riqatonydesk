# RiqatonyDesk
# Copyright (C) 2026 Bruno Machado
# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing MainWindow Help and Quick Tour methods, relocated unchanged."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox, QLabel, QMenu, QMessageBox, QPushButton,
    QVBoxLayout, QWizard, QWizardPage,
)
from riqatony_desk.widgets.dialogs.about_dialog import AboutDialog
from riqatony_desk.widgets.dialogs.shortcuts_dialog import ShortcutsDialog


class HelpActionsMixin:
    def _shortcut_catalog(self):
        """Return every assigned shortcut, grouped by authoritative AppMenu menu.

        Menu actions are collected recursively so nested formatting/alignment/
        paragraph/spacing shortcuts cannot silently disappear from the reference
        dialog.  Non-menu shortcuts are appended explicitly.
        """
        label_overrides = {
            self.rename_file_action: "Rename File or Folder",
            self.zoom_reset_action: "Zoom Reset",
            self.quick_start_action: "Quick Tour",
        }

        def collect(menu: QMenu):
            entries = []
            for action in menu.actions():
                submenu = action.menu()
                if submenu is not None:
                    entries.extend(collect(submenu))
                    continue
                if action.shortcut().toString(QKeySequence.SequenceFormat.NativeText).strip():
                    entries.append((label_overrides.get(action, action.text()), action))
            return entries

        catalog = {
            "File": collect(self.file_menu),
            "Edit": collect(self.edit_menu),
            "Format": collect(self.format_menu),
            "Insert": collect(self.insert_menu),
            "View": collect(self.view_menu),
            "Settings": collect(self.settings_menu),
            "Help": collect(self.help_menu),
        }

        # These shortcuts are intentionally not represented by AppMenu QActions.
        catalog["File"].extend((
            ("Close Tab / Dashboard", self.close_context_action),
            ("Open Context Tab", self.open_context_tab_action),
        ))
        catalog["Edit"].extend((
            ("Find Next", "F3"),
            ("Previous Match", "Shift+F3"),
        ))
        catalog["View"].extend((
            (("Next Document Tab" if self._tabs_enabled() else "Next Ribbon Tab"), self.next_document_tab_action),
            (("Previous Document Tab" if self._tabs_enabled() else "Previous Ribbon Tab"), self.previous_document_tab_action),
        ))
        catalog["Settings"].extend((
            ("Toggle List/Grid View", self.toggle_dashboard_view_action),
            ("Toggle Sidebar Position", self.toggle_sidebar_position_action),
        ))
        return catalog

    def _show_shortcuts(self, _checked=False) -> None:
        if self.shortcuts_dialog is not None:
            self.shortcuts_dialog.show()
            self.shortcuts_dialog.raise_()
            self.shortcuts_dialog.activateWindow()
            return
        dialog = ShortcutsDialog(self._shortcut_catalog(), self)
        dialog.finished.connect(
            lambda _result: setattr(self, "shortcuts_dialog", None)
        )
        self.shortcuts_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog.search.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _show_quick_tour(self) -> None:
        """Show the first-time RiqatonyDesk tour in the established wizard UI."""
        if self.quick_tour_dialog is not None:
            self.quick_tour_dialog.show()
            self.quick_tour_dialog.raise_()
            self.quick_tour_dialog.activateWindow()
            return

        wizard = QWizard(self)
        wizard.setWindowTitle("Quick Tour — RiqatonyDesk")
        wizard.setWindowIcon(self.windowIcon())
        wizard.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        wizard.setModal(False)
        wizard.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        wizard.setMinimumSize(700, 470)
        wizard.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        startup_checkbox = QCheckBox("Don't show Quick Tour on startup again", wizard)
        startup_checkbox.setChecked(bool(self.config.get("quick_tour_seen", False)))
        startup_checkbox.toggled.connect(
            lambda checked: self.config.set("quick_tour_seen", bool(checked), save=True)
        )
        wizard.setButton(QWizard.WizardButton.CustomButton1, startup_checkbox)
        wizard.setOption(QWizard.WizardOption.HaveCustomButton1, True)
        wizard.setButtonLayout([
            QWizard.WizardButton.CustomButton1,
            QWizard.WizardButton.Stretch,
            QWizard.WizardButton.BackButton,
            QWizard.WizardButton.NextButton,
            QWizard.WizardButton.FinishButton,
            QWizard.WizardButton.CancelButton,
        ])

        def add_page(title: str, subtitle: str, body: str, button=None) -> None:
            page = QWizardPage(wizard)
            page.setTitle(title)
            page.setSubTitle(subtitle)
            layout = QVBoxLayout(page)
            label = QLabel(body, page)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(label)
            if button is not None:
                layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addStretch(1)
            wizard.addPage(page)

        add_page(
            "Welcome to RiqatonyDesk",
            "A workspace-scale Ricopad for ordinary Rich Text Format files.",
            "<p>The Ribbon has five tabs: <b>File, Home, Insert, Configure "
            "and Help</b>, with Home open by default.</p>"
            "<p>Hover a command for its name and shortcut. When document tabs are "
            "<b>enabled</b>, <b>Ctrl+Tab</b> and <b>Ctrl+Shift+Tab</b> move forward "
            "and backward through open document and navigation tabs. When document tabs are "
            "<b>disabled</b>, the same shortcuts move forward and backward through the Ribbon pages instead.</p>"
            "<p><b>Ctrl+T</b> opens the current navigation context as a tab, enabling tabs first if necessary. "
            "From an open document, this opens its containing folder; from a folder or Dashboard view, it opens "
            "or reuses that navigation context.</p>"
            "<p><b>Ctrl+W</b> closes the active document tab when tabs are enabled, using the normal unsaved-changes "
            "protection, then returns to its folder navigation context. When tabs are disabled, or no document is active, "
            "<b>Ctrl+W</b> returns to the Dashboard.</p>"
            "<p>Double-click a Ribbon page title to collapse the Ribbon controls; click a Ribbon page title once to reveal them again.</p>",
        )
        add_page(
            "Workspaces and Dashboard",
            "Keep separate RTF collections without moving the application.",
            "<p><b>File → Workspace(s)</b> lists registered Workspaces and marks "
            "the active one. <b>Open / Manage Workspaces…</b> adds an existing folder, "
            "renames its display label, relinks it, or removes only its "
            "registration.</p>"
            "<p>Only the active Workspace is scanned and watched. The Dashboard "
            "and sidebar are the navigation layer around Ricopad's RTF editor.</p>",
        )
        add_page(
            "Create, open and save",
            "RiqatonyDesk edits standards-based RTF files directly.",
            "<p><b>File</b> contains New File, New Folder, New Window…, "
            "Save, Save As, Print, Export PDF and file-management commands. "
            "Save and New, Save and Dashboard and Save and Exit save first, "
            "then perform the named action.</p>"
            "<p>Use <b>Ctrl+Up</b> and <b>Ctrl+Down</b> for adjacent RTF files in "
            "the folder tree. Dragged RTF files follow the configured active-"
            "window/new-window behavior.</p>",
        )
        add_page(
            "Format rich text",
            "Ricopad remains the document-formatting engine.",
            "<p><b>Home</b> provides font face, size, paragraph style, emphasis, "
            "colours/highlights, bullets, indentation, alignment, paragraph "
            "settings and line spacing.</p>"
            "<p><b>Insert</b> contains tables, links, symbols, images, horizontal "
            "rules, dates and times. Character formatting operates on the "
            "selection, or on the current word when there is no selection.</p>",
        )
        add_page(
            "Find, protect and read",
            "Search quickly, reduce distractions and prevent accidental edits when needed.",
            "<p><b>Ctrl+F</b> opens Find in documents or focuses Dashboard/folder search. Use <b>F3</b> for the next document match and "
            "<b>Shift+F3</b> for the previous result. Home also provides Find and Replace.</p>"
            "<p><b>Locked Mode</b> prevents accidental document changes while navigation, copying and search remain available. "
            "The lock is a RiqatonyDesk preference and persists as you move between files and sessions.</p>"
            "<p><b>Focused Mode</b> temporarily clears away surrounding interface elements so you can concentrate on the document. "
            "It hides the sidebar, status bar and file header and collapses the Ribbon, while remembering their previous states. "
            "Turn Focused Mode off to restore the interface exactly as it was before.</p>",
        )
        add_page(
            "Configure appearance",
            "Application and editor appearance are controlled independently.",
            "<p><b>App Theme</b> controls the RiqatonyDesk interface and can be set to <b>Light, Dark or System</b>. "
            "New installations default to <b>Light</b>.</p>"
            "<p><b>Dark Editor</b> controls the editor canvas independently of the application theme. With Dark Editor off, "
            "the editor uses its light canvas; with it on, the editor uses its dark canvas. New installations default to a "
            "<b>Light application with a Light editor</b>. Changing App Theme does not automatically change the editor canvas, "
            "and changing Dark Editor does not change the application theme.</p>"
            "<p>Configure also contains <b>Riqa Icons Harmony, Humility and Heritage</b>, zoom, sidebar and status controls, Word Wrap, "
            "Tab Width, New Document Defaults, Dashboard List/Grid view, launch-screen choice and Tabs Enabled/Disabled. "
            "<b>New Document Defaults…</b> is also available under <b>View → Editor Miscellaneous</b>, while <b>Focused Mode</b> "
            "is available from Settings.</p>",
        )
        shortcuts_button = QPushButton("Open Keyboard Shortcuts…", wizard)
        shortcuts_button.setAutoDefault(False)
        shortcuts_button.clicked.connect(self._show_shortcuts)
        add_page(
            "RTF interoperability and help",
            "Use Ricopad's established RTF workflow with Plus workspace management.",
            "<p>RiqatonyDesk writes standards-based RTF intended to interoperate "
            "with other RTF applications. Lists use standard RTF list tables and "
            "overrides rather than private markers.</p>"
            "<p>Help contains the bundled documentation, this Quick Tour, "
            "the live keyboard-shortcut inventory, the RiqatonyDesk GitHub Repository, issue reporting and "
            "About.</p>",
            shortcuts_button,
        )

        def tour_finished(_result: int) -> None:
            self.quick_tour_dialog = None
            page = self._current_page()
            if page is not None:
                QTimer.singleShot(0, page.editor.setFocus)

        wizard.finished.connect(tour_finished)
        self.quick_tour_dialog = wizard
        wizard.show()
        wizard.raise_()
        wizard.activateWindow()

    def _open_documentation(self, _checked=False) -> None:
        path = self.package_root / "docs" / "Documentation.rtf"
        if not path.is_file():
            QMessageBox.information(
                self,
                "Documentation — RiqatonyDesk",
                "The bundled RiqatonyDesk RTF documentation could not be found.",
            )
            return
        self._launch_new_window(path)

    def _show_about_dialog(self, _checked=False) -> None:
        if self.about_dialog is not None:
            self.about_dialog.show()
            self.about_dialog.raise_()
            self.about_dialog.activateWindow()
            return
        path = self.package_root / "assets" / "icons" / "riqatonydesk-about.png"
        dialog = AboutDialog(
            path if path.is_file() else self.icon_path,
            self.runtime_paths.config_path,
            self,
            desktop_launcher=self.desktop_launcher,
        )
        dialog.finished.connect(
            lambda _result: setattr(self, "about_dialog", None)
        )
        self.about_dialog = dialog
        dialog.show()

